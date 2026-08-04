#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include "types.h"

/*=============================
        board.c
=============================*/

void initializeBoard(void);
void displayBoard(void);

void setProperty(int index,
                 const char *name,
                 PropertyGroup group,
                 int purchasePrice,
                 int baseRent,
                 int mortgageValue,
                 int houseCost,
                 int hotelCost);

void setRailway(int index, const char *name);
void setUtility(int index, const char *name);

void setSpecialSquare(int index,
                      SquareType type,
                      const char *name);

/*=============================
        players.c
=============================*/

void initializePlayers(void);
void displayPlayers(void);

int shouldBuyProperty(int playerIndex);

/*=============================
        finance.c
=============================*/

void buyProperty(int playerIndex);

void payRent(int playerIndex);

void payTax(int playerIndex, int amount);

void payMoney(int playerIndex, int amount);

void receiveMoney(int playerIndex, int amount);

int calculateRent(int position);

/*=============================
        game.c
=============================*/

void playGame(void);

void playTurn(int playerIndex);

void movePlayer(int playerIndex,
                int dice);

int rollDice(void);

void determineTurnOrder(void);

/*=============================
        events.c
=============================*/

void executeEvent(int playerIndex);

#endif