#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_syncpoint_user_list.py $
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

class TestSyncpointUserList(unittest.TestCase):
    def setUp(self):
        self.sp = os.path.join(LIB, '..', '..', 'bin', 'syncpoint_user.py')
        self.rc = dmx.utillib.utils.run_command
        
    def tearDown(self):
        pass

    def test_001___user_does_not_exist(self):
        exitcode, stdout, stderr = self.rc('{} list -u xxxxx'.format(self.sp), maxtry=1)
        self.assertIn('User xxxxx does not exist', stdout+stderr)

    def test_002___user_has_no_role(self):
        exitcode, stdout, stderr = self.rc('{} list -u jwquah'.format(self.sp), maxtry=1)
        self.assertIn('has no roles', stdout+stderr)

    def test_003___admin_user(self):
        exitcode, stdout, stderr = self.rc('{} list -u lionelta'.format(self.sp), maxtry=1)
        self.assertIn('admin', stdout+stderr)

    def test_010___list_users_by_role(self):
        exitcode, stdout, stderr = self.rc('{} list -r admin'.format(self.sp), maxtry=1)
        self.assertIn('lionelta', stdout+stderr)

    def test_010___list_users_by_role(self):
        exitcode, stdout, stderr = self.rc('{} list -r xxxxx'.format(self.sp), maxtry=1)
        self.assertIn("invalid choice: 'xxxxx'", stdout+stderr)



if __name__ == '__main__':
    unittest.main()
