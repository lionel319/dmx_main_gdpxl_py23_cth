
"""
A simple wrapper for the Splunk HTTP API.
"""
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import object
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
from xml.dom import minidom
from xml.etree import ElementTree as ET
import logging
import sys
from argparse import ArgumentParser
from datetime import datetime
from getpass import getpass

from dmx.tnrlib.servers import Servers

logger = logging.getLogger(__name__)

SPLUNK_REST_API_MAXROWS = 50000 # Configured in the Splunk server [restapi]

class DashboardQuery(object):
    """
    Query the ICE QA Dashboard.
    """
    def __init__(self, userid, password, production=True):
        """
        You must provide a valid Splun userid and password.
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

        self.set_session_key()

    def set_session_key(self):
        """
        Creates and stores the Splunk HTTP API session key which 
        must be provided with each HTTP request.
        """
        # Login and get the session key
        url = self.base_url + '/servicesNS/%s/search/auth/login' % (self.username)
        logger.debug("Session request URL: %s" % url)
        data = urllib.parse.urlencode({'username': self.username, 'password': self.password})
        request = urllib.request.Request(url, data)
        server_content = urllib.request.urlopen(request)

        self.session_key = minidom.parseString(server_content.read()).\
                getElementsByTagName('sessionKey')[0].childNodes[0].nodeValue
        logger.debug("Session Key: %s" % self.session_key)

    def submit_query(self, search_query, earliest='0', latest='now'):
        """
        Submits the search to Splunk.  
        Returns a search id.
        Use get_results() to read the results.
        """
        url = self.base_url + '/services/search/jobs/'
        # POST request
        #data = urllib.urlencode({'search': search_query, 'earliest_time':earliest, 'latest_time':latest, 'output_mode': 'xml', 'count': SPLUNK_REST_API_MAXROWS})

        # "long" searches fail, while short ones work fine.  Grr...

        data = urllib.parse.urlencode({'search': search_query})
        headers = { 'Authorization': ('Splunk %s' % self.session_key), 'Content-Type': 'application/x-www-form-urlencoded'}
        logger.debug(url)
        logger.debug(data)
        logger.debug(headers)
        request = urllib.request.Request(url, data, headers)
        try:
            response = urllib.request.urlopen(request)
            search_id = minidom.parseString(response.read()). getElementsByTagName('sid')[0].childNodes[0].nodeValue
            logger.debug('Generated search id %s for search: "%s"' % (search_id, search_query))

            return search_id
        except:
            logger.error("Got an exception while submitting search to Splunk.")
            raise


    def get_results(self, search_id):
        """
        Blocks until the Splunk search finishes, at which point it
        gathers all the results into a single list 
        """
        # TODO: wait until search job is done....

        # GET request
        url = self.base_url + '/services/search/jobs/%s/results/?count=0' % search_id
        headers = { 'Authorization': ('Splunk %s' % self.session_key)}
        logger.debug(url)
        logger.debug(headers)
        request = urllib.request.Request(url)
        for (k,v) in list(headers.items()):
            request.add_header(k, v)
        try:
            response = urllib.request.urlopen(request)
            return response.read()
        except:
            logger.error("Got an exception while retrieving seearch results from Splunk.")
            raise

    def run_query(self, search_query, earliest='0', latest='now', max_rows=100):
        """
        Search_query is a Splunk search string.
        earliest and latest are Splunk time indicators (like in the Search GUI)
        max_rows is the maximum number of rows to return (0 means no limit)
        Returns results as Splunk API XML.

        Note that Splunk limits the number of rows returned in several situations.
        First, the REST API itself imposes a 50,000 row limit for oneshot searches.
        If you need to return more than 50,000 records, use the submit_query()
        and get_results() methods instead of this method.

        Second, if you use the Splunk search "sort" command by default it truncates
        at 10,000 records. You have use "sort 0" instead to prevent this.  Sub-searches
        are another area where Splunk will limit the number of records returned.
        You should ensure your search returns everything you think it should on large 
        data sets by testing it manually before deploying a utility users will trust.
        """
        logger.debug("Running query: %s" % search_query)

        # Perform a search
        url = self.base_url + '/servicesNS/%s/tnr/search/jobs/oneshot' % (self.username)
        #data = urllib.urlencode({'search': search_query, 'earliest_time':earliest, 'latest_time':latest, 'output_mode': 'xml', 'exec_mode':'oneshot'} )
        data = urllib.parse.urlencode({'search': search_query, 'earliest_time':earliest, 'latest_time':latest, 'output_mode': 'xml', 'exec_mode':'oneshot', 'count': max_rows} )
        headers = { 'Authorization': ('Splunk %s' % self.session_key)}
        logger.debug(url)
        logger.debug(data)
        logger.debug(headers)
        request = urllib.request.Request(url, data, headers)

        try:
            search_results = urllib.request.urlopen(request)
            return search_results.read()
        except urllib.error.URLError as e:
            if hasattr(e, 'reason'):
                print('We failed to reach a server.')
                print('Reason: ', e.reason)
            elif hasattr(e, 'code'):
                print('The server couldn\'t fulfill the request.')
                print('Error code: ', e.code)
                print('Message: ', e.message)

    def release_details_url(self, rid, earliest, latest):
        """
        The Splunk URL for the release details dashboard page.
        """
        result = self.base_ui_url
        result += "/app/tnr/release_request_detail?form.request_id=%(rid)s&earliest=%(earliest)s&latest=%(latest)s" % locals()
        return result


