#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/overlaydeliverables.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr "createsnapshot" subcommand plugin
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import os
import re
import sys
import logging
import textwrap
import datetime
import glob
import shutil
from pprint import pprint, pformat
import multiprocessing
import random
import time

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, rootdir)

from dmx.abnrlib.icm import ICManageCLI
import dmx.utillib.utils
import dmx.utillib.arcutils
import dmx.abnrlib.config_factory


class OverlayDeliverablesError(Exception): pass

class OverlayDeliverables(object):
    '''
    Class to control running the createsnapshot command
    '''

    def __init__(self, source_dest_list, project, variant, config, cells=[], directory=None, preview=True, desc='', wait=False, forcerevert=False, filespec=None):
        '''
        source_dest_list = [ [project, variant, libtype, srcconfig, dstconfig], ... ]
        cells = cells to be overlaid
        desc = No double-quotes allowed in the description.
        wait = if True, will only return prompt after all jobs are completed.
        '''
        self.arc = '/p/psg/ctools/arc/bin/arc'
        self.wsdir = '/nfs/site/disks/psg_dmx_1/ws'
        self.filespec = filespec 
        self.dmx = os.path.join(os.path.dirname(os.path.dirname(rootdir)), 'bin', 'dmx')
        self.preview = preview
        self.desc = desc.replace('"', "").replace("'", "")
        self.cells = cells
        self.wait = wait
        self.forcerevert = forcerevert
        self.project = project
        self.variant = variant
        self.config = config

        self.cli = ICManageCLI(preview=preview)
        self.logger = logging.getLogger(__name__)
        self.source_dest_list = source_dest_list
        self.uniqlist = []
       
        self.logger.debug("dmx: {}".format(self.dmx))
        self.logger.debug("source_dest_list: {}".format(pformat(source_dest_list)))

        ### Sometimes the list has duplicated entries. There is no point overlaying 
        ### the same thing more than once. Thus, we are uniqifying the list.
        ### https://jira.devtools.intel.com/browse/PSGDMX-1696
        [self.uniqlist.append(x) for x in source_dest_list if x not in self.uniqlist]
        self.logger.debug("uniqlist: {}".format(pformat(self.uniqlist)))

        self.shared_wsname_list = []
        self.shared_wsroot_list = []

        self.maxnproc = 10
        self.nproc = int(os.getenv("DMX_OVERLAY_NPROCESS", self.maxnproc))
        if self.nproc > self.maxnproc:
            self.nproc = self.maxnproc

    def run(self):

        retval = 0
        self.precheck()

        self.create_shared_workspaces()

        ### Create all multiprocessing jobs and store them in thread_list
        #===============================
        thread_list = []
        free_wsroots = self.shared_wsroot_list[:]
        done_list = []
        running_list = []
        wsusage = {}    # store the wsroot which is being used by a job
        index = 0
        while len(done_list) < len(self.uniqlist):

            ### Remove completed process from `running_list
            ### Add completed process to `done_list
            for p in running_list:
                self.logger.debug("--- free_wsroots: {}".format(free_wsroots))
                if not p.is_alive():
                    done_list.append(p)
                    running_list.remove(p)
                    self.logger.debug("job {} done. Freeing up wsroot {} ...".format(p.name, wsusage[p.name]))
                    free_wsroots.append(wsusage[p.name])
                else:
                    self.logger.debug("job {} still running on {} ...".format(p.name, wsusage[p.name]))
                self.logger.debug("+++ free_wsroots: {}".format(free_wsroots))

            ### submit process to run on the available slots
            while index < len(self.uniqlist) and free_wsroots:
                [project, variant, libtype, srcconfig, dstconfig] = self.uniqlist[index]
                key = ':'.join(self.uniqlist[index])

                self.logger.debug("process_limit:{}, available_slots:{}\n- {}".format(self.nproc, len(free_wsroots), free_wsroots))
                wsroot = free_wsroots.pop(0)
                wsusage[key] = wsroot
                self.logger.info("run_deliverable_overlay: {}/{}:{}@{} => {}\n- on wsroot {}".format(project, variant, libtype, srcconfig, dstconfig, wsroot))
                cmd = self.get_dmx_overlay_command(project, variant, libtype, srcconfig, dstconfig, wsroot, )

                thread_list.append(multiprocessing.Process(target=run_deliverable_overlay, args=(key, cmd,)))
                thread_list[-1].name = key
                t = thread_list[index]
                self.logger.debug("starting process: {}".format(t.name))
                t.start()
                running_list.append(t)
                index += 1

            time.sleep(5)


        for t in thread_list:
            self.logger.debug("joining process: {}".format(t.name))
            t.join()

        retval = self.report_status()

        self.delete_shared_workspaces()
        return retval

    def get_dmx_overlay_command(self, project, variant, libtype, srcconfig, dstconfig, wsroot):
        cmd = "{} overlay -p {} -i {}:{} -sb {} -db {} --debug".format(self.dmx, project, variant, libtype, srcconfig, dstconfig)
        if self.desc:
            cmd = cmd + ' ' + '--desc "{}"'.format(self.desc)
        if self.cells:
            cellstr = ' '.join(self.cells)
            cmd = cmd + ' ' + '--cells {}'.format(cellstr)
        if self.preview:
            cmd = cmd + ' ' + '-n'
        if self.forcerevert:
            cmd = cmd + ' --forcerevert'
        if self.filespec:
            cmd = cmd + ' ' + ' '.join(self.filespec)

        cmd = cmd + ' -swr {}'.format(wsroot)
        self.logger.debug("cmd:{}".format(cmd))
        return cmd


    def precheck(self):
        '''
        1. make sure all project/variant@dstconfig is part of the project/variant@config tree structure
        '''
        self.logger.info("Starting precheck to make sure all tobe overlaid items are part of the toplevel project/variant@config ...")
        errors = []
        cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, self.config)
        for [project, variant, libtype, srcconfig, dstconfig] in self.uniqlist:
            matched = cf.search('^{}$'.format(project), '^{}$'.format(variant), '^{}$'.format(libtype))
            if not matched:
                errors.append([project, variant, libtype, dstconfig])
            elif matched[0].name != dstconfig:
                errors.append([project, variant, libtype, dstconfig])
        if errors:
            errmsg = """These tobe overlaid items is not part of the toplevel project/variant@config({}/{}@{}):\n{}""".format(self.project, self.variant, self.config, errors)
            self.logger.error(errmsg)
            raise Exception(errmsg)

        self.logger.info("Precheck completed without errors.")

    def create_shared_workspaces(self):
        '''
        Workspace creation/skeleton sync needs to be done in series !!!
        Doing this is parallel will create signification icm slowness, especially when it is done
        from PG site !!!

        FIFO method:
            sw = multiprocessing.Manager().list()
            sw.append(ws1)
            sw.append(ws2)
            use_this_shared_worksapce = sw.pop(0)
        '''
        wscount = len(self.uniqlist)
        if wscount > self.nproc:
            wscount = self.nproc


        self.logger.info("Preparing to create {} shared workspaces.".format(wscount))
        i = 0
        ### Loop until we are sure that $wscount of workspaces are successfully created.
        while i < wscount:
            self.logger.info("Creating shared ws #{} ...".format(i+1))
            try:
                wsname = self.cli.add_workspace(self.project, self.variant, self.config, dirname=self.wsdir)
                self.cli.sync_workspace(wsname, skeleton=True)
                wsroot = '{}/{}'.format(self.wsdir, wsname)
                self.logger.info("- ws #{} created and skeleton synced. {}".format(i+1, wsroot))

                ### At this point, we know that the workspace creation 'really' succeeded.
                #SHARED_WSROOT_LIST.append(wsroot)
                self.shared_wsname_list.append(wsname)
                self.shared_wsroot_list.append(wsroot)
                i += 1
            except Exception as e:
                self.logger.debug(e)
                pass

    def delete_shared_workspaces(self):
        self.logger.info("Cleaning up shared workspaces ...")
        for wsname in self.shared_wsname_list:
            try:
                self.cli.del_workspace(wsname, preserve=False, force=True)                            
            except:
                pass

    def report_status(self):
        errors = []
        txt = ''
        for key in dict(joboutput):
            exitcode, stdout, stderr = joboutput[key]

            txt = '''

    ============================================================================================
    Job Status For: {}
    ============================================================================================
    EXITCODE: {}
    STDOUT: {}
    STDERR: {}
    ============================================================================================
    ============================================================================================

    '''.format(key, exitcode, stdout, stderr)

            if exitcode:
                errors.append(key)

            self.logger.info(txt)

        summary = '''
    ============================================================================================
    ============================================================================================
    SUMMARY:
    ===========
    {}
    ============================================================================================
    ============================================================================================
    '''
        if not errors:
            status = 'All jobs completed with no errors.'
            retval = 0
        else:
            status = 'There were some jobs which has some warnings/errors (non-zero exitcode).\n{}'.format(pformat(errors))
            retval = 1
        self.logger.info(summary.format(status))

        return retval




### Store all the runs output in a dict
### The format looks like this
### joboutput = {
###     "project:variant:libtype:srcconfig:dstconfig": [exitcode, stdout, stderr]
###     ...   ...   ...
### }
joboutput = multiprocessing.Manager().dict()
#SHARED_WSROOT_LIST = multiprocessing.Manager().list()
def run_deliverable_overlay(key, cmd):
    #cmd = 'echo {}; sleep {}'.format(key, random.randrange(30, 60))
    exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
    joboutput[key] = [exitcode, stdout, stderr]

