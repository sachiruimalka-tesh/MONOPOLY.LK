#ifndef TYPES_H
#define TYPES_H

/*==========================
    CONSTANTS
==========================*/

#define MAX_PLAYERS        4
#define BOARD_SIZE         40
#define MAX_NAME_LENGTH    50
#define MAX_ROUNDS         500
#define START_MONEY        30000

#define GO_MONEY           2000
#define JAIL_BAIL          300

#define MAX_HOUSES         4
#define MAX_HOTELS         1

#define LOAN_DURATION_ROUNDS   20
#define LOAN_INTEREST_RATE     8   /* 8% - "Stable Economy" row of Table 9.
                                       Will vary once we add the economy
                                       phase (inflation / recessions).  */

/*==========================
    ENUMERATIONS
==========================*/

/* Board Square Types */
typedef enum
{
    GO,
    PROPERTY,
    RAILWAY,
    UTILITY,
    TAX,
    EVENT,
    BANK,
    INSURANCE,
    JAIL,
    FREE_PARKING,
    GO_TO_JAIL

} SquareType;


/* Property Colour Groups */
typedef enum
{
    BROWN,
    LIGHT_BLUE,
    PINK,
    ORANGE,
    RED,
    YELLOW,
    GREEN,
    DARK_BLUE,
    NO_GROUP

} PropertyGroup;


/* Player Strategies */
typedef enum
{
    AGGRESSIVE_INVESTOR,
    CONSERVATIVE_BANKER,
    RISK_TAKER,
    OPPORTUNISTIC_TRADER

} PlayerType;


/* Insurance Types */
typedef enum
{
    NO_INSURANCE,
    BASIC_INSURANCE,
    COMPREHENSIVE_INSURANCE,
    BUSINESS_INTERRUPTION

} InsuranceType;


/* Types of disasters (Rule-LK 10) */
typedef enum
{
    FIRE,
    FLOOD,
    RIOT,
    BUILDING_COLLAPSE,
    ELECTRICAL_FAILURE

} DisasterType;


/*==========================
        LOAN
==========================*/

typedef struct
{
    int active;
    int amount;
    int interestRate;
    int remainingRounds;

} Loan;


/*==========================
      PROPERTY
==========================*/

typedef struct
{
    char name[MAX_NAME_LENGTH];

    PropertyGroup group;

    int purchasePrice;
    int mortgageValue;
    int baseRent;

    int houseCost;
    int hotelCost;

    int owner;

    int houses;
    int hotel;

    int mortgaged;

    int loanLocked;   /* 1 = pledged as loan collateral, cannot be
                          sold / mortgaged / auctioned until loan is
                          cleared (Rule-LK 3)                        */

    InsuranceType insurance;

    int insuranceRoundsLeft;   /* counts down from 20 (Rule-LK 9) */

    int damaged;         /* 1 = building is damaged and earns no rent */
    int repairCostOwed;  /* amount owner still must pay to fix it     */

    int age;
    int depreciation;

    int condition;

    int roundsSinceMaintenance;   /* Rule-LK 27/28 : neglect counter   */
    int structurallyDamaged;      /* Rule-LK 28 : 1 = badly neglected  */
    int preDamagePurchasePrice;   /* remembered so we can restore it   */
    int preDamageBaseRent;        /* remembered so we can restore it   */
    int maintenanceCostMultiplierPercent;  /* 100 = normal, 150 = +50% */

} Property;


/*==========================
      BOARD SQUARE
==========================*/

typedef struct
{
    int index;

    SquareType type;

    char name[MAX_NAME_LENGTH];

    Property property;

} Square;


/*==========================
        PLAYER
==========================*/

typedef struct
{
    char name[MAX_NAME_LENGTH];

    PlayerType strategy;

    int position;

    int cash;

    int inJail;

    int jailTurns;

    int bankrupt;

    int propertiesOwned;

    int railwaysOwned;

    int utilitiesOwned;

    Loan loan;

    int sufferedLoss;  /* has this player ever lost money to an
                           uninsured disaster? (Risk Taker strategy) */

} Player;


/*==========================
   GLOBAL VARIABLES
==========================*/

extern Square board[BOARD_SIZE];

extern Player players[MAX_PLAYERS];

/* Current state of the national economy - both change over time
   (Rule-LK 12, 13). Defined in economy.c                            */
extern int currentInflationRate;
extern int currentLoanInterestRate;

#endif