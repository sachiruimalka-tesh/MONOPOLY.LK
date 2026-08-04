#include <stdio.h>
#include "types.h"
#include "functions.h"

/* Function prototype from game.c */
void startGame(void);

int main(void)
{
    printf("=========================================\n");
    printf("        MONOPOLY-LK SIMULATION\n");
    printf("=========================================\n\n");

    startGame();

    return 0;
}