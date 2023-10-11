#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/search.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $
'''
import sys
import os
import logging
import textwrap
import urllib

LOGGER = logging.getLogger(__name__)

class Confluence(object):
    '''
    env -i curl -u lionelta:Abcd.8080 -G "https://wiki.ith.intel.com/rest/api/content/search" --data-urlencode 'cql=(space=tdmainfra and text ~ "release tnr" )'
    '''

    def __init__(self, space='tdmainfra', searchstring='dmx' ):
        '''
        '''
        self.space = space
        self.searchstring = searchstring
        self.baseurl = 'https://wiki.ith.intel.com/dosearchsite.action'
        self.data = {'cql': '(space={} and text ~ "{}")'.format(self.space, self.searchstring)}
        LOGGER.debug("data:{}".format(self.data))
        self.encdata = urllib.urlencode(self.data)
        LOGGER.debug("encdata:{}".format(self.encdata))
        self.fullurl = self.baseurl + "?" + self.encdata
        LOGGER.debug("fullurl:{}".format(self.fullurl))


    def run(self):
        '''
        '''
        os.system("/usr/intel/bin/firefox {}".format(self.fullurl))


