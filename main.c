#include <stdio.h>
#include "types.h"

/* Function Prototypes */
void initializeBoard(void);
void displayBoard(void);

void initializePlayers(void);
void displayPlayers(void);

int main(void)
{
    printf("=========================================\n");
    printf("       MONOPOLY-LK SIMULATION\n");
    printf("=========================================\n");

    initializeBoard();
    initializePlayers();

    displayBoard();

    displayPlayers();

    return 0;
}