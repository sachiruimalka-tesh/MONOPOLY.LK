#include <stdio.h>
#include <stdlib.h>
#include "types.h"
#include "functions.h"

/*========================================
    NOTE: no global variables, no pointers. initEconomy() fills in
    the game[0].economy part of whatever GameState it's given - it
    doesn't own or create anything global any more.
========================================*/

void initEconomy(GameState game[])
{
    game[0].economy.inflationRate = 0;
    game[0].economy.loanInterestRate = LOAN_INTEREST_RATE;

    game[0].economy.hotelRentMultiplierPercent = 100;
    game[0].economy.hotelRentRoundsLeft = 0;

    game[0].economy.railwayRentMultiplierPercent = 100;
    game[0].economy.railwayRentRoundsLeft = 0;

    game[0].economy.utilityRentMultiplierPercent = 100;
    game[0].economy.utilityRentRoundsLeft = 0;

    game[0].economy.constructionCostMultiplierPercent = 100;
    game[0].economy.constructionCostRoundsLeft = 0;

    game[0].economy.insurancePremiumMultiplierPercent = 100;
    game[0].economy.insurancePremiumRoundsLeft = 0;

    game[0].economy.constructionSuspendedRoundsLeft = 0;

    game[0].economy.closedPropertyIndex = -1;
    game[0].economy.closedPropertyRoundsLeft = 0;

    game[0].economy.incomeTaxAmount = 1000;

    game[0].economy.antiSpeculationActive = 0;

    game[0].economy.currentCardIndex = 0;
}

/*========================================
    Apply New = Old * (1 + rate/100) to a
    value, never letting it drop below 1
    (Rule-LK 14). This one doesn't touch the
    game state at all, so it stays a small,
    plain helper with no GameState parameter.
========================================*/

int applyRate(int oldValue, int ratePercent)
{
    int newValue;

    newValue = oldValue + (oldValue * ratePercent) / 100;

    if(newValue < 1)
        newValue = 1;

    return newValue;
}

/*========================================
    INFLATION (Section 2.3)
    Runs every 10 rounds.
========================================*/

void applyInflation(GameState game[])
{
    int possibleRates[6] = {-3, 0, 2, 5, 8, 12};
    int rate;
    int i;

    rate = possibleRates[rand() % 6];
    game[0].economy.inflationRate = rate;

    printf("\n=== Inflation Update ===\n");
    printf("New Inflation Rate : %+d%%\n", rate);

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type != PROPERTY &&
           game[0].board[i].type != RAILWAY &&
           game[0].board[i].type != UTILITY)
        {
            continue;
        }

        game[0].board[i].property.purchasePrice =
            applyRate(game[0].board[i].property.purchasePrice, rate);

        game[0].board[i].property.mortgageValue =
            applyRate(game[0].board[i].property.mortgageValue, rate);

        if(game[0].board[i].type == PROPERTY)
        {
            game[0].board[i].property.baseRent =
                applyRate(game[0].board[i].property.baseRent, rate);

            game[0].board[i].property.houseCost =
                applyRate(game[0].board[i].property.houseCost, rate);

            game[0].board[i].property.hotelCost =
                applyRate(game[0].board[i].property.hotelCost, rate);
        }
    }

    /* New loans (not existing ones) follow inflation too - Rule-LK 13 */
    game[0].economy.loanInterestRate = applyRate(game[0].economy.loanInterestRate, rate);

    printf("New Loan Interest Rate : %d%%\n", game[0].economy.loanInterestRate);
}

/*========================================
    PROPERTY AGE & DEPRECIATION
    (Rule-LK 15, 16)
========================================*/

/* "Current market value" after depreciation is taken into account.
   Used for insurance premiums, repair costs, and renovation costs. */
int currentMarketValue(GameState game[], int propIndex)
{
    int price;
    int depreciation;
    PropertyGroup group;

    price = game[0].board[propIndex].property.purchasePrice;
    depreciation = game[0].board[propIndex].property.depreciation;

    price = price - (price * depreciation) / 100;

    /* Also apply any active Dynamic Market / Regional Card effect
       on this property's colour group (Sections 2.9, 2.10)         */
    if(game[0].board[propIndex].type == PROPERTY)
    {
        group = game[0].board[propIndex].property.group;
        price = (price * game[0].economy.groupValueMultiplier[group]) / 100;
    }

    return price;
}

void ageProperties(GameState game[])
{
    int i;
    int roundsOver50;
    int newDepreciation;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type != PROPERTY)
            continue;

        game[0].board[i].property.age++;

        if(game[0].board[i].property.age > 50)
        {
            roundsOver50 = game[0].board[i].property.age - 50;
            newDepreciation = roundsOver50 / 5;

            if(newDepreciation > 30)
                newDepreciation = 30;

            game[0].board[i].property.depreciation = newDepreciation;
        }
    }
}

/*========================================
    RENOVATE AWAY AGE DEPRECIATION (Rule-LK 17)
    Called when a player lands on their OWN
    developed-or-not property.
========================================*/

void tryRenovateAgeDepreciation(GameState game[], int playerIndex, int propIndex)
{
    int cost;

    if(game[0].board[propIndex].property.depreciation <= 0)
        return;

    if(!shouldRenovateAgeDepreciation(game, playerIndex,
                                       game[0].board[propIndex].property.depreciation))
    {
        return;
    }

    cost = (currentMarketValue(game, propIndex) * 10) / 100;

    if(game[0].players[playerIndex].cash < cost)
        return;

    payMoney(game, playerIndex, cost);

    game[0].board[propIndex].property.age = 0;
    game[0].board[propIndex].property.depreciation = 0;

    /* Renovation "increases rental" - a small permanent 5% bump */
    game[0].board[propIndex].property.baseRent =
        applyRate(game[0].board[propIndex].property.baseRent, 5);

    printf("\n%s renovated %s.\n",
           game[0].players[playerIndex].name, game[0].board[propIndex].name);

    printf("Renovation Cost : LKR %d\n", cost);
}

/*========================================
    BUILDING CONDITION & MAINTENANCE
    (Rule-LK 25 - 29)
========================================*/

/* Table 3 : how much rent a building actually collects,
   based on its condition. Pure lookup - no game state needed. */
int rentConditionPercent(int condition)
{
    if(condition >= 90)  return 100;
    if(condition >= 75)  return 90;
    if(condition >= 50)  return 75;
    if(condition >= 25)  return 50;

    return 0;   /* Below 25% - building closed */
}

void ageBuildings(GameState game[])
{
    int i;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type != PROPERTY)
            continue;

        if(game[0].board[i].property.houses == 0 && !game[0].board[i].property.hotel)
            continue;   /* nothing built here yet */

        /* Condition wears down 2% every round (Rule-LK 25) */
        game[0].board[i].property.condition -= 2;

        if(game[0].board[i].property.condition < 0)
            game[0].board[i].property.condition = 0;

        game[0].board[i].property.roundsSinceMaintenance++;

        /* Rule-LK 28 : 20+ rounds neglected -> structural damage */
        if(game[0].board[i].property.roundsSinceMaintenance > 20 &&
           !game[0].board[i].property.structurallyDamaged)
        {
            game[0].board[i].property.structurallyDamaged = 1;

            /* Remember the values from just before the damage,
               so a later renovation can restore them exactly    */
            game[0].board[i].property.preDamagePurchasePrice =
                game[0].board[i].property.purchasePrice;
            game[0].board[i].property.preDamageBaseRent =
                game[0].board[i].property.baseRent;

            game[0].board[i].property.purchasePrice =
                game[0].board[i].property.purchasePrice -
                (game[0].board[i].property.purchasePrice * 15) / 100;

            game[0].board[i].property.baseRent =
                game[0].board[i].property.baseRent -
                (game[0].board[i].property.baseRent * 25) / 100;

            game[0].board[i].property.maintenanceCostMultiplierPercent = 150;
            game[0].board[i].property.condition = 0;

            printf("\n%s has suffered structural damage from neglect!\n",
                   game[0].board[i].name);
        }
    }
}

/*========================================
    REGULAR MAINTENANCE (Rule-LK 27)
    Called at the start of a player's turn.
========================================*/

void performMaintenance(GameState game[], int playerIndex)
{
    int i;
    int baseCost;
    int cost;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type != PROPERTY)
            continue;

        if(game[0].board[i].property.owner != playerIndex)
            continue;

        if(game[0].board[i].property.houses == 0 && !game[0].board[i].property.hotel)
            continue;

        if(game[0].board[i].property.structurallyDamaged)
            continue;   /* needs a full renovation instead, see below */

        if(game[0].board[i].property.condition >= 100)
            continue;   /* nothing to fix */

        if(game[0].board[i].property.hotel)
            baseCost = (game[0].board[i].property.hotelCost * 8) / 100;
        else
            baseCost = (game[0].board[i].property.houseCost * 5) / 100;

        cost = (baseCost * game[0].board[i].property.maintenanceCostMultiplierPercent) / 100;

        if(!shouldMaintain(game, playerIndex, game[0].board[i].property.condition, cost))
            continue;

        if(game[0].players[playerIndex].cash < cost)
            continue;

        payMoney(game, playerIndex, cost);

        game[0].board[i].property.condition = 100;
        game[0].board[i].property.roundsSinceMaintenance = 0;

        printf("\n%s performed maintenance on %s.\n",
               game[0].players[playerIndex].name, game[0].board[i].name);

        printf("Maintenance Cost : LKR %d\n", cost);
    }
}

/*========================================
    FULL RENOVATION AFTER STRUCTURAL DAMAGE
    (Rule-LK 29)
========================================*/

void renovateStructuralDamage(GameState game[], int playerIndex)
{
    int i;
    int replacementValue;
    int cost;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type != PROPERTY)
            continue;

        if(game[0].board[i].property.owner != playerIndex)
            continue;

        if(!game[0].board[i].property.structurallyDamaged)
            continue;

        replacementValue = game[0].board[i].property.hotel ?
                            game[0].board[i].property.hotelCost :
                            game[0].board[i].property.houseCost;

        cost = (replacementValue * 25) / 100;

        if(game[0].players[playerIndex].cash < cost)
            continue;

        payMoney(game, playerIndex, cost);

        game[0].board[i].property.purchasePrice = game[0].board[i].property.preDamagePurchasePrice;
        game[0].board[i].property.baseRent = game[0].board[i].property.preDamageBaseRent;
        game[0].board[i].property.condition = 100;
        game[0].board[i].property.structurallyDamaged = 0;
        game[0].board[i].property.maintenanceCostMultiplierPercent = 100;
        game[0].board[i].property.roundsSinceMaintenance = 0;

        printf("\n%s fully renovated %s after structural damage.\n",
               game[0].players[playerIndex].name, game[0].board[i].name);

        printf("Renovation Cost : LKR %d\n", cost);
    }
}
