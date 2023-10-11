#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_ip_export.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
import inspect
import os
import sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.utils

class TestDmxIpExport(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        self.setsite = 'env DB_THREAD=ACRrevA0 DB_DEVICE=ACR DB_FAMILY=Acomarock DMXDATA_ROOT=/p/psg/flows/common/dmxdata/14.5'
        
    def tearDown(self):
        pass
    
    def test_001___dmx_ip_export___list(self):
        exitcode, stdout, stderr = self.rc('{} {} ip export -l --debug'.format(self.setsite, self.dmx), maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        ans = """Available format name for export: ['demo']"""
        self.assertIn(ans, stdout+stderr)



if __name__ == '__main__':
    unittest.main()
