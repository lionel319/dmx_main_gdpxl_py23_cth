#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests syncpoint release
#

import unittest
from mock import patch
import re
import sys
import os

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.syncpointlib.syncpoint_plugins.copy import *

class TestCopy(unittest.TestCase):
    '''
    Tests the syncpoint copy plugin
    '''

    @patch('dmx.syncpointlib.syncpoint_plugins.copy.SyncpointWebAPI.syncpoint_exists')
    def test_init_source_syncpoint_does_not_exist(self, mock_syncpoint_exists):
        mock_syncpoint_exists.side_effect = [False, False]

        with self.assertRaises(CopyError):
            CopyRunner('src-syncpoint', 'dest-syncpoint', 'Testing description')

    @patch('dmx.syncpointlib.syncpoint_plugins.copy.SyncpointWebAPI.syncpoint_exists')
    def test_init_destination_syncpoint_exist(self, mock_syncpoint_exists):
        mock_syncpoint_exists.side_effect = [True, True]

        with self.assertRaises(CopyError):
            CopyRunner('src-syncpoint', 'dest-syncpoint', 'Testing description')

    @patch('dmx.syncpointlib.syncpoint_plugins.copy.SyncpointWebAPI.get_user_roles')          
    @patch('dmx.syncpointlib.syncpoint_plugins.copy.SyncpointWebAPI.syncpoint_exists')
    def test_init_user_not_fclead(self, mock_syncpoint_exists, mock_get_user_roles):
        mock_syncpoint_exists.side_effect = [True, False]
        mock_get_user_roles.return_value = ['sslead']
        
        with self.assertRaises(CopyError):
            CopyRunner('src-syncpoint', 'dest-syncpoint', 'Testing description')

    
if __name__ == '__main__':
    unittest.main()
