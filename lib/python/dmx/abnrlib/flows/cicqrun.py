#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/cicqrun.py#2 $
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

#import dmx.utillib.teamcity_cicq_api
import dmx.utillib.factory_cicq_api

LOGGER = logging.getLogger(__name__)

class CicqRunError(Exception): pass

class CicqRun(object):
    
    def __init__(self, project, ip, thread, dryrun=False, force=False):
        self.project = project
        self.ip = ip
        self.thread = thread
        self.dryrun = dryrun
        self.force = force
        self.atime = time.strftime('%Y%m%d%H%M%S')
        self.arcname = '{}_{}'.format(self.atime, self.thread)
        self.ssh = '/p/psg/da/infra/admin/setuid/tnr_ssh'

    def run(self):
        #api = dmx.utillib.teamcity_cicq_api.TeamcityCicqApi(self.project, self.ip, self.thread, dryrun=self.dryrun)
        api = dmx.utillib.factory_cicq_api.FactoryCicqApi(self.project, self.ip, self.thread, dryrun=self.dryrun)

        ### Abort if there is already a running/queued job.
        ### https://jira.devtools.intel.com/browse/PSGDMX-3007
        jobs = {'running': api.get_current_running_build(), 'queued': api.get_current_queued_build()}
        for k in list(jobs.keys()):
            LOGGER.debug("get_current_{}_build ret: {}".format(k, jobs[k]))
            if 'count' not in jobs[k]:
                LOGGER.error("Problem getting current {} build! Abort!".format(k))
                return 1
            if jobs[k]['count'] != 0:
                LOGGER.error("There is a job currently already {} for this thread. Please try again later after the job completed.\n{}\n".format(k, jobs[k]['build'][0]['webUrl']))
                return 1
        LOGGER.info("There is no running/queued job currently for this thread. Ready to submit job ...")

        if not dmx.utillib.factory_cicq_api.is_cicq_platform_jenkins():
            props = {'env.ARCNAME': self.arcname}
            if self.force:
                props['env.CICQ_FORCERUN'] = '1'
        else:
            props = {'ARC_NAME': self.arcname}
            if self.force:
                props['CICQ_FORCERUN'] = '1'

        ret = api.run_build(props=props)

        if ret:
            LOGGER.info("Job successfully submitted to TeamCity queue.")

            ### loop until get the arc job id
            cmd = """ {} -q sc-login.sc.intel.com '/p/psg/ctools/arc/bin/arc job-query --limit=1 user=psginfraadm name="{}" ' """.format(self.ssh, self.arcname)
            while True:
                time.sleep(30)
                LOGGER.info("Waiting for job (ARCNAME:{}) to run ...".format(self.arcname))
                LOGGER.debug("cmd: {}".format(cmd))
                exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
                if stdout:
                    arcjobid = stdout.strip()
                    arclink = 'https://psg-sc-arc.sc.intel.com/arc/dashboard/reports/show_job/{}'.format(arcjobid)
                    LOGGER.info("Job Startung Running. Arc Job: {}".format(arclink))
                    break

        return ret
