#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/arcenv.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Class to instantiate connection to servers

Author: Kevin Lim Khai - Wern

Copyright (c) Altera Corporation 2016
All rights reserved.
'''

import os
import logging
import sys
from dmx.utillib.utils import run_command, is_pice_env, run_once
LOGGER = logging.getLogger(__name__)

ENV_VARS = ['DB_PROJECT',
            'DB_FAMILY',
            'DB_THREAD',
            'DB_DEVICE',
            'DB_PROCESS',
            'TV_MILESTONE']

@run_once
def print_values(dict):
    LOGGER.debug('ARC Environment values: {}'.format(dict))

class ARCEnvError(Exception): pass

class ARCEnv(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vars = {}
        for var in ENV_VARS:
            value = os.getenv(var, '')            
            self.vars[var] = value
        print_values(self.vars)            
        
    def get_arc_vars(self):
        return (self.get_project(), self.get_family(), self.get_thread(), self.get_device(), self.get_process())

    def get_project(self):
        return self.vars['DB_PROJECT'].split()
        
    def get_family(self):
        return self.vars['DB_FAMILY']
    
    def get_thread(self):
        return self.vars['DB_THREAD']

    def get_device(self):
        #return self.vars['DB_DEVICE'][:3]
        return self.vars['DB_DEVICE']

    def get_process(self):
        return self.vars['DB_PROCESS']

    def get_milestone(self):
        return self.vars['TV_MILESTONE']

        

                    
