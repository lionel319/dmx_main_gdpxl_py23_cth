#!/usr/bin/env python
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/tnrlib/audit_check.py#13 $
# $DateTime: 2023/08/15 19:36:37 $
# $Author: lionelta $

## @addtogroup tnrlib
## @{

"""
The AuditFile class supports two main modes of operation:
    1. generating audit files during a checker run
    2. validating auditing files in a workspace 

.. note: If you don't know what a "checker" is, you can see a list (including docs) on http://sw-web.altera.com/ice/tests/

The first mode supports flow creators who need to generate audit files.  These folks must read `HowToCreateAnAuditedTestFlow <https://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/HowToCreateAnAuditedTestFlow>`_ which provides more details.

The second mode supports the gated release system and quick check.

Having both modes defined in one place ensures there will be no issues due to different assumptions by flow creators or the gated release system owner.

For the first mode, this is the flow:

    #. create an instance of :py:class:`AuditFile`, indicating the IC Manage workspace root directory
    #. call `~AuditFile.set_test_info` with all required fields as defined by test docstring
    #. call `~AuditFile.add_requirement` for each file that needs to be validated during a release
       validation in this case means calculating a checksum (excluding RCS keywords)
    #. call `~AuditFile.add_result` at least once; each one is a waivable result of the flow (that is, error message)
    #. call `~AuditFile.add_data` to add additional data to be dashboarded when the audit file gets processed during a release
    #. call `~AuditFile.save` to write the audit file based on these requirements; will throw an exception if you did anything wrong
    #. optional: call `~AuditFile.run_audit` after creating an audit file to ensure validation output is as expected
       (that is, failures are reported as such, checksum validation works as expected, etc.)

In the second mode, these are the basic steps:

    #. create an instance of AuditFile
    #. call `~AuditFile.load` with the name of an existing .xml file or .f filelist
    #. call `~AuditFile.run_audit` to validate the audit file against files in the current workspace
       if this is done after `~AuditFile.load` on a filelist, each of the audit files listed
       will be audited in turn.

.. note:: It is also possible to mix these modes.  For example, one could load() an audit file, change header, requirements, or data, and then write a new audit file back out.  This is not normally done, but could be used to "fix" incorrect audit files, for example.

"""
from __future__ import print_function
# Python libs
from builtins import str
from builtins import ascii
from builtins import range
from builtins import object
from sys import exit
from argparse import ArgumentParser
from os import path, environ, getcwd, makedirs, chdir, access, W_OK
from os.path import getmtime
from calendar import timegm
from datetime import datetime, timedelta
from time import mktime
from re import compile
from hashlib import md5
from getpass import getuser
from socket import gethostname
from xml.etree import ElementTree as ET
from logging import basicConfig, getLogger, DEBUG, ERROR
from glob import glob
import re
import os
import multiprocessing
from pprint import pprint

# Altera libs
import os,sys
rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)
#from dmx.tnrlib.execute import execute
from dmx.tnrlib.splunk_log import SplunkLog
from dmx.tnrlib.test_result import TestFailure 
from dmx.utillib.version import Version
import dmx.utillib.naa
import dmx.utillib.cache
#import dmx.utillib.arcutils
import dmx.abnrlib.goldenarc_db
import dmx.utillib.utils

af_logger = getLogger(__name__)

RCS_FILTER = "\$Id.*\$|\$Header.*\$|\$Date.*\$|\$DateTime.*\$|\$Change.*\$|\$File.*\$|\$Revision.*\$|\$Author.*\$"

def ascii(ustr):
    """
    Anything that will go into XML (via ElementTree)
    needs to be ASCII, so we use this helped to ensure
    that everywhere.
    """
    return ustr.encode('ascii','xmlcharrefreplace').decode(errors='ignore')

def remove_linebreaks(string):
    "Returns a new string with \n and \r removed."
    return string.replace('\n',' ').replace('\r',' ').replace('\\',' ')

class AuditException(Exception):
    "A simple wrapper of the base Exception class for the purpose of identifying exceptions from this class."
    pass

class AuditFile(object):
    """
    In-memory representation of an audit file or filelist.
    Responsible for reading/writing such files as well as 
    providing a way to validate the audit trail by checking
    the results (pass/fail) and requirements (file checksums)
    that comprise the bulk of the audit file.

    By default (when no workspace_rootdir is provided), AuditFile
    will use :ref:`dm.ICManageWorkspace <dm:dm.ICManageWorkspace>` 
    to auto-detect the IC Manage workspace.  This enables logging of 
    the workspace name, configuration it is based on, variant it is 
    based on, and the top cells it contains.
    """
    def __init__(self, workspace_rootdir, logger=None, update_dashboard=False, web_api=None, snapshot_config='', development_mode=False, splunk_app_name='qa', exempted_varlibs=None, thread='', milestone=''):
        
        self.workarea = workspace_rootdir
        if workspace_rootdir is None:
            raise AuditException("workspace_rootdir can not be None. Please provide a valid WORKAREA path to workspace_rootdir.")
        else:
            self.workspace = None
            self.icm_configuration = 'not.a.real.configuration'
            self.workspace_name = workspace_rootdir.replace('/','_')
            if path.isdir(workspace_rootdir):
                self.ws_root = os.path.realpath(path.abspath(workspace_rootdir))
            else:
                raise AuditException("Workspace root given to AuditFile does not exist.")
            self.workspace_top = 'no.top'
            self.project = 'TestFamily' # This is what unit tests need

        self.snapshot_config = snapshot_config

        self.audit_file = None
        self.run_date = datetime.now().isoformat(' ')
        self.logger = af_logger

        ### This is Legacy (Splunk dashboard). We no longer use this.
        ### Keeping it for backward compatibility
        #self.update_dashboard = update_dashboard
        self.update_dashboard = False

        self.web_api = web_api

        self.splunk_app_name = splunk_app_name

        self.dashboard = None

        self.audit_filelist = None
        
        self.audit_filelist_raw = None

        self.development_mode = development_mode

        ### introduces this 2 new properties due to the need of goldenarc validation
        ### http://pg-rdjira.altera.com:8080/browse/DI-1300
        self.thread = thread
        self.milestone = milestone

        # http://pg-rdjira:8080/browse/DI-720
        self.arcsite = os.getenv("ARC_SITE", "")
        if not self.arcsite:
            self.logger.warning("$ARC_SITE environment variable is not defined !! This might cause problem !")

        ### exempted_varlibs = [ [variant, libtype], [variant, libtype], ...]
        self.exempted_varlibs = []
        if exempted_varlibs:
            self.exempted_varlibs = exempted_varlibs
        self.logger.debug("audit_check.__init__.exempted_varlibs: {}".format(self.exempted_varlibs))


        ### Required file that are already registered 
        self.done_reqfiles = {}

        self.no_expand_paths = ['/p/psg/flows/', '/p/psg/PDK/', '/p/hdk/cad/', '/p/psg/eda/', '/p/psg/EIP/']


        ### For Cth Release POC Exercise
        self._cthpoc = ['cthpoc', 'cthfe']

    def __str__(self):
        """
        Prints out a text representation of this audit instance.
        """
        result = ''
        audit_file_path = self.get_audit_file_path()
        variant = str(self.flow.get('variant'))
        libtype = str(self.flow.get('libtype'))
        result += "Audit Log %s for %s/%s\n" % (audit_file_path, variant, libtype)

        result += "\nEnvironment:"
        result += '\trun_date %s\n'% str(self.environment.get('run_date'))
        result += '\tmachine %s\n'% str(self.environment.get('machine'))
        result += '\topen_files %s\n'% str(self.environment.get('open_files'))
        result += '\tarc_resources %s\n'% str(self.environment.get('arc_resources'))
        result += '\tshell_arc_job_id %s\n'% str(self.environment.get('arc_job_id'))
        result += '\towner %s\n'% str(self.environment.get('user'))
        result += '\tworkspace %s\n'% str(self.environment.get('workspace'))
        result += '\tconfiguration %s\n'% str(self.environment.get('configuration'))

        result += "\nRequirements:"
        for f in self.files:
            result += "\t%s\n" % str(f.get('file_path'))

        result += "\nResults:"
        for r in self.results:
            text = str(r.get('text'))
            status = str(r.get('failure'))
            result += "\t%s - %s\n" % (status, text)

        result += "\nData:"
        for d in self.data:
            text = str(d.get('text'))
            tag = str(d.get('tag'))
            result += "\t%s: %s\n" % (tag, text)

        return result


    def convert_path_from_local_to_site(self, fullpath):
        '''
        In order for the release system to work in all sites, 
        all 
            /nfs/$ARC_SITE/...
        paths need to be converted into 
            /nfs/site/...

        http://pg-rdjira:8080/browse/DI-720
        '''
        prefix = '/nfs/{}/'.format(self.arcsite)
        if fullpath.startswith(prefix):
            fullpath = re.sub("^{}".format(prefix), '/nfs/site/', fullpath, count=1)

        return fullpath


    @staticmethod
    def detect_variant_using_cwd(ws_root):
        """
        Strips off the workspace from the front of cwd,
        and assumes the leftmost directory is the name of
        the variant.
        """
        cwd = getcwd()
        common_prefix = AuditFile.commonprefix([cwd, ws_root])
        if common_prefix != '':
            cwd_rel_to_ws_root = path.relpath(cwd, common_prefix)
            return cwd_rel_to_ws_root.split(path.sep)[0]
        else:
            raise AuditException("Cannot detemine variant using cwd: cwd not under workspace root.")

    @staticmethod
    def commonprefix(l):
        """
        Unlike the os.path.commonprefix version, this
        always returns path prefixes (not string prefixes)
        as it compares path component wise.
        See `this link <http://stackoverflow.com/questions/21498939/how-to-circumvent-the-fallacy-of-pythons-os-path-commonprefix>`_ for details.
        """
        cp = []
        ls = [p.split(path.sep) for p in l]
        ml = min( len(p) for p in ls )

        for i in range(ml):
            s = set( p[i] for p in ls )         
            if len(s) != 1:
                break

            cp.append(s.pop())

        return path.sep.join(cp)

    def generate_unique_run_id(self):
        """
        Returns a unique string identifying this audit run.
        Used to group related Splunk events.
        """
        return 'audit_api_run_for_'+self.workspace_name+'_on_'+datetime.strftime(datetime.now(),'%Y-%m-%d_%H:%M:%S.%f')

    def get_dashboard_api(self):
        """
        Provides a handle to the Splunk logging API.
        Ensures all required fields are populated.
        Must be called after `load` or `set_test_info`.
        """
        # TODO: check that the current user is the release system -- we don't want users mucking up the dashboard with audit data
        if self.dashboard is None:
            # The front-end dashboard code should use the "transaction" command to group events with the same run_id.
            run_id = self.generate_unique_run_id()

            # Now set up the main dashboard API the rest of this class uses.
            required_fields = { 
                     'run_id': run_id,
                     'project': self.project,
                     'variant': self.workspace_top,
                     'configuration': self.icm_configuration,
                     'workspace': self.workspace_name,
                     'owner': str(self.environment.get('user')),
                     'flow': str(self.flow.get('name')),
                     'subflow': str(self.flow.get('subflow')),
                     'flow-variant': str(self.flow.get('variant')), 
                     'flow-libtype': str(self.flow.get('libtype')),
                     'flow-topcell': str(self.flow.get('topcell')), 
                     'info-type': 'unspecified' # Indicates if the data is the flow result, an error detail, additional logging, etc.
                     }
            self.dashboard = SplunkLog(self.splunk_app_name, run_id, required_fields, development_mode=self.development_mode)

        return self.dashboard

    def load(self, filepath):
        """
        Parses the given file and stores the info in this class. 
        Once you load an audit filelist, you can't re-use this 
        instance for a non-filelist type AuditFile object.
        """
        if self.is_audit_filelist(filepath):
            self.audit_file = filepath
            self.audit_filelist, self.audit_filelist_raw = self.read_audit_filelist(filepath)
            #self.logger.debug("filepath: {}\naudit_filelist: {}\naudit_filelist_raw:{}".format(filepath, self.audit_filelist, self.audit_filelist_raw))
        else:
            self.audit_filelist = None
            self.audit_file = filepath

            if os.stat(filepath).st_size == 0:
                raise Exception("Empty audit XML file is not allowed. UNWAIVABLE : {}" .format(filepath))

            if not filepath.endswith('.xml'):
                raise Exception("Only audit.*.xml files are allowed in audit filelist: UNWAIVABLE : {}".format(filepath))

            with open(filepath,'r') as f:
                xml = f.read()
                self.from_xml(xml)

            ### Make all wrong formatted xml audit errors UNWAIVABLE
            try:
                if self.environment is None:
                    raise Exception("Bad audit.*.xml file format (1). UNWAIVABLE : {}".format(filepath))
                if not hasattr(self.environment, 'attrib') or 'arc_resources' not in self.environment.attrib:
                    raise Exception("Bad audit.*.xml file format (2). UNWAIVABLE : {}".format(filepath))
                
                if self.flow is None:
                    raise Exception("Bad audit.*.xml file format (3). UNWAIVABLE : {}".format(filepath))
                if not hasattr(self.flow, 'attrib') or 'topcell' not in self.flow.attrib:
                    raise Exception("Bad audit.*.xml file format (4). UNWAIVABLE : {}".format(filepath))
            except:
                raise


    @staticmethod
    def is_audit_filelist(filepath):
        """
        An audit filelist is one that ends with .f.
        If some other "\*.f" file is given (not a 
        list of audit XML files), you won't get a failure
        until you call run_audit() which tries to load the
        individual files in the filelist.
        """
        return filepath.endswith('.f')

    @staticmethod
    def get_equivalent_xml_from_filelist_path(filepath):
        """
        An audit filelist is one that ends with .f.
        And equivalent audit xml is one that ends with the same path as a filelist, 
        but with an .xml extension.
        """
        return filepath.rstrip('.f') + '.xml'


    def read_audit_filelist(self, filepath):
        """
        Reads in the audit "filelist".
        Assumes there is one file path per line.
        Lines that begin with a # are comments and ignored.
        Blank lines (or all spaces/tabs) are also ignored.
        File paths must be relative to the filelist location.
        """
        files = []
        files_raw = []
        filepath_dir = path.dirname(filepath)
        with open(filepath,'r') as filelist:
            for line in filelist.readlines():
                clean_line = line.strip(' \t\n')
                if not clean_line.startswith('#') and len(clean_line)>1:
                    files.append(path.join(filepath_dir, clean_line))
                    files_raw.append(clean_line)
        return [files, files_raw]

    def set_test_info(self, flow, subflow, run_dir, cmdline, libtype, topcell=None, variant='None', arc_job_id='', lsf_job_id='', subtest=''):
        """
        Initializes an AuditFile instance with the provided test flow info, and 
        the info gathered by the audit API.  Calling this funtion will overwrite 
        any existing data, for example from a load() or prior set_test_info().

        The arguments are the audit fields provided by a test flow:

        :param flow: (mandatory) official flow name as defined by the Roadmap web site
        :param subflow: (mandatory) official sub-flow name as defined by the Roadmap web site
        :param run_dir: (mandatory) directory where the cmdline was executed
        :param cmdline: (mandatory) the top level command used to invoke the test flow 
        :param libtype: (mandatory) the libtype related to the flow; it should be possible 
               to query ICE_MAN for this, but for now the test can specifiy it
        :param topcell: (optional) the top cell; optional if there is only one possible
        :param variant: (optional) the variant this audit relates to; if None it is auto-
               detected based on the current working directory (cwd)
        :param arc_job_id: (optional) ARC job id of the top-level test run (cmdline)
        :param lsf_job_id: (optional) LSF job id of the top-level test run (cmdline)
        :param subtest: (optional) if provided, forms part of the audit filename; used by
                test flows which have multiple auditable sub-flows which are NOT 
                known to the Roadmap web site.  These have to be referenced 
                in an audit filelist to be processed by a gated release.
        """
        if variant is None:
            variant = self.detect_variant_using_cwd(self.ws_root)

        if libtype == None or libtype == '':
            raise AuditException("Must specify top cell to audit API.  Audit log not created.")

        if topcell is None:
            dm_topcells = self.workspace.getCellNamesForIPName(variant)
            if len(dm_topcells) == 1:
                topcell = list(dm_topcells)[0]
            else:
                raise AuditException("Must specify top cell to audit API.  Audit log not created.")
        
        self.flowname = flow
        self.subflowname = subflow
        self.libtypename = libtype
        self.topcellname = topcell
        self.variantname = variant

        self.init_xml_instance()
        self.flow.set('name', ascii(flow))
        self.flow.set('subflow', ascii(subflow))
        self.flow.set('subtest', ascii(subtest))
        self.flow.set('run_dir', ascii(run_dir))
        self.flow.set('cmdline', ascii(cmdline))
        self.flow.set('variant', ascii(variant))
        self.flow.set('libtype', ascii(libtype))
        self.flow.set('topcell', ascii(topcell))
        self.flow.set('arc_job_id', ascii(arc_job_id))
        self.flow.set('lsf_job_id', ascii(lsf_job_id))
        self.flow.set('audit_log_initialized', datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S.%f'))

        self.set_automatic_info()

        self.checker_type = "c"
        try:
            self.checker_type = self.get_checker_type(libtype, flow, subflow)
        except Exception as e:
            self.logger.warning(str(e))


    def get_checker_type(self, libtype, flow, subflow):
        '''
        return 'c' if flow/subflow is a Context_check
        return 'd' if flow/subflow is a Data_check
        '''

        ### If self.thread is given, use it as the golden.
        ### else, use the $DB_THREAD environment variable as golden.
        ### This should solve both scenarios:-
        ### - when flow generating audit.xml, they will not provide the self.thread during AuditFile() initialization.
        ###   however, they should be running within a correct arc shell, thus, the $DB_THREAD env var is used.
        ### - when during TNR backend, all the AuditFile() initialization called in test_runner.py will make sure that
        ###   the correct self.thread is passed into AuditFile() during object creation.
        e = dmx.ecolib.ecosphere.EcoSphere()
        if self.thread:
            thread = self.thread
        else:
            thread = os.getenv("DB_THREAD", "")

        f = e.get_family_for_thread(thread)
        familyname = f.name
        roadmap = e.get_roadmap_for_thread(thread)
        l = f.get_deliverable(libtype, roadmap=roadmap)
        try:
            c = l.get_checkers(flow_filter='^{}$'.format(flow), subflow_filter='^{}$'.format(subflow))[0]
        except:
            raise AuditException("Flow/Subflow({}/{}) not found for family:{} libtype:{}".format(flow, subflow, familyname, libtype))
        self.logger.debug("Checker_Type for Flow/Subflow({}/{}) for Family:{} == {}".format(flow, subflow, familyname, c.type))
        return c.type


    def init_xml_instance(self):
        self.audit       = ET.Element('audit')
        self.environment = ET.SubElement(self.audit, 'environment')
        self.flow        = ET.SubElement(self.audit, 'flow')
        self.files       = ET.SubElement(self.audit, 'files')
        self.results     = ET.SubElement(self.audit, 'results')
        self.data        = ET.SubElement(self.audit, 'data')

    def set_automatic_info(self):
        """
        This funtion defines the audit fields that get set automatically
        populated.  Set when the test flow calls set_test_info().
        These are the fields and what they mean:

        :param run_date: the date the audit API was initialized
        :param user: the user running this script (and presumably the test flow)
        :param machine: the machine where this script is running
        :param shell_arc_job_id: the ARC job id of the parent shell for this script
        :param workspace: the name of the IC Manage workspace
        :param configuration: the IC Manage configuration associated with the workspace
        :param open_files: the output of 'p4 opened ...'
        :param arc_resources: fully expanded list of ARC resources in the current shell 
        """
        self.environment.set('run_date', self.run_date)
        self.environment.set('user', ascii(getuser())) 
        self.environment.set('machine', ascii(gethostname()))
        arc_job_id = environ.get('ARC_JOB_ID')
        if arc_job_id:
            self.environment.set('arc_job_id', ascii(arc_job_id))
        else:
            self.environment.set('arc_job_id', ascii('000'))

        workspace = self.get_workspace_name()
        self.environment.set('workspace', ascii(workspace))
        configuration = self.get_configuration_name()
        self.environment.set('configuration', ascii(configuration))
        #open_files = self.get_open_files()
        open_files = ''     # http://pg-rdjira:8080/browse/DI-1114
        self.environment.set('open_files', ascii(open_files))
        arc_resources = self.get_arc_resources()
        self.environment.set('arc_resources', ascii(arc_resources))

        v = Version()
        self.environment.set('dmx_version', ascii(v.dmx))
        self.environment.set('dmxdata_version', ascii(v.dmxdata))

    def get_workspace_name(self):
        if self.workspace is None:
            return "Not_a_real_workspace"
        else:
            return self.workspace.workspaceName

    def get_configuration_name(self):
        if self.workspace is None:
            return "Not_a_real_configuration"
        else:
            return self.workspace.configurationName

    def get_open_files(self):
        """
        Returns a comman-separated list of open ICMP4 files in the current client.
        Return '' if workspace is None (for faster testing).
        """
        if self.workspace is None:
            return ''
        else:
            #(out,err) = execute(['icmp4', 'opened', path.join(self.ws_root, '...')])
            exitcode, out, err = dmx.utillib.utils.run_command('icmp4 opened {}'.format(path.join(self.ws_root, '...')))
            filelist = []
            if len(err) > 0:
                if 'not opened on this client' in err[0]:
                    filelist.append("No open files")
                else:
                    self.logger.warning("Got error reading shell open files:\n%s"%err)
            for f in out:
                parts = f.split()
                filelist.append(parts[0]) # Just the file name please
            return ','.join(filelist)

    def get_arc_resources(self):
        """
        Returns a comma-separated list of resolved ARC resources in the current shell.
        Returns '' if workspace is None (for faster testing).
        """
        return "no_longer_applicable"

        #(out,err) = execute(['arc','job-info','resources'])
        exitcode, out, err = dmx.utillib.utils.run_command('arc job-info resources')
        if len(err) > 0:
            self.logger.warning("Got error reading shell ARC resource list:\n%s"%err)
        resources = out.strip()
        return resources

    def set_xml_environment(self, key, value):
        """
        For testing.
        """
        self.environment.set(key, value)

    def add_relocated_requirement(self, actual_filepath, libtype_run_dir, libtype_dir, checksum=False, filter=None, disable_rcs_filtering=False, inputfile=None, skip_revision=False):
        """
        Call this to require a file which exists in one directory during the
        run, but which may later be copied to its official IC Manage location.
        This facilitates flows which need to run from directories other than the
        official IC Manage location.  See :case:`319106`

        :param actual_filepath: a path to the file relative to the workspace root.
            If it is not relative to the workspace root, 
            but is a full path, then it will be made relative to the ws root.
            Either way, this should be the file that currently exists on disk.
        :param libtype_run_dir: the name of the directory (part of "filepath")
            that is different than the IC Manage location of this file.  Flows 
            that need to use this feature should run from a directory that parallels 
            the actual libtype directory.  For example, the "pv" libtype flows might 
            run in "pvrun"; in that case, this parameter would be set to "pvrun",
            and the next parameter, libtype_dir, will be set to "pv".  The filepath 
            parameter should be a path that includes "pvrun".
        :param libtype_dir: the name of the official IC Manage location where 
            this file is stored.  
        :param checksum: if provided, it will be used, otherwise, the checksum
            is calculated by referencing the current file on disk.
        :param filter: if provided, lines matching this regexp will be excluded
            in the contents used to calculate the checksum value .
            Regardless of the filter argument, Perforce-expanded keywords
            will be filtered prior to checksum calculation.
        :param disable_rcs_filtering: disables RCS filtering altogether
        :param inputfile: If True, sets type=input, False, type=output, otherwise
            no type field is written to the XML audit file.

        For more information, see `~AuditFile.add_requirement`.
        """
        run_dir = path.sep+libtype_run_dir+path.sep
        official_dir = path.sep+libtype_dir+path.sep
        future_filepath = path.abspath(actual_filepath).replace(run_dir, official_dir)

        self.add_requirement_helper(actual_filepath, future_filepath, checksum, filter, disable_rcs_filtering, inputfile, skip_revision=skip_revision)

    def add_requirement(self, filepath, checksum=False, filter=None, libtype_run_dir=None, libtype_dir=None, disable_rcs_filtering=False, inputfile=None, skip_revision=False):
        """
        Call this to require a file to be audited using a checksum.  
        
        :param filepath: a path to the file relative to the workspace root.
            If it is not relative to the workspace root, 
            but is a full path, then it will be made relative to the ws root.
        :param checksum: if provided, it will be used, otherwise, the checksum
            is calculated by referencing the current file on disk.
        :param filter: if provided, lines matching this regexp will be excluded
            in the contents used to calculate the checksum value.
            Regardless of the filter argument, Perforce-expanded keywords
            will be filtered prior to checksum calculation.
        :param libtype_run_dir: the name of the directory (part of "filepath")
            that is different than the IC Manage location of this file.  Flows 
            that need to use this feature should run from a directory that parallels 
            the actual libtype directory.  For example, the "pv" libtype flows might 
            run in "pvrun"; in that case, this parameter would be set to "pvrun",
            and the next parameter, libtype_dir, will be set to "pv".  The filepath 
            parameter should be a path that includes "pvrun".  If you don't need
            to use this feature, set this to None (or don't provide it).
        :param libtype_dir: the name of the official IC Manage location where 
            this file is stored.  Set this to None if not using relocation feature.
        :param disable_rcs_filtering: disables RCS filtering altogether
        :param inputfile: If True, sets type=input, False, type=output, otherwise
            no type field is written to the XML audit file.

        Perforce will be queried to detemine the current
        file revision on disk to help debug checksum failures at release time.

        :case:`249604` prevents duplicate requirements from being added
        """
        if libtype_run_dir is None:
            self.add_requirement_helper(filepath, filepath, checksum, filter, disable_rcs_filtering, inputfile, skip_revision=skip_revision)
        else:
            self.add_relocated_requirement(filepath, libtype_run_dir, libtype_dir, checksum, filter, disable_rcs_filtering, inputfile, skip_revision=skip_revision)


    def is_file_binary(self, filepath):
        '''
        return True if file is non-ascii file.
        return False if file is ascii file.

        Shamelessly copied from https://stackoverflow.com/a/7392391/335181
        '''
        textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
        return bool(open(filepath, 'rb').read(1024).translate(None, textchars))


    def add_requirement_helper(self, filepath_to_checksum, filepath_to_write_to_audit_log, checksum=False, filter=None, disable_rcs_filtering=False, inputfile=None, skip_revision=False):
        """
        Adds required files to audit log.  Users should use `~AuditFile.add_requirement`
        or `~AuditFile.add_relocated_requirement` instead of this function.
        """
        clean_filepath = self.validate_filepath(filepath_to_checksum)
        filepath_for_audit_log = self.validate_filepath(filepath_to_write_to_audit_log, check_existence=False)

        ### raise error during audit xml file generation for a data_check when an added checksum file is not within its own variant/lib
        ### https://jira.devtools.intel.com/browse/PSGDMX-1546
        if self.checker_type == 'd' and not self.in_variant_and_libtype(filepath_for_audit_log) and not filepath_for_audit_log.startswith('/'):
            raise AuditException("Flow/Subflow({}/{}) is a data_check.\n Checksuming a file({}) outside of it's own variant/libtype({}/{}) for a data_check is not allowed.".format(
                self.flowname, self.subflowname, filepath_for_audit_log, self.variantname, self.libtypename))

        if clean_filepath and clean_filepath not in self.done_reqfiles:
            self.done_reqfiles[clean_filepath] = 1
            accessible_filepath = path.join(self.ws_root, clean_filepath)
            have_revision = self.get_have_revision(accessible_filepath, skip_revision=skip_revision)
            if checksum:
                the_checksum = checksum
            else:
                ### disable rcs for binary files
                ### https://jira.devtools.intel.com/browse/PSGDMX-1556
                if self.is_file_binary(accessible_filepath):
                    filter = None
                    disable_rcs_filtering = True
                the_checksum = self.get_checksum(accessible_filepath, filter, disable_rcs_filtering)

            et_file = ET.SubElement(self.files, 'file')
            et_file.set('file_path', ascii(filepath_for_audit_log))
            et_file.set('rcs_disable', ('yes' if disable_rcs_filtering else ''))
            et_file.set('checksum', ascii(the_checksum))
            if inputfile is not None:
                et_file.set('type', ('input' if inputfile else 'output'))
            
            #This will make the generated have_revision in xml file look like b'-1' in py2 environment.
            #et_file.set('have_revision', str(have_revision))   
            et_file.set('have_revision', '{}'.format(have_revision))
            
            if filter:
                et_file.set('filter', ascii(filter)) 
            else:
                et_file.set('filter', '')

    def validate_filepath(self, filepath, check_existence=True):
        """
        Ensures the filepath exists either under the workspace rootdir,
        or is a full path on /tools.
        or is a full path on /archive. (Case 340980)
        Returrns the path relative to the workspace rootdir.
        """

        for p in self.no_expand_paths:
            if filepath.startswith(p):
                return filepath

        site_wsroot = self.convert_path_from_local_to_site(self.ws_root)

        if path.isabs(filepath):
            #fullpath = filepath
            fullpath = path.abspath(filepath) # Call abspath to remove erroneous double slashes.
        else:
            fullpath = path.abspath(path.join(self.ws_root, filepath))
      

        ### Use the realpath
        fullpath = os.path.realpath(fullpath)

        ### Make path site agnostic.
        ### http://pg-rdjira:8080/browse/DI-720
        fullpath = self.convert_path_from_local_to_site(fullpath)

        # Do we really need to check this?
        if check_existence and not path.exists( fullpath ):
            raise AuditException("Path to audited file requirement does not exist: %s" % fullpath)

        allowable_paths = [site_wsroot, '/tools', '/archive', '/nfs/site/disks/psg_pdk', '/nfs/site/disks/psg_flows', '/nfs/site/disks/psgswbuild', '/nfs/site/disks/swbld', '/nfs/site/disks/psg_eda',
            '/nfs/site/disks/psg_ext', '/nfs/site/disks/easic', '/nfs/site/disks/psg_rambus', '/nfs/site/proj/tech1/n5', '/nfs/site/disks/crt', '/nfs/site/disks/psg_silicon',
            '/nfs/site/disks/psgknl.arc.transaction', '/nfs/site/disks/psgltm.arc.transaction']

        ok = False
        for apath in allowable_paths:
            if fullpath.startswith(apath):
                ok = True
                break
        
        ### Support NAA paths   - http://pg-rdjira:8080/browse/DI-1326
        ### Support Cache paths - http://pg-rdjira:8080/browse/DI-1373
        naa = dmx.utillib.naa.NAA()
        cache = dmx.utillib.cache.Cache()
        if not ok:
            if naa.is_path_naa_path(fullpath) or cache.is_path_cache_path(fullpath):
                ok = True

        if not ok:
            #raise AuditException("Audited files ({}) is not within the following allowable paths : {}".format(fullpath, allowable_paths))
            self.add_result("Audited files ({}) is not within the following allowable paths : {} (UNWAIVABLE)".format(fullpath, allowable_paths), False)
            return ''

        if fullpath.startswith(site_wsroot):
            result = fullpath.replace(site_wsroot, '')[1:] # remove leading slash
        else:
            result = fullpath

        ### If NAA path, convert it to relative path wrt workspace root
        ### http://pg-rdjira:8080/browse/DI-1326
        ### NAA path: /nfs/site/disks/psg_naa_1/Falcon/i10socfm/liotest2/rcxt/dev/toto.1
        if naa.is_path_naa_path(fullpath):
            result = naa.get_info_from_naa_path(fullpath)['wsrelpath']

        ### If Cache path, convert it to relative path wrt workspace root
        ### http://pg-rdjira:8080/browse/DI-1373
        ### Cache path: /nfs/site/disks/fln_sion_1/cache/i10socfm/liotest1/rdf/REL5.0FM8revA0--TestSyncpoint__17ww404a/audit/audit.aib_ssm.rdf.xml
        if cache.is_path_cache_path(fullpath):
            result = cache.get_info_from_cache_path(fullpath)['wsrelpath']

        '''
        ### Disabled this section , as it breaks other r2g2 process.
        ### https://jira01.devtools.intel.com/browse/PSGDMX-1470

        ### Prevent symlink from being added as required file
        ### https://jira01.devtools.intel.com/browse/PSGDMX-1457
        if path.islink(filepath):
            ### raise error if symlink is not a symlink to NAA/Cache area
            if not naa.is_path_naa_path(fullpath) and not cache.is_path_cache_path(fullpath):
                raise AuditException("Path to audited file requirement can not be a symlink: {}".format(filepath))
            ### This part catches a symlink which is linked to a file within the workspace which is symlinked to 
            ### a NAA/Cache area.
            if not os.readlink(filepath).startswith('/'):
                raise AuditException("Path to audited file requirement can not be a (relpath) symlink: {}".format(filepath))
        '''

        return result


    def get_have_revision(self, filepath, skip_revision=False):
        """
        Returns the revision of the given file currently in the workspace
        using "icmp4 have <filepath>".
        If the file is open for add, returns 0, otherwise the revision #.
        If it cannot be determined, return -1
        """
        if skip_revision:
            return -1

        # We need to run with shell=True # because release_runner, for example, 
        # is not invoked from within an ICM workspace.
        try:
            cmd = ['_icmp4', 'have', filepath]
            #(out, err) = execute(cmd, shell=True)
            exitcode, out, err = dmx.utillib.utils.run_command('_icmp4 have {}'.format(filepath))
        except:
            out = []
            err = []

        if 'not on client' in err:
            revision = 0
        else:
            try:
                (depotpath, rev_and_localpath) = out[0].split('#') # You can't add files with '#' to Perforce 
                rev_and_rest = rev_and_localpath.split(' - ') # Separates depot with rev from localpath, but could be in a filepath
                rev = rev_and_rest[0]
                revision = int(rev)
            except:
                revision = -1

        return revision

    def add_result(self, name, passed, severity='error'):
        """
        Call this to add a Result entry to the audit log.  A Result entry
        indicates the pass or fail status of a given sub-flow.  Each
        Result will be listed in the dashboard.  Each Result in a given 
        audit file must have a unique name.  It can only have the value 
        "pass" or "fail".  The result name will be stripped of all CR/LF 
        characters and backslashes (these can cause crashes when processing 
        the strings downstream) as well as trailing spaces (these can cause
        weird issues with command-line waivers).

        :case:`249604` silently removes workspace paths from error messages
        """
        name = remove_linebreaks(name)
        name = self.remove_all_workspace_paths(name)
        name = name.rstrip()
        if not name in [str(r.get('text')) for r in self.results]:
            et_result = ET.SubElement(self.results, 'result')
            et_result.set('text', ascii(name))
            if passed:
                et_result.set('failure', 'pass')
            else:
                et_result.set('failure', 'fail')

            severity_list = ['error', 'warning', 'info']
            l_severity = severity.lower()
            if l_severity in severity_list:
                et_result.set('severity', l_severity) # TODO: parameterize
            else:
                raise AuditException("Tried to add invalid severity value({}). Valid values are {}.".format(severity, severity_list))

            ### If severity='info', force to always set failure='pass'
            ### http://pg-rdjira:8080/browse/DI-1320
            if l_severity == 'info':
                et_result.set('failure', 'pass')


    def remove_all_workspace_paths(self, name):
        """
        If the string "name" contains any paths to the current workspace,
        replace them all with a workspace-relative path.
        Return the resulting string.
        """
        ws_root_with_slash = '%s/' % self.ws_root
        return name.replace(ws_root_with_slash, '')

        
    def make_relative_to_workspace(self, filepath):
        """
        Converts the give filepath into one relative to the workspace root.
        """
        fullpath = path.abspath(path.join(self.ws_root, filepath))
        if not path.exists( fullpath ):
            self.logger.error("Path to audited file requirement does not exist: %s" % fullpath)

        if not fullpath.startswith(self.ws_root):
            self.logger.error("Logfiles must be specified relative to the workspace root: %s" % fullpath)
            
        if fullpath.startswith(self.ws_root):
            result = fullpath.replace(self.ws_root, '')[1:] # remove leading slash
        else:
            result = 'Logfile not found, consult audit logs for details.'

        return result


    def add_data(self, name, value):
        """
        Call this to add a Data entry to the audit log.  A Data entry
        is additional data to be sent to the dashboard for logging.
        Data entires do now affect the auditing process in any way.
        Each (data,value) pair in a given audit file must be unique.
        The value is a string, but can be re-interpreted (ie, as a number)
        by the dashboard code.  If that is the case, it is up to the caller
        to ensure the value is of the desired format.
        LF/CR will be stripped from names and values.
        """
        name = remove_linebreaks(name)
        value = remove_linebreaks(value)
        for d in self.data:
            if name == str(d.get('tag')) and value == str(d.get('text')):
                raise AuditException("Tried to add second Data item with same name and value as an existing entry: (%s, %s)." % (name,value))

        et_record = ET.SubElement(self.data, 'record')
        et_record.set('tag', ascii(name))
        et_record.set('text', ascii(value))

    def from_xml(self, xml):
        """
        Configures this AuditFile instance with the data contained
        in the given XML string.  Cannot be used to specify an
        audit filelist.
        Returns non-zero if the audit file could not be read.
        """
        self.audit = ET.fromstring(xml)
        if self.audit.tag != 'audit':
            self.logger.info("ERROR: Bad audit log file: does not start with <audit>")
            return 1

        # Suck the data into our own data structure
        self.environment = self.audit.find('environment')
        self.flow = self.audit.find('flow')
        self.files = self.audit.findall('files/file')
        self.results = self.audit.findall('results/result')
        self.data = self.audit.findall('data/record') # ok to not exist

        # If we are loading XML directly, this is clearly not a filelist
        self.audit_filelist = None
        
        return 0

    def to_xml(self):
        """
        Returns an XML string representation of the current
        AuditFile instance which from_xml() can load.
        """
        # For easier reading during prototyping efforts...
        # ...but this will cause unit test failures...
        #xml = parseString( ET.tostring(self.audit) )
        #return xml.toprettyxml()
        try:
            string = ET.tostring(self.audit).decode(errors='ignore')
        except UnicodeDecodeError as e:
            print("Unicode exception: %s" % e)
            print("Audit instance: %s" % self)
            raise

        return string

    def save(self, custom_dir=None):
        """
        Writes an audit file based on the current state of this object.
        The file name is: audit.<topcell>.<flow>_<subflow>.<subtest>.xml

        If subflow is '', then the _<subflow> is omitted.
        If subtest is '', then .<subtest> is omitted.
        
        This file is created in the audit folder under the current 
        working directory (must be the variant/libtype dir) unless
        the custom_dir option is given in which case the audit file
        is created in the given custom_dir.

        If the file can't be created (becuase it is not writeable),
        this method will throw an AuditException.  Before that happens,
        the audit file is written into a /tmp location so that the
        user may avoid re-running the checker flow.  For example, if 
        the user forgot to check out the audit file before running the
        audited flow, they could simply check it out after the flow
        completes, copy it over from the /tmp location, and then submit.
        """
        self.flow.set('audit_log_saved', datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S.%f'))
        self.validate_before_save()

        audit_file_path = self.get_audit_file_path(custom_dir)

        if not path.exists(audit_file_path) or (path.exists(audit_file_path) and access(audit_file_path, W_OK)):
            with open(audit_file_path,'w') as f:
                f.write(self.to_xml())
        else:
            message = "Unable to write audit file to proper location.  Is the path writeable?  Tried: %s" % audit_file_path
            tmp_path = self.audit_file_temp_path()
            if not path.exists(tmp_path) or (path.exists(tmp_path) and access(tmp_path, W_OK)):
                with open(tmp_path, 'w') as f2:
                    f2.write( self.to_xml() )
                message += "\nTo avoid data loss, wrote audit file to temp storage: %s" % tmp_path
            else:
                message += "\nSorry, unable to even write audit log to temp storage to avoid data loss: %s" % tmp_path

            raise AuditException(message)

    @staticmethod
    def get_audit_file_paths_for_testable_item(ws_root, variant, libtype, topcell, flow, subflow=''):
        """
        Identifies audit files which need to be validated based on the given criteria.
        Returns a list of audit files that match the criteria, or
        if no (top-level) audit file is found, returns an empty list.
        If an audit filelist is found for the given test, returns just the filelist;
        it does not return all the audit logs within that filelist.
        """
        found_files = []
        folder = path.join(ws_root, variant, libtype, 'audit')
        # Audit file naming convention: audit.<topcell>.<flow>_<subflow>.<subtest>.xml
        # No dots or underscores allowed in topcell, flow, subflow, or subtest names.
        # We don't match subtest files because those MUST be specified via a filelist.
        if subflow == '':
            audit_file_pattern     = r'audit\.%(topcell)s\.%(flow)s\.xml$' % locals()
            audit_filelist_pattern = r'audit\.%(topcell)s\.%(flow)s\.f$' % locals()
        else:
            audit_file_pattern     = r'audit\.%(topcell)s\.%(flow)s_%(subflow)s\.xml$' % locals()
            audit_filelist_pattern = r'audit\.%(topcell)s\.%(flow)s_%(subflow)s\.f$' % locals()

        audit_file_re = re.compile(audit_file_pattern)
        audit_filelist_re = re.compile(audit_filelist_pattern)

        all_audit_files = AuditFile.get_audit_files_in_folder(folder)

        # Filelist audit logs take precedence over plain XML audit logs
        found_filelist = False
        for f in all_audit_files:
            basename = path.basename(f)
            if audit_filelist_re.match(basename):
                found_files.append(f)
                found_filelist = True

        if not found_filelist:
            for f in all_audit_files:
                basename = path.basename(f)
                if audit_file_re.match(basename):
                    found_files.append(f)

        return found_files

    @staticmethod
    def get_audit_files_in_folder(folder):
        """
        Returns audit.* files in the given folder.
        """
        return glob(path.join(folder, 'audit.*'))

    def audit_file_temp_path(self):
        """
        Creates a properly named audit file in /tmp.
        Supports saving the audit XML if the real path is readonly.
        See :case:`209382` and also :case:`336505`
        """
        audit_file_name = self.audit_file_name()
        return self.audit_file_in_dir(audit_file_name, '/tmp/tnr_{}'.format(os.getenv("USER", "")))

    def get_audit_file_path(self, custom_dir=None):
        audit_file_name = self.audit_file_name()

        return self.audit_file_in_dir(audit_file_name, dir_prefix=None, custom_dir=custom_dir)

    def audit_file_name(self):
        """
        The file name is:
          audit.<topcell>.<flow>_<subflow>.<subtest>.xml

        If subflow is '', then the _<subflow> is omitted.
        If subtest is '', then .<subtest> is omitted.
        The full path starts with workspace root/variant/libtype/'audit'

        Of course, the flow cannot have an underscore in it,
        not can any of the names have periods in them, but
        who would do something crazy like that? ;-)
        """
        variant = str(self.flow.get('variant'))
        libtype = str(self.flow.get('libtype'))
        topcell = str(self.flow.get('topcell'))
        flow    = str(self.flow.get('name'))
        subflow = str(self.flow.get('subflow'))
        subtest = str(self.flow.get('subtest'))

        return self.get_audit_file_name(flow, subflow, topcell, subtest)

    def audit_file_in_dir(self, audit_file_name, dir_prefix=None, custom_dir=None):
        """
        Returns the full path to the audit file.
        If dir_prefix is provided, the returned path is 
        in a directory starting from dir_prefix and
        including the workspace name and all the rest.
        However, if custom_dir is provided, dir_prefix
        is ignored and the returned path is directly
        in the given custom directory.
        """
        variant = str(self.flow.get('variant'))
        libtype = str(self.flow.get('libtype'))

        if libtype in self._cthpoc:
            custom_dir = os.path.join(os.path.abspath(self.workarea), 'output', 'psgaudit')

        if custom_dir is not None:
            audit_dir = path.abspath(custom_dir)
        else:
            if dir_prefix is not None:
                # Remove the leading slash from the ws_root, itself a full path 
                audit_dir = path.join(dir_prefix, self.ws_root[1:], variant, libtype, 'audit')
            else:
                #audit_dir = path.join(self.ws_root, variant, libtype, 'audit')
                ### For CTH POC
                audit_dir = path.join(self.workarea, 'psg', variant, libtype, 'audit')

        if not path.isdir(audit_dir):
            ### Wrap in a try: loop to prevent failure when running multi-threaded
            ### http://pg-rdjira:8080/browse/DI-1432
            try: 
                makedirs(audit_dir)
            except Exception as e:
                self.logger.warning("Tried to mkdir {} but it already exist.".format(audit_dir))


        audit_file_path = path.join(audit_dir, audit_file_name)

        return audit_file_path

    @staticmethod
    def get_audit_file_name(flow, subflow, topcell, subtest):
        if subflow == '':
            if subtest == '':
                audit_file_name = 'audit.%s.%s.xml' % (topcell, flow)
            else:
                audit_file_name = 'audit.%s.%s.%s.xml' % (topcell, flow, subtest)
        else:
            if subtest == '':
                audit_file_name = 'audit.%s.%s_%s.xml' % (topcell, flow, subflow)
            else:
                audit_file_name = 'audit.%s.%s_%s.%s.xml' % (topcell, flow, subflow, subtest)

        return audit_file_name

    def validate_before_save(self):
        """
        Called prior to saving an audit file, this method ensures a
        valid audit file will be produced.  It ensures all the required
        fields are present.
        """
        assert str(self.flow.get('name')) != '', "flow name is required but was not provided."
        assert str(self.flow.get('cmdline')) != '', "cmdline is required but was not provided."
        assert str(self.flow.get('run_dir')) != '', "run_dir is required but was not provided."
        assert str(self.environment.get('run_date')) != '', "run_date is required but could not be determined."
        assert str(self.environment.get('user')) != '', "run_dir is required but could not be determined."
        assert str(self.environment.get('configuration')) != '', "configuration is required but could not be determined."
        assert str(self.environment.get('workspace')) != '', "workspace is required but could not be determined."
        assert str(self.environment.get('arc_job_id')) != '', "arc_job_id is required but could not be determined."
        assert str(self.environment.get('arc_resources')) != '', "arc_resources is required but could not be determined."
        audit_file_path = self.get_audit_file_path()
        # Removed this need. https://jira.devtools.intel.com/browse/PSGDMX-1596
        #assert len(self.results) > 0, "At least one result is required, but not found when saving %s; be sure to call add_result() before save()." % audit_file_path

    def promote_to_official(self, custom_dir):
        """
        After creating an audit file using save() using a custom_dir
        argument (to create the file in a custom directory), you
        can use this method to promote the audit log to the official 
        location.  It is just like save() except that, before saving,
        the paths of all required files added via add_requirement() 
        are updated to point from the custom directory to the workspace
        directory.  Actually, those files are already workspace-relative...
        So it isn't clear how these file paths get updated...

        See :case:`319106`

        NOT YET IMPLEMENTED
        """
        pass 

    def run_audit(self, initial_info={}, results_only=False, skip_links=False, validate_checksum=True, validate_result=True, validate_goldenarc=False, dont_validate_xml=False, foreign_checksum_only=False):
        """
        If an audit filelist was previously load()-ed, loads each
        audit xml in the list and validates each in turn.
        Files are assumed to be relative to the workspace root.
        Otherwise, runs an audit on this instance.
        Either way, load() must have already been called, or
        a valid AuditFile instance created via set_test_info().
        Returns a list of the results.

        Takes an optional info dict of key,value pairs
        to add to the Splunk dashboard when reporting results.

        This method takes an optional AuditFile class
        argument which is used to support unit tests.

        If skip_links is true (which it should be for libtype releases),
        then any required files which are links should not be checksummed
        because the links might point to something that doesn't exist
        in the release area.

        if validate_checksum=False, then it will not validate checksum.
        Any checksum errors will not be caught.

        if validate_result=False, then it will not validate result.
        Any result errors will not be caught.
        """
        results = []
        if self.audit_filelist is not None:
            # If audit file doesn't exist, we need to know these to report the error.
            variant = initial_info['variant']
            libtype = initial_info['libtype']
            topcell = initial_info['topcell']
            flow = initial_info['flow']
            subflow = initial_info['subflow']

            ### http://pg-rdjira:8080/browse/DI-1156
            ### If .f is used, the equivalent .xml file needs to be part of the content of the .f file
            ### ... if the .xml file exist
            equivalent_xml = self.get_equivalent_xml_from_filelist_path(self.audit_file)
            if os.path.isfile(equivalent_xml) and equivalent_xml not in self.audit_filelist:
                error = 'Both {} and {} exist, but .xml is not part of the content of .f. This is not allowed. (UNWAIVABLE)'.format(
                    equivalent_xml, self.audit_file)
                test_failure = TestFailure(variant, libtype, topcell, flow, subflow, error)
                results.append(test_failure)

            ### http://pg-rdjira:8080/browse/DI-1381
            ### content of audit.f filelist can be only filename of audit.xml.
            ### no path (relative nor absolute) is allowed.
            for auditfile in self.audit_filelist_raw:
                if '/' in auditfile:
                    error = 'Audit filelist ({}) should only contain filename, and not paths ({}). (UNWAIVABLE)'.format(self.audit_file, auditfile)
                    test_failure = TestFailure(variant, libtype, topcell, flow, subflow, error)
                    results.append(test_failure)

            ### https://jira01.devtools.intel.com/browse/PSGDMX-1448
            ### This is to support the capability to not run the same *.xml file more than once.
            if not dont_validate_xml:
                for auditfile in self.audit_filelist:

                    auditfile_path = path.join(self.ws_root, auditfile)
                    exists = self.check_file_exists(auditfile_path)

                    if exists:
                        audit = self.__class__(self.ws_root, self.logger, self.update_dashboard, self.web_api, self.snapshot_config, self.development_mode, self.splunk_app_name, exempted_varlibs=self.exempted_varlibs, thread=self.thread, milestone=self.milestone)
                        audit.load(auditfile_path)
                        results += audit.run_single_file_audit(initial_info, results_only, skip_links, validate_checksum=validate_checksum, validate_result=validate_result, validate_goldenarc=validate_goldenarc,
                            foreign_checksum_only=foreign_checksum_only) 
                    else:
                        error = 'Could not read audit xml %s referenced by audit filelist %s'%(auditfile, self.audit_file)
                        test_failure = TestFailure(variant, libtype, topcell, flow, subflow, error)
                        results.append(test_failure)
        else:
            results += self.run_single_file_audit(initial_info, results_only, skip_links, validate_checksum=validate_checksum, validate_result=validate_result, validate_goldenarc=validate_goldenarc,
                foreign_checksum_only=foreign_checksum_only)

        return results

    def get_filelist_audit_files(self):
        """
        You must call load() or from_xml() before you can call this.
        Returns the list of audit files in a filelist, including all
        the files inside those files if they are also filelists, all
        the way down until all the audit XML files have been identified.
        Does NOT return this audit file's path, however.
        This is to support verifying no required audit logs are checked
        out during quick check (:case:`287314`).
        """
        audit_files = []

        if self.audit_filelist is not None:
            for audit_file in self.audit_filelist:
                audit_files.append(audit_file)
                auditfile_path = path.join(self.ws_root, audit_file)
                exists = self.check_file_exists(auditfile_path)

                if exists:
                    audit = self.__class__(self.ws_root, self.logger, self.update_dashboard, self.web_api, self.snapshot_config, self.development_mode, self.splunk_app_name, thread=self.thread, milestone=self.milestone)
                    audit.load(auditfile_path)
                    audit_files += audit.get_filelist_audit_files()
        else:
            audit_files += self.get_audit_file_path()

        return audit_files

    def get_required_files(self, generate_reqfiles_info=False):
        """
        You must call load() or from_xml() before you can call this.
        Returns a list of workspace-relative paths to required files 
        in this audit file, or, if this audit file is an audit filelist, 
        returns the concatenated list of all the required files
        from all the sub-audits files referenced in the 
        filelist.  This method was added to support selective
        syncing of files during official release/audit validation.

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
        required_files = []
        reqfiles_info = {}

        if self.audit_filelist is not None:
            for auditfile in self.audit_filelist:
                self.logger.debug("Processing audit file from filelist: %s" % auditfile)
                auditfile_path = path.join(self.ws_root, auditfile)
                exists = self.check_file_exists(auditfile_path)

                if exists:
                    audit = self.__class__(self.ws_root, self.logger, self.update_dashboard, self.web_api, self.snapshot_config, self.development_mode, self.splunk_app_name, thread=self.thread, milestone=self.milestone)
                    audit.load(auditfile_path)
                    if not generate_reqfiles_info:
                        required_files += audit.get_required_files()
                    else:
                        tmp = audit.get_required_files(generate_reqfiles_info=generate_reqfiles_info)
                        required_files += tmp[0]
                        reqfiles_info.update(tmp[1])
        else:
            required_files += [str(req_file.get('file_path')) for req_file in self.files]
            if generate_reqfiles_info:
                afile = self.remove_workspace_from_filepath(self.audit_file)
                reqfiles_info[afile] = {'varlib': self.get_varlib(afile), 'reqfiles': {}}
                for req_file in self.files:
                    reqfiles_info[afile]['reqfiles'][str(req_file.get('file_path'))] = {
                        'varlib': self.get_varlib(str(req_file.get('file_path'))),
                        'filter': str(req_file.get('filter')),
                        'rcs_disable': str(req_file.get('rcs_disable')),
                        'checksum': str(req_file.get('checksum'))
                    }

        if not generate_reqfiles_info:
            return required_files
        else:
            return [required_files, reqfiles_info]


    def check_file_exists(self, filepath):
        io_error = False
        try:
            with open(filepath,'r') as f:
                abyte = f.read(1)
        except:
            io_error = True
            clean_filepath = self.remove_workspace_from_filepath(filepath)
            error = 'Could not read audit xml %s referenced by audit filelist %s'%(clean_filepath, self.audit_file)
            self.logger.debug(error)

        return not io_error

    def run_single_file_audit(self, initial_info, results_only=False, skip_links=False, validate_checksum=True, validate_result=True, validate_goldenarc=False, foreign_checksum_only=False):
        """
        Processes the single audit file represented by this class instance.

        :param initial_info: is a dict of additional info for the dashboard
        :param results_only: defaults to False.  When True, checksum checks
            for files outside the variant are ignored (libtype release flow)
        :param validate_checksum: if False, then it will not validate checksum. 
            Any checksum errors will not be caught.
        :param validate_result: if False, then it will not validate result. 
            Any result errors will not be caught.
        
        :return: the list of results (each file requirement and result)
        """
        results = []

        ### http://pg-rdjira:8080/browse/DI-1111
        if validate_checksum:
            results += self.validate_checksum_requirements(initial_info, results_only, skip_links, foreign_checksum_only=foreign_checksum_only)
        if validate_result:
            results += self.validate_result_requirements(initial_info)
        if validate_goldenarc:
            results += self.validate_goldenarc_requirements(initial_info)

        return results

    def make_test_failure(self, error):
        """
        :param error: The error message being logged.
        :return: a `~test_result.TestFailure` named tuple
        """
        variant = self.flow.get('variant')
        libtype = self.flow.get('libtype')
        topcell = self.flow.get('topcell')
        flow    = self.flow.get('name')
        subflow = self.flow.get('subflow')

        clean_error = self.remove_workspace_from_filepath(error)
        
        return TestFailure(variant, libtype, topcell, flow, subflow, clean_error)

    def remove_workspace_from_filepath(self, str):
        """
        We can't put the workspace path in any failures
        as then waivers would never work!

        The Splunk logging class also strips newlines and 
        single-quotes so we do that here too.

        This whole thing is going to go away soon
        as audit validation should not be done here
        in AuditFile, but rather in TestRunner.

        Although we still need to ensure the quotes 
        and newlines get stripped in both places...
        the clean function should be a public helper 
        exported by SplunkLog...
        """
        return str.replace(self.ws_root, '').replace('\n',' ').replace("'","").replace('"','')

    def get_checksum(self, accessible_filepath, filter, rcs_disable):
        return get_checksum(accessible_filepath, filter, rcs_disable)

    def validation_fails(self, checkfile, filter, rcs_disable, required_sum):
        """
        Returns None if validation is successful, otherwise returns the calculated
        checksum.

        If there is no user filter, it does a simple md5 sum
        If that matches, then validation passed (return False).

        Otherwise, it then does a checksum using the filters (including
        RCS filtering).
        """
        if not filter:
            unfiltered_sum = self.md5sum(checkfile)
            if unfiltered_sum == required_sum:
                return None

        sum = self.get_checksum(checkfile, filter, rcs_disable)
        if sum != required_sum:
            return sum
        else:
            return None

    def validate_checksum_requirements(self, initial_info, in_variant_only=False, skip_links=False, foreign_checksum_only=False):
        """
        For each file checksum requirement, calculate the checksum
        of the file in our workspace and ensure it matches.
        If there are any filters defined for the file, be sure
        those are applied before calculating the checksum.
        Returns a list of results (actually, failures only).

        :param initial_info: dict of key/values for Splunk
        :param in_variant_only: defaults to False.  If True, 
            only files in the current variant will be checked.
        """
        results = []

        files_to_get_checksum = []
        naa = dmx.utillib.naa.NAA()
        for req_file in self.files:
            if (in_variant_only and self.in_variant_and_libtype(rstr(eq_file.get('file_path')))) or \
                (foreign_checksum_only and not self.in_variant_and_libtype(str(req_file.get('file_path')))) or \
                (not in_variant_only and not foreign_checksum_only):
                checkfile    = path.join(self.ws_root, str(req_file.get('file_path')))
                required_sum = str(req_file.get('checksum'))
                rcs_disable = str(req_file.get('rcs_disable', False))
                filter       = str(req_file.get('filter'))
                audit_revision = str(req_file.get('have_revision'))

                message = ''

                ### http://pg-rdjira:8080/browse/DI-330
                ### skip validating files from exempted_varlibs.
                self.logger.debug("audit_check.exempted_varlibs: {}".format(self.exempted_varlibs))
                checkfile_variant = ''
                checkfile_libtype = ''
                splitted_file_path = str(req_file.get('file_path')).strip('/').split('/')
                if len(splitted_file_path) > 1:
                    checkfile_variant, checkfile_libtype = splitted_file_path[:2]
                if [checkfile_variant, checkfile_libtype] in self.exempted_varlibs or ['*', checkfile_libtype] in self.exempted_varlibs:
                    message = "SKIPPED validation of %s: Checksum exempted for file %s" % (self.audit_file, checkfile)
                    self.logger.debug(message)

                else:
                    try:
                        if path.islink(checkfile) and skip_links:
                            continue

                        cache = dmx.utillib.cache.Cache()
                        if path.islink(checkfile) and not naa.is_path_naa_path(checkfile) and not cache.is_path_cache_path(checkfile) and not self.is_path_in_no_expand_paths(checkfile):
                            message = 'FAILED validation of {}: checksum file ({}) is not allowed to be a symlink.'.format(self.audit_file, checkfile)
                            results.append(self.make_test_failure(message))
                            self.logger.debug(message)
                            continue

                        ### Gather all the files that need to run checksum in a list first.
                        ### We will get the checksums of those filelists later, in parallel,
                        ### then only we do the validation.
                        files_to_get_checksum.append([checkfile, filter, rcs_disable, required_sum, audit_revision])

                    except (OSError,IOError) as e:
                        message = "FAILED validation of %s: checksum for %s failed: can not access file" % (self.audit_file, checkfile)
                        results.append(self.make_test_failure(message))
                        self.logger.debug(message)


        pool_results = {}
        pool = multiprocessing.Pool(processes=10, maxtasksperchild=1)
        for (checkfile, filter, rcs_disable, required_sum, audit_revision) in files_to_get_checksum:
            pool_results[checkfile] = pool.apply_async(get_checksum, args=(checkfile, filter, rcs_disable,))
        pool.close()
        pool.join()

        for (checkfile, filter, rcs_disable, required_sum, audit_revision) in files_to_get_checksum:
            sum = pool_results[checkfile].get()
            if sum == -1:
                message = "FAILED validation of %s: checksum for %s failed: can not access file" % (self.audit_file, checkfile)
                results.append(self.make_test_failure(message))
                self.logger.debug(message)
            elif sum != required_sum:
                message = "FAILED validation of %s: checksum for file %s (%s) does not match audit requirement (%s)." % (self.audit_file, checkfile, sum, required_sum)
                if audit_revision == '-1':
                    audit_revision = 'unknown'
                release_revision = self.get_have_revision(checkfile)
                if release_revision == -1:
                    release_revision = 'unknown'
                else:
                    release_revision = str(release_revision)
                message += "Revision #%s of the file was used during checking, but an attempt was made to release revision #%s." % (audit_revision, release_revision)
                results.append(self.make_test_failure(message))
                self.logger.debug(message)
            else:
                message = "PASSED validation of %s: checksum match for file %s" % (self.audit_file, checkfile)
                self.logger.debug(message)

        return results

    def is_path_in_no_expand_paths(self, fullpath):
        if fullpath.startswith(tuple(self.no_expand_paths)):
            return True
        return False

    def in_variant_and_libtype(self, ws_relative_path):
        """
        :param ws_relative_path: a workspace-relative path
        :return: True if the given path is under this audit 
            file's variant and libtype, False otherwise.
        """
        # The first component of the ws-relative path is the variant
        (first_component, second_component) = self.get_varlib(ws_relative_path)
        variant = str(self.flow.get('variant'))
        libtype = str(self.flow.get('libtype'))
        return (first_component == variant) and (second_component == libtype)

    def get_varlib(self, ws_relative_path):
        '''
        returns the [variant,libtype] from a given ws_relative_path
        '''
        ### Remove first '/' character
        if ws_relative_path.startswith('/'):
            ws_relative_path = ws_relative_path[1:]

        return ws_relative_path.split(path.sep)[0:2]


    def validate_result_requirements(self, initial_info):
        """
        If there are any 'fail' Results in the audit file, then the audit
        fails.
        Returns a list of failures.
        """
        failures = []
        all_passed = True

        for result in self.results:
            if str(result.get('type')) == 'logfile':
                name = str(result.get('name'))
                path = str(result.get('path'))
                info = dict(initial_info) 
                info['info-type'] = 'audit-result'
                info['status'] = 'pass'
                info['error'] = name
                info['logfile'] = path
                self.dashboard.log(info)
            else:
                passed = True

                flow = str(self.flow.get('name'))
                subflow = str(self.flow.get('subflow'))
                error = self.remove_workspace_from_filepath(str(result.get('text')))
                
                if not str(result.get('failure')) == 'pass' and str(result.get('severity')) == 'error':
                    passed = False

                    message = "FAILED validation of %s: test results indicated failure: %s" % (self.audit_file, error)
                    failures.append(self.make_test_failure(message))
                    self.logger.debug(message)
                    passed = False
                    all_passed = False

        return failures

    
    def validate_goldenarc_requirements(self, initial_info):
        """
        """
        if not self.thread or not self.milestone:
            raise AuditException("goldenarc validation can not proceed because thread/milestone property is not provided to AuditFile().")


        failures = []
        status = 'pass'
        flow = str(self.flow.get('name'))
        subflow = str(self.flow.get('subflow'))
        arc = str(self.environment.get('arc_resources'))

        #arcutils = dmx.utillib.arcutils.ArcUtils()
        goldenarc = dmx.abnrlib.goldenarc_db.GoldenarcDb(usejson=True)

        arcres_tobe_checked = goldenarc.get_tools_by_checker(self.thread, self.milestone, flow, subflow)
        self.logger.debug("arcres_tobe_checked: {}".format(arcres_tobe_checked))
        if not arcres_tobe_checked:
            message = 'FAILED validation of {}: goldenarc is not defined for checker(flow:{}, subflow:{}) in {}/{}. UNWAIVABLE.'.format(self.audit_file, flow, subflow, self.milestone, self.thread)
            failures.append(self.make_test_failure(message))
            self.logger.debug(message)
            status = 'fail'
                

        elif 'skipgoldenarc' in arcres_tobe_checked:
            message = "SKIPPED validation of {}: arc resource used for flow:subflow({}:{}) is {}.".format(self.audit_file, flow, subflow, 'skipgoldenarc')
            self.logger.debug(message)
            status = 'pass'


        else:
            #resarc = arcutils.get_resolved_list_from_resources(arc)
            resarc = 'not_applicable_in_cth'
            self.logger.debug("resarc:{}".format(resarc))
            for arcres in arcres_tobe_checked:
                if arcres not in resarc:
                    message = 'FAILED validation of {}: goldenarc tobe checked ({}) is not found in the arc resource in audit file ({}). UNWAIVABLE.'.format(self.audit_file, arcres, arc)
                    failures.append(self.make_test_failure(message))
                    self.logger.debug(message)
                    status = 'fail'
                elif not goldenarc.is_goldenarc_exist(self.thread, self.milestone, flow, subflow, arcres, resarc[arcres]):
                    goldenvers = goldenarc.get_tool_versions(self.thread, self.milestone, flow, subflow, arcres)
                    message = 'FAILED validation of {}: arc resource in audit file is {}{}, which does not meet {}/{} goldenarc:{}. UNWAIVABLE'.format(self.audit_file, arcres, resarc[arcres], self.milestone, self.thread, goldenvers)
                    failures.append(self.make_test_failure(message))
                    self.logger.debug(message)
                    status = 'fail'
                else:
                    message = "PASSED validation of {}: arc resource used for flow:subflow({}:{}) is {}{}.".format(self.audit_file, flow, subflow, arcres, resarc[arcres])
                    self.logger.debug(message)
                    status = 'pass'


        return failures


    @staticmethod
    def md5sum(filename, blocksize=65536):
        return md5sum(filename, blocksize)

    @staticmethod
    def md5sum_with_filtering(filename, remove_regexp, blocksize=65536):
        return md5sum_with_filtering(filename, remove_regexp, blocksize)

##############################################################
##############################################################
##############################################################

def md5sum(filename, blocksize=65536):
    hash = md5()
    with open(filename, 'rb') as f:
        while True:
            block = f.read(blocksize)
            if block:
                hash.update(block)
            else:
                break
    return hash.hexdigest()


def md5sum_with_filtering(filename, remove_regexp, blocksize=65536):
    regexp = compile(remove_regexp)
    hash = md5()

    ### https://stackoverflow.com/a/36490019/335181
    ### https://jira.devtools.intel.com/browse/PSGDMX-3582
    with open(filename, 'r', newline='') as f:
        for line in f: 
            if not regexp.search(line):
                if sys.version_info[0] > 2:
                    hash.update(line.encode())
                else:
                    hash.update(line)
    return hash.hexdigest()
   

def get_checksum(accessible_filepath, filter, rcs_disable):
    try:
        if rcs_disable and not filter:
            the_checksum = md5sum(accessible_filepath)
        else:
            if filter:
                if rcs_disable:
                    md5_filter = filter
                else:
                    md5_filter = '(?:%s)|(?:%s)' % (filter, RCS_FILTER)
            else:
                md5_filter = RCS_FILTER

            the_checksum = md5sum_with_filtering(accessible_filepath, md5_filter)
        return the_checksum
    except Exception as e:
        #return e   # for debugging
        return -1

def sample_run():
    """
    Prototype runner.
    Expects to be run from the rtl folder (testws/ar_lib/rtl)
    """
    # Exercise the audit process given an audit file (flow #2)
    audit = AuditFile('../..')
    audit.load('../../../audit_sample.xml')
    audit.run_audit()

    # Exercise the creation of an audit file (flow #1)
    new_audit = AuditFile('../..')
    # Cheating a bit: use the info from the sample audit file
    new_audit.set_test_info(audit.flow.get('name'), audit.flow.get('subflow'), audit.flow.get('run_dir'), audit.flow.get('cmdline'))

    new_audit.add_requirement('ar_lib/rtl/input2.v', 'd41d8cd98f00b204e9800998ecf8427e') 
    new_audit.add_requirement('ar_lib/rtl/input3.v', 'b322f3450d3877cbc82d008add7130ee', 'Run date:.*') 

    new_audit.add_result('main',True)
    new_audit.add_result('sub test abc',True)
    new_audit.add_result('error 57',False)

    new_audit.add_data('sample','1.23')
    new_audit.add_data('sample2','xyz') 

    new_audit.save()

    # Ensure we can still audit the files based on the newly created audit file (flow #2)
    check_audit = AuditFile('../..')
    check_audit.load('audit/audit.lint.xml')
    check_audit.run_audit()

def parse_cmdline():
    parser = ArgumentParser(description='Audit file generator.  Called by test flows, this program creates an audit log that indicates the detail of the test, results, and files to be validated during a gated release.  This program can also be used to validate an existing audit file (with the -v option).')

    parser.add_argument('-n', '--name', help='name of test flow (flow+subflow must be defined on http://sw-web/ice/roadmap)')
    parser.add_argument('-s', '--subflow', default='', help='test sub-flow name (flow+subflow must be defined on http://sw-web/ice/roadmap)')
    parser.add_argument('-d', '--dir', help='folder where the top level test flow command was run')
    parser.add_argument('-c', '--cmdline', help='the top level test flow command line')
    parser.add_argument('-a', '--arc_job_id', default=None, help='the ARC job id of the top level test flow command')
    parser.add_argument('-l', '--lsf_job_id', default=None, help='the LSF job id of the top level test flow command')

    parser.add_argument('-r', '--requirement', nargs='+', help='path to file that should be audited')
    parser.add_argument('-f', '--filelist', help='file listing paths to files which should be audited')

    parser.add_argument('-v', '--validate', nargs='+', help='paths to audit files to validate (using -v ignores all other args)')

    parser.add_argument('-p', '--prototype', default=False, action='store_true', help='run the prototype; must be run from testws folder')

    args = parser.parse_args()

    return args

def main():
    """
    Supports generation of audit files from the command-line.
    """
    args = parse_cmdline()
    if args.prototype:
        sample_run()
    else:
        if args.validate:
            basicConfig(level=DEBUG)
            for filepath in args.validate:
                audit = AuditFile(update_dashboard=False)
                audit.load(filepath)
                results = audit.run_audit()
        else:
            audit = AuditFile(update_dashboard=False)
            audit.set_test_info(args.flow, args.subflow, args.run_dir, args.cmdline, args.arc_job_id, args.lsf_job_id)

    return 0

## @}

if __name__ == '__main__':
    exit(main())

