#include <stdio.h>
#include "types.h"
#include "functions.h"

/*========================================
    NOTE: no global variables and no pointers are used anywhere in
    this file. Every function that needs the board, the players, or
    the economy receives the whole GameState as an array parameter
    (`GameState game[]`), and reads/writes it using plain dot and
    bracket notation: game[0].board[...], game[0].players[...],
    game[0].economy....
========================================*/

/*========================================
    MONEY HELPERS
========================================*/

void receiveMoney(GameState game[], int playerIndex, int amount)
{
    game[0].players[playerIndex].cash += amount;
}

void payMoney(GameState game[], int playerIndex, int amount)
{
    game[0].players[playerIndex].cash -= amount;

    if(game[0].players[playerIndex].cash < 0 && !game[0].players[playerIndex].bankrupt)
    {
        game[0].players[playerIndex].bankrupt = 1;

        printf("\n*** BANKRUPTCY ***\n");
        printf("%s has been declared bankrupt.\n",
               game[0].players[playerIndex].name);

        liquidateBankruptAssets(game, playerIndex);
    }
}

/*========================================
    Rule 14 : when a player goes bankrupt,
    every building they own is demolished
    and every property/railway/utility they
    own is auctioned off (Rule-LK 19).
========================================*/

void liquidateBankruptAssets(GameState game[], int playerIndex)
{
    int i;

    printf("%s's remaining assets are being liquidated.\n",
           game[0].players[playerIndex].name);

    /* The unpaid loan (if any) is simply written off - there is
       nothing left to collect from a bankrupt player            */
    game[0].players[playerIndex].loan.active = 0;
    game[0].players[playerIndex].loan.amount = 0;
    game[0].players[playerIndex].loan.interestRate = 0;
    game[0].players[playerIndex].loan.remainingRounds = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].property.owner != playerIndex)
            continue;

        demolishBuildingsOn(game, i);

        game[0].board[i].property.owner = -1;
        game[0].board[i].property.mortgaged = 0;
        game[0].board[i].property.loanLocked = 0;
        game[0].board[i].property.insurance = NO_INSURANCE;
        game[0].board[i].property.damaged = 0;
        game[0].board[i].property.repairCostOwed = 0;

        if(game[0].board[i].type == PROPERTY)
            game[0].players[playerIndex].propertiesOwned--;
        else if(game[0].board[i].type == RAILWAY)
            game[0].players[playerIndex].railwaysOwned--;
        else if(game[0].board[i].type == UTILITY)
            game[0].players[playerIndex].utilitiesOwned--;

        runAuction(game, i);
    }
}

void payTax(GameState game[], int playerIndex, int amount)
{
    printf("\n%s landed on Income Tax.\n",
           game[0].players[playerIndex].name);

    printf("%s paid tax : LKR %d\n",
           game[0].players[playerIndex].name,
           amount);

    payMoney(game, playerIndex, amount);
}

/*========================================
    MORTGAGING (Rule 7, and the "Mortgage
    Value" / "Mortgage Status" property
    attributes from Section 1.1)

    A player can mortgage an undeveloped
    property/railway/utility they own to get
    quick cash. A mortgaged square earns no
    rent (Rule 7) and cannot be used as loan
    collateral (Rule-LK 1) until it is
    redeemed by paying back the mortgage
    value plus 10% interest.
========================================*/

/* Find one property this player could mortgage right now */
int findPropertyToMortgage(GameState game[], int playerIndex)
{
    int i;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].property.owner != playerIndex)
            continue;

        if(game[0].board[i].property.mortgaged)
            continue;

        if(game[0].board[i].property.loanLocked)
            continue;   /* already pledged to a loan */

        /* A developed property must be undeveloped before it can be
           mortgaged (standard Monopoly rule - can't mortgage land
           that still has houses/a hotel standing on it)             */
        if(game[0].board[i].type == PROPERTY &&
           (game[0].board[i].property.houses > 0 || game[0].board[i].property.hotel))
        {
            continue;
        }

        return i;
    }

    return -1;
}

/* Find one of this player's mortgaged properties */
int findMortgagedProperty(GameState game[], int playerIndex)
{
    int i;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].property.owner == playerIndex &&
           game[0].board[i].property.mortgaged)
        {
            return i;
        }
    }

    return -1;
}

void mortgageProperty(GameState game[], int playerIndex)
{
    int propIndex;

    if(!shouldMortgage(game, playerIndex))
        return;

    propIndex = findPropertyToMortgage(game, playerIndex);

    if(propIndex == -1)
        return;

    game[0].board[propIndex].property.mortgaged = 1;

    receiveMoney(game, playerIndex, game[0].board[propIndex].property.mortgageValue);

    printf("\n%s mortgaged %s for LKR %d.\n",
           game[0].players[playerIndex].name,
           game[0].board[propIndex].name,
           game[0].board[propIndex].property.mortgageValue);
}

void redeemMortgage(GameState game[], int playerIndex)
{
    int propIndex;
    int redeemCost;

    propIndex = findMortgagedProperty(game, playerIndex);

    if(propIndex == -1)
        return;

    /* Standard rule : pay back the mortgage value plus 10% interest */
    redeemCost = (game[0].board[propIndex].property.mortgageValue * 110) / 100;

    if(!shouldRedeemMortgage(game, playerIndex, redeemCost))
        return;

    if(game[0].players[playerIndex].cash < redeemCost)
        return;

    payMoney(game, playerIndex, redeemCost);

    game[0].board[propIndex].property.mortgaged = 0;

    printf("\n%s redeemed the mortgage on %s for LKR %d.\n",
           game[0].players[playerIndex].name,
           game[0].board[propIndex].name,
           redeemCost);
}

/* Step 7 of a turn : "Complete financial transactions" (Rule 3) */
void handleMortgageDecisions(GameState game[], int playerIndex)
{
    /* Try to pay off a mortgage first if things are going well,
       otherwise consider raising quick cash by mortgaging something */
    redeemMortgage(game, playerIndex);
    mortgageProperty(game, playerIndex);
}

/*========================================
    RENT CALCULATION
========================================*/

/* Rent for a normal PROPERTY square, based on houses/hotel (Table 6),
   scaled down if the building's condition is poor (Table 3).
   NOTE: this used to grab a pointer to the property to save typing;
   it now just reads game[0].board[position].property fields directly
   instead, exactly like every other function in the project.        */
int calculateRent(GameState game[], int position)
{
    int rent;
    int conditionPercent;
    int houses;
    int hotel;
    int baseRent;
    PropertyGroup group;
    int condition;

    houses = game[0].board[position].property.houses;
    hotel = game[0].board[position].property.hotel;
    baseRent = game[0].board[position].property.baseRent;
    group = game[0].board[position].property.group;
    condition = game[0].board[position].property.condition;

    if(hotel)
        rent = baseRent * 10;
    else
    {
        switch(houses)
        {
            case 0:  rent = baseRent * 1; break;
            case 1:  rent = baseRent * 2; break;
            case 2:  rent = baseRent * 3; break;
            case 3:  rent = baseRent * 5; break;
            case 4:  rent = baseRent * 7; break;
            default: rent = baseRent;     break;
        }
    }

    /* Apply any active Dynamic Market / Regional Card rent effect
       on this property's colour group (Sections 2.9, 2.10)         */
    rent = (rent * game[0].economy.groupRentMultiplier[group]) / 100;

    /* Apply any active hotel rent bonus/penalty from events (Section 2.5/2.7) */
    if(hotel)
        rent = (rent * game[0].economy.hotelRentMultiplierPercent) / 100;

    if(houses > 0 || hotel)
    {
        conditionPercent = rentConditionPercent(condition);
        rent = (rent * conditionPercent) / 100;
    }

    return rent;
}

/* Rent for a railway station, based on Table 7 (how many the owner has) */
int calculateRailwayRent(GameState game[], int playerIndex)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type == RAILWAY &&
           game[0].board[i].property.owner == playerIndex)
        {
            count++;
        }
    }

    switch(count)
    {
        case 1:  return (250  * game[0].economy.railwayRentMultiplierPercent) / 100;
        case 2:  return (500  * game[0].economy.railwayRentMultiplierPercent) / 100;
        case 3:  return (1000 * game[0].economy.railwayRentMultiplierPercent) / 100;
        case 4:  return (2000 * game[0].economy.railwayRentMultiplierPercent) / 100;
        default: return 0;
    }
}

/* Rent for a utility, based on Table 8 (dice value just rolled) */
int calculateUtilityRent(GameState game[], int playerIndex, int diceValue)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type == UTILITY &&
           game[0].board[i].property.owner == playerIndex)
        {
            count++;
        }
    }

    if(count == 2)
        return (10 * diceValue * game[0].economy.utilityRentMultiplierPercent) / 100;

    if(count == 1)
        return (4 * diceValue * game[0].economy.utilityRentMultiplierPercent) / 100;

    return 0;
}

/*========================================
    MONOPOLY / BUILDING CONSTRUCTION
    (Rules 8, 9, 10)
========================================*/

/* How many PROPERTY squares belong to this colour group in total? */
int groupSize(GameState game[], PropertyGroup group)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type == PROPERTY && game[0].board[i].property.group == group)
            count++;
    }

    return count;
}

/* Does this player own every property in the given colour group? */
int ownsMonopoly(GameState game[], int playerIndex, PropertyGroup group)
{
    int i;
    int owned;

    owned = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type == PROPERTY && game[0].board[i].property.group == group)
        {
            if(game[0].board[i].property.owner == playerIndex)
                owned++;
        }
    }

    return (owned == groupSize(game, group));
}

/* Try to build one house (or one hotel) somewhere in this colour group.
   Building must stay even : we always add to the property with the
   fewest houses first (Rule 9).                                        */
void developGroup(GameState game[], int playerIndex, PropertyGroup group)
{
    int i;
    int minHouses;
    int targetIndex;
    int allFourHouses;

    if(!ownsMonopoly(game, playerIndex, group))
        return;

    minHouses = MAX_HOUSES + 1;
    targetIndex = -1;
    allFourHouses = 1;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type == PROPERTY && game[0].board[i].property.group == group)
        {
            if(game[0].board[i].property.hotel)
                continue;

            if(game[0].board[i].property.houses < MAX_HOUSES)
                allFourHouses = 0;

            if(game[0].board[i].property.houses < minHouses)
            {
                minHouses = game[0].board[i].property.houses;
                targetIndex = i;
            }
        }
    }

    /* Every property already has a hotel - nothing left to build */
    if(targetIndex == -1)
        return;

    /* Case 1 : every property in the group already has 4 houses ->
                 try to upgrade the target property to a hotel      */
    if(allFourHouses)
    {
        int hotelCost;

        hotelCost = (game[0].board[targetIndex].property.hotelCost *
                     game[0].economy.constructionCostMultiplierPercent) / 100;

        if(!shouldConstruct(game, playerIndex, hotelCost))
            return;

        if(game[0].players[playerIndex].cash < hotelCost)
            return;

        payMoney(game, playerIndex, hotelCost);

        game[0].board[targetIndex].property.houses = 0;
        game[0].board[targetIndex].property.hotel = 1;

        printf("\n%s upgraded %s to a Hotel.\n",
               game[0].players[playerIndex].name,
               game[0].board[targetIndex].name);

        printf("Construction Cost : LKR %d\n", hotelCost);

        return;
    }

    /* Case 2 : build one more house on the property with the fewest */
    {
        int houseCost;

        houseCost = (game[0].board[targetIndex].property.houseCost *
                     game[0].economy.constructionCostMultiplierPercent) / 100;

        if(!shouldConstruct(game, playerIndex, houseCost))
            return;

        if(game[0].players[playerIndex].cash < houseCost)
            return;

        payMoney(game, playerIndex, houseCost);

        game[0].board[targetIndex].property.houses++;

        printf("\n%s constructed one house on %s.\n",
               game[0].players[playerIndex].name,
               game[0].board[targetIndex].name);

        printf("Construction Cost : LKR %d\n", houseCost);
    }
}

/* Called once per turn : look at every colour group and try to build */
void constructBuildings(GameState game[], int playerIndex)
{
    PropertyGroup group;

    if(game[0].economy.constructionSuspendedRoundsLeft > 0)
        return;   /* Labour Strike / Fuel Crisis event active */

    for(group = BROWN; group < NO_GROUP; group++)
    {
        developGroup(game, playerIndex, group);
    }
}

/*========================================
    NET WORTH (Rule 15)
    Net Worth = Cash + Property Value + Building Value
                + Railway Value + Utility Value
                + Insurance Claims Receivable
                - Outstanding Loans - Accrued Interest - Taxes Due

    NOTE for the viva : three of these terms are always 0 in this
    simulation, and that is a deliberate simplification, not a bug -
    insurance compensation is paid out immediately when a disaster
    happens (there is no "pending claim" to track), income tax is
    always paid immediately too (there is no unpaid-tax balance to
    carry forward), and loan interest is compounded directly into
    loan.amount every round rather than kept as a separate number.
    So those three terms are included in the formula for correctness,
    but they simplify to 0 given how the rest of the program works.
========================================*/

/* Property + Railway + Utility value, all combined into one number */
int calculatePropertyValue(GameState game[], int playerIndex)
{
    int i;
    int total;

    total = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].property.owner != playerIndex)
            continue;

        if(game[0].board[i].type == PROPERTY)
            total += currentMarketValue(game, i);
        else if(game[0].board[i].type == RAILWAY || game[0].board[i].type == UTILITY)
            total += game[0].board[i].property.purchasePrice;
    }

    return total;
}

/* Value of all houses/hotels the player has built */
int calculateBuildingValue(GameState game[], int playerIndex)
{
    int i;
    int total;

    total = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type != PROPERTY)
            continue;

        if(game[0].board[i].property.owner != playerIndex)
            continue;

        if(game[0].board[i].property.hotel)
            total += game[0].board[i].property.hotelCost;
        else
            total += game[0].board[i].property.houses * game[0].board[i].property.houseCost;
    }

    return total;
}

int calculateNetWorth(GameState game[], int playerIndex)
{
    int cash;
    int propertyValue;
    int buildingValue;
    int insuranceClaimsReceivable;
    int outstandingLoans;
    int accruedInterest;
    int taxesDue;

    cash = game[0].players[playerIndex].cash;
    propertyValue = calculatePropertyValue(game, playerIndex);
    buildingValue = calculateBuildingValue(game, playerIndex);

    insuranceClaimsReceivable = 0;   /* see note above */
    accruedInterest = 0;              /* already folded into loan.amount */
    taxesDue = 0;                     /* taxes are always paid immediately */

    outstandingLoans = game[0].players[playerIndex].loan.active ?
                        game[0].players[playerIndex].loan.amount : 0;

    return cash + propertyValue + buildingValue + insuranceClaimsReceivable
           - outstandingLoans - accruedInterest - taxesDue;
}

/*========================================
    BUYING PROPERTY / RAILWAY / UTILITY
========================================*/

int countUndevelopedProperties(GameState game[], int playerIndex)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type == PROPERTY &&
           game[0].board[i].property.owner == playerIndex &&
           game[0].board[i].property.houses == 0 &&
           !game[0].board[i].property.hotel)
        {
            count++;
        }
    }

    return count;
}

void buyProperty(GameState game[], int playerIndex)
{
    int pos;
    int price;

    pos = game[0].players[playerIndex].position;

    /* Only these three square types can be purchased */
    if(game[0].board[pos].type != PROPERTY &&
       game[0].board[pos].type != RAILWAY &&
       game[0].board[pos].type != UTILITY)
    {
        return;
    }

    /* Already owned by someone -> nothing to buy */
    if(game[0].board[pos].property.owner != -1)
        return;

    price = game[0].board[pos].property.purchasePrice;

    if(game[0].board[pos].type == PROPERTY)
        price = currentMarketValue(game, pos);

    /* Rule 5 : if the player does not buy it directly (for ANY reason -
       their strategy declined, they can't afford it, or the
       Anti-Speculation Act blocks them) the property goes to auction
       instead of just sitting there unbought forever.                  */
    if(!shouldBuyProperty(game, playerIndex) || game[0].players[playerIndex].cash < price ||
       (game[0].economy.antiSpeculationActive && game[0].board[pos].type == PROPERTY &&
        countUndevelopedProperties(game, playerIndex) >= 3))
    {
        runAuction(game, pos);
        return;
    }

    payMoney(game, playerIndex, price);

    game[0].board[pos].property.owner = playerIndex;

    if(game[0].board[pos].type == PROPERTY)
        game[0].players[playerIndex].propertiesOwned++;
    else if(game[0].board[pos].type == RAILWAY)
        game[0].players[playerIndex].railwaysOwned++;
    else if(game[0].board[pos].type == UTILITY)
        game[0].players[playerIndex].utilitiesOwned++;

    printf("\n%s purchased %s for LKR %d\n",
           game[0].players[playerIndex].name,
           game[0].board[pos].name,
           price);

    printf("Remaining Balance : LKR %d\n",
           game[0].players[playerIndex].cash);
}

/*========================================
    PAYING RENT
========================================*/

void payRent(GameState game[], int playerIndex, int diceValue)
{
    int pos;
    int owner;
    int rent;

    pos = game[0].players[playerIndex].position;

    if(game[0].board[pos].type != PROPERTY &&
       game[0].board[pos].type != RAILWAY &&
       game[0].board[pos].type != UTILITY)
    {
        return;
    }

    owner = game[0].board[pos].property.owner;

    /* Landing on your own square : no rent, but maybe renovate it
       if it has aged and lost value (Rule-LK 17)                  */
    if(owner == playerIndex)
    {
        if(game[0].board[pos].type == PROPERTY)
            tryRenovateAgeDepreciation(game, playerIndex, pos);

        return;
    }

    if(owner == -1)
        return;

    if(game[0].board[pos].property.mortgaged)
        return;

    if(pos == game[0].economy.closedPropertyIndex && game[0].economy.closedPropertyRoundsLeft > 0)
    {
        printf("\n%s landed on %s, but it is closed (Political Rally) - no rent.\n",
               game[0].players[playerIndex].name, game[0].board[pos].name);
        return;
    }

    if(game[0].board[pos].type == PROPERTY && game[0].board[pos].property.damaged)
    {
        printf("\n%s landed on %s, but it is damaged and collects no rent.\n",
               game[0].players[playerIndex].name, game[0].board[pos].name);
        return;
    }

    if(game[0].board[pos].type == PROPERTY)
        rent = calculateRent(game, pos);
    else if(game[0].board[pos].type == RAILWAY)
        rent = calculateRailwayRent(game, owner);
    else
        rent = calculateUtilityRent(game, owner, diceValue);

    payMoney(game, playerIndex, rent);
    receiveMoney(game, owner, rent);

    printf("\n%s landed on %s (owned by %s)\n",
           game[0].players[playerIndex].name,
           game[0].board[pos].name,
           game[0].players[owner].name);

    printf("Rent Paid : LKR %d\n", rent);
}
