#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_workspace_list.py $
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
import dmx.utillib.contextmgr

class TestDmxWorkspaceList(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        #self.setsite = 'env DB_THREAD=ACRrevA0 DB_DEVICE=ACR DB_FAMILY=Acomarock DMXDATA_ROOT=/p/psg/flows/common/dmxdata/14.5'
        #self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_44'

    def tearDown(self):
        pass
    
    def test_001___dmx_workspace_list___no_format(self):
        exitcode, stdout, stderr = self.rc('{} workspace list -u lionelta -p Raton_Mesa -i rtmliotest1'.format(self.dmx), maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))

        self.assertIn('lionelta_Raton_Mesa_rtmliotest1_6', stdout+stderr)

    def test_002___dmx_workspace_list___csv(self):
        exitcode, stdout, stderr = self.rc('{} workspace list -u lionelta -p Raton_Mesa -i rtmliotest1 -f csv'.format(self.dmx), maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        ans = 'Raton_Mesa,rtmliotest1,dev,/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/./lionelta_Raton_Mesa_rtmliotest1_6,lionelta_Raton_Mesa_rtmliotest1_6,lionelta'
        self.assertIn(ans, stdout+stderr)

    def test_003___dmx_workspace_list___json(self):
        exitcode, stdout, stderr = self.rc('{} workspace list -u lionelta -p Raton_Mesa -i rtmliotest1 -f json'.format(self.dmx), maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))
        anslist = ['''"PATH": "/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/./lionelta_Raton_Mesa_rtmliotest1_6"''', '''"WORKSPACE_NAME": "lionelta_Raton_Mesa_rtmliotest1_6"''']
        for ans in anslist:
            self.assertIn(ans, stdout+stderr)



if __name__ == '__main__':
    unittest.main()
