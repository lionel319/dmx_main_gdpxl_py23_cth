#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_workspace_check.py $
# $Revision: #2 $
# $Change: 7444498 $
# $DateTime: 2023/01/15 19:15:53 $
# $Author: lionelta $

from __future__ import print_function
import unittest
import inspect
import os
import sys
import json

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.utils

class TestDmxWorkspaceCheck(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_44'
        self.setenv = 'env DB_THREAD=RTMrevA0 DB_DEVICE=RTM DB_FAMILY=Ratonmesa DMXDATA_ROOT=/p/psg/flows/common/dmxdata/14.4'

    def tearDown(self):
        pass
    
    def _test_001___dmx_workspace_check___goldenarccheck(self):
        cmd = """cd {}; {} {} workspace check -i rtmliotest1 -d reldoc -t RTMrevA0 -m 0.5 --nowarn --disable_checksum_check --disable_type_check --source devdb """.format(self.wsroot, self.setenv, self.dmx)
        print("Running: {}".format(cmd))
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("""
        exitcode:{}
        stdout: {}
        stderr: {}
        """.format(exitcode, stdout, stderr))
        ans1 = 'goldenarc : Failed goldenarc check for rtmliotest1/reldoc/audit/audit.rtmliotest1.reldoc.xml: Golden(dmxdata/14.4) / Used(dmxdata/latestdev)'
        self.assertIn(ans1, stdout+stderr)

    def test_002___dmx_workspace_check___typecheck(self):
        cmd = """cd {}; {} {} workspace check -i rtmliotest1 -d complib -t RTMrevA0 -m 1.0 --nowarn --disable_checksum_check --disable_goldenarc_check """.format(self.wsroot, self.setenv, self.dmx)
        print("Running: {}".format(cmd))
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("""
        exitcode:{}
        stdout: {}
        stderr: {}
        """.format(exitcode, stdout, stderr))
        ans = 'complib type for rtmliotest1: pattern file rtmliotest1/complib/*.dmz does not exist.'
        self.assertIn(ans, stdout+stderr)

    def test_003___dmx_workspace_check___checksumcheck(self):
        cmd = """cd {}; {} {} workspace check -i rtmliotest1 -d complib -t RTMrevA0 -m 1.0 --nowarn --disable_type_check --disable_goldenarc_check """.format(self.wsroot, self.setenv, self.dmx)
        print("Running: {}".format(cmd))
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("""
        exitcode:{}
        stdout: {}
        stderr: {}
        """.format(exitcode, stdout, stderr))
        ans1 = 'dmzcomplib  for rtmliotest1: FAILED validation of /rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml: checksum for /liotest1/rdf/no_such_file.txt failed: can not access file'
        ans2 = 'dmzcomplib  for rtmliotest1: FAILED validation of /rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml: checksum for file /rtmliotest1/ipspec/cell_names.txt (6ccdc74c1e9dfbb30a9a3d7f2db448e3) does not match audit requirement (d41d8cd98f00b204e9800998ecf8427e).Revision #1 of the file was used during checking, but an attempt was made to release revision #unknown.'
        self.assertIn(ans1, stdout+stderr)
        self.assertIn(ans2, stdout+stderr)

    def _test_005___dmx_workspace_check___goldenarccheck_resource_unavailable(self):
        cmd = """cd {}; {} {} workspace check -i rtmliotest1 -d complib -t RTMrevA0 -m 0.5 --nowarn --disable_checksum_check --disable_type_check --disable_result_check --source devdb""".format(self.wsroot, self.setenv, self.dmx)
        print("Running: {}".format(cmd))
        exitcode, stdout, stderr = self.rc(cmd, maxtry=1)
        print("""
        exitcode:{}
        stdout: {}
        stderr: {}
        """.format(exitcode, stdout, stderr))
        ans = 'goldenarc : Failed goldenarc check for rtmliotest1/complib/audit/audit.rtmliotest1.dmzcomplib.xml: ERROR: Resource atrenta_sgmaster/2.1_fm4_1.7a_rdc not found: type = atrenta_sgmaster, address = /2.1_fm4_1.7a_rdc'
        self.assertIn(ans, stdout+stderr)


if __name__ == '__main__':
    unittest.main()
