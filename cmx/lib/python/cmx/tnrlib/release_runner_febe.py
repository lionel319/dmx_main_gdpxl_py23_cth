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
sys.path.insert(0, DMXLIB)
sys.path.insert(0, CMXLIB)

from cmx.tnrlib.release_runner_icm import ReleaseRunnerIcm
import cmx.tnrlib.utils

class ReleaseRunnerFebe(ReleaseRunnerIcm):
    
    def __init__(self, thread, milestone, deliverable, project, ip, bom, label=None, views=None, skipmscheck=None, prel=None, syncpoint=None, skipsyncpoint=None, workarea=None, dryrun=False, force=False):
        super().__init__(thread, milestone, deliverable, project, ip, bom, label=label, views=views, skipmscheck=skipmscheck, prel=prel, syncpoint=syncpoint, skipsyncpoint=skipsyncpoint, workarea=workarea, dryrun=dryrun, force=force)


    def pre_run_workspace_check(self, staging_workarea):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        self.logger.info("  >FAKE COPY audit files from febe to $WORKAREA/output/psgaudit/...")
        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))

    def populate_workspace(self):
        return super().populate_workspace(opts=' -d febe --debug -f ')

    def get_staging_workarea(self):
        '''
        We need to override this for febe release, because for backend releases, it is special.
        the 'dmx release' command is already wrapped and called within a `cth_psetup_psg ..... -ward <staging_workarea>`
        Thus, we should get the staging_workarea variable from the $WORKAREA environment.
        '''
        if not hasattr(self, 'staging_workarea') or not self.staging_workarea:
            #self.staging_workarea = cmx.tnrlib.utils.get_uniq_staging_workarea(self.project, self.ip)
            self.staging_workarea = os.getenv("WORKAREA")
        return self.staging_workarea

    def run(self):
        self.generate_rel_configs()
        self.logger.info("=THE END=")
        return 0


    def generate_rel_configs(self):
        key = 'CTHFE_RELTAG'
        febe_bom = self.get_deliverable_bom()
        cthfe_reltag = febe_bom.properties[key]
        super().generate_rel_configs(props={key: cthfe_reltag}, relname=cthfe_reltag)

    def post_generate_rel_configs(self):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))

        stage = 'fe_collateral'
        duts = self.get_duts()
        for dut in duts:
            self.logger.info(" > Cloning {}/{}/{} to {} ...".format(dut, stage, self.deliverable_bom.name, self.generated_rel_config_name))
            cmd = 'arc.pl -triplet {}/{}/{} -copy -to_tag {}'.format(dut, stage, self.deliverable_bom.name, self.generated_rel_config_name)
            self.logger.info("    - Running: {}".format(cmd))
            os.system(cmd)

            self.logger.info(" > Locking {}/{}/{} ...".format(dut, stage, self.generated_rel_config_name))
            cmd = 'cthlock -triplet {}/{}/{} -set lock'.format(dut, stage, self.generated_rel_config_name)
            self.logger.info("    - Running: {}".format(cmd))
            os.system(cmd)

        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))
        return 0


    def get_duts(self):
        staging_workarea = self.get_staging_workarea()
        tr = self.get_testrunner(staging_workarea)
        return tr.get_cells()



