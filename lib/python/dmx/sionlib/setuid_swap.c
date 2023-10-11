/* This binary is intended to be a setuid script wrapper for dbRsync.pl.

   Example compilation on an hp machine:  gcc dbRsync.c -o dbRsync
   This compilation creates an executable called dbRsync. After compiling,
   chmod +s dbRsync (or whatever the executable is) to set the sticky bit or
   it won't work.
*/

#define _BSD_SOURCE

#include <sys/types.h>
#include <unistd.h>

int main(int ac, char **av) {
    int uid;
    uid = geteuid();
    setreuid(uid, uid);
    execv("/p/psg/flows/common/dmx/main/lib/python/dmx/sionlib/workspace_helper", av);
}
