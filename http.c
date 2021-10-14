#include "./runpy.h"
#include "./server.h"
#include <unistd.h>

int main() {
    pid_t pid = fork();
    if(pid == 0){
        run_server();
    }
    else{
        runpy();
    }
    return 0;
}

