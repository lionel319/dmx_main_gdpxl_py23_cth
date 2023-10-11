#!/usr/bin/env python

import os
import sys
from dmx.utillib.utils import run_command


def main():
    if len(sys.argv) < 2  or '-h' in sys.argv:
        help()
        return 0
    userid = os.getenv("USER", None)
    if not userid:
        print "ERROR: USER env var not defined!"
        return 1
    indir = sys.argv[1]
    if '-dryrun' in sys.argv:
        dryrun = True
    else:
        dryrun = False
    
    os.chdir(indir)
    print "cwd: {}".format(os.getcwd())
    
    ### Only find workspaces that are 7 days old.
    cmd = 'find -maxdepth 1 -type d -mtime +7 | grep {}'.format(userid)
    print "cmd:{}".format(cmd)
    exitcode, stdout, stderr = run_command(cmd)


    i = 1
    for line in stdout.split():
        wsname = os.path.basename(line)
        print
        print "{}: {}".format(i, wsname)
        
        cmd = 'pm workspace -x -F {}'.format(wsname)
        print "> {}".format(cmd)
        if not dryrun:
            os.system(cmd)

        cmd = 'rm -rf {}'.format(os.path.join(indir, wsname))
        print "> {}".format(cmd)
        if not dryrun:
            os.system(cmd)

        i += 1

def help():
    print """
Usage:-
=======
> cleanup_workspace_from_comm_area.py [fullpath_to_workspaces_parent_folder] [-dryrun]
> cleanup_workspace_from_comm_area.py -h

Example:-
=========
> cleanup_workspace_from_comm_area.py /nfs/site/disks/psg_dmx_1/ws -dryrun
> cleanup_workspace_from_comm_area.py /nfs/site/disks/psg_dmx_1/ws
   
"""

if __name__ == '__main__':
    sys.exit(main())

