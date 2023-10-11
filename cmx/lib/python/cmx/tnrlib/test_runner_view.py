#!/usr/bin/env python

import os
import sys
import json
from pprint import pprint
import textwrap
import logging

CMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, os.getenv("DMXLIB"))
sys.path.insert(0, os.getenv("CMXLIB"))

from dmx.utillib.utils import add_common_args, run_command
import dmx.tnrlib.audit_check
from dmx.tnrlib.test_result import TestResult, TestFailure
from dmx.tnrlib.waiver_file import WaiverFile
import dmx.ecolib.ecosphere
import dmx.ecolib.ip

import cmx.tnrlib.typecheck
import cmx.utillib.utils
import cmx.tnrlib.test_runner_factory

class TestRunnerView():

    def __init__(self, thread=None, milestone=None, deliverable=None, workspace_root=None, ipname=None, stepname='a0'):

        self.logger = logging.getLogger(__name__)

        if not workspace_root:
            self.workspace_root = os.getenv("WORKAREA")
        else:
            self.workspace_root = workspace_root
        self.thread = thread
        self.milestone = milestone
        self.deliverable = deliverable
        self.test_results = []
        self.tests_failed = []
        self.dmxdata = None
        self._required_checkers = []
        self.required_deliverables = []

        self._icmwsroot = None
        self._ipname = ipname             # equivalent to turnin's cluster name
        self._stepname = stepname         # equivalent to turnin's step name
        self._cellnames_file = None     # cell_names.txt fullpath
        self._tnrwaivers_files = []     # tnrwaivers.csv fullpath

        self._errors = {'waived':[], 'unwaived':[]}
        self._waiverfile = None
        self._exit_code = 0

        self.family = None
        self.roadmap = None
        self.iptype = None


    def get_family_obj(self):
        if not self.family:
            eco = dmx.ecolib.ecosphere.EcoSphere(workspaceroot='dummy')
            self.family = eco.get_family_for_thread(self.thread)
        return self.family
        
    def get_roadmap_obj(self):
        familyobj = self.get_family_obj()
        if not self.roadmap:
            eco = dmx.ecolib.ecosphere.EcoSphere(workspaceroot='dummy')
            self.roadmap = familyobj.get_roadmap(eco.get_roadmap_for_thread(self.thread))
        return self.roadmap

    def get_required_deliverables(self):
        if not self.required_deliverables:
            roadmapobj = self.get_roadmap_obj()
            self.required_deliverables = roadmapobj.get_deliverables(milestone=self.milestone, views=[self.deliverable])
        return self.required_deliverables 


    def get_iptype(self):
        if not self.iptype:
            family = self.get_family_obj().name
            ip = dmx.ecolib.ip.IP(family, self._ipname)
            self.iptype = ip.iptype
        return self.iptype

    #========================================================

    def run_tests(self):
        results = {}
        self.get_required_deliverables()
        for deliverable in self.required_deliverables:
            self.logger.info(""" 
        ################################################################
        ### =START= WORKSPACE CHECK for {}/{} 
        ################################################################""".format(self._ipname, deliverable.name))

            tr = cmx.tnrlib.test_runner_factory.TestRunnerFactory(self.thread, self.milestone, deliverable.name, self.workspace_root, self._ipname, self._stepname).get_testrunner()
            errors = tr.run_tests()
            tr.report_errors(errors)
            if tr._exit_code:
                status = 'FAIL'
                self.logger.error("  - {}: workspace_check({}).".format(status, deliverable.name))
                results[deliverable] = 1
            else:
                status = 'PASS'
                self.logger.info("  - {}: workspace_check({}).".format(status, deliverable.name))
                results[deliverable] = 0
              
            self.logger.info(""" 
        ###############################################################
        ### =END= {}: WORKSPACE CHECK for {}/{}
        ###############################################################""".format(status, self._ipname, deliverable.name))

        return results 


    def report_errors(self, results):
        self._exit_code = 0
        msg = """
        ==============================================================
        SUMMARY RESULTS OF WORKSPACE CHECK
        =============================================================="""
        for k, v in results.items():
            if v:
                status = 'FAIL'
                self._exit_code = 1
            else:
                status = 'PASS'
            msg += """
        {}: {}""".format(status, k)
        self.logger.info(msg)


