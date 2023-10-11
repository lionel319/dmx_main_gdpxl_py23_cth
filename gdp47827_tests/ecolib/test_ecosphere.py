#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/ecolib/test_ecosphere.py $
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
from dmx.ecolib.ecosphere import EcoSphere, EcoSphereError
from dmx.abnrlib.workspace import Workspace, WorkspaceError
from dmx.errorlib.exceptions import *

class TestEcoSphere(unittest.TestCase):
    def setUp(self):
        pass
        
    @classmethod
    def setUpClass(self):
        self.family = 'Falcon'
        self.EcoSphere = EcoSphere(production=False)
        self.ip = 'liotest4'
        self.icmproject = 'i10socfm'
        self.bom = 'dev'
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS/manual_pice_test_runner'
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/gdpxl_ws/lionelta_i10socfm_liotestfc1_5'
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_i10socfm_liotest4_10'
        self.wsroot = '/nfs/site/disks/da_infra_1/users/yltan/FOR_SYSTEM_TESTS_GDPXL/lionelta_Raton_Mesa_rtmliotest1_6'
        self.path = self.wsroot
        self.ws = Workspace(workspacepath=self.wsroot)

    @classmethod
    def tearDownClass(self):
        pass

    def test__get_families(self):
        families = [x.family for x in self.EcoSphere._get_families()]
        self.assertIn(self.family, families)

    def test_get_families(self):
        families = [x.family for x in self.EcoSphere.get_families()]
        self.assertIn(self.family, families)

    def test_get_families_with_family_filter(self):
        families = [x.family for x in self.EcoSphere.get_families('Falcon')]
        self.assertIn(self.family, families)

    def test_has_family(self):
        self.assertTrue(self.EcoSphere.has_family(self.family))        

    def test_has_no_family(self):
        self.assertFalse(self.EcoSphere.has_family('doesnotexist'))

    def test_get_family(self):
        self.assertEqual('Falcon', self.EcoSphere.get_family('Falcon').family)            

    def test_get_non_existing_family(self):
        with self.assertRaises(DmxErrorRMFM01):
            self.EcoSphere.get_family('doesnotexist')

    def test_get_family_invalid_character(self):
        with self.assertRaises(DmxErrorRMFM01):
            self.EcoSphere.get_family('@#$')        

    def test_ecosphere_with_workspace(self):
        ecosphere = EcoSphere(production=False, workspace=self.ws)
        self.assertEqual(self.ws._workspacename, ecosphere.workspace._workspacename)

    def test_ecosphere_with_workspaceroot(self):
        ecosphere = EcoSphere(production=False, workspaceroot=self.ws._workspaceroot)
        self.assertEqual(self.ws._workspacename, ecosphere.workspace._workspacename)
       
    def test_ecosphere_with_non_workspace(self):
        with self.assertRaises(DmxErrorICWS03):
            ecosphere = EcoSphere(production=False, workspace='non-workspace')

    def test_ecosphere_with_non_workspaceroot(self):
        ecosphere = EcoSphere(production=False, workspaceroot='non-workspaceroot')
        with self.assertRaises(DmxErrorICWS03):
            ecosphere.workspace

    def test_500___with_workspace(self):
        e = EcoSphere(workspaceroot=self.wsroot)
        self.assertEqual(e.workspace.project, 'Raton_Mesa')
        self.assertEqual(e.workspace.ip, 'rtmliotest1')
        self.assertEqual(e.workspace.bom, 'dev')
        self.assertEqual(os.path.abspath(e.workspace.path), self.wsroot)
        self.assertEqual(e.workspace.name, 'lionelta_Raton_Mesa_rtmliotest1_6')
        
    def test_600___get_icmprojects(self):
        e = EcoSphere(workspaceroot=self.wsroot)
        ret = e.get_icmprojects()
        self.assertIn('Raton_Mesa', ret)
        self.assertIn('g55lp', ret)


if __name__ == '__main__':
    unittest.main()
