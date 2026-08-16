#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include "types.h"

/* board.c */

void initializeBoard(GameState game[]);
void displayBoard(GameState game[]);

void setProperty(GameState game[],
                 int index,
                 char name[],
                 PropertyGroup group,
                 int purchasePrice,
                 int baseRent,
                 int mortgageValue,
                 int houseCost,
                 int hotelCost);

void setRailway(GameState game[], int index, char name[], int purchasePrice);
void setUtility(GameState game[], int index, char name[], int purchasePrice);

void setSpecialSquare(GameState game[],
                      int index,
                      SquareType type,
                      char name[]);

/* players.c */

void initializePlayers(GameState game[]);
void displayPlayers(GameState game[]);

int shouldBuyProperty(GameState game[], int playerIndex);
int shouldConstruct(GameState game[], int playerIndex, int cost, int isHotel);
int wantsLoan(GameState game[], int playerIndex);
int wantsToRepayLoan(GameState game[], int playerIndex);
int wantsIncreaseLoan(GameState game[], int playerIndex);
int wantsExtendLoan(GameState game[], int playerIndex);
int wantsRefinance(GameState game[], int playerIndex);
InsuranceType desiredInsurance(GameState game[], int playerIndex, int propIndex);
int shouldRenovateAgeDepreciation(GameState game[], int playerIndex, int depreciationPercent);
int shouldMaintain(GameState game[], int playerIndex, int condition, int cost);
int willingToBid(GameState game[], int playerIndex, int propIndex, int candidateBid);
int shouldMortgage(GameState game[], int playerIndex);
int shouldRedeemMortgage(GameState game[], int playerIndex, int redeemCost);
int shouldPayBail(GameState game[], int playerIndex);

/* finance.c */

void buyProperty(GameState game[], int playerIndex);
void payRent(GameState game[], int playerIndex, int diceValue);
void payTax(GameState game[], int playerIndex);
void payCommunityFundTax(GameState game[], int playerIndex);
void payMoney(GameState game[], int playerIndex, int amount);
void liquidateBankruptAssets(GameState game[], int playerIndex);
void receiveMoney(GameState game[], int playerIndex, int amount);

int calculatePropertyValue(GameState game[], int playerIndex);
int calculateBuildingValue(GameState game[], int playerIndex);
int calculateNetWorth(GameState game[], int playerIndex);

int findPropertyToMortgage(GameState game[], int playerIndex);
int findMortgagedProperty(GameState game[], int playerIndex);
void mortgageProperty(GameState game[], int playerIndex);
void redeemMortgage(GameState game[], int playerIndex);
void handleMortgageDecisions(GameState game[], int playerIndex);

int calculateRent(GameState game[], int position);
int calculateRailwayRent(GameState game[], int playerIndex);
int calculateUtilityRent(GameState game[], int playerIndex, int diceValue);
int countUndevelopedProperties(GameState game[], int playerIndex);

int wouldCompleteMonopoly(GameState game[], int playerIndex, int pos);
void sellLowValueProperty(GameState game[], int playerIndex);
void sellDecliningProperties(GameState game[], int playerIndex);
void enforceAntiSpeculation(GameState game[]);
void sellUndevelopedPropertyToAuction(GameState game[], int playerIndex);

int groupSize(GameState game[], PropertyGroup group);
int ownsMonopoly(GameState game[], int playerIndex, PropertyGroup group);
int developGroup(GameState game[], int playerIndex, PropertyGroup group);
void constructBuildings(GameState game[], int playerIndex);

/* game.c */

void startGame(GameState game[]);
void playGame(GameState game[], int turnOrder[]);
int playTurn(GameState game[], int playerIndex);
int movePlayer(GameState game[], int playerIndex, int dice);
int rollDice(void);
int handleJail(GameState game[], int playerIndex);

int resolveGroup(GameState game[], int groupPlayers[], int groupSize,
                  int output[], int startIndex);

void determineTurnOrder(GameState game[], int turnOrder[]);
void displayRoundSummary(GameState game[], int round);
int countSolventPlayers(GameState game[]);
int countHouses(GameState game[], int playerIndex);
int countHotels(GameState game[], int playerIndex);
int determineWinner(GameState game[]);
void displayFinalResults(GameState game[]);

/* events.c */

void executeEvent(GameState game[], int playerIndex);
void triggerEconomicEvent(GameState game[]);
void triggerGovernmentRegulation(GameState game[]);
void decrementEventTimers(GameState game[]);

/* market.c */

void initMarket(GameState game[]);
void groupName(PropertyGroup group, char buffer[]);
PropertyGroup pickEligibleGroup(GameState game[], int currentRound, int avoid1, int avoid2);
void reviewPropertyMarket(GameState game[], int currentRound);
void drawRegionalCard(GameState game[]);
void displayMarketConditions(GameState game[]);

/* bank.c */

int totalEligibleCollateral(GameState game[], int playerIndex);
int calculateMaxLoan(GameState game[], int playerIndex);
void obtainLoan(GameState game[], int playerIndex);
void repayLoan(GameState game[], int playerIndex, int amount);
void handleBankVisit(GameState game[], int playerIndex);
void increaseLoan(GameState game[], int playerIndex);
void extendLoan(GameState game[], int playerIndex);
void refinanceLoan(GameState game[], int playerIndex);
void demolishBuildingsOn(GameState game[], int index);
void foreclose(GameState game[], int playerIndex);
void processLoans(GameState game[]);

/* insurance.c */

int propertyValue(GameState game[], int propIndex);
int repairCost(GameState game[], int propIndex);
DisasterType pickDisaster(GameState game[]);
int isCovered(InsuranceType policy, DisasterType disaster);
int compensationPercent(InsuranceType policy);
void purchaseInsurance(GameState game[], int playerIndex, int propIndex, InsuranceType type);
int findPropertyToInsure(GameState game[], int playerIndex);
int findPropertyToRenew(GameState game[], int playerIndex);
void handleInsuranceVisit(GameState game[], int playerIndex);
void tryAutoRepair(GameState game[], int playerIndex);
void triggerDisaster(GameState game[]);
void processInsuranceExpiry(GameState game[]);

/* economy.c */

int applyRate(int oldValue, int ratePercent);
void initEconomy(GameState game[]);
void applyInflation(GameState game[]);
void addModifier(GameState game[], ModifierType type, int group, int index,
                 int percent, int roundsLeft);
void addSourcedModifier(GameState game[], ModifierType type, int group,
                        int index, int percent, int roundsLeft,
                        ModifierSource source);
int modifierMultiplier(GameState game[], ModifierType type, int group, int index);
int isModifierActive(GameState game[], ModifierType type, int group, int index);
void decrementModifiers(GameState game[]);
void formatLKR(int amount, char out[]);
int currentMarketValue(GameState game[], int propIndex);
int currentTaxRatePercent(GameState game[], int baseRate);
void ageProperties(GameState game[]);
void tryRenovateAgeDepreciation(GameState game[], int playerIndex, int propIndex);
int rentConditionPercent(int condition);
void ageBuildings(GameState game[]);
void performMaintenance(GameState game[], int playerIndex);
void renovateStructuralDamage(GameState game[], int playerIndex);

/* auction.c */

int getAskingValue(GameState game[], int propIndex);
void runAuction(GameState game[], int propIndex, int sellerIndex);

#endif
