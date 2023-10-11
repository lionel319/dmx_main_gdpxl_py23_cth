#!/usr/intel/pkgs/python3/3.9.6/bin/python3

# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/gdp47827_tests/cmxcmd/test_cmx_size.py $
# $Revision: #2 $
# $Change: 7461586 $
# $DateTime: 2023/01/29 18:49:14 $
# $Author: lionelta $
from __future__ import print_function
import UsrIntel.R1

import unittest
import inspect
import os
import sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import cmx.utillib.utils

class TestDmxSize(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'cmx.py')
        self.rc = cmx.utillib.utils.run_command
        
    def tearDown(self):
        pass

    def test_003___mutable_deliverable(self):
        exitcode, stdout, stderr = self.rc('{} size -p Raton_Mesa -i rtmliotest1 -d ipspec -b dev'.format(self.dmx), maxtry=1)
        print("exitcode:{}\nstdout:{}\nstderr:{}\n".format(exitcode, stdout, stderr))
        self.assertIn('Raton_Mesa/rtmliotest1:ipspec@dev[] - Size', stdout)



if __name__ == '__main__':
    unittest.main()
