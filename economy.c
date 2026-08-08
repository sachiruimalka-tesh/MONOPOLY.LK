#include <stdio.h>
#include <stdlib.h>
#include "types.h"
#include "functions.h"

/*========================================
    GLOBAL VARIABLES
========================================*/

extern Player players[MAX_PLAYERS];
extern Square board[BOARD_SIZE];

/* THE single global Economy struct instance (declared extern in
   types.h so every file can see it). C automatically zero-fills
   this at startup, but several fields need a non-zero starting
   value (like interest rate = 8%, not 0%), so initEconomy() sets
   those up properly - call it once at the very start of the game. */
Economy economy;

void initEconomy(void)
{
    economy.inflationRate = 0;
    economy.loanInterestRate = LOAN_INTEREST_RATE;

    economy.hotelRentMultiplierPercent = 100;
    economy.hotelRentRoundsLeft = 0;

    economy.railwayRentMultiplierPercent = 100;
    economy.railwayRentRoundsLeft = 0;

    economy.utilityRentMultiplierPercent = 100;
    economy.utilityRentRoundsLeft = 0;

    economy.constructionCostMultiplierPercent = 100;
    economy.constructionCostRoundsLeft = 0;

    economy.insurancePremiumMultiplierPercent = 100;
    economy.insurancePremiumRoundsLeft = 0;

    economy.constructionSuspendedRoundsLeft = 0;

    economy.closedPropertyIndex = -1;
    economy.closedPropertyRoundsLeft = 0;

    economy.incomeTaxAmount = 1000;

    economy.antiSpeculationActive = 0;

    economy.currentCardIndex = 0;
}

/*========================================
    Apply New = Old * (1 + rate/100) to a
    value, never letting it drop below 1
    (Rule-LK 14)
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

void applyInflation(void)
{
    int possibleRates[6] = {-3, 0, 2, 5, 8, 12};
    int rate;
    int i;

    rate = possibleRates[rand() % 6];
    economy.inflationRate = rate;

    printf("\n=== Inflation Update ===\n");
    printf("New Inflation Rate : %+d%%\n", rate);

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type != PROPERTY &&
           board[i].type != RAILWAY &&
           board[i].type != UTILITY)
        {
            continue;
        }

        board[i].property.purchasePrice =
            applyRate(board[i].property.purchasePrice, rate);

        board[i].property.mortgageValue =
            applyRate(board[i].property.mortgageValue, rate);

        if(board[i].type == PROPERTY)
        {
            board[i].property.baseRent =
                applyRate(board[i].property.baseRent, rate);

            board[i].property.houseCost =
                applyRate(board[i].property.houseCost, rate);

            board[i].property.hotelCost =
                applyRate(board[i].property.hotelCost, rate);
        }
    }

    /* New loans (not existing ones) follow inflation too - Rule-LK 13 */
    economy.loanInterestRate = applyRate(economy.loanInterestRate, rate);

    printf("New Loan Interest Rate : %d%%\n", economy.loanInterestRate);
}

/*========================================
    PROPERTY AGE & DEPRECIATION
    (Rule-LK 15, 16)
========================================*/

/* "Current market value" after depreciation is taken into account.
   Used for insurance premiums, repair costs, and renovation costs. */
int currentMarketValue(int propIndex)
{
    int price;
    int depreciation;
    PropertyGroup group;

    price = board[propIndex].property.purchasePrice;
    depreciation = board[propIndex].property.depreciation;

    price = price - (price * depreciation) / 100;

    /* Also apply any active Dynamic Market / Regional Card effect
       on this property's colour group (Sections 2.9, 2.10)         */
    if(board[propIndex].type == PROPERTY)
    {
        group = board[propIndex].property.group;
        price = (price * economy.groupValueMultiplier[group]) / 100;
    }

    return price;
}

void ageProperties(void)
{
    int i;
    int roundsOver50;
    int newDepreciation;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type != PROPERTY)
            continue;

        board[i].property.age++;

        if(board[i].property.age > 50)
        {
            roundsOver50 = board[i].property.age - 50;
            newDepreciation = roundsOver50 / 5;

            if(newDepreciation > 30)
                newDepreciation = 30;

            board[i].property.depreciation = newDepreciation;
        }
    }
}

/*========================================
    RENOVATE AWAY AGE DEPRECIATION (Rule-LK 17)
    Called when a player lands on their OWN
    developed-or-not property.
========================================*/

void tryRenovateAgeDepreciation(int playerIndex, int propIndex)
{
    int cost;

    if(board[propIndex].property.depreciation <= 0)
        return;

    if(!shouldRenovateAgeDepreciation(playerIndex,
                                       board[propIndex].property.depreciation))
    {
        return;
    }

    cost = (currentMarketValue(propIndex) * 10) / 100;

    if(players[playerIndex].cash < cost)
        return;

    payMoney(playerIndex, cost);

    board[propIndex].property.age = 0;
    board[propIndex].property.depreciation = 0;

    /* Renovation "increases rental" - a small permanent 5% bump */
    board[propIndex].property.baseRent =
        applyRate(board[propIndex].property.baseRent, 5);

    printf("\n%s renovated %s.\n",
           players[playerIndex].name, board[propIndex].name);

    printf("Renovation Cost : LKR %d\n", cost);
}

/*========================================
    BUILDING CONDITION & MAINTENANCE
    (Rule-LK 25 - 29)
========================================*/

/* Table 3 : how much rent a building actually collects,
   based on its condition                                */
int rentConditionPercent(int condition)
{
    if(condition >= 90)  return 100;
    if(condition >= 75)  return 90;
    if(condition >= 50)  return 75;
    if(condition >= 25)  return 50;

    return 0;   /* Below 25% - building closed */
}

void ageBuildings(void)
{
    int i;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type != PROPERTY)
            continue;

        if(board[i].property.houses == 0 && !board[i].property.hotel)
            continue;   /* nothing built here yet */

        /* Condition wears down 2% every round (Rule-LK 25) */
        board[i].property.condition -= 2;

        if(board[i].property.condition < 0)
            board[i].property.condition = 0;

        board[i].property.roundsSinceMaintenance++;

        /* Rule-LK 28 : 20+ rounds neglected -> structural damage */
        if(board[i].property.roundsSinceMaintenance > 20 &&
           !board[i].property.structurallyDamaged)
        {
            board[i].property.structurallyDamaged = 1;

            /* Remember the values from just before the damage,
               so a later renovation can restore them exactly    */
            board[i].property.preDamagePurchasePrice =
                board[i].property.purchasePrice;
            board[i].property.preDamageBaseRent =
                board[i].property.baseRent;

            board[i].property.purchasePrice =
                board[i].property.purchasePrice -
                (board[i].property.purchasePrice * 15) / 100;

            board[i].property.baseRent =
                board[i].property.baseRent -
                (board[i].property.baseRent * 25) / 100;

            board[i].property.maintenanceCostMultiplierPercent = 150;
            board[i].property.condition = 0;

            printf("\n%s has suffered structural damage from neglect!\n",
                   board[i].name);
        }
    }
}

/*========================================
    REGULAR MAINTENANCE (Rule-LK 27)
    Called at the start of a player's turn.
========================================*/

void performMaintenance(int playerIndex)
{
    int i;
    int baseCost;
    int cost;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type != PROPERTY)
            continue;

        if(board[i].property.owner != playerIndex)
            continue;

        if(board[i].property.houses == 0 && !board[i].property.hotel)
            continue;

        if(board[i].property.structurallyDamaged)
            continue;   /* needs a full renovation instead, see below */

        if(board[i].property.condition >= 100)
            continue;   /* nothing to fix */

        if(board[i].property.hotel)
            baseCost = (board[i].property.hotelCost * 8) / 100;
        else
            baseCost = (board[i].property.houseCost * 5) / 100;

        cost = (baseCost * board[i].property.maintenanceCostMultiplierPercent) / 100;

        if(!shouldMaintain(playerIndex, board[i].property.condition, cost))
            continue;

        if(players[playerIndex].cash < cost)
            continue;

        payMoney(playerIndex, cost);

        board[i].property.condition = 100;
        board[i].property.roundsSinceMaintenance = 0;

        printf("\n%s performed maintenance on %s.\n",
               players[playerIndex].name, board[i].name);

        printf("Maintenance Cost : LKR %d\n", cost);
    }
}

/*========================================
    FULL RENOVATION AFTER STRUCTURAL DAMAGE
    (Rule-LK 29)
========================================*/

void renovateStructuralDamage(int playerIndex)
{
    int i;
    int replacementValue;
    int cost;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type != PROPERTY)
            continue;

        if(board[i].property.owner != playerIndex)
            continue;

        if(!board[i].property.structurallyDamaged)
            continue;

        replacementValue = board[i].property.hotel ?
                            board[i].property.hotelCost :
                            board[i].property.houseCost;

        cost = (replacementValue * 25) / 100;

        if(players[playerIndex].cash < cost)
            continue;

        payMoney(playerIndex, cost);

        board[i].property.purchasePrice = board[i].property.preDamagePurchasePrice;
        board[i].property.baseRent = board[i].property.preDamageBaseRent;
        board[i].property.condition = 100;
        board[i].property.structurallyDamaged = 0;
        board[i].property.maintenanceCostMultiplierPercent = 100;
        board[i].property.roundsSinceMaintenance = 0;

        printf("\n%s fully renovated %s after structural damage.\n",
               players[playerIndex].name, board[i].name);

        printf("Renovation Cost : LKR %d\n", cost);
    }
}
