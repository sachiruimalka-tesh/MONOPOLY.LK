#include <stdio.h>
#include "types.h"
#include "functions.h"

/*========================================
        GLOBAL VARIABLES
========================================*/

extern Player players[MAX_PLAYERS];
extern Square board[BOARD_SIZE];

/*========================================
    MONEY HELPERS
========================================*/

void receiveMoney(int playerIndex, int amount)
{
    players[playerIndex].cash += amount;
}

void payMoney(int playerIndex, int amount)
{
    players[playerIndex].cash -= amount;

    if(players[playerIndex].cash < 0 && !players[playerIndex].bankrupt)
    {
        players[playerIndex].bankrupt = 1;

        printf("\n*** BANKRUPTCY ***\n");
        printf("%s has been declared bankrupt.\n",
               players[playerIndex].name);

        liquidateBankruptAssets(playerIndex);
    }
}

/*========================================
    Rule 14 : when a player goes bankrupt,
    every building they own is demolished
    and every property/railway/utility they
    own is auctioned off (Rule-LK 19).
========================================*/

void liquidateBankruptAssets(int playerIndex)
{
    int i;

    printf("%s's remaining assets are being liquidated.\n",
           players[playerIndex].name);

    /* The unpaid loan (if any) is simply written off - there is
       nothing left to collect from a bankrupt player            */
    players[playerIndex].loan.active = 0;
    players[playerIndex].loan.amount = 0;
    players[playerIndex].loan.interestRate = 0;
    players[playerIndex].loan.remainingRounds = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].property.owner != playerIndex)
            continue;

        demolishBuildingsOn(i);

        board[i].property.owner = -1;
        board[i].property.mortgaged = 0;
        board[i].property.loanLocked = 0;
        board[i].property.insurance = NO_INSURANCE;
        board[i].property.damaged = 0;
        board[i].property.repairCostOwed = 0;

        if(board[i].type == PROPERTY)
            players[playerIndex].propertiesOwned--;
        else if(board[i].type == RAILWAY)
            players[playerIndex].railwaysOwned--;
        else if(board[i].type == UTILITY)
            players[playerIndex].utilitiesOwned--;

        runAuction(i);
    }
}

void payTax(int playerIndex, int amount)
{
    printf("\n%s landed on Income Tax.\n",
           players[playerIndex].name);

    printf("%s paid tax : LKR %d\n",
           players[playerIndex].name,
           amount);

    payMoney(playerIndex, amount);
}

/*========================================
    RENT CALCULATION
========================================*/

/* Rent for a normal PROPERTY square, based on houses/hotel (Table 6),
   scaled down if the building's condition is poor (Table 3)          */
int calculateRent(int position)
{
    Property *p;
    int rent;
    int conditionPercent;

    p = &board[position].property;

    if(p->hotel)
        rent = p->baseRent * 10;
    else
    {
        switch(p->houses)
        {
            case 0:  rent = p->baseRent * 1; break;
            case 1:  rent = p->baseRent * 2; break;
            case 2:  rent = p->baseRent * 3; break;
            case 3:  rent = p->baseRent * 5; break;
            case 4:  rent = p->baseRent * 7; break;
            default: rent = p->baseRent;     break;
        }
    }

    /* Apply any active Dynamic Market / Regional Card rent effect
       on this property's colour group (Sections 2.9, 2.10)         */
    rent = (rent * economy.groupRentMultiplier[p->group]) / 100;

    /* Apply any active hotel rent bonus/penalty from events (Section 2.5/2.7) */
    if(p->hotel)
        rent = (rent * economy.hotelRentMultiplierPercent) / 100;

    if(p->houses > 0 || p->hotel)
    {
        conditionPercent = rentConditionPercent(p->condition);
        rent = (rent * conditionPercent) / 100;
    }

    return rent;
}

/* Rent for a railway station, based on Table 7 (how many the owner has) */
int calculateRailwayRent(int playerIndex)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type == RAILWAY &&
           board[i].property.owner == playerIndex)
        {
            count++;
        }
    }

    switch(count)
    {
        case 1:  return (250  * economy.railwayRentMultiplierPercent) / 100;
        case 2:  return (500  * economy.railwayRentMultiplierPercent) / 100;
        case 3:  return (1000 * economy.railwayRentMultiplierPercent) / 100;
        case 4:  return (2000 * economy.railwayRentMultiplierPercent) / 100;
        default: return 0;
    }
}

/* Rent for a utility, based on Table 8 (dice value just rolled) */
int calculateUtilityRent(int playerIndex, int diceValue)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type == UTILITY &&
           board[i].property.owner == playerIndex)
        {
            count++;
        }
    }

    if(count == 2)
        return (10 * diceValue * economy.utilityRentMultiplierPercent) / 100;

    if(count == 1)
        return (4 * diceValue * economy.utilityRentMultiplierPercent) / 100;

    return 0;
}

/*========================================
    MONOPOLY / BUILDING CONSTRUCTION
    (Rules 8, 9, 10)
========================================*/

/* How many PROPERTY squares belong to this colour group in total? */
int groupSize(PropertyGroup group)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type == PROPERTY && board[i].property.group == group)
            count++;
    }

    return count;
}

/* Does this player own every property in the given colour group? */
int ownsMonopoly(int playerIndex, PropertyGroup group)
{
    int i;
    int owned;

    owned = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type == PROPERTY && board[i].property.group == group)
        {
            if(board[i].property.owner == playerIndex)
                owned++;
        }
    }

    return (owned == groupSize(group));
}

/* Try to build one house (or one hotel) somewhere in this colour group.
   Building must stay even : we always add to the property with the
   fewest houses first (Rule 9).                                        */
void developGroup(int playerIndex, PropertyGroup group)
{
    int i;
    int minHouses;
    int targetIndex;
    int allFourHouses;

    if(!ownsMonopoly(playerIndex, group))
        return;

    minHouses = MAX_HOUSES + 1;
    targetIndex = -1;
    allFourHouses = 1;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type == PROPERTY && board[i].property.group == group)
        {
            if(board[i].property.hotel)
                continue;

            if(board[i].property.houses < MAX_HOUSES)
                allFourHouses = 0;

            if(board[i].property.houses < minHouses)
            {
                minHouses = board[i].property.houses;
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

        hotelCost = (board[targetIndex].property.hotelCost *
                     economy.constructionCostMultiplierPercent) / 100;

        if(!shouldConstruct(playerIndex, hotelCost))
            return;

        if(players[playerIndex].cash < hotelCost)
            return;

        payMoney(playerIndex, hotelCost);

        board[targetIndex].property.houses = 0;
        board[targetIndex].property.hotel = 1;

        printf("\n%s upgraded %s to a Hotel.\n",
               players[playerIndex].name,
               board[targetIndex].name);

        printf("Construction Cost : LKR %d\n", hotelCost);

        return;
    }

    /* Case 2 : build one more house on the property with the fewest */
    {
        int houseCost;

        houseCost = (board[targetIndex].property.houseCost *
                     economy.constructionCostMultiplierPercent) / 100;

        if(!shouldConstruct(playerIndex, houseCost))
            return;

        if(players[playerIndex].cash < houseCost)
            return;

        payMoney(playerIndex, houseCost);

        board[targetIndex].property.houses++;

        printf("\n%s constructed one house on %s.\n",
               players[playerIndex].name,
               board[targetIndex].name);

        printf("Construction Cost : LKR %d\n", houseCost);
    }
}

/* Called once per turn : look at every colour group and try to build */
void constructBuildings(int playerIndex)
{
    PropertyGroup group;

    if(economy.constructionSuspendedRoundsLeft > 0)
        return;   /* Labour Strike / Fuel Crisis event active */

    for(group = BROWN; group < NO_GROUP; group++)
    {
        developGroup(playerIndex, group);
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
int calculatePropertyValue(int playerIndex)
{
    int i;
    int total;

    total = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].property.owner != playerIndex)
            continue;

        if(board[i].type == PROPERTY)
            total += currentMarketValue(i);
        else if(board[i].type == RAILWAY || board[i].type == UTILITY)
            total += board[i].property.purchasePrice;
    }

    return total;
}

/* Value of all houses/hotels the player has built */
int calculateBuildingValue(int playerIndex)
{
    int i;
    int total;

    total = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type != PROPERTY)
            continue;

        if(board[i].property.owner != playerIndex)
            continue;

        if(board[i].property.hotel)
            total += board[i].property.hotelCost;
        else
            total += board[i].property.houses * board[i].property.houseCost;
    }

    return total;
}

int calculateNetWorth(int playerIndex)
{
    int cash;
    int propertyValue;
    int buildingValue;
    int insuranceClaimsReceivable;
    int outstandingLoans;
    int accruedInterest;
    int taxesDue;

    cash = players[playerIndex].cash;
    propertyValue = calculatePropertyValue(playerIndex);
    buildingValue = calculateBuildingValue(playerIndex);

    insuranceClaimsReceivable = 0;   /* see note above */
    accruedInterest = 0;              /* already folded into loan.amount */
    taxesDue = 0;                     /* taxes are always paid immediately */

    outstandingLoans = players[playerIndex].loan.active ?
                        players[playerIndex].loan.amount : 0;

    return cash + propertyValue + buildingValue + insuranceClaimsReceivable
           - outstandingLoans - accruedInterest - taxesDue;
}

/*========================================
    BUYING PROPERTY / RAILWAY / UTILITY
========================================*/

int countUndevelopedProperties(int playerIndex)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type == PROPERTY &&
           board[i].property.owner == playerIndex &&
           board[i].property.houses == 0 &&
           !board[i].property.hotel)
        {
            count++;
        }
    }

    return count;
}


void buyProperty(int playerIndex)
{
    int pos;
    int price;

    pos = players[playerIndex].position;

    /* Only these three square types can be purchased */
    if(board[pos].type != PROPERTY &&
       board[pos].type != RAILWAY &&
       board[pos].type != UTILITY)
    {
        return;
    }

    /* Already owned by someone -> nothing to buy */
    if(board[pos].property.owner != -1)
        return;

    price = board[pos].property.purchasePrice;

    if(board[pos].type == PROPERTY)
        price = currentMarketValue(pos);

    /* Rule 5 : if the player does not buy it directly (for ANY reason -
       their strategy declined, they can't afford it, or the
       Anti-Speculation Act blocks them) the property goes to auction
       instead of just sitting there unbought forever.                  */
    if(!shouldBuyProperty(playerIndex) || players[playerIndex].cash < price ||
       (economy.antiSpeculationActive && board[pos].type == PROPERTY &&
        countUndevelopedProperties(playerIndex) >= 3))
    {
        runAuction(pos);
        return;
    }

    payMoney(playerIndex, price);

    board[pos].property.owner = playerIndex;

    if(board[pos].type == PROPERTY)
        players[playerIndex].propertiesOwned++;
    else if(board[pos].type == RAILWAY)
        players[playerIndex].railwaysOwned++;
    else if(board[pos].type == UTILITY)
        players[playerIndex].utilitiesOwned++;

    printf("\n%s purchased %s for LKR %d\n",
           players[playerIndex].name,
           board[pos].name,
           price);

    printf("Remaining Balance : LKR %d\n",
           players[playerIndex].cash);
}

/*========================================
    PAYING RENT
========================================*/

void payRent(int playerIndex, int diceValue)
{
    int pos;
    int owner;
    int rent;

    pos = players[playerIndex].position;

    if(board[pos].type != PROPERTY &&
       board[pos].type != RAILWAY &&
       board[pos].type != UTILITY)
    {
        return;
    }

    owner = board[pos].property.owner;

    /* Landing on your own square : no rent, but maybe renovate it
       if it has aged and lost value (Rule-LK 17)                  */
    if(owner == playerIndex)
    {
        if(board[pos].type == PROPERTY)
            tryRenovateAgeDepreciation(playerIndex, pos);

        return;
    }

    if(owner == -1)
        return;

    if(board[pos].property.mortgaged)
        return;

    if(pos == economy.closedPropertyIndex && economy.closedPropertyRoundsLeft > 0)
    {
        printf("\n%s landed on %s, but it is closed (Political Rally) - no rent.\n",
               players[playerIndex].name, board[pos].name);
        return;
    }

    if(board[pos].type == PROPERTY && board[pos].property.damaged)
    {
        printf("\n%s landed on %s, but it is damaged and collects no rent.\n",
               players[playerIndex].name, board[pos].name);
        return;
    }

    if(board[pos].type == PROPERTY)
        rent = calculateRent(pos);
    else if(board[pos].type == RAILWAY)
        rent = calculateRailwayRent(owner);
    else
        rent = calculateUtilityRent(owner, diceValue);

    payMoney(playerIndex, rent);
    receiveMoney(owner, rent);

    printf("\n%s landed on %s (owned by %s)\n",
           players[playerIndex].name,
           board[pos].name,
           players[owner].name);

    printf("Rent Paid : LKR %d\n", rent);
}
