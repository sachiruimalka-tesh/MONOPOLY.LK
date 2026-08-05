#include <stdio.h>
#include <stdlib.h>
#include "types.h"
#include "functions.h"

/*========================================
    GLOBAL VARIABLES
========================================*/

extern Player players[MAX_PLAYERS];
extern Square board[BOARD_SIZE];

/* Definitions of the "current economic condition" variables that
   were declared extern in types.h                                */
int hotelRentMultiplierPercent = 100;
int hotelRentRoundsLeft = 0;

int railwayRentMultiplierPercent = 100;
int railwayRentRoundsLeft = 0;

int utilityRentMultiplierPercent = 100;
int utilityRentRoundsLeft = 0;

int constructionCostMultiplierPercent = 100;
int constructionCostRoundsLeft = 0;

int insurancePremiumMultiplierPercent = 100;
int insurancePremiumRoundsLeft = 0;

int constructionSuspendedRoundsLeft = 0;

int closedPropertyIndex = -1;
int closedPropertyRoundsLeft = 0;

int incomeTaxAmount = 1000;

int antiSpeculationActive = 0;

/* Which National Event Card is on top of the deck right now.
   The deck is just a fixed list of 20 cards that we cycle through
   in order - drawing a card and "returning it to the bottom" is the
   same as simply moving on to the next index, then wrapping around. */
int currentCardIndex = 0;

/*========================================
    SMALL HELPERS
========================================*/

/* Change every property's purchasePrice by ratePercent (Rule-LK 14 style) */
void changeAllPropertyValues(int ratePercent)
{
    int i;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type == PROPERTY)
        {
            board[i].property.purchasePrice =
                applyRate(board[i].property.purchasePrice, ratePercent);
        }
    }
}

/* Change purchasePrice for just one colour group */
void changeGroupValues(PropertyGroup group, int ratePercent)
{
    int i;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type == PROPERTY && board[i].property.group == group)
        {
            board[i].property.purchasePrice =
                applyRate(board[i].property.purchasePrice, ratePercent);
        }
    }
}

/* Change house construction cost for every property */
void changeAllHouseCosts(int ratePercent)
{
    int i;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(board[i].type == PROPERTY)
        {
            board[i].property.houseCost =
                applyRate(board[i].property.houseCost, ratePercent);
        }
    }
}

/*========================================
    NATIONAL EVENT CARDS (Appendix A)
    Drawn whenever a player lands on an
    EVENT square.
========================================*/

void executeEvent(int playerIndex)
{
    printf("\n*** NATIONAL EVENT CARD ***\n");

    switch(currentCardIndex)
    {
        case 0:  /* Tourism Hype */

            printf("Tourism Hype : Hotels earn double rent for 5 rounds.\n");
            hotelRentMultiplierPercent = 200;
            hotelRentRoundsLeft = 5;
            break;

        case 1:  /* Fuel Shortage */

            printf("Fuel Shortage : Railway rent doubles for 5 rounds.\n");
            railwayRentMultiplierPercent = 200;
            railwayRentRoundsLeft = 5;
            break;

        case 2:  /* Heavy Floods */

            printf("Heavy Floods : a random coastal property is damaged.\n");
            triggerDisaster();
            break;

        case 3:  /* Political Rally */
        {
            int candidates[BOARD_SIZE];
            int count;
            int i;

            count = 0;

            for(i = 0; i < BOARD_SIZE; i++)
            {
                if(board[i].type == PROPERTY && board[i].property.owner != -1)
                {
                    candidates[count] = i;
                    count++;
                }
            }

            if(count > 0)
            {
                closedPropertyIndex = candidates[rand() % count];
                closedPropertyRoundsLeft = 2;

                printf("Political Rally : %s is closed for 2 rounds.\n",
                       board[closedPropertyIndex].name);
            }
            else
            {
                printf("Political Rally : no owned property to close.\n");
            }
            break;
        }

        case 4:  /* Stock Market Rise */

            printf("Stock Market Rise : All property values increase by 10%%.\n");
            changeAllPropertyValues(10);
            break;

        case 5:  /* Economic Downturn */

            printf("Economic Downturn : Property values decrease by 15%%.\n");
            changeAllPropertyValues(-15);
            break;

        case 6:  /* Housing Subsidy */

            printf("Housing Subsidy : House construction cost reduced by 30%%.\n");
            changeAllHouseCosts(-30);
            break;

        case 7:  /* Interest Rate Cut */

            currentLoanInterestRate -= 2;
            if(currentLoanInterestRate < 1)
                currentLoanInterestRate = 1;

            printf("Interest Rate Cut : Loan interest reduced by 2%%. Now %d%%.\n",
                   currentLoanInterestRate);
            break;

        case 8:  /* Interest Rate Increase */

            currentLoanInterestRate += 2;

            printf("Interest Rate Increase : Loan interest increased by 2%%. Now %d%%.\n",
                   currentLoanInterestRate);
            break;

        case 9:  /* Tax Amnesty */
        {
            int i;

            printf("Tax Amnesty : Each player receives LKR 2,000.\n");

            for(i = 0; i < MAX_PLAYERS; i++)
                receiveMoney(i, 2000);

            break;
        }

        case 10:  /* Power Failure */

            printf("Power Failure : Utility income halved for 3 rounds.\n");
            utilityRentMultiplierPercent = 50;
            utilityRentRoundsLeft = 3;
            break;

        case 11:  /* Foreign Funding - treating Orange group as "commercial" */

            printf("Foreign Funding : Commercial property values increase by 15%%.\n");
            changeGroupValues(ORANGE, 15);
            break;

        case 12:  /* Port Expansion */
        {
            int i;

            printf("Port Expansion : Railway station values increase by 20%%.\n");

            for(i = 0; i < BOARD_SIZE; i++)
            {
                if(board[i].type == RAILWAY)
                {
                    board[i].property.purchasePrice =
                        applyRate(board[i].property.purchasePrice, 20);
                }
            }
            break;
        }

        case 13:  /* Festival Season */

            printf("Festival Season : Hotels receive 50%% additional rent for 5 rounds.\n");
            hotelRentMultiplierPercent = 150;
            hotelRentRoundsLeft = 5;
            break;

        case 14:  /* Labour Strike */

            printf("Labour Strike : Construction suspended for 2 rounds.\n");
            constructionSuspendedRoundsLeft = 2;
            break;

        case 15:  /* Insurance Discount */

            printf("Insurance Discount : Premiums reduced by 20%% for 10 rounds.\n");
            insurancePremiumMultiplierPercent = 80;
            insurancePremiumRoundsLeft = 10;
            break;

        case 16:  /* Property Revaluation */
        {
            PropertyGroup group;

            group = (PropertyGroup)(rand() % NO_GROUP);

            printf("Property Revaluation : one property group appreciates by 15%%.\n");
            changeGroupValues(group, 15);
            break;
        }

        case 17:  /* Currency Depreciation */
        {
            int i;

            printf("Currency Depreciation : Construction costs increase by 10%%.\n");

            for(i = 0; i < BOARD_SIZE; i++)
            {
                if(board[i].type == PROPERTY)
                {
                    board[i].property.houseCost =
                        applyRate(board[i].property.houseCost, 10);
                    board[i].property.hotelCost =
                        applyRate(board[i].property.hotelCost, 10);
                }
            }
            break;
        }

        case 18:  /* Government Grant */
        {
            int lucky;

            lucky = rand() % MAX_PLAYERS;

            printf("Government Grant : %s receives LKR 5,000.\n",
                   players[lucky].name);

            receiveMoney(lucky, 5000);
            break;
        }

        case 19:  /* National Disaster */

            printf("National Disaster : a random developed property is damaged.\n");
            triggerDisaster();
            break;

        default:

            break;
    }

    /* "Return the card to the bottom of the deck" - just move on */
    currentCardIndex = (currentCardIndex + 1) % 20;
}

/*========================================
    ECONOMIC EVENTS (Section 2.5)
    Happen automatically every 15 rounds,
    and affect every player.
========================================*/

void triggerEconomicEvent(void)
{
    int choice;

    choice = rand() % 8;

    printf("\n=== Economic Event ===\n");

    switch(choice)
    {
        case 0:  /* Tourism Boom */

            printf("Tourism Boom\n");
            printf("Hotels receive double rent for 15 rounds.\n");
            printf("Southern Province properties increase in value by 15%%.\n");

            hotelRentMultiplierPercent = 200;
            hotelRentRoundsLeft = 15;
            changeGroupValues(YELLOW, 15);   /* Galle Fort, Unawatuna, Hikkaduwa */
            break;

        case 1:  /* Fuel Crisis */

            printf("Fuel Crisis\n");
            printf("Railway rent doubles for 15 rounds.\n");
            printf("Property development costs increase 20%% for 15 rounds.\n");

            railwayRentMultiplierPercent = 200;
            railwayRentRoundsLeft = 15;
            constructionCostMultiplierPercent = 120;
            constructionCostRoundsLeft = 15;
            break;

        case 2:  /* Heavy Monsoon */

            printf("Heavy Monsoon\n");
            printf("Insurance premiums increase for 15 rounds.\n");
            printf("Coastal properties lose 10%% value.\n");

            insurancePremiumMultiplierPercent = 115;
            insurancePremiumRoundsLeft = 15;
            changeGroupValues(YELLOW, -10);
            break;

        case 3:  /* Economic Recession */
        {
            int i;

            printf("Economic Recession\n");
            printf("Property values decrease 15%%. Rent decreases 10%%.\n");
            printf("Loan interest increases by 15%%.\n");

            changeAllPropertyValues(-15);

            for(i = 0; i < BOARD_SIZE; i++)
            {
                if(board[i].type == PROPERTY)
                {
                    board[i].property.baseRent =
                        applyRate(board[i].property.baseRent, -10);
                }
            }

            currentLoanInterestRate = applyRate(currentLoanInterestRate, 15);
            break;
        }

        case 4:  /* Stock Market Boom */

            printf("Stock Market Boom\n");
            printf("Property values increase 10%%. Loan interest decreases 10%%.\n");

            changeAllPropertyValues(10);
            currentLoanInterestRate = applyRate(currentLoanInterestRate, -10);
            break;

        case 5:  /* Government Housing Programme */

            printf("Government Housing Programme\n");
            printf("House construction costs reduce 25%%.\n");

            changeAllHouseCosts(-25);
            break;

        case 6:  /* Foreign Investment */

            printf("Foreign Investment\n");
            printf("Commercial properties increase 20%%.\n");

            changeGroupValues(ORANGE, 20);
            break;

        case 7:  /* Political Unrest */

            printf("Political Unrest\n");
            printf("Hotel rent drops by 50%% for 15 rounds.\n");

            hotelRentMultiplierPercent = 50;
            hotelRentRoundsLeft = 15;
            break;

        default:

            break;
    }
}

/*========================================
    GOVERNMENT REGULATIONS (Section 2.7)
    Happen automatically every 20 rounds.
========================================*/

void triggerGovernmentRegulation(void)
{
    int choice;

    choice = rand() % 8;

    printf("\n=== Government Regulation ===\n");

    switch(choice)
    {
        case 0:  /* Increase Property Tax */

            incomeTaxAmount = applyRate(incomeTaxAmount, 50);

            if(incomeTaxAmount > 5000)
                incomeTaxAmount = 5000;

            printf("Increase Property Tax\n");
            printf("Income Tax increased by 50%%. Now LKR %d.\n", incomeTaxAmount);
            break;

        case 1:  /* Reduce Loan Interest */

            currentLoanInterestRate -= 2;
            if(currentLoanInterestRate < 1)
                currentLoanInterestRate = 1;

            printf("Reduce Loan Interest\n");
            printf("Interest decreased by 2%%. Now %d%%.\n", currentLoanInterestRate);
            break;

        case 2:  /* Housing Subsidy */

            printf("Housing Subsidy\n");
            printf("House construction costs reduced by 30%%.\n");

            changeAllHouseCosts(-30);
            break;

        case 3:  /* Luxury Property Tax */
        {
            int i;
            int tax;

            printf("Luxury Property Tax\n");
            printf("Hotels pay a maintenance tax of 25%% of their value.\n");

            for(i = 0; i < BOARD_SIZE; i++)
            {
                if(board[i].type == PROPERTY && board[i].property.hotel &&
                   board[i].property.owner != -1)
                {
                    tax = (currentMarketValue(i) * 25) / 100;
                    payMoney(board[i].property.owner, tax);
                }
            }
            break;
        }

        case 4:  /* Railway Modernization */

            printf("Railway Modernization\n");
            printf("Railway rents increase 25%% for 20 rounds.\n");

            railwayRentMultiplierPercent = 125;
            railwayRentRoundsLeft = 20;
            break;

        case 5:  /* Electricity Tariff Revision */

            printf("Electricity Tariff Revision\n");
            printf("Utility rents increase 20%% for 20 rounds.\n");

            utilityRentMultiplierPercent = 120;
            utilityRentRoundsLeft = 20;
            break;

        case 6:  /* Insurance Regulation */

            printf("Insurance Regulation\n");
            printf("Insurance premiums decrease 15%% for 20 rounds. Coverage unchanged.\n");

            insurancePremiumMultiplierPercent = 85;
            insurancePremiumRoundsLeft = 20;
            break;

        case 7:  /* Anti-Speculation Act */

            printf("Anti-Speculation Act\n");
            printf("Players may now own at most three undeveloped properties.\n");

            antiSpeculationActive = 1;
            break;

        default:

            break;
    }
}

/*========================================
    Count down every temporary event timer.
    Called once at the end of each round.
========================================*/

void decrementEventTimers(void)
{
    if(hotelRentRoundsLeft > 0)
    {
        hotelRentRoundsLeft--;
        if(hotelRentRoundsLeft == 0)
            hotelRentMultiplierPercent = 100;
    }

    if(railwayRentRoundsLeft > 0)
    {
        railwayRentRoundsLeft--;
        if(railwayRentRoundsLeft == 0)
            railwayRentMultiplierPercent = 100;
    }

    if(utilityRentRoundsLeft > 0)
    {
        utilityRentRoundsLeft--;
        if(utilityRentRoundsLeft == 0)
            utilityRentMultiplierPercent = 100;
    }

    if(constructionCostRoundsLeft > 0)
    {
        constructionCostRoundsLeft--;
        if(constructionCostRoundsLeft == 0)
            constructionCostMultiplierPercent = 100;
    }

    if(insurancePremiumRoundsLeft > 0)
    {
        insurancePremiumRoundsLeft--;
        if(insurancePremiumRoundsLeft == 0)
            insurancePremiumMultiplierPercent = 100;
    }

    if(constructionSuspendedRoundsLeft > 0)
        constructionSuspendedRoundsLeft--;

    if(closedPropertyRoundsLeft > 0)
    {
        closedPropertyRoundsLeft--;
        if(closedPropertyRoundsLeft == 0)
            closedPropertyIndex = -1;
    }
}
