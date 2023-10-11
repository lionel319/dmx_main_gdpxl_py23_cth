#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_overlaydeliverable.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import Mock, patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.overlaydeliverable import *
from dmx.abnrlib.icm import ICManageCLI, ICManageError
from dmx.abnrlib.icmconfig import IcmConfig, IcmConfigError
from dmx.abnrlib.icmlibrary import IcmLibrary, IcmLibraryError
from dmx.ecolib.family import Family
from dmx.ecolib.iptype import IPType
from mock_ecolib import *
from dmx.utillib.utils import is_pice_env

class simple(object):
    def __init__(self, library, activedev=True, depot='//depot...@123'):
        self._library = library
        self._config = library
        self._activedev = activedev
        self._depot = depot
    @property
    def library(self):
        return self._library
    def is_active_dev(self):
        return self._activedev
    def get_bom(self, p4):
        return self._depot
    @property
    def config(self):
        return self._config

class TestOverlayDeliverable(unittest.TestCase):
    @patch('os.path.isdir')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmconfig.IcmConfig.search')	
    @patch("dmx.ecolib.family.Family.get_ip")
    def setUp(self, mock_getip, mock_search, mock_create_from_icm, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists, mock_get_family_for_icmproject, mock_isdir):   
        # Test disabled for NX
        if not is_pice_env():
            return
        #os.environ["DB_FAMILY"] = "Falcon"
        mock_create_from_icm.side_effect = [simple('src_library'), simple('dest_library')]        
        self.runner = OverlayDeliverable('project', 'variant:libtype', 'libtype', 'src_config', 'dest_config', directory='directory', preview=True)

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmconfig.IcmConfig.search')	
    def test_init_cell_file_extension_not_txt(self, mock_search, mock_create_from_icm, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists, mock_get_family_for_icmproject):
        # Test disabled for NX
        if not is_pice_env():
            return
        mock_create_from_icm.side_effect = [simple('src_library'), simple('dest_library')]        
        with self.assertRaises(OverlayDeliverableError):
            OverlayDeliverable('project', 'variant:libtype', 'libtype', 'src_config', 'dest_config', cells = ['file.csv'], preview=True)

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmconfig.IcmConfig.search')	
    def test_init_cell_file_contains_invalid_characters(self, mock_search, mock_create_from_icm, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists, mock_get_family_for_icmproject):
        # Test disabled for NX
        if not is_pice_env():
            return
        mock_create_from_icm.side_effect = [simple('src_library'), simple('dest_library')]
        file = '/tmp/filelist.txt'
        with open(file, 'w') as f:
            f.write('cell%01')
        with self.assertRaises(OverlayDeliverableError):
            OverlayDeliverable('project', 'variant:libtype', 'libtype', 'src_config', 'dest_config', cells = [file], preview=True)
        os.remove(file)            

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmconfig.IcmConfig.search')
    def test_init_cell_file_does_not_exist(self, mock_search, mock_create_from_icm, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists, mock_get_family_for_icmproject):
        # Test disabled for NX
        if not is_pice_env():
            return
        mock_create_from_icm.side_effect = [simple('src_library'), simple('dest_library')]
        file = '/tmp/does_not_exist.txt'
        with self.assertRaises(OverlayDeliverableError):
            OverlayDeliverable('project', 'variant:libtype', 'libtype', 'src_config', 'dest_config', cells = [file], preview=True)

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmconfig.IcmConfig.search')
    def test_init_cell_cannot_contain_file_and_list_of_cells(self, mock_search, mock_create_from_icm, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists, mock_get_family_for_icmproject):
        # Test disabled for NX
        if not is_pice_env():
            return
        mock_create_from_icm.side_effect = [simple('src_library'), simple('dest_library')]
        file = '/tmp/does_not_exist.txt'
        with self.assertRaises(OverlayDeliverableError):
            OverlayDeliverable('project', 'variant:libtype', 'libtype', 'src_config', 'dest_config', cells = [file, 'cell01'], preview=True)

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmconfig.IcmConfig.search')
    @patch("dmx.ecolib.family.Family.get_ip")
    def test_init_source_and_dest_configs_are_different(self, mock_getip, mock_Search, mock_create_from_icm, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists, mock_get_family_for_icmproject):
        # Test disabled for NX
        if not is_pice_env():
            return
        mock_create_from_icm.side_effect = [simple('src_library'), simple('dest_library')]
        with self.assertRaises(OverlayDeliverableError):
            OverlayDeliverable('project', 'variant:libtype', 'libtype', 'src_config', 'src_config', preview=True)
            
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmconfig.IcmConfig.search')
    def test_init_invalid_project(self, mock_search, mock_create_from_icm, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists, mock_get_family_for_icmproject):
        # Test disabled for NX
        if not is_pice_env():
            return
        mock_create_from_icm.side_effect = [simple('src_library'), simple('dest_library')]
        mock_project_exists.return_value = False
        with self.assertRaises(OverlayDeliverableError):
            OverlayDeliverable('project', 'variant:libtype', 'libtype', 'src_config', 'dest_config', preview=True)            
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmconfig.IcmConfig.search')
    def test_init_invalid_variant(self, mock_search, mock_create_from_icm, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists, mock_get_family_for_icmproject):
        # Test disabled for NX
        if not is_pice_env():
            return
        mock_create_from_icm.side_effect = [simple('src_library'), simple('dest_library')]
        mock_variant_exists.return_value = False
        with self.assertRaises(OverlayDeliverableError):
            OverlayDeliverable('project', 'variant:libtype', 'libtype', 'src_config', 'dest_config', preview=True)                    
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmconfig.IcmConfig.search')
    def test_init_invalid_libtype(self, mock_search, mock_create_from_icm, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists, mock_get_family_for_icmproject):
        # Test disabled for NX
        if not is_pice_env():
            return
        mock_create_from_icm.side_effect = [simple('src_library'), simple('dest_library')]
        mock_libtype_exists.return_value = False
        with self.assertRaises(OverlayDeliverableError):
            OverlayDeliverable('project', 'variant:libtype', 'libtype', 'src_config', 'dest_config', preview=True)            

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmconfig.IcmConfig.search')
    def test_init_invalid_slice(self, mock_search, mock_create_from_icm, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists, mock_get_family_for_icmproject):
        # Test disabled for NX
        if not is_pice_env():
            return
        mock_create_from_icm.side_effect = [simple('src_library'), simple('dest_library')]
        mock_get_family_for_icmproject.side_effect = Exception()
        with self.assertRaises(Exception):
            OverlayDeliverable('project', 'variant:libtype', 'slice', 'src_config', 'dest_config', preview=True)            

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmconfig.IcmConfig.search')
    @patch("dmx.ecolib.family.Family.get_ip")
    def test_init_invalid_source_config(self, mock_getip, mock_search, mock_create_from_icm, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists, mock_get_family_for_icmproject):
        # Test disabled for NX
        if not is_pice_env():
            return
        mock_create_from_icm.side_effect = [simple('src_library'), simple('dest_library')]
        mock_config_exists.side_effect = [False, True]
        with self.assertRaises(OverlayDeliverableError):
            OverlayDeliverable('project', 'variant:libtype', 'libtype', 'src_config', 'dest_config', preview=True)            

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmconfig.IcmConfig.search')
    @patch("dmx.ecolib.family.Family.get_ip")
    def test_init_invalid_dest_config(self, mock_getip, mock_search, mock_create_from_icm, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists, mock_get_family_for_icmproject):
        # Test disabled for NX
        if not is_pice_env():
            return
        mock_create_from_icm.side_effect = [simple('src_library'), simple('dest_library')]
        mock_config_exists.side_effect = [True, False]
        with self.assertRaises(OverlayDeliverableError):
            OverlayDeliverable('project', 'variant:libtype', 'libtype', 'src_config', 'dest_config', preview=True)            

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.icmconfig.IcmConfig.search')
    @patch("dmx.ecolib.family.Family.get_ip")
    def test_init_source_and_dest_libraries_are_different(self, mock_getip, mock_search, mock_create_from_icm, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists, mock_get_family_for_icmproject):
        # Test disabled for NX
        if not is_pice_env():
            return
        mock_create_from_icm.side_effect = [simple('src_library'), simple('src_library', False)]
        with self.assertRaises(OverlayDeliverableError):
            OverlayDeliverable('project', 'variant:libtype', 'libtype', 'src_config', 'dest_config', preview=True)                        

    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    def _test_invalid_source_depotpath(self, mock_create_from_icm): 
        # Test disabled for NX
        if not is_pice_env():
            return  
        mock_create_from_icm.side_effect = [simple('src_library', depot='//depot'), simple('dest_library')]        
        with self.assertRaises(OverlayDeliverableError):
            self.runner.run()           

    @patch('dmx.abnrlib.flows.overlaydeliverable.ConfigFactory.create_from_icm')
    def _test_invalid_dest_depotpath(self, mock_create_from_icm): 
        # Test disabled for NX
        if not is_pice_env():
            return  
        mock_create_from_icm.side_effect = [simple('src_library'), simple('dest_library', depot='//depot')]
        with self.assertRaises(OverlayDeliverableError):
            self.runner.run()               

if __name__ == '__main__':
    unittest.main()
