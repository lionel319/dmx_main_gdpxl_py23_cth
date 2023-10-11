#!/usr/bin/env python

## @addtogroup abnrlib
## @{

'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/version.py#2 $
$Change: 7480145 $
$DateTime: 2023/02/12 17:58:36 $
$Author: lionelta $

Description: Contains standard libraries for interacting with the roadmap

Author: Lee Cartwright

Copyright (c) Altera Corporation 2014
All rights reserved.
'''
from __future__ import print_function

from builtins import str
from builtins import object
import os
import sys

class VersionError(Exception): pass

class Version(object):
    def __init__(self, debug=False):
        self.dmx_version = os.path.realpath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
        self.dmx_version = os.path.basename(self.dmx_version)
        self.dmxdata_version = os.path.basename(os.getenv("DMXDATA_ROOT", ""))

    @property
    def dmx(self):
        return self.dmx_version

    @property
    def dmxdata(self):
        return self.dmxdata_version

    def print_version(self):
        print('dmx: {}'.format(self.dmx))
        print('dmxdata: {}'.format(self.dmxdata))

    def get_bundle_version(self):        
        return (self.dmx, self.dmxdata)

