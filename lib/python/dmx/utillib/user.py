#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/user.py#1 $
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
from pprint import pprint, pformat

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)
))))
sys.path.insert(0, LIB)

import dmx.utillib.utils
import dmx.utillib.loggingutils
from dmx.utillib.utils import run_command
from dmx.utillib.iem import IEM 

#LOGGER = dmx.utillib.loggingutils.setup_logger(__name__)
LOGGER = logging.getLogger()

class UserError(Exception): pass

class User(object):

    def __init__(self, wwid_or_idsid):
        self.exe = '/usr/intel/bin/cdislookup'
        self.wwid_or_idsid = wwid_or_idsid
        self.data = self._get_data()
        if self.data.get('IDSID') :
            self.idsid = self.get_idsid()
        else:
            self.idsid = wwid_or_idsid
        self.iem = IEM()

    def get_email(self):
        return self.data['DomainAddress']

    def get_wwid(self):
        return self.data['WWID']

    def get_idsid(self):
        return self.data['IDSID']

    def get_fullname(self):
        return self.data['ccMailName']

    def get_manager_wwid(self):
        return self.data['MgrWWID']

    def get_iem_groups(self):
        return self.iem.get_user_iem_groups(self.idsid)

    def is_exists(self):
        return bool(self.data)

    def _get_data(self):
        if self.wwid_or_idsid.isdigit():
            self.option = '-w'
        else:
            self.option = '-i'

        self.cmd = '{} {} {}'.format(self.exe, self.option, self.wwid_or_idsid)
        LOGGER.debug("cmd: {}".format(self.cmd))
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(self.cmd)
        LOGGER.debug("exitcode: {}".format(exitcode))
        LOGGER.debug("stdout: {}".format(stdout))
        LOGGER.debug("stderr: {}".format(stderr))

        data = {}
        if 'No match' in stdout or 'No match' in stderr:
            return data

        for line in stdout.splitlines():
            sline = line.split('=', 1)
            data[sline[0].strip()] = sline[1].strip()

        LOGGER.debug("data: {}".format(pformat(data)))
        return data
               
if __name__ == '__main__':

    LOGGER = dmx.utillib.loggingutils.setup_logger(level=logging.DEBUG)
    u = User(sys.argv[1])


            
            
