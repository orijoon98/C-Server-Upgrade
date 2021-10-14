#include <stdio.h>
#include <stdlib.h>

#define SHELLSCRIPT "\
#/bin/bash \n\
python3.7 /home/pi/C-Server/env/update.py \n\
"

void runpy()
{
    system(SHELLSCRIPT);
}
