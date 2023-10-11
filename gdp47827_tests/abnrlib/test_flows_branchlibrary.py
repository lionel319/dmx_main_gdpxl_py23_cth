#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr branchlib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_branchlibrary.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.branchlibrary import *
import dmx.ecolib.ip
import dmx.ecolib.deliverable
import dmx.ecolib.family

class TestBranchLibrary(unittest.TestCase):
    '''
    Tests the BranchLibrary class
    '''

    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.library_exists')
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.variant_exists') 
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.libtype_exists') 
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.project_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.ip.IP.get_deliverable')
    def setUp(self, mock_get_deliverable, mock_get_ip, mock_eco, mock_project_exists, mock_libtype_exists, mock_variant_exists, mock_config_exists, mock_library_exists):
        # config exists is called twice and needs to return a different
        # result each time
        config_exists_returns = [True, False]
        def side_effect(project, variant, config, libtype=None):
            return config_exists_returns.pop(0)

        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = True
        mock_config_exists.side_effect = side_effect
        mock_library_exists.return_value = False
        mock_eco.return_value = dmx.ecolib.family.Family('Falcon')

        self.runner = BranchLibrary('source_project', 'source_variant', 'libtype', 'REL_config',
                                      'target_library', preview=True)

    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.variant_exists') 
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.libtype_exists') 
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.config_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere')
    def test_init_config_does_not_exist(self, mock_eco, mock_config_exists, mock_project_exists, mock_libtype_exists, mock_variant_exists):
        '''
        Tests the __init__ method when the source config does not exist
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = True
        mock_config_exists.return_value = False
        with self.assertRaises(BranchLibraryError):
            BranchLibrary('source_project', 'source_variant', 'libtype', 'config',
                            'target_library', preview=True)

    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.variant_exists') 
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.libtype_exists') 
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.project_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere')
    def test_init_libtype_does_not_exist(self, mock_eco, mock_project_exists, mock_libtype_exists, mock_variant_exists):
        '''
        Tests the __init__ method when the source libtype does not exist
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = False
        with self.assertRaises(BranchLibraryError):
            BranchLibrary('source_project', 'source_variant', 'libtype', 'config',
                            'target_library', preview=True)
            
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.variant_exists') 
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.project_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere')
    def test_init_variant_does_not_exist(self, mock_eco, mock_project_exists, mock_variant_exists):
        '''
        Tests the __init__ method when the source variant does not exist
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = False
        with self.assertRaises(BranchLibraryError):
            BranchLibrary('source_project', 'source_variant', 'libtype', 'config',
                            'target_library', preview=True)

    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.project_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere')
    def test_init_project_does_not_exist(self, mock_eco, mock_project_exists):
        '''
        Tests the __init__ method when the source project does not exist
        '''
        mock_project_exists.return_value = False
        with self.assertRaises(BranchLibraryError):
            BranchLibrary('source_project', 'source_variant', 'libtype', 'config',
                            'target_library', preview=True)            


    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.library_exists')
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.config_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere')
    def test_init_target_library_exists(self, mock_eco, mock_config_exists, mock_library_exists):
        '''
        Tests the __init__ method when the target library already exists
        '''
        mock_config_exists.return_value = True
        mock_library_exists.return_value = True

        with self.assertRaises(BranchLibraryError):
            BranchLibrary('source_project', 'source_variant', 'libtype', 'config',
                            'target_library', preview=True)

    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.library_exists')
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.config_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere')
    def test_init_target_config_exists(self, mock_eco, mock_config_exists, mock_library_exists):
        '''
        Tests the __init__ method when the target config already exists
        '''
        mock_config_exists.return_value = True
        mock_library_exists.return_value = False

        with self.assertRaises(BranchLibraryError):
            BranchLibrary('source_project', 'source_variant', 'libtype', 'config',
                            'target_library', preview=True)

    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.library_exists')
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.branchlibrary.ICMName.is_library_name_valid')
    @patch('dmx.ecolib.ecosphere.EcoSphere')
    def test_init_invalid_branch_name(self, mock_eco, mock_is_library_name_valid, mock_config_exists,
                                      mock_library_exists):
        '''
        Tests branchlib init with an invalid branch name
        '''
        # config exists is called twice and needs to return a different
        # result each time
        config_exists_returns = [True, False]
        def side_effect(project, variant, config, libtype=None):
            return config_exists_returns.pop(0)

        mock_config_exists.side_effect = side_effect
        mock_library_exists.return_value = False
        mock_is_library_name_valid.return_value = False

        with self.assertRaises(BranchLibraryError):
            BranchLibrary('project', 'variant', 'libtype', 'config',
                            'bad target library', preview=True)

    @patch('dmx.abnrlib.flows.branchlibrary.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.branch_library')
    @patch('dmx.abnrlib.flows.branchlibrary.IcmLibrary')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.ip.IP.get_deliverable')
    def test_run_branch_fails(self, mock_get_deliverable, mock_get_ip, 
                              mock_library_config, mock_branch_library, mock_create_from_icm):
        '''
        Tests the run method when the branch fails
        '''
        mock_get_ip.return_value = dmx.ecolib.ip.IP
        deliverable = dmx.ecolib.deliverable.Deliverable
        deliverable.large = False
        deliverable.dm = 'icmanage'
        deliverable.dm_meta = dict()
        mock_get_deliverable.return_value = deliverable
        mock_create_from_icm.return_value = mock_library_config.return_value
        mock_branch_library.return_value = False
        self.assertEqual(self.runner.run(), 1)


    @patch('dmx.abnrlib.flows.branchlibrary.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.branchlibrary.ICManageCLI.branch_library')
    @patch('dmx.abnrlib.flows.branchlibrary.IcmLibrary')
    @patch('dmx.ecolib.family.Family.get_ip')
    @patch('dmx.ecolib.ip.IP.get_deliverable')
    def test_run_branch_succeeds(self, mock_get_deliverable, mock_get_ip, 
                                 mock_library_config, mock_branch_library,
                                 mock_create_from_icm):
        '''
        Tests the run method when the branch succeeds
        '''
        mock_get_ip.return_value = dmx.ecolib.ip.IP
        deliverable = dmx.ecolib.deliverable.Deliverable
        deliverable.large = False
        mock_get_deliverable.return_value = deliverable
        mock_create_from_icm.return_value = mock_library_config.return_value
        mock_branch_cfg = mock_library_config.return_value
        mock_branch_cfg.save.return_value = True
        mock_branch_library.return_value = True
        self.assertNotEqual(self.runner.run(), 1)


if __name__ == '__main__':
    unittest.main()
