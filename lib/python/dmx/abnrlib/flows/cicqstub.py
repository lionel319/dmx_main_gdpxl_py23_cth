#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/cicqstub.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "abnr clonconfigs"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import sys
import os
import logging
import textwrap

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, ROOTDIR)

import dmx.abnrlib.config_factory
from dmx.abnrlib.icm import ICManageCLI
import dmx.abnrlib.flows.cicqupdate

LOGGER = logging.getLogger(__name__)

class CicqStubError(Exception): pass

class CicqStub(object):
    '''
    Runner class for abnr cloneconfigs
    '''
    def __init__(self, project=None, ip=None, thread=None, cfgfile='./cicq.ini'):
        self.project = project
        self.ip = ip
        self.thread = thread
        self.cfgfile = cfgfile

    
    def run(self):
        rootdir = os.getenv("CICQ_ROOT", '')
        if not rootdir:
            raise CicqStubError("Can not find cicq resource. Make sure you arc shell to cicq.")
        
        if self.project and self.ip and self.thread:
            cu = dmx.abnrlib.flows.cicqupdate.CicqUpdate(project=self.project, variant=self.ip, config='', suffix=self.thread)
            cu.cfgfile = '{}.{}.{}.cicq.ini'.format(self.project, self.ip, self.thread)
            ret = cu.download_cfgfile() 
            if not ret:
                LOGGER.info('Successfully downloaded cicq.ini config file from {}.{}.{} to {}'.format(self.project, self.ip, self.thread, cu.cfgfile))
            else:
                LOGGER.error("Fail to download cicq.ini config file from {}.{}.{}.".format(self.project, self.ip, self.thread))
        else:
            ret = os.system("cp -rfv $CICQ_ROOT/cfg/cicq.ini {}".format(self.cfgfile))
            if not ret:
                LOGGER.info('cicq.ini template file donwloaded to {}.'.format(self.cfgfile))
            else:
                LOGGER.error("Fail to download cicq.ini template file.")
        
        return ret
