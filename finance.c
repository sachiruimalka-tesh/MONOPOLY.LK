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

/* Rent for a normal PROPERTY square, based on houses/hotel (Table 6) */
int calculateRent(int position)
{
    Property *p;

    p = &board[position].property;

    if(p->hotel)
        return p->baseRent * 10;

    switch(p->houses)
    {
        case 0:  return p->baseRent * 1;
        case 1:  return p->baseRent * 2;
        case 2:  return p->baseRent * 3;
        case 3:  return p->baseRent * 5;
        case 4:  return p->baseRent * 7;
        default: return p->baseRent;
    }
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
        case 1:  return 250;
        case 2:  return 500;
        case 3:  return 1000;
        case 4:  return 2000;
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
        return 10 * diceValue;

    if(count == 1)
        return 4 * diceValue;

    return 0;
}

/*========================================
    BUYING PROPERTY / RAILWAY / UTILITY
========================================*/

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

    price = board[pos].property.purchasePrice;

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

    /* Unowned, or player landed on their own square -> no rent */
    if(owner == -1 || owner == playerIndex)
        return;

    if(board[pos].property.mortgaged)
        return;

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
