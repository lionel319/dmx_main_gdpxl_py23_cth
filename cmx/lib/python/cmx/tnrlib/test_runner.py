#!/usr/bin/env python

import os
import sys
import json
from pprint import pprint
import textwrap
import logging

CMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, DMXLIB)
sys.path.insert(0, CMXLIB)

from dmx.utillib.utils import add_common_args, run_command
import dmx.tnrlib.audit_check
from dmx.tnrlib.test_result import TestResult, TestFailure
from dmx.tnrlib.waiver_file import WaiverFile
import dmx.ecolib.ecosphere
import dmx.ecolib.ip

import cmx.tnrlib.typecheck
import cmx.utillib.utils

sys.path.insert(0, '/p/cth/rtl/proj_tools/cth_mako_render/23.03.001')
import cth_design_cfg

class TestRunnerPoc():

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

        self._icmwsroot = None
        self._ipname = ipname             # equivalent to turnin's cluster name
        self._stepname = stepname         # equivalent to turnin's step name
        self._cellnames_file = None     # cell_names.txt fullpath
        self._tnrwaivers_files = []     # tnrwaivers.csv fullpath

        self._errors = {'waived':[], 'unwaived':[]}
        self._waiverfile = None
        self._exit_code = 0

        self.family = None
        self.iptype = None
        self.roadmap = None

    '''
    def get_step_name_from_git(self):
        return self.get_cluster_step_name_from_git()[1]

    def get_cluster_name_from_git(self):
        return self.get_cluster_step_name_from_git()[0]

    def get_cluster_step_name_from_git(self):
        if not self._ipname:
            cmd = 'cd {}; git remote show origin | grep "Fetch URL:"'.format(self.workspace_root)
            exitcode, stdout, stderr = run_command(cmd)
            self.logger.debug("cmd: {}\nstdout: {}\nstderr: {}\n".format(cmd, stdout, stderr))
            master_repo_name = os.path.basename(stdout.split()[-1])
            self._ipname, self._stepname = master_repo_name.rsplit('-', 1)
        return [self._ipname, self._stepname]
    '''

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

    def get_iptype(self):
        if not self.iptype:
            family = self.get_family_obj().name
            ip = dmx.ecolib.ip.IP(family, self._ipname, roadmap=self.get_roadmap_obj())
            self.iptype = ip.iptype
        return self.iptype

    def get_required_checkers(self, match_attr_dict={'audit_verification': True}):
        family = self.get_family_obj()
        deliverable = family.get_deliverable(self.deliverable)
        #get_checkers(self, flow_filter = '', subflow_filter = '', checker_filter = '', milestone = '99', roadmap = '', iptype_filter='', prel_filter=''):
        checkers = deliverable.get_checkers(milestone=self.milestone, iptype_filter='^{}$'.format(self.get_iptype()))
        retlist = []
        for c in checkers:
            match = True
            for key in match_attr_dict:
                value = getattr(c, key, None)
                if value is None or value != match_attr_dict[key]:
                    match = False
                    break
            if match:
                retlist.append(c)
        return retlist

    def get_cells(self):
        cfgdir = os.path.join(self.workspace_root, 'cfg')
        dd = cth_design_cfg.DutData(cfgdir)
        cells = dd.keys()
        if not cells:
            raise Exception("There are not duts found in this workarea.")
        return cells
        

    def get_cells_old(self):
        retval = []
        filepath = self.get_cellnames_file()
        try:
            with open(filepath) as f:
                for line in f:
                    if not line.isspace() and line:
                        retval.append(line.strip())
        except Exception as e:
            raise Exception("{}\nCannot open file({}) for read.".format(e, filepath))

        return retval

    def get_icm_wsroot(self):
        if not self._icmwsroot:
            self._icmwsroot = cmx.utillib.utils.get_icm_wsroot_from_workarea_envvar(self.workspace_root)
        return self._icmwsroot

    def get_cellnames_file(self):
        if not self._cellnames_file:
            '''
            ### Temporary move cell_names.txt file into $WORKAREA/psgcheck/cell_names.txt .... 
            ### Until we have clearer directions from TYBB
            ipname = self._ipname
            if not ipname:
                raise Exception("Can not find ipname(cluster) from $WORKAREA.")
            icmwsroot = self.get_icm_wsroot()
            if not icmwsroot:
                raise Exception("Can not find icm_wsroot from $WORKAREA.")
            self._cellnames_file = = os.path.join(icmwsroot, ipname, 'ipspec', 'cell_names.txt')
            '''
            self._cellnames_file = os.path.join(self.workspace_root, 'psgcheck', 'cell_names.txt')
        return self._cellnames_file

    def get_tnrwaivers_files(self):
        if not self._tnrwaivers_files:
            if not self.deliverable:
                ### This is a VARIANT check: Get tnrwaivers.csv from reldoc
                ipname = self._ipname
                icmwsroot = self.get_icm_wsroot()
                filepath = os.path.join(icmwsroot, ipname, 'reldoc', 'tnrwaivers.csv')
                if os.path.isfile(filepath):
                    self._tnrwaivers_files.append(filepath)
                
            ### Always get tnrwaivers.csv from $WORKAREA/psgcheck/
            filepath = os.path.join(self.workspace_root, 'psgcheck', 'tnrwaivers.csv')
            if os.path.isfile(filepath):
                self._tnrwaivers_files.append(filepath)

        return self._tnrwaivers_files


    #========================================================

    def run_tests(self):
        self.run_audit_check()

        if self.deliverable:
            self.run_type_check()

        return self.tests_failed

    def log_test_pass(self, flow, message, variant=None, libtype=None, topcell='', subflow=''):
        """
        Adds a "pass" TestResult to the list of results for this run which can be used for reporting.
        """
        if variant is None:
            variant=self.variant 
        if libtype is None:
            libtype=self.libtype

        result = TestResult('pass', variant, libtype, topcell, flow, subflow, message)
        self.test_results.append(result)

    def log_test_skip(self, flow, message, variant=None, libtype=None, topcell='', subflow=''):
        """
        Adds a "skip" TestResult to the list of results for this run which can be used for reporting.
        """
        if variant is None:
            variant=self.variant 
        if libtype is None:
            libtype=self.libtype

        result = TestResult('skip', variant, libtype, topcell, flow, subflow, message)
        self.test_results.append(result)
        
    def log_test_fail(self, flow, error, variant=None, libtype=None, topcell='', subflow=''):
        """
        Adds a "fail" TestResult to the list of results for this run which can be used for reporting.

        Also adds a TestFailure to the list of failed tests for this run.
        """
        if not variant:
            variant = 'None'
        if not libtype:
            libtype = 'None'

        if 'Could not find any audit file' in error:
            error += ' (UNWAIVABLE)'


        clean_error = self.remove_workspace_from_filepath(error)

        failure = TestFailure(variant, libtype, topcell, flow, subflow, clean_error)
        self.tests_failed.append(failure)

        result = TestResult('fail', variant, libtype, topcell, flow, subflow, clean_error)
        self.test_results.append(result)

    def log_test_failures(self, failures):
        """
        For each TestFailure in the given list, logs a failure for this run.
        This helps ensure all failures are logged as both TestFailures and
        TestResults.
        """
        for (variant, libtype, topcell, flow, subflow, error) in failures:
            self.log_test_fail(flow=flow, error=error, variant=variant, libtype=libtype, topcell=topcell, subflow=subflow)

    def remove_workspace_from_filepath(self, str):
        """
        We can't put the workspace path in any failures
        as then waivers would never work!
        """
        return str.replace(self.workspace_root, '').replace('\n',' ').replace("'","").replace('"','')


    def load_waiverfile(self):
        if self._waiverfile:
            return self._waiverfile

        self._waiverfile = WaiverFile()
        waiverfiles = self.get_tnrwaivers_files()
        if not waiverfiles:
            self.logger.info("No Waiver Files found.")
        else:
            for waiverfilepath in waiverfiles:
                self._waiverfile.load_from_file(waiverfilepath)
                self.logger.info("Waiver File Found And Loaded ({})".format(waiverfilepath))
        return self._waiverfile


    def find_matching_waiver(self, variant, flow, subflow, error):
        wf = self.load_waiverfile()
        return wf.find_matching_waiver(variant, flow, subflow, error) 


    def run_audit_check(self):
        self.logger.info(">>> =START= run_audit_check ({}/{})".format(self._ipname, self.deliverable))
        af = dmx.tnrlib.audit_check.AuditFile(workspace_rootdir=self.workspace_root, update_dashboard=False, thread=self.thread, milestone=self.milestone)
        aftemp = dmx.tnrlib.audit_check.AuditFile(workspace_rootdir=self.workspace_root, update_dashboard=False, thread=self.thread, milestone=self.milestone)
        for checker in self.get_required_checkers():
            flow = checker.flow
            subflow = checker.subflow
            for cell in self.get_cells():
                aftemp.set_test_info(flow, subflow, 'rundir', 'cmdline', self.deliverable, cell, variant=self._ipname)
                audit_filepath = aftemp.get_audit_file_path()
                try:
                    af.load(audit_filepath)
                    failures = af.run_audit()
                    self.log_test_failures(failures)
                except Exception as e:
                    #logger.debug("Caught an Exception during audit validation: {}".format(str(e)))
                    self.log_test_fail(flow=flow, subflow=subflow, topcell=cell, libtype=self.deliverable, error='WAIVABLE Exception validating audit log {}: {}'.format(audit_filepath, str(e)))
        self.logger.info(">>> =COMPLETE= run_audit_check ({}/{})".format(self._ipname, self.deliverable))


    def run_type_check(self):
        self.logger.info(">>> =START= run_type_check ({}/{})".format(self._ipname, self.deliverable))
        failures = []
        for cellname in self.get_cells():
            tc = cmx.tnrlib.typecheck.TypeCheck(self.workspace_root, self._ipname, cellname, self.deliverable, self.get_family_obj())
            errors = tc.runCheck()
            for error in errors:
                failures.append([self._ipname, self.deliverable, cellname, self.deliverable, 'type', error])
        self.log_test_failures(failures)
        self.logger.info(">>> =COMPLETE= run_type_check ({}/{})".format(self._ipname, self.deliverable))


    def report_errors(self, errors):
        '''
        Reports the TestFailure objects sorted by
        - flow, subflow, variant, libtype, topcell, error
        TestFailure object == TestFailure(variant=u'an', libtype='lint', topcell='', flow='deliverable', subflow='type', error='VP/templateset not yet available')
        '''
        
        sum = {'failed':0, 'hsdeswaived':0, 'cmdwaived':0, 'webwaived':0, 'total':0}

        errmsg = ''
        waivemsg = ''
        if errors:
            errors = sorted(errors, key=lambda e: (e.flow, e.subflow, e.variant, e.libtype, e.topcell, e.error))
            errmsg = "cthdmxpoc cthdmxpoc wscheck completed with errors found!\n"
            
            for num, err in enumerate(errors):
            
                if err.error:
                    matched_waiver = self.find_matching_waiver(err.variant, err.flow, err.subflow, err.error)
                    matched_hsdes_waiver = self.find_matching_waiver(err.variant, err.flow, err.subflow, err.error)

                    if not matched_waiver and not matched_hsdes_waiver:
                        sum['failed'] += 1
                        sum['total'] += 1
                        if err.topcell:
                            errmsg += "  {}: {} {} for {}: {}\n".format(sum['failed'], err.flow, err.subflow, err.topcell, err.error)
                        else:
                            errmsg += "  {}: {} {}: {}\n".format(sum['failed'], err.flow, err.subflow, err.error)
                        
                        self._errors['unwaived'].append(err)

                    elif matched_waiver:
                        if 'CommandLine' in matched_waiver:
                            sum['cmdwaived'] += 1
                            sum['total'] += 1
                        else:
                            sum['webwaived'] += 1
                            sum['total'] += 1
                        waivemsg += "  {}: {} {}: {}\n".format(sum['cmdwaived']+sum['webwaived'], err.flow, err.subflow, err.error)

                        self._errors['waived'].append(err)

                    elif matched_hsdes_waiver:
                        if 'HsdesWaiver' in matched_hsdes_waiver:
                            sum['hsdeswaived'] += 1
                            sum['total'] += 1
                        else:
                            sum['webwaived'] += 1
                            sum['total'] += 1
                        waivemsg += "  {}: {} {}: {}\n".format(sum['hsdeswaived']+sum['webwaived'], err.flow, err.subflow, err.error)

                        self._errors['waived'].append(err)


            errmsg += textwrap.dedent("""
            Tests are based on this list of checkers: http://goto/psg_roadmap
            Please consult that site for documentation, owners and ready status of the checkers.
            If you get a missing audit log failure and the corresponding check is marked "not ready" on the web site, 
            please continue with your release. Automatic waivers are created for not ready checks, so that failure
            will not prevent the release. You will need to re-release once the checker is ready.
            """)
        else:
            errmsg = "cthdmxpoc wscheck completed with no errors!\n"
        
        if waivemsg:
            errmsg += textwrap.dedent("""
            ========================================================
            ============= These are the Waived errors. ============= 
            ========================================================
            """)
            errmsg += waivemsg

        errmsg += textwrap.dedent("""
        ===================================
        ============= SUMMARY =============
        ===================================
        ERRORS NOT WAIVED          : {failed}
        ERRORS WITH HSDES WAIVED   : {hsdeswaived}
        ERRORS WITH CMDLINE WAIVED : {cmdwaived}
        ERRORS WITH SW-WEB  WAIVED : {webwaived}
        ===================================
        TOTAL ERRORS FOUND         : {total}
        ===================================
        """.format(**sum))

        errmsg += textwrap.dedent('''
        ------------------------
        WORKAREA: {}
        ------------------------
        '''.format(self.workspace_root))
        self.logger.info(errmsg)

        # http://pg-rdjira:8080/browse/DI-779
        # 0 = check executed and no error found
        # 1 = (check executed and error found) or (system error)
        if int(sum['failed']) > 0:
            self._exit_code = 1
        self.report_message = errmsg

        return errmsg

