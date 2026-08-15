#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "types.h"
#include "functions.h"

void initMarket(GameState game[])
{
    int i;

    for(i = 0; i < NO_GROUP; i++)
    {
        game[0].economy.groupValueMultiplier[i] = 100;
        game[0].economy.groupRentMultiplier[i] = 100;
        game[0].economy.groupRoundsLeft[i] = 0;
        game[0].economy.groupCooldownUntilRound[i] = 0;
    }

    game[0].economy.lastBoomGroup = -1;
    game[0].economy.lastDeclineGroup = -1;
}

void groupName(PropertyGroup group, char buffer[])
{
    if(group == BROWN)
        strcpy(buffer, "Brown");
    else if(group == LIGHT_BLUE)
        strcpy(buffer, "Light Blue");
    else if(group == PINK)
        strcpy(buffer, "Pink");
    else if(group == ORANGE)
        strcpy(buffer, "Orange");
    else if(group == RED)
        strcpy(buffer, "Red");
    else if(group == YELLOW)
        strcpy(buffer, "Yellow");
    else if(group == GREEN)
        strcpy(buffer, "Green");
    else if(group == DARK_BLUE)
        strcpy(buffer, "Dark Blue");
    else
        strcpy(buffer, "Unknown");
}

/* Picks a random group that isn't on cooldown and isn't one of the
   two groups to avoid (Rule-LK 30, 33). */
PropertyGroup pickEligibleGroup(GameState game[], int currentRound, int avoid1, int avoid2)
{
    int candidates[NO_GROUP];
    int count;
    int g;

    count = 0;

    for(g = 0; g < NO_GROUP; g++)
    {
        if(g == avoid1 || g == avoid2)
            continue;

        if(game[0].economy.groupCooldownUntilRound[g] > currentRound)
            continue;

        candidates[count] = g;
        count++;
    }

    if(count == 0)
        return (PropertyGroup)((avoid1 + 1) % NO_GROUP);   /* rare fallback */

    return (PropertyGroup)candidates[rand() % count];
}

/* Rule-LK 30-34: every 10 rounds, one group booms and a different
   one declines, each for 10 rounds. */
void reviewPropertyMarket(GameState game[], int currentRound)
{
    PropertyGroup boomGroup;
    PropertyGroup declineGroup;
    char boomName[12];
    char declineName[12];

    boomGroup = pickEligibleGroup(game, currentRound, game[0].economy.lastBoomGroup, -1);
    declineGroup = pickEligibleGroup(game, currentRound, game[0].economy.lastDeclineGroup, boomGroup);

    groupName(boomGroup, boomName);
    groupName(declineGroup, declineName);

    printf("\n=== Property Market Review ===\n");
    printf("Market Boom : %s (values +20%%, rent +25%%) for 10 rounds.\n", boomName);
    printf("Market Decline : %s (values -15%%, rent -20%%) for 10 rounds.\n", declineName);

    game[0].economy.groupValueMultiplier[boomGroup] = 120;
    game[0].economy.groupRentMultiplier[boomGroup] = 125;
    game[0].economy.groupRoundsLeft[boomGroup] = 10;

    game[0].economy.groupValueMultiplier[declineGroup] = 85;
    game[0].economy.groupRentMultiplier[declineGroup] = 80;
    game[0].economy.groupRoundsLeft[declineGroup] = 10;

    game[0].economy.constructionCostMultiplierPercent = 110;
    game[0].economy.constructionCostRoundsLeft = 10;

    game[0].economy.groupCooldownUntilRound[boomGroup] = currentRound + 30;
    game[0].economy.groupCooldownUntilRound[declineGroup] = currentRound + 30;

    game[0].economy.lastBoomGroup = boomGroup;
    game[0].economy.lastDeclineGroup = declineGroup;
}

/* Table 4: one card every 15 rounds, active for 15 rounds. */
void drawRegionalCard(GameState game[])
{
    int choice;

    choice = rand() % 12;

    printf("\n=== Regional Development Card ===\n");

    switch(choice)
    {
        case 0:
            printf("Southern Tourism Boom : Galle Fort, Unawatuna and "
                   "Hikkaduwa rental income +40%%.\n");
            game[0].economy.groupRentMultiplier[YELLOW] = 140;
            game[0].economy.groupRoundsLeft[YELLOW] = 15;
            break;

        case 1:
            printf("Port City Expansion : Pettah and Maradana values +25%%.\n");
            game[0].economy.groupValueMultiplier[BROWN] = 125;
            game[0].economy.groupRoundsLeft[BROWN] = 15;
            break;

        case 2:
            printf("IT Industry Growth : Maharagama, Nugegoda and "
                   "Kottawa values +20%%.\n");
            game[0].economy.groupValueMultiplier[PINK] = 120;
            game[0].economy.groupRoundsLeft[PINK] = 15;
            break;

        case 3:
            printf("Northern Development Programme : Jaffna Town, Nallur "
                   "and Trincomalee values +30%%.\n");
            game[0].economy.groupValueMultiplier[GREEN] = 130;
            game[0].economy.groupRoundsLeft[GREEN] = 15;
            break;

        case 4:
            printf("Tea Export Boom : Nuwara Eliya value +35%%.\n");
            game[0].economy.groupValueMultiplier[DARK_BLUE] = 135;
            game[0].economy.groupRoundsLeft[DARK_BLUE] = 15;
            break;

        case 5:
            printf("Airport Expansion : Negombo, Katunayake and "
                   "Ja-Ela rents +30%%.\n");
            game[0].economy.groupRentMultiplier[ORANGE] = 130;
            game[0].economy.groupRoundsLeft[ORANGE] = 15;
            break;

        case 6:
            printf("University City Growth : Peradeniya and "
                   "Kandy City values +20%%.\n");
            game[0].economy.groupValueMultiplier[RED] = 120;
            game[0].economy.groupRoundsLeft[RED] = 15;
            break;

        case 7:
            printf("Beach Pollution : Southern coastal rents -30%%.\n");
            game[0].economy.groupRentMultiplier[YELLOW] = 70;
            game[0].economy.groupRoundsLeft[YELLOW] = 15;
            break;

        case 8:
            printf("Flood Damage : Low-lying coastal properties lose 20%% value.\n");
            game[0].economy.groupValueMultiplier[YELLOW] = 80;
            game[0].economy.groupRoundsLeft[YELLOW] = 15;
            break;

        case 9:
            printf("Transport Strike : Railway revenue reduced by 40%%.\n");
            game[0].economy.railwayRentMultiplierPercent = 60;
            game[0].economy.railwayRentRoundsLeft = 15;
            break;

        case 10:
            printf("Electricity Tariff Increase : Utility rent +25%%.\n");
            game[0].economy.utilityRentMultiplierPercent = 125;
            game[0].economy.utilityRentRoundsLeft = 15;
            break;

        case 11:
            printf("Water Shortage : Utility revenue +20%%.\n");
            game[0].economy.utilityRentMultiplierPercent = 120;
            game[0].economy.utilityRentRoundsLeft = 15;
            break;

        default:
            break;
    }
}

void decrementMarketTimers(GameState game[])
{
    int g;

    for(g = 0; g < NO_GROUP; g++)
    {
        if(game[0].economy.groupRoundsLeft[g] > 0)
        {
            game[0].economy.groupRoundsLeft[g]--;

            if(game[0].economy.groupRoundsLeft[g] == 0)
            {
                game[0].economy.groupValueMultiplier[g] = 100;
                game[0].economy.groupRentMultiplier[g] = 100;
            }
        }
    }
}

/* Rule-LK 36: shows the currently active market conditions. */
void displayMarketConditions(GameState game[])
{
    int g;
    int shown;
    char name[12];

    printf("\n=========================================\n");
    printf("Current Market Conditions\n");
    printf("=========================================\n");

    shown = 0;

    for(g = 0; g < NO_GROUP; g++)
    {
        if(game[0].economy.groupRoundsLeft[g] > 0)
        {
            groupName((PropertyGroup)g, name);

            printf("%s : Value x%d%%, Rent x%d%% (%d rounds remaining)\n",
                   name,
                   game[0].economy.groupValueMultiplier[g],
                   game[0].economy.groupRentMultiplier[g],
                   game[0].economy.groupRoundsLeft[g]);

            shown = 1;
        }
    }

    if(!shown)
        printf("No active market booms or declines right now.\n");

    printf("Inflation Rate : %+d%%\n", game[0].economy.inflationRate);
    printf("Current Loan Interest : %d%%\n", game[0].economy.loanInterestRate);
    printf("=========================================\n");
}
