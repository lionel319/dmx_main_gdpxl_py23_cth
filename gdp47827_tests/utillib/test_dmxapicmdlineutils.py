#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_dmxapicmdlineutils.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import inspect
import os
import sys
import logging

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.dmxapicmdlineutils


class DmxApiCmdlineUtilsTest(unittest.TestCase):

    def setUp(self):
        self.a = dmx.utillib.dmxapicmdlineutils
        self.list = ['a', 'b', 'a c d']
        self.dict = {'name':'lionel tan', 'age': {'a':1, "b":[1,3,5]}}
        self.string = 'hello world '
        self.true = True
        self.false = False

    def tearDown(self):
        pass


    def test_010___print_output_and_parse_output___string(self):
        ret = self.a.parse_output_to_dict(self.a.print_output(self.string))
        self.assertEqual(ret, self.string)

    def test_011___print_output_and_parse_output___list(self):
        ret = self.a.parse_output_to_dict(self.a.print_output(self.list))
        self.assertEqual(ret, self.list)

    def test_012___print_output_and_parse_output___dict(self):
        ret = self.a.parse_output_to_dict(self.a.print_output(self.dict))
        self.assertEqual(ret, self.dict)

    def test_013___print_output_and_parse_output___true(self):
        ret = self.a.parse_output_to_dict(self.a.print_output(self.true))
        self.assertEqual(ret, self.true)

    def test_014___print_output_and_parse_output___false(self):
        ret = self.a.parse_output_to_dict(self.a.print_output(self.false))
        self.assertEqual(ret, self.false)



if __name__ == '__main__':
    logging.basicConfig(format="%(levelname)s: %(message)s")
    unittest.main()
