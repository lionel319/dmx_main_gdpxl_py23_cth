#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_washgroup.py $
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
import dmx.utillib.washgroup
print(dmx.utillib.washgroup.__file__)

class TestWashGroup(unittest.TestCase):

    def setUp(self):
        self.dbfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'washgroups.json')
        os.environ[dmx.utillib.washgroup.WashGroup.ENVVAR_OVERRIDE] = self.dbfile

        self.w = dmx.utillib.washgroup.WashGroup()

    def tearDown(self):
        os.environ.pop(dmx.utillib.washgroup.WashGroup.ENVVAR_OVERRIDE,'')


    def test_010___get_dbfile(self):
        self.assertEqual(self.w.get_dbfile(), self.dbfile)

    def test_100___get_groups_by_families___1_family(self):
        groups = self.w.get_groups_by_families(['falcon'])
        self.assertEqual([u'haha', u'psgfln', u'psgi10', u'psgi10arm'], groups)

    def test_101___get_groups_by_families___2_families(self):
        groups = self.w.get_groups_by_families(['falcon', 'wharfrock'])
        self.assertEqual([u'haha', u'psgfln', u'psgi10', u'psgi10arm', u'psgt16ff', u'psgwhr'], groups)

    def test_102___get_groups_by_families___2_families_and_eip_and_base(self):
        groups = self.w.get_groups_by_families(['falcon', 'wharfrock'], include_eip_groups=True, include_base_groups=True)
        self.assertEqual(sorted([u'haha', u'psgfln', u'psgi10', u'psgi10arm', u'psgt16ff', u'psgwhr', 'psgeng', 'psgintel', 'psgship', 'psgsynopsys']), groups)


    def test_200___get_groups_by_icmprojects___1_project(self):
        groups = self.w.get_groups_by_icmprojects(['Raton_Mesa'])
        self.assertEqual([u'haha', u'psgfln', u'psgi10', u'psgi10arm'], groups)

    def test_201___get_groups_by_icmprojects___2_projects(self):
        groups = self.w.get_groups_by_icmprojects(['Raton_Mesa', 'g55lp'])
        self.assertEqual([u'haha', u'psgfln', u'psgi10', u'psgi10arm'], groups)

    def _test_202___get_groups_by_icmprojects___2_projects_and_softip(self):
        groups = self.w.get_groups_by_icmprojects(['rnr', 'whr', 'SoftIP'])
        self.assertEqual(['psgrnr', 'psgship', 'psgwhr'], groups)
    
    def test_203___get_groups_by_icmprojects___2_projects_and_eip_and_base(self):
        groups = self.w.get_groups_by_icmprojects(['Raton_Mesa', 'g55lp'], include_eip_groups=True, include_base_groups=True)
        print(groups)
        self.assertEqual([u'haha', 'psgeng', u'psgfln', u'psgi10', u'psgi10arm', 'psgintel', 'psgship', 'psgsynopsys'], groups)


    def test_300___get_user_groups(self):
        groups = self.w.get_user_groups('psginfraadm')
        print("psginfraadm groups: {}".format(groups))
        self.assertIn("psgeng", groups)


    def test_301___get_user_missing_groups_from_accessing_icmprojects(self):
        groups = self.w.get_user_missing_groups_from_accessing_icmprojects('psginfraadm', ['g55lp', 'Raton_Mesa'])
        print(groups)
        print(dmx.utillib.washgroup.__file__)
        print(LIB)
        self.assertEqual(['haha'], groups)


    def _test_400___get_groups_by_pvc(self):
        groups = self.w.get_groups_by_pvc('Raton_Mesa', 'liotest1', 'snap-liotest1-multidie1')
        self.assertEqual(groups, [u'psgfln', u'psggdr', 'psgrnr', 'psgship'])

    def test_401___get_groups_by_pvc(self):
        groups = self.w.get_groups_by_pvc('Raton_Mesa', 'rtmliotest1', 'dev')
        self.assertEqual(groups, [u'haha', u'psgfln', u'psgi10', u'psgi10arm'])

    def test_450___get_user_missing_groups_from_accessing_pvc(self):
        groups = self.w.get_user_missing_groups_from_accessing_pvc('psginfraadm', 'Raton_Mesa', 'rtmliotest1', 'dev')
        self.assertEqual(groups, ['haha'])

if __name__ == '__main__':
    unittest.main()
