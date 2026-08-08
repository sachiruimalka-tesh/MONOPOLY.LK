#include <stdio.h>
#include <stdlib.h>
#include "types.h"
#include "functions.h"

/*========================================
    GLOBAL VARIABLES
========================================*/

extern Player players[MAX_PLAYERS];
extern Square board[BOARD_SIZE];

/* Note: the hotel/railway/utility rent multipliers, construction cost
   multiplier, insurance premium multiplier, closed-property tracker,
   income tax amount, anti-speculation flag, and event-card position
   used in this file are all fields of the single global `economy`
   struct (see types.h / economy.c) - nothing declared here needs to
   be a separate global variable any more.                            */

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

    switch(economy.currentCardIndex)
    {
        case 0:  /* Tourism Hype */

            printf("Tourism Hype : Hotels earn double rent for 5 rounds.\n");
            economy.hotelRentMultiplierPercent = 200;
            economy.hotelRentRoundsLeft = 5;
            break;

        case 1:  /* Fuel Shortage */

            printf("Fuel Shortage : Railway rent doubles for 5 rounds.\n");
            economy.railwayRentMultiplierPercent = 200;
            economy.railwayRentRoundsLeft = 5;
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
                economy.closedPropertyIndex = candidates[rand() % count];
                economy.closedPropertyRoundsLeft = 2;

                printf("Political Rally : %s is closed for 2 rounds.\n",
                       board[economy.closedPropertyIndex].name);
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

            economy.loanInterestRate -= 2;
            if(economy.loanInterestRate < 1)
                economy.loanInterestRate = 1;

            printf("Interest Rate Cut : Loan interest reduced by 2%%. Now %d%%.\n",
                   economy.loanInterestRate);
            break;

        case 8:  /* Interest Rate Increase */

            economy.loanInterestRate += 2;

            printf("Interest Rate Increase : Loan interest increased by 2%%. Now %d%%.\n",
                   economy.loanInterestRate);
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
            economy.utilityRentMultiplierPercent = 50;
            economy.utilityRentRoundsLeft = 3;
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
            economy.hotelRentMultiplierPercent = 150;
            economy.hotelRentRoundsLeft = 5;
            break;

        case 14:  /* Labour Strike */

            printf("Labour Strike : Construction suspended for 2 rounds.\n");
            economy.constructionSuspendedRoundsLeft = 2;
            break;

        case 15:  /* Insurance Discount */

            printf("Insurance Discount : Premiums reduced by 20%% for 10 rounds.\n");
            economy.insurancePremiumMultiplierPercent = 80;
            economy.insurancePremiumRoundsLeft = 10;
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
    economy.currentCardIndex = (economy.currentCardIndex + 1) % 20;
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

            economy.hotelRentMultiplierPercent = 200;
            economy.hotelRentRoundsLeft = 15;
            changeGroupValues(YELLOW, 15);   /* Galle Fort, Unawatuna, Hikkaduwa */
            break;

        case 1:  /* Fuel Crisis */

            printf("Fuel Crisis\n");
            printf("Railway rent doubles for 15 rounds.\n");
            printf("Property development costs increase 20%% for 15 rounds.\n");

            economy.railwayRentMultiplierPercent = 200;
            economy.railwayRentRoundsLeft = 15;
            economy.constructionCostMultiplierPercent = 120;
            economy.constructionCostRoundsLeft = 15;
            break;

        case 2:  /* Heavy Monsoon */

            printf("Heavy Monsoon\n");
            printf("Insurance premiums increase for 15 rounds.\n");
            printf("Coastal properties lose 10%% value.\n");

            economy.insurancePremiumMultiplierPercent = 115;
            economy.insurancePremiumRoundsLeft = 15;
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

            economy.loanInterestRate = applyRate(economy.loanInterestRate, 15);
            break;
        }

        case 4:  /* Stock Market Boom */

            printf("Stock Market Boom\n");
            printf("Property values increase 10%%. Loan interest decreases 10%%.\n");

            changeAllPropertyValues(10);
            economy.loanInterestRate = applyRate(economy.loanInterestRate, -10);
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

            economy.hotelRentMultiplierPercent = 50;
            economy.hotelRentRoundsLeft = 15;
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

            economy.incomeTaxAmount = applyRate(economy.incomeTaxAmount, 50);

            if(economy.incomeTaxAmount > 5000)
                economy.incomeTaxAmount = 5000;

            printf("Increase Property Tax\n");
            printf("Income Tax increased by 50%%. Now LKR %d.\n", economy.incomeTaxAmount);
            break;

        case 1:  /* Reduce Loan Interest */

            economy.loanInterestRate -= 2;
            if(economy.loanInterestRate < 1)
                economy.loanInterestRate = 1;

            printf("Reduce Loan Interest\n");
            printf("Interest decreased by 2%%. Now %d%%.\n", economy.loanInterestRate);
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

            economy.railwayRentMultiplierPercent = 125;
            economy.railwayRentRoundsLeft = 20;
            break;

        case 5:  /* Electricity Tariff Revision */

            printf("Electricity Tariff Revision\n");
            printf("Utility rents increase 20%% for 20 rounds.\n");

            economy.utilityRentMultiplierPercent = 120;
            economy.utilityRentRoundsLeft = 20;
            break;

        case 6:  /* Insurance Regulation */

            printf("Insurance Regulation\n");
            printf("Insurance premiums decrease 15%% for 20 rounds. Coverage unchanged.\n");

            economy.insurancePremiumMultiplierPercent = 85;
            economy.insurancePremiumRoundsLeft = 20;
            break;

        case 7:  /* Anti-Speculation Act */

            printf("Anti-Speculation Act\n");
            printf("Players may now own at most three undeveloped properties.\n");

            economy.antiSpeculationActive = 1;
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
    if(economy.hotelRentRoundsLeft > 0)
    {
        economy.hotelRentRoundsLeft--;
        if(economy.hotelRentRoundsLeft == 0)
            economy.hotelRentMultiplierPercent = 100;
    }

    if(economy.railwayRentRoundsLeft > 0)
    {
        economy.railwayRentRoundsLeft--;
        if(economy.railwayRentRoundsLeft == 0)
            economy.railwayRentMultiplierPercent = 100;
    }

    if(economy.utilityRentRoundsLeft > 0)
    {
        economy.utilityRentRoundsLeft--;
        if(economy.utilityRentRoundsLeft == 0)
            economy.utilityRentMultiplierPercent = 100;
    }

    if(economy.constructionCostRoundsLeft > 0)
    {
        economy.constructionCostRoundsLeft--;
        if(economy.constructionCostRoundsLeft == 0)
            economy.constructionCostMultiplierPercent = 100;
    }

    if(economy.insurancePremiumRoundsLeft > 0)
    {
        economy.insurancePremiumRoundsLeft--;
        if(economy.insurancePremiumRoundsLeft == 0)
            economy.insurancePremiumMultiplierPercent = 100;
    }

    if(economy.constructionSuspendedRoundsLeft > 0)
        economy.constructionSuspendedRoundsLeft--;

    if(economy.closedPropertyRoundsLeft > 0)
    {
        economy.closedPropertyRoundsLeft--;
        if(economy.closedPropertyRoundsLeft == 0)
            economy.closedPropertyIndex = -1;
    }
}
