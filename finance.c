#include <stdio.h>
#include "types.h"

/*========================================
        GLOBAL VARIABLES
========================================*/

extern Player players[MAX_PLAYERS];
extern Square board[BOARD_SIZE];

/*========================================
        FUNCTION PROTOTYPES
========================================*/

void buyProperty(int playerIndex);
void payRent(int playerIndex);
void payTax(int playerIndex, int amount);
void receiveMoney(int playerIndex, int amount);
void payMoney(int playerIndex, int amount);
int calculateRent(int position);
void receiveMoney(int playerIndex, int amount)
{
    players[playerIndex].cash += amount;
}
void payMoney(int playerIndex, int amount)
{
    players[playerIndex].cash -= amount;

    if(players[playerIndex].cash < 0)
    {
        players[playerIndex].bankrupt = 1;

        printf("%s is BANKRUPT!\n",
               players[playerIndex].name);
    }
}
void payTax(int playerIndex, int amount)
{
    printf("%s paid tax : LKR %d\n",
           players[playerIndex].name,
           amount);

    payMoney(playerIndex, amount);
}
int calculateRent(int position)
{
    Property *p;

    p = &board[position].property;

    if(p->hotel)
        return p->baseRent * 10;

    switch(p->houses)
    {
        case 0:
            return p->baseRent;

        case 1:
            return p->baseRent * 2;

        case 2:
            return p->baseRent * 3;

        case 3:
            return p->baseRent * 5;

        case 4:
            return p->baseRent * 7;

        default:
            return p->baseRent;
    }
}
int shouldBuyProperty(int playerIndex);

void buyProperty(int playerIndex)
{
    int pos;

    pos = players[playerIndex].position;

    if(board[pos].type != PROPERTY)
        return;

    if(board[pos].property.owner != -1)
        return;

    if(!shouldBuyProperty(playerIndex))
        return;

    if(players[playerIndex].cash <
       board[pos].property.purchasePrice)
        return;

    payMoney(playerIndex,
             board[pos].property.purchasePrice);

    board[pos].property.owner = playerIndex;

    players[playerIndex].propertiesOwned++;

    printf("\n%s purchased %s\n",
           players[playerIndex].name,
           board[pos].property.name);

    printf("Price : LKR %d\n",
           board[pos].property.purchasePrice);

    printf("Balance : LKR %d\n",
           players[playerIndex].cash);
}
void payRent(int playerIndex)
{
    int pos;
    int owner;
    int rent;

    pos = players[playerIndex].position;

    if(board[pos].type != PROPERTY)
        return;

    owner = board[pos].property.owner;

    if(owner == -1)
        return;

    if(owner == playerIndex)
        return;

    if(board[pos].property.mortgaged)
        return;

    rent = calculateRent(pos);

    payMoney(playerIndex, rent);

    receiveMoney(owner, rent);

    printf("\n%s paid LKR %d rent to %s\n",
           players[playerIndex].name,
           rent,
           players[owner].name);
}
void payRent(int playerIndex)
{
    int pos;
    int owner;
    int rent;

    pos = players[playerIndex].position;

    if(board[pos].type != PROPERTY)
        return;

    owner = board[pos].property.owner;

    if(owner == -1)
        return;

    if(owner == playerIndex)
        return;

    if(board[pos].property.mortgaged)
        return;

    rent = calculateRent(pos);

    payMoney(playerIndex, rent);

    receiveMoney(owner, rent);

    printf("\n%s paid LKR %d rent to %s\n",
           players[playerIndex].name,
           rent,
           players[owner].name);
}

