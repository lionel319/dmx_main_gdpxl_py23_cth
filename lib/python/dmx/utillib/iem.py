#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/iem.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Class to get user info

Copyright (c) Altera Corporation 2016
All rights reserved.
'''

import os
import logging
import sys
import re
from pprint import pprint, pformat

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)
))))
sys.path.insert(0, LIB)

import dmx.utillib.utils
import dmx.utillib.loggingutils
from dmx.utillib.utils import run_command, print_errors

#LOGGER = dmx.utillib.loggingutils.setup_logger(__name__)

LOGGER = logging.getLogger()

class IEMError(Exception): pass

class IEM(object):

    def get_group_members(self, groupname):
        LOGGER.info("Get IEM group member of {}".format(groupname))
        group_members = []
        cmd = 'iem members -g {}'.format(groupname)
        LOGGER.debug("cmd")
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode or stderr:
            print_errors(cmd, exitcode, stdout, stderr) 

        results = stdout.rstrip().split('\n')
        for ea_result in results:
            match = re.search('(\S+)\\\(\S+)', ea_result)
            if match:
                member = match.group(2)
                group_members.append(member)
            else:
                logging.warning('Cannot find group member for line \'{}\' in \'{}\''.format(ea_result, groupname))
        return group_members 
              
    def get_user_iem_groups(self, user):
        LOGGER.info("Get user \'{}\' iem groups".format(user))
        iem_groups = []
        cmd = 'iem groups -a {} --dn' .format(user)
        LOGGER.debug(cmd)
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode or stderr:
            print_errors(cmd, exitcode, stdout, stderr)

        for line in stdout.rstrip().split('\n'):
            if 'Total' in line: continue
            iem_groups.append(line.split(',')[0].split('=')[1])
        return iem_groups
    
 
if __name__ == '__main__':
    LOGGER = dmx.utillib.loggingutils.setup_logger(level=logging.DEBUG)
    u = User(sys.argv[1])


            
            
