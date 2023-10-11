#!/usr/bin/env python

import os
import sys
import json
from pprint import pprint, pformat
import textwrap
import logging
import inspect
import json
import time
import re
import tempfile

CMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, os.getenv("DMXLIB"))
sys.path.insert(0, os.getenv("CMXLIB"))

import cmx.utillib.utils
from cmx.tnrlib.test_runner import TestRunnerPoc
import dmx.abnrlib.config_factory
import dmx.abnrlib.icm
from cmx.tnrlib.release_runner_base import ReleaseRunnerBase

class ReleaseRunnerIcm(ReleaseRunnerBase):
    
    def __init__(self, thread, milestone, deliverable, project, ip, bom, label=None, views=None, skipmscheck=None, prel=None, syncpoint=None, skipsyncpoint=None, workarea=None, dryrun=False, force=False):
        super().__init__(thread, milestone, deliverable, project, ip, bom, label=label, views=views, skipmscheck=skipmscheck, prel=prel, syncpoint=syncpoint, skipsyncpoint=skipsyncpoint, workarea=workarea, dryrun=dryrun, force=force)
        self.logger = logging.getLogger(__name__)
        self.workarea = workarea
        if not self.workarea:
            self.workarea = self.get_workarea()
        self.thread = thread
        self.milestone = milestone
        self.deliverable = deliverable
        #self.deliverable = 'cthfe' # XXX: For debugging
        self.project = project
        self.ip = ip
        self.bom = bom  # This is the ip-bom
        self.staging_bomname = None     # this is the bom that is used to create the workspace, which is cloned from self.bom, and had its cthfe bom replaced
        self.label = label
        self.views = views
        self.skipmscheck = skipmscheck
        self.prel = prel
        self.syncpoint = syncpoint
        self.skipsyncpoint = skipsyncpoint
        self.dryrun = dryrun
        self.staging_workarea = self.get_staging_workarea()
        self.cfobj = None

    def find_mapping_reltag(self, release_model):
        import dmx.abnrlib.icm
        i = dmx.abnrlib.icm.ICManageCLI()
        retlist = i._find_objects('release', 'IP_MODEL:~{}$'.format(release_model), retkeys=['*'])
        return retlist


    def run(self):
        ''' Here's the flow of releasing CTHFE.

        User runs
        > dmx release -p i18asockm -i liotest1 -d reldoc -b RC1 -t KM2revA0 -m 1.0

        1. get_bom_name_of_reldoc

            11. if reldoc@REL
                111. Exit("Already released")
        
            12. if reldoc@snap-liotest1-a0-23ww11a -or- reldoc@dev
                121. get changenum
                122. if changenum already have mapping REL, exit("Already released")
                123. else, (staging_bom == i18asockm/liotest1@RC1)

        2. dmx populate workspace <staging_bom>

        3. dmx workspace check

        4. if all steps went thru successfully:
           - generate reldoc@REL

        '''

        self.precheck()
        
        self.deliverable_bom = self.get_deliverable_bom()

        if self.deliverable_bom.name.startswith('REL'):
            self.logger.info("{} is already a REL({}). There is nothing to be done here. Exiting.".format(self.deliverable, self.deliverable_bom.name))
            return 1

        if not self.force:
            self.exit_if_exiting_reltag_found_for_changenum(self.deliverable_bom)
        
        self.staging_bomname = self.bom

        staging_workarea = self.populate_workspace()

        self.pre_run_workspace_check(staging_workarea)
        error = self.run_workspace_check(staging_workarea)
        if error:
            return error
        
        self.generate_rel_configs()
        self.post_generate_rel_configs()

        error = self.run_posthooks()
        if error:
            return error


        self.logger.info("=THE END=")
        return 0


    def precheck(self):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        errlist = []
        if not os.getenv("WORKAREA"):
            errlist.append("$WORKAREA env var not defined.")
        
        if errlist:
            self.logger.error("  - FAIL: precheck. Please check the errors below. \n{}".format(pformat(errlist)))
            raise Exception("FAIL: precheck")

        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))

    def exit_if_exiting_reltag_found_for_changenum(self, deliverable_bom):
        stagename = inspect.currentframe().f_code.co_name
        self.logger.info("-Running-: {}".format(stagename))
        
        import dmx.abnrlib.icm
        i = dmx.abnrlib.icm.ICManageCLI()
        # uri: 'p4://scylicm.sc.intel.com:1666/depot/gdpxl/intel/i18asockm/liotest3/cthfe/dev/...@112443'
        retlist = i._find_objects('release', 'uri:~/{}/{}/{}/*/.*@{}$'.format(self.project, self.ip, self.deliverable, deliverable_bom.changenumdigit), retkeys=['*'])

        if retlist:
            self.logger.info("  - This changenum:{}({}) already has equivalent icm REL bom. dmx release is not needed.".format(deliverable_bom._defprops['uri'], deliverable_bom.changenumdigit))
            for e in retlist:
                if e['name'].startswith("REL"):
                    self.logger.info("    > {}".format(e['name']))
            raise Exception("FAIL: {}.".format(stagename))
        else:
            self.logger.info("  - This changenum:{}({}) does not have equivalent icm REL bom.".format(deliverable_bom._defprops['uri'], deliverable_bom.changenumdigit))
        self.logger.info("-Complete-: {}".format(stagename))


    def run_posthooks(self):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        self.logger.info("  - For now, just assume all posthooks PASSES.")
        super().run_posthooks()
        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))
        return 0


    def generate_rel_configs(self, props=None, srcbom=None, relname=None):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        self.make_rel_config(props=props, srcbom=srcbom, relname=relname)
        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))

    def pre_run_workspace_check(self, staging_workarea):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        self.logger.info("  > No overriding method from derived class. Skipping this step.")
        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))

    def post_generate_rel_configs(self):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        self.logger.info("  > No overriding method from derived class. Skipping this step.")
        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))


