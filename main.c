#include <stdio.h>
#include "types.h"
#include "functions.h"

int main(void)
{
    /* This is the ONE and only place the whole game's data gets
       created. It is an ordinary local variable - not a global, and
       nothing here is a pointer. It is written as an array of size
       1 (`GameState game[1]`) specifically so that every function
       we hand it to can just use plain array/dot notation
       (game[0].board[...], game[0].players[...], game[0].economy...)
       instead of needing any `*` or `->` pointer syntax.

       `= {0}` zero-fills every field of the struct (and everything
       nested inside it) before we touch it - this is the same "start
       from zero" guarantee that global variables used to give us for
       free, done explicitly now that GameState is a local variable. */
    GameState game[1] = {0};

    printf("=========================================\n");
    printf("        MONOPOLY-LK SIMULATION\n");
    printf("=========================================\n\n");

    startGame(game);

    return 0;
}
