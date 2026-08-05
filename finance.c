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
    rent = (rent * groupRentMultiplier[p->group]) / 100;

    /* Apply any active hotel rent bonus/penalty from events (Section 2.5/2.7) */
    if(p->hotel)
        rent = (rent * hotelRentMultiplierPercent) / 100;

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
        case 1:  return (250  * railwayRentMultiplierPercent) / 100;
        case 2:  return (500  * railwayRentMultiplierPercent) / 100;
        case 3:  return (1000 * railwayRentMultiplierPercent) / 100;
        case 4:  return (2000 * railwayRentMultiplierPercent) / 100;
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
        return (10 * diceValue * utilityRentMultiplierPercent) / 100;

    if(count == 1)
        return (4 * diceValue * utilityRentMultiplierPercent) / 100;

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
                     constructionCostMultiplierPercent) / 100;

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
                     constructionCostMultiplierPercent) / 100;

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

    if(constructionSuspendedRoundsLeft > 0)
        return;   /* Labour Strike / Fuel Crisis event active */

    for(group = BROWN; group < NO_GROUP; group++)
    {
        developGroup(playerIndex, group);
    }
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

    if(!shouldBuyProperty(playerIndex))
        return;

    if(antiSpeculationActive && board[pos].type == PROPERTY)
    {
        if(countUndevelopedProperties(playerIndex) >= 3)
            return;   /* Rule-LK 24 : Anti-Speculation Act */
    }

    price = board[pos].property.purchasePrice;

    if(board[pos].type == PROPERTY)
        price = currentMarketValue(pos);

    if(players[playerIndex].cash < price)
        return;

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

    if(pos == closedPropertyIndex && closedPropertyRoundsLeft > 0)
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
