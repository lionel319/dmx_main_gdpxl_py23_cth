#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/errorlib/errorcode.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: This library loads the cfgfiles/errorcodes.json into a dictionary.
'''
import os
import sys
import logging
from pprint import pprint
import json

class ErrorCode(object):

    def __init__(self, infile=None):
        self.logger = logging.getLogger(__name__)
        if infile:
            self.infile = infile
        else:
            self.infile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'cfgfiles', 'errorcodes.json')

        self.data = {}
        self.rawdata = {}


    def load_errorcode_data_file(self, force=False):
        ''' Load in the errorcode.json file into the self.data dict.

        If file has been loaded before, skip.
        If force=True, reload input file regardless of previous state.
        '''
        if force or not self.rawdata:
            with open(self.infile) as f:
                self.logger.debug("Loading in datafile: {}".format(self.infile))
                self.rawdata = json.load(f)
            self.data = self.convert_rawdata_to_errcode_kvp_data()
        return self.data


    def convert_rawdata_to_errcode_kvp_data(self):
        comment = '#'
        ret = {}
        for parent  in self.rawdata:
            for suberr in self.rawdata[parent]:
                if comment in suberr:
                    continue
                for code in self.rawdata[parent][suberr]:
                    if comment in code:
                        continue
                    errcode = '{}{}{}'.format(parent, suberr, code)
                    ret[errcode] = self.rawdata[parent][suberr][code]
        return ret

    
    def get_filtered_errcodes(self, searchstring=''):
        retlist = []
        for errcode in self.data:
            if searchstring in errcode:
                retlist.append(errcode)
        return retlist



