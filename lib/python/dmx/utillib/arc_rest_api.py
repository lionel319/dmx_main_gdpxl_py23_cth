#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/arc_rest_api.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Class to instantiate connection to servers

Author: Kevin Lim Khai - Wern

Copyright (c) Altera Corporation 2016
All rights reserved.
'''

import os
import logging
import sys
import time
import dmx.utillib.utils 
from dmx.errorlib.exceptions import *
import json

class ArcRestApiError(Exception): pass

class ArcRestApi(object):

    BASEURL = {
        'sc':  'http://psg-sc-arc-web01.sc.intel.com/arc/api',
        'png': 'http://psg-png-arc-web01.png.intel.com/arc/api',
    }
    RETRY = 5
    WAITTIME = 10

    def __init__(self, site='sc', baseurl=''):
        if baseurl:
            self.baseurl = baseurl
        else:
            self.baseurl = self.BASEURL[site]
        self.logger = logging.getLogger(__name__)
        retried = 0


    def get_job(self, arcjobid):
        request = 'job/{}/'.format(arcjobid)
        cmd = self.get_curl_command(request)
        return self.run_command(cmd)

    def get_jobtree(self, arcjobid):
        request = 'jobtree/{}/'.format(arcjobid)
        cmd = self.get_curl_command(request)
        return self.run_command(cmd)

    def get_resource(self, resource):
        pass
   
    def get_curl_command(self, request):
        finalcmd = 'env -i curl {}'.format(self.get_request_url(request))
        return finalcmd

    def get_request_url(self, request):
        return '{}/{}'.format(self.baseurl, request)

    def run_command(self, cmd):
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)

        self.logger.debug("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
       
        retried = 0
        while True:
            if not exitcode:
                jsondata = self.string_to_json(stdout)
                if jsondata:
                    return jsondata

            if retried >= self.RETRY:
                return None
            else:
                retried += 1
                self.logger.info("Problem running arc_rest_api. Trying again ... {} time out of {} ...".format(retried, self.RETRY))
                time.sleep(self.WAITTIME)

    def string_to_json(self, text):
        '''
        parse text to json object.

        if successful:
            return json object
        else:
            return None
        '''
        try:
            data = json.loads(text)
            return data
        except Exception as e:
            self.logger.debug("Failed parsing string_to_json: {}".format(text))
            return None


