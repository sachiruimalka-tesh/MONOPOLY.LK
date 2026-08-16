#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "types.h"
#include "functions.h"

void initMarket(GameState game[])
{
    int i;

    for(i = 0; i < NO_GROUP; i++)
        game[0].economy.groupCooldownUntilRound[i] = 0;

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
   one declines, each for 10 rounds.  All effects are temporary
   modifiers (Rule-LK 34) so no base value or cost is ever changed. */
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

    addModifier(game, MOD_GROUP_VALUE, boomGroup, -1, 120, 10);
    addModifier(game, MOD_GROUP_RENT, boomGroup, -1, 125, 10);

    addModifier(game, MOD_GROUP_VALUE, declineGroup, -1, 85, 10);
    addModifier(game, MOD_GROUP_RENT, declineGroup, -1, 80, 10);

    /* Rule-LK 34: the boom group's mortgage values rise by 15% and
       the decline group's fall by 10%; direct purchase prices rise
       by 15% and auction starting prices fall by 25%. */
    addModifier(game, MOD_MARKET_MORTGAGE, boomGroup, -1, 115, 10);
    addModifier(game, MOD_PURCHASE_PRICE, -1, -1, 115, 10);
    addModifier(game, MOD_CONSTRUCTION, -1, -1, 110, 10);

    addModifier(game, MOD_MARKET_MORTGAGE, declineGroup, -1, 90, 10);
    addModifier(game, MOD_AUCTION_PRICE, -1, -1, 75, 10);

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
            addModifier(game, MOD_GROUP_RENT, YELLOW, -1, 140, 15);
            break;

        case 1:
            printf("Port City Expansion : Pettah and Maradana values +25%%.\n");
            addModifier(game, MOD_GROUP_VALUE, BROWN, -1, 125, 15);
            addModifier(game, MOD_INDEX_VALUE, -1, 5, 125, 15);   /* Colombo Fort Station */
            break;

        case 2:
            printf("IT Industry Growth : Maharagama, Nugegoda and "
                   "Kottawa values +20%%.\n");
            addModifier(game, MOD_GROUP_VALUE, PINK, -1, 120, 15);
            break;

        case 3:
            printf("Northern Development Programme : Jaffna Town, Nallur "
                   "and Trincomalee values +30%%.\n");
            addModifier(game, MOD_GROUP_VALUE, GREEN, -1, 130, 15);
            break;

        case 4:
            printf("Tea Export Boom : Nuwara Eliya value +35%%.\n");
            addModifier(game, MOD_INDEX_VALUE, -1, 37, 135, 15);
            break;

        case 5:
            printf("Airport Expansion : Negombo, Katunayake and "
                   "Ja-Ela rents +30%%.\n");
            addModifier(game, MOD_GROUP_RENT, ORANGE, -1, 130, 15);
            break;

        case 6:
            printf("University City Growth : Peradeniya and "
                   "Kandy City values +20%%.\n");
            addModifier(game, MOD_GROUP_VALUE, RED, -1, 120, 15);
            break;

        case 7:
            printf("Beach Pollution : Southern coastal rents -30%%.\n");
            addModifier(game, MOD_GROUP_RENT, YELLOW, -1, 70, 15);
            break;

        case 8:
            printf("Flood Damage : Low-lying coastal properties lose 20%% value.\n");
            addModifier(game, MOD_GROUP_VALUE, YELLOW, -1, 80, 15);
            break;

        case 9:
            printf("Transport Strike : Railway revenue reduced by 40%%.\n");
            addModifier(game, MOD_RAIL_RENT, -1, -1, 60, 15);
            break;

        case 10:
            printf("Electricity Tariff Increase : Utility rent +25%%.\n");
            addModifier(game, MOD_UTIL_RENT, -1, -1, 125, 15);
            break;

        case 11:
            printf("Water Shortage : Utility revenue +20%%.\n");
            addModifier(game, MOD_UTIL_RENT, -1, -1, 120, 15);
            addModifier(game, MOD_INDEX_VALUE, -1, 13, 90, 15);
            addModifier(game, MOD_INDEX_VALUE, -1, 29, 90, 15);
            break;

        default:
            break;
    }
}

/* Rule-LK 36: shows the currently active market conditions. */
void displayMarketConditions(GameState game[])
{
    int i;
    int shown;
    char name[32];

    printf("\n=========================================\n");
    printf("Current Market Conditions\n");
    printf("=========================================\n");

    shown = 0;

    for(i = 0; i < game[0].economy.modifierCount; i++)
    {
        ActiveModifier *m = &game[0].economy.modifiers[i];

        switch(m->type)
        {
            case MOD_GROUP_VALUE:
                groupName((PropertyGroup)m->group, name);
                printf("%s properties : values x%d%% (%d rounds remaining)\n",
                       name, m->percent, m->roundsLeft);
                shown = 1;
                break;

            case MOD_GROUP_RENT:
                groupName((PropertyGroup)m->group, name);
                printf("%s properties : rent x%d%% (%d rounds remaining)\n",
                       name, m->percent, m->roundsLeft);
                shown = 1;
                break;

            case MOD_INDEX_VALUE:
                printf("%s : value x%d%% (%d rounds remaining)\n",
                       game[0].board[m->index].name, m->percent, m->roundsLeft);
                shown = 1;
                break;

            case MOD_RAIL_VALUE:
                printf("Railway values : x%d%% (%d rounds remaining)\n",
                       m->percent, m->roundsLeft);
                shown = 1;
                break;

            case MOD_RAIL_RENT:
                printf("Railway rents : x%d%% (%d rounds remaining)\n",
                       m->percent, m->roundsLeft);
                shown = 1;
                break;

            case MOD_UTIL_RENT:
                printf("Utility rents : x%d%% (%d rounds remaining)\n",
                       m->percent, m->roundsLeft);
                shown = 1;
                break;

            default:
                break;
        }
    }

    if(!shown)
        printf("No active market booms or declines right now.\n");

    printf("Inflation Rate : %+d%%\n", game[0].economy.inflationRate);
    printf("Current Loan Interest : %d%%\n", game[0].economy.loanInterestRate);
    printf("=========================================\n");
}
