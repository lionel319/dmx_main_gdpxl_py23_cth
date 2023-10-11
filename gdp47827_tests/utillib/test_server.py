#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_server.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import inspect
import os
import sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.server

class TestServer(unittest.TestCase):

    def setUp(self):
        self.s = dmx.utillib.server.Server()
        self.working = self.s.get_working_server()

    def test_010___get_list_of_sc_servers(self):
        ret = self.s.get_list_of_sc_servers()
        print(ret)
        self.assertTrue(ret)

    def test_020___get_list_of_servers(self):
        ret = self.s.get_list_of_servers()
        print(ret)
        self.assertTrue(ret)

    def test_030___get_working_server(self):
        ret = self.s.get_working_server()
        print(ret)
        self.assertTrue(ret)

    def test_040___is_server_available___true(self):
        ret = self.s.is_server_available(self.working)
        print(ret)
        self.assertTrue(ret)

    def test_040___is_server_available___false(self):
        ret = self.s.is_server_available('xxx')
        print(ret)
        self.assertFalse(ret)

    def test_050___is_server_alive___true(self):
        ret = self.s.is_server_alive(self.working)
        print(ret)
        self.assertTrue(ret)

    def test_050___is_server_alive___false(self):
        ret = self.s.is_server_alive('xxx')
        print(ret)
        self.assertFalse(ret)

    def test_060___is_arc_available___true(self):
        ret = self.s.is_arc_available(self.working)
        print(ret)
        self.assertTrue(ret)

    def test_060___is_arc_available___false(self):
        ret = self.s.is_arc_available('xxx')
        print(ret)
        self.assertFalse(ret)


if __name__ == '__main__':
    unittest.main()
