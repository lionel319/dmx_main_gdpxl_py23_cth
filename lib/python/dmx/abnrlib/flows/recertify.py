#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/recertify.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: dmx "recertify" subcommand plugin
Author: Lionel Tan Yoke Liang
Documentation: https://wiki.ith.intel.com/display/tdmaInfra/Release+Configuration+Re-Certification
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import sys
import os
import logging
import textwrap
from pprint import pprint

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, rootdir)

import dmx.abnrlib.icm
import dmx.abnrlib.config_factory
import dmx.utillib.arcutils
import dmx.utillib.utils
import dmx.dmxlib.workspace
import dmx.abnrlib.goldenarc_db
import dmx.abnrlib.certificate_db


class RecertifyError(Exception): pass

class Recertify(object):
    '''
    Class to certify if a project/variant@config is reusable for a given thread/milestone.
    '''

    def __init__(self, project, variant, config, thread, milestone, reuse_workspace='', completerun=False, devmode=False, preview=False):
        '''
        reuse_workspace is only meant for easing development/troubleshooting work.
        It should never be used for any production.
        Speficy reuse_workspace with an ICM-workspaceroot, and the program will bypass the
            - creation of workspace
            - sync workspace
            - populate workspace 
        ... steps, and directly dive into the validation steps.
        '''
        self.project = project
        self.variant = variant
        self.config = config
        self.thread = thread
        self.milestone = milestone
        self.reuse_workspace = reuse_workspace
        self.completerun = completerun
        self.devmode = devmode
        self.preview = preview
        self.icm = dmx.abnrlib.icm.ICManageCLI(preview=preview)
        self.logger = logging.getLogger(__name__)


        self.wsname = ''
        self.wsroot = ''
        self.wsobj = None
        self.topcfobj = None    # Top pvc configFactory Object
        self.errors = {'delivery':{}, 'version':{}}
        self.all_errors = []


        ### Recertify only allows to be run if the latest dmx and dmxdata is used.
        ### unless devmode is True.
        self.verify_if_latest_version_is_used()


    def verify_if_latest_version_is_used(self):
        '''
        '''
        msg = "This command can only be run with the latest version of dmx and dmxdata.\n"
        error = 0

        ### DMX version check
        thisdir = os.path.dirname(os.path.realpath(__file__))
        latestdir = os.path.realpath('/p/psg/flows/common/dmx/current/lib/python/dmx/abnrlib/flows')
        if thisdir != latestdir:
            msg += "Your   version:{}\nLatest version:{}\n".format(thisdir, latestdir)
            error += 1

        ### DMXDATA version check
        thisdir = os.path.realpath(os.getenv("DMXDATA_ROOT", ""))
        latestdir = os.path.realpath('/p/psg/flows/common/dmxdata/current')
        if thisdir != latestdir:
            msg += "Your   version:{}\nLatest version:{}\n".format(thisdir, latestdir)
            error += 1

        if error:
            if self.devmode:
                self.logger.warning(msg)
            else:
                raise RecertifyError(msg)
        else:
            self.logger.info("OK: Latest dmx and dmxdata is used.")

    
    def run(self):
        '''
        Runs the createsnapshot command
        '''
        ret = 1

        if not self.reuse_workspace:
            self.verify_project_variant_config(self.project, self.variant, self.config)
            self.verify_thread_milestone(self.project, self.thread, self.milestone)

            self.logger.info("Creating workspace ...")
            self.wsname = self.icm.add_workspace(self.project, self.variant, self.config)
            self.logger.info("Workspace {} created ...".format(self.wsname))

            self.logger.info("Skeleton syncing workspace ...")
            self.icm.sync_workspace(self.wsname) # skeleton sync
            self.wsroot = os.path.join(os.getcwd(), self.wsname)
            
            self.logger.info("Populating workspace ...")
            self.populate_workspace(self.wsroot)
        else:
            self.wsroot = self.reuse_workspace
        
        self.wsobj = dmx.dmxlib.workspace.Workspace(self.wsroot)
        self.wsname = self.wsobj.name
        self.topcfobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(
            self.project, self.variant, self.config)

        
        self.logger.info("Running recertify process for all deliverables and ip. This may take a while ...")
        status = self.run_certify()
        if status:
            # FAILED
            self.report_errors2()
        else:
            # PASSED
            self.logger.info("Successfully Recertified.")
            if self.devmode or self.reuse_workspace:
                self.logger.info("--devmode/--reusews is used. No certification granted.")
            else:
                self.logger.info("Adding {}/{}@{} to {}/{} certificate Database ...".format(
                    self.project, self.variant, self.config, self.thread, self.milestone))
                self.grant_certification()


    def grant_certification(self):
        ''' '''
        c = dmx.abnrlib.certificate_db.CertificateDb()
        c.add_certified_list(self.thread, self.milestone, self.project, self.variant, self.config)


    def run_certify(self):
        '''
        if fail: return 1
        if pass: return 0
        '''
        status = 0
        os.chdir(self.wsroot)
        for c in self.topcfobj.flatten_tree():
            if c.is_composite():
                libtype = None
            else:
                libtype = c.libtype

            pvcstr = dmx.utillib.utils.format_configuration_name_for_printing(
                c.project, c.variant, c.config, libtype)
            self.logger.debug("Certifying {} ...".format(pvcstr))

            ######################################################
            ### Certify a single unit (a libtype, or a variant)
            ######################################################
            this_errors = self.certifying_single_unit(c.variant, libtype)
            self.all_errors += this_errors
            if this_errors:
                self.logger.debug(" - FAIL: Certify_of_delivery({})".format(pvcstr))
                status = 1
                if not self.completerun:
                    return status
            else:
                self.logger.debug(" - PASS: Certify_of_delivery({})".format(pvcstr))

        return status


    def certifying_single_unit(self, variant, libtype):
        '''
        Verifying a single libtype/variant in the workspace and make sure that it passes.
        
        if fail:
            return [list-of-errors]
        if pass:
            return []
        '''
        logging.disable(logging.WARNING)

        if libtype == None:
            ### Variant level check
            ### - check for missing libtypes (ie: libtypes that needs to be delivered)
            self.wsobj.check(variant, self.milestone, self.thread, deliverable=libtype, nowarnings=True,
                validate_deliverable_existence_check=True,
                validate_type_check=False,
                validate_checksum_check=False,
                validate_result_check=False,
                validate_goldenarc_check=False)
        else:
            ### Libtyle-level check
            ### - check for missing audit files (ie: checks that was not run)
            ### - check for mis-align goldenarc resource version
            self.wsobj.check(variant, self.milestone, self.thread, deliverable=libtype, nowarnings=True,
                validate_deliverable_existence_check=False,
                validate_type_check=False,
                validate_checksum_check=False,
                validate_result_check=False,
                validate_goldenarc_check=True)
        logging.disable(logging.NOTSET)

        errors = [] 
        errors = self.extract_deliverable_existence_errors(self.wsobj.errors)
        errors += self.extract_unwaivable_errors(self.wsobj.errors)
        return errors


    def report_errors2(self):
        '''
        Reports the TestFailure objects sorted by
        - flow, subflow, variant, libtype, topcell, error
        TestFailure object == TestFailure(variant=u'an', libtype='lint', topcell='', flow='deliverable', subflow='type', error='VP/templateset not yet available')
        '''
        
        sum = {'failed':0, 'cmdwaived':0, 'webwaived':0, 'total':0}

        errmsg = ''
        waivemsg = ''
        errors = self.all_errors
        if errors:
            errors = sorted(errors, key=lambda e: (e.flow, e.subflow, e.variant, e.libtype, e.topcell, e.error))
            
            errmsg = "dmx recertify for {}/{}@{} on {}/{} completed with errors found!\n".format(self.project, self.variant, self.config, self.milestone, self.thread)
            
            for num, err in enumerate(errors):
            
                if err.error:

                    sum['failed'] += 1
                    sum['total'] += 1
                    if err.topcell:
                        errmsg += "  {}: {} {} for {}: {}\n".format(sum['failed'], err.flow, err.subflow, err.topcell, err.error)
                    else:
                        errmsg += "  {}: {} {}: {}\n".format(sum['failed'], err.flow, err.subflow, err.error)
                        

            errmsg += textwrap.dedent(""" """)

        else:
            errmsg = "dmx recertify for {}/{}@{} on {}/{} completed with no errors!\n".format(self.project, self.variant, self.config, self.milestone, self.thread)
        

        errmsg += textwrap.dedent("""
        ===================================
        ============= SUMMARY =============
        ===================================
        TOTAL ERRORS FOUND         : {total}
        ===================================
        """.format(**sum))

        self.logger.error(errmsg)



    def extract_unwaivable_errors(self, errors):
        ''' 
        Given the list of errors returned from workspace.check()
        return a list of unwaived errors which has 'UNWAIVABLE' in error message
        '''
        retlist = []
        for e in errors['unwaived']:
            if 'UNWAIVABLE' in e.error:
                retlist.append(e)
        return retlist


    def extract_deliverable_existence_errors(self, errors):
        '''
        Given the list of errors returned from workspace.check()
        return a list of unwaived errors which match flow=deliverable, subflow=existence.
        '''
        retlist = []
        for e in errors['unwaived']:
            if e.flow == 'deliverable' and e.subflow == 'existence':
                retlist.append(e)
        return retlist


    def populate_workspace(self, wsroot):
        os.chdir(wsroot)
        os.system("icmp4 sync '*/ipspec/...'        >& /dev/null ")
        os.system("icmp4 sync '*/*/audit/...'       >& /dev/null ")
        os.system("icmp4 sync '*/*/tnrwaivers.csv'  >& /dev/null ")



    def verify_project_variant_config(self, project, variant, config):
        if not config.startswith("REL"):
            raise RecertifyError("Only REL Configs are allowed.")
        if not self.icm.project_exists(project):
            raise RecertifyError("Invalid ICM-Project: {}".format(project))
        if not self.icm.variant_exists(project, variant):
            raise RecertifyError("Invalid ICM-Variant: {}".format(variant))
        if not self.icm.config_exists(project, variant, config):
            raise RecertifyError("Invalid ICM-Config: {}".format(config))
        
        return True

    
    def verify_thread_milestone(self, project, thread, milestone):
        family = dmx.ecolib.ecosphere.EcoSphere().get_family_for_thread(thread)
        schedule_items = family.get_valid_milestones_threads()
        if (milestone, thread) not in schedule_items:
            raise RecertifyError("({}/{}) is not a valid thread/milestone for project:{}".format(
                thread, milestone, project))



