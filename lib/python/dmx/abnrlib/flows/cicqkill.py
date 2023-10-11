#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/cicqkill.py#2 $
$Change: 7437460 $
$DateTime: 2023/01/09 18:36:07 $
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
import time
import dmx.utillib.utils

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, ROOTDIR)

import dmx.utillib.factory_cicq_api
import dmx.utillib.server

LOGGER = logging.getLogger(__name__)

class CicqKillError(Exception): pass

class CicqKill(object):
    
    def __init__(self, project, ip, thread, dryrun=False):
        self.project = project
        self.ip = ip
        self.thread = thread
        self.dryrun = dryrun
        self.ssh = '/p/psg/da/infra/admin/setuid/tnr_ssh'

    def run(self):
        api = dmx.utillib.factory_cicq_api.FactoryCicqApi(self.project, self.ip, self.thread)
        arcjobid = api.get_current_running_build_arc_job_id()
        if not arcjobid:
            LOGGER.info("Can not find any current running job.")
            return 1

        server = dmx.utillib.server.Server().get_working_server()
        cmd = "{} -q {} 'arc cancel -r -f {}'  ".format(self.ssh, server, arcjobid)
        LOGGER.debug("Running cmd: {}".format(cmd))
        if self.dryrun:
            LOGGER.info("Dryrun mode on. Nothing done.")
            return 0
        ret = os.system(cmd)

        return ret
