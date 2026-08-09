#include <stdio.h>
#include "types.h"
#include "functions.h"

/*========================================
    NOTE: no global variables, no pointers - everything reads and
    writes through the GameState array parameter `game`.
========================================*/

/*========================================
    What price should the auction open at?
    (Rule-LK 19 : 50% of market value)
========================================*/

int getAskingValue(GameState game[], int propIndex)
{
    if(game[0].board[propIndex].type == PROPERTY)
        return currentMarketValue(game, propIndex);

    return game[0].board[propIndex].property.purchasePrice;
}

/*========================================
    RUN AN AUCTION FOR ONE SQUARE
    (Rule-LK 19 - 23)
========================================*/

void runAuction(GameState game[], int propIndex)
{
    int active[MAX_PLAYERS];
    int activeCount;
    int i;
    int currentBid;
    int highBidder;
    int candidateBid;
    int safetyRounds;

    printf("\n*** AUCTION ***\n");
    printf("Property : %s\n", game[0].board[propIndex].name);

    currentBid = getAskingValue(game, propIndex) / 2;
    printf("Opening Bid : LKR %d\n", currentBid);

    highBidder = -1;
    activeCount = 0;

    for(i = 0; i < MAX_PLAYERS; i++)
    {
        active[i] = !game[0].players[i].bankrupt;

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

            if(willingToBid(game, i, propIndex, candidateBid))
            {
                currentBid = candidateBid;
                highBidder = i;

                printf("%s bids LKR %d.\n", game[0].players[i].name, currentBid);
            }
            else
            {
                active[i] = 0;
                activeCount--;

                printf("%s withdraws.\n", game[0].players[i].name);
            }
        }

        safetyRounds++;
    }

    /* Rule-LK 23 : nobody ever bid -> stays with the Bank */
    if(highBidder == -1)
    {
        printf("No bids received. %s remains with the Bank.\n",
               game[0].board[propIndex].name);
        return;
    }

    payMoney(game, highBidder, currentBid);

    game[0].board[propIndex].property.owner = highBidder;

    if(game[0].board[propIndex].type == PROPERTY)
        game[0].players[highBidder].propertiesOwned++;
    else if(game[0].board[propIndex].type == RAILWAY)
        game[0].players[highBidder].railwaysOwned++;
    else if(game[0].board[propIndex].type == UTILITY)
        game[0].players[highBidder].utilitiesOwned++;

    printf("%s wins the auction for LKR %d.\n",
           game[0].players[highBidder].name, currentBid);
}
