#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/environmentinfo.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr "createsnapshot" subcommand plugin
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
from __future__ import print_function
from builtins import object
import os
import sys
import logging
import tempfile
from pprint import pprint

import dmx.utillib.utils
from joblib import Parallel, delayed

class EnvironmentInfoError(Exception): pass

class EnvironmentInfo(object):
    '''
    Class to control running the createsnapshot command
    '''

    def __init__(self, nomail=True):
        self.logger = logging.getLogger(__name__)
        self.nomail = nomail
       
    def get_dmx_info(self):
        
        info = {}
        
        envvar_list = ['P4CONFIG', 'P4CLIENT', 'P4PORT', 'P4USER', 'USER', 'DB_DEVICE', 'DB_PROCESS', 'DB_THREAD', 
            'DB_FAMILY', 'DB_PROJECT', 'PWD', 'DMXDATA_ROOT', 'HOSTNAME', 'DMX_ROOT']

        for envvar in envvar_list:
            info[envvar] = os.environ.get(envvar)
            #info[envvar] = os.getenv(envvar)
       
        #cmd_list = ['pwd', 'which dmx', 'echo $DMXDATA_ROOT', 'dmx workspace info', 'icmp4 info', 'arc job', 'hostname', 'icmp4 users $USER', 
        cmd_list = ['arc job', '_icmp4 info', 'cat ~/.p4enviro', 'groups $USER', 'groups', "env|grep '^DB_'", "env|grep '^DMX'"]
            #'pm user -l $USER', 'iem groups -a $USER | grep -i psg', 'cat ~/.cshrc.$USER', 'cat ~/.p4enviro']

        for cmd in cmd_list:
            info[cmd] = {}
            info[cmd]['exit'], info[cmd]['stdout'], info[cmd]['stderr'] = dmx.utillib.utils.run_command(cmd)
            ### Split these into list so that pprint displays it in a newline (more human readable)
            for k in ['stdout', 'stderr']:
                info[cmd][k] = info[cmd][k].splitlines()

        # User run command
        info['Command Run'] = ' '.join(sys.argv)

        return info

 

    def run(self):
        info = self.get_dmx_info()
        pprint(info)

        if not self.nomail:
            ### Creating Temp File
            f = tempfile.NamedTemporaryFile('w', delete=False, suffix='.txt')
            tmpfile = f.name
            pprint(info, f)
            f.close()

            print("==============================================")
            print("Content saved in {}".format(tmpfile))
            os.system("echo report | mail -s 'dmx report env' -a {} {}".format(tmpfile, info['USER']))
            print("File sent as email attachment to {}".format(info['USER']))
            print("==============================================")

