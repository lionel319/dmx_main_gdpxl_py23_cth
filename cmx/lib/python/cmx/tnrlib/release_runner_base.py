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
import cmx.tnrlib.test_runner_factory
import dmx.abnrlib.config_factory
import dmx.abnrlib.icm
import cmx.tnrlib.utils

class ReleaseRunnerBase():
    
    def __init__(self, thread, milestone, deliverable, project, ip, bom, label=None, views=None, skipmscheck=None, prel=None, syncpoint=None, skipsyncpoint=None, workarea=None, dryrun=False, force=False):
        self.logger = logging.getLogger(__name__)
        self.workarea = workarea
        if not self.workarea:
            self.workarea = self.get_workarea()
        self.thread = thread
        self.milestone = milestone
        self.deliverable = deliverable
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
        self.posthookdir = None
        self.posthookscript = None
        self.force = force

    def set_dmx_env_vars(self):
        ''' These are the env vars that posthook scripts need '''
        self.setenv("DMX_THREAD", self.thread)
        self.setenv("DMX_MILESTONE", self.milestone)
        self.setenv("DMX_DELIVERABLE", self.deliverable)
        self.setenv("DMX_PROJECT", self.project)
        self.setenv("DMX_IP", self.ip)
        self.setenv("DMX_BOM", self.bom)
        self.setenv("DMX_STAGING_WORKAREA", self.get_staging_workarea())

    def setenv(self, key, val):
        os.environ[key] = val

    def get_testrunner(self, workarea):
        tr = cmx.tnrlib.test_runner_factory.TestRunnerFactory(self.thread, self.milestone, self.deliverable, workspace_root=workarea, ipname=self.ip).get_testrunner()
        return tr

    def get_staging_workarea(self):
        if not hasattr(self, 'staging_workarea') or not self.staging_workarea:
            self.staging_workarea = cmx.tnrlib.utils.get_uniq_staging_workarea(self.project, self.ip)
        return self.staging_workarea

    def get_workarea(self):
        self.workarea = os.getenv("WORKAREA")
        if not self.workarea:
            raise Exception("WORKAREA env var not defined! Program Terminated!")
        return self.workarea

 
    def create_staging_bom(self, old_libtype_bom, new_libtype_bom):
        '''
        staging_bomname = _for_tnr_<libtype>_<user>_<atime>
        1. clone project/ip@bom -> project/ip@staging_Bom
        2. replace project/ip:cthfe@bom -> project/ip:cthfe@release_model_icm_bom
        '''
        self.staging_bomname = '_for_tnr_{}_{}_{}'.format(self.deliverable, os.getenv("USER"), int(time.time()))
        cf = self.get_config_factory_obj()
        newcf = cf.clone(self.staging_bomname)
        newcf.replace_object_in_tree(old_libtype_bom, new_libtype_bom)
        print(newcf.report())
        newcf.save()
        return self.staging_bomname


    def get_config_factory_obj(self):
        if not self.cfobj:
            self.cfobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.ip, self.bom)
        return self.cfobj


    def populate_workspace(self, opts=''):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        staging_workarea = self.get_staging_workarea()
        self.logger.debug("  - staging_workarea: {}".format(staging_workarea))
        os.system("mkdir -p {}".format(staging_workarea))
    
        foldername = os.path.basename(os.path.dirname(__file__))
        dmxrootdir = cmx.utillib.utils.get_dmx_root_from_folder(foldername)
        exe = os.path.join(dmxrootdir, 'cmx', 'bin', 'dmx')
        #project, ip, bom = self.get_icmws_project_ip_bom()
        cmd = 'env WORKAREA={} {} workspace populate -p {} -i {} -b {} {}'.format(staging_workarea, exe, self.project, self.ip, self.staging_bomname, opts)
        if os.getenv("DMXDEBUG"):
            cmd += ' --debug'
        self.logger.info("  - cmd: {}".format(cmd))
        os.system(cmd)

        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))
        return staging_workarea

    def run_workspace_check(self, staging_workarea):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        tr = self.get_testrunner(staging_workarea)
        errors = tr.run_tests()
        tr.report_errors(errors)
        if tr._exit_code:
            self.logger.error("  - FAIL: workspace_check at {} is not clean.".format(staging_workarea))
            retval = 1
        else:
            self.logger.info("  - PASS: workspace_check at {} is clean.".format(staging_workarea))
            retval = 0
        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))
        return retval


    def get_icmws_project_ip_bom(self):
        icmwsobj = self.get_icmws_obj()
        return [icmwsobj._project, icmwsobj._ip, icmwsobj._bom]

    def get_icmws_obj(self):
        if not hasattr(self, 'icmwsobj') or not self.icmwsobj:
            import dmx.abnrlib.workspace
            wsroot = cmx.utillib.utils.get_icm_wsroot_from_workarea_envvar()
            self.icmwsobj = dmx.abnrlib.workspace.Workspace(workspacepath=wsroot)
        return self.icmwsobj


    def get_rel_name(self):
        import dmx.tnrlib.release_runner
        import argparse
        args = argparse.ArgumentParser()
        args.configuration = args.work_dir = args.dont_create_rel = None
        rr = dmx.tnrlib.release_runner.ReleaseRunner(args)
        relname = rr.get_rel_config_name(self.project, self.ip, self.deliverable, self.milestone, self.thread, label=self.label, views=self.views, skipmscheck=self.skipmscheck, prel=self.prel)
        return relname


    def make_rel_config(self, props=None, srcbom=None, relname=None):
        if not relname:
            relname = self.get_rel_name()
        self.logger.info("  - relconfig tobe created: {}".format(relname))
        if not srcbom:
            dev = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.ip, 'dev', libtype=self.deliverable)
        else:
            dev = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.ip, srcbom, libtype=self.deliverable)

        rel = dev.clone(relname)
        rel.add_property('Owner', os.getenv("USER"))
        #rel.add_property('DMX_Version', self.versionobj.dmx)
        #rel.add_property('DMXDATA_Version', self.versionobj.dmxdata)

        ### http://pg-rdjira:8080/browse/DI-1401
        ### Add --views into property
        viewlabel = ''
        if self.views:
            # eg: views=['view_rtl', 'view_phys'], ==> 'RTL,PHYS'
            viewlabel = ','.join([v[5:] for v in self.views]).upper()
            rel.add_property("RELEASEVIEWS", viewlabel)
        ### http://pg-rdjira:8080/browse/DI-1061
        if self.syncpoint:
            rel.add_property("SYNCPOINT", self.syncpoint)
        if self.skipsyncpoint:
            rel.add_property("SKIPSYNCPOINT", self.skipsyncpoint)
        ### http://pg-rdjira:8080/browse/DI-1176
        if self.skipmscheck:
            rel.add_property("SKIPMSCHECK", self.skipmscheck)
      
        if props:
            for k, v in props.items():
                rel.add_property(k, v)

        if not self.dryrun:
            success = rel.save(shallow=True)
            if success:
                self.logger.info("  - Successfully created release configuration: {}".format(relname))
            else:
                self.logger.info("  - Release Configuration not created: {}".format(relname))
        else:
            self.logger.info("  - DRYRUN: Release Configuration not created: {}".format(relname))

        self.logger.debug("\n{}".format(rel.report()))

        self.generated_rel_config_name = relname
        return relname


    def get_deliverable_bom(self):
        stagename = inspect.currentframe().f_code.co_name
        self.logger.info("-Running-: {}".format(stagename))

        cf = self.get_config_factory_obj()
        match = cf.search(project='^{}$'.format(self.project), variant='^{}$'.format(self.ip), libtype='^{}$'.format(self.deliverable))
        if not match:
            self.logger.error("  - Can not locate {} bom from your configuration.".format(self.deliverable))
            raise Exception("FAIL: {}".format(stagename))
       
        bom = match[0]
        self.logger.info("  - {}: {}".format(stagename, bom.name))
        self.logger.info("-Complete-: {}".format(stagename))
        return bom

    
    def run_posthooks(self):
        stagename = inspect.currentframe().f_code.co_name
        self.logger.info("-Running-: {}".format(stagename))
        script = self.get_posthook_script()
        cmd = script
        self.logger.info("  - cmd: {}".format(cmd))
        exitcode = os.system(cmd)
        if exitcode:
            self.logger.info("-Complete-: {} [with ERRORS]".format(stagename))
        else:
            self.logger.info("-Complete-: {} [without ERRORS]".format(stagename))
        return exitcode

    def get_posthook_dir(self):
        if not self.posthookdir:
            self.posthookdir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'DMX_RELEASE_POSTHOOK'))
        return self.posthookdir

    def get_posthook_script(self):
        if not self.posthookscript:
            posthookdir = self.get_posthook_dir()
            if self.deliverable:
                scriptname = 'deliverable.{}.py'.format(self.deliverable)
            elif self.views:
                viewname = self.views[0].split("_", 1)[-1]
                scriptname = 'view.{}.py'.format(viewname)
            else:
                scriptname = 'variant.none.py'
        self.posthookscript = os.path.join(posthookdir, self.thread, scriptname)
        return self.posthookscript


