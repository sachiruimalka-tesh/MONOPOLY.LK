#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include "types.h"

/*=============================
        board.c
=============================*/

void initializeBoard(void);
void displayBoard(void);

void setProperty(int index,
                 char name[],
                 PropertyGroup group,
                 int purchasePrice,
                 int baseRent,
                 int mortgageValue,
                 int houseCost,
                 int hotelCost);

void setRailway(int index, char name[], int purchasePrice);
void setUtility(int index, char name[], int purchasePrice);

void setSpecialSquare(int index,
                      SquareType type,
                      char name[]);

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

void payRent(int playerIndex, int diceValue);

void payTax(int playerIndex, int amount);

void payMoney(int playerIndex, int amount);

void receiveMoney(int playerIndex, int amount);

int calculateRent(int position);
int calculateRailwayRent(int playerIndex);
int calculateUtilityRent(int playerIndex, int diceValue);

/*=============================
        game.c
=============================*/

void startGame(void);

void playGame(void);

void playTurn(int playerIndex);

void movePlayer(int playerIndex,
                int dice);

int rollDice(void);

int handleJail(int playerIndex);

void determineTurnOrder(void);

void displayRoundSummary(int round);

int countSolventPlayers(void);

/*=============================
        events.c
=============================*/

void executeEvent(int playerIndex);

#endif