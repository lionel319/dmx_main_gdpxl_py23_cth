#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests syncpoint check
#

import unittest
from mock import patch
import re
import sys
import os

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.syncpointlib.syncpoint_plugins.check import *

class TestCheck(unittest.TestCase):
    '''
    Tests the syncpoint check plugin
    '''
    @patch('dmx.syncpointlib.syncpoint_plugins.check.SyncpointWebAPI.syncpoint_exists')
    def setUp(self, mock_syncpoint_exists):
        mock_syncpoint_exists.return_value = True
        self.runner = CheckRunner('_kwlim_conflict_test_')

    @patch('dmx.syncpointlib.syncpoint_plugins.check.SyncpointWebAPI.syncpoint_exists')
    def test_init_syncpoint_does_not_exist(self, mock_syncpoint_exists):
        mock_syncpoint_exists.return_value = False

        with self.assertRaises(CheckError):
            CheckRunner('syncpoint')

if __name__ == '__main__':
    unittest.main()
