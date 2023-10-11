#!/usr/bin/env python
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/releasestatus.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $
"""
release_status is a user utility for querying the status
of a release via the Splunk API.

Kirk Martinez
March 20, 2015
"""
from __future__ import print_function
from builtins import object
from time import sleep
from xml.dom import minidom
from xml.etree import ElementTree as ET
from logging import getLogger, DEBUG, ERROR, StreamHandler, Formatter
from sys import exit, exc_info, stdout
from argparse import ArgumentParser
from datetime import datetime
from getpass import getpass
from traceback import format_exception
from collections import namedtuple
import os
import sys
import logging

from dmx.tnrlib.splunk_sdk import results as splunk_results, client as splunk_client
from dmx.tnrlib.servers import Servers
from dmx.tnrlib.dashboard_query import DashboardQuery
from dmx.tnrlib.waiver_file import WaiverFile, AWaiver

Release = namedtuple('Release', 'rid, started, project, variant, libtype, snapshot_config, runtime, latest, failures, waived, unwaived, rel_config, starttime, stoptime, arc_resources') 
ReleaseError = namedtuple('ReleaseError', 'info_type, flow, subflow, topcell, status, err_msg' )

class ReleaseStatusError(Exception): pass

class ReleaseStatus(object):
    '''
    Used to fetch release status from the dashboard.
    '''

    def __init__(self, production, userid, password, show_errors, releaser, project, variant, libtype, milestone, thread, number, arc_resources, owner, kvp, test, waiver_file, rel_config, snapshot_config=None):
        self.show_errors = show_errors 
        self.releaser = releaser
        self.project = project
        self.variant = variant
        self.libtype = libtype
        self.milestone = milestone
        self.thread = thread
        self.snapshot_config = snapshot_config
        self.number = number
        self.arc_resources = arc_resources
        self.owner = owner
        self.kvp = kvp
        self.test = test 
        self.rel_config = rel_config 
        self.waiver_file = waiver_file      
        self.logger = logging.getLogger(__name__)

        if production:
            self.server = Servers.SPLUNK_PROD_URL
        else:
            self.server = Servers.SPLUNK_TEST_URL

        # Using Splunk HTTP API
        self.dashboard = DashboardQuery(userid, password, production)

        # Splunk Python API (which wraps Splunk's HTTP API)
        # See: http://dev.splunk.com/view/python-sdk/SP-CAAAEE5#normaljob
        # And: http://docs.splunk.com/Documentation/PythonSDK
        self.splunk_sdk_service = splunk_client.connect(host=Servers.SPLUNK_PROD_HOST, scheme="https", port=Servers.SPLUNK_PROD_PORT, app='tnr', username=userid, password=password)

    def release_report(self):
        """
        Prints the selected report.
        """
        if self.waiver_file:
            self.gen_waiver_file(self.waiver_file, self.project, self.variant, self.libtype, self.rel_config, self.owner)
        elif self.kvp:
            self.kvp_report()
        else:
            self.text_report()

    def gen_waiver_file(self, waiver_file, project, variant, libtype, rel_config, default_owner):
        """
        Queries Splunk for the waivers, generates a command-line waiver file, 
        and saves it to the given path.
        """
        waivers_iter = self.get_waivers(project, variant, libtype, rel_config)

        wf = WaiverFile()
        wf.load_from_list(waivers_iter)
        contents = wf.to_ascii()

        try:
            with open(waiver_file, 'w') as f:
                f.write("# Contents based on waivers extracted from %s\n" % self.icm_id(project, variant, libtype, rel_config) ) 
                f.write("# variant, flow, subflow, reason, error\n")
                for w in contents:
                    # TODO: add owner
                    owner = ''
                    (variant, flow, subflow, reason, error, filepath) = w
                    if owner == '':
                        owner = default_owner
                    f.write( '{0}, {1}, {2}, {3}, "{4}", "{5}"\n'.format(variant, flow, subflow, owner, reason, error) )
        except Exception as e:
            self.logger.debug(format_exception(*exc_info()))
            self.logger.error("There was a problem generating the waiver file:\n%s" % e)
            exit(1)

    def get_waivers(self, project, variant, libtype, rel_config):
        """
        Run Splunk search to get the waivers for the given p/v/c.
        Returns a list of AWaiver named tuples. 
        """
        request_id = self.get_request_id(project, variant, libtype, rel_config)

        if libtype == '':
            search = 'search index=qa [| savedsearch earliest_subrelease request_id="%(request_id)s"] [| savedsearch latest_subrelease request_id="%(request_id)s"] variant="*" flow-libtype="*" status=waived | join request_id [| inputlookup subreleases | search request_id="%(request_id)s" | eval request_id=rid | eval stoptime=starttime+duration+1] | rename user as releaser | table project variant flow-libtype RelConfig ReleasedOn releaser flow subflow waiver-creator waiver-reason error request_id starttime stoptime' % locals()
        else:
            self.logger.error("Creating a waiver file for libtype releases is not currently supported.")
            # The problem is mainly that we don't know the relevant time range
            self.logger.error("Workaround: specify a variant config that includes the libtype release you want.")
            exit(1)

        # Count=0 means return all results
        print("Searching Splunk dashboard for matching waivers...")
        job = self.splunk_sdk_service.jobs.create(search, exec_mode='normal')

        while True:
            while not job.is_ready():
                pass
            stats = {"isDone": job["isDone"],
                     "doneProgress": float(job["doneProgress"])*100,
                      "scanCount": int(job["scanCount"]),
                      "eventCount": int(job["eventCount"]),
                      "resultCount": int(job["resultCount"])}
        
            status = ("\r%(doneProgress)03.1f%%   %(scanCount)d records scanned   "
                      "%(eventCount)d waivers found") % stats
        
            stdout.write(status)
            stdout.flush()
            if stats["isDone"] == "1":
                stdout.write("\n")
                break
            sleep(2)

        # Collect ALL the results using paging
        waiver_count = int(job['resultCount'])
        waivers = []
        waivers_processed = 0
        offset = 0;
        print("Fetching results from Splunk...")
        while (offset < waiver_count):
            # count=0 only gives 50,000 hence the pagination
            results = splunk_results.ResultsReader(job.results(offset=offset, count=50000)) 

            for w in results:
                variant = w['variant']
                flow = w['flow']
                subflow = w['subflow']
                try:
                    reason = w['waiver-reason']
                except:
                    reason = 'Not provided.'
                error = w['error']

                # '' is filepath which is not relevant for our purposes
                waivers.append( AWaiver(variant, flow, subflow, reason, error, '') )
                waivers_processed += 1

                pctComplete = 100 * (0.0+offset) / waiver_count
                status = "\r%03.1f%%   %d retrieved / %d total)" % (pctComplete, waivers_processed, waiver_count)
                stdout.write(status)
                stdout.flush()

            offset = offset + 50000

        job.cancel()
        stdout.write('\n')

        return waivers

    def get_text_from_xml_default_to_empty_string(self, elem, field):
            the_field = elem.find(field)
            if the_field is not None:
                if the_field.text is None:
                    return ''
                else:
                    return the_field.text
            else:
                return ''

    def get_request_id(self, project, variant, libtype, rel_config):
        """
        Looks up the request_id in Splunk.
        """
        if libtype == '':
            search = '| inputlookup successful_releases | rename rid as request_id | search project="{0}" variant="{1}" libtype=None RelConfig="{3}" | fields request_id'.format(project, variant, libtype, rel_config)
        else:
            search = '| inputlookup successful_releases | rename rid as request_id | search project="{0}" variant="{1}" libtype="{2}" RelConfig="{3}" | fields request_id'.format(project, variant, libtype, rel_config)

        result = self.dashboard.run_query(search, '-24h', 'now') 
        root = ET.fromstring(result)
        try:
            the_result = root.find('result')
            request_id = the_result.find('.//field[@k="request_id"]/value/text').text
        except Exception as e:
            self.logger.error( "Cannot find the release ID for {0}".format( self.icm_id(project, variant, libtype, rel_config) ) )

        return request_id

    def icm_id(self, project, variant, libtype, rel_config):
        if libtype == '':
            return "{0}/{1}@{3}".format(project, variant, libtype, rel_config)
        else:
            return "{0}/{1}:{2}@{3}".format(project, variant, libtype, rel_config)

    def kvp_report(self):
        """
        Prints out a key-value-pair formatted dump of the releases.
        """
        releases = self.releases_summary(self.number, self.arc_resources, self.rel_config)
        for release in releases:
            print("started = %s" % release.started)
            print("project = %s" % release.project)
            print("variant = %s" % release.variant)
            print("libtype = %s" % release.libtype)
            print("snap_config = %s" % release.snapshot_config)
            print("rel_config = %s" % release.rel_config)
            print("status = %s" % self.get_release_status(release))
            print("failures = %s" % release.failures)
            print("waived = %s" % release.waived)
            print("unwaived = %s" % release.unwaived)
            for resource in release.arc_resources:
                print("audit_file = %s" % resource[0])
                print("arc_resources = %s" % resource[1])

            if self.errors:
                for error in self.release_errors(release.rid, release.starttime, release.stoptime):
                    print("error = %s" % error)

            print("\n")

    def text_report(self):
        """
        Prints out a human-readable tabular text report of the selected releases.
        """
        print("\nReleases summary (last 24 hours) for the given user, project, variant, and libtype")
        print("----------------------------------------------------------------------------------\n")
        print('\t'.join(['status   ', 'project  ', 'variant'+' '*13, 'libtype', 'fail', 'waive', 'unwaived', 'rel_config'])) 
        print('\t'.join(['------   ', '-------  ', '-------'+' '*13, '-------', '----', '-----', '--------', '----------'])) 
        releases = self.releases_summary(self.number, self.arc_resources, self.rel_config)
        for r in releases:
            status = self.get_release_status(r)

            print('\t'.join([status, r.project, r.variant.ljust(20), r.libtype, r.failures, r.waived, r.unwaived.ljust(8), r.rel_config]))

        if self.show_errors:
            print("Now showing details for each of the releases listed above.")

            for r in releases:
                print("\n")
                name = self.get_release_name(r)
                print("Release of %s" % name)
                search = 'search index=qa request_id="%s" ' % r.rid
                result = self.dashboard.run_query(search, r.starttime, r.stoptime)
                print(self.dashboard.release_details_url(r.rid, r.starttime, r.stoptime))
                cmd = self.release_commandline(r.rid, r.starttime, r.stoptime)
                print("Command-line: %s" % cmd)
                errors = self.release_errors(r.rid, r.starttime, r.stoptime)
                print("Errors:")
                print(view_releaseerror_header())
                print('\n'.join([view_releaseerror(e) for e in errors]))

    def get_release_status(self, r):
        """
        Returns a string indicating if the release succeeded, failed, or is in progress.
        """
        if r.rel_config:
            status='Released'
        elif r.latest == 'Finished handling request':
            status='Failed  '
        else:
            status='Working '
        
        return status

    def get_release_name(self, r):
        """
        Returns a string version of the release in the form:
        project/variant:libtype@config
        """
        name = '%s/%s' % (r.project, r.variant)
        if r.libtype:
            name += ':%s' % r.libtype
        if r.rel_config:
            name += '@%s' % r.rel_config

        return name

    def releases_summary(self, max_releases, get_arc_resources, find_rel_config=None):
        """
        Simiar to the main table on the Test & Release dashboard, this 
        lists all the matching release requests along with a summary of
        failed and waived errors and the REL config if any.
        (It also contains other tidbits like snapshot config and arc resources.)
        Returns a list of Release named tuples.
        """
        if find_rel_config is not None:
            search = '| savedsearch releases project="%s" user="%s" variant="%s" libtype="%s" | search "Configuration Released"="%s" | sort -starttime | head %d | lookup snapshot_by_request_id request_id as rid output snapshot_config' % (self.project, self.releaser, self.variant, self.libtype, find_rel_config, max_releases)
        else:
            search = '| savedsearch releases project="%s" user="%s" variant="%s" libtype="%s" | sort -starttime | head %d | lookup snapshot_by_request_id request_id as rid output snapshot_config' % (self.project, self.releaser, self.variant, self.libtype, max_releases)

        result = self.dashboard.run_query(search, '-24h', 'now') 
        #result = self.dashboard.run_query(search, '-7d', 'now')
        self.logger.debug("Got release summary XML: %s" % result)
        root = ET.fromstring(result)
        releases = []
        for release in root.iter('result'):
            rid = release.find('.//field[@k="rid"]/value/text').text
            started = release.find('.//field[@k="Started"]/value/text').text 
            project = release.find('.//field[@k="Project"]/value/text').text 
            variant = release.find('.//field[@k="Variant"]/value/text').text 
            libtype = release.find('.//field[@k="LibType"]/value/text').text 
            runtime = release.find('.//field[@k="Runtime"]/value/text').text 
            latest = release.find('.//field[@k="Latest"]/value/text').text 
            failures = release.find('.//field[@k="Failures"]/value/text').text 
            waived = release.find('.//field[@k="Waived"]/value/text').text 
            unwaived = release.find('.//field[@k="Unwaived"]/value/text').text 
            starttime = release.find('.//field[@k="starttime"]/value/text').text 
            stoptime = release.find('.//field[@k="stoptime"]/value/text').text 
            snapshot_config = release.find('.//field[@k="snapshot_config"]/value/text').text 
            try:
                rel_config = release.find('.//field[@k="Configuration Released"]/value/text').text 
            except AttributeError:
                rel_config = ''

            resources = []
            if get_arc_resources:
                resource_search = "| savedsearch arc_resources_for_request_id request_id=%s" %  rid
                resource_result = self.dashboard.run_query(resource_search, starttime, stoptime)
                self.logger.debug("Got ARC resource info XML: %s" % resource_result)
                if resource_result is not None:
                    resource_root = ET.fromstring(resource_result)
                    for entry in resource_root.iter('result'):
                        audit_file = entry.find('.//field[@k="audit_file"]/value/text').text 
                        arc_resources = entry.find('.//field[@k="arc_resources"]/value/text').text 
                        resources.append( (audit_file, arc_resources) )

            releases.append( Release(rid, started, project, variant, libtype, snapshot_config, runtime, latest, failures, waived, unwaived, rel_config, starttime, stoptime, resources) )

        self.logger.debug("Found these releases:\n%s" % releases)

        return releases

    def release_commandline(self, rid, starttime, stoptime):
        """
        Retrieves a string of the abnr release command given by the user. 
        
        :param rid: the Splunk request_id value for the release of interest
        :param starttime: the beginning of the time range for finding the Splunk data
        :param stoptime: the end of the time range for finding the Splunk data
        """
        release_command_search = '| savedsearch release_command request_id="%s" | head 1 | table cmdline' % rid
        result = self.dashboard.run_query(release_command_search, starttime, stoptime)
        xml = ET.fromstring(result)
        return xml.find('.//field[@k="cmdline"]/value/text').text

    def release_errors(self, rid, starttime, stoptime):
        """
        Returns a list of the errors for the specified release.

        :param rid: the Splunk request_id value for the release of interest
        :param starttime: the beginning of the time range for finding the Splunk data
        :param stoptime: the end of the time range for finding the Splunk data
        """
        error_search = '| savedsearch release_errors request_id="%s"' % rid
        result = self.dashboard.run_query(error_search, starttime, stoptime)
        self.logger.debug(result)
        root = ET.fromstring(result)
        errors = []
        for error in root.iter('result'):
            info_type = error.find('.//field[@k="info-type"]/value/text').text
            flow = error.find('.//field[@k="flow"]/value/text').text
            subflow = error.find('.//field[@k="subflow"]/value/text').text
            topcell = error.find('.//field[@k="topcell"]/value/text').text
            status = error.find('.//field[@k="status"]/value/text').text
            err_msg = error.find('.//field[@k="Error"]/value/text').text
            errors.append( ReleaseError(info_type, flow, subflow, topcell, status, err_msg) )

        return errors

def view_releaseerror_header():
    """
    A string header row for release errors.
    """
    row1 = '\t'.join(['Flow'.ljust(10), 'Subflow'.ljust(10), 'Topcell'.ljust(10), 'Status'.ljust(10), 'Error'])
    row2 = '\t'.join(['----'.ljust(10), '-------'.ljust(10), '-------'.ljust(10), '------'.ljust(10), '-----'])
    return '\n'.join([row1, row2])

def view_releaseerror(r):
    """
    Returns a string representation of the release error.
    """
    f = r.flow.ljust(10)
    if r.subflow:
        sf = r.subflow.ljust(10)
    else:
        sf = ''.ljust(10)
    if r.topcell:
        tc = r.topcell.ljust(10)
    else:
        tc = ''.ljust(10)
    stat = r.status.ljust(10)
    e = r.err_msg

    return '\t'.join([f, sf, tc, stat, e])
