#ifndef TYPES_H
#define TYPES_H

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
#define LOAN_INTEREST_RATE     8   /* starting rate, drifts with inflation */

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


/* Disaster Types (Rule-LK 10) */
typedef enum
{
    FIRE,
    FLOOD,
    RIOT,
    BUILDING_COLLAPSE,
    ELECTRICAL_FAILURE

} DisasterType;


typedef struct
{
    int active;
    int amount;
    int interestRate;
    int remainingRounds;

} Loan;


typedef struct
{
    char name[MAX_NAME_LENGTH];

    PropertyGroup group;

    int purchasePrice;
    int mortgageValue;
    int baseRent;

    int houseCost;
    int hotelCost;

    int owner;          /* -1 means unowned */

    int houses;
    int hotel;

    int mortgaged;
    int loanLocked;      /* pledged as loan collateral */

    InsuranceType insurance;
    int insuranceRoundsLeft;

    int damaged;          /* disaster damage - no rent until repaired */
    int repairCostOwed;
    int lostIncomeRoundsLeft;   /* Business Interruption: no rent for 5 rounds */

    int age;
    int depreciation;

    int condition;               /* building condition, Rule-LK 25-27 */
    int roundsSinceMaintenance;
    int structurallyDamaged;
    int preDamagePurchasePrice;   /* remembered so renovation can restore it */
    int preDamageBaseRent;
    int maintenanceCostMultiplierPercent;

} Property;


typedef struct
{
    int index;

    SquareType type;

    char name[MAX_NAME_LENGTH];

    Property property;

} Square;


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

    int sufferedLoss;   /* Risk Taker only insures after a loss */

} Player;


/* Current state of the economy - inflation, interest rate, and every
   temporary rent/cost bonus or penalty from events and the market.  */
typedef struct
{
    int inflationRate;
    int loanInterestRate;

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

    int currentCardIndex;   /* position in the National Event Card deck */

    int groupValueMultiplier[NO_GROUP];
    int groupRentMultiplier[NO_GROUP];
    int groupRoundsLeft[NO_GROUP];
    int groupCooldownUntilRound[NO_GROUP];

    int lastBoomGroup;
    int lastDeclineGroup;

} Economy;


/* Everything the game needs to remember, bundled into one struct so
   it can be passed to functions as a plain array parameter instead
   of using global variables or pointers.                            */
typedef struct
{
    Square board[BOARD_SIZE];
    Player players[MAX_PLAYERS];
    Economy economy;

} GameState;

#endif
