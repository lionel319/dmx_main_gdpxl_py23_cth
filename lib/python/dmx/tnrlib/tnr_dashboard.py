#!/usr/bin/env python
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/tnrlib/tnr_dashboard.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $
"""
This class provides a consistent way to log test results
to the TNR Splunk dashboard.  Architecturally, it sits 
between the low level SplunkLog class and the high-level
classes that invoke TestRunner.run_test() such as 
release_runner and quick.

It provides a higher level of abstraction than just the
collection of name/value pairs SplunkLog accepts.  If
you want to understand how the data in the Splunk TNR 
indexes is organized, understanding this class will help.
In fact, this class exists to provide the regularity 
the Splunk TNR application needs to function.  If you
change this class, there is a good chance you need to 
make a corresponding change to the Splunk TNR app.

TODO:
    - Do we really need all those release fields for EVERY record?

Author: Kirk Martinez
November 10, 2014
"""
from builtins import object
from logging import getLogger
from datetime import datetime
from socket import gethostname

# Altera libs
import os,sys
rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)
from dmx.tnrlib.execute import execute
from dmx.tnrlib.splunk_log import SplunkLog


logger = getLogger(__name__)

class TNRDashboard(object):
    """
    Structured interface for logging test results, configuations, logfiles,
    and various other data to the Splunk TNR app.   Use this class to log
    test results gathered by TestRunner's run_tests() method, or to log
    information from your application to Splunk in a format that the TNR
    Splunk application will understand.
    """
    def __init__(self, index, development_mode=False, splunk_log=None):
        """
        Development_mode is passed to the underlying SplunkLog class,
        and controls where the Splunk data is written.

        Index is used to indicate which Splunk index the data should go to,
        (probably "qa" for releases, or "quick" for quick check).

        Splunk_log is optional and exists only to support unit testing.
        """
        logger.debug("Initializing TNRDashboard")

        self.development_mode = development_mode
        self.splunk_log = splunk_log
        self.request_id = self.generate_unique_request_id()
        self.setup_dashboard_api(index)

    def setup_dashboard_api(self, index):
        """
        Provides a handle to the Splunk logging API.
        Ensures all required fields are populated.
        """
        self.info = self.required_fields()

        # self.info is what will always get included with every Splunk record
        if self.splunk_log is None:
            self.dashboard = SplunkLog(appname=index, datafile=self.request_id, fields=self.info, development_mode=self.development_mode)
        else:
            self.dashboard = self.splunk_log

    def generate_unique_request_id(self):
        """
        Returns a globally unique string identifier built using the current ARC job id,
        hostname, and datetime to fractions of a second.
        """
        hostname = gethostname()
        arc_job_id = self.get_arc_jobid()
        return 'tnr_'+str(arc_job_id)+'_'+str(hostname)+'_'+datetime.strftime(datetime.now(),'%Y-%m-%d_%H:%M:%S.%f')

    def get_arc_jobid(self):
        """
        Returns a string version of the ARC job id.
        """
        (out,err) = execute(['arc','job-info','id'])
        if len(err) > 0:
            logger.warning("Got error reading shell ARC job id:\n%s"%err)
        id = out[0].strip()
        return id

    def required_fields(self):
        """
        Returns the required fields.  Required fields will always be written to the Splunk log.
        Should be overridden by sub-classes.  By default, returns an empty dict.
        """
        return {}

    def write_logfile(self, logfile_fullpath):
        """
        Writes the given logfile using SplunkLog (which makes a copy
        of the file).  It is important that the logfile be closed 
        prior to calling this method.
        """
        info = dict(self.info)
        info['logfile'] = logfile_fullpath
        self.dashboard.log(info)

    def write_test_result(self, result):
        """
        Takes a TestResult and logs the appropriate info to Splunk.
        """
        if result.result_type == 'fail':
            self.write_failed_test_result(result)
        elif result.result_type == 'waived':
            raise "Not supported"
        else:
            self.write_a_pass_or_skipped_test(result)

    def write_failed_test_result(self, result):
        """
        Test is a TestResult named tuple (from test_result.py)
        """
        error_msg = self.clean_error_message(result.message)
        info = { 
                 'info-type':    'test-failure',
                 'flow':         result.flow,
                 'subflow':      result.subflow,
                 'flow-variant': result.variant,
                 'flow-libtype': result.libtype,
                 'flow-topcell': result.topcell,
                 'error':        error_msg}
        self.log_new_status(info, 'fail')

    def clean_error_message(self, error):
        error_msg = error
        if len(error_msg) > 1000:
            error_msg = error_msg[0:1000] + '...(error truncated -- run quick check in a workspace to see the complete text)'

        return error_msg

    def write_failed_test(self, test):
        """
        Test is a TestFailure named tuple (from test_result.py)
        """
        error_msg = self.clean_error_message(test.error)
        info = { 
                 'info-type':    'test-failure',
                 'flow':         test.flow,
                 'subflow':      test.subflow,
                 'flow-variant': test.variant,
                 'flow-libtype': test.libtype,
                 'flow-topcell': test.topcell,
                 'error':        error_msg}
        self.log_new_status(info, 'fail')

    def write_waived_test(self, test, creator, reason, source):
        """
        Test is a TestFailure named tuple.
        """
        info = { 
                 'info-type':      'test-failure',
                 'flow':           test.flow,
                 'subflow':        test.subflow,
                 'flow-variant':   test.variant,
                 'flow-libtype':   test.libtype,
                 'flow-topcell':   test.topcell,
                 'error':          test.error,
                 'waiver-creator': creator,
                 'waiver-reason':  reason,
                 'waiver-source':  source}
        self.log_new_status(info, 'waived')

    def write_a_pass_or_skipped_test(self, result):
        """
        Result is a TestResult named tuple.
        """
        info = {
                 'info-type':    'test-result',
                 'flow':         result.flow,
                 'subflow':      result.subflow,
                 'flow-variant': result.variant,
                 'flow-libtype': result.libtype,
                 'flow-topcell': result.topcell,
                 'message':      result.message
               }
        self.log_new_status(info, result.result_type)

    def write_passed_and_skipped_tests(self, results):
        """
        Writes given test results (as returned by TestRunner.get_test_results).
        """
        for result in results:
            if result.result_type == 'pass' or result.result_type == 'skip':
                self.write_a_pass_or_skipped_test(result)

    def log_new_status(self, given_info, status):
        """
        Writes a new record to Splunk with the given "status" field value.
        Also appends any given info (although a "status" field there 
        would be ignored) to the default info as set when this instance
        was created.
        """
        info = dict(self.info)
        info.update(given_info)
        info['status'] = status
        logger.debug("New status: %s" % status)
        if status == 'fail':
            logger.debug(">>> {}".format(info))
        self.dashboard.log(info)

    def log_flattenned_config(self, rel):
        """
        Writes a flattenned version of the given IC Manage configuration,
        which is of type ICManageConfiguration.
        CASE:264059 has us mark the top-level subconfigs
        """
        # Nothing needs to be done for simple configs as they have no sub-configs
        if rel.is_simple():
            return

        info = dict(self.info)
        logger.debug("Sending flattenned config to the dashboard...")

        for (sub_project, sub_variant, sub_libtype, sub_config, sub_toplevel) in self.flatten_config(rel):
            info['subconfig_project'] = sub_project
            info['subconfig_variant'] = sub_variant
            info['subconfig_libtype'] = sub_libtype
            info['subconfig_config'] = sub_config
            info['subconfig_toplevel'] = sub_toplevel

            logger.debug("Log subconfig: %s/%s@%s#%s (%d)" % (sub_project, sub_libtype, sub_variant, sub_config, sub_toplevel))
            self.dashboard.log(info)

    def flatten_config(self, icm_config):
        """
        Given a ComplexConfig instance, returns a set of tuples, one for each
        configuration referenced anywhere within that config (as well as at the
        top level).  Each tuple consists of:
        (project, variant, libtype, config_name, top_level) where
        libtype==None for complex configs. 
        Project, variant, libtype, and config_name are strings.
        top_level is an integer 1 if either:

            a. the subconfig is immediately below the given config, 
            b. the subconfig is a simple config directly below an entry in a) it is 0 otherwise

        The top_level field supports reports showing only first-level hierarchy.
        """
        result = set()
        configs = icm_config.flatten_tree()
        for sub_config in configs:
            try:
                # simple configs will have a libtype, complex don't return one 
                (project, variant, libtype, config) = sub_config.key()
            except:
                (project, variant, config) = sub_config.key() 
                libtype = None

            top_level = 0
            # Direct descendant is considered top_level
            if sub_config in icm_config.configurations:
                top_level = 1
            elif sub_config.is_simple():
                # Simple config under a direct descendant is also top_level
                for direct in icm_config.configurations:
                    if not direct.is_simple() and sub_config in direct.configurations:
                        top_level = 1
                        break

            record = (project, variant, libtype, config, top_level)
            logger.debug("Found config: %s" % repr(record))
            result.add(record)

        return result

class TNRDashboardForRelease(TNRDashboard):
    """
    A TNRDashboard with release-specific header fields.
    """
    def __init__(self, index, arc_job_id, rerun_config, ipspec_config, request, development_mode=False, splunk_log=None):
        """
        Takes the normal TNRDashboard args as well as:
        arc_job_id      - the ID of the ARC job for the release runner job
        request         - a ReleaseRequest object
        rerun_config    - the config the user should use to re-run the release
        ipspec_config   - the IPSPEC configuration used for the release
        """
        self.arc_job_id    = arc_job_id
        self.rerun_config  = rerun_config
        self.ipspec_config = ipspec_config
        self.request       = request

        super(TNRDashboardForRelease, self).__init__(index, development_mode, splunk_log)

        logger.debug("Base TNRDashboard infoset:")
        for (k,v) in list(self.info.items()):
            logger.debug("%s: %s" % (k,v))

    def required_fields(self):
        """
        Override base class to define different required fields for releases.
        """
        return {'status': 'no status',
                'info-type': 'runner-log',
                'arc_job_id': self.arc_job_id,
                'request_id': self.request_id,
                'abnr_release_id': self.request.release_id,
                'user': self.request.user,
                'timestamp': self.request.timestamp,
                'project': self.request.project,
                'variant': self.request.variant,
                'config': self.request.config,
                'libtype': self.request.libtype,
                'milestone': self.request.milestone,
                'thread': self.request.thread,
                'label': self.request.label,
                'description': self.request.description,
                'snapshot_config': self.rerun_config,
                'ipspec_config': self.ipspec_config,
                'abnr_version': self.request.abnr_version
               }

class TNRDashboardForQuick(TNRDashboard):
    """
    A TNRDashboard with quick check-specific fields.
    """
    def __init__(self, index, workspace_name, milestone, thread, project, variant, libtype, configuration, user, run_date, development_mode=False, splunk_log=None):
        """
        index            - the name of a Splunk data storage area (see splunk_log.py)
        milestone, thread, project, variant, libtype, configuration 
                         - quick check args
        user             - who ran quick check
        run_date         - when did quick check run?
        development_mode - if true, splunk_log writes to a separate area which can be indexed by a dev splunk server, for example
        splunk_log       - an instance of SplunkLog; for unit testing only
        """
        self.workspace_name = workspace_name
        self.milestone = milestone
        self.thread = thread
        self.project = project
        self.variant = variant
        self.libtype = libtype
        self.configuration = configuration
        self.user = user 
        self.run_date = run_date
        self.timestamp =  datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')

        super(TNRDashboardForQuick, self).__init__(index, development_mode, splunk_log)

    def required_fields(self):
        """
        Override base class to define different required fields for quick check.
        """
        return {'status': 'no status',
                'workspace': self.workspace_name,
                'info-type': 'quick-log',
                'request_id': self.request_id,
                'user': self.user,
                'timestamp': self.timestamp,
                'project': self.project,
                'variant': self.variant,
                'libtype': self.libtype,
                'config': self.configuration,
                'milestone': self.milestone,
                'thread': self.thread,
               }
