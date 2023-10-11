#!/usr/bin/env python
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/tnrlib/release_runner.py#4 $
# $DateTime: 2023/03/14 20:54:44 $
# $Author: lionelta $
"""
This program processes release requests.
It is invoked by `release_queue_watcher` which is 
invoked via sj-ice-cron2 under the icetnr account.
`release_queue_watcher` ensures it runs continuously.

Release_runner is expected to run in an ARC shell 
that includes a project/nadder (or other) project bundle.

The main loop polls the release queue at regular 
intervals for new release requests.  When it sees
one, it creates and populates a workspace and 
runs the appropriate tests based on the request
details.  As tests run, results are logged to 
the Splunk dashboard.  When all test have completed, 
waivers are applied to the results, and if all
tests pass or all failures are waived, then the
given snapshot configuration is promoted to REL.
"""
from __future__ import print_function
from builtins import chr
from builtins import str
from builtins import object
from os import environ
from argparse import ArgumentParser
from datetime import datetime, timedelta
from sys import stdout, stderr, exc_info, exit
from os import chdir, path
from logging import basicConfig, getLogger, FileHandler, StreamHandler, Formatter, Filter, DEBUG, INFO, ERROR
from collections import namedtuple
from traceback import format_exception
import time
import socket
import re

# Altera libs
import os,sys
rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)

from dmx.utillib.utils import get_tools_path, is_pice_env
from dmx.tnrlib.execute import execute
from dmx.tnrlib.servers import Servers
from dmx.tnrlib.tnr_dashboard import TNRDashboardForRelease
from dmx.tnrlib.waivers import Waivers
from dmx.tnrlib.waiver_file import WaiverFile
import dmx.tnrlib.test_runner
from dmx.tnrlib.test_result import TestFailure
from dmx.tnrlib.qa_logger import SingleLevelFilter

from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.utillib.utils import run_as_user

from dmx.dmlib.ICManageConfiguration import ICManageConfiguration
import dmx.utillib.intel_dates as intel_dates

from dmx.utillib.utils import run_command, get_class_filepath
from dmx.utillib.version import Version
from dmx.abnrlib.config_naming_scheme import ConfigNamingScheme

import dmx.ecolib.ecosphere
import dmx.utillib.releaselog
import dmx.abnrlib.workspace
import dmx.abnrlib.flows.workspace
import dmx.utillib.arcutils

import sys

import os
import glob
import re


MAX_UNWAIVED_FAILURES=1000


def now():
    """
    Returns a string containing the current date and time joined by an underscore.
    """
    return datetime.strftime(datetime.now(),'%Y-%m-%d_%H:%M:%S')


class ReleaseRunner(object):
    """
    Configure ReleaseRunner with the appropriate servers and modes.

    :param queue_mgr: a ReleaseWorkQueue: the source for release requests
    :param notification_queue_mgr: a NotificationQueue: the channel for the back-end release runner to communicate release results back to abnr
    :param web_api: a WebAPI: the source of test, roadmap and waiver info 
    :param logger: a Python logger
    :param development_mode: is passed along to the audit and splunk APIs to prevent writing to production areas of Splunk
    :param logfile: a file to receive the Python log messages
    :param logger_file_handler: a Python logger handler for files (its presence will force flushing the logs before copying them to Splunk)
    :param arc_job_id: a ARC job id of this release_runner used to generating links to the logs on the ARC dashboard
    :param work_dir: the appropriate filesystem location for generating the workspace
    """
    def __init__(self, args, logger=None, logfile=None, logger_file_handler=None, arc_job_id=0):
        """
        See above.
        """
        self.request = args
        self.request.snapshot_config = self.request.configuration
        self.request.config = self.request.configuration
        self.request.timestamp = datetime.strftime(datetime.now(),'%Y-%m-%d_%H:%M:%S.%f')
        self.request.abnr_version = '9.9.9'

        self.web_api = None
        self.workspace = None
        self.workspace_path = None
        self.work_directory = args.work_dir

        if logger is None:
            self.logger = getLogger(__name__)
            self.logger_file_handler = None

            self.enable_logging()
           
            self.logfile = None
        else:
            self.logger = logger
            if logfile is not None:
                self.logfile = path.abspath(logfile)
            else:
                self.logfile = None
            self.logger_file_handler = logger_file_handler

        self.arc_job_id = arc_job_id
        self.rerun_config = None
        self.ipspec_config = None
        self.tnr_dashboard = None

        self.logger.info("Initialized ReleaseRunner")


    def handle_request(self):
        """
        Given a ReleaseRequest instance, run the tests,
        apply waivers, promote to REL if pass.
        Returns the failures.
        """
        self.start_time = int(time.time())
        failures = []
        message_to_abnr = ''
        rel_config = None
        self.rel_config = 'NA'
        request = self.request

        self.rel_config_name = ''

        ### print the version of dmx/dmxdata used
        self.versionobj = Version()
        self.logger.debug("Version.__file__:{}".format(get_class_filepath(Version)))
        self.logger.debug("dmx version     : {}".format(self.versionobj.dmx))
        self.logger.debug("dmxdata version : {}".format(self.versionobj.dmxdata))
        self.logger.debug("hostname        : {}".format(socket.gethostname()))
        self.logger.debug("fqdn            : {}".format(socket.getfqdn()))

        groups = run_command('groups')
        self.logger.debug("groups          : {}".format(groups))

        self.prepare_to_handle_request(request)
        self.tnr_dashboard = TNRDashboardForRelease('qa', self.arc_job_id, self.rerun_config, self.ipspec_config, request, self.request.devmode)
        self.tnr_dashboard.log_new_status({}, 'Start handling request')

        suppress_final_message = False
        waivers_applied = False
        try:
                
            message_to_abnr = 'Creating workspace'
            self.tnr_dashboard.log_new_status({}, 'Creating workspace')
            self.logger.info("Creating workspace")
            size = self.create_workspace()
            self.tnr_dashboard.log_new_status({'workspace_rootdir': self.workspace_path, 'workspace_size': size}, 'Created workspace')

            ### For more info:- 
            ### https://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/NewTnrWaiverProposal
            self.logger.info("Loading in available waiver files ...")
            request.waivers = WaiverFile()
            request.waivers.autoload_tnr_waivers(self.workspace_path, self.request.variant, self.request.libtype)
            request.waivers.autoload_hsdes_waivers(request.thread, request.variant, request.milestone)

            self.tnr_dashboard.log_new_status({}, 'Running tests')
            message_to_abnr = 'Running tests'
            (failures,results) = self.run_tests() 
            
            ''' Comment out this until Golden Arc Check is ready
            ### goldenarc check
            gc = dmx.tnrlib.goldenarc_check.GoldenArcCheck(request.project, request.variant, request.libtype, request.config, self.workspace_path, request.milestone, request.thread, views=request.views, prel=request.prel, prod=True)
            gc.run_test()
            self.logger.info("gc result:{}".format(gc.result))
            gcerrors = gc.report(printout=False)
            failures += gcerrors
            '''
            

            self.tnr_dashboard.log_new_status({}, 'Applying waivers')
            message_to_abnr = 'Applying waivers'

            got_to_waiver_application = True
            self.rlogresults = []    ### Results for ReleaseLog.
            self._waived_count = 0
            self._unwaived_count = 0
            self._errors_count = 0
            self._unwaived_errors = []
            self.all_tests_passed_or_waived = True

            waivers_applied = self.apply_waivers(failures, request.waivers)
            if not waivers_applied:
                # Release was aborted
                suppress_final_message = True
            else:

                ### Submit turnin for cthfe libtype
                if self.all_pass_or_waived() and self.request.libtype and self.request.libtype == 'cthfe':
                    ### sync evertyhing out, as all the files need to be transfered to the git repo
                    cmd = "xlp4 sync -f '{}/{}/...'".format(self.request.variant, self.request.libtype)
                    self.logger.info("Special Sync everything for git libtype\n- cmd: {}".format(cmd))
                    exitcode, stdout, stderr = run_command(cmd)
                    self.logger.debug('stdout:{}'.format(stdout))
                    self.logger.debug('stderr:{}'.format(stderr))

                    import dmx.utillib.gkutils
                    gk = dmx.utillib.gkutils.GkUtils()
                    rel_config_name = self.get_rel_config_name(request.project, request.variant, request.libtype, request.milestone, request.thread, self.request.label, self.request.views, self.request.skipmscheck, prel=self.request.prel)
                    retcode, retmsg = gk.run_turnin_from_icm_workspace(self.workspace_path, request.project, request.variant, request.libtype, request.thread, request.milestone, mock=False, tag=rel_config_name)
                    if retcode:
                        # turnin failed.
                        retmsg += ' (UNWAIVABLE)'
                        result = TestFailure(request.variant, request.libtype, 'NA', 'turnin', '', retmsg)
                        self.apply_waivers([result], request.waivers)

                if self.all_pass_or_waived():
                    self.tnr_dashboard.write_passed_and_skipped_tests(results)
                    self.tnr_dashboard.log_new_status({}, 'Generating REL configuration')
                    message_to_abnr = 'Generating REL configuration'
                    rel_config = self.make_rel_config()
                    self.rel_config = rel_config
                else:
                    import dmx.abnrlib.flows.workspace
                    ### Generate tnrerror.csv files. https://jira.devtools.intel.com/browse/PSGDMX-2162
                    ws = dmx.abnrlib.flows.workspace.Workspace()
                    ws.create_tnrerror_csv(self._unwaived_errors, wsroot=self.workspace_path)
                
        

        except Exception as e:
            the_error = 'Exception handling request\n%s' % '\n'.join(format_exception(*exc_info()))
            self.tnr_dashboard.log_new_status({}, the_error)
            self.logger.error(the_error)
            message = 'While %s, got an %s' % (message_to_abnr, the_error)
            self.send_completion_notification(False, message, rel_config)
            raise



        ### Include waived_count, unwaived_count, errors_count properties
        ### https://jira01.devtools.intel.com/browse/PSGDMX-24
        extrainfo = {'waived_count': self._waived_count, 'unwaived_count': self._unwaived_count, 'errors_count': self._errors_count, 'elkrelconfig': str(rel_config)}
        self.tnr_dashboard.log_new_status(extrainfo, 'ELK header record')

        if not suppress_final_message:
            self.tnr_dashboard.log_new_status({}, 'Finished handling request')
            message_to_abnr = 'Finished handling request'

        # Let abnr know we completed successfully
        self.send_completion_notification(True, message_to_abnr, rel_config)

        # We have to disable and then enable logging to ensure the logfile exists.
        if self.logger_file_handler is not None:
            self.disable_logging()
            self.tnr_dashboard.write_logfile(self.logfile)
            self.enable_logging()


        ### Write new format of releaselog (for desplunk exercise)
        ### http://pg-rdjira:8080/browse/DI-1372
        self.end_time = int(time.time())
        self.create_new_release_log()

        
        ### Get Resource Usage
        ### This has to be the VERY LAST JOB, as this self job needs to be fully completed by lsf before
        ### it pumps out all the usage data.
        ### https://jira.devtools.intel.com/browse/PSGDMX-1604
        try:
            cmd = "arc submit -- 'get_release_resource_usage.py --logfile {} --project {} --variant {} --libtype {} --milestone {} --thread {} --debug --delay 120 ' ".format(
                os.path.join(os.getenv("ARC_JOB_STORAGE"), 'stdout.txt'), request.project, request.variant, request.libtype, request.milestone, request.thread)
            os.system(cmd)
        except Exception as e:
            self.logger.error("Failed to run get_release_resource_usage.py.")
            self.logger.error(str(e))

        return failures


    def create_new_release_log(self):
        release_id = self.request.release_id
        filename = '{}.json'.format(release_id)
        if self.request.devmode:
            filepath = '/tmp/{}'.format(filename)
        else:
            filepath = '/nfs/site/disks/fln_tnr_1/tnr/release_logs/{}'.format(filename)

        project = self.request.project
        variant = self.request.variant
        if self.request.libtype == '' or self.request.libtype == None:
            libtype = 'None'
        else:
            libtype = self.request.libtype
        config = self.request.configuration
        releaser = self.request.user
        curdatetime = datetime.now().isoformat()
        arcjobid = os.environ['ARC_JOB_ID']
        rel_config = self.rel_config
        milestone = self.request.milestone
        thread = self.request.thread
        description = self.request.description
        runtime = self.end_time - self.start_time
        arc_browse_host = os.environ['ARC_BROWSE_HOST']
        arcjob_path = "https://{}/arc/dashboard/reports/show_job/{}".format(arc_browse_host, arcjobid)

        rlog = dmx.utillib.releaselog.ReleaseLog( filepath, project, variant, libtype, config, releaser, 
            curdatetime, arcjobid, rel_config, milestone, thread, description, release_id, runtime=runtime, arcjob_path=arcjob_path)

        for [flow, subflow, topcell, status, error, waiver] in self.rlogresults:
            rlog.add_result(flow, subflow, topcell, status, error, waiver)

        rlog.save()



    def get_tnrwaivers_files(self):
        ### for Libtype release, only get <wsroot>/variant/libtype/tnrwaivers.csv
        filename = 'tnrwaivers.csv'
        if self.request.libtype:
            libtype = self.request.libtype
        else:
            libtype = '*'
        cmd = '{}/{}/{}'.format(self.request.variant, libtype, filename)
        self.logger.debug("globbing {} ...".format(cmd))
        files = glob.glob(cmd)
        return files


    def prepare_to_handle_request(self, request):
        self.rerun_config = self.get_snapshot_config_for_abnr_rerun(request.project, request.variant, request.libtype, request.snapshot_config)
        self.ipspec_config = self.get_ipspec_config(request.project, request.variant, request.snapshot_config)


    def send_completion_notification(self, success, message, rel_config):
        self.logger.info("""
            Completion Notification: {}
            Message: {}
            Rel Config: {}""".format(success, message, rel_config))


    def disable_logging(self):
        if self.logger_file_handler is not None:
            self.logger.removeHandler(self.logger_file_handler)
            self.logger_file_handler.flush()
            self.logger_file_handler.close()

    def enable_logging(self):
        if self.logger_file_handler is not None:
            self.logger_file_handler.setFormatter(Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', '%m-%d %H:%M:%S'))
            self.logger.addHandler(self.logger_file_handler)

    def create_workspace(self):
        """
        Create a brand new IC Manage workspace for the variant (if any)
        or libtype in the release request.  Populate it with the
        content necessary to run the tests.
        """

        icm = ICManageCLI()
        real_work_dir_path = os.path.realpath(os.path.abspath(self.request.work_dir))
        try:
            wsname = icm.add_workspace(self.request.project, self.request.variant, self.request.configuration, dirname=real_work_dir_path)
            self.wsname = wsname
            self.workspace_path = os.path.join(real_work_dir_path, wsname)
            icm.sync_workspace(wsname, skeleton=True)
        except Exception as e:
            self.logger.error(str(e))


        # We must be in the workspace folder for things like xlp4 sync to work.
        chdir(self.workspace_path)
        
        self.logger.info("Populating workspace %s" % self.workspace_path)
        self.populate_workspace() 

        return self.workspace_size(self.workspace_path)

    @staticmethod
    def workspace_size(workspace_path):
        (stdout, stderr) = execute(['du', '-sk', workspace_path], shell=True)
        return int(stdout[0].split()[0])

    def populate_workspace(self):
        """
        Determines what needs syncing based on the tests to be run. 
        Works by first syncing out all the audit logs (audit/...),
        then harvesting the required files from those audit logs and
        syncing those files.  Finally, it also syncs the file patterns
        required by vpNadder checks that will be run.

        Initially, we just synced everything, but that got slow...
        """
        # Sync ipspec so we know top cells, unneeded deliverables, etc.
        self.sync('*/ipspec/...')


        # Sync all audit logs (just for that variant should be enough)
        self.logger.debug("syncing audit logs ...")
        exitcode, stdout, stderr = run_command("xlp4 sync '*/*/audit/...'".format(self.request.variant))
        self.logger.debug('stdout:{}'.format(stdout))
        self.logger.debug('stderr:{}'.format(stderr))

        # Sync all tnrwaivers.csv file
        self.logger.debug("syncing tnrwaivers.csv ...")
        exitcode, stdout, stderr = run_command("xlp4 sync '{}/*/tnrwaivers.csv'".format(self.request.variant))
        self.logger.debug('stdout:{}'.format(stdout))
        self.logger.debug('stderr:{}'.format(stderr))


        ### This part is now needed regardless of whether it is a libtype or a variant release
        ### since context_check needs to be run on both occassions. http://pg-rdjira:8080/browse/DI-560
        self.logger.debug("Entering workspace population mode for required files ...")

        ### For Variant Release and Libtype Release, sync all files which are required in the audit xml files.
        runner = self.get_testrunner_instance(skip_required_fields=True)
        required_audit_logs, required_chksum_files = runner.get_required_files(include_all_files=True)
        self.logger.debug("required_chksum_files: {}".format(required_chksum_files))
      
        ### If libtype-release, then we need to sync over all files
        ### defined in manifest as well (for type-check).
        required_typecheck_files = []
        if self.request.libtype:
            e = dmx.ecolib.ecosphere.EcoSphere()
            f = e.get_family_for_thread(self.request.thread)
            ip = f.get_ip(self.request.variant, self.request.project)
            roadmap = e.get_roadmap_for_thread(self.request.thread)

            ### get_deliverable() needs to be called without milestone, because, example,
            ### sta exists in asic iptype ms 5.0, but not in ms 1.0.
            #d = ip.get_deliverable(self.request.libtype, milestone=self.request.milestone)
            d = ip.get_deliverable(self.request.libtype, roadmap=roadmap)
            cells = ip.get_cells_names()
            for c in cells:
                p = d.get_patterns(ip=self.request.variant, cell=c)
                required_typecheck_files += list(p.keys())

                x = d.get_filelists(ip=self.request.variant, cell=c)
                required_typecheck_files += list(x.keys())
            ### Remove duplicated patterns
            required_typecheck_files = list(set(required_typecheck_files))
        self.logger.debug("required_typecheck_files: {}".format(required_typecheck_files))

        ### https://jira.devtools.intel.com/browse/PSGDMX-2714
        ### special handling for syncing oa during TNR
        sync_all_oa = os.getenv('DMX_SYNC_ALL_OA_SCH_SYM', False)
        
        ### For each of the required_chksum_file, append it into
        ### tmpfile, and then sync tmpfile with the following command
        ###    xlp4 -x tmpfile sync
        tmpfile = '.ttt'
        f = open(tmpfile, 'w')
        for fn in required_chksum_files + required_typecheck_files:
            if len(fn) > 1 and not fn.startswith('/'):
                ### http://pg-rdjira:8080/browse/DI-423
                ### Remove multiple backslash
                cfn = re.sub('/+', '/', fn)

                pattern = '^[^/]+/oa/[^/]+/[^/]+/(schematic|symbol)/.+'
                if sync_all_oa and re.search(pattern, cfn):
                    self.logger.debug("sync_all_oa==True: Skip inserting file to .ttt: {}".format(cfn))
                else:
                    f.write(cfn + '@@\n')
        f.close()

        ### Sync All OA
        if sync_all_oa:
            self.logger.debug("Syncing all oa files ...")
            exitcode, stdout, stderr = run_command("xlp4 sync -f '*/oa/*/*/schematic/...' '*/oa/*/*/symbol/...' ")
            self.logger.debug('stdout:{}'.format(stdout))
            self.logger.debug('stderr:{}'.format(stderr))


        ### Uniqify files so that same files don't get sync'ed more than once
        ### https://jira.devtools.intel.com/browse/PSGDMX-1567
        uniqtmpfile = '.uniqttt'
        os.system("sort -u {} > {}".format(tmpfile, uniqtmpfile))

        self.logger.debug("Syncing {} syncfile ...".format(uniqtmpfile))
        exitcode, stdout, stderr = run_command('xlp4 -x {} sync'.format(uniqtmpfile))
        self.logger.debug('stdout:{}'.format(stdout))
        self.logger.debug('stderr:{}'.format(stderr))

        ### For each of the required_chksum_file, crawl it's symlink(if any)
        ### and sync it recursively.
        self.logger.debug("Starting recursive sync_symlink calls ...")
        with open(uniqtmpfile) as f:
            for line in f:
                ### remove the last '@@' character
                filename = line.strip()[0:-2]
                self.logger.debug("self.sync_symlink({})".format(filename))
                self.sync_symlink(filename)


        ### Support for designsync
        ### http://pg-rdjira:8080/browse/DI-1413
        ws = dmx.abnrlib.workspace.Workspace()
        try:
            ws.sync(libtypes=['bumps'])
        except Exception as e:
            self.logger.error(str(e))


    def sync_symlink(self, filepath):
        '''
        Assuming:-
            a.txt -> b.txt
            b.txt -> c.txt
            (c.txt is physical file)

        os.readlink('a.txt') will return b.txt
        os.readlink('b.txt') will return c.txt
        os.readlink('c.txt') will raise exception
        os.path.realpath('a.txt') will return c.txt
        os.path.realpath('b.txt') will return c.txt

        Given:-
            sync_symlink('a.txt')
        this will sync b.txt, and then it calls
            sync_symlink('b.txt')
        this will sync c.txt, and then it calls 
            sync_symlink('c.txt')
        which will raise exception, and ends here.
        '''
        try:
            ### Convert to absolute pathname (https://docs.python.org/2/library/os.html#os.readlink)
            target = os.path.abspath(os.path.join(os.path.dirname(filepath), os.readlink(filepath)))
            self.logger.debug('symlink syncing target file ==> {}'.format(target))
            exitcode, stdout, stderr = run_command("xlp4 sync {}@@".format(target))
            self.logger.debug('stdout:{}'.format(stdout))
            self.logger.debug('stderr:{}'.format(stderr))
            self.sync_symlink(target)
        except Exception as e:
            self.logger.debug("sync_symlink Exception: {}".format(str(e)))



    @staticmethod
    def extract_sync_patterns(required_files):
        """
        Calling xlp4 sync over and over for every required file would
        be too slow.  Instead, this method analyzes the required files
        and generates a list of Perforce file path patterns which are
        sure to cover the required files (and probably more).
        The current algorithm extracts file types (after the final dot) 
        and builds patterns that include all files of that type.  Any
        files without dots, are included as explicit patterns.
        """
        types = set()
        for file in required_files:
            if '.' in file:
                type = file.split('.')[-1]
                types.add('.../*.%s' % type)
            else:
                # No dot type means no generalization
                types.add(file)

        return types

    def sync(self, path):
        # Added @@ suffix to fix filenames with '@' or '#'. Fogbugz 336479
        cmd = ['xlp4', 'sync', '%s/%s@@' % (self.workspace_path, path)]
        self.logger.info("cmd: {}".format(cmd))
        (stdout, stderr) = execute(cmd, shell=True)
        self.logger.info("stdout: %s" % stdout)
        self.logger.info("stderr: %s" % stderr)

    def get_testrunner_instance(self, skip_required_fields=False):
        project = self.request.project
        variant = self.request.variant
        libtype = self.request.libtype
        configuration = self.get_configuration_to_test_and_release()
        
        workspace = self.workspace_path
        milestone = self.request.milestone
        thread = self.request.thread
        if skip_required_fields:
            info = {}
        else:
            info = self.tnr_dashboard.required_fields()
        return dmx.tnrlib.test_runner.TestRunner(project, variant, libtype, configuration, workspace, milestone, thread, self.web_api, info, development_mode=self.request.devmode, views=self.request.views, prel=self.request.prel)

    def run_tests(self):
        """
        Runs the tests, logs results to the dashboard,
        and returns a list of failures.
        """
        runner = self.get_testrunner_instance()
        failures = runner.run_tests()
        results = runner.get_test_results()

        return (failures,results)

    def get_snapshot_config_for_abnr_rerun(self, project, variant, libtype, composite_config):
        """
        For libtype releases, extracts and returns the libtype being 
        released from the composite configuration (which includes ipspec).
        For variant releases, just returns the given config.
        This snapshot is the one users shold provide when they re-run the
        release to have waivers applied.
        """
        if libtype is None:
            return composite_config
        else:
            return self.extract_subconfig_for_libtype(project, variant, libtype, composite_config)

    def get_ipspec_config(self, project, variant, composite_config):
        """
        Extracts the ipspec (libtype) configuration from the
        given composite configuration name.
        """
        return self.extract_subconfig_for_libtype(project, variant, 'ipspec', composite_config)

    def extract_subconfig_for_libtype(self, project, variant, libtype, composite_config):
        """
        Pulls out the name of the sub-configuration for the given libtype from
        the composite configuration.  
        For example, if you request libtype='ipspec' and give this composite config::

            * mycfg@snap1/
                * ipspec@snap2/
                * rtl@snap3/

        'snap2' will be returned.  If the libtype is not found immediately below the 
        top level config (mycfg in the example), then None is returned.
        """
        result = None
        snap_config = self.get_composite_configuration(project, variant, composite_config)
        for subconfig in snap_config.configurations:
            if hasattr(subconfig, 'libtype') and subconfig.libtype == libtype:
                #result = subconfig.config
                result = subconfig.name

        return result

    def get_configuration_to_test_and_release(self):
        """
        As of abnr 3.2.3 the configuration provided via the release queue
        for library releases is a variant configuration which includes the
        library AND ipspec.  Prior to 3.2.3 it was just the library, but
        we soon realized without ipspec even some type checks would
        not work (the top cells have to be enumerable).

        This method returns the configuration to be tested/released -- in 
        other words, for library releases, it is just the library snap
        create by abnr and inside the variant configuration in the request.

        For variant releases, there is no change, so this function simply 
        returns the request configuration.

        If there is some problem, an exception is raised with the
        text of the error that should appear on the dashboard.
        """
        result = None

        if self.request.libtype is None:
            result = self.request.snapshot_config
        else:
            # Look inside the config for the actual library
            snap_config = self.get_composite_configuration(self.request.project, self.request.variant, self.request.snapshot_config)
            # We expect either: 1) ipspec and the libtype being released, 
            # or 2) just ipspec (when ipspec is the libtype being released).

            for subconfig in snap_config.configurations:
                if not subconfig.is_config() and subconfig.libtype == self.request.libtype:
                    result =  subconfig.name
                    break

            if result is None:
                raise Exception("Did not find libtype being released in snapshot configuration!")

        return result 

    def get_composite_configuration(self, project, variant, config):
        """
        Returns an abnrlib CompositeConfig built from the IC Manage DB.
        """
        return ConfigFactory.create_from_icm(project, variant, config)

    def apply_waivers(self, failures, waivers):
        """
        Looks at the errors and sees if there are any waivers that match.
        Waivers have two sources: the web site and files on abnr cmdline.

        Failures is a list of TestFailure namedtuples.
        Waivers are a list from the abnr cmdline passed via RabbitMQ.

        This method loops over all the failures, sees if there is a waiver,
        and if there is, adds an entry in Splunk indicating so.
        Note that audit validation already applies waivers, so these are
        only for non-audit tests.

        Sets self.all_tests_passed_or_waived
        Returns False if the release was aborted, True otherwise.
        """
        api = Waivers()
        api.add_waiver_file(waivers)
        unwaived_failures = 0
        for failure in failures:
            waiver = api.find_matching_waiver(failure.variant, failure.flow, failure.subflow, failure.error)
            hsdes_waiver = api.find_matching_hsdes_waiver(failure.variant, failure.flow, failure.subflow, failure.error)

            self._errors_count += 1
            if waiver:
                (creator, reason, source) = waiver
                self.tnr_dashboard.write_waived_test(failure, creator, reason, source)
                self.rlogresults.append([failure.flow, failure.subflow, failure.topcell, 'waived', failure.error, reason])
                self._waived_count += 1
            elif hsdes_waiver:
                (creator, reason, source) = hsdes_waiver
                self.tnr_dashboard.write_waived_test(failure, creator, reason, source)
                self.rlogresults.append([failure.flow, failure.subflow, failure.topcell, 'waived', failure.error, reason])
                self._waived_count += 1
            else:
                self.tnr_dashboard.write_failed_test(failure)
                self.rlogresults.append([failure.flow, failure.subflow, failure.topcell, 'fail', failure.error, ''])
                self.all_tests_passed_or_waived = False
                unwaived_failures += 1
                self._unwaived_count += 1
                self._unwaived_errors.append(failure)
                if unwaived_failures == MAX_UNWAIVED_FAILURES:
                    self.logger.info("RELEASE ABORTED: TOO MANY UNWAIVED ERRROS") 
                    self.tnr_dashboard.log_new_status({}, "RELEASE ABORTED: too many unwaived errors.  Please use command-line waivers to proceed with this release.")
                    return False

        return True

    def all_pass_or_waived(self):
        return self.all_tests_passed_or_waived

    def make_rel_config(self):
        """
        Call this to create a REL configuration from the request snapshot
        configuration.  This should only be called if all the tests pass
        or were waived!  Returns True is the REL was created.
        """
        success = False

        project = self.request.project
        variant = self.request.variant
        libtype = self.request.libtype
        if libtype == '':
            libtype = None
        config = self.get_configuration_to_test_and_release()
        milestone = self.request.milestone
        thread = self.request.thread
        label = self.request.label

        rel_config_name = self.get_rel_config_name(project, variant, libtype, milestone, thread, label, self.request.views, self.request.skipmscheck, prel=self.request.prel)

        if self.request.dont_create_rel:
            self.logger.info("Should be making release configuration {}, but --dont_create_rel option is turned on, so skipping.".format(rel_config_name))
            return rel_config_name

        self.logger.info("Making release configuration %s" % rel_config_name) 
        self.tnr_dashboard.log_new_status({}, "Making release configuration %s" % rel_config_name)

        if libtype is None:
            snap = ConfigFactory.create_from_icm(project, variant, config)
        else:
            snap = ConfigFactory.create_from_icm(project, variant, config, libtype=libtype)

        rel = snap.clone(rel_config_name)
        rel.add_property('Owner', self.request.user)
        rel.add_property('DMX_Version', self.versionobj.dmx)
        rel.add_property('DMXDATA_Version', self.versionobj.dmxdata)

        ### http://pg-rdjira:8080/browse/DI-1401
        ### Add --views into property
        viewlabel = ''
        if self.request.views:
            # eg: views=['view_rtl', 'view_phys'], ==> 'RTL,PHYS'
            viewlabel = ','.join([v[5:] for v in self.request.views]).upper()
            rel.add_property("RELEASEVIEWS", viewlabel)

        ### http://pg-rdjira:8080/browse/DI-1061
        if self.request.syncpoint:
            rel.add_property("SYNCPOINT", self.request.syncpoint)
        if self.request.skipsyncpoint:
            rel.add_property("SKIPSYNCPOINT", self.request.skipsyncpoint)

        ### http://pg-rdjira:8080/browse/DI-1176
        if self.request.skipmscheck:
            rel.add_property("SKIPMSCHECK", self.request.skipmscheck)


        #####################################################
        ### Do this as user:icetnr
        icm = ICManageCLI()
        '''
        For now, we do not have protect table, thus, we dont have icetnr.
        We will just let psginfraadm to create the REL for now.
        icm.login_as_user('icetnr', all_host=True)
        with run_as_user('icetnr'):
            # Shallow is better since it is faster and all sub-configs are already immutable RELs
            success = rel.save(shallow=True)
        #icm.logout_as_user('icetnr')   # http://pg-rdjira:8080/browse/DI-668
        ### Done.
        '''
        success = rel.save(shallow=True)
        #####################################################

        if success:
            self.logger.info("Successfully created release configuration %s" % rel_config_name) 
            self.tnr_dashboard.log_new_status({'release_configuration':rel_config_name}, "Successfully created release configuration %s" % rel_config_name)
            
        return rel_config_name

    def get_rel_config_name(self, project, variant, libtype, milestone, thread, label, views=None, skipmscheck=None, prel=None):
        """
        Builds the official REL config name for the requested release.
        Consults IC Manage to detemine the right sequence number.
        The naming convention is: REL milestone -- thread [--label] __ timestamp

        Where the components are defined as follows:
          * Fixed strings "REL", "--", and "__"
          * The milestone must be a registered milestone string on the web
          * The thread (ie, NF5revA) which must be a registered thread string
          * An optional label (free-form identifier)
          * The timestamp (ie, 14ww032q) which is composed of

            * Two digit year
            * Fixed string "ww"
            * Two digit Altera workweek number
            * Day of the week (Monday=1, Friday=5)
            * A single letter (a-z) sequence number (to ensure uniqueness)
        """
        
        if hasattr(self, 'rel_config_name') and self.rel_config_name:
            return self.rel_config_name

        if self.request.dont_create_rel:
            self.rel_config_name = 'regmode_' + datetime.strftime(datetime.now(),'%Y%m%d_%H%M%S')
            return self.rel_config_name

        ### Add view name to label
        ### http://pg-rdjira:8080/browse/DI-704
        viewlabel = ''
        if views:
            # eg: views=['view_rtl', 'view_phys'], ==> 'RTL-PHYS'
            viewlabel = '-'.join([v[5:] for v in views]).upper()

        if prel:
            viewlabel = prel

        if label is not None:
            if viewlabel:
                viewlabel = viewlabel + '-' + label
            else:
                viewlabel = label

        if viewlabel:
            viewlabel = '--' + viewlabel
        
        ### Add skipmscheck to label
        ### http://pg-rdjira:8080/browse/DI-1176
        if skipmscheck:
            if viewlabel:
                viewlabel = viewlabel + '-SKIPMSCHECK'
            else:
                viewlabel = '--SKIPMSCHECK'


        (yy, ww, dow) = self.get_config_timestamp_info()
        name_prefix = 'REL%(milestone)s%(thread)s%(viewlabel)s__%(yy)sww%(ww)s%(dow)s' % locals()
        if prel:
            name_prefix = 'P' + name_prefix

        latest_existing_config = self.find_latest_similar_config(name_prefix, project, variant, libtype)
        if latest_existing_config is None:
            seqnum = 'a'
        else:
            last = latest_existing_config[-1] # last letter is the seqnum
            if last == 'z':
                self.logger.info("Ran out of sequence letters!  Try again tomorrow.")
                self.tnr_dashboard.log_new_status({}, "Ran out of sequence letters!  Try again tomorrow.")
            else:
                seqnum = chr(ord(last)+1)

        self.rel_config_name = '%s%s' % (name_prefix, seqnum)
        return self.rel_config_name

    def get_config_timestamp_info(self):
        """
        Returns a tuple (yy, ww, dow) based on the current date containing the two 
        digit year, the work week, and the day of the week where Mon=1, Tues=2, etc.
        """
        (yyyy, ww, dow) = self.get_yyyy_ww_dow_for_today()
        yy = '%02d' % (yyyy % 100)
        ww = '%02d' % ww
        dow = str(dow)

        return (yy, ww, dow)

    def get_yyyy_ww_dow_for_today(self):
        return intel_dates.intel_calendar(self.get_today_date_object())

    def get_today_date_object(self):
        ''' This method exist for unittest patching '''
        return datetime.today().date()

    def find_latest_similar_config(self, config_name, project, variant, libtype):
        """
        Retuns a configuration name that start with the same string as the 
        given config_name and has the highest sequence letter of all the 
        matches.  Returns None if there are no matching configurations.
        """
        configs = self.get_all_configs(project, variant, libtype)
        matches = sorted([c for c in configs if c.startswith(config_name)])
        if matches:
            return matches[-1]
        else:
            return None

    def get_all_configs(self, project, variant, libtype):
        """
        Returns a list of all the configuration names in IC Manage for the given params.
        """
        icm = ICManageCLI()
        if not libtype:
            ret = icm.get_configs(project, variant)
        else:
            ret = icm.get_library_releases(project, variant, libtype, library='*')
        return ret

    def flatten_config(self, icm_config):
        """
        Given a ComplexConfig instance, returns a set of tuples, one for each
        configuration referenced anywhere within that config (as well as at the
        top level).  Each tuple consists of:
        (project, variant, libtype, config_name) where
        libtype==None for complex configs. 
        """
        result = set()
        configs = icm_config.flatten_tree()
        for icm_config in configs:
            try:
                # simple configs will have a libtype, complex don't return one 
                (project, variant, libtype, config) = icm_config.key()
            except:
                (project, variant, config) = icm_config.key() 
                libtype = None

            record = (project, variant, libtype, config)
            self.logger.info("Found config: %s" % repr(record))
            result.add(record)

        return result

def setup_logging():
    """
    Sets up logging to stdout and stderr.
    """
    # Logger
    logger = getLogger()
    logger.setLevel(DEBUG)

    # Disable pika DEBUG
    pika = getLogger('pika')
    pika.setLevel(ERROR)

    # We log to stdout/stderr since this is generally run as an ARC job.
    logger_file_handler = None

    # stdout handler 
    logger_stdout_handler = StreamHandler(stdout)
    logger_stdout_handler.setFormatter(Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', '%m-%d %H:%M:%S'))
    logger.addHandler(logger_stdout_handler)

    # stderr handler (just errors)
    logger_stderr_handler = StreamHandler(stderr)
    logger_stderr_handler.setFormatter(Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', '%m-%d %H:%M:%S'))
    errors_only = SingleLevelFilter(ERROR, False)
    logger_stderr_handler.addFilter(errors_only)
    logger.addHandler(logger_stderr_handler)

    return (logger, logger_file_handler)

def parse_cmdline():
    """
    Handle command-line options.
    """
    parser = ArgumentParser(description='Gated release runner.  Constantly running (in production mode) on ARC via a cron job, this program listens to the build queue, and processes the requests.  By default, this program will listen to the test queue unless you give it the --production option which makes it listen to the production queue.  By default, this program will write workspaces to /icd_da/tnr/nadder/release, but you can use the --workdir option to override that for testing purposes.')

    #parser.add_argument('-p', '--production', default=False, action='store_true', help='listen to the production queue')
    #parser.add_argument('-q', '--queue', help='name of the RabbitMQ queue to send/receive release requests')
    parser.add_argument('-w', '--work_dir', default='/nfs/site/disks/psg_tnr_1/release/', help='where to create the workspace')

    parser.add_argument('-p', '--project', required=True, help='ICM Project')
    parser.add_argument('-v', '--variant', required=True, help='ICM Variant')
    parser.add_argument('-l', '--libtype', required=False, default=None, help='ICM Libtype (None if variant release)')
    parser.add_argument('-c', '--configuration', required=True, help='ICM Composite Configuration (This is always the configuration of the variant even if it is a libtype release)')
    parser.add_argument('-t', '--thread', required=True, help='Thread to be released.')
    parser.add_argument('-m', '--milestone', required=True, help='Milestone to be released.')
    parser.add_argument('-d', '--description', required=True, help='Description of the release.')
    parser.add_argument('--label', required=False, default=None, help='Label name that will be included in the released configuration.')
    parser.add_argument('-u', '--user', required=True, help='The unixid of the releaser.')
    parser.add_argument('--devmode', default=False, action='store_true', help='For developers only. Turned on so that the audit and splunk APIs does not write to production areas of Splunk. Default is off.')
    parser.add_argument('--dont_create_rel', default=False, action='store_true', help='For developers only. Turned on so that upon a full pass of audit validation, no REL config is created.')
    parser.add_argument('--release_id', required=True, help='The unique release_id generated from utillib.utils.get_abnr_id() function.')
    
    ### http://pg-rdjira.altera.com:8080/browse/DI-672
    parser.add_argument('--views', required=False, default=None, nargs='+', help='The views which contains a list of required deliverables. (Only applicable during variant release)')
    
    parser.add_argument('--prel', required=False, default=None, help='PREL')

    ### http://pg-rdjira:8080/browse/DI-1061
    parser.add_argument('--syncpoint', required=False, default=None, help='Syncpoint name which will be attached to the REL config')
    parser.add_argument('--skipsyncpoint', required=False, default=None, help='Reason for skipping syncpoint check that will be attached to the REL config.')

    ### http://pg-rdjira:8080/browse/DI-1176
    parser.add_argument('--skipmscheck', required=False, default=None, help='Reason for skipping milestone check. (label SKIPMSCHECK will be attached to the REL config.')

    args = parser.parse_args()

    return args


def main():
    """
    Main entrypoint for the release runner.
    """
    print("Entering release_runner main() at %s" % now())

    args = parse_cmdline()

    arc_job_id = environ['ARC_JOB_ID']

    (logger, logger_file_handler) = setup_logging()

    rr = ReleaseRunner(args, logger, logfile=None, logger_file_handler=None, arc_job_id=arc_job_id)
    rr.handle_request()


if __name__ == "__main__":
    exit(main())

