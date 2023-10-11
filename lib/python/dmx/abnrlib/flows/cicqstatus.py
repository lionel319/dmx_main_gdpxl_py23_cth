#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/cicqstatus.py#2 $
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
import json
import re
from pprint import pprint, pformat

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, ROOTDIR)

import dmx.abnrlib.config_factory
from dmx.abnrlib.icm import ICManageCLI
import dmx.utillib.arc_rest_api

LOGGER = logging.getLogger(__name__)

class CicqStatusError(Exception): pass

class CicqStatus(object):
    
    def __init__(self, project, ip, thread, infokeys='id,name,status', arcjobid=''):
        self.project = project
        self.ip = ip
        self.thread = thread
        self.arcjobid = arcjobid
        self.tcapi = dmx.utillib.factory_cicq_api.FactoryCicqApi(project, ip, thread)
        self.ara = dmx.utillib.arc_rest_api.ArcRestApi()
        for i in infokeys:
            self.infokeys = infokeys.strip().split(',')


    def run(self):

        if self.arcjobid:
            self.report_arc_jobtree_status(arcjobid=self.arcjobid)
            LOGGER.info("The full arc job info can be accessed here: {}".format(self.get_arc_dashboard_link(self.arcjobid)))
            return 0

        data = self.tcapi.get_current_running_build()
        if 'build' not in data:
            LOGGER.critical("Problem getting info from TeamCity! Please rerun with --debug option and send the full output message to psgicmsupport@intel.com")
            return -1
        else:
            if data['build']:
                LOGGER.info("TeamCity job is still running.")
                is_job_done = False
                buildid = data['build'][0]['id']
            else:
                LOGGER.info("TeamCity job has completed.")
                is_job_done = True
                data = self.tcapi.get_latest_build()
                if 'id' not in data:
                    LOGGER.critical("Problem getting info from TeamCity! Please rerun with --debug option and send the full output message to psgicmsupport@intel.com")
                    return -1
                else:
                    buildid = data['id']

        LOGGER.debug(data)
        LOGGER.debug("buildId: {}".format(buildid))
        
        agentid = self.tcapi.get_agentid_for_build(buildid)
        LOGGER.debug("agentId: {}".format(agentid))

        #arcjobid = self.tcapi.get_agent_last_arc_job_id(agentid)
        arcjobid = self.tcapi.get_agent_arc_job_id_for_buildid(agentid, buildid)
        LOGGER.debug("arcjobid: {}".format(arcjobid))

        if not arcjobid:
            LOGGER.critical("Problem getting ARC job id from buildlog! Please rerun with --debug option and send the full output message to psgicmsupport@intel.com")
            return -1

        data = self.ara.get_jobtree(arcjobid)
        if not data:
            LOGGER.info("Failed getting job status. Exiting")
            return -1
        topdata = self.get_job_from_data_by_id(data, arcjobid)

        if is_job_done:
            LOGGER.info("Job status: completed. return_code == {}".format(topdata['return_code']))
            LOGGER.info("The full arc job info can be accessed here: {}".format(self.get_arc_dashboard_link(arcjobid)))
            return int(topdata['return_code'])
            
        else:
            LOGGER.info("Job status: running ...")
            txt = self.report_arc_jobtree_status(data)
            LOGGER.info("The full arc job info can be accessed here: {}".format(self.get_arc_dashboard_link(arcjobid)))
            return 2


    def report_arc_jobtree_status(self, data=None, arcjobid=None):
        '''
        if data is not given, arcjobid must be provided.
        data == a dictionary returned by arc_rest_api.get_jobtree(arcjobid)
        '''
        if not data:
            data = self.ara.get_jobtree(arcjobid)
        info = self.get_all_children_job_info(data)
        txt = ''
        for i in info:
            for k in self.infokeys:
                txt += '{}: {}\n'.format(k, i[k])
            txt += '\n'
        LOGGER.info("\n{}".format(txt))
        return txt


    def get_arc_dashboard_link(self, arcjobid):
        return 'https://psg-sc-arc.sc.intel.com/arc/dashboard/reports/show_job/{}'.format(arcjobid)


    def get_all_children_job_info(self, data):
        ret = []

        for d in data:
            tmp = {}
            for k in self.infokeys:
                if k in d:
                    tmp[k] = d[k]
                else:
                    tmp[k] = '---'
            ret.append(tmp)
        return ret


    def get_job_from_data_by_id(self, data, arcid):
        for d in data:
            if str(d['id']) == arcid:
                return d
        return None

