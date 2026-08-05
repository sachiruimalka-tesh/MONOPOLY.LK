#include <stdio.h>
#include <stdlib.h>
#include "types.h"
#include "functions.h"

/*========================================
    GLOBAL VARIABLES
========================================*/

extern Player players[MAX_PLAYERS];
extern Square board[BOARD_SIZE];

/*========================================
    "Current value" of a property, used to
    work out premiums and repair costs.
    For now this is just the purchase price -
    it will become more accurate once we add
    the Depreciation and Dynamic Market phases.
========================================*/

int propertyValue(int propIndex)
{
    return board[propIndex].property.purchasePrice;
}

/* Assumption: repairing storm/fire/etc damage costs 30% of the
   property's value. The assignment does not give an exact figure,
   so this is a reasonable fixed rule used consistently everywhere. */
int repairCost(int propIndex)
{
    return (propertyValue(propIndex) * 30) / 100;
}

/*========================================
    Does a given insurance policy cover a
    given disaster type? (Section 1.2 / E)
========================================*/

int isCovered(InsuranceType policy, DisasterType disaster)
{
    if(policy == NO_INSURANCE)
        return 0;

    if(policy == BASIC_INSURANCE)
    {
        /* Basic only covers Fire and Flood */
        return (disaster == FIRE || disaster == FLOOD);
    }

    /* Comprehensive and Business Interruption cover everything */
    return 1;
}

int compensationPercent(InsuranceType policy)
{
    switch(policy)
    {
        case BASIC_INSURANCE:            return 80;
        case COMPREHENSIVE_INSURANCE:    return 100;
        case BUSINESS_INTERRUPTION:      return 100;
        default:                         return 0;
    }
}

/*========================================
    BUYING / RENEWING INSURANCE
========================================*/

void purchaseInsurance(int playerIndex, int propIndex, InsuranceType type)
{
    int value;
    int premium;
    int premiumPercent;

    value = propertyValue(propIndex);

    switch(type)
    {
        case BASIC_INSURANCE:          premiumPercent = 5;  break;
        case COMPREHENSIVE_INSURANCE:  premiumPercent = 10; break;
        case BUSINESS_INTERRUPTION:    premiumPercent = 15; break;
        default:                       return;
    }

    premium = (value * premiumPercent) / 100;

    if(players[playerIndex].cash < premium)
        return;

    payMoney(playerIndex, premium);

    board[propIndex].property.insurance = type;
    board[propIndex].property.insuranceRoundsLeft = 20;

    printf("\n%s purchased insurance for %s.\n",
           players[playerIndex].name,
           board[propIndex].name);

    printf("Premium : LKR %d\n", premium);
}

/*========================================
    Find one of this player's developed,
    uninsured properties that their strategy
    wants to insure.
========================================*/

int findPropertyToInsure(int playerIndex)
{
    int i;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type != PROPERTY)
            continue;

        if(board[i].property.owner != playerIndex)
            continue;

        if(board[i].property.houses == 0 && !board[i].property.hotel)
            continue;   /* not developed - nothing worth insuring yet */

        if(board[i].property.insurance != NO_INSURANCE)
            continue;   /* already insured */

        if(desiredInsurance(playerIndex, i) != NO_INSURANCE)
            return i;
    }

    return -1;
}

/*========================================
    WHAT HAPPENS WHEN A PLAYER LANDS ON
    AN INSURANCE SQUARE
========================================*/

void handleInsuranceVisit(int playerIndex)
{
    int propIndex;
    InsuranceType type;

    printf("\n%s landed on an Insurance square.\n",
           players[playerIndex].name);

    propIndex = findPropertyToInsure(playerIndex);

    if(propIndex == -1)
    {
        printf("No suitable property to insure right now.\n");
        return;
    }

    type = desiredInsurance(playerIndex, propIndex);

    purchaseInsurance(playerIndex, propIndex, type);
}

/*========================================
    AUTOMATIC REPAIR (Rule-LK 11)
    Called at the start of a player's turn -
    if they can now afford it, damaged
    buildings are fixed automatically.
========================================*/

void tryAutoRepair(int playerIndex)
{
    int i;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type != PROPERTY)
            continue;

        if(board[i].property.owner != playerIndex)
            continue;

        if(!board[i].property.damaged)
            continue;

        if(players[playerIndex].cash >= board[i].property.repairCostOwed)
        {
            payMoney(playerIndex, board[i].property.repairCostOwed);

            printf("\n%s repaired %s. It can collect rent again.\n",
                   players[playerIndex].name, board[i].name);

            board[i].property.damaged = 0;
            board[i].property.repairCostOwed = 0;
        }
    }
}

/*========================================
    DISASTERS (Rule-LK 10)
    Happens every 10 rounds, hits one random
    developed property (any owner).
========================================*/

void triggerDisaster(void)
{
    int developed[BOARD_SIZE];
    int developedCount;
    int i;
    int chosen;
    DisasterType disaster;
    int owner;
    int cost;
    int compensation;

    developedCount = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type == PROPERTY &&
           (board[i].property.houses > 0 || board[i].property.hotel))
        {
            developed[developedCount] = i;
            developedCount++;
        }
    }

    if(developedCount == 0)
        return;   /* nothing built yet - no disaster possible */

    chosen = developed[rand() % developedCount];
    disaster = (DisasterType)(rand() % 5);
    owner = board[chosen].property.owner;

    printf("\n*** DISASTER ***\n");

    switch(disaster)
    {
        case FIRE:                printf("Fire occurred.\n");               break;
        case FLOOD:                printf("Flood occurred.\n");             break;
        case RIOT:                 printf("Riot occurred.\n");              break;
        case BUILDING_COLLAPSE:    printf("Building Collapse occurred.\n"); break;
        case ELECTRICAL_FAILURE:   printf("Electrical Failure occurred.\n");break;
    }

    printf("Affected Property : %s (owner : %s)\n",
           board[chosen].name, players[owner].name);

    cost = repairCost(chosen);

    if(isCovered(board[chosen].property.insurance, disaster))
    {
        compensation = (cost * compensationPercent(board[chosen].property.insurance)) / 100;

        receiveMoney(owner, compensation);

        printf("Insurance Claim Approved.\n");
        printf("Compensation Paid : LKR %d\n", compensation);

        /* Business Interruption also covers 5 rounds of lost rent -
           since the building stays fully working (not marked damaged),
           the compensation itself stands in for that lost income. */
    }
    else
    {
        compensation = 0;
        players[owner].sufferedLoss = 1;

        printf("Property was NOT insured against this disaster.\n");
    }

    /* Whatever is still owed after compensation must be repaired
       before the building earns rent again */
    board[chosen].property.repairCostOwed = cost - compensation;

    if(board[chosen].property.repairCostOwed > 0)
    {
        board[chosen].property.damaged = 1;
        printf("%s is damaged and stops earning rent until repaired.\n",
               board[chosen].name);
    }
}

/*========================================
    END-OF-ROUND INSURANCE PROCESSING
    (Rule-LK 9)
========================================*/

void processInsuranceExpiry(void)
{
    int i;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type != PROPERTY)
            continue;

        if(board[i].property.insurance == NO_INSURANCE)
            continue;

        board[i].property.insuranceRoundsLeft--;

        if(board[i].property.insuranceRoundsLeft == 3)
        {
            printf("\nInsurance policy on %s expires in 3 rounds.\n",
                   board[i].name);
        }

        if(board[i].property.insuranceRoundsLeft <= 0)
        {
            printf("\nInsurance policy on %s has expired.\n",
                   board[i].name);

            board[i].property.insurance = NO_INSURANCE;
        }
    }
}
