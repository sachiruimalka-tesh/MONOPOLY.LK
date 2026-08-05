#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "functions.h"
int rollDice(void)
{
    int die1 = rand() % 6 + 1;
    int die2 = rand() % 6 + 1;

    return die1 + die2;
}
void movePlayer(int playerIndex,
                int dice)
{
    int oldPosition;

    oldPosition = players[playerIndex].position;

    players[playerIndex].position =
        (oldPosition + dice) % BOARD_SIZE;

    if(oldPosition + dice >= BOARD_SIZE)
    {
        receiveMoney(playerIndex, GO_MONEY);

        printf("%s passed GO and received LKR %d\n",
               players[playerIndex].name,
               GO_MONEY);
    }

    printf("%s moved to %s\n",
           players[playerIndex].name,
           board[players[playerIndex].position].name);
}
void playTurn(int playerIndex)
{
    int dice;
    int pos;

    if(players[playerIndex].bankrupt)
        return;

    printf("\n----------------------------------\n");
    printf("%s's Turn\n",
           players[playerIndex].name);

    dice = rollDice();

    printf("Dice : %d\n",
           dice);

    movePlayer(playerIndex,
               dice);
    pos = players[playerIndex].position;
    
switch(board[pos].type)
{
    case PROPERTY:

        payRent(playerIndex);
        buyProperty(playerIndex);
        break;

    case EVENT:

        executeEvent(playerIndex);
        break;

    case TAX:

        payTax(playerIndex,1000);
        break;

    default:

        break;
}
}

    payRent(playerIndex);

    buyProperty(playerIndex);
}
void determineTurnOrder(void)
{
    printf("\nGame Started\n");
}
void playGame(void)
{
    int round;
    int i;

    srand((unsigned)time(NULL));

    determineTurnOrder();

    for(round = 1;
        round <= MAX_ROUNDS;
        round++)
    {
        printf("\n=====================================\n");
        printf("ROUND %d\n",
               round);
        printf("=====================================\n");

        for(i = 0;
            i < MAX_PLAYERS;
            i++)
        {
            playTurn(i);
        }

        /* Temporary stop for testing */

        if(round == 5)
            break;
    }
}
