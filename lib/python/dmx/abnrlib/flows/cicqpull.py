#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/cicqpull.py#1 $
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
import tempfile
from pprint import pprint

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, rootdir)

import dmx.abnrlib.config_factory
import dmx.abnrlib.icm
import dmx.abnrlib.flows.overlaydeliverables
import dmx.utillib.teamcity_cicq_api
import dmx.abnrlib.flows.cicqupdate

class CicqPullError(Exception): pass

class CicqPull(object):
    
    def __init__(self, thread, project=None, ip=None, bom=None, deliverables=None, hier=False, preview=True, wait=False):
        
        self.project = project
        self.ip = ip
        self.bom = bom
        self.deliverables = deliverables
        self.thread = thread
        self.hier = hier
        self.preview = preview
        self.wait = wait
        self.logger = logging.getLogger(__name__)
        self.icm = dmx.abnrlib.icm.ICManageCLI()
        self.tc = self.get_teamcity_object()
        self.desc = 'dmx cicq pushed from {}/{}@{}. '.format(self.project, self.ip, self.bom)
        self.dmx = os.path.join(os.path.dirname(os.path.dirname(rootdir)), 'bin', 'dmx')

        ### Cicq Backend Boms
        self.lz = 'landing_zone'    ### Default dstconfig.
        if self.thread:
            self.lz = self.lz + '_' + self.thread
        self.logger.debug("self.lz: {}".format(self.lz))

    def get_teamcity_object(self):
        if self.project and self.ip and self.thread:
            self.tc = dmx.utillib.teamcity_cicq_api.TeamcityCicqApi(self.project, self.ip, self.thread)
            if not self.tc.get_arc_resources():
                raise CicqPullError("Can't find any cicq job matching the following data:{}".format(self.tc))
        else:
            tc = dmx.utillib.teamcity_cicq_api.TeamcityCicqApi('', '', '')
            bt = tc.get_buildtype_by_thread(self.thread)
            if not bt:
                raise CicqPullError("Can't find any cicq job matching thread name:{}".format(self.thread))
            prefix, self.project, self.ip, self.thread = tc.decompose_buildtype_id(bt['id'])
            self.tc = dmx.utillib.teamcity_cicq_api.TeamcityCicqApi(self.project, self.ip, self.thread)
        return self.tc

    def run(self):
        self.logger.debug("dmx: {}".format(self.dmx))
        
        if not self.bom:
            self.bom = self.tc.get_refbom()
      

        update_cmd = '{} cicq update -p {} -i {} -b {} -t {} --debug '.format(self.dmx, self.project, self.ip, self.bom, self.thread)
        self.logger.debug("update_cmd: {}".format(update_cmd))

        ### get deliverables from cicq.ini
        if not self.deliverables:
            cu = dmx.abnrlib.flows.cicqupdate.CicqUpdate(self.project, self.ip, self.bom, self.thread)
            cu.cfgfile = tempfile.mkstemp(dir='/tmp')[1]
            cu.download_cfgfile()
            self.deliverables = cu.get_deliverables_from_cfgfile()
        push_cmd = '{} cicq push -p {} -i {} -b {} -d {} -t {} --debug '.format(self.dmx, self.project, self.ip, self.bom, ' '.join(self.deliverables), self.thread)
        if self.hier:
            push_cmd += '--hier '
        if self.wait:
            push_cmd += '--wait '
        self.logger.debug("push_cmd: {}".format(push_cmd))

        self.logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        self.logger.info("START: cicq update ...")
        exitcode = os.system(update_cmd)
        if exitcode:
            self.logger.error("Terminated, as there is an error while running cicq update.")
            return 1
        self.logger.info("DONE: cicq update.") 

        self.logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        self.logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        self.logger.info("START: cicq push ...")
        exitcode = os.system(push_cmd)
        if exitcode:
            self.logger.error("Terminated, as there is an error while running cicq push.")
            return 1
        self.logger.info("DONE: cicq push.") 
        self.logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

        return 0
