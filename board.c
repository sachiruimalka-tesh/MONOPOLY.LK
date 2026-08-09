#include <stdio.h>
#include <string.h>
#include "types.h"
#include "functions.h"

/*=====================================
    NOTE: there is no global board array any more. Every function
    below receives the whole GameState as an array parameter (named `game`),
    and writes into game[0].board[...] instead of a global variable.
=====================================*/

void setProperty(GameState game[],
                 int index,
                 char name[],
                 PropertyGroup group,
                 int purchasePrice,
                 int baseRent,
                 int mortgageValue,
                 int houseCost,
                 int hotelCost)
{
    game[0].board[index].index = index;
    game[0].board[index].type = PROPERTY;

    strcpy(game[0].board[index].name, name);
    strcpy(game[0].board[index].property.name, name);

    game[0].board[index].property.group = group;

    game[0].board[index].property.purchasePrice = purchasePrice;
    game[0].board[index].property.baseRent = baseRent;
    game[0].board[index].property.mortgageValue = mortgageValue;

    game[0].board[index].property.houseCost = houseCost;
    game[0].board[index].property.hotelCost = hotelCost;

    game[0].board[index].property.owner = -1;

    game[0].board[index].property.houses = 0;
    game[0].board[index].property.hotel = 0;

    game[0].board[index].property.mortgaged = 0;

    game[0].board[index].property.loanLocked = 0;

    game[0].board[index].property.insurance = NO_INSURANCE;
    game[0].board[index].property.insuranceRoundsLeft = 0;

    game[0].board[index].property.damaged = 0;
    game[0].board[index].property.repairCostOwed = 0;

    game[0].board[index].property.age = 0;
    game[0].board[index].property.depreciation = 0;
    game[0].board[index].property.condition = 100;

    game[0].board[index].property.roundsSinceMaintenance = 0;
    game[0].board[index].property.structurallyDamaged = 0;
    game[0].board[index].property.preDamagePurchasePrice = 0;
    game[0].board[index].property.preDamageBaseRent = 0;
    game[0].board[index].property.maintenanceCostMultiplierPercent = 100;
}

void setRailway(GameState game[], int index, char name[], int purchasePrice)
{
    game[0].board[index].index = index;
    game[0].board[index].type = RAILWAY;

    strcpy(game[0].board[index].name, name);
    strcpy(game[0].board[index].property.name, name);

    game[0].board[index].property.purchasePrice = purchasePrice;
    game[0].board[index].property.mortgageValue = purchasePrice / 2;

    game[0].board[index].property.owner = -1;
    game[0].board[index].property.mortgaged = 0;
    game[0].board[index].property.loanLocked = 0;

    /* Railways/utilities never have houses, a hotel, insurance, or
       age/condition tracking, but since GameState is now an ordinary
       local variable (not a global), C will NOT auto-zero these for
       us the way it used to. We zero them explicitly here so every
       field is always in a known, safe state.                       */
    game[0].board[index].property.houses = 0;
    game[0].board[index].property.hotel = 0;
    game[0].board[index].property.insurance = NO_INSURANCE;
    game[0].board[index].property.insuranceRoundsLeft = 0;
    game[0].board[index].property.damaged = 0;
    game[0].board[index].property.repairCostOwed = 0;
    game[0].board[index].property.age = 0;
    game[0].board[index].property.depreciation = 0;
    game[0].board[index].property.condition = 100;
    game[0].board[index].property.roundsSinceMaintenance = 0;
    game[0].board[index].property.structurallyDamaged = 0;
    game[0].board[index].property.preDamagePurchasePrice = 0;
    game[0].board[index].property.preDamageBaseRent = 0;
    game[0].board[index].property.maintenanceCostMultiplierPercent = 100;
    game[0].board[index].property.baseRent = 0;
    game[0].board[index].property.houseCost = 0;
    game[0].board[index].property.hotelCost = 0;
}

void setUtility(GameState game[], int index, char name[], int purchasePrice)
{
    game[0].board[index].index = index;
    game[0].board[index].type = UTILITY;

    strcpy(game[0].board[index].name, name);
    strcpy(game[0].board[index].property.name, name);

    game[0].board[index].property.purchasePrice = purchasePrice;
    game[0].board[index].property.mortgageValue = purchasePrice / 2;

    game[0].board[index].property.owner = -1;
    game[0].board[index].property.mortgaged = 0;
    game[0].board[index].property.loanLocked = 0;

    game[0].board[index].property.houses = 0;
    game[0].board[index].property.hotel = 0;
    game[0].board[index].property.insurance = NO_INSURANCE;
    game[0].board[index].property.insuranceRoundsLeft = 0;
    game[0].board[index].property.damaged = 0;
    game[0].board[index].property.repairCostOwed = 0;
    game[0].board[index].property.age = 0;
    game[0].board[index].property.depreciation = 0;
    game[0].board[index].property.condition = 100;
    game[0].board[index].property.roundsSinceMaintenance = 0;
    game[0].board[index].property.structurallyDamaged = 0;
    game[0].board[index].property.preDamagePurchasePrice = 0;
    game[0].board[index].property.preDamageBaseRent = 0;
    game[0].board[index].property.maintenanceCostMultiplierPercent = 100;
    game[0].board[index].property.baseRent = 0;
    game[0].board[index].property.houseCost = 0;
    game[0].board[index].property.hotelCost = 0;
}

void setSpecialSquare(GameState game[],
                      int index,
                      SquareType type,
                      char name[])
{
    game[0].board[index].index = index;

    game[0].board[index].type = type;

    strcpy(game[0].board[index].name, name);

    /* BUG FIX : special squares (GO, TAX, EVENT, JAIL, BANK,
       INSURANCE, etc.) were never given an owner. Since C fills
       unused fields with 0, `owner` defaulted to 0 - but 0 is a
       real player index (Aggressive Investor), NOT "nobody"! This
       made every function that scans the board for "does player 0
       own this square?" incorrectly think Aggressive Investor owned
       every special square on the board. -1 is the correct value
       for "nobody owns this," matching every other setXxx function. */
    game[0].board[index].property.owner = -1;
    game[0].board[index].property.mortgaged = 0;
    game[0].board[index].property.loanLocked = 0;
    game[0].board[index].property.houses = 0;
    game[0].board[index].property.hotel = 0;
    game[0].board[index].property.insurance = NO_INSURANCE;
}

void initializeBoard(GameState game[])
{
    /* ---------- Special Squares ---------- */

    setSpecialSquare(game, 0, GO, "GO");
    setSpecialSquare(game, 2, EVENT, "Community Development Fund");
    setSpecialSquare(game, 4, TAX, "Income Tax");
    setSpecialSquare(game, 7, EVENT, "National Event Card");
    setSpecialSquare(game, 10, JAIL, "Jail / Just Visiting");
    setSpecialSquare(game, 17, INSURANCE, "Sri Lanka Insurance");
    setSpecialSquare(game, 20, FREE_PARKING, "Free Parking");
    setSpecialSquare(game, 22, EVENT, "National Event Card");
    setSpecialSquare(game, 30, GO_TO_JAIL, "Go To Jail");
    setSpecialSquare(game, 33, INSURANCE, "Ceylinco Insurance");
    setSpecialSquare(game, 36, EVENT, "National Event Card");
    setSpecialSquare(game, 38, BANK, "Bank of Ceylon");

    /* ---------- Railways ---------- */

    setRailway(game, 5, "Colombo Fort Railway Station", 1500);
    setRailway(game, 15, "Kandy Railway Station", 1500);
    setRailway(game, 25, "Galle Railway Station", 1500);
    setRailway(game, 35, "Jaffna Railway Station", 1500);

    /* ---------- Utilities ---------- */

    setUtility(game, 12, "Ceylon Electricity Board", 1500);
    setUtility(game, 28, "National Water Supply and Drainage Board", 1500);

    /* ---------- Brown ---------- */

    setProperty(game, 1,"Pettah",BROWN,1500,100,750,500,2000);
    setProperty(game, 3,"Maradana",BROWN,1800,120,900,500,2000);

    /* ---------- Light Blue ---------- */

    setProperty(game, 6,"Bambalapitiya",LIGHT_BLUE,2500,180,1250,750,3000);
    setProperty(game, 8,"Wellawatte",LIGHT_BLUE,2700,200,1350,750,3000);
    setProperty(game, 9,"Mount Lavinia",LIGHT_BLUE,3000,220,1500,750,3000);

    /* ---------- Pink ---------- */

    setProperty(game, 11,"Nugegoda",PINK,3500,260,1750,1000,4000);
    setProperty(game, 13,"Maharagama",PINK,3800,280,1900,1000,4000);
    setProperty(game, 14,"Kottawa",PINK,4000,300,2000,1000,4000);

    /* ---------- Orange ---------- */

    setProperty(game, 16,"Negombo",ORANGE,4500,350,2250,1250,5000);
    setProperty(game, 18,"Katunayake",ORANGE,4700,370,2350,1250,5000);
    setProperty(game, 19,"Ja-Ela",ORANGE,5000,400,2500,1250,5000);

    /* ---------- Red ---------- */

    setProperty(game, 21,"Kandy City",RED,5500,450,2750,1500,6000);
    setProperty(game, 23,"Peradeniya",RED,5800,480,2900,1500,6000);
    setProperty(game, 24,"Katugastota",RED,6000,500,3000,1500,6000);

    /* ---------- Yellow ---------- */

    setProperty(game, 26,"Galle Fort",YELLOW,6500,600,3250,2000,8000);
    setProperty(game, 27,"Unawatuna",YELLOW,6800,620,3400,2000,8000);
    setProperty(game, 29,"Hikkaduwa",YELLOW,7000,650,3500,2000,8000);

    /* ---------- Green ---------- */

    setProperty(game, 31,"Jaffna Town",GREEN,8000,750,4000,2500,10000);
    setProperty(game, 32,"Nallur",GREEN,8300,780,4150,2500,10000);
    setProperty(game, 34,"Trincomalee",GREEN,8500,800,4250,2500,10000);

    /* ---------- Dark Blue ---------- */

    setProperty(game, 37,"Nuwara Eliya",DARK_BLUE,10000,1000,5000,3000,12000);
    setProperty(game, 39,"Galle Face",DARK_BLUE,12000,1200,6000,3000,12000);
}

void displayBoard(GameState game[])
{
    int i;

    printf("\n========== BOARD ==========\n");

    for(i = 0; i < BOARD_SIZE; i++)
    {
        printf("%2d  %-35s", i, game[0].board[i].name);

        if(game[0].board[i].type == PROPERTY)
        {
            printf(" Price : %5d  Rent : %4d",
                   game[0].board[i].property.purchasePrice,
                   game[0].board[i].property.baseRent);
        }

        printf("\n");
    }
}
