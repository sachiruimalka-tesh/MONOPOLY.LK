#include <stdio.h>
#include "types.h"
#include "functions.h"

/*========================================
    GLOBAL VARIABLES
========================================*/

extern Player players[MAX_PLAYERS];
extern Square board[BOARD_SIZE];

/*========================================
    Total mortgage value of everything this
    player owns that is NOT mortgaged and NOT
    already pledged to another loan.
    (Properties + Railways + Utilities, Rule-LK 1)
========================================*/

int totalEligibleCollateral(int playerIndex)
{
    int i;
    int total;

    total = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type != PROPERTY &&
           board[i].type != RAILWAY &&
           board[i].type != UTILITY)
        {
            continue;
        }

        if(board[i].property.owner != playerIndex)
            continue;

        if(board[i].property.mortgaged)
            continue;

        if(board[i].property.loanLocked)
            continue;

        total += board[i].property.mortgageValue;
    }

    return total;
}

/* Maximum loan a player could get right now (Rule-LK 2) */
int calculateMaxLoan(int playerIndex)
{
    return (totalEligibleCollateral(playerIndex) * 75) / 100;
}

/*========================================
    TAKE OUT A NEW LOAN (Rule-LK 3)
========================================*/

void obtainLoan(int playerIndex)
{
    int i;
    int maxLoan;

    /* Only one active loan allowed at a time */
    if(players[playerIndex].loan.active)
        return;

    maxLoan = calculateMaxLoan(playerIndex);

    if(maxLoan <= 0)
        return;

    /* Set up the loan */
    players[playerIndex].loan.active = 1;
    players[playerIndex].loan.amount = maxLoan;
    players[playerIndex].loan.interestRate = LOAN_INTEREST_RATE;
    players[playerIndex].loan.remainingRounds = LOAN_DURATION_ROUNDS;

    receiveMoney(playerIndex, maxLoan);

    printf("\n%s obtained a secured loan.\n", players[playerIndex].name);
    printf("Loan Amount : LKR %d\n", maxLoan);
    printf("Interest Rate : %d%%\n", LOAN_INTEREST_RATE);
    printf("Duration : %d Rounds\n", LOAN_DURATION_ROUNDS);

    /* Pledge every eligible property as collateral (Loan Locked) */
    printf("Collateral :\n");

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type != PROPERTY &&
           board[i].type != RAILWAY &&
           board[i].type != UTILITY)
        {
            continue;
        }

        if(board[i].property.owner == playerIndex &&
           !board[i].property.mortgaged &&
           !board[i].property.loanLocked)
        {
            board[i].property.loanLocked = 1;
            printf("%s\n", board[i].name);
        }
    }
}

/*========================================
    REPAY PART / ALL OF THE LOAN (Rule-LK 5)
========================================*/

void repayLoan(int playerIndex, int amount)
{
    int i;

    if(!players[playerIndex].loan.active)
        return;

    if(amount > players[playerIndex].loan.amount)
        amount = players[playerIndex].loan.amount;

    if(players[playerIndex].cash < amount)
        amount = players[playerIndex].cash;

    payMoney(playerIndex, amount);
    players[playerIndex].loan.amount -= amount;

    printf("\n%s repaid LKR %d towards their loan.\n",
           players[playerIndex].name, amount);

    printf("Outstanding Balance : LKR %d\n",
           players[playerIndex].loan.amount);

    /* Loan fully repaid -> release the collateral */
    if(players[playerIndex].loan.amount <= 0)
    {
        players[playerIndex].loan.active = 0;
        players[playerIndex].loan.amount = 0;
        players[playerIndex].loan.interestRate = 0;
        players[playerIndex].loan.remainingRounds = 0;

        for(i = 0; i < BOARD_SIZE; i++)
        {
            if(board[i].property.owner == playerIndex)
                board[i].property.loanLocked = 0;
        }

        printf("%s has fully repaid the loan. Collateral released.\n",
               players[playerIndex].name);
    }
}

/*========================================
    WHAT HAPPENS WHEN A PLAYER LANDS ON
    THE BANK OF CEYLON SQUARE (Rule-LK 5)
========================================*/

void handleBankVisit(int playerIndex)
{
    printf("\n%s landed on Bank of Ceylon.\n", players[playerIndex].name);

    if(players[playerIndex].loan.active)
    {
        if(wantsToRepayLoan(playerIndex))
        {
            int repayAmount;

            /* Repay as much as the strategy is comfortable with,
               capped at what is still owed */
            repayAmount = players[playerIndex].cash / 2;

            if(repayAmount > players[playerIndex].loan.amount)
                repayAmount = players[playerIndex].loan.amount;

            repayLoan(playerIndex, repayAmount);
        }

        return;
    }

    if(wantsLoan(playerIndex))
    {
        obtainLoan(playerIndex);
    }
}

/*========================================
    END-OF-ROUND LOAN PROCESSING (Rule-LK 4, 6, 7)
    Called once after every player has taken
    their turn in a round.
========================================*/

void demolishBuildingsOn(int index)
{
    board[index].property.houses = 0;
    board[index].property.hotel = 0;
}

void foreclose(int playerIndex)
{
    int i;
    int ownsAnythingLeft;

    printf("\n%s has defaulted on their loan!\n", players[playerIndex].name);

    ownsAnythingLeft = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].property.owner != playerIndex)
            continue;

        if(board[i].property.loanLocked)
        {
            /* Pledged property : goes back to the Bank */
            printf("%s (pledged collateral) transferred to the Bank.\n",
                   board[i].name);

            demolishBuildingsOn(i);

            board[i].property.owner = -1;
            board[i].property.loanLocked = 0;
            board[i].property.mortgaged = 0;
            board[i].property.insurance = NO_INSURANCE;

            if(board[i].type == PROPERTY)
                players[playerIndex].propertiesOwned--;
            else if(board[i].type == RAILWAY)
                players[playerIndex].railwaysOwned--;
            else if(board[i].type == UTILITY)
                players[playerIndex].utilitiesOwned--;
        }
        else
        {
            ownsAnythingLeft = 1;
        }
    }

    players[playerIndex].loan.active = 0;
    players[playerIndex].loan.amount = 0;
    players[playerIndex].loan.interestRate = 0;
    players[playerIndex].loan.remainingRounds = 0;

    printf("Outstanding debt cleared.\n");

    /* Rule-LK 7 : nothing left at all -> bankrupt */
    if(!ownsAnythingLeft && players[playerIndex].cash <= 0)
    {
        players[playerIndex].bankrupt = 1;
        printf("%s has no remaining assets and is declared BANKRUPT.\n",
               players[playerIndex].name);
    }
}

void processLoans(void)
{
    int i;

    for(i = 0; i < MAX_PLAYERS; i++)
    {
        if(players[i].bankrupt)
            continue;

        if(!players[i].loan.active)
            continue;

        /* Interest compounds every complete round (Rule-LK 4) */
        int interest;

        interest = (players[i].loan.amount * players[i].loan.interestRate) / 100;
        players[i].loan.amount += interest;

        players[i].loan.remainingRounds--;

        printf("\n%s's loan accrued LKR %d interest. New balance : LKR %d\n",
               players[i].name, interest, players[i].loan.amount);

        /* Ran out of time to repay -> default (Rule-LK 6) */
        if(players[i].loan.remainingRounds <= 0)
        {
            foreclose(i);
        }
    }
}