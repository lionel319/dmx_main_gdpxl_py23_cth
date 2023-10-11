#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_workspace_check_2.py $
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

class TestDmxWorkspaceCheck(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        self.setenv = 'env DB_THREAD=RTMrevA0 DB_DEVICE=RTM DB_FAMILY=Ratonmesa TV_MILESTONE=1.0 DMXDATA_ROOT=/p/psg/flows/common/dmxdata/14.5'
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_44'

    def tearDown(self):
        pass
    
    def test_001___dmx_workspace_check___ipspec_clean(self):
        exitcode, stdout, stderr = self.rc('cd {}; {} {} workspace check -i rtmliotest1 -d ipspec'.format(self.wsroot, self.setenv, self.dmx), maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))

        ans = 'INFO: dmx workspace check(library-level) for Raton_Mesa/rtmliotest1@dev (ipspec) completed with no errors!\n\n===================================\n============= SUMMARY =============\n===================================\nERRORS NOT WAIVED          : 0\nERRORS WITH HSDES WAIVED   : 0\nERRORS WITH CMDLINE WAIVED : 0\nERRORS WITH SW-WEB  WAIVED : 0\n===================================\nTOTAL ERRORS FOUND         : 0\n===================================\n'
        self.assertIn(ans, stdout+stderr)
        self.assertFalse(exitcode)


    def test_002___dmx_workspace_check___invalid_deliverable(self):
        exitcode, stdout, stderr = self.rc('cd {}; {} {} workspace check -i rtmliotest1 -d xxxxx'.format(self.wsroot, self.setenv, self.dmx), maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))

        ans = 'xxxxx is not a valid libtype'
        self.assertIn(ans, stdout+stderr)
        self.assertTrue(exitcode)


    def test_003___dmx_workspace_check___complib(self):
        cmd = 'cd {}; {} {} workspace check -i rtmliotest1 -d complib -t RTMrevA0 -m 1.0'.format(self.wsroot, self.setenv, self.dmx)
        print("cmd: {}".format(cmd))
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("exitcode: {}\nstdout: {}\nstderr: {}\n".format(exitcode, stdout, stderr))

        anslist = [
            '''complib type for rtmliotest1: pattern file rtmliotest1/complib/*.dmz does not exist.''',
            '''dmzcomplib  for rtmliotest1: FAILED validation of /rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml: checksum for /liotest1/rdf/no_such_file.txt failed: can not access file''',
            '''dmzcomplib  for rtmliotest1: FAILED validation of /rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml: checksum for file /rtmliotest1/ipspec/cell_names.txt (6ccdc74c1e9dfbb30a9a3d7f2db448e3) does not match audit requirement (d41d8cd98f00b204e9800998ecf8427e).Revision #1 of the file was used during checking, but an attempt was made to release revision #unknown.''',
            '''dmzcomplib  for rtmliotest1: FAILED validation of /rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml: test results indicated failure: some errors found''',
            '''TOTAL ERRORS FOUND         : 4'''
        ]
        for ans in anslist:
            self.assertIn(ans, stdout+stderr)
        self.assertTrue(exitcode)



if __name__ == '__main__':
    unittest.main()
