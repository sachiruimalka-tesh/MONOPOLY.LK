#include <stdio.h>
#include <stdlib.h>
#include "types.h"
#include "functions.h"

/*========================================
    GLOBAL VARIABLES
========================================*/

extern Player players[MAX_PLAYERS];
extern Square board[BOARD_SIZE];

/* NOTE (simplification worth mentioning in the viva) : the Dynamic
   Market (every 10 rounds) and the Regional Development Cards
   (every 15 rounds) both use the SAME per-group arrays inside the
   `economy` struct. Since only one thing can be "the most recent
   event" for a group at a time, if a Market event and a Regional
   card happen to target the same group at once, whichever one's
   timer runs out first will reset the group back to normal - even
   if the other was technically still active. Building fully
   independent, stackable timers per group would need a much more
   complex data structure than fits this course, so this is a
   deliberate, documented trade-off.                                */

void initMarket(void)
{
    int i;

    for(i = 0; i < NO_GROUP; i++)
    {
        economy.groupValueMultiplier[i] = 100;
        economy.groupRentMultiplier[i] = 100;
        economy.groupRoundsLeft[i] = 0;
        economy.groupCooldownUntilRound[i] = 0;
    }

    economy.lastBoomGroup = -1;
    economy.lastDeclineGroup = -1;
}

const char *groupName(PropertyGroup group)
{
    switch(group)
    {
        case BROWN:      return "Brown";
        case LIGHT_BLUE: return "Light Blue";
        case PINK:       return "Pink";
        case ORANGE:     return "Orange";
        case RED:        return "Red";
        case YELLOW:     return "Yellow";
        case GREEN:      return "Green";
        case DARK_BLUE:  return "Dark Blue";
        default:         return "Unknown";
    }
}

/*========================================
    Pick a random group that is not
    currently in cooldown and is not one
    of the two groups we want to avoid.
========================================*/

PropertyGroup pickEligibleGroup(int currentRound, int avoid1, int avoid2)
{
    int candidates[NO_GROUP];
    int count;
    int g;

    count = 0;

    for(g = 0; g < NO_GROUP; g++)
    {
        if(g == avoid1 || g == avoid2)
            continue;

        if(economy.groupCooldownUntilRound[g] > currentRound)
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

void reviewPropertyMarket(int currentRound)
{
    PropertyGroup boomGroup;
    PropertyGroup declineGroup;

    boomGroup = pickEligibleGroup(currentRound, economy.lastBoomGroup, -1);
    declineGroup = pickEligibleGroup(currentRound, economy.lastDeclineGroup, boomGroup);

    printf("\n=== Property Market Review ===\n");

    printf("Market Boom : %s (values +20%%, rent +25%%) for 10 rounds.\n",
           groupName(boomGroup));

    printf("Market Decline : %s (values -15%%, rent -20%%) for 10 rounds.\n",
           groupName(declineGroup));

    economy.groupValueMultiplier[boomGroup] = 120;
    economy.groupRentMultiplier[boomGroup] = 125;
    economy.groupRoundsLeft[boomGroup] = 10;

    economy.groupValueMultiplier[declineGroup] = 85;
    economy.groupRentMultiplier[declineGroup] = 80;
    economy.groupRoundsLeft[declineGroup] = 10;

    /* Boom also raises construction costs everywhere for a while
       (reusing the multiplier already built in Phase 6)            */
    economy.constructionCostMultiplierPercent = 110;
    economy.constructionCostRoundsLeft = 10;

    economy.groupCooldownUntilRound[boomGroup] = currentRound + 30;
    economy.groupCooldownUntilRound[declineGroup] = currentRound + 30;

    economy.lastBoomGroup = boomGroup;
    economy.lastDeclineGroup = declineGroup;
}

/*========================================
    REGIONAL DEVELOPMENT CARDS (Table 4)
    One card drawn every 15 rounds, stays
    active for 15 rounds.
========================================*/

void drawRegionalCard(void)
{
    int choice;

    choice = rand() % 12;

    printf("\n=== Regional Development Card ===\n");

    switch(choice)
    {
        case 0:  /* Southern Tourism Boom */

            printf("Southern Tourism Boom : Galle Fort, Unawatuna and "
                   "Hikkaduwa rental income +40%%.\n");
            economy.groupRentMultiplier[YELLOW] = 140;
            economy.groupRoundsLeft[YELLOW] = 15;
            break;

        case 1:  /* Port City Expansion */

            printf("Port City Expansion : Pettah and Maradana values +25%%.\n");
            economy.groupValueMultiplier[BROWN] = 125;
            economy.groupRoundsLeft[BROWN] = 15;
            break;

        case 2:  /* IT Industry Growth */

            printf("IT Industry Growth : Maharagama, Nugegoda and "
                   "Kottawa values +20%%.\n");
            economy.groupValueMultiplier[PINK] = 120;
            economy.groupRoundsLeft[PINK] = 15;
            break;

        case 3:  /* Northern Development Programme */

            printf("Northern Development Programme : Jaffna Town, Nallur "
                   "and Trincomalee values +30%%.\n");
            economy.groupValueMultiplier[GREEN] = 130;
            economy.groupRoundsLeft[GREEN] = 15;
            break;

        case 4:  /* Tea Export Boom */

            printf("Tea Export Boom : Nuwara Eliya value +35%%.\n");
            economy.groupValueMultiplier[DARK_BLUE] = 135;
            economy.groupRoundsLeft[DARK_BLUE] = 15;
            break;

        case 5:  /* Airport Expansion */

            printf("Airport Expansion : Negombo, Katunayake and "
                   "Ja-Ela rents +30%%.\n");
            economy.groupRentMultiplier[ORANGE] = 130;
            economy.groupRoundsLeft[ORANGE] = 15;
            break;

        case 6:  /* University City Growth */

            printf("University City Growth : Peradeniya and "
                   "Kandy City values +20%%.\n");
            economy.groupValueMultiplier[RED] = 120;
            economy.groupRoundsLeft[RED] = 15;
            break;

        case 7:  /* Beach Pollution */

            printf("Beach Pollution : Southern coastal rents -30%%.\n");
            economy.groupRentMultiplier[YELLOW] = 70;
            economy.groupRoundsLeft[YELLOW] = 15;
            break;

        case 8:  /* Flood Damage */

            printf("Flood Damage : Low-lying coastal properties lose 20%% value.\n");
            economy.groupValueMultiplier[YELLOW] = 80;
            economy.groupRoundsLeft[YELLOW] = 15;
            break;

        case 9:  /* Transport Strike */

            printf("Transport Strike : Railway revenue reduced by 40%%.\n");
            economy.railwayRentMultiplierPercent = 60;
            economy.railwayRentRoundsLeft = 15;
            break;

        case 10:  /* Electricity Tariff Increase */

            printf("Electricity Tariff Increase : Utility rent +25%%.\n");
            economy.utilityRentMultiplierPercent = 125;
            economy.utilityRentRoundsLeft = 15;
            break;

        case 11:  /* Water Shortage */

            printf("Water Shortage : Utility revenue +20%%.\n");
            economy.utilityRentMultiplierPercent = 120;
            economy.utilityRentRoundsLeft = 15;
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

void decrementMarketTimers(void)
{
    int g;

    for(g = 0; g < NO_GROUP; g++)
    {
        if(economy.groupRoundsLeft[g] > 0)
        {
            economy.groupRoundsLeft[g]--;

            if(economy.groupRoundsLeft[g] == 0)
            {
                economy.groupValueMultiplier[g] = 100;
                economy.groupRentMultiplier[g] = 100;
            }
        }
    }
}

/*========================================
    Rule-LK 36 : show the currently active
    market conditions. Called at the end of
    every round.
========================================*/

void displayMarketConditions(void)
{
    int g;
    int shown;

    printf("\n=========================================\n");
    printf("Current Market Conditions\n");
    printf("=========================================\n");

    shown = 0;

    for(g = 0; g < NO_GROUP; g++)
    {
        if(economy.groupRoundsLeft[g] > 0)
        {
            printf("%s : Value x%d%%, Rent x%d%% (%d rounds remaining)\n",
                   groupName((PropertyGroup)g),
                   economy.groupValueMultiplier[g],
                   economy.groupRentMultiplier[g],
                   economy.groupRoundsLeft[g]);

            shown = 1;
        }
    }

    if(!shown)
        printf("No active market booms or declines right now.\n");

    printf("Inflation Rate : %+d%%\n", economy.inflationRate);
    printf("Current Loan Interest : %d%%\n", economy.loanInterestRate);
    printf("=========================================\n");
}
