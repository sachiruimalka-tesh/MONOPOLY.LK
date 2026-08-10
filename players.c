#include <stdio.h>
#include <string.h>
#include "types.h"
#include "functions.h"

/*====================================
    NOTE: there is no global players array any more. Every function
    below receives the whole GameState as an array parameter (named `game`), and
    reads/writes game[0].players[...] instead of a global variable.
====================================*/

void initializePlayers(GameState game[])
{
    int i;

    /* Player 1 */
    strcpy(game[0].players[0].name, "Aggressive Investor");
    game[0].players[0].strategy = AGGRESSIVE_INVESTOR;

    /* Player 2 */
    strcpy(game[0].players[1].name, "Conservative Banker");
    game[0].players[1].strategy = CONSERVATIVE_BANKER;

    /* Player 3 */
    strcpy(game[0].players[2].name, "Risk Taker");
    game[0].players[2].strategy = RISK_TAKER;

    /* Player 4 */
    strcpy(game[0].players[3].name, "Opportunistic Trader");
    game[0].players[3].strategy = OPPORTUNISTIC_TRADER;

    /* Initialize common values */

    for(i = 0; i < MAX_PLAYERS; i++)
    {
        game[0].players[i].position = 0;
        game[0].players[i].cash = START_MONEY;

        game[0].players[i].inJail = 0;
        game[0].players[i].jailTurns = 0;

        game[0].players[i].bankrupt = 0;

        game[0].players[i].propertiesOwned = 0;
        game[0].players[i].railwaysOwned = 0;
        game[0].players[i].utilitiesOwned = 0;

        game[0].players[i].loan.active = 0;
        game[0].players[i].loan.amount = 0;
        game[0].players[i].loan.interestRate = 0;
        game[0].players[i].loan.remainingRounds = 0;

        game[0].players[i].sufferedLoss = 0;
    }
}

void displayPlayers(GameState game[])
{
    int i;

    printf("\n================ PLAYERS ================\n");

    for(i = 0; i < MAX_PLAYERS; i++)
    {
        printf("\nPlayer %d\n", i + 1);
        printf("Name       : %s\n", game[0].players[i].name);
        printf("Cash       : LKR %d\n", game[0].players[i].cash);
        printf("Position   : %d\n", game[0].players[i].position);
        printf("Properties : %d\n", game[0].players[i].propertiesOwned);
        printf("Railways   : %d\n", game[0].players[i].railwaysOwned);
        printf("Utilities  : %d\n", game[0].players[i].utilitiesOwned);

        if(game[0].players[i].bankrupt)
            printf("Status     : Bankrupt\n");
        else
            printf("Status     : Active\n");
    }

    printf("\n=========================================\n");
}

int shouldBuyProperty(GameState game[], int playerIndex)
{
    int price;

    price = game[0].board[game[0].players[playerIndex].position].property.purchasePrice;

    switch(game[0].players[playerIndex].strategy)
    {
        case AGGRESSIVE_INVESTOR:

            /* Buy unless almost broke */

            return (game[0].players[playerIndex].cash - price >= 1000);

        case CONSERVATIVE_BANKER:

            /* Keep at least 50% of current cash */

            return (game[0].players[playerIndex].cash - price >=
                    game[0].players[playerIndex].cash / 2);

        case RISK_TAKER:

            /* Always buy if affordable */

            return (game[0].players[playerIndex].cash >= price);

        case OPPORTUNISTIC_TRADER:

            /* Buy only cheaper properties */

            return (price <= game[0].players[playerIndex].cash * 40 / 100);

        default:

            return 0;
    }
}

/*========================================
    Should this player build a house/hotel
    right now, given its cost?
    (Section 3 - construction preferences)
========================================*/

int shouldConstruct(GameState game[], int playerIndex, int cost)
{
    switch(game[0].players[playerIndex].strategy)
    {
        case AGGRESSIVE_INVESTOR:

            /* Builds aggressively, just keep a small safety margin */

            return (game[0].players[playerIndex].cash - cost >= 1000);

        case CONSERVATIVE_BANKER:

            /* Cautious - never develops hotels while a loan is active,
               and always keeps at least 50% of cash in hand          */

            if(game[0].players[playerIndex].loan.active)
                return 0;

            return (game[0].players[playerIndex].cash - cost >=
                    game[0].players[playerIndex].cash / 2);

        case RISK_TAKER:

            /* Builds as early as possible, only limited by cash */

            return (game[0].players[playerIndex].cash >= cost);

        case OPPORTUNISTIC_TRADER:

            /* Moderate - build only if it still leaves a fair reserve */

            return (game[0].players[playerIndex].cash - cost >=
                    game[0].players[playerIndex].cash * 40 / 100);

        default:

            return 0;
    }
}

/*========================================
    Does this player want to take out a loan
    right now? (Section 3 - loan preferences)
========================================*/

int wantsLoan(GameState game[], int playerIndex)
{
    switch(game[0].players[playerIndex].strategy)
    {
        case AGGRESSIVE_INVESTOR:

            /* Borrows whenever it can, to fund more rental income */

            return 1;

        case CONSERVATIVE_BANKER:

            /* Avoids loans unless bankruptcy is close */

            return (game[0].players[playerIndex].cash < 1000);

        case RISK_TAKER:

            /* Always borrows the maximum permitted */

            return 1;

        case OPPORTUNISTIC_TRADER:

            /* Borrows only when cash is starting to run low */

            return (game[0].players[playerIndex].cash < 5000);

        default:

            return 0;
    }
}

/*========================================
    Does this player want to repay some of
    their loan right now?
========================================*/

int wantsToRepayLoan(GameState game[], int playerIndex)
{
    int loanAmount;

    loanAmount = game[0].players[playerIndex].loan.amount;

    switch(game[0].players[playerIndex].strategy)
    {
        case AGGRESSIVE_INVESTOR:

            /* Only repays once cash is more than double the loan */

            return (game[0].players[playerIndex].cash >= 2 * loanAmount);

        case CONSERVATIVE_BANKER:

            /* Repays immediately whenever possible */

            return (game[0].players[playerIndex].cash >= loanAmount);

        case RISK_TAKER:

            /* Rarely repays - prefers to keep using the cash */

            return (game[0].players[playerIndex].cash >= 5 * loanAmount);

        case OPPORTUNISTIC_TRADER:

            return (game[0].players[playerIndex].cash >= (loanAmount * 3) / 2);

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

InsuranceType desiredInsurance(GameState game[], int playerIndex, int propIndex)
{
    int hasHotel;
    int purchasePrice;

    hasHotel = game[0].board[propIndex].property.hotel;
    purchasePrice = game[0].board[propIndex].property.purchasePrice;

    switch(game[0].players[playerIndex].strategy)
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

            /* Only starts insuring after already suffering a loss.
               The spec doesn't say which policy this strategy picks,
               so : Business Interruption is the only policy that
               applies to hotels (Section 1.2), so use that for
               hotels, and the cheaper Basic policy for houses.        */

            if(!game[0].players[playerIndex].sufferedLoss)
                return NO_INSURANCE;

            if(hasHotel)
                return BUSINESS_INTERRUPTION;

            return BASIC_INSURANCE;

        case OPPORTUNISTIC_TRADER:

            /* Only insures high-value developments */

            if(purchasePrice >= 6000)
                return COMPREHENSIVE_INSURANCE;

            return NO_INSURANCE;

        default:

            return NO_INSURANCE;
    }
}

/*========================================
    Should this player renovate a property
    that has lost value to age (Rule-LK 17)?
========================================*/

int shouldRenovateAgeDepreciation(GameState game[], int playerIndex, int depreciationPercent)
{
    switch(game[0].players[playerIndex].strategy)
    {
        case CONSERVATIVE_BANKER:

            return (depreciationPercent >= 10);

        case OPPORTUNISTIC_TRADER:

            return (depreciationPercent >= 15);

        case AGGRESSIVE_INVESTOR:
        case RISK_TAKER:
        default:

            /* Not specified in the assignment for these strategies -
               a reasonable default : renovate once quite worn down  */

            return (depreciationPercent >= 20);
    }
}

/*========================================
    Should this player pay to maintain a
    building right now? (Rule-LK 27)
========================================*/

int shouldMaintain(GameState game[], int playerIndex, int condition, int cost)
{
    if(game[0].players[playerIndex].strategy == RISK_TAKER)
    {
        /* "Ignores depreciation until repair becomes unavoidable" */
        return (condition < 25 && game[0].players[playerIndex].cash >= cost);
    }

    /* Everyone else keeps a modest cash cushion while maintaining */
    return (game[0].players[playerIndex].cash - cost >=
            game[0].players[playerIndex].cash * 20 / 100);
}

/*========================================
    Is this player willing to bid this
    amount at an auction? (Section 3,
    Rule-LK 19-22)
========================================*/

int willingToBid(GameState game[], int playerIndex, int propIndex, int candidateBid)
{
    int marketValue;

    if(game[0].players[playerIndex].cash < candidateBid)
        return 0;   /* Rule-LK 22 : can never bid more than you have */

    marketValue = game[0].board[propIndex].property.purchasePrice;

    switch(game[0].players[playerIndex].strategy)
    {
        case AGGRESSIVE_INVESTOR:

            /* Bids aggressively up to 120% of market value */

            return (candidateBid <= (marketValue * 120) / 100);

        case CONSERVATIVE_BANKER:

            /* Only bids while the price is still below market value */

            return (candidateBid < marketValue);

        case RISK_TAKER:

            /* Bids until cash runs out, no other limit */

            return 1;

        case OPPORTUNISTIC_TRADER:

            /* Only wants a bargain - stops well below market value */

            return (candidateBid <= (marketValue * 80) / 100);

        default:

            return 0;
    }
}

/*========================================
    Is this player desperate enough to
    mortgage a property for quick cash?
    (Rule 7 - each strategy has a different
    idea of "desperate")
========================================*/

int shouldMortgage(GameState game[], int playerIndex)
{
    switch(game[0].players[playerIndex].strategy)
    {
        case CONSERVATIVE_BANKER:

            /* Keeps a big cash cushion, so acts early */

            return (game[0].players[playerIndex].cash < 3000);

        case RISK_TAKER:

            /* Prefers loans over mortgaging - only as a last resort */

            return (game[0].players[playerIndex].cash < 500);

        case AGGRESSIVE_INVESTOR:

            return (game[0].players[playerIndex].cash < 1000);

        case OPPORTUNISTIC_TRADER:

            return (game[0].players[playerIndex].cash < 1200);

        default:

            return 0;
    }
}

/*========================================
    Is this player comfortable enough to
    redeem (pay off) a mortgaged property?
========================================*/

int shouldRedeemMortgage(GameState game[], int playerIndex, int redeemCost)
{
    /* Simple rule for everyone : only redeem if there's still a
       healthy amount of cash left over afterwards                */
    return (game[0].players[playerIndex].cash - redeemCost >= redeemCost);
}

/*========================================
    Does this player choose to voluntarily
    pay bail to leave jail immediately,
    rather than gambling on rolling doubles?
    (Rule 13 - paying bail is available on
    ANY turn in jail, not just as a last
    resort. The assignment doesn't specify
    which strategies prefer which option, so
    this is a documented, reasonable
    assumption per strategy.)
========================================*/

int shouldPayBail(GameState game[], int playerIndex)
{
    switch(game[0].players[playerIndex].strategy)
    {
        case CONSERVATIVE_BANKER:

            /* Cautious - doesn't like wasting turns stuck in jail,
               pays immediately if it can comfortably afford to     */

            return (game[0].players[playerIndex].cash >= 1500);

        case RISK_TAKER:

            /* Prefers to gamble on doubles rather than spend money -
               only ever pays via the forced 3-turn rule            */

            return 0;

        case AGGRESSIVE_INVESTOR:
        case OPPORTUNISTIC_TRADER:

            /* Pays if cash is healthy, otherwise tries for doubles
               first to save the money for investing                */

            return (game[0].players[playerIndex].cash >= 5000);

        default:

            return 0;
    }
}
