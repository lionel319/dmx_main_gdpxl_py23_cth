# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/tnrlib/splunk_log.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $
"""
This module provides a generic API to write data to the QA Dashboard.
Each application can write data via the SplunkLog class.
The name of the application determines where the data will be stored.
Each application can define different data formats, which will require
different front-end Splunk applications to process them.

The module is site-aware.  Each application has a location local to 
SJ and local to PG.  The PG content is rsynced over to SJ on a regular 
basis (via a cron job on kmartine@sj-ice-cron).  The SJ Splunk server
only looks at the SJ location.  This was done instead of using a 
Splunk forwarder because we have to rsync the persistent logs anyway,
and we don't want timing issues causing broken links on the dashboard.

Here is an example of how to use it for the "fcv" application::

    # splunk_log is part of the icd_cad_qa resource
    >>> from splunk_log import SplunkLog
    >>> from datetime import datetime

You must provide a unique identifier for the Splunk data file::

    >>> run_id = 'test_run_on_'+datetime.strftime(datetime.now(),'%Y-%m-%d')

The following fields will always be written out to the Splunk log
with these values, unless they are overriden in dictionary
provided to the log() method::

    >>> required_fields = {'configuration': run_id,
    >>>                    'test': '',
    >>>                    'a field_name': 'its default value'}

    >>> db = SplunkLog('fcv', run_id, required_fields)

If you want to follow test progress with Splunk (recommended
for long-running jobs) pre-register all tests before starting::

    >>> info = {'test': 'test one', 'status':'Not started'}
    >>> db.log(info)

Then, later::

    >>> info = {'test': 'test one', 'status':'Running'}
    >>> db.log(info)

A field called "logfile" has special significance: the SplunkLog
API will save off those logfiles to a persistent storage are
so they can be browsed even after the IC Manage workspace is deleted.

Note that the path will be preserved, but if you run your application
twice from the same directory (referencing the same logfile path),
then the persisted file will get overwritten the 2nd time.
You are expected to run your tool in a different directory each time.

Also, please do not reference excessively large log files.

If you provide a field called "configuration", this is assumed to be
an IC Manage configuration name, and multiple fields will be added.
The values are found by splitting the standard name into its component 
parts.  If the name does not adhere to the naming convention, the extra
fields for the parts will not be added.  This is done to facilitate 
front-end dashboard coding.

Every call to log() creates a line in the Splunk logfile.  These are 
called "events" in Splunk.  As soon as the log() call is made, the
Splunk server starts indexing them, and they are immediately searchable.

It is imperative that there be no newlines in the keys or values in
the dictionary of data you log!  If there are newlines, Splunk will 
not index that file on or beyond the erroneous newline.

For Splunk servers, please see servers.py.

If you want to generate Splunk data is a different place (where it will 
NOT automatically be picked up by the Splunk demo dashboard), you can  
provide your own full paths to the Splunk file, and persistent logfile 
locations as the 4th and 5th arguments when creating the SplunkLog().

TODO:
    * Define the fields for each application here, along with what they mean
      and when they are filled out, so that someone looking at the front-end
      Splunk dashboards can make sense of the data.
    * use the run-id to uniqify logfiles to avoid overwriting logfiles
"""
from __future__ import print_function
from past.builtins import basestring
from builtins import object
import copy
from datetime import datetime
import os
import sys
import shutil
import re
import logging

# Altera libs
rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)

from dmx.utillib.utils import get_tools_path, is_pice_env

LOGGER = logging.getLogger(__name__)

class SplunkLog(object):
    """
    SplunkLog is the class to use when you need to write data in a Splunk-friendly
    format.  Features:

        * allows you to define required fields, and default values
        * allows additional fields to be defined "on the fly" when writing to the log
        * saves off logfiles to a separate area so they will be linkable from Splunk
          even after the original file has been deleted
        * is site-aware: when run in Penang, it logs to a local directory which is then
          rsynced back to SJ.

    This class is the single place to define where Splunk logs live for each
    application which uses it.
    """
    # For each site with independent storage, every supported app is given a tuple:
    # (splunk_data_fullpath, logfiles_fullpath)
    PRODUCTION_LOCATIONS = {
            'pice-pg': {
                'qa':('/nfs/site/disks/fln_tnr_1/splunk/qa_data', '/nfs/site/disks/fln_tnr_1/splunk/qa_logs'),
                },
            'pice-sj': {
                'qa':('/nfs/site/disks/fln_tnr_1/splunk/qa_data', '/nfs/site/disks/fln_tnr_1/splunk/qa_logs'),
                },
            'sj': {
                'qa': ('/net/sj-iticenas01/ifs/iceng/icmisc/tnr/nadder/splunk/qa_data', '/net/sj-iticenas01/ifs/iceng/icmisc/tnr/nadder/splunk/qa_logs'),
                'ice_project': ('/net/sj-iticenas01/ifs/iceng/icmisc/tnr/nadder/splunk/ice_project_data', '/net/sj-iticenas01/ifs/iceng/icmisc/tnr/nadder/splunk/ice_project_logs'),
                'build': ('/net/sj-iticenas01/ifs/iceng/icmisc/tnr/nadder/splunk/build_data', '/net/sj-iticenas01/ifs/iceng/icmisc/tnr/nadder/splunk/build_logs'),
                'fcv': ('/net/sj-iticenas01/ifs/iceng/icmisc/tnr/nadder/splunk/fcv_data', '/net/sj-iticenas01/ifs/iceng/icmisc/tnr/nadder/splunk/fcv_logs'),
                'periodic': ('/net/sj-iticenas01/ifs/iceng/icmisc/tnr/nadder/splunk/periodic_data', '/net/sj-iticenas01/ifs/iceng/icmisc/tnr/nadder/splunk/periodic_logs'),
                },
            'pg': {
                'qa': ('/net/pg-itenginas01/ifs/iceng/icmisc/tnr/nadder/splunk/qa_data', '/net/pg-itenginas01/ifs/iceng/icmisc/tnr/nadder/splunk/qa_logs'),
                'fcv': ('/net/pg-itenginas01/ifs/iceng/icmisc/tnr/nadder/splunk/fcv_data', '/net/pg-itenginas01/ifs/iceng/icmisc/tnr/nadder/splunk/fcv_logs'),
                'periodic': ('/net/pg-itenginas01/ifs/iceng/icmisc/tnr/nadder/splunk/periodic_data', '/net/pg-itenginas01/ifs/iceng/icmisc/tnr/nadder/splunk/periodic_logs'),
                }
            }

    DEVELOPMENT_LOCATIONS = {
            'pice-pg': {
                'qa':('/tmp', '/tmp'),
                },
            'pice-sj': {
                'qa':('/tmp', '/tmp'),
                },
            'sj': {
                'qa': ('/data/yltan/splunk/qa_data', '/data/yltan/splunk/qa_logs'),
                'ice_project': ('/net/sj-itnas01a/data/kmartine/splunk/ice_project_data', '/net/sj-itnas01a/data/kmartine/splunk/ice_project_logs'),
                'build': ('/data/kmartine/splunk/build_data', '/data/kmartine/splunk/build_logs'),
                'fcv': ('/data/kmartine/splunk/fcv_data', '/data/kmartine/splunk/fcv_logs'),
                'periodic': ('/data/kmartine/splunk/periodic_data', '/data/kmartine/splunk/periodic_logs'),
                },
            'pg': {
                'qa': ('/data/yltan/splunk/qa_data', '/data/yltan/splunk/qa_logs'),
                'fcv': ('/data/kmartine/splunk/fcv_data', '/data/kmartine/splunk/fcv_logs'),
                'periodic': ('/data/kmartine/splunk/periodic_data', '/data/kmartine/splunk/periodic_logs'),
                }
            }

    def __init__(self, appname, datafile, fields, splunk_data_dir=None, splunk_log_dir=None, development_mode=False):
        """
        appname     the name of the application using this class
                    this determines the file path where the Splunk logs 
                    and saved logfiles will be written.  Must be a valid name.
        datafile    the name of the Splunk data file that will be created
                    under the log path determined using appname.  These need
                    to be unique to avoid problems with multiple SplunkLog
                    instances writing to the same file at the same time.
        fields      a dictionary of field names and their default values
                    some fields are pre-defined and will always be written:
                        utc_time: the time when the log entry was written
                    fields that start with "config-" are auto-created when
                    a "configuration" field is provided, here or via log(),
                    so you may wish to avoid those.
                    Field names and values should not contain newlines.
        splunk_data_dir and
        splunk_log_dir     are provided for testing purposes:
                    if provided, data and logs will be written to these locations 
                    instead of the appname default.   The appname still must be 
                    valid however.
        """
        self.appname = appname

        try:
            site = os.environ['ARC_SITE'].lower()
            if site.startswith('p'):
                self.site = 'pg'
            else:
                self.site = 'sj'
            if is_pice_env():
                self.site = 'pice-' + self.site
        except KeyError as e:
            print("Can't detemine site.  You must be in an ARC shell to log data to splunk.")
            raise

        try:
            if development_mode:
                LOGGER.info("Development mode")
                (self.data_dir, self.log_dir) = self.DEVELOPMENT_LOCATIONS[self.site][appname]
            else:
                LOGGER.debug("Production mode")
                (self.data_dir, self.log_dir) = self.PRODUCTION_LOCATIONS[self.site][appname]
        except KeyError as e:
            print("Can't detemine storage location for application, %s" % appname)
            print("Valid application names are: %s" % ','.join(list(self.LOCATIONS[self.site].keys())))
            raise

        if splunk_data_dir:
            self.data_dir = splunk_data_dir
        if splunk_log_dir:
            self.log_dir = splunk_log_dir

        LOGGER.debug("SplunkLog writing data to %s" % self.data_dir)
        LOGGER.debug("SplunkLog writing logs to %s" % self.log_dir)

        self.datafile = os.path.join(self.data_dir, datafile)
        LOGGER.debug("SplunkLog data file: %s" % self.datafile)

        self.fields = self.clean(fields)

    def clean(self, fields):
        """
        Return a new dict with all newlines removed.
        Also, any single-quotes in the values are removed (JavaScript for waivers barfs on them).
        Also, any double quotes in the values are removed (JSON data becomes malformed with on them).
        """
        clean = {}
        for (k,v) in list(fields.items()):
            clean_key = k.replace('\n','')
            if isinstance(v, basestring):
                clean_value = v.replace('\n',' ').replace("'","").replace('"','')
            else:
                clean_value = v

            clean[clean_key] = clean_value

        return clean

    def split_configuration(self, configuration):
        """
        Splits and IC Manage configurations that adhere to the standard
        naming conventino into several sub-fields.  Returns a dictionary
        of fields and values.  If the given name is not in the standard,
        returns the same fields but with empty string values.
        """
        config_re = re.compile('REL(\d.\d)(--\S+)*__(\d\d)ww(\d\d)(\d)([a-z]{3})')
        config_milestone = ''
        config_year = ''
        config_workweek = ''
        config_day = ''
        config_suffix = ''
        parsed_config = config_re.match(configuration)
        if parsed_config:
            config_milestone = parsed_config.group(1)
            config_year = parsed_config.group(3)
            config_workweek = parsed_config.group(4)
            config_day = parsed_config.group(5)
            config_suffix = parsed_config.group(6)

        return {'config_milestone': config_milestone,
                'config_year': config_year,
                'config_workweek': config_workweek,
                'config_day': config_day,
                'config_suffix': config_suffix}

    def log(self, info):
        """
        Writes a JSON-formatted entry into the splunk log for the current app, 
        integrating the information provided in the info dictionary.  
        The key 'utc_time' will be populated with log currenet UTC time.
        If a 'logfile' key is provided in info, its value must be a full path.
        This function will save it off to a persistent location and save that 
        location (instead of the one given) to the splunk log.
        """
        clean_info = self.clean(info)
        splunk_data = copy.copy(self.fields)

        # Add in (or override defaults with) any passed-in data
        for (key, value) in list(clean_info.items()):
            splunk_data[key] = value

        if 'configuration' in list(splunk_data.keys()):
            for (k, v) in list(self.split_configuration(splunk_data['configuration']).items()):
                splunk_data[k] = v

        splunk_data['utc_time'] = datetime.strftime(datetime.now(), '%Y-%m-%d_%H:%M:%S.%f')

        # Save off any logfiles to persistent storage
        if 'logfile' in list(clean_info.keys()) and clean_info['logfile']:
            logfile = self.save_off_logfiles(clean_info['logfile'])
            if logfile:
                splunk_data['logfile'] = logfile

        self.write_to_datafile(splunk_data)

    def write_to_datafile(self, splunk_data):
        """
        Writes the given data into the previously selected Splunk data file.
        """
        js_fields = []
        for k in sorted(splunk_data.keys()):
            js_fields.append('"%s": "%s"' % (k, splunk_data[k]))
        js_obj = ','.join(js_fields)

        with open(self.datafile, 'a') as splunk_file:
            splunk_file.write('{%s}\n' % js_obj)

    def log_all_html(self, rootdir):
        """
        Scan the given directory and all subdirectories for HTML
        files (\*.html).  Saves them off to persistent storage.
        Caller is expected to call log() on each top-level HTML
        file.
        """
        for root, dirs, files in os.walk(rootdir):
            htmlfiles = [f for f in files if f.endswith('.html')]
            for htmlfile in htmlfiles:
                self.save_off_logfiles(os.path.join(root, htmlfile))
                
    def save_off_logfiles(self, src_path):
        """
        Saves off the given file to persistent storage while preserving the 
        directory structure.  Src_path must be an absolute path.  Returns 
        the path where the file was persisted.  If there is a problem doing 
        the copy, an exception will be thrown.
        """
        dst_dir = self.get_dest_dir(src_path)
        shutil.copy(src_path, dst_dir)
        logfile = os.path.join(dst_dir, os.path.basename(src_path))

        return logfile

    def get_dest_dir(self, src_path):
        """
        Returns the destination directory of src_path, creating it
        if it doesn't exist.  If it creates it, it does so using
        775 permissions.
        """
        # TODO: we only really need the path from the workspace root on down...
        #       or, generally, some "top-level" folder for the app
        src_file = os.path.basename(src_path)
        dst_dir = os.path.dirname(src_path)
        dst_dir = dst_dir[1:] # Remove leading slash
        dst_dir = os.path.join(self.log_dir, dst_dir)

        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir, 0o775)

        return dst_dir

