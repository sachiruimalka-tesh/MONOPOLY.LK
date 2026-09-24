#ifndef TYPES_H
#define TYPES_H

#define MAX_PLAYERS        4
#define BOARD_SIZE         40
#define MAX_NAME_LENGTH    50
#define MAX_ROUNDS         500
#define START_MONEY        30000

#define GO_MONEY           2000
#define JAIL_BAIL          300

#define INCOME_TAX_RATE        15   /* base rate at game start, drifts with market */
#define COMMUNITY_FUND_TAX_RATE 10  /* base rate, drifts with market */

#define MAX_HOUSES         4
#define MAX_HOTELS         1

#define LOAN_DURATION_ROUNDS   20
#define LOAN_INTEREST_RATE     8   /* starting rate, drifts with inflation */
#define LOAN_COLLATERAL_PERCENT 75 /* Rule-LK 2: max loan is 75% of collateral */
#define LOAN_EXTEND_ROUNDS     10  /* Rule-LK 5: extension adds 10 rounds */
#define MORTGAGE_REPAY_PERCENT 110 /* redeeming a mortgage costs 110% of its value */

/* Loan interest rate limits */
#define LOAN_INTEREST_MIN        1   /* interest can never go below this */
#define LOAN_INTEREST_MAX       25   /* ...or above this */
#define LOAN_INTEREST_STEP       2   /* cards/regulations move it by 2 points */
#define TAX_RATE_MAX            25
#define HOTEL_LUXURY_TAX_PERCENT 25  /* luxury tax: 25% of a hotel's value */

/* Strategy decision thresholds, in LKR (rule-book strategy rules) */
#define MIN_CASH_SAFETY        1000  /* reserve before spending / borrowing */
#define MIN_CASH_FLOOR          500  /* risk taker's floor before mortgaging */
#define TRADER_CASH_FLOOR      1200  /* opportunistic trader's mortgage floor */
#define COMFORTABLE_CASH       3000  /* conservative banker's comfort line */
#define BAIL_CASH_SPARE        1500  /* conservative banker's bail threshold */
#define RICH_CASH_LINE         5000  /* rich-player threshold */
#define EXPENSIVE_PROP_PRICE   6000  /* price above which a trader insures */

/* Rent tables (Tables 7, 8): one railway/utility owned -> this rent */
#define RAILWAY_RENT_1         250
#define RAILWAY_RENT_2         500
#define RAILWAY_RENT_3         1000
#define RAILWAY_RENT_4         2000
#define UTILITY_RENT_ONE        4   /* rent = 4 x dice */
#define UTILITY_RENT_TWO       10   /* rent = 10 x dice when both owned */

/* Auction rules */
#define AUCTION_OPENING_DIVISOR 2   /* opening bid = asking value / 2 */
#define AUCTION_BID_INCREMENT  250  /* every bid must raise the price by this */
#define AUCTION_MAX_ROUNDS     200  /* safety limit so bidding always ends */

/* Property market review (Rule-LK 30) */
#define MARKET_REVIEW_EVERY    10   /* review happens every 10 rounds */
#define MARKET_COOLDOWN_ROUNDS 30   /* a group can't re-trigger for 30 rounds */

/* Property ageing and neglect (Rule-LK 15, 16, 25-27) */
#define PROPERTY_AGE_LIMIT      50  /* value starts dropping past this age */
#define DEPRECIATION_STEP        5  /* every 5 rounds past the limit */
#define MAX_DEPRECIATION        30
#define RENOVATION_COST_PERCENT 10  /* renovation costs 10% of current value */
#define RENOVATION_RENT_BOOST    5  /* renovated base rent rises 5% */
#define NEGLECT_ROUNDS          20  /* no maintenance this long = structural damage */
#define STRUCTURAL_VALUE_LOSS   15  /* damaged building loses 15% of its value */
#define STRUCTURAL_RENT_LOSS    25  /* ...and 25% of its rent */
#define DAMAGE_REPAIR_MULTIPLIER 150 /* fixing structural damage costs 150% */

/* Insurance rules */
#define REPAIR_COST_PERCENT     30  /* repairs cost 30% of a property's value */
#define PREMIUM_BASIC_PERCENT    5
#define PREMIUM_COMPREHENSIVE_PERCENT 10
#define PREMIUM_INTERRUPTION_PERCENT 15
#define INSURANCE_DURATION_ROUNDS 20
#define INSURANCE_RENEW_AT       10  /* renew when 10 or fewer rounds remain */
#define INSURANCE_EXPIRY_WARNING 3   /* warn 3 rounds before a policy expires */
#define DISASTER_WEIGHT         20  /* every disaster is equally likely at base */
#define DISASTER_BOOST          30  /* weather/unrest makes one type +30 likely */
#define BI_LOST_INCOME_ROUNDS    5  /* Business Interruption: no rent for 5 rounds */

/* Jail (Rule 13) */
#define JAIL_SQUARE             10
#define JAIL_MAX_TURNS           3

/* Event / card deck sizes */
#define EVENT_CARD_COUNT        20
#define ECONOMIC_EVENT_COUNT     8
#define REGULATION_COUNT         8
#define REGIONAL_CARD_COUNT     12

/* Round cadences for periodic events */
#define ECONOMY_CYCLE           10  /* disasters, inflation, market review */
#define EVENT_CYCLE             15  /* economic events and regional cards */
#define REGULATION_CYCLE        20  /* government regulations */

/* Anti-Speculation Act (Rule-LK 8) */
#define MAX_UNDEVELOPED_PROPS    3   /* at most this many undeveloped properties */
#define ANTI_SPEC_TRIGGER_ROUNDS 5   /* enforced after 5 consecutive rounds */

/* Board Square Types */
typedef enum
{
    GO,
    PROPERTY,
    RAILWAY,
    UTILITY,
    TAX,
    COMMUNITY_FUND,
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

    int incomeTaxRate;

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
