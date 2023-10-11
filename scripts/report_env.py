#!/usr/bin/env python

import os
import sys
import tempfile
from pprint import pprint

rootdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, rootdir)

import dmx.utillib.utils


def main():
    
    ### Creating Temp File
    f = tempfile.NamedTemporaryFile('w', delete=False, suffix='.txt')
    tmpfile = f.name
    
    info = {}
    
    envvar_list = ['P4CONFIG', 'P4CLIENT', 'P4PORT', 'P4USER', 'USER', 'DB_DEVICE', 'DB_PROCESS', 'DB_THREAD', 
        'DB_FAMILY', 'DB_PROJECT']
    for envvar in envvar_list:
        info[envvar] = os.getenv(envvar)
   
    cmd_list = ['pwd', 'which dmx', 'echo $DMXDATA_ROOT', 'dmx workspace info', 'icmp4 info', 'arc job', 'hostname', 'icmp4 users $USER', 
        'pm user -l $USER', 'iem groups -a $USER | grep -i psg']
    for cmd in cmd_list:
        info[cmd] = {}
        info[cmd]['exit'], info[cmd]['stdout'], info[cmd]['stderr'] = dmx.utillib.utils.run_command(cmd)
        ### Split these into list so that pprint displays it in a newline (more human readable)
        for k in ['stdout', 'stderr']:
            info[cmd][k] = info[cmd][k].splitlines()

    pprint(info)
    pprint(info, f)

    f.close()
    print "=============================================="
    print "Content saved in {}".format(tmpfile)
    os.system("echo report | mail -s 'dmx report env' -a {} {}".format(tmpfile, info['USER']))
    print "File sent as email attachment to {}".format(info['USER'])
    print "=============================================="
    


if __name__ == '__main__':
    sys.exit(main())
