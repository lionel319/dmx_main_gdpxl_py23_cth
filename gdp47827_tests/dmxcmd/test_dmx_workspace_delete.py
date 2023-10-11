#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_workspace_delete.py $
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

class TestDmxWorkspaceDelete(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        #self.setsite = 'env DB_THREAD=ACRrevA0 DB_DEVICE=ACR DB_FAMILY=Acomarock DMXDATA_ROOT=/p/psg/flows/common/dmxdata/14.5'
        #self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_44'

    def tearDown(self):
        pass
    
    def test_001___dmx_workspace_delete___does_not_exist(self):
        exitcode, stdout, stderr = self.rc('{} workspace delete -w xxxxx -y'.format(self.dmx), maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))

        self.assertIn('does not exist', stdout+stderr)

    def test_001___dmx_workspace_delete___preview(self):
        exitcode, stdout, stderr = self.rc('{} workspace delete -n -w lionelta_Raton_Mesa_rtmliotest1_14 -y'.format(self.dmx), maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))

        self.assertIn('Deleting workspace lionelta_Raton_Mesa_rtmliotest1_14 and its files', stdout+stderr)



if __name__ == '__main__':
    unittest.main()
