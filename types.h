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
   -> There are NONE. Every piece of the game's data (the board,
      the 4 players, and the economy) is bundled into ONE struct
      called GameState, defined right below. main.c creates exactly
      one GameState, and every function that needs to read or change
      the game receives it as an ARRAY parameter of size 1, written
      as `GameState game[]`. Passing an array never needs the `*`,
      `->`, or `&` symbols - you just use `game[0].something`, the
      exact same dot notation as any other struct. This is how the
      whole project shares data between files with zero pointer
      syntax and zero global variables.
==========================*/

/*==========================
   ECONOMY (grouped into one struct instead of many variables)
==========================*/

/* Every piece of "current state of the country's economy" is
   grouped into this ONE struct, instead of being lots of separate
   variables scattered across files. There is only one economy in
   the whole simulation, so one struct (living inside GameState) is
   the simplest way to share it - far fewer stray variables than
   having 20+ individual ints floating around.                      */
typedef struct
{
    /* Rule-LK 12, 13 : inflation and the interest rate new loans use */
    int inflationRate;
    int loanInterestRate;

    /* Temporary rent bonuses/penalties from event cards, economic
       events, and government regulations. "RoundsLeft" counts down
       to 0, at which point the multiplier resets back to 100
       (normal). If several events would affect the same thing, the
       most recent one simply overwrites the last (kept simple on
       purpose - no stacking).                                       */
    int hotelRentMultiplierPercent;
    int hotelRentRoundsLeft;

    int railwayRentMultiplierPercent;
    int railwayRentRoundsLeft;

    int utilityRentMultiplierPercent;
    int utilityRentRoundsLeft;

    int constructionCostMultiplierPercent;
    int constructionCostRoundsLeft;

    int insurancePremiumMultiplierPercent;
    int insurancePremiumRoundsLeft;

    int constructionSuspendedRoundsLeft;

    int closedPropertyIndex;
    int closedPropertyRoundsLeft;

    int incomeTaxAmount;

    int antiSpeculationActive;

    /* Which National Event Card is on top of the deck (Appendix A) */
    int currentCardIndex;

    /* Dynamic Property Market (Section 2.9) and Regional Development
       Cards (Section 2.10) both work by temporarily multiplying a
       whole colour group's value/rent, then reverting back to 100
       (normal) once the countdown ends. They share the same arrays -
       see market.c for why, and for the one simplification this
       causes.                                                        */
    int groupValueMultiplier[NO_GROUP];
    int groupRentMultiplier[NO_GROUP];
    int groupRoundsLeft[NO_GROUP];

    /* Rule-LK 33 : a group cannot be picked again for 30 rounds */
    int groupCooldownUntilRound[NO_GROUP];

    /* Rule-LK 30 : the same group cannot repeat in back-to-back reviews */
    int lastBoomGroup;
    int lastDeclineGroup;

} Economy;

/*==========================
   GAME STATE (the ONE and only struct passed around
   the whole program - this replaces every global variable)
==========================*/

typedef struct
{
    Square board[BOARD_SIZE];
    Player players[MAX_PLAYERS];
    Economy economy;

} GameState;

#endif