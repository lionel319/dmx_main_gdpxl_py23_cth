#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_roadmap.py $
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

class TestDmxRoadmap(unittest.TestCase):
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        #self.env = 'env DB_FAMILY=Falcon DB_DEVICE=FM8 DMXDATA_ROOT=/p/psg/flows/common/dmxdata/12.25'
        self.env = 'env DB_FAMILY=Ratonmesa DB_DEVICE=RTM DB_THREAD=RTMrevA0 DMXDATA_ROOT=/p/psg/flows/common/dmxdata/14.4'
        #self.env = ''
        self.rc = dmx.utillib.utils.run_command
        
    def tearDown(self):
        pass

    def test_001___dmx_roadmap_thread(self):
        exitcode, stdout, stderr = self.rc('{} {} roadmap --thread '.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        self.assertIn('Wharfrock\n===============\n- WHRrevA0/0.3\n- WHRrevA0/0.5\n- WHRrevA0/0.8\n- WHRrevA0/1.0', stdout)

    def test_002___dmx_roadmap_project_type(self):
        exitcode, stdout, stderr = self.rc('{} {} roadmap --project Raton_Mesa --type'.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        self.assertIn('asic', stdout)

    def test_003___dmx_roadmap_project_type_soft_macro(self):
        exitcode, stdout, stderr = self.rc('{} {} roadmap --project Raton_Mesa --type soft_macro'.format(self.env, self.dmx), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans1 = 'arc_device: RTM\narc_family: Ratonmesa'
        ans4 = 'arc_thread: RTMrevA0'
        ans2 = 'deliverables:\n\tRTM:\n\t\t0.0: [ipspec]\n\t\t0.3: '
        ans3 = 'family: Ratonmesa\niptype: soft_macro\nroadmap: RTM\n'

        self.assertIn(ans1, stdout)
        self.assertIn(ans2, stdout)
        self.assertIn(ans3, stdout)
        self.assertIn(ans4, stdout)

    def test_004___dmx_roadmap_family_product_milestone(self):
        cmd = 'roadmap --family Ratonmesa --product RTM --milestone'
        exitcode, stdout, stderr = self.rc('{} {} {}'.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = '4.0\n5.0\n99\n'
        ans = '0.0\n0.3\n0.5\n0.8\n1.0\n99\n'
        self.assertIn(ans, stdout)

    def test_005___dmx_roadmap_family_product_type_deliverable(self):
        cmd = 'roadmap --family Ratonmesa --product RTM --type soft_macro --deliverable'
        exitcode, stdout, stderr = self.rc('{} {} {}'.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'ipspec\nreldoc\nrtl\n'
        self.assertIn(ans, stdout)

    def test_006___dmx_roadmap_family_product_type_deliverable_milestone(self):
        cmd = 'roadmap --family Ratonmesa --product RTM --type soft_macro --deliverable --milestone 0.3'
        exitcode, stdout, stderr = self.rc('{} {} {}'.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'ipspec\nreldoc\nrtl\n'
        self.assertIn(ans, stdout)


    def test_007___dmx_roadmap_project_ip_bom_product_deliverable(self):
        cmd = 'roadmap --project Raton_Mesa --ip rtmliotest1 --bom dev --product RTM --deliverable'
        exitcode, stdout, stderr = self.rc('{} {} {}'.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'ipspec'
        self.assertIn(ans, stdout)

    def test_008___dmx_roadmap_project_ip_bom_product_deliverable_ipspec_dev(self):
        cmd = 'roadmap --project Raton_Mesa --ip rtmliotest1 --bom ipspec@dev --product RTM --deliverable'
        exitcode, stdout, stderr = self.rc('{} {} {}'.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'ipspec'
        self.assertIn(ans, stdout)


    def test_009___dmx_roadmap_project_ip_bom_product_deliverable_ipspec_snap(self):
        cmd = 'roadmap --project Raton_Mesa --ip rtmliotest1 --bom ipspec@snap-fortnr_1 --product RTM --deliverable'
        exitcode, stdout, stderr = self.rc('{} {} {}'.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'ipspec'
        self.assertIn(ans, stdout)


    def test_010___dmx_roadmap_project_product_milestone_check(self):
        cmd = 'roadmap --project Raton_Mesa --product RTM --milestone 1.0 --check'
        exitcode, stdout, stderr = self.rc('{} {} {}'.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'bcmrbc/rtl/rtl_bcmrbc_check'
        ans = 'reldoc/reldoc_check'
        self.assertIn(ans, stdout)

    def test_011___dmx_roadmap_project_ip_product_milestone_deliverable_check(self):
        cmd = 'roadmap --project Raton_Mesa --ip rtmliotest1 --product RTM --milestone 1.0 --deliverable reldoc --check'
        exitcode, stdout, stderr = self.rc('{} {} {}'.format(self.env, self.dmx, cmd), maxtry=1)
        self._print(exitcode, stdout, stderr)
        ans = 'reldoc/reldoc_check'
        self.assertIn(ans, stdout)


    def _print(self, exitcode, stdout, stderr):
        print("exitcode: {}\n".format(exitcode))
        print("stdout: {}\n".format(stdout))
        print("stderr: {}\n".format(stderr))


if __name__ == '__main__':
    unittest.main()
