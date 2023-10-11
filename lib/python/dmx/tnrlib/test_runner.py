#!/usr/bin/env python
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/tnrlib/test_runner.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $
"""
This is the main test runner supporting the quick 
test utility and gated releases.

You provide it an IC Manage workspace directory, the 
collateral to be tested, and a target milestone.  It
talks to the web server to find out what tests are 
required for that milestone, runs them, and returns
the results as a list of TestFailures.
"""
import os
from sys import exc_info
from traceback import format_exception
from logging import getLogger, ERROR
from xml.etree import ElementTree as ET
from glob import glob
import re
from dmx.utillib.decorators import memoized
import threading
import multiprocessing
from pprint import pprint, pformat
import time

# Altera libs
import os,sys
rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)
from dmx.tnrlib.execute import execute
import dmx.tnrlib.audit_check
from dmx.tnrlib.test_result import TestFailure, TestResult

from dmx.abnrlib.icm import ICManageCLI
from dmx.dmlib.ICManageConfiguration import ICManageConfiguration 
from dmx.dmlib.ICManageWorkspace import ICManageWorkspace

from dmx.checklib.manifestcheck import ManifestCheck
from dmx.checklib.datacheck import DataCheck

### This one we still need 
import dmx.ecolib.ecosphere


# These match the check_type options in web/ice/models.py for class Test
DATA_CHECK = 'd'
CONTEXT_CHECK = 'c'

logger = getLogger(__name__)

@memoized
def get_topcells(workspace_root, variant):
    """
    Get the list of top cells for the variant in the workspace.
    """
    icm_ws = ICManageWorkspace(workspace_root)
    topcells = icm_ws.getCellNamesForIPName(variant)
    return topcells

class TestRunner(object):
    """
    Provides the common elements required by "quick test" 
    and the gated release runner.  Basically, the ability 
    to identify and execute tests associated with a release
    target.  This class must never depend on the release
    queue or the dashboard -- it just runs tests as identified
    by the roadmap (via the web api).

    log_audit_validation_to_splunk defaults to true because
    ReleaseRunner needs to log audit arc resource details
    to support ARC Resource reports on the release dashboard.
    """
    def __init__(self, project, variant, libtype, configuration, workspace_root, milestone, thread, web_api=None, dashboard_context={}, development_mode=False, splunk_app_name='qa', log_audit_validation_to_splunk=True, views=None, validate_deliverable_existence_check=True, validate_type_check=True, validate_checksum_check=True, validate_result_check=True, validate_goldenarc_check=False, familyobj=None, only_run_flow_subflow_list=None, prel=None):
        """
        workspace_root - the absolute path to the root of the IC Manage workspace 

        configuration - the name of the IC Manage configuration to be tested/released

        dashboard_context - a dict of key/values pairs for Splunk.
            only provded by the gated release runner and ensures the data logged
            by the audit API is tied to the rest of the release data.
        """
        self.project = project
        self.variant = variant
        self.libtype = libtype 
        self.configuration = configuration
        self.workspace_root = workspace_root 
        self.milestone = milestone
        self.thread = thread
        self.eco = dmx.ecolib.ecosphere.EcoSphere(workspaceroot=self.workspace_root)
        self.family = self.eco.get_family_for_thread(thread)
        if familyobj:
            self.family = familyobj
        self.roadmap = self.eco.get_roadmap_for_thread(thread)
        self.ip = self.family.get_ip(self.variant, self.project)
        self.views = views
        self.validate_deliverable_existence_check = validate_deliverable_existence_check
        self.validate_type_check = validate_type_check
        self.validate_checksum_check = validate_checksum_check
        self.validate_result_check = validate_result_check
        self.validate_goldenarc_check = validate_goldenarc_check


        self.web_api = None

        self.splunk_app_name = splunk_app_name
        self.log_audit_validation_to_splunk = log_audit_validation_to_splunk
        self.dashboard_context = dashboard_context

        self.development_mode = development_mode

        # List of files referenced by tests; populated before invoking any tests
        self.files_to_sync = []

        # List of TestFailure named tuple for each test failure
        # More for backward compatibility since test_results 
        # provides this and more...
        self.tests_failed = []
        self.tests_failed = multiprocessing.Manager().list()

        # A list of TestResult named tuples stored in the order they were executed
        self.test_results = []
        self.test_results = multiprocessing.Manager().list()

        ### Get exempted libtypes
        self.exempted_varlibs = self.get_exempted_varlibs()

        ### Provide an option/flexibility to only run per list of flow/subflow
        self.only_run_flow_subflow_list = only_run_flow_subflow_list

        ### Introduced a new variable to store the parent *.f files of the children xml audit logs
        self.audit_log_parents = {}

        ### Support for prel
        self.prel = prel
        if not self.prel:
            self.prels = None
        else:
            self.prels = [self.prel]

        if self.prel and self.views:
            raise Exception("Prel:{} and Views:{} cannot be used together.".format(self.prel, self.views))
        

    def get_exempted_varlibs(self):
        ''' 
        '''
        exempted_varlibs = []
        unneeded_deliverables = self.get_unneeded_deliverables()

        exempted_libtypes = self.get_libtype_where_all_topcells_unneeded(unneeded_deliverables)
        if exempted_libtypes:
            exempted_varlibs = [[self.variant, libtype] for libtype in exempted_libtypes]
        logger.debug("test_runner.exempted_varlibs(only  unneeded): {}".format(exempted_varlibs))
      
        roadmap_libtypes = [x.name for x in self.ip.get_all_deliverables(milestone='99', roadmap=self.roadmap)]
        view_libtypes = [x.name for x in self.ip.get_deliverables(milestone=self.milestone, roadmap=self.roadmap, views=self.views)]
        exempted_libtypes = list(set(roadmap_libtypes) - set(view_libtypes))
        logger.debug("- test_runner.roadmap_libtypes: {} {}".format(roadmap_libtypes, len(roadmap_libtypes)))
        logger.debug("- test_runner.view_libtypes: {} {}".format(view_libtypes, len(view_libtypes)))
        logger.debug("- test_runner.exempted_libtypes: {} {}".format(exempted_libtypes, len(exempted_libtypes)))
        if exempted_libtypes:
            exempted_varlibs += [['*', libtype] for libtype in exempted_libtypes]
      
        logger.debug("test_runner.exempted_varlibs(views+unneeded): {}".format(exempted_varlibs))
        return exempted_varlibs


    def run_tests(self):
        """
        The tests to run include:
          - deliverable filetype checks (library releases)
          - audited library checks (library releases)
          - deliverable existence checks (variant releases)
          - audit validations based on the roadmap (variant releases)

        Info is a set of fields for the dashboard including
        request_id so test results can be grouped with the 
        overall request.

        Returns a list of failures.  Passed and skipped tests
        can be gotten via other methods of this class.
        """
        unneeded_deliverables = self.get_unneeded_deliverables()
        unneeded_deliverables_for_all_topcells = self.get_libtype_where_all_topcells_unneeded(unneeded_deliverables)

        if self.libtype is None:
            # Variant release
            if self.validate_deliverable_existence_check:
                self.run_deliverable_existence_checks(unneeded_deliverables)
            self.run_audit_validation(unneeded_deliverables)
        else:
            # Library release
            if self.libtype in unneeded_deliverables_for_all_topcells:
                ### http://pg-rdjira.altera.com:8080/browse/DI-1301
                ### make it an UNWAIVABLE error if user is trying to do libtype release on an unneeded libtype.
                logger.debug("Error: Releasing an unneeded deliverable is not allowed.")
                self.log_test_fail(flow='unneeded', subflow=self.libtype, libtype=self.libtype, error='Not allowed to release {} because it is defined as unneeded.(UNWAIVABLE)'.format(self.libtype))
            elif self.libtype in [libtype for (topcell,libtype) in unneeded_deliverables]:
                logger.debug("Skipping type checks for unneeded deliverable, %s" % self.libtype)
                self.log_test_skip(flow='unneeded', subflow='deliverable', libtype=self.libtype, topcell='', message='IPSPEC indicates %s will never be provided for some/all top cells; skipping type checks.' % self.libtype)
            else:
                if self.validate_type_check:
                    self.run_deliverable_filetype_check()

            ### Explicitly skip for ipspec as ipspec does not have audit check
            ### http://pg-rdjira:8080/browse/DI-419
            if self.libtype != 'ipspec':
                self.run_audit_validation(unneeded_deliverables)

        return self.tests_failed

    def get_unneeded_deliverables(self):
        """
        Reads the unneeded deliverables from ipspec
        and returns a list of (topcell,deliverable)
        which are declared as "unneeded" -- that is
        they will never be provided by this variant.
        """
        logger.debug("Getting unneeded deliverables...")
        results = []
        for unneeded_file in self.get_unneeded_deliverable_filepaths():
            logger.debug("Analyzing file %s" % unneeded_file)
            topcell = os.path.basename(unneeded_file).replace('.unneeded_deliverables.txt','') #.encode('ascii','ignore')
            if not topcell in get_topcells(self.workspace_root, self.variant):
                logger.error("Detected unneeded deliverable file (%s) for an unknown top cell (one not in cell_names.txt)" % unneeded_file)
            else:
                for libtype in self.get_unneeded_deliverables_from_file(unneeded_file):
                    results.append( (topcell, libtype) )

        logger.debug("Unneeded deliverables (topcell,libtype) detected: %s" % results)
        return results

    def get_unneeded_deliverable_filepaths(self):
        """
        Returns a list of path names which are unneeded deliverables files.
        """
        ipspec_dir = os.path.join(self.workspace_root, self.variant, 'ipspec')
        return glob(os.path.join(ipspec_dir, '*.unneeded_deliverables.txt'))

    def get_unneeded_deliverables_from_file(self, filepath):
        """
        Reads the libtypes (one per line) from the given file.
        Ignores lines whose first non-blank character is #
        """
        libtypes = []
        for line in self.get_file_lines(filepath):
            clean = line.strip().upper()
            if len(clean)>0 and not clean.startswith('#'):
                if clean == 'IPSPEC':
                    logger.error("IPSPEC cannot be listed as an unneeded deliverable in %s" % filepath)
                else:
                    ### Avoid adding duplicated entries of the same libtype
                    d = clean.lower()
                    if d not in libtypes:
                        libtypes.append(d)
                    else:
                        logger.warning("Duplicated libtype({}) entry in {}".format(d, filepath))
    
        return libtypes


    def get_file_lines(self, filepath):
        """
        Returns a list of all the lines in the given file.
        Using this instead of just readlines() facilitates unit testing.
        """
        lines = []
        with open(filepath, 'r') as f:
            lines = f.readlines()

        return lines

    def run_deliverable_existence_checks(self, unneeded_deliverables):
        """
        The snapshot configuration must contain all the required libtypes under the variant
        being released.  The only exceptions are any deliverables which are listed as
        "unneeded" in ipspec (a single top cell being unneeded means the deliverable is unneeded).
        """
        exempt_libtypes = self.get_libtype_where_all_topcells_unneeded(unneeded_deliverables)
        libtypes = self.get_required_libtypes()
        logger.debug("required deliverables: {}".format(libtypes))
        for libtype in libtypes:
            if not libtype in exempt_libtypes:
                self.check_libtype_in_config_for_variant(libtype, self.configuration, self.variant)

    def get_libtype_where_all_topcells_unneeded(self, unneeded_deliverables):
        """
        Unneeded delivarables is a list of tuples: (topcell, libtype)
        This function returns those libtypes which have an entry in
        unneeded_deliverables for EVERY top cell defined for this variant.
        """
        topcells = get_topcells(self.workspace_root, self.variant)
        logger.debug("Seeing which libtypes are excluded for all topcells (%s)..."%topcells)
        num_topcells = len(topcells)

        topcell_counts = {}
        for (topcell,libtype) in unneeded_deliverables:
            topcell_counts.setdefault(libtype, 0)
            topcell_counts[libtype] += 1

        logger.debug("topcell_counts: %s" % topcell_counts)

        result = [libtype for (libtype,count) in topcell_counts.items() if count==num_topcells]
        logger.debug("These: %s" % result)
        return result

    def check_libtype_in_config_for_variant(self, libtype, configuration, variant, log_test_fail=True):
        """
        Variants releases are required to include certain deliverables.
        This test checks the configuration to make sure they all exist.
        If the configuration top level variant contains the given libtype
        this test passes, otherwise it is a failure.
        """
        cf = self.eco._workspace.get_config_factory_object()
        match = cf.search(variant='^{}$'.format(variant), libtype='^{}$'.format(libtype))
        if match:
            logger.debug("Check that libtype %s in configuration passed." % libtype)
            retval = True
        else:
            if log_test_fail:
                self.log_test_fail(flow='deliverable', subflow='existence', libtype=libtype, error='Libtype %s is required by the roadmap, but not included in the release configuration.' % libtype)
            retval = False
        return retval


    def get_required_audit_logs(self, include_all_files=False, unneeded_deliverables=[]):
        """
        A complete list of the audit logs required for this test run.
        Includes not only top level audit logs, but also all audit logs
        referenced in audit filelists.
        """
        (audit_files, required_files) = self.get_required_files(include_all_files, unneeded_deliverables)
        return audit_files

    def get_required_files_from_required_audits(self, include_all_files=False, unneeded_deliverables=[]):
        """
        A complete list of the required files as specified in audit logs
        required for this test run.
        """
        (audit_files, required_files) = self.get_required_files(include_all_files, unneeded_deliverables)
        return required_files

    #Ideally, @memoized, but I think we have to make it global for that...
    def get_required_files(self, include_all_files=False, unneeded_deliverables=[], generate_reqfiles_info=False):
        """
        Returns a tuple (list of audit logs and list of required files)
        all workspace-relative, of the file paths that will need to be 
        synced before audit validation can be run.  The required files
        are those specified in the audit logs.  It is assumed that the 
        audit files themselves have already been synced before calling
        this method.
        Setting include_all_files=True will include all required files
        even for data checks.  The default is False, which is all that
        is required to be synced for a release to work.  The True option
        supports quick warnings per CASE:295543 and CASE:287314.

        When generate_reqfiles_info=True, return an extra 3rd value(dict), which looks like this:-
        {
            audit_xml_file_1: {
                varlib = [variant, libtype],
                reqfiles: {
                    reqfile_1: {filter:str, rcs_disable:bool, varlib:(variant, libtype), checksum:str},
                    reqfile_n: {filter:str, rcs_disable:bool, varlib:(variant, libtype), checksum:str},
                    ...   ...   ...
                }
            },
            audit_xml_file_n: {
                varlib = [variant, libtype],
                reqfiles: {
                    reqfile_1: {filter:str, rcs_disable:bool, varlib:(variant, libtype), checksum:str},
                    reqfile_n: {filter:str, rcs_disable:bool, varlib:(variant, libtype), checksum:str},
                    ...   ...   ...
                }
            },
            ...   ...   ...

        }
        """
        audit_logs = []
        audit_logs_fullpath = []
        required_files = []
        reqfiles_info = {}


        variant_type = self.get_variant_type()
        required_tests = self.get_required_tests(self.project, self.milestone, self.thread, variant_type)

        for topcell in get_topcells(self.workspace_root, self.variant):
            for (libtype, flow, subflow, check_type, checker, owner_name, owner_email, owner_phone) in required_tests:
                if libtype == self.libtype:
                    # Library release: we only check required files for data checks.
                    if not (topcell,libtype) in unneeded_deliverables and (check_type == DATA_CHECK or include_all_files):
                        tmplogs_fp = dmx.tnrlib.audit_check.AuditFile.get_audit_file_paths_for_testable_item(self.workspace_root, self.variant, libtype, topcell, flow, subflow)
                        audit_logs_fullpath += tmplogs_fp
                        logger.debug("get_required_files for %s %s %s need audit logs: %s" % (topcell, flow, subflow, audit_logs_fullpath))

                        tmplogs = [self.remove_workspace_from_filepath(audit_fullpath) for audit_fullpath in tmplogs_fp]
                        audit_logs += tmplogs

                elif self.libtype is None:
                    # Variant release: only check required files for context checks (unless user asked to include all files)
                    if (not (topcell,libtype) in unneeded_deliverables and check_type == CONTEXT_CHECK):
                        tmplogs_fp = dmx.tnrlib.audit_check.AuditFile.get_audit_file_paths_for_testable_item(self.workspace_root, self.variant, libtype, topcell, flow, subflow)
                        audit_logs_fullpath += tmplogs_fp
                        
                        tmplogs = [self.remove_workspace_from_filepath(audit_fullpath) for audit_fullpath in tmplogs_fp]
                        audit_logs += tmplogs


        for audit_file in audit_logs_fullpath:
            audit_api = dmx.tnrlib.audit_check.AuditFile(self.workspace_root, logger=None, web_api=self.web_api, update_dashboard=self.log_audit_validation_to_splunk, development_mode=self.development_mode, splunk_app_name=self.splunk_app_name, thread=self.thread)
            logger.debug("Analyzing audit log for required_files: %s" % audit_file)
            try:
                audit_api.load(audit_file)
                if not generate_reqfiles_info:
                    required_files += audit_api.get_required_files()
                else:
                    tmp = audit_api.get_required_files(generate_reqfiles_info=generate_reqfiles_info)
                    required_files += tmp[0]
                    reqfiles_info.update(tmp[1])

                if audit_api.is_audit_filelist(audit_file):
                    tmplogs = audit_api.get_filelist_audit_files()
                    audit_logs += tmplogs
                    
                    self.update_audit_log_parents(tmplogs, audit_file)
            except:
                logger.debug('Caught an Exception during audit scan for required files! %s' % format_exception(*exc_info()))

        if not generate_reqfiles_info:
            return (audit_logs, required_files)
        else:
            return (audit_logs, required_files, reqfiles_info)



    def find_skippable_required_files(self):
        ''' '''
        retlist = {}
        errlist = {}
        
        required_audit_logs, required_chksum_files, reqfiles_info = self.get_required_files(include_all_files=True, generate_reqfiles_info=True)
        logger.debug("reqfiles_info:({}) ==>".format(len(reqfiles_info)))
        logger.debug("{}".format(pformat(reqfiles_info)))

        same_varlib_reqfiles = self._get_all_reqfile_which_is_from_same_varlib_audit_file(reqfiles_info)
        logger.debug("SAME_VARLIB_REQFILES: ({}) ==>".format(len(same_varlib_reqfiles)))
        logger.debug("{}".format(pformat(same_varlib_reqfiles)))

        for reqfile_name, reqfile_dict in same_varlib_reqfiles.iteritems():
            meta = self._get_meta_info_for_reqfile_across_all_audit_files(reqfile_name, reqfiles_info)
            if len(meta.keys()) == 1:
                retlist[reqfile_name] = meta
            else:
                errlist[reqfile_name] = meta

        logger.debug("SKIPPABLE:({}) ==>".format(len(retlist)))
        logger.debug("{}".format(pformat(retlist)))
        logger.debug("MISMATCH:({}) ==>".format(len(errlist)))
        logger.debug("{}".format(pformat(errlist)))

        return retlist


    def _get_all_reqfile_which_is_from_same_varlib_audit_file(self, reqfiles_info):
        '''
        extract out all the reqfiles which is from the same varlib as their audit xml files,
        and store it in a dict like this:-

        same_varlib_reqfiles = {
            'z1574a/cdl/z1574a_z1574f.cdl': {'checksum': '4350bcdb1ab6441f41f58027bc0145c2',
                                            'filter': '^\\*\\s*Netlisted on:.*$',
                                            'rcs_disable': '',
                                            'varlib': ['z1574a', 'cdl']},
             'z1574a/complib/complist/complist_z1574a_z1574f.txt': {'checksum': '78c504bdbdf588bfbc4016a27e31dbef',
                                            'filter': '',
                                            'rcs_disable': None,
                                            'varlib': ['z1574a', 'complib']},
            ...   ...   ...
        }
        '''
        same_varlib_reqfiles = {}
        for xmlfile_name, xmlfile_dict in reqfiles_info.iteritems():
            for reqfile_name, reqfile_dict in xmlfile_dict['reqfiles'].iteritems():
                if reqfile_dict['varlib'] == xmlfile_dict['varlib']:
                    same_varlib_reqfiles[reqfile_name] = reqfile_dict
        return same_varlib_reqfiles


    def _get_meta_info_for_reqfile_across_all_audit_files(self, filename, reqfiles_info):
        ''' '''
        ### Every key in meta should be equal in order to pass
        meta = {'checksum':'', 'filter':'', 'rcs_disable':''}
        retlist = {}

        for xmlfile_name, xmlfile_dict in reqfiles_info.iteritems():
            for reqfile_name, reqfile_dict in xmlfile_dict['reqfiles'].iteritems():
                if reqfile_name == filename:
                    key = (reqfile_dict['checksum'], reqfile_dict['filter'], reqfile_dict['rcs_disable'])
                    if key not in retlist:
                        retlist[key] = [xmlfile_name]
                    else:
                        retlist[key].append(xmlfile_name)

        return retlist


    def update_audit_log_parents(self, auditlogs, parent_f):
        '''
        '''
        for al in self._cleanup_required_files(auditlogs):
            bn_xml = os.path.basename(al)
            bn_f = os.path.basename(parent_f)
            if bn_xml not in self.audit_log_parents:
                self.audit_log_parents[bn_xml] = [bn_f]
            else:
                self.audit_log_parents[bn_xml].append(bn_f)

    def decipher_topcell_fsf_from_auditlog(self, auditlog):
        ''' given an auditlog xml/f file, return (topcell, flowsubflow)
        '''
        bn = os.path.basename(auditlog)
        return bn.split('.')[1:3]


    def get_required_varlibs(self, required_files):
        '''
        Given a list of required_files (output of get_required_files_from_required_audits()),
        return all the [variant, libtype] that are impacted.

        Example:-
            required_files == [
                'liotest1/rdf/no_such_file.txt',
                'liotest1/rdf/file1.txt',
                'liotest1/pv/c.txt',
                'liotest1/stamod/c.txt',
                'liotest2/rdf/no_such_file.txt',
                'liotest2/rdf/file1.txt',
                'liotest2/pv/c.txt',
                'liotest2/stamod/c.txt',
                ]

            return == [
                ('liotest1', 'rdf'),
                ('liotest1', 'pv'),
                ('liotest1', 'stamod'),
                ('liotest2', 'rdf'),
                ('liotest2', 'pv'),
                ('liotest2', 'stamod'),
            ]
        '''
        retval = []
        for f in self._cleanup_required_files(required_files):
            ### Ignore files that starts with '/' , as it is not files within this workspace
            if not f.startswith('/'):
                var, lib = f.split('/')[0:2]
                retval.append((var, lib))

        return list(set(retval))


    def _cleanup_required_files(self, filelist):
        '''
        There's some strange thing happening.
        Some returned value in the list are only 1 single character, 
        which is clearly some bug.
        Thus, this method removes those problematic values.
        '''
        retval = []
        for f in filelist:
            if len(f) > 2:
                retval.append(f)
        return retval

    def run_audit_validation(self, unneeded_deliverables=[]):
        """
        Validates the audit files required by the roadmap.
        """
        logger.debug("run_audit_validation_for_library_release()")

        ### If all audit related checks are turned off, skip.
        ### http://pg-rdjira:8080/browse/DI-1410
        if self.validate_checksum_check==False and self.validate_result_check==False and self.validate_goldenarc_check==False:
            logger.debug("Skipping audit validation as all audit file related checks were set to False.")
            return

        variant_type = self.get_variant_type()
        logger.debug("variant type: %s" % variant_type)
        #required_tests = self.web_api.get_required_tests(self.project, self.milestone, self.thread, variant_type)
        required_tests = self.get_required_tests(self.project, self.milestone, self.thread, variant_type)
        logger.debug("required tests: %s" % required_tests)

        ### Check if the libtype exists in the composite configuration
        ### http://pg-rdjira:8080/browse/DI-267
        ### http://pg-rdjira:8080/browse/DI-303
        if self.libtype is None:
            libtype_in_config = {}
            for (libtype, flow, subflow, check_type, checker, owner_name, owner_email, owner_phone) in required_tests:
                if libtype not in libtype_in_config:
                    libtype_in_config[libtype] = self.check_libtype_in_config_for_variant(libtype, self.configuration, self.variant, log_test_fail=False)

        all_audit_logs = []
        # Loop over all top cells for the given variant
        for topcell in get_topcells(self.workspace_root, self.variant):
            logger.debug("Test top cell: %s" % topcell)
            for (libtype, flow, subflow, check_type, checker, owner_name, owner_email, owner_phone) in required_tests:
                audit_logs = []
                audit_result_logs = []
                # Library release
                if libtype == self.libtype:
                    is_variant_rel = False
                    if (topcell,libtype) in unneeded_deliverables: 
                        logger.debug("Skipping %s checks for unneeded deliverables for %s %s" % (libtype, self.variant, topcell))
                        self.log_test_skip(flow=flow, subflow=subflow, message='Skipping %s %s audit checks based on ipspec/%s.unneeded_deliverables.txt' % (topcell, flow, topcell), libtype=libtype, topcell=topcell)
                    elif check_type == DATA_CHECK:
                        logger.debug("Locating audit files for %s %s check for %s" % (flow, subflow, libtype))
                        audit_logs = dmx.tnrlib.audit_check.AuditFile.get_audit_file_paths_for_testable_item(self.workspace_root, self.variant, libtype, topcell, flow, subflow)
                        if len(audit_logs) == 0:
                            self.log_test_fail(flow=flow, subflow=subflow, topcell=topcell, error='Could not find any audit files for %s %s %s check' % (topcell, flow, subflow), libtype=libtype)
                    elif check_type == CONTEXT_CHECK:
                        logger.debug("Libtype release will now run full context_check too:  %s %s for %s" % (flow, subflow, libtype))
                        audit_logs = dmx.tnrlib.audit_check.AuditFile.get_audit_file_paths_for_testable_item(self.workspace_root, self.variant, libtype, topcell, flow, subflow)
                        if len(audit_logs) == 0:
                            self.log_test_fail(flow=flow, subflow=subflow, topcell=topcell, error='Could not find any audit files for %s %s %s results-only check' % (topcell, flow, subflow), libtype=libtype)
                # Variant release
                elif self.libtype is None:
                    is_variant_rel = True
                    if (topcell,libtype) in unneeded_deliverables: 
                        logger.debug("Skipping %s checks for unneeded deliverables for %s %s" % (libtype, self.variant, topcell))
                        self.log_test_skip(flow=flow, subflow=subflow, message='Skipping %s %s audit checks based on ipspec/%s.unneeded_deliverables.txt' % (topcell, flow, topcell), libtype=libtype, topcell=topcell)
                    elif not libtype_in_config[libtype]:
                        logger.debug("Libtype {} is not included in configuration. Skipping all related checks.".format(libtype))
                    elif check_type == CONTEXT_CHECK:
                        logger.debug("Locating audit files for %s %s check" % (flow, subflow))
                        audit_logs = dmx.tnrlib.audit_check.AuditFile.get_audit_file_paths_for_testable_item(self.workspace_root, self.variant, libtype, topcell, flow, subflow)
                        if len(audit_logs) == 0:
                            self.log_test_fail(flow=flow, subflow=subflow, topcell=topcell, error='Could not find any audit files for %s %s %s check' % (topcell, flow, subflow), libtype=libtype)
                
                logger.debug("topcell:{}, libtype:{}, flow:{}, subflow:{}, audit_logs:{}".format(topcell, libtype, flow, subflow, audit_logs))
                if audit_logs:
                    all_audit_logs.append([audit_logs, flow, subflow, libtype, topcell, is_variant_rel])

        # Run the required audit validation
        all_f_files = []    ### all the audit.*.f files
        all_xml_files = []  ### This includes all the audit.*.xml files within all the audit.*.f files
        thread_list = []
        for (audit_files, flow, subflow, libtype, topcell, is_variant_rel) in all_audit_logs:

            if self.only_run_flow_subflow_list and (flow, subflow) not in self.only_run_flow_subflow_list:
                logger.debug("Skipping flow/subflow:({}/{}) as it is not in only_run_flow_subflow_list.".format(flow, subflow))
                continue

            for audit_file in audit_files:

                ### Segregate all the *.xml and *.f files
                ### https://jira01.devtools.intel.com/browse/PSGDMX-1448
                if audit_file.endswith('.f'):
                    audit_api = dmx.tnrlib.audit_check.AuditFile(self.workspace_root, logger=logger, web_api=self.web_api, update_dashboard=self.log_audit_validation_to_splunk, 
                        development_mode=self.development_mode, splunk_app_name=self.splunk_app_name, exempted_varlibs=self.exempted_varlibs, thread=self.thread, milestone=self.milestone)
                    audit_api.load(audit_file)

                    #thread_list.append(threading.Thread(target=self.run_audit, args=(audit_file, flow, subflow, libtype, topcell), kwargs={'results_only':False, 'dont_validate_xml':True}))
                    thread_list.append(multiprocessing.Process(target=self.run_audit, args=(audit_file, flow, subflow, libtype, topcell), kwargs={'results_only':False, 'dont_validate_xml':True}))
                    thread_list[-1].name = "{}:{}".format(thread_list[-1].name, audit_file)
                    all_f_files.append(audit_file)
                    for xmlfile in audit_api.audit_filelist:
                        if xmlfile not in all_xml_files:
                            #thread_list.append(threading.Thread(target=self.run_audit, args=(xmlfile, flow, subflow, libtype, topcell), kwargs={'results_only':False, 'dont_validate_xml':False, 'foreign_checksum_only':is_variant_rel}))
                            thread_list.append(multiprocessing.Process(target=self.run_audit, args=(xmlfile, flow, subflow, libtype, topcell), kwargs={'results_only':False, 'dont_validate_xml':False, 'foreign_checksum_only':is_variant_rel}))
                            thread_list[-1].name = "{}:{}".format(thread_list[-1].name, xmlfile)
                            all_xml_files.append(xmlfile)
                else:
                    if audit_file not in all_xml_files:
                        #thread_list.append(threading.Thread(target=self.run_audit, args=(audit_file, flow, subflow, libtype, topcell), kwargs={'results_only':False, 'dont_validate_xml':False, 'foreign_checksum_only':is_variant_rel}))
                        thread_list.append(multiprocessing.Process(target=self.run_audit, args=(audit_file, flow, subflow, libtype, topcell), kwargs={'results_only':False, 'dont_validate_xml':False, 'foreign_checksum_only':is_variant_rel}))
                        thread_list[-1].name = "{}:{}".format(thread_list[-1].name, audit_file)
                        all_xml_files.append(audit_file)

        process_limit = int(os.getenv("TNR_NPROCESS", 500))
        done_list = []
        running_list = []
        index = 0
        while len(done_list) < len(thread_list):

            ### Remove completed process from `running_list
            ### Add completed process to `done_list
            for p in running_list:
                if not p.is_alive():
                    done_list.append(p)
                    running_list.remove(p)

            ### submit process to run on the available slots
            available_slots = process_limit - len(running_list)
            while index < len(thread_list) and available_slots > 0:
                t = thread_list[index]
                logger.debug("process_limit:{}, available_slots:{}".format(process_limit, available_slots))
                logger.debug("starting process: {}".format(t.name))
                t.start()
                running_list.append(t)
                index += 1
                available_slots -= 1

            time.sleep(5)


        for t in thread_list:
            logger.debug("joining process: {}".format(t.name))
            t.join()





    def run_audit(self, audit_file, flow, subflow, libtype, topcell, results_only, skip_links=False, dont_validate_xml=False, foreign_checksum_only=False):
        """
        Creates an AuditFile instance, loads the given file, runs `AuditFile.run_audit` on it, 
        and then logs the results to Splunk.  Any exceptions are caught and reported via Splunk
        as well.
        """
        # Use separate audit_api instances -- we had some issues with state leaking across instances when we shared them
        audit_api = dmx.tnrlib.audit_check.AuditFile(self.workspace_root, logger=logger, web_api=self.web_api, update_dashboard=self.log_audit_validation_to_splunk, 
            development_mode=self.development_mode, splunk_app_name=self.splunk_app_name, exempted_varlibs=self.exempted_varlibs, thread=self.thread, milestone=self.milestone)
        logger.debug("Analyzing audit log: %s" % audit_file)
        try:
            audit_api.load(audit_file) 
            # We need this info in the info so audit knows how to log errors
            # about missing audit XML files in audit filelists.
            info = dict(self.dashboard_context)
            info['variant'] = self.variant
            info['libtype'] = libtype
            info['topcell'] = topcell
            info['flow'] = flow
            info['subflow'] = subflow
            failures = audit_api.run_audit(info, results_only=results_only, skip_links=skip_links, validate_checksum=self.validate_checksum_check, validate_result=self.validate_result_check, validate_goldenarc=self.validate_goldenarc_check, dont_validate_xml=dont_validate_xml, foreign_checksum_only=foreign_checksum_only)

            logger.debug("Failure from audit: %s" % failures)

            if len(failures) == 0:
                self.log_test_pass(flow=flow, subflow=subflow, libtype=libtype, topcell=topcell, message='Validated %s' % audit_file)
            else:
                self.log_test_failures(failures)

        except Exception as e:
            logger.debug("Caught an Exception during audit validation: {}".format(str(e)))
            self.log_test_fail(flow=flow, subflow=subflow, topcell=topcell, libtype=libtype, error='UNWAIVABLE Exception validating audit log {}: {}'.format(audit_file, str(e)))


    def run_deliverable_filetype_check(self):
        """
        Only run for library releases, this is the "VP type check" which
        ensures the files or patterns defined for the deliverable (in the 
        templateset) actually exist.  VP also supports a minimum number of
        matches for patterns, checking the files referenced in a filelist
        actually exist, and checking the format of filelists.

        This also includes the IPSPEC deliverable data check which is the
        only data check implemented via VP (or DM)
        """
        self.run_type_check()

        if self.libtype == 'ipspec':
            self.run_ipspec_data_check()

    def run_type_check(self):
        """
        Run the type checks and processes the output to detemine pass/fail.
        Returns nothing.
        """
        mc = ManifestCheck(self.workspace_root, ips=[[self.project, self.variant]], deliverables=[self.libtype], roadmap=self.roadmap, prel=self.prel)
        mc.runChecks()
        results = mc.getResults()
        logger.debug("type check results: {}".format(results))
        self.log_vp_results(results)


    def log_vp_results(self, results):
        """
        `results` is a list. 
        It is the output from ManifestCheck() or DataCheck().

        results = [
            (project, variant, libtype, cell, [error1, error2, ...]),
            (project, variant, libtype, cell, [error1, error2, ...]),
            ...   ...   ...
        ]

        """

        ### http://pg-rdjira:8080/browse/DI-1040
        ### Skip symbolic link errors for LargeData Deliverables
        #ldlist = [x.name for x in self.family.get_all_deliverables() if x.large]
        ldlist = [x.name for x in self.family.get_all_deliverables() if x.dm == 'naa']  # changed in dmxdata/11.0 for designsync support
        logger.debug("Large Data Deliverables: {}".format(ldlist))

        if not results:
            self.log_test_fail(flow=self.libtype, subflow='type', error='Your cell_names.txt is empty.  This is not allowed.')
        else:
            for (project, variant, libtype, topcell, errors) in results:
                if libtype == self.libtype:
                    if not errors:
                        self.log_test_pass(flow=self.libtype, subflow='type', topcell=topcell, message='Passed type check')
                    for error in errors:
                        '''
                        This section is no longer needed as it is fixed in dmx/dmlib/CheckerBase.py
                        https://jira01.devtools.intel.com/browse/PSGDMX-36

                        if self.libtype in ldlist:
                            if re.search("pattern file .* contains symbolic link", error):
                                logger.debug("Skipping LargeData symbolic link error: {}".format(error))
                                continue
                        '''
                        self.log_test_fail(flow=self.libtype, subflow='type', topcell=topcell, error=error)
                        

    def get_xunit_test_results(self, xunit_filepath, datacheck):
        """
        Extracts the errors, if any, from the Xunit XML file
        created by vp.  Uses ElementTree to parse the XML by
        hand.  I did that rather than use a library because 
        there is no clear adherence to a set of standards and
        it's just simpler.
        Returns a list of one-line strings (no newlines!) 
        indicating the failure.
        """
        errors = []

        with open(xunit_filepath, 'r') as f:
            tree = ET.fromstring( f.read() )
            testcount = tree.get('tests')
            if testcount != '1':
                errors.append('Internal error running type check: did not find single test result file.')
            else:
                # TODO: don't hard-code the class names in these Xpath expressions
                if datacheck:
                    result_node = tree.find("testcase[@classname='dm.deliverables.ipspec.CheckData.Check']")
                    failure_node = tree.find("testcase[@classname='dm.deliverables.ipspec.CheckData.Check']/failure")
                    check = 'data'
                else:
                    result_node = tree.find("testcase[@classname='dm.VpNadder.VpCheckType']")
                    failure_node = tree.find("testcase[@classname='dm.VpNadder.VpCheckType']/failure")
                    check = 'type'

                if result_node is None:
                    errors.append(self.make_workspace_paths_relative('Failed to find results for %(check)s check in %(xunit_filepath)s' % locals()))
                elif failure_node is not None:
                    error_section = self.remove_stack_trace(failure_node.text)
                    # We can't have single-quotes in the error strings becuase 
                    # they break the JavaScript waiver mechanisms on the dashboard
                    # We build a JS object: {error:'<the_error>'} so if <the_error>
                    # has single-quotes, we get "Uncaught SyntaxError: Unexpected identifier"
                    # TODO: move this into the splunk_log class as a general requirement?
                    lines = [aline.strip().replace("'","") for aline in error_section.splitlines()]
                    # Type checks start with a header line, the ipspec data checks doesn't
                    # Nope, not all of em.  Ugh.
                    if not datacheck and (
                        lines[0].startswith('Verification Failure') 
                        or lines[0].startswith('Found problems with the files described in the templateset')
                        or len(lines[0].strip()) == 0):
                        lines = lines[1:] # Remove that first line
                    # Replace any full paths in workspace with workspace-relative paths.
                    lines = [self.make_workspace_paths_relative(line) for line in lines]
                    errors = lines

        return errors 

    def make_workspace_paths_relative(self, string):
        """
        Replaces any paths under the workspace root with workspace-relative paths
        in the given string.  This basically amounts to stripping out the 
        full path to the workspace root.
        """
        workspace_root_with_trailing_slash = os.path.join(self.workspace_root, '')
        return string.replace(workspace_root_with_trailing_slash, '')

    def remove_stack_trace(self, error):
        """
        vp outputs the entire stack trace for type/data failures, 
        but we only want to show the user the actual error message.

        Basically, strip out everything before "Verification Failure"
        unless that leaves nothing, in which case don't strip anything.

        OK, that doesn't cover all different type checks.  Ugh.  Sometimes 
        there is a stack trace: we don't want that.  So if it starts with 
        "Traceback", ignore that line and all subsequent INDENTED lines.
        """
        result = error

        parts = error.split('Verification Failure: ')
        if len(parts) > 1:
            message = parts[1]
            if message != '':
                result = message 
        else:
            lines = error.splitlines()
            if lines[0].startswith('Traceback'):
                i = 1
                while lines[i].startswith(' '):
                    i += 1
                result = '\n'.join(lines[i:])

        return result

    def run_ipspec_data_check(self):
        """
        Runs the IPSPEC data check, analyzes, and logs the pass/fail results. 
        """
        dc = DataCheck(self.workspace_root, ips=[[self.project, self.variant]], deliverables=['ipspec'], roadmap=self.roadmap)
        dc.runChecks()
        results = dc.getResults()
        logger.debug("ipspec data check results:{}".format(results))
        self.log_vp_results(results)

    def invoke_vp_data_check(self):
        """
        Calls the vpNadder executable to run the IPSPEC data check for the
        variant being released.
        """
        cmdline = ['vpNadder', '-i', self.variant, '-d', 'ipspec', '--datacheck']
        logger.debug("Invoking: %s" % ' '.join(cmdline))
        (out,err) = execute(cmdline)

        logger.debug("vp stdout:\n%s" % out)
        logger.debug("vp stderr:\n%s" % err)

        return (out,err)

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
        if variant is None:
            variant=self.variant 
        if libtype is None:
            libtype=self.libtype

        ### Make 'Could not find any audit file' error UNWAIVABLE for milestones 4.5 and 5.0
        ### http://fogbugz.altera.com/default.asp?360842
        #unwaivable_milestones = ['4.5', '5.0']
        ### - UPDATED: 19 Oct 2016
        # Make error UNWAIVABLE for all milestones 
        # http://pg-rdjira:8080/browse/DI-320
        if 'Could not find any audit file' in error:
            error += ' (UNWAIVABLE)'


        clean_error = self.remove_workspace_from_filepath(error)

        failure = TestFailure(variant, libtype, topcell, flow, subflow, clean_error)
        self.tests_failed.append(failure)

        result = TestResult('fail', variant, libtype, topcell, flow, subflow, clean_error)
        self.test_results.append(result)

    def remove_workspace_from_filepath(self, str):
        """
        We can't put the workspace path in any failures
        as then waivers would never work!
        """
        return str.replace(self.workspace_root, '').replace('\n',' ').replace("'","").replace('"','')

    def log_test_failures(self, failures):
        """
        For each TestFailure in the given list, logs a failure for this run.
        This helps ensure all failures are logged as both TestFailures and
        TestResults.
        """
        for (variant, libtype, topcell, flow, subflow, error) in failures:
            self.log_test_fail(flow=flow, error=error, variant=variant, libtype=libtype, topcell=topcell, subflow=subflow)

    def get_test_results(self):
        """
        Returns the results of running the tests.  Usually 
        called after run_tests().  Returns a list of TestResult
        named tuples.
        """
        return self.test_results


    def get_required_tests(self, project, milestone, thread, variant_type):
        '''
        return get all the checkers 
            (libtype, flow, subflow, check_type, checker, owner_name, owner_email, owner_phone)
        '''
        retlist = []
        if self.prel:
            prel_filter = '^{}$'.format(self.prel)
        else:
            prel_filter = ''

        if variant_type:
            iptype_filter = '^{}$'.format(variant_type)
        else:
            iptype_filter = ''

        for d in self.ip.get_deliverables(milestone=milestone, views=self.views, roadmap=self.roadmap, prels=self.prels):
            for c in d.get_checkers(milestone=milestone, iptype_filter=iptype_filter, prel_filter=prel_filter):
                ### ipspec checkers ALWAYS need to be included,
                ### regardless of "Audit Verification" property
                if d.name == 'ipspec' or c.audit_verification:
                    retlist.append( [c.deliverable, c.flow, c.subflow, c.type, c.checkname, c.user, 'NA', 'NA'] )
        return retlist

    def get_required_libtypes(self):
        """
        Determines variant type, and queries the roadmap
        system to find out what libtypes are required
        for the given milestone, thread, and variant type.
        Returns a list of libtype name strings.
        """
        return [d.name for d in self.ip.get_deliverables(milestone=self.milestone, views=self.views, roadmap=self.roadmap, prels=self.prels)]
        

    def get_variant_type(self):
        """
        Returns the variant type for the requested variant.
        Talks to IC Manage server via abnrlib.
        """
        return self.ip.iptype

