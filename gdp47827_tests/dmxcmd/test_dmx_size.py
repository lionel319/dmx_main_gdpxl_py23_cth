#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_size.py $
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

class TestDmxSize(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        
    def tearDown(self):
        pass

    def test_001___immutable_deliverable(self):
        exitcode, stdout, stderr = self.rc('{} size -p Raton_Mesa -i rtmliotest1 -d ipspec -b REL1.0RTMrevA0__22ww135a '.format(self.dmx), maxtry=1)
        print("exitcode:{}\nstdout:{}\nstderr:{}\n".format(exitcode, stdout, stderr))
        ans = 'Raton_Mesa/rtmliotest1:ipspec@dev[REL1.0RTMrevA0__22ww135a] - Size : 94 File : 4\nTotal size : 94, total file : 4\n'
        self.assertEqual(stdout, ans)

    def test_002___immutable_ip(self):
        exitcode, stdout, stderr = self.rc('{} size -p Raton_Mesa -i rtmliotest1 -b REL1.0RTMrevA0__22ww135a '.format(self.dmx), maxtry=1)
        print("exitcode:{}\nstdout:{}\nstderr:{}\n".format(exitcode, stdout, stderr))
        ans = 'Raton_Mesa/rtmliotest1:ipspec@dev[REL1.0RTMrevA0__22ww135a] - Size : 94 File : 4\nRaton_Mesa/rtmliotest1:reldoc@dev[REL1.0RTMrevA0__22ww135d] - Size : 83283 File : 5\nTotal size : 83377, total file : 9\n'
        self.assertIn(ans, stdout)

    def test_003___mutable_deliverable(self):
        exitcode, stdout, stderr = self.rc('{} size -p Raton_Mesa -i rtmliotest1 -d ipspec -b dev'.format(self.dmx), maxtry=1)
        print("exitcode:{}\nstdout:{}\nstderr:{}\n".format(exitcode, stdout, stderr))
        self.assertIn('Raton_Mesa/rtmliotest1:ipspec@dev[] - Size', stdout)

    def test_003___mutable_ip(self):
        exitcode, stdout, stderr = self.rc('{} size -p Raton_Mesa -i rtmliotest1 -b dev'.format(self.dmx), maxtry=1)
        print("exitcode:{}\nstdout:{}\nstderr:{}\n".format(exitcode, stdout, stderr))
        self.assertIn('Raton_Mesa/rtmliotest1:ipspec@dev[] - Size', stdout)


if __name__ == '__main__':
    unittest.main()
