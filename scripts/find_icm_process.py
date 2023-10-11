#!/usr/bin/env python

### 
#ssh scc044166.sc.intel.com " netstat -planet | grep '35277 '" | awk '{print $NF}'


import sys
import os
from dmx.utillib.utils import run_command

def main():
    txt = sys.argv[1]
    host, port = txt.split(':')
    cmd = """ ssh {} "netstat -planet" | grep {} """.format(host, port)
    print "Running: {}".format(cmd)
    exitcode, stdout, stderr = run_command(cmd)
    print "stdout: {}".format(stdout)
    # stdout = 'tcp        0      0 0.0.0.0:54029           0.0.0.0:*               LISTEN      11645384   457295314  4229/vnc --site San '
    # stdout = 
    #find pid 
    pidcmd = stdout.split("\n")[0].split()[8]
    print "pidcmd: {}".format(pidcmd)
    _pid, _cmd = pidcmd.split('/')

    cmd = """ ssh {} "pstree -pulna {}" """.format(host, _pid)
    print "Running: {}".format(cmd)
    exitcode, stdout, stderr = run_command(cmd)
    print "stdout:\n{}".format(stdout)


if __name__ == '__main__':
    main()
