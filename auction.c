#include <stdio.h>
#include "types.h"
#include "functions.h"

/*========================================
    GLOBAL VARIABLES
========================================*/

extern Player players[MAX_PLAYERS];
extern Square board[BOARD_SIZE];

/*========================================
    What price should the auction open at?
    (Rule-LK 19 : 50% of market value)
========================================*/

int getAskingValue(int propIndex)
{
    if(board[propIndex].type == PROPERTY)
        return currentMarketValue(propIndex);

    return board[propIndex].property.purchasePrice;
}

/*========================================
    RUN AN AUCTION FOR ONE SQUARE
    (Rule-LK 19 - 23)
========================================*/

void runAuction(int propIndex)
{
    int active[MAX_PLAYERS];
    int activeCount;
    int i;
    int currentBid;
    int highBidder;
    int candidateBid;
    int safetyRounds;

    printf("\n*** AUCTION ***\n");
    printf("Property : %s\n", board[propIndex].name);

    currentBid = getAskingValue(propIndex) / 2;
    printf("Opening Bid : LKR %d\n", currentBid);

    highBidder = -1;
    activeCount = 0;

    for(i = 0; i < MAX_PLAYERS; i++)
    {
        active[i] = !players[i].bankrupt;

        if(active[i])
            activeCount++;
    }

    /* safetyRounds just stops any theoretical infinite loop -
       in practice everyone withdraws within a handful of passes */
    safetyRounds = 0;

    while(activeCount > 1 && safetyRounds < 200)
    {
        for(i = 0; i < MAX_PLAYERS; i++)
        {
            if(!active[i])
                continue;

            if(activeCount <= 1)
                break;

            candidateBid = currentBid + 250;   /* Rule-LK 20 */

            if(willingToBid(i, propIndex, candidateBid))
            {
                currentBid = candidateBid;
                highBidder = i;

                printf("%s bids LKR %d.\n", players[i].name, currentBid);
            }
            else
            {
                active[i] = 0;
                activeCount--;

                printf("%s withdraws.\n", players[i].name);
            }
        }

        safetyRounds++;
    }

    /* Rule-LK 23 : nobody ever bid -> stays with the Bank */
    if(highBidder == -1)
    {
        printf("No bids received. %s remains with the Bank.\n",
               board[propIndex].name);
        return;
    }

    payMoney(highBidder, currentBid);

    board[propIndex].property.owner = highBidder;

    if(board[propIndex].type == PROPERTY)
        players[highBidder].propertiesOwned++;
    else if(board[propIndex].type == RAILWAY)
        players[highBidder].railwaysOwned++;
    else if(board[propIndex].type == UTILITY)
        players[highBidder].utilitiesOwned++;

    printf("%s wins the auction for LKR %d.\n",
           players[highBidder].name, currentBid);
}
