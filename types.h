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

    int antiSpecRounds; /* rounds in a row above the 3-undeveloped limit */

} Player;


/* Kinds of temporary modifiers that can be active at once.  Each
   event, card, regulation, market review and regional card adds a
   timed entry to Economy.modifiers[].  All matching entries are
   multiplied together (Rule-LK 34) so effects are cumulative and
   never permanently corrupt the base property values/costs. */
typedef enum
{
    MOD_VALUE_GLOBAL,       /* all property values */
    MOD_GROUP_VALUE,        /* one colour group's property values */
    MOD_INDEX_VALUE,        /* a single square's value (any type) */
    MOD_RAIL_VALUE,         /* all railway station values */
    MOD_PURCHASE_PRICE,     /* direct purchase prices (boom +15%) */
    MOD_RENT_GLOBAL,        /* all property/rail/utility rent */
    MOD_GROUP_RENT,         /* one colour group's rent */
    MOD_HOTEL_RENT,         /* hotel rent */
    MOD_RAIL_RENT,          /* railway rent */
    MOD_UTIL_RENT,          /* utility rent */
    MOD_CONSTRUCTION,       /* house/hotel construction costs */
    MOD_INSURANCE,          /* insurance premiums */
    MOD_MARKET_MORTGAGE,    /* mortgage values (boom +15% / decline -10%) */
    MOD_AUCTION_PRICE,      /* auction starting prices (decline -25%) */
    MOD_FLOOD_RISK,         /* Heavy Monsoon - flood more likely */
    MOD_RIOT_RISK,          /* Political Unrest - riot more likely */
    MOD_BI_CLAIMS,          /* Political Unrest - business interruption claims */
    MOD_RECESSION           /* Economic Recession - strategies may react */

} ModifierType;


/* Where a modifier came from - used by Rule-LK 36 to group the
   currently active conditions into Market Boom / Market Decline /
   Regional Development sections. */
typedef enum
{
    SRC_GENERAL,    /* events, national cards, government regulations */
    SRC_BOOM,       /* Property Market Review - boom group */
    SRC_DECLINE,    /* Property Market Review - decline group */
    SRC_REGIONAL    /* Regional Development Card */

} ModifierSource;


typedef struct
{
    ModifierType type;
    int group;      /* group for GROUP modifiers, else -1 */
    int index;      /* square index for INDEX modifiers, else -1 */
    int percent;    /* 100 means no change */
    int roundsLeft;
    ModifierSource source;

} ActiveModifier;


#define MAX_MODIFIERS 48


/* Current state of the economy - inflation, interest rate, and every
   temporary rent/cost bonus or penalty from events and the market.  */
typedef struct
{
    int inflationRate;
    int loanInterestRate;

    int constructionSuspendedRoundsLeft;

    int closedPropertyIndex;
    int closedPropertyRoundsLeft;

    int incomeTaxAmount;

    int antiSpeculationActive;

    int currentCardIndex;   /* position in the National Event Card deck */

    int groupCooldownUntilRound[NO_GROUP];

    int lastBoomGroup;
    int lastDeclineGroup;

    ActiveModifier modifiers[MAX_MODIFIERS];
    int modifierCount;

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
