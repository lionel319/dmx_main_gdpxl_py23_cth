#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_syncpoint_list.py $
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

class TestSyncpointList(unittest.TestCase):
    def setUp(self):
        self.sp = os.path.join(LIB, '..', '..', 'bin', 'syncpoint.py')
        self.rc = dmx.utillib.utils.run_command
        self.name = 'PHYS4.0ND0revA0'
        
    def tearDown(self):
        pass

    def test_001___list_all_syncpoint(self):
        exitcode, stdout, stderr = self.rc('{} list'.format(self.sp), maxtry=1)
        self.assertIn(self.name, stdout+stderr)

    def test_002___list_pvc_of_given_syncpoint(self):
        exitcode, stdout, stderr = self.rc('{} list -s {}'.format(self.sp, self.name), maxtry=1)
        self.assertIn('i14socnd/vseam_common@REL5.0ND0revA0__19ww194a', stdout+stderr)

    def test_003___list_specific_pvc_of_a_syncpoint(self):
        exitcode, stdout, stderr = self.rc('{} list -s {} -p i14socnd -v vseam_common --force'.format(self.sp, self.name), maxtry=1)
        self.assertIn('REL5.0ND0revA0__19ww194a', stdout+stderr)

    def test_004___syncpoint_does_not_exist(self):
        exitcode, stdout, stderr = self.rc('{} list -s xxxxx'.format(self.sp), maxtry=1)
        self.assertIn('Syncpoint xxxxx does not exist', stdout+stderr)



if __name__ == '__main__':
    unittest.main()
