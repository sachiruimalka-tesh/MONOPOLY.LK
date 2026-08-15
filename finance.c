#include <stdio.h>
#include "types.h"
#include "functions.h"

void receiveMoney(GameState game[], int playerIndex, int amount)
{
    game[0].players[playerIndex].cash += amount;
}

void payMoney(GameState game[], int playerIndex, int amount)
{
    game[0].players[playerIndex].cash -= amount;

    if(game[0].players[playerIndex].cash < 0 && !game[0].players[playerIndex].bankrupt)
    {
        game[0].players[playerIndex].bankrupt = 1;

        printf("\n*** BANKRUPTCY ***\n");
        printf("%s has been declared bankrupt.\n",
               game[0].players[playerIndex].name);

        liquidateBankruptAssets(game, playerIndex);
    }
}

/* Rule 14: on bankruptcy, buildings are demolished and every
   property/railway/utility owned is auctioned off (Rule-LK 19). */
void liquidateBankruptAssets(GameState game[], int playerIndex)
{
    int i;

    printf("%s's remaining assets are being liquidated.\n",
           game[0].players[playerIndex].name);

    game[0].players[playerIndex].loan.active = 0;
    game[0].players[playerIndex].loan.amount = 0;
    game[0].players[playerIndex].loan.interestRate = 0;
    game[0].players[playerIndex].loan.remainingRounds = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].property.owner != playerIndex)
            continue;

        demolishBuildingsOn(game, i);

        game[0].board[i].property.owner = -1;
        game[0].board[i].property.mortgaged = 0;
        game[0].board[i].property.loanLocked = 0;
        game[0].board[i].property.insurance = NO_INSURANCE;
        game[0].board[i].property.damaged = 0;
        game[0].board[i].property.repairCostOwed = 0;

        if(game[0].board[i].type == PROPERTY)
            game[0].players[playerIndex].propertiesOwned--;
        else if(game[0].board[i].type == RAILWAY)
            game[0].players[playerIndex].railwaysOwned--;
        else if(game[0].board[i].type == UTILITY)
            game[0].players[playerIndex].utilitiesOwned--;

        runAuction(game, i);
    }
}

void payTax(GameState game[], int playerIndex, int amount)
{
    printf("\n%s landed on Income Tax.\n",
           game[0].players[playerIndex].name);

    printf("%s paid tax : LKR %d\n",
           game[0].players[playerIndex].name,
           amount);

    payMoney(game, playerIndex, amount);
}

int findPropertyToMortgage(GameState game[], int playerIndex)
{
    int i;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].property.owner != playerIndex)
            continue;

        if(game[0].board[i].property.mortgaged)
            continue;

        if(game[0].board[i].property.loanLocked)
            continue;

        /* must be undeveloped before it can be mortgaged */
        if(game[0].board[i].type == PROPERTY &&
           (game[0].board[i].property.houses > 0 || game[0].board[i].property.hotel))
        {
            continue;
        }

        return i;
    }

    return -1;
}

int findMortgagedProperty(GameState game[], int playerIndex)
{
    int i;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].property.owner == playerIndex &&
           game[0].board[i].property.mortgaged)
        {
            return i;
        }
    }

    return -1;
}

void mortgageProperty(GameState game[], int playerIndex)
{
    int propIndex;

    if(!shouldMortgage(game, playerIndex))
        return;

    propIndex = findPropertyToMortgage(game, playerIndex);

    if(propIndex == -1)
        return;

    game[0].board[propIndex].property.mortgaged = 1;

    receiveMoney(game, playerIndex, game[0].board[propIndex].property.mortgageValue);

    printf("\n%s mortgaged %s for LKR %d.\n",
           game[0].players[playerIndex].name,
           game[0].board[propIndex].name,
           game[0].board[propIndex].property.mortgageValue);
}

void redeemMortgage(GameState game[], int playerIndex)
{
    int propIndex;
    int redeemCost;

    propIndex = findMortgagedProperty(game, playerIndex);

    if(propIndex == -1)
        return;

    /* pay back the mortgage value plus 10% interest */
    redeemCost = (game[0].board[propIndex].property.mortgageValue * 110) / 100;

    if(!shouldRedeemMortgage(game, playerIndex, redeemCost))
        return;

    if(game[0].players[playerIndex].cash < redeemCost)
        return;

    payMoney(game, playerIndex, redeemCost);

    game[0].board[propIndex].property.mortgaged = 0;

    printf("\n%s redeemed the mortgage on %s for LKR %d.\n",
           game[0].players[playerIndex].name,
           game[0].board[propIndex].name,
           redeemCost);
}

void handleMortgageDecisions(GameState game[], int playerIndex)
{
    redeemMortgage(game, playerIndex);
    mortgageProperty(game, playerIndex);
}

/* Rent for a normal property, based on houses/hotel (Table 6),
   scaled by any active bonuses and by building condition (Table 3). */
int calculateRent(GameState game[], int position)
{
    int rent;
    int conditionPercent;
    int houses;
    int hotel;
    int baseRent;
    PropertyGroup group;
    int condition;

    houses = game[0].board[position].property.houses;
    hotel = game[0].board[position].property.hotel;
    baseRent = game[0].board[position].property.baseRent;
    group = game[0].board[position].property.group;
    condition = game[0].board[position].property.condition;

    if(hotel)
    {
        rent = baseRent * 10;
    }
    else
    {
        if(houses == 0)
            rent = baseRent * 1;
        else if(houses == 1)
            rent = baseRent * 2;
        else if(houses == 2)
            rent = baseRent * 3;
        else if(houses == 3)
            rent = baseRent * 5;
        else
            rent = baseRent * 7;
    }

    rent = (rent * game[0].economy.groupRentMultiplier[group]) / 100;

    if(hotel)
        rent = (rent * game[0].economy.hotelRentMultiplierPercent) / 100;

    if(houses > 0 || hotel)
    {
        conditionPercent = rentConditionPercent(condition);
        rent = (rent * conditionPercent) / 100;
    }

    return rent;
}

/* Rent for a railway, based on how many the same owner has (Table 7). */
int calculateRailwayRent(GameState game[], int playerIndex)
{
    int i;
    int count;
    int baseRent;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type == RAILWAY &&
           game[0].board[i].property.owner == playerIndex)
        {
            count++;
        }
    }

    if(count == 1)
        baseRent = 250;
    else if(count == 2)
        baseRent = 500;
    else if(count == 3)
        baseRent = 1000;
    else if(count == 4)
        baseRent = 2000;
    else
        baseRent = 0;

    return (baseRent * game[0].economy.railwayRentMultiplierPercent) / 100;
}

/* Rent for a utility, based on the dice roll just made (Table 8). */
int calculateUtilityRent(GameState game[], int playerIndex, int diceValue)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type == UTILITY &&
           game[0].board[i].property.owner == playerIndex)
        {
            count++;
        }
    }

    if(count == 2)
        return (10 * diceValue * game[0].economy.utilityRentMultiplierPercent) / 100;

    if(count == 1)
        return (4 * diceValue * game[0].economy.utilityRentMultiplierPercent) / 100;

    return 0;
}

int groupSize(GameState game[], PropertyGroup group)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type == PROPERTY && game[0].board[i].property.group == group)
            count++;
    }

    return count;
}

int ownsMonopoly(GameState game[], int playerIndex, PropertyGroup group)
{
    int i;
    int owned;

    owned = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type == PROPERTY && game[0].board[i].property.group == group)
        {
            if(game[0].board[i].property.owner == playerIndex)
                owned++;
        }
    }

    return (owned == groupSize(game, group));
}

/* Builds one house (or upgrades to a hotel) somewhere in this
   colour group. Always adds to whichever property currently has the
   fewest houses, so development stays even (Rule 9). */
void developGroup(GameState game[], int playerIndex, PropertyGroup group)
{
    int i;
    int minHouses;
    int targetIndex;
    int allFourHouses;

    if(!ownsMonopoly(game, playerIndex, group))
        return;

    minHouses = MAX_HOUSES + 1;
    targetIndex = -1;
    allFourHouses = 1;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type == PROPERTY && game[0].board[i].property.group == group)
        {
            if(game[0].board[i].property.hotel)
                continue;

            if(game[0].board[i].property.houses < MAX_HOUSES)
                allFourHouses = 0;

            if(game[0].board[i].property.houses < minHouses)
            {
                minHouses = game[0].board[i].property.houses;
                targetIndex = i;
            }
        }
    }

    if(targetIndex == -1)
        return;   /* every property already has a hotel */

    if(allFourHouses)
    {
        int hotelCost;

        hotelCost = (game[0].board[targetIndex].property.hotelCost *
                     game[0].economy.constructionCostMultiplierPercent) / 100;

        if(!shouldConstruct(game, playerIndex, hotelCost))
            return;

        if(game[0].players[playerIndex].cash < hotelCost)
            return;

        payMoney(game, playerIndex, hotelCost);

        game[0].board[targetIndex].property.houses = 0;
        game[0].board[targetIndex].property.hotel = 1;

        printf("\n%s upgraded %s to a Hotel.\n",
               game[0].players[playerIndex].name,
               game[0].board[targetIndex].name);

        printf("Construction Cost : LKR %d\n", hotelCost);

        return;
    }

    {
        int houseCost;

        houseCost = (game[0].board[targetIndex].property.houseCost *
                     game[0].economy.constructionCostMultiplierPercent) / 100;

        if(!shouldConstruct(game, playerIndex, houseCost))
            return;

        if(game[0].players[playerIndex].cash < houseCost)
            return;

        payMoney(game, playerIndex, houseCost);

        game[0].board[targetIndex].property.houses++;

        printf("\n%s constructed one house on %s.\n",
               game[0].players[playerIndex].name,
               game[0].board[targetIndex].name);

        printf("Construction Cost : LKR %d\n", houseCost);
    }
}

void constructBuildings(GameState game[], int playerIndex)
{
    PropertyGroup group;

    if(game[0].economy.constructionSuspendedRoundsLeft > 0)
        return;

    for(group = BROWN; group < NO_GROUP; group++)
    {
        developGroup(game, playerIndex, group);
    }
}

/* Rule 15 net worth formula. Three terms are always 0 in this
   simulation - insurance claims are paid immediately, tax is always
   paid immediately, and loan interest is folded into loan.amount -
   so there's never a pending balance for those three to track. */
int calculatePropertyValue(GameState game[], int playerIndex)
{
    int i;
    int total;

    total = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].property.owner != playerIndex)
            continue;

        if(game[0].board[i].type == PROPERTY)
            total += currentMarketValue(game, i);
        else if(game[0].board[i].type == RAILWAY || game[0].board[i].type == UTILITY)
            total += game[0].board[i].property.purchasePrice;
    }

    return total;
}

int calculateBuildingValue(GameState game[], int playerIndex)
{
    int i;
    int total;

    total = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type != PROPERTY)
            continue;

        if(game[0].board[i].property.owner != playerIndex)
            continue;

        if(game[0].board[i].property.hotel)
            total += game[0].board[i].property.hotelCost;
        else
            total += game[0].board[i].property.houses * game[0].board[i].property.houseCost;
    }

    return total;
}

/* Rule 15 net worth formula. Three terms are always 0 in this
   simulation - insurance claims are paid out immediately, tax is
   always paid immediately, and loan interest is folded straight
   into loan.amount - so there is never a pending balance for any
   of those three to carry forward. */
int calculateNetWorth(GameState game[], int playerIndex)
{
    int cash;
    int propertyValue;
    int buildingValue;
    int insuranceClaimsReceivable;
    int outstandingLoans;
    int accruedInterest;
    int taxesDue;

    cash = game[0].players[playerIndex].cash;
    propertyValue = calculatePropertyValue(game, playerIndex);
    buildingValue = calculateBuildingValue(game, playerIndex);

    insuranceClaimsReceivable = 0;
    accruedInterest = 0;
    taxesDue = 0;

    outstandingLoans = game[0].players[playerIndex].loan.active ?
                        game[0].players[playerIndex].loan.amount : 0;

    return cash + propertyValue + buildingValue + insuranceClaimsReceivable
           - outstandingLoans - accruedInterest - taxesDue;
}

int countUndevelopedProperties(GameState game[], int playerIndex)
{
    int i;
    int count;

    count = 0;

    for(i = 0; i < BOARD_SIZE; i++)
    {
        if(game[0].board[i].type == PROPERTY &&
           game[0].board[i].property.owner == playerIndex &&
           game[0].board[i].property.houses == 0 &&
           !game[0].board[i].property.hotel)
        {
            count++;
        }
    }

    return count;
}

void buyProperty(GameState game[], int playerIndex)
{
    int pos;
    int price;
    int wantsToBuy;

    pos = game[0].players[playerIndex].position;

    if(game[0].board[pos].type != PROPERTY &&
       game[0].board[pos].type != RAILWAY &&
       game[0].board[pos].type != UTILITY)
    {
        return;
    }

    if(game[0].board[pos].property.owner != -1)
        return;   /* already owned */

    price = game[0].board[pos].property.purchasePrice;

    if(game[0].board[pos].type == PROPERTY)
        price = currentMarketValue(game, pos);

    wantsToBuy = shouldBuyProperty(game, playerIndex);

    if(game[0].players[playerIndex].cash < price)
        wantsToBuy = 0;

    if(game[0].economy.antiSpeculationActive && game[0].board[pos].type == PROPERTY)
    {
        if(countUndevelopedProperties(game, playerIndex) >= 3)
            wantsToBuy = 0;
    }

    /* Rule 5: if they don't buy directly, it goes to auction */
    if(!wantsToBuy)
    {
        runAuction(game, pos);
        return;
    }

    payMoney(game, playerIndex, price);

    game[0].board[pos].property.owner = playerIndex;

    if(game[0].board[pos].type == PROPERTY)
        game[0].players[playerIndex].propertiesOwned++;
    else if(game[0].board[pos].type == RAILWAY)
        game[0].players[playerIndex].railwaysOwned++;
    else if(game[0].board[pos].type == UTILITY)
        game[0].players[playerIndex].utilitiesOwned++;

    printf("\n%s purchased %s for LKR %d\n",
           game[0].players[playerIndex].name,
           game[0].board[pos].name,
           price);

    printf("Remaining Balance : LKR %d\n",
           game[0].players[playerIndex].cash);
}

void payRent(GameState game[], int playerIndex, int diceValue)
{
    int pos;
    int owner;
    int rent;

    pos = game[0].players[playerIndex].position;

    if(game[0].board[pos].type != PROPERTY &&
       game[0].board[pos].type != RAILWAY &&
       game[0].board[pos].type != UTILITY)
    {
        return;
    }

    owner = game[0].board[pos].property.owner;

    if(owner == playerIndex)
    {
        /* landed on your own square - no rent, maybe renovate */
        if(game[0].board[pos].type == PROPERTY)
            tryRenovateAgeDepreciation(game, playerIndex, pos);
        return;
    }

    if(owner == -1)
        return;

    if(game[0].board[pos].property.mortgaged)
        return;

    if(pos == game[0].economy.closedPropertyIndex && game[0].economy.closedPropertyRoundsLeft > 0)
    {
        printf("\n%s landed on %s, but it is closed (Political Rally) - no rent.\n",
               game[0].players[playerIndex].name, game[0].board[pos].name);
        return;
    }

    if(game[0].board[pos].type == PROPERTY && game[0].board[pos].property.damaged)
    {
        printf("\n%s landed on %s, but it is damaged and collects no rent.\n",
               game[0].players[playerIndex].name, game[0].board[pos].name);
        return;
    }

    if(game[0].board[pos].type == PROPERTY)
        rent = calculateRent(game, pos);
    else if(game[0].board[pos].type == RAILWAY)
        rent = calculateRailwayRent(game, owner);
    else
        rent = calculateUtilityRent(game, owner, diceValue);

    payMoney(game, playerIndex, rent);
    receiveMoney(game, owner, rent);

    printf("\n%s landed on %s (owned by %s)\n",
           game[0].players[playerIndex].name,
           game[0].board[pos].name,
           game[0].players[owner].name);

    printf("Rent Paid : LKR %d\n", rent);
}
