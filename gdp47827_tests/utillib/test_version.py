#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_version.py $
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
import dmx.utillib.version

class TestVersion(unittest.TestCase):
    def setUp(self):
        self.v = dmx.utillib.version.Version()

    def test_010___dmx(self):
        self.assertTrue(self.v.dmx)

    def test_010___dmxdata(self):
        self.assertTrue(self.v.dmxdata)

    def test_020___get_bundle_version(self):
        ret = self.v.get_bundle_version()
        self.assertEqual(len(ret), 2)
        self.assertTrue(ret[0])
        self.assertTrue(ret[1])

if __name__ == '__main__':
    unittest.main()
