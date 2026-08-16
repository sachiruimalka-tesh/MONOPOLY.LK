#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "types.h"
#include "functions.h"

int rollDice(void)
{
    int die1 = rand() % 6 + 1;
    int die2 = rand() % 6 + 1;

    return die1 + die2;
}

/* Moves a player, returns 1 if they passed or landed on GO. */
int movePlayer(GameState game[], int playerIndex, int dice)
{
    int oldPosition;
    int passedGo;
    char moneyBuffer[32];

    oldPosition = game[0].players[playerIndex].position;
    game[0].players[playerIndex].position = (oldPosition + dice) % BOARD_SIZE;

    printf("%s moves from Square %d to Square %d (%s)\n",
           game[0].players[playerIndex].name,
           oldPosition,
           game[0].players[playerIndex].position,
           game[0].board[game[0].players[playerIndex].position].name);

    passedGo = 0;

    if(oldPosition + dice >= BOARD_SIZE)
    {
        passedGo = 1;

        receiveMoney(game, playerIndex, GO_MONEY);

        printf("%s passed GO.\n", game[0].players[playerIndex].name);

        formatLKR(GO_MONEY, moneyBuffer);

        printf("Collected LKR %s\n", moneyBuffer);

        printf("Current Balance : LKR %d\n",
               game[0].players[playerIndex].cash);
    }

    return passedGo;
}

/* Handles a player's turn while they're in jail.
   Return codes:
     0 = wasn't in jail, or just paid bail - take a normal turn
     1 = still stuck (or forced to pay bail this turn) - turn ends
     2 = escaped via doubles, that move passed GO
     3 = escaped via doubles, did not pass GO                 */
/* Handles a player's turn while they're in jail.
   Return codes:
     0 = wasn't in jail, or just paid bail - take a normal turn
     1 = still stuck (or forced to pay bail this turn) - turn ends
     100 + dice = escaped via doubles, did not pass GO, dice is the
                  roll used (this move IS the turn's move, no reroll)
     200 + dice = escaped via doubles, and that move passed GO      */
int handleJail(GameState game[], int playerIndex)
{
    int die1, die2;
    int total;
    int passedGo;

    if(!game[0].players[playerIndex].inJail)
        return 0;

    /* Rule 13: paying bail is a choice available on any turn, not
       just a fallback after 3 failed attempts. */
    if(shouldPayBail(game, playerIndex) &&
       game[0].players[playerIndex].cash >= JAIL_BAIL)
    {
        printf("%s chooses to pay bail of LKR %d and is released from Jail.\n",
               game[0].players[playerIndex].name, JAIL_BAIL);

        payMoney(game, playerIndex, JAIL_BAIL);

        game[0].players[playerIndex].inJail = 0;
        game[0].players[playerIndex].jailTurns = 0;

        return 0;
    }

    die1 = rand() % 6 + 1;
    die2 = rand() % 6 + 1;
    total = die1 + die2;

    printf("%s is in Jail. Rolled %d and %d.\n",
           game[0].players[playerIndex].name, die1, die2);

    if(die1 == die2)
    {
        printf("Doubles! %s is released from Jail.\n",
               game[0].players[playerIndex].name);

        game[0].players[playerIndex].inJail = 0;
        game[0].players[playerIndex].jailTurns = 0;

        /* Rule 13: this doubles roll IS the player's move for the
           turn - they do not also get a separate normal turn. */
        passedGo = movePlayer(game, playerIndex, total);

        if(passedGo)
            return 200 + total;

        return 100 + total;
    }

    game[0].players[playerIndex].jailTurns++;

    if(game[0].players[playerIndex].jailTurns >= 3)
    {
        printf("%s has been in Jail for 3 turns - must pay bail of "
               "LKR %d and is released.\n",
               game[0].players[playerIndex].name, JAIL_BAIL);

        payMoney(game, playerIndex, JAIL_BAIL);

        game[0].players[playerIndex].inJail = 0;
        game[0].players[playerIndex].jailTurns = 0;

        return 1;
    }

    printf("%s remains in Jail (%d/3 turns).\n",
           game[0].players[playerIndex].name,
           game[0].players[playerIndex].jailTurns);

    return 1;
}

/* One player's whole turn, matching Rule 3. Returns 1 if GO was
   passed at any point during the turn. */
int playTurn(GameState game[], int playerIndex)
{
    int dice;
    int pos;
    int passedGo;
    int jailResult;
    SquareType squareType;

    if(game[0].players[playerIndex].bankrupt)
        return 0;

    printf("\n----------------------------------\n");
    printf("%s's Turn\n", game[0].players[playerIndex].name);

    /* Step 1: fix any damaged, worn, or neglected buildings first */
    tryAutoRepair(game, playerIndex);
    performMaintenance(game, playerIndex);
    renovateStructuralDamage(game, playerIndex);

    passedGo = 0;

    jailResult = handleJail(game, playerIndex);

    if(jailResult == 1)
        return 0;   /* still stuck, or just paid forced bail - no move */

    if(jailResult >= 100)
    {
        /* Escaped via doubles - that move already happened inside
           handleJail(). Do not roll or move again this turn.       */
        if(jailResult >= 200)
        {
            passedGo = 1;
            dice = jailResult - 200;
        }
        else
        {
            dice = jailResult - 100;
        }
    }
    else
    {
        /* jailResult == 0: wasn't in jail, or just paid bail
           voluntarily - take a completely normal turn.             */
        dice = rollDice();
        printf("%s rolled %d.\n", game[0].players[playerIndex].name, dice);

        if(movePlayer(game, playerIndex, dice))
            passedGo = 1;
    }

    /* Step 4: resolve landing action */
    pos = game[0].players[playerIndex].position;
    squareType = game[0].board[pos].type;

    if(squareType == PROPERTY || squareType == RAILWAY || squareType == UTILITY)
    {
        payRent(game, playerIndex, dice);
        buyProperty(game, playerIndex);
    }
    else if(squareType == EVENT)
    {
        executeEvent(game, playerIndex);
    }
    else if(squareType == TAX)
    {
        payTax(game, playerIndex, game[0].economy.incomeTaxAmount);
    }
    else if(squareType == GO_TO_JAIL)
    {
        printf("%s is sent to Jail!\n", game[0].players[playerIndex].name);
        game[0].players[playerIndex].position = 10;
        game[0].players[playerIndex].inJail = 1;
        game[0].players[playerIndex].jailTurns = 0;
    }
    else if(squareType == BANK)
    {
        handleBankVisit(game, playerIndex);
    }
    else if(squareType == INSURANCE)
    {
        handleInsuranceVisit(game, playerIndex);
    }
    /* GO, JAIL (just visiting), FREE_PARKING need no action */

    /* Step 6: build if eligible */
    constructBuildings(game, playerIndex);

    /* Step 7: mortgage or redeem if the player's situation calls for it */
    handleMortgageDecisions(game, playerIndex);

    return passedGo;
}

/* Resolves one group of (possibly tied) players into a strict order.
   Writes the result into output[] starting at startIndex, and
   returns how many players it wrote. Any players still tied after
   rolling call this function again on just themselves. */
int resolveGroup(GameState game[], int groupPlayers[], int groupSize,
                  int output[], int startIndex)
{
    int rolls[MAX_PLAYERS];
    int i, j, temp;
    int runStart, runLength;
    int tiedPlayers[MAX_PLAYERS];
    int written;
    int k;

    written = 0;

    for(i = 0; i < groupSize; i++)
    {
        rolls[i] = rollDice();
        printf("%s rolls %d.\n", game[0].players[groupPlayers[i]].name, rolls[i]);
    }

    /* sort this group by roll, highest first */
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

    /* walk the sorted list - a run of equal rolls is a tie */
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

/* A round is not "each player took one turn" - it only finishes
   once every player still in the game has passed GO at least once.
   Since players move different distances each turn, this usually
   takes several turns per player, not one - so this loop keeps
   cycling through turnOrder until everyone has crossed GO. */
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

        /* has every player still playing passed GO this round? */
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

        if(!allPassed)
            continue;

        processLoans(game);
        processInsuranceExpiry(game);
        ageProperties(game);
        ageBuildings(game);
        decrementEventTimers(game);
        decrementModifiers(game);
        enforceAntiSpeculation(game);

        if(round % 10 == 0)
        {
            triggerDisaster(game);
            applyInflation(game);
            reviewPropertyMarket(game, round);
        }

        if(round % 15 == 0)
        {
            triggerEconomicEvent(game);
            drawRegionalCard(game);
        }

        if(round % 20 == 0)
        {
            triggerGovernmentRegulation(game);
        }

        displayRoundSummary(game, round);
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

/* Whoever is still solvent wins. If several are still solvent at
   round 500, the highest net worth wins (Rule 15). */
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

    if(winner == -1)
    {
        /* edge case: everyone bankrupt at once - compare everyone anyway */
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

void startGame(GameState game[])
{
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
