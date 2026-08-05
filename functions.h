#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include "types.h"

/*=============================
        board.c
=============================*/

void initializeBoard(void);
void displayBoard(void);

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

/*=============================
        players.c
=============================*/

void initializePlayers(void);
void displayPlayers(void);

int shouldBuyProperty(int playerIndex);
int shouldConstruct(int playerIndex, int cost);
int wantsLoan(int playerIndex);
int wantsToRepayLoan(int playerIndex);
InsuranceType desiredInsurance(int playerIndex, int propIndex);
int shouldRenovateAgeDepreciation(int playerIndex, int depreciationPercent);
int shouldMaintain(int playerIndex, int condition, int cost);

/*=============================
        finance.c
=============================*/

void buyProperty(int playerIndex);

void payRent(int playerIndex, int diceValue);

void payTax(int playerIndex, int amount);

void payMoney(int playerIndex, int amount);

void receiveMoney(int playerIndex, int amount);

int calculateRent(int position);
int calculateRailwayRent(int playerIndex);
int calculateUtilityRent(int playerIndex, int diceValue);
int countUndevelopedProperties(int playerIndex);

int groupSize(PropertyGroup group);
int ownsMonopoly(int playerIndex, PropertyGroup group);
void developGroup(int playerIndex, PropertyGroup group);
void constructBuildings(int playerIndex);

/*=============================
        game.c
=============================*/

void startGame(void);

void playGame(void);

void playTurn(int playerIndex);

void movePlayer(int playerIndex,
                int dice);

int rollDice(void);

int handleJail(int playerIndex);

void determineTurnOrder(void);

void displayRoundSummary(int round);

int countSolventPlayers(void);

int countHouses(int playerIndex);
int countHotels(int playerIndex);

/*=============================
        events.c
=============================*/

void executeEvent(int playerIndex);
void triggerEconomicEvent(void);
void triggerGovernmentRegulation(void);
void decrementEventTimers(void);
void changeAllPropertyValues(int ratePercent);
void changeGroupValues(PropertyGroup group, int ratePercent);
void changeAllHouseCosts(int ratePercent);

/*=============================
        market.c
=============================*/

void initMarket(void);
const char *groupName(PropertyGroup group);
PropertyGroup pickEligibleGroup(int currentRound, int avoid1, int avoid2);
void reviewPropertyMarket(int currentRound);
void drawRegionalCard(void);
void decrementMarketTimers(void);
void displayMarketConditions(void);

/*=============================
        bank.c
=============================*/

int totalEligibleCollateral(int playerIndex);
int calculateMaxLoan(int playerIndex);
void obtainLoan(int playerIndex);
void repayLoan(int playerIndex, int amount);
void handleBankVisit(int playerIndex);
void demolishBuildingsOn(int index);
void foreclose(int playerIndex);
void processLoans(void);

/*=============================
        insurance.c
=============================*/

int propertyValue(int propIndex);
int repairCost(int propIndex);
int isCovered(InsuranceType policy, DisasterType disaster);
int compensationPercent(InsuranceType policy);
void purchaseInsurance(int playerIndex, int propIndex, InsuranceType type);
int findPropertyToInsure(int playerIndex);
void handleInsuranceVisit(int playerIndex);
void tryAutoRepair(int playerIndex);
void triggerDisaster(void);
void processInsuranceExpiry(void);

/*=============================
        economy.c
=============================*/

int applyRate(int oldValue, int ratePercent);
void applyInflation(void);

int currentMarketValue(int propIndex);
void ageProperties(void);
void tryRenovateAgeDepreciation(int playerIndex, int propIndex);

int rentConditionPercent(int condition);
void ageBuildings(void);
void performMaintenance(int playerIndex);
void renovateStructuralDamage(int playerIndex);

#endif