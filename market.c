#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "types.h"
#include "functions.h"

/*========================================
    NOTE (simplification worth mentioning in the viva) : the Dynamic
    Market (every 10 rounds) and the Regional Development Cards
    (every 15 rounds) both use the SAME per-group arrays inside the
    game[0].economy struct. Since only one thing can be "the most
    recent event" for a group at a time, if a Market event and a
    Regional card happen to target the same group at once, whichever
    one's timer runs out first will reset the group back to normal -
    even if the other was technically still active. Building fully
    independent, stackable timers per group would need a much more
    complex data structure than fits this course, so this is a
    deliberate, documented trade-off.

    Also no global variables and no pointers here - everything reads
    and writes through the GameState array parameter `game`.
========================================*/

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

/* Pure lookup, no game state needed. Instead of returning a pointer
   to the text (const char *), it copies the name into a buffer the
   caller already owns - buffer must be at least 12 characters.      */
void groupName(PropertyGroup group, char buffer[])
{
    switch(group)
    {
        case BROWN:      strcpy(buffer, "Brown");      break;
        case LIGHT_BLUE: strcpy(buffer, "Light Blue"); break;
        case PINK:       strcpy(buffer, "Pink");       break;
        case ORANGE:     strcpy(buffer, "Orange");     break;
        case RED:        strcpy(buffer, "Red");        break;
        case YELLOW:     strcpy(buffer, "Yellow");     break;
        case GREEN:      strcpy(buffer, "Green");      break;
        case DARK_BLUE:  strcpy(buffer, "Dark Blue");  break;
        default:         strcpy(buffer, "Unknown");    break;
    }
}

/*========================================
    Pick a random group that is not
    currently in cooldown and is not one
    of the two groups we want to avoid.
========================================*/

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
    {
        /* Nothing eligible (rare) - just pick anything except avoid1 */
        return (PropertyGroup)((avoid1 + 1) % NO_GROUP);
    }

    return (PropertyGroup)candidates[rand() % count];
}

/*========================================
    DYNAMIC PROPERTY MARKET (Rule-LK 30-34)
    Runs every 10 rounds.
========================================*/

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

    printf("Market Boom : %s (values +20%%, rent +25%%) for 10 rounds.\n",
           boomName);

    printf("Market Decline : %s (values -15%%, rent -20%%) for 10 rounds.\n",
           declineName);

    game[0].economy.groupValueMultiplier[boomGroup] = 120;
    game[0].economy.groupRentMultiplier[boomGroup] = 125;
    game[0].economy.groupRoundsLeft[boomGroup] = 10;

    game[0].economy.groupValueMultiplier[declineGroup] = 85;
    game[0].economy.groupRentMultiplier[declineGroup] = 80;
    game[0].economy.groupRoundsLeft[declineGroup] = 10;

    /* Boom also raises construction costs everywhere for a while
       (reusing the multiplier already built in Phase 6)            */
    game[0].economy.constructionCostMultiplierPercent = 110;
    game[0].economy.constructionCostRoundsLeft = 10;

    game[0].economy.groupCooldownUntilRound[boomGroup] = currentRound + 30;
    game[0].economy.groupCooldownUntilRound[declineGroup] = currentRound + 30;

    game[0].economy.lastBoomGroup = boomGroup;
    game[0].economy.lastDeclineGroup = declineGroup;
}

/*========================================
    REGIONAL DEVELOPMENT CARDS (Table 4)
    One card drawn every 15 rounds, stays
    active for 15 rounds.
========================================*/

void drawRegionalCard(GameState game[])
{
    int choice;

    choice = rand() % 12;

    printf("\n=== Regional Development Card ===\n");

    switch(choice)
    {
        case 0:  /* Southern Tourism Boom */

            printf("Southern Tourism Boom : Galle Fort, Unawatuna and "
                   "Hikkaduwa rental income +40%%.\n");
            game[0].economy.groupRentMultiplier[YELLOW] = 140;
            game[0].economy.groupRoundsLeft[YELLOW] = 15;
            break;

        case 1:  /* Port City Expansion */

            printf("Port City Expansion : Pettah and Maradana values +25%%.\n");
            game[0].economy.groupValueMultiplier[BROWN] = 125;
            game[0].economy.groupRoundsLeft[BROWN] = 15;
            break;

        case 2:  /* IT Industry Growth */

            printf("IT Industry Growth : Maharagama, Nugegoda and "
                   "Kottawa values +20%%.\n");
            game[0].economy.groupValueMultiplier[PINK] = 120;
            game[0].economy.groupRoundsLeft[PINK] = 15;
            break;

        case 3:  /* Northern Development Programme */

            printf("Northern Development Programme : Jaffna Town, Nallur "
                   "and Trincomalee values +30%%.\n");
            game[0].economy.groupValueMultiplier[GREEN] = 130;
            game[0].economy.groupRoundsLeft[GREEN] = 15;
            break;

        case 4:  /* Tea Export Boom */

            printf("Tea Export Boom : Nuwara Eliya value +35%%.\n");
            game[0].economy.groupValueMultiplier[DARK_BLUE] = 135;
            game[0].economy.groupRoundsLeft[DARK_BLUE] = 15;
            break;

        case 5:  /* Airport Expansion */

            printf("Airport Expansion : Negombo, Katunayake and "
                   "Ja-Ela rents +30%%.\n");
            game[0].economy.groupRentMultiplier[ORANGE] = 130;
            game[0].economy.groupRoundsLeft[ORANGE] = 15;
            break;

        case 6:  /* University City Growth */

            printf("University City Growth : Peradeniya and "
                   "Kandy City values +20%%.\n");
            game[0].economy.groupValueMultiplier[RED] = 120;
            game[0].economy.groupRoundsLeft[RED] = 15;
            break;

        case 7:  /* Beach Pollution */

            printf("Beach Pollution : Southern coastal rents -30%%.\n");
            game[0].economy.groupRentMultiplier[YELLOW] = 70;
            game[0].economy.groupRoundsLeft[YELLOW] = 15;
            break;

        case 8:  /* Flood Damage */

            printf("Flood Damage : Low-lying coastal properties lose 20%% value.\n");
            game[0].economy.groupValueMultiplier[YELLOW] = 80;
            game[0].economy.groupRoundsLeft[YELLOW] = 15;
            break;

        case 9:  /* Transport Strike */

            printf("Transport Strike : Railway revenue reduced by 40%%.\n");
            game[0].economy.railwayRentMultiplierPercent = 60;
            game[0].economy.railwayRentRoundsLeft = 15;
            break;

        case 10:  /* Electricity Tariff Increase */

            printf("Electricity Tariff Increase : Utility rent +25%%.\n");
            game[0].economy.utilityRentMultiplierPercent = 125;
            game[0].economy.utilityRentRoundsLeft = 15;
            break;

        case 11:  /* Water Shortage */

            printf("Water Shortage : Utility revenue +20%%.\n");
            game[0].economy.utilityRentMultiplierPercent = 120;
            game[0].economy.utilityRentRoundsLeft = 15;
            break;

        default:

            break;
    }
}

/*========================================
    Count down the group timers and reset
    anything that has expired back to
    normal (Rule-LK 35). Called once at the
    end of every round.
========================================*/

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

/*========================================
    Rule-LK 36 : show the currently active
    market conditions. Called at the end of
    every round.
========================================*/

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
