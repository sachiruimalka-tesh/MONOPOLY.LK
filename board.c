#include <stdio.h>
#include <string.h>
#include "types.h"
#include "functions.h"
/*=====================================
        GLOBAL BOARD
=====================================*/

Square board[BOARD_SIZE];

/*=====================================
    FUNCTION PROTOTYPES
=====================================*/

void initializeBoard(void);

void setProperty(int index,
                 char name[],
                 PropertyGroup group,
                 int purchasePrice,
                 int baseRent,
                 int mortgageValue,
                 int houseCost,
                 int hotelCost);

void setRailway(int index, char name[], int purchasePrice);

void setUtility(int index, char name[], int purchasePrice);

void setSpecialSquare(int index,
                      SquareType type,
                      char name[]);

void displayBoard(void);

void setProperty(int index,
                 char name[],
                 PropertyGroup group,
                 int purchasePrice,
                 int baseRent,
                 int mortgageValue,
                 int houseCost,
                 int hotelCost)
{
    board[index].index = index;
    board[index].type = PROPERTY;

    strcpy(board[index].name, name);
    strcpy(board[index].property.name, name);

    board[index].property.group = group;

    board[index].property.purchasePrice = purchasePrice;
    board[index].property.baseRent = baseRent;
    board[index].property.mortgageValue = mortgageValue;

    board[index].property.houseCost = houseCost;
    board[index].property.hotelCost = hotelCost;

    board[index].property.owner = -1;

    board[index].property.houses = 0;
    board[index].property.hotel = 0;

    board[index].property.mortgaged = 0;

    board[index].property.loanLocked = 0;

    board[index].property.insurance = NO_INSURANCE;
    board[index].property.insuranceRoundsLeft = 0;

    board[index].property.damaged = 0;
    board[index].property.repairCostOwed = 0;

    board[index].property.age = 0;
    board[index].property.depreciation = 0;
    board[index].property.condition = 100;
}

void setRailway(int index, char name[], int purchasePrice)
{
    board[index].index = index;
    board[index].type = RAILWAY;

    strcpy(board[index].name, name);
    strcpy(board[index].property.name, name);

    board[index].property.purchasePrice = purchasePrice;
    board[index].property.mortgageValue = purchasePrice / 2;

    board[index].property.owner = -1;
    board[index].property.mortgaged = 0;
    board[index].property.loanLocked = 0;
}

void setUtility(int index, char name[], int purchasePrice)
{
    board[index].index = index;
    board[index].type = UTILITY;

    strcpy(board[index].name, name);
    strcpy(board[index].property.name, name);

    board[index].property.purchasePrice = purchasePrice;
    board[index].property.mortgageValue = purchasePrice / 2;

    board[index].property.owner = -1;
    board[index].property.mortgaged = 0;
    board[index].property.loanLocked = 0;
}

void setSpecialSquare(int index,
                      SquareType type,
                      char name[])
{
    board[index].index = index;

    board[index].type = type;

    strcpy(board[index].name, name);
}

void initializeBoard(void)
{
    /* ---------- Special Squares ---------- */

    setSpecialSquare(0, GO, "GO");
    setSpecialSquare(2, EVENT, "Community Development Fund");
    setSpecialSquare(4, TAX, "Income Tax");
    setSpecialSquare(7, EVENT, "National Event Card");
    setSpecialSquare(10, JAIL, "Jail / Just Visiting");
    setSpecialSquare(17, INSURANCE, "Sri Lanka Insurance");
    setSpecialSquare(20, FREE_PARKING, "Free Parking");
    setSpecialSquare(22, EVENT, "National Event Card");
    setSpecialSquare(30, GO_TO_JAIL, "Go To Jail");
    setSpecialSquare(33, INSURANCE, "Ceylinco Insurance");
    setSpecialSquare(36, EVENT, "National Event Card");
    setSpecialSquare(38, BANK, "Bank of Ceylon");

    /* ---------- Railways ---------- */

    setRailway(5, "Colombo Fort Railway Station", 2000);
    setRailway(15, "Kandy Railway Station", 2000);
    setRailway(25, "Galle Railway Station", 2000);
    setRailway(35, "Jaffna Railway Station", 2000);

    /* ---------- Utilities ---------- */

    setUtility(12, "Ceylon Electricity Board", 1500);
    setUtility(28, "National Water Supply and Drainage Board", 1500);

    /* ---------- Brown ---------- */

    setProperty(1,"Pettah",BROWN,1500,100,750,500,2000);
    setProperty(3,"Maradana",BROWN,1800,120,900,500,2000);

    /* ---------- Light Blue ---------- */

    setProperty(6,"Bambalapitiya",LIGHT_BLUE,2500,180,1250,750,3000);
    setProperty(8,"Wellawatte",LIGHT_BLUE,2700,200,1350,750,3000);
    setProperty(9,"Mount Lavinia",LIGHT_BLUE,3000,220,1500,750,3000);

    /* ---------- Pink ---------- */

    setProperty(11,"Nugegoda",PINK,3500,260,1750,1000,4000);
    setProperty(13,"Maharagama",PINK,3800,280,1900,1000,4000);
    setProperty(14,"Kottawa",PINK,4000,300,2000,1000,4000);

    /* ---------- Orange ---------- */

    setProperty(16,"Negombo",ORANGE,4500,350,2250,1250,5000);
    setProperty(18,"Katunayake",ORANGE,4700,370,2350,1250,5000);
    setProperty(19,"Ja-Ela",ORANGE,5000,400,2500,1250,5000);

    /* ---------- Red ---------- */

    setProperty(21,"Kandy City",RED,5500,450,2750,1500,6000);
    setProperty(23,"Peradeniya",RED,5800,480,2900,1500,6000);
    setProperty(24,"Katugastota",RED,6000,500,3000,1500,6000);

    /* ---------- Yellow ---------- */

    setProperty(26,"Galle Fort",YELLOW,6500,600,3250,2000,8000);
    setProperty(27,"Unawatuna",YELLOW,6800,620,3400,2000,8000);
    setProperty(29,"Hikkaduwa",YELLOW,7000,650,3500,2000,8000);

    /* ---------- Green ---------- */

    setProperty(31,"Jaffna Town",GREEN,8000,750,4000,2500,10000);
    setProperty(32,"Nallur",GREEN,8300,780,4150,2500,10000);
    setProperty(34,"Trincomalee",GREEN,8500,800,4250,2500,10000);

    /* ---------- Dark Blue ---------- */

    setProperty(37,"Nuwara Eliya",DARK_BLUE,10000,1000,5000,3000,12000);
    setProperty(39,"Galle Face",DARK_BLUE,12000,1200,6000,3000,12000);
}

void displayBoard(void)
{
    int i;

    printf("\n========== BOARD ==========\n");

    for(i = 0; i < BOARD_SIZE; i++)
    {
        printf("%2d  %-35s", i, board[i].name);

        if(board[i].type == PROPERTY)
        {
            printf(" Price : %5d  Rent : %4d",
                   board[i].property.purchasePrice,
                   board[i].property.baseRent);
        }

        printf("\n");
    }
}


