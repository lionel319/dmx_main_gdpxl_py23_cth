#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/environmenterrorcode.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: List DMX errorcodes info.
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
from __future__ import print_function
from builtins import object
import os
import sys
import logging
from pprint import pprint
import json

import dmx.utillib.utils
import dmx.errorlib.errorcode


class EnvironmentErrorcode(object):

    def __init__(self, search=''):
        self.logger = logging.getLogger(__name__)
        self.search = search
        self.ec = dmx.errorlib.errorcode.ErrorCode()


    def run(self):
        self.ec.load_errorcode_data_file()
        filtered_errcodes = self.ec.get_filtered_errcodes(self.search)
        for errcode in sorted(filtered_errcodes):
            print("{}: {}".format(errcode, self.ec.data[errcode]))
        return 0


