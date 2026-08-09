#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "types.h"
#include "functions.h"

/*========================================
    NOTE: no global variables, no pointers - everything reads and
    writes through the GameState array parameter `game`.
========================================*/

/*========================================
    DICE
    (This doesn't touch the game state at all, so it doesn't need
    the `game` parameter.)
========================================*/

int rollDice(void)
{
    int die1 = rand() % 6 + 1;
    int die2 = rand() % 6 + 1;

    return die1 + die2;
}

/*========================================
    MOVEMENT
    Returns 1 if this move passed or landed
    on GO, 0 otherwise - the round-counting
    logic in playGame() needs to know this.
========================================*/

int movePlayer(GameState game[], int playerIndex, int dice)
{
    int oldPosition;
    int passedGo;

    oldPosition = game[0].players[playerIndex].position;

    game[0].players[playerIndex].position = (oldPosition + dice) % BOARD_SIZE;

    printf("%s moves from Square %d to Square %d (%s)\n",
           game[0].players[playerIndex].name,
           oldPosition,
           game[0].players[playerIndex].position,
           game[0].board[game[0].players[playerIndex].position].name);

    passedGo = 0;

    /* Passed or landed exactly on GO */
    if(oldPosition + dice >= BOARD_SIZE)
    {
        passedGo = 1;

        receiveMoney(game, playerIndex, GO_MONEY);

        printf("%s passed GO and collected LKR %d\n",
               game[0].players[playerIndex].name,
               GO_MONEY);

        printf("Current Balance : LKR %d\n",
               game[0].players[playerIndex].cash);
    }

    return passedGo;
}

/*========================================
    JAIL
    Return codes:
      0 = player was not in jail - proceed with a normal turn
      1 = player is still stuck in jail (or just paid bail) -
          the turn ends right here, with no movement at all
      2 = player rolled doubles, escaped, and that escape move
          passed GO (a normal turn still follows, same as before)
      3 = player rolled doubles, escaped, but did NOT pass GO
========================================*/

int handleJail(GameState game[], int playerIndex)
{
    int die1, die2;
    int passedGo;

    if(!game[0].players[playerIndex].inJail)
        return 0;

    die1 = rand() % 6 + 1;
    die2 = rand() % 6 + 1;

    printf("%s is in Jail. Rolled %d and %d.\n",
           game[0].players[playerIndex].name, die1, die2);

    if(die1 == die2)
    {
        printf("Doubles! %s is released from Jail.\n",
               game[0].players[playerIndex].name);

        game[0].players[playerIndex].inJail = 0;
        game[0].players[playerIndex].jailTurns = 0;

        passedGo = movePlayer(game, playerIndex, die1 + die2);

        if(passedGo)
            return 2;

        return 3;
    }

    game[0].players[playerIndex].jailTurns++;

    if(game[0].players[playerIndex].jailTurns >= 3)
    {
        printf("%s pays bail of LKR %d and is released from Jail.\n",
               game[0].players[playerIndex].name, JAIL_BAIL);

        payMoney(game, playerIndex, JAIL_BAIL);

        game[0].players[playerIndex].inJail = 0;
        game[0].players[playerIndex].jailTurns = 0;

        /* Player is released but does not move this turn */
        return 1;
    }

    printf("%s remains in Jail (%d/3 turns).\n",
           game[0].players[playerIndex].name,
           game[0].players[playerIndex].jailTurns);

    return 1;
}

/*========================================
    ONE PLAYER'S TURN
    Returns 1 if the player passed/landed on
    GO at any point during this turn, 0 if not.
========================================*/

int playTurn(GameState game[], int playerIndex)
{
    int dice;
    int pos;
    int passedGo;
    int jailResult;

    if(game[0].players[playerIndex].bankrupt)
        return 0;

    printf("\n----------------------------------\n");
    printf("%s's Turn\n", game[0].players[playerIndex].name);

    /* Step 1 : Resolve outstanding penalties (jail, damaged buildings) */
    tryAutoRepair(game, playerIndex);
    performMaintenance(game, playerIndex);
    renovateStructuralDamage(game, playerIndex);

    passedGo = 0;

    jailResult = handleJail(game, playerIndex);

    if(jailResult == 1)
        return 0;   /* still stuck in jail (or just paid bail) - turn over */

    if(jailResult == 2)
        passedGo = 1;   /* escaped via doubles, and that move passed GO */

    /* Step 2 & 3 : Roll dice and move (this always happens, even right
       after escaping jail via doubles - matches the traditional rule
       that you then still take a normal turn straight away)          */
    dice = rollDice();
    printf("%s rolled %d.\n", game[0].players[playerIndex].name, dice);

    if(movePlayer(game, playerIndex, dice))
        passedGo = 1;

    /* Step 4 : Resolve landing action */
    pos = game[0].players[playerIndex].position;

    switch(game[0].board[pos].type)
    {
        case PROPERTY:
        case RAILWAY:
        case UTILITY:

            payRent(game, playerIndex, dice);
            buyProperty(game, playerIndex);
            break;

        case EVENT:

            executeEvent(game, playerIndex);
            break;

        case TAX:

            payTax(game, playerIndex, game[0].economy.incomeTaxAmount);
            break;

        case GO_TO_JAIL:

            printf("%s is sent to Jail!\n", game[0].players[playerIndex].name);
            game[0].players[playerIndex].position = 10;
            game[0].players[playerIndex].inJail = 1;
            game[0].players[playerIndex].jailTurns = 0;
            break;

        case BANK:

            handleBankVisit(game, playerIndex);
            break;

        case INSURANCE:

            handleInsuranceVisit(game, playerIndex);
            break;

        default:

            /* GO, JAIL (just visiting), FREE_PARKING */
            break;
    }

    /* Step 6 : Construct buildings if eligible (Rules 8, 9, 10) */
    constructBuildings(game, playerIndex);

    /* Step 7 : Complete financial transactions (Rule 3) - mortgage or
       redeem a property if the player's situation calls for it       */
    handleMortgageDecisions(game, playerIndex);

    return passedGo;
}

/*========================================
    TURN ORDER (Rule 2)

    Only players who are ACTUALLY TIED with each other re-roll -
    anyone whose rank is already clear from the first roll keeps it.
    For example, if Aggressive=9, Conservative=7, Risk=4,
    Opportunistic=7 : Aggressive is locked into 1st place and Risk is
    locked into last place immediately. Only Conservative and
    Opportunistic (tied at 7) roll again against each other to decide
    2nd and 3rd place. This is done with a small recursive helper,
    resolveGroup(), which resolves one group of (possibly tied)
    players into a strict order, and calls itself again for any
    smaller tied sub-group it finds.
========================================*/

/* Resolves one group of (possibly tied) players into a strict order,
   writing the result into output[] starting at position startIndex.
   Returns how many players it wrote - this replaces using a pointer
   to a shared counter: the caller just adds up the return value
   instead of a function reaching back and modifying the caller's
   variable directly.                                                */
int resolveGroup(GameState game[], int groupPlayers[], int groupSize,
                  int output[], int startIndex)
{
    int rolls[MAX_PLAYERS];
    int i, j, k, temp;
    int runStart, runLength;
    int tiedPlayers[MAX_PLAYERS];
    int written;

    written = 0;

    for(i = 0; i < groupSize; i++)
    {
        rolls[i] = rollDice();
        printf("%s rolls %d.\n", game[0].players[groupPlayers[i]].name, rolls[i]);
    }

    /* Sort this group's players by roll, highest first (a simple
       bubble sort - swap neighbours if they're in the wrong order,
       moving both the roll and the matching player index together) */
    for(i = 0; i < groupSize - 1; i++)
    {
        for(j = 0; j < groupSize - 1 - i; j++)
        {
            if(rolls[j] < rolls[j + 1])
            {
                temp = rolls[j];
                rolls[j] = rolls[j + 1];
                rolls[j + 1] = temp;

                temp = groupPlayers[j];
                groupPlayers[j] = groupPlayers[j + 1];
                groupPlayers[j + 1] = temp;
            }
        }
    }

    /* Walk through the sorted list. A run of two or more equal rolls
       is a tie - only that run re-rolls, against each other only.   */
    i = 0;

    while(i < groupSize)
    {
        runStart = i;
        runLength = 1;

        while(runStart + runLength < groupSize &&
              rolls[runStart + runLength] == rolls[runStart])
        {
            runLength++;
        }

        if(runLength == 1)
        {
            /* No tie here - this player's place is fully decided */
            output[startIndex + written] = groupPlayers[runStart];
            written++;
        }
        else
        {
            printf("Tie detected between %d players at %d. Rolling again.\n",
                   runLength, rolls[runStart]);

            for(k = 0; k < runLength; k++)
                tiedPlayers[k] = groupPlayers[runStart + k];

            written += resolveGroup(game, tiedPlayers, runLength,
                                     output, startIndex + written);
        }

        i = runStart + runLength;
    }

    return written;
}

void determineTurnOrder(GameState game[], int turnOrder[])
{
    int allPlayers[MAX_PLAYERS];
    int i;

    for(i = 0; i < MAX_PLAYERS; i++)
        allPlayers[i] = i;

    printf("\nDetermining the First Player\n");

    resolveGroup(game, allPlayers, MAX_PLAYERS, turnOrder, 0);

    printf("\n%s will begin the game.\n", game[0].players[turnOrder[0]].name);

    printf("\nTurn order:\n");
    for(i = 0; i < MAX_PLAYERS; i++)
        printf("%s\n", game[0].players[turnOrder[i]].name);
}

/*========================================
    ROUND SUMMARY
========================================*/

int countHouses(GameState game[], int playerIndex)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type == PROPERTY &&
           game[0].board[i].property.owner == playerIndex &&
           !game[0].board[i].property.hotel)
        {
            count += game[0].board[i].property.houses;
        }
    }

    return count;
}

int countHotels(GameState game[], int playerIndex)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type == PROPERTY &&
           game[0].board[i].property.owner == playerIndex &&
           game[0].board[i].property.hotel)
        {
            count++;
        }
    }

    return count;
}

void displayRoundSummary(GameState game[], int round)
{
    int i;

    printf("\n=============================================\n");
    printf("Round %d Summary\n", round);
    printf("=============================================\n");

    for(i = 0; i < MAX_PLAYERS; i++)
    {
        printf("%s\n", game[0].players[i].name);
        printf("Cash : LKR %d\n", game[0].players[i].cash);
        printf("Net Worth : LKR %d\n", calculateNetWorth(game, i));
        printf("Properties : %d\n", game[0].players[i].propertiesOwned);
        printf("Railways   : %d\n", game[0].players[i].railwaysOwned);
        printf("Utilities  : %d\n", game[0].players[i].utilitiesOwned);
        printf("Houses     : %d\n", countHouses(game, i));
        printf("Hotels     : %d\n", countHotels(game, i));

        if(game[0].players[i].loan.active)
            printf("Outstanding Loan : LKR %d\n", game[0].players[i].loan.amount);
        else
            printf("Outstanding Loan : None\n");

        if(game[0].players[i].bankrupt)
            printf("Status : BANKRUPT\n");

        printf("---------------------------------------------\n");
    }
}

/*========================================
    COUNT PLAYERS STILL SOLVENT
========================================*/

int countSolventPlayers(GameState game[])
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < MAX_PLAYERS; i++)
    {
        if(!game[0].players[i].bankrupt)
            count++;
    }

    return count;
}

/*========================================
    MAIN GAME LOOP

    IMPORTANT : a "round" is NOT simply "each of the 4 players took
    one turn." A round only finishes once EVERY player still in the
    game has passed (or landed on) GO at least once. Since players
    move different distances each turn, this usually takes each
    player several turns, not just one, to complete a single round -
    so the game loop below is a `while` loop that keeps cycling
    through the turn order, one turn at a time, and only does the
    "end of round" work (interest, aging, event timers, and the
    every-10/15/20-round triggers) once everybody has crossed GO.
========================================*/

void playGame(GameState game[], int turnOrder[])
{
    int round;
    int turnPointer;
    int playerIndex;
    int passedGoThisRound[MAX_PLAYERS];
    int i;
    int allPassed;
    int passedGo;

    round = 1;
    turnPointer = 0;

    for(i = 0; i < MAX_PLAYERS; i++)
        passedGoThisRound[i] = 0;

    printf("\n=====================================\n");
    printf("ROUND %d\n", round);
    printf("=====================================\n");

    while(round <= MAX_ROUNDS)
    {
        playerIndex = turnOrder[turnPointer];

        if(!game[0].players[playerIndex].bankrupt)
        {
            passedGo = playTurn(game, playerIndex);

            if(passedGo)
                passedGoThisRound[playerIndex] = 1;
        }

        turnPointer = (turnPointer + 1) % MAX_PLAYERS;

        /* Has every player still in the game passed GO at least once
           since this round began? Bankrupt players don't count -
           they no longer take turns, so they can't be waited on.     */
        allPassed = 1;

        for(i = 0; i < MAX_PLAYERS; i++)
        {
            if(game[0].players[i].bankrupt)
                continue;

            if(!passedGoThisRound[i])
            {
                allPassed = 0;
                break;
            }
        }

        if(allPassed)
        {
            /* End of round : loans accrue interest and may default */
            processLoans(game);

            /* End of round : insurance policies count down / expire */
            processInsuranceExpiry(game);

            /* End of round : properties get one round older, buildings
               wear down a little (Rule-LK 15, 25)                      */
            ageProperties(game);
            ageBuildings(game);

            /* Count down any active event bonuses/penalties */
            decrementEventTimers(game);
            decrementMarketTimers(game);

            /* Every 10 rounds : disasters, inflation, and a market review
               (Rule-LK 10, 12, 30)                                       */
            if(round % 10 == 0)
            {
                triggerDisaster(game);
                applyInflation(game);
                reviewPropertyMarket(game, round);
            }

            /* Every 15 rounds : an Economic Event and a Regional
               Development Card (Section 2.5, 2.10)                      */
            if(round % 15 == 0)
            {
                triggerEconomicEvent(game);
                drawRegionalCard(game);
            }

            /* Every 20 rounds : a Government Regulation (Section 2.7) */
            if(round % 20 == 0)
            {
                triggerGovernmentRegulation(game);
            }

            displayRoundSummary(game, round);

            /* Rule-LK 36 : show current market conditions every round */
            displayMarketConditions(game);

            if(countSolventPlayers(game) <= 1)
            {
                printf("\nOnly one solvent player remains. Ending game.\n");
                break;
            }

            round++;

            if(round <= MAX_ROUNDS)
            {
                printf("\n=====================================\n");
                printf("ROUND %d\n", round);
                printf("=====================================\n");
            }

            for(i = 0; i < MAX_PLAYERS; i++)
                passedGoThisRound[i] = 0;
        }
    }
}

/*========================================
    WHO WON? (Rule 15)
    Whoever is left solvent automatically wins.
    If several players are still solvent when
    the 500-round limit is reached, the one
    with the highest net worth wins instead.
========================================*/

int determineWinner(GameState game[])
{
    int i;
    int winner;
    int bestNetWorth;
    int netWorth;

    winner = -1;
    bestNetWorth = 0;

    for(i = 0; i < MAX_PLAYERS; i++)
    {
        if(game[0].players[i].bankrupt)
            continue;

        netWorth = calculateNetWorth(game, i);

        if(winner == -1 || netWorth > bestNetWorth)
        {
            winner = i;
            bestNetWorth = netWorth;
        }
    }

    /* Extremely unlikely edge case : everyone ended up bankrupt at
       the exact same moment. Fall back to comparing everyone anyway. */
    if(winner == -1)
    {
        for(i = 0; i < MAX_PLAYERS; i++)
        {
            netWorth = calculateNetWorth(game, i);

            if(winner == -1 || netWorth > bestNetWorth)
            {
                winner = i;
                bestNetWorth = netWorth;
            }
        }
    }

    return winner;
}

void displayFinalResults(GameState game[])
{
    int winner;
    int i;

    winner = determineWinner(game);

    printf("\n=============================================\n");
    printf("GAME OVER\n");
    printf("=============================================\n");

    printf("Winner\n%s\n", game[0].players[winner].name);
    printf("Total Cash\nLKR %d\n", game[0].players[winner].cash);

    printf("Total Property Value\nLKR %d\n",
           calculatePropertyValue(game, winner) + calculateBuildingValue(game, winner));

    if(game[0].players[winner].loan.active)
        printf("Outstanding Loans\nLKR %d\n", game[0].players[winner].loan.amount);
    else
        printf("Outstanding Loans\nNone\n");

    printf("Net Worth\nLKR %d\n", calculateNetWorth(game, winner));
    printf("=============================================\n");

    printf("\nFinal Standings (all players)\n");
    printf("=============================================\n");

    for(i = 0; i < MAX_PLAYERS; i++)
    {
        printf("\n%s\n", game[0].players[i].name);
        printf("Cash : LKR %d\n", game[0].players[i].cash);
        printf("Net Worth : LKR %d\n", calculateNetWorth(game, i));
        printf("Properties : %d\n", game[0].players[i].propertiesOwned);
        printf("Railways   : %d\n", game[0].players[i].railwaysOwned);
        printf("Utilities  : %d\n", game[0].players[i].utilitiesOwned);
        printf("Status : %s\n", game[0].players[i].bankrupt ? "Bankrupt" : "Active");
    }
}

/*========================================
    ENTRY POINT CALLED FROM main.c
========================================*/

void startGame(GameState game[])
{
    /* Which order the 4 players take their turns in. A normal local
       array, passed to the functions that need it as a parameter -
       no global variable, no pointer.                                */
    int turnOrder[MAX_PLAYERS];

    srand((unsigned)time(NULL));

    initializeBoard(game);
    initializePlayers(game);
    initEconomy(game);
    initMarket(game);

    printf("Player 1 : %s\n", game[0].players[0].name);
    printf("Player 2 : %s\n", game[0].players[1].name);
    printf("Player 3 : %s\n", game[0].players[2].name);
    printf("Player 4 : %s\n", game[0].players[3].name);
    printf("\nEach player begins with LKR %d.\n", START_MONEY);

    determineTurnOrder(game, turnOrder);

    playGame(game, turnOrder);

    displayFinalResults(game);
}
