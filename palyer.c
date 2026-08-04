#include <stdio.h>
#include <string.h>
#include "types.h"

/*====================================
        GLOBAL PLAYERS
====================================*/

Player players[MAX_PLAYERS];

/*====================================
    FUNCTION PROTOTYPES
====================================*/

void initializePlayers(void);
void displayPlayers(void);
int shouldBuyProperty(int playerIndex);

void initializePlayers(void)
{
    /* Player 1 */
    strcpy(players[0].name, "Aggressive Investor");
    players[0].strategy = AGGRESSIVE_INVESTOR;

    /* Player 2 */
    strcpy(players[1].name, "Conservative Banker");
    players[1].strategy = CONSERVATIVE_BANKER;

    /* Player 3 */
    strcpy(players[2].name, "Risk Taker");
    players[2].strategy = RISK_TAKER;

    /* Player 4 */
    strcpy(players[3].name, "Opportunistic Trader");
    players[3].strategy = OPPORTUNISTIC_TRADER;

    /* Initialize common values */

    for(int i = 0; i < MAX_PLAYERS; i++)
    {
        players[i].position = 0;
        players[i].cash = START_MONEY;

        players[i].inJail = 0;
        players[i].jailTurns = 0;

        players[i].bankrupt = 0;

        players[i].propertiesOwned = 0;
        players[i].railwaysOwned = 0;
        players[i].utilitiesOwned = 0;

        players[i].loan.active = 0;
        players[i].loan.amount = 0;
        players[i].loan.interestRate = 0;
        players[i].loan.remainingRounds = 0;
    }
}

void displayPlayers(void)
{
    int i;

    printf("\n================ PLAYERS ================\n");

    for(i = 0; i < MAX_PLAYERS; i++)
    {
        printf("\nPlayer %d\n", i + 1);
        printf("Name       : %s\n", players[i].name);
        printf("Cash       : LKR %d\n", players[i].cash);
        printf("Position   : %d\n", players[i].position);
        printf("Properties : %d\n", players[i].propertiesOwned);
        printf("Railways   : %d\n", players[i].railwaysOwned);
        printf("Utilities  : %d\n", players[i].utilitiesOwned);

        if(players[i].bankrupt)
            printf("Status     : Bankrupt\n");
        else
            printf("Status     : Active\n");
    }

    printf("\n=========================================\n");
}

int shouldBuyProperty(int playerIndex)
{
    int price;

    price = board[players[playerIndex].position].property.purchasePrice;

    switch(players[playerIndex].strategy)
    {
        case AGGRESSIVE_INVESTOR:

            /* Buy unless almost broke */

            return (players[playerIndex].cash - price >= 1000);

        case CONSERVATIVE_BANKER:

            /* Keep at least 50% of current cash */

            return (players[playerIndex].cash - price >=
                    players[playerIndex].cash / 2);

        case RISK_TAKER:

            /* Always buy if affordable */

            return (players[playerIndex].cash >= price);

        case OPPORTUNISTIC_TRADER:

            /* Buy only cheaper properties */

            return (price <= players[playerIndex].cash * 40 / 100);

        default:

            return 0;
    }
}

