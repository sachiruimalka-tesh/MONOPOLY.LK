#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "types.h"
#include "functions.h"

/*========================================
        GLOBAL VARIABLES
========================================*/

extern Square board[BOARD_SIZE];
extern Player players[MAX_PLAYERS];

/* Stores the order in which players take turns (player indices) */
int turnOrder[MAX_PLAYERS];

/*========================================
    DICE
========================================*/

int rollDice(void)
{
    int die1 = rand() % 6 + 1;
    int die2 = rand() % 6 + 1;

    return die1 + die2;
}

/*========================================
    MOVEMENT
========================================*/

void movePlayer(int playerIndex, int dice)
{
    int oldPosition;

    oldPosition = players[playerIndex].position;

    players[playerIndex].position = (oldPosition + dice) % BOARD_SIZE;

    printf("%s moves from Square %d to Square %d (%s)\n",
           players[playerIndex].name,
           oldPosition,
           players[playerIndex].position,
           board[players[playerIndex].position].name);

    /* Passed or landed exactly on GO */
    if(oldPosition + dice >= BOARD_SIZE)
    {
        receiveMoney(playerIndex, GO_MONEY);

        printf("%s passed GO and collected LKR %d\n",
               players[playerIndex].name,
               GO_MONEY);

        printf("Current Balance : LKR %d\n",
               players[playerIndex].cash);
    }
}

/*========================================
    JAIL
    Returns 1 if the player is still stuck in jail
    (so playTurn should skip the rest of the turn),
    Returns 0 if the player is free to move normally.
========================================*/

int handleJail(int playerIndex)
{
    int die1, die2;

    if(!players[playerIndex].inJail)
        return 0;

    die1 = rand() % 6 + 1;
    die2 = rand() % 6 + 1;

    printf("%s is in Jail. Rolled %d and %d.\n",
           players[playerIndex].name, die1, die2);

    if(die1 == die2)
    {
        printf("Doubles! %s is released from Jail.\n",
               players[playerIndex].name);

        players[playerIndex].inJail = 0;
        players[playerIndex].jailTurns = 0;

        movePlayer(playerIndex, die1 + die2);
        return 0;
    }

    players[playerIndex].jailTurns++;

    if(players[playerIndex].jailTurns >= 3)
    {
        printf("%s pays bail of LKR %d and is released from Jail.\n",
               players[playerIndex].name, JAIL_BAIL);

        payMoney(playerIndex, JAIL_BAIL);

        players[playerIndex].inJail = 0;
        players[playerIndex].jailTurns = 0;

        /* Player is released but does not move this turn */
        return 1;
    }

    printf("%s remains in Jail (%d/3 turns).\n",
           players[playerIndex].name,
           players[playerIndex].jailTurns);

    return 1;
}

/*========================================
    ONE PLAYER'S TURN
========================================*/

void playTurn(int playerIndex)
{
    int dice;
    int pos;

    if(players[playerIndex].bankrupt)
        return;

    printf("\n----------------------------------\n");
    printf("%s's Turn\n", players[playerIndex].name);

    /* Step 1 : Resolve outstanding penalties (jail, damaged buildings) */
    tryAutoRepair(playerIndex);
    performMaintenance(playerIndex);
    renovateStructuralDamage(playerIndex);

    if(handleJail(playerIndex))
        return;

    /* Step 2 & 3 : Roll dice and move */
    dice = rollDice();
    printf("%s rolled %d.\n", players[playerIndex].name, dice);

    movePlayer(playerIndex, dice);

    /* Step 4 : Resolve landing action */
    pos = players[playerIndex].position;

    switch(board[pos].type)
    {
        case PROPERTY:
        case RAILWAY:
        case UTILITY:

            payRent(playerIndex, dice);
            buyProperty(playerIndex);
            break;

        case EVENT:

            executeEvent(playerIndex);
            break;

        case TAX:

            payTax(playerIndex, incomeTaxAmount);
            break;

        case GO_TO_JAIL:

            printf("%s is sent to Jail!\n", players[playerIndex].name);
            players[playerIndex].position = 10;
            players[playerIndex].inJail = 1;
            players[playerIndex].jailTurns = 0;
            break;

        case BANK:

            handleBankVisit(playerIndex);
            break;

        case INSURANCE:

            handleInsuranceVisit(playerIndex);
            break;

        default:

            /* GO, JAIL (just visiting), FREE_PARKING, BANK, INSURANCE */
            /* Bank / Insurance actions are added in later phases      */
            break;
    }

    /* Step 6 : Construct buildings if eligible (Rules 8, 9, 10) */
    constructBuildings(playerIndex);
}

/*========================================
    TURN ORDER (Rule 2)
========================================*/

void determineTurnOrder(void)
{
    int rolls[MAX_PLAYERS];
    int i, j, temp;
    int tie;

    printf("\nDetermining the First Player\n");

    do
    {
        tie = 0;

        for(i = 0; i < MAX_PLAYERS; i++)
        {
            rolls[i] = rollDice();
            printf("%s rolls %d.\n", players[i].name, rolls[i]);
        }

        /* If any two players rolled the same number, everyone re-rolls */
        for(i = 0; i < MAX_PLAYERS && !tie; i++)
        {
            for(j = i + 1; j < MAX_PLAYERS; j++)
            {
                if(rolls[i] == rolls[j])
                {
                    tie = 1;
                    break;
                }
            }
        }

        if(tie)
            printf("Tie detected. Rolling again.\n\n");

    } while(tie);

    /* Start with players in index order, then sort by roll (highest first) */
    for(i = 0; i < MAX_PLAYERS; i++)
        turnOrder[i] = i;

    for(i = 0; i < MAX_PLAYERS - 1; i++)
    {
        for(j = 0; j < MAX_PLAYERS - 1 - i; j++)
        {
            if(rolls[turnOrder[j]] < rolls[turnOrder[j + 1]])
            {
                temp = turnOrder[j];
                turnOrder[j] = turnOrder[j + 1];
                turnOrder[j + 1] = temp;
            }
        }
    }

    printf("\n%s will begin the game.\n", players[turnOrder[0]].name);

    printf("\nTurn order:\n");
    for(i = 0; i < MAX_PLAYERS; i++)
        printf("%s\n", players[turnOrder[i]].name);
}

/*========================================
    ROUND SUMMARY (simple version for now)
========================================*/

int countHouses(int playerIndex)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type == PROPERTY &&
           board[i].property.owner == playerIndex &&
           !board[i].property.hotel)
        {
            count += board[i].property.houses;
        }
    }

    return count;
}

int countHotels(int playerIndex)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type == PROPERTY &&
           board[i].property.owner == playerIndex &&
           board[i].property.hotel)
        {
            count++;
        }
    }

    return count;
}

void displayRoundSummary(int round)
{
    int i;

    printf("\n=============================================\n");
    printf("Round %d Summary\n", round);
    printf("=============================================\n");

    for(i = 0; i < MAX_PLAYERS; i++)
    {
        printf("%s\n", players[i].name);
        printf("Cash : LKR %d\n", players[i].cash);
        printf("Properties : %d\n", players[i].propertiesOwned);
        printf("Railways   : %d\n", players[i].railwaysOwned);
        printf("Utilities  : %d\n", players[i].utilitiesOwned);
        printf("Houses     : %d\n", countHouses(i));
        printf("Hotels     : %d\n", countHotels(i));

        if(players[i].loan.active)
            printf("Outstanding Loan : LKR %d\n", players[i].loan.amount);
        else
            printf("Outstanding Loan : None\n");

        if(players[i].bankrupt)
            printf("Status : BANKRUPT\n");

        printf("---------------------------------------------\n");
    }
}

/*========================================
    COUNT PLAYERS STILL SOLVENT
========================================*/

int countSolventPlayers(void)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < MAX_PLAYERS; i++)
    {
        if(!players[i].bankrupt)
            count++;
    }

    return count;
}

/*========================================
    MAIN GAME LOOP
========================================*/

void playGame(void)
{
    int round;
    int i;

    for(round = 1; round <= MAX_ROUNDS; round++)
    {
        printf("\n=====================================\n");
        printf("ROUND %d\n", round);
        printf("=====================================\n");

        for(i = 0; i < MAX_PLAYERS; i++)
        {
            playTurn(turnOrder[i]);
        }

        /* End of round : loans accrue interest and may default */
        processLoans();

        /* End of round : insurance policies count down / expire */
        processInsuranceExpiry();

        /* End of round : properties get one round older, buildings
           wear down a little (Rule-LK 15, 25)                      */
        ageProperties();
        ageBuildings();

        /* Count down any active event bonuses/penalties */
        decrementEventTimers();

        /* Every 10 rounds : disasters and inflation (Rule-LK 10, 12) */
        if(round % 10 == 0)
        {
            triggerDisaster();
            applyInflation();
        }

        /* Every 15 rounds : a national Economic Event (Section 2.5) */
        if(round % 15 == 0)
        {
            triggerEconomicEvent();
        }

        /* Every 20 rounds : a Government Regulation (Section 2.7) */
        if(round % 20 == 0)
        {
            triggerGovernmentRegulation();
        }

        displayRoundSummary(round);

        if(countSolventPlayers() <= 1)
        {
            printf("\nOnly one solvent player remains. Ending game.\n");
            break;
        }
    }
}

/*========================================
    ENTRY POINT CALLED FROM main.c
========================================*/

void startGame(void)
{
    srand((unsigned)time(NULL));

    initializeBoard();
    initializePlayers();

    printf("Player 1 : %s\n", players[0].name);
    printf("Player 2 : %s\n", players[1].name);
    printf("Player 3 : %s\n", players[2].name);
    printf("Player 4 : %s\n", players[3].name);
    printf("\nEach player begins with LKR %d.\n", START_MONEY);

    determineTurnOrder();

    playGame();

    printf("\n=============================================\n");
    printf("GAME OVER\n");
    printf("=============================================\n");
    displayPlayers();
}
