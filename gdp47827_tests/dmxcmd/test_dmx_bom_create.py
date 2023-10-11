#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_bom_create.py $
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

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.utils

class TestDmxBomCreate(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.env = 'env DB_FAMILY=Falcon DMX_GDPSITE=intel'
        self.env = 'env DB_FAMILY=Ratonmesa DB_DEVICE=RTM DB_THREAD=RTMrevA0 '
        self.rc = dmx.utillib.utils.run_command
        self.asadmin = '--user=icmanage'
        
    def tearDown(self):
        pass

    def test_001___dmx_bom_create___got_conflict(self):
        cmd = 'bom create -p Raton_Mesa -i rtmliotest1 -b __xx__ --include Raton_Mesa/rtmliotest1@dev --include Raton_Mesa/rtmliotest1@snap-1 -n'
        exitcode, stdout, stderr = self.rc('{} {} {} '.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)

        if sys.version_info[0] < 3:
            ans = """Building configuration Raton_Mesa/rtmliotest1@__xx__\nERROR-PREVIEW: Problems detected when validating the config tree\nERROR-PREVIEW: Multiple configurations for (u'Raton_Mesa', u'rtmliotest1', u'reldoc') found:\nRaton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d\n    -> Raton_Mesa/rtmliotest1/snap-1\nRaton_Mesa/rtmliotest1/reldoc/dev\n    -> Raton_Mesa/rtmliotest1/dev\nERROR-PREVIEW: Multiple configurations for (u'Raton_Mesa', u'rtmliotest1') found:\nRaton_Mesa/rtmliotest1/dev\nRaton_Mesa/rtmliotest1/snap-1\nRaton_Mesa/rtmliotest1/__xx__\nERROR-PREVIEW: Multiple configurations for (u'Raton_Mesa', u'rtmliotest1', u'ipspec') found:\nRaton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a\n    -> Raton_Mesa/rtmliotest1/snap-1\nRaton_Mesa/rtmliotest1/ipspec/dev\n    -> Raton_Mesa/rtmliotest1/dev\nERROR-PREVIEW: Could not save Raton_Mesa/rtmliotest1/__xx__ to the IC Manage database"""
        else:
            ans = """Building configuration Raton_Mesa/rtmliotest1@__xx__\nERROR-PREVIEW: Problems detected when validating the config tree\nERROR-PREVIEW: Multiple configurations for ('Raton_Mesa', 'rtmliotest1', 'reldoc') found:\nRaton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d\n    -> Raton_Mesa/rtmliotest1/snap-1\nRaton_Mesa/rtmliotest1/reldoc/dev\n    -> Raton_Mesa/rtmliotest1/dev\nERROR-PREVIEW: Multiple configurations for ('Raton_Mesa', 'rtmliotest1') found:\nRaton_Mesa/rtmliotest1/dev\nRaton_Mesa/rtmliotest1/snap-1\nRaton_Mesa/rtmliotest1/__xx__\nERROR-PREVIEW: Multiple configurations for ('Raton_Mesa', 'rtmliotest1', 'ipspec') found:\nRaton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a\n    -> Raton_Mesa/rtmliotest1/snap-1\nRaton_Mesa/rtmliotest1/ipspec/dev\n    -> Raton_Mesa/rtmliotest1/dev\nERROR-PREVIEW: Could not save Raton_Mesa/rtmliotest1/__xx__ to the IC Manage database"""

        anslist = sorted(ans.split('\n'))

        print("=================================")
        print(ans)
        print("=================================")
        print(stderr)
        print("=================================")
        print("=================================")
        print(anslist)
        print("=================================")
        for ans in anslist:
            self.assertIn(ans, stderr)

    def test_002___dmx_bom_create___already_exist(self):
        cmd = 'bom create -p Raton_Mesa -i rtmliotest1 -b dev --include Raton_Mesa/rtmliotest1:reldoc@dev -n'
        exitcode, stdout, stderr = self.rc('{} {} {} '.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        self.assertIn("Raton_Mesa/rtmliotest1@dev already exists", stderr)

    def test_003___dmx_bom_create___cant_create_immutable(self):
        cmd = 'bom create -p Raton_Mesa -i rtmliotest1 -b snap-xxx --include i10socfm/liotestfc1:reldoc@fmx_dev -n'
        exitcode, stdout, stderr = self.rc('{} {} {} '.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'cannot use dmx bom create to create immutable configuration'
        self.assertIn(ans, stderr)

    def test_099___dmx_bom_create___successful(self):
        cmd = 'bom create -p Raton_Mesa -i rtmliotest2 -b __xx__  --include Raton_Mesa/rtmliotest2:reldoc@dev --include Raton_Mesa/rtmliotest1@dev -n'
        exitcode, stdout, stderr = self.rc('{} {} {} '.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)

        ans = '''INFO-PREVIEW: This is a preview (dry-run) mode, no changes will be made.
INFO-PREVIEW: Building configuration i10socfm/liotestfc1@__xx__
INFO-PREVIEW: Creating i10socfm/liotestfc1/__xx__
INFO-PREVIEW: Creating configuration: i10socfm/liotestfc1/__xx__
INFO-PREVIEW: gdp create configuration '/intel/i10socfm/liotestfc1/__xx__'
INFO-PREVIEW: Updating configuration i10socfm/liotestfc1@__xx__
INFO-PREVIEW: gdp update '/intel/i10socfm/liotestfc1/__xx__' --force --add '/intel/i10socfm/liotest4/fmx_dev:config' --add '/intel/i10socfm/liotestfc1/reldoc/fmx_dev:library'
INFO-PREVIEW: Configuration i10socfm/liotestfc1/__xx__ built
INFO-PREVIEW: This was a preview (dry-run) mode, no changes have been made.'''
       
        ans1 = """Building configuration Raton_Mesa/rtmliotest2@__xx__\nINFO-PREVIEW: Creating Raton_Mesa/rtmliotest2/__xx__\nINFO-PREVIEW: Creating configuration: Raton_Mesa/rtmliotest2/__xx__\nINFO-PREVIEW: gdp '--user=icmanage' create configuration '/intel/Raton_Mesa/rtmliotest2/__xx__'\nINFO-PREVIEW: Updating configuration Raton_Mesa/rtmliotest2@__xx__\nINFO-PREVIEW: gdp '--user=icmanage' update '/intel/Raton_Mesa/rtmliotest2/__xx__' --force --add '/intel/Raton_Mesa/rtmliotest2/reldoc/dev:library' --add '/intel/Raton_Mesa/rtmliotest1/dev:config'\nINFO-PREVIEW: Configuration Raton_Mesa/rtmliotest2/__xx__ built"""
        ans2 = """Building configuration Raton_Mesa/rtmliotest2@__xx__\nINFO-PREVIEW: Creating Raton_Mesa/rtmliotest2/__xx__\nINFO-PREVIEW: Creating configuration: Raton_Mesa/rtmliotest2/__xx__\nINFO-PREVIEW: gdp '--user=icmanage' create configuration '/intel/Raton_Mesa/rtmliotest2/__xx__'\nINFO-PREVIEW: Updating configuration Raton_Mesa/rtmliotest2@__xx__\nINFO-PREVIEW: gdp '--user=icmanage' update '/intel/Raton_Mesa/rtmliotest2/__xx__' --force --add '/intel/Raton_Mesa/rtmliotest1/dev:config' --add '/intel/Raton_Mesa/rtmliotest2/reldoc/dev:library'\nINFO-PREVIEW: Configuration Raton_Mesa/rtmliotest2/__xx__ built"""
        print('====================')
        print(ans1)
        print('------')
        print(ans2)
        print('------')
        print(stderr)
        print('====================')
        self.assertTrue(re.search(ans1, stderr) or re.search(ans2, stderr))


    def _print(self, exitcode, stdout, stderr):
        print("exitcode: {}\n".format(exitcode))
        print("stdout: {}\n".format(stdout))
        print("stderr: {}\n".format(stderr))


if __name__ == '__main__':
    unittest.main()
