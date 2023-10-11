#!/usr/bin/env python
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/tnrlib/dashboard_query2.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

"""
A simple Splunk Python API (which wraps Splunk's sdk HTTP API)

For more info on how the splunk sdk works:-

* See: http://dev.splunk.com/view/python-sdk/SP-CAAAEE5#normaljob
* And: http://docs.splunk.com/Documentation/PythonSDK
* Pagination: http://dev.splunk.com/view/python-sdk/SP-CAAAER5#paginating
"""

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
import urllib, urllib2
import sys
import os

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)

from dmx.tnrlib.splunk_sdk import results as splunk_results, client as splunk_client
from dmx.tnrlib.servers import Servers
from dmx.tnrlib.waiver_file import WaiverFile, AWaiver
from dmx.utillib.utils import run_command

logger = getLogger(__name__)

class DashboardQuery2:
    """
    You must provide a valid Splunk ``userid`` and ``password``.
    """
    def __init__(self, userid, password, production=True):
        """
        You must provide a valid Splunk userid and password.
        """
        logger.debug("Initializing DashboardQuery instance...")
        if production:
            self.base_url = Servers.SPLUNK_PROD_URL
            self.base_ui_url = Servers.SPLUNK_PROD_UI_URL 
        else:
            self.base_url = Servers.SPLUNK_TEST_URL
            self.base_ui_url = Servers.SPLUNK_DEV_UI_URL 

        self.username = userid
        self.password = password

        self.CACHE = '/p/psg/flows/common/common_info/main/rel_config_splunk_request_id.txt'


        # Splunk Python API (which wraps Splunk's HTTP API)
        # See: http://dev.splunk.com/view/python-sdk/SP-CAAAEE5#normaljob
        # And: http://docs.splunk.com/Documentation/PythonSDK
        # Pagination: http://dev.splunk.com/view/python-sdk/SP-CAAAER5#paginating
        
        ### Found out that some jobs took too long to finish, ended up the DashboardQuery2 instance giving a timeout error.(http://fogbugz.altera.com/default.asp?334963)
        ### Thus, moving this connection into `self.run_query`.
        #self.splunk_sdk_service = splunk_client.connect(host=Servers.SPLUNK_PROD_HOST, scheme="https", port=Servers.SPLUNK_PROD_PORT, app='tnr', username=userid, password=password)


    def run_query(self, search_query, earliest='0', latest='now'):
        """
        Runs a given splunk ``search_query``, and returns the data(table) in a list of dictionaries.

        Example::
            
            search_query = "search index=qa | table a b c"
            retlist = self.run_query(search_query)
            retlist == [
                {'a': value_a, 'b': value_b, 'c': value_c},
                {'a': value_a, 'b': value_b, 'c': value_c},
                ...   ...   ...
            ]

        """
        logger.debug("Running query: %s" % search_query)
        self.splunk_sdk_service = splunk_client.connect(host=Servers.SPLUNK_PROD_HOST, scheme="https", port=Servers.SPLUNK_PROD_PORT, app='tnr', username=self.username, password=self.password, autologin=True)
        job = self.splunk_sdk_service.jobs.create(search_query, exec_mode='normal', earliest_time=earliest, latest_time=latest)

        while True:
            while not job.is_ready():
                pass
            stats = {"isDone": job["isDone"],
                     "doneProgress": float(job["doneProgress"])*100,
                      "scanCount": int(job["scanCount"]),
                      "eventCount": int(job["eventCount"]),
                      "resultCount": int(job["resultCount"])}
        
            logger.debug(stats)

            if stats["isDone"] == "1":
                logger.debug("Splunk Job is Done ...\n")
                break
            sleep(2)

        retlist = []
        ### Get sets of 10k results at a time
        offset = 0
        count = 10000
        while offset < stats['resultCount']:
            kwargs_paginate = {"count": count, "offset": offset}
            blocksearch_results = job.results(**kwargs_paginate)

            for result in splunk_results.ResultsReader(blocksearch_results):
                retlist.append(result)

            # Increate the offset to get the next set of results
            offset += count

        return retlist


    def get_request_id_from_pvlc(self, project, variant, libtype, config):
        ''' 
        | Returns the request_id from a given ``project, variant, libtype, config``.
        | Specify ``libtype="None"`` if you are looking for a variant's request_id.
        | Returns the ``request_id`` as a ``string``.
        '''

        ### http://pg-rdjira:8080/browse/DI-1135
        rid = self.get_request_id_from_pvlc_cache(project, variant, libtype, config)
        if rid:
            logger.debug("found rid from cache: {}".format(rid))
            return rid

        try:
            search = 'search index=qa project="{}" variant="{}" libtype="{}" release_configuration="{}" | table request_id, project, variant, libtype, release_configuration'.format(project, variant, libtype, config)
            result = self.run_query(search)
            logger.debug(result)
            return result[0].get('request_id', '')
        except Exception as e:
            logger.error("Fail finding request_id for {}/{}:{}@{}".format(project, variant, libtype, config))
            logger.error(e)
            raise


    def get_request_id_from_pvlc_cache(self, project, variant, libtype, config):
        '''
        | Search for the request_id for a given ``project, variant, libtype, config``,
        | from the cache file (self.CACHE).
        | Specify ``libtype="None"`` if you are looking for a variant's request_id.
        | If found:
        |     Returns the ``request_id`` as a ``string``.
        | else:
        |     Return ''
        |
        | Each line of the format of the CACHE file looks like this:
        |     project/variant/libtype/config/request_id
        '''
        cmd = "grep '^{}/{}/{}/{}/' {}".format(project, variant, libtype, config, self.CACHE)
        exitcode, stdout, stderr = run_command(cmd)
        rid = ''
        if not exitcode and stdout:
            ### Found
            tmp = stdout.rstrip().split('/')[-1]
            if 'error' not in tmp:
                rid = tmp
        return rid


    def get_waived_errors_from_pvlc(self, project, variant, libtype, config, with_topcell=False):
        ''' 
        | Returns all the waived errors for a given ``project, variant, libtype, config``.
        | Specify ``libtype="None"`` if you are looking for a variant's waived errors.
        | The variant level waived errors only returns the waived-errors during the variant release.
        | It does not return the waived-errors for all the libtypes/variants within the given variant.
        | If you need a complete full list of all the waived-errors of the variants and libtypes for a given pvc,
        | then you need to list out all the variants and libtypes of each of them, greb the waived for each of those,
        | and concatenate them together.
        |
        | Returns a list of dictionaries, eg::

            retlist == [
                {'project':'', 'variant':'', 'flow-libtype':'', 'RelConfig':'', 'releaser':'', 'flow':'', 
                'subflow':'', 'waiver-creator':'', 'waiver-reason':'', 'error':'', 'request_id':''},   
                ...   ...   ...
            ]

        Usage example::

            d = DashboardQuery2(...)
            retlist = d.get_waived_errors_from_pvlc('i14socnd', 'ar_lib', 'pv', 'REL3.0ND5revA__15ww321a')
            for data in retlist:
                ### Use data.get('key', '') instead of data['key'] to prevent error raised
                ### when the table returned doesn't have value for that field.
                project = data.get('project', '')
                releaser = data.get('releaser', '')
                ...   ...   ...

        '''
        rid = self.get_request_id_from_pvlc(project, variant, libtype, config)
        
        ### This search was from Kirk. It was used to get all the waived-errors hierarchically from web-dashboard.
        ### Since now that we are doing it thru script, we should be traversing thru the pvc, and find out each of the
        ### configuration, and then run the query on each of them. This should be a better solution.
        #search = 'search index=qa [| savedsearch earliest_subrelease request_id="{}"] [| savedsearch latest_subrelease request_id="{}"] variant="*" flow-libtype="*" status=waived | join request_id [| inputlookup subreleases | search request_id="{}" | eval request_id=rid | eval stoptime=starttime+duration+1] | rename user as releaser | table project variant flow-libtype RelConfig releaser flow subflow waiver-creator waiver-reason error request_id'.format(rid, rid, rid)

        search = 'search index=qa request_id={} status=waived | rename user as releaser | table project variant flow-libtype RelConfig releaser flow subflow waiver-creator waiver-reason error'.format(rid)
        if with_topcell:
            search += ' flow-topcell '

        try:
            retlist = self.run_query(search)
            return retlist
        except Exception as e:
            logger.error("Fail finding waived errors for {}/{}:{}@{}".format(project, variant, libtype, config))
            logger.error(e)
            raise


if __name__ == '__main__':
    exit(main())

