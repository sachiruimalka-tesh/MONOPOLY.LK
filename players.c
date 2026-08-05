#include <stdio.h>
#include <string.h>
#include "types.h"
#include "functions.h"

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

        players[i].sufferedLoss = 0;
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

/*========================================
    Should this player build a house/hotel
    right now, given its cost?
    (Section 3 - construction preferences)
========================================*/

int shouldConstruct(int playerIndex, int cost)
{
    switch(players[playerIndex].strategy)
    {
        case AGGRESSIVE_INVESTOR:

            /* Builds aggressively, just keep a small safety margin */

            return (players[playerIndex].cash - cost >= 1000);

        case CONSERVATIVE_BANKER:

            /* Cautious - never develops hotels while a loan is active,
               and always keeps at least 50% of cash in hand          */

            if(players[playerIndex].loan.active)
                return 0;

            return (players[playerIndex].cash - cost >=
                    players[playerIndex].cash / 2);

        case RISK_TAKER:

            /* Builds as early as possible, only limited by cash */

            return (players[playerIndex].cash >= cost);

        case OPPORTUNISTIC_TRADER:

            /* Moderate - build only if it still leaves a fair reserve */

            return (players[playerIndex].cash - cost >=
                    players[playerIndex].cash * 40 / 100);

        default:

            return 0;
    }
}

/*========================================
    Does this player want to take out a loan
    right now? (Section 3 - loan preferences)
========================================*/

int wantsLoan(int playerIndex)
{
    switch(players[playerIndex].strategy)
    {
        case AGGRESSIVE_INVESTOR:

            /* Borrows whenever it can, to fund more rental income */

            return 1;

        case CONSERVATIVE_BANKER:

            /* Avoids loans unless bankruptcy is close */

            return (players[playerIndex].cash < 1000);

        case RISK_TAKER:

            /* Always borrows the maximum permitted */

            return 1;

        case OPPORTUNISTIC_TRADER:

            /* Borrows only when cash is starting to run low */

            return (players[playerIndex].cash < 5000);

        default:

            return 0;
    }
}

/*========================================
    Does this player want to repay some of
    their loan right now?
========================================*/

int wantsToRepayLoan(int playerIndex)
{
    int loanAmount;

    loanAmount = players[playerIndex].loan.amount;

    switch(players[playerIndex].strategy)
    {
        case AGGRESSIVE_INVESTOR:

            /* Only repays once cash is more than double the loan */

            return (players[playerIndex].cash >= 2 * loanAmount);

        case CONSERVATIVE_BANKER:

            /* Repays immediately whenever possible */

            return (players[playerIndex].cash >= loanAmount);

        case RISK_TAKER:

            /* Rarely repays - prefers to keep using the cash */

            return (players[playerIndex].cash >= 5 * loanAmount);

        case OPPORTUNISTIC_TRADER:

            return (players[playerIndex].cash >= (loanAmount * 3) / 2);

        default:

            return 0;
    }
}

/*========================================
    What insurance policy (if any) does this
    player want for a given property?
    Returns NO_INSURANCE if they don't want one.
    (Section 3 - insurance preferences)
========================================*/

InsuranceType desiredInsurance(int playerIndex, int propIndex)
{
    int hasHotel;
    int purchasePrice;

    hasHotel = board[propIndex].property.hotel;
    purchasePrice = board[propIndex].property.purchasePrice;

    switch(players[playerIndex].strategy)
    {
        case AGGRESSIVE_INVESTOR:

            /* Basic Insurance for houses, Comprehensive for hotels */

            if(hasHotel)
                return COMPREHENSIVE_INSURANCE;

            return BASIC_INSURANCE;

        case CONSERVATIVE_BANKER:

            /* Always Comprehensive, for every developed property */

            return COMPREHENSIVE_INSURANCE;

        case RISK_TAKER:

            /* Only starts insuring after already suffering a loss */

            if(players[playerIndex].sufferedLoss)
                return BASIC_INSURANCE;

            return NO_INSURANCE;

        case OPPORTUNISTIC_TRADER:

            /* Only insures high-value developments */

            if(purchasePrice >= 6000)
                return COMPREHENSIVE_INSURANCE;

            return NO_INSURANCE;

        default:

            return NO_INSURANCE;
    }
}
