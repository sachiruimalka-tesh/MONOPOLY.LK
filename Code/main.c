#include <stdio.h>
#include "types.h"
#include "functions.h"

int main(void)
{
    /* the only place a GameState is ever created */
    GameState game[1] = {0};

    printf("=========================================\n");
    printf("        MONOPOLY-LK SIMULATION\n");
    printf("=========================================\n\n");

    startGame(game);

    return 0;
}
