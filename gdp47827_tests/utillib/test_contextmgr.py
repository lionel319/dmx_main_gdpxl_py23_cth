#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_contextmgr.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
import inspect
import os
import sys
import re
import logging
from mock import patch

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.utillib.contextmgr import cd, setenv, get_env_var


class TestUtils(unittest.TestCase):
    def setUp(self):
        pass

    def test_010___cd___pass(self):
        cwd = os.getcwd()
        ans = '/tmp'
        self.assertEqual(os.getcwd(), cwd)
        with cd(ans):
            self.assertEqual(os.getcwd(), ans)
        self.assertEqual(os.getcwd(), cwd)

    def test_010___cd_nested___pass(self):
        cwd = os.getcwd()
        ans = '/tmp'
        ans2 = '/nfs/site/disks'
        self.assertEqual(os.getcwd(), cwd)
        with cd(ans):
            self.assertEqual(os.getcwd(), ans)
            with cd(ans2):
                self.assertEqual(os.getcwd(), ans2)
            self.assertEqual(os.getcwd(), ans)
        self.assertEqual(os.getcwd(), cwd)

    def test_010___cd___fail(self):
        cwd = os.getcwd()
        ans = '/xxx'
        with self.assertRaises(OSError):
            with cd(ans):
                print('hahaha')

    def test_020___setenv___original_no_value_setto_got_value(self):
        d = {'aaa':'AA', 'bbb':'BB'}
        ori = get_env_var(d)
        with setenv(d):
            for k,v in list(d.items()):
                self.assertEqual(os.getenv(k), v)
        for k,v in list(ori.items()):
            self.assertEqual(os.getenv(k), v)
                
    def test_020___setenv___original_got_value_setto_got_value(self):
        d = {'GROUP':'AA'}
        ori = get_env_var(d)
        with setenv(d):
            for k,v in list(d.items()):
                self.assertEqual(os.getenv(k), v)
        for k,v in list(ori.items()):
            self.assertEqual(os.getenv(k), v)
                
    def test_020___setenv___original_no_value_setto_no_value(self):
        d = {'aaa':None}
        ori = get_env_var(d)
        with setenv(d):
            for k,v in list(d.items()):
                self.assertEqual(os.getenv(k), v)
        for k,v in list(ori.items()):
            self.assertEqual(os.getenv(k), v)
                
    def test_020___setenv___original_got_value_setto_no_value(self):
        d = {'GROUP`:':None}
        ori = get_env_var(d)
        with setenv(d):
            for k,v in list(d.items()):
                self.assertEqual(os.getenv(k), v)
        for k,v in list(ori.items()):
            self.assertEqual(os.getenv(k), v)
                


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
