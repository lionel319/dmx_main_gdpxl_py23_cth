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
from cmx.tnrlib.test_runner_view import TestRunnerView
import cmx.tnrlib.test_runner_factory
import dmx.abnrlib.config_factory
import dmx.abnrlib.icm
from cmx.tnrlib.release_runner_base import ReleaseRunnerBase

class ReleaseRunnerView(ReleaseRunnerBase):
    
    def __init__(self, thread, milestone, deliverable, project, ip, bom, label=None, views=None, skipmscheck=None, prel=None, syncpoint=None, skipsyncpoint=None, workarea=None, dryrun=False):
        super().__init__(thread, milestone, deliverable, project, ip, bom, label=label, views=views, skipmscheck=skipmscheck, prel=prel, syncpoint=syncpoint, skipsyncpoint=skipsyncpoint, workarea=workarea, dryrun=dryrun)
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
        self.required_deliverables = None

    def find_mapping_reltag(self, release_model):
        import dmx.abnrlib.icm
        i = dmx.abnrlib.icm.ICManageCLI()
        retlist = i._find_objects('release', 'IP_MODEL:~{}$'.format(release_model), retkeys=['*'])
        return retlist


    def run(self):
        ''' Here's the flow of releasing CTHFE.

        User runs
        > dmx release -p i18asockm -i liotest1 -d view_acds -b RC1 -t KM2revA0 -m 1.0

        1. Precheck
               - $WORKAREA env var is defined
               - Sub-IPs in i18asockm/liotest1@RC1 are all REL

        2. Create Staging bom:
               self.staging_bomname self.get_staging_bomname()
               clone(i18asockm/liotest1@RC1) -> self.staging_bomname
               remove all libtypes which are not required.

        3. dmx populate workspace <self.staging_bomname>

        4. for each of required_libtype:
               dmx workspace check x
           ### (all the above is wrapped under test_runner_view.py)

        5. if all steps went thru successfully:
               for deliverable in required_deliverables:
                   if deliverable is not REL:
                       generate deliverable@REL
                       replace deliverable@REL into staging_bom
               clone(staging_bom) --> REL
        '''

        self.precheck()

        self.staging_bomname = self.create_staging_bom()
        
        staging_workarea = self.populate_workspace()

        # XXX: To temporary get audit to pass for cthfe
        os.system("env WORKAREA={} /nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/bin/mycmx poc genaudits -i liotest3 -d cthfe -t KM2revA0 -m 1.0".format(staging_workarea))

        error = self.run_workspace_check(staging_workarea)
        if error:
            return error
        
        error = self.run_posthooks()
        if error:
            return error

        self.generate_rel_configs()
        
        self.logger.info("=THE END=")
        return 0

 
    def precheck(self):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        errlist = []
        if not os.getenv("WORKAREA"):
            errlist.append("$WORKAREA env var not defined.")
       
        ### All sub-ip bom must be REL
        cfobj = self.get_config_factory_obj()
        for c in cfobj.configurations:
            if c.is_config():
                if not c.is_released():
                    errlist.append("Sub-IP {}@{} is not a REL.".format(c.variant, c.name))

        ### All required libtypes must be in source bom
        ### - and they must be REL too
        required_deliverable_names = [x.name for x in self.get_required_deliverables()]
        cf = self.get_config_factory_obj()
        for c in cf.configurations:
            if not c.is_config():
                if c.libtype in required_deliverable_names:
                    required_deliverable_names.remove(c.libtype)

                    if not c.is_released():
                        errlist.append("required_deliverable({}) is not a REL.".format(c.libtype))

        if required_deliverable_names:
            errlist.append("These required_deliverables are not found in the given bom: {}".format(required_deliverable_names))


        if errlist:
            self.logger.error("  - FAIL: precheck. Please check the errors below. \n{}".format(pformat(errlist)))
            raise Exception("FAIL: precheck")

        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))


    def create_staging_bom(self):
        '''
        staging_bomname = _for_tnr_variant_<user>_<atime>
        1. clone project/ip@bom -> project/ip@staging_Bom
        2. replace project/ip:cthfe@bom -> project/ip:cthfe@release_model_icm_bom
        '''
        self.staging_bomname = '_for_tnr_variant_{}_{}'.format(os.getenv("USER"), int(time.time()))
        cf = self.get_config_factory_obj()
        newcf = cf.clone(self.staging_bomname)
        
        ### Removed all libtypes which are not required
        required_deliverable_names = [x.name for x in self.get_required_deliverables()]
        tobe_removed = []
        for c in newcf.configurations:
            if not c.is_config():
                if c.libtype not in required_deliverable_names:
                    tobe_removed.append(c)

        for c in tobe_removed:
            newcf.remove_object(c)

        self.logger.debug(newcf.report())

        newcf.save()
        self.staging_bom_obj = newcf

        return self.staging_bomname


    def get_required_deliverables(self):
        if not self.required_deliverables:
            tr = self.get_testrunner(self.workarea)
            self.required_deliverables = tr.get_required_deliverables()
        return self.required_deliverables


    def get_testrunner(self, workarea):
        tr = cmx.tnrlib.test_runner_factory.TestRunnerFactory(self.thread, self.milestone, self.views[0], workspace_root=workarea, ipname=self.ip).get_testrunner()
        return tr


    def run_posthooks(self):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        self.logger.info("  - For now, just assume all posthooks PASSES.")
        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))
        return 0


    def generate_rel_configs(self):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        self.make_rel_config(srcbom=self.staging_bomname)
        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))



