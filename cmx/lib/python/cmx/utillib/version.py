#!/usr/intel/pkgs/python3/3.9.6/bin/python3



## @addtogroup abnrlib
## @{

'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/utillib/version.py#2 $
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
        self.cmx_version = os.path.realpath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))))
        self.cmx_version = os.path.basename(self.cmx_version)
        self.dmxdata_version = os.path.basename(os.getenv("DMXDATA_ROOT", ""))

    @property
    def cmx(self):
        return self.cmx_version

    @property
    def dmx(self):
        return self.cmx_version

    @property
    def dmxdata(self):
        return self.dmxdata_version

    def print_version(self):
        print('cmx: {}'.format(self.cmx))
        print('dmxdata: {}'.format(self.dmxdata))

    def get_bundle_version(self):        
        return (self.cmx, self.dmxdata)


