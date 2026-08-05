#include <stdio.h>
#include <stdlib.h>
#include "functions.h"

/*====================================
        EVENT FUNCTION
====================================*/

void executeEvent(int playerIndex)
{
    int event;

    /* Random event number (1 - 6) */
    event = rand() % 6 + 1;

    printf("\n*** EVENT CARD ***\n");

    switch(event)
    {
        case 1:
            printf("Salary Bonus! Receive LKR 1000.\n");
            receiveMoney(playerIndex, 1000);
            break;

        case 2:
            printf("Medical Expenses! Pay LKR 800.\n");
            payMoney(playerIndex, 800);
            break;

        case 3:
            printf("Lottery Winner! Receive LKR 2000.\n");
            receiveMoney(playerIndex, 2000);
            break;

        case 4:
            printf("Road Development Tax! Pay LKR 500.\n");
            payMoney(playerIndex, 500);
            break;

        case 5:
            printf("Scholarship Award! Receive LKR 1500.\n");
            receiveMoney(playerIndex, 1500);
            break;

        case 6:
            printf("Vehicle Repair! Pay LKR 1000.\n");
            payMoney(playerIndex, 1000);
            break;
    }

    printf("Current Balance : LKR %d\n",
           players[playerIndex].cash);
}
