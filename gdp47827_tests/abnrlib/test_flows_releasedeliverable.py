#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr releaselib plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_releasedeliverable.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
from mock import Mock, PropertyMock, patch
import os, sys
import logging

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.releasedeliverable import *
from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.tnrlib.waiver_file import WaiverFile
from dmx.abnrlib.releaseinputvalidation import RoadmapValidationError
from mock_ecolib import *

class TestReleaseDeliverable(unittest.TestCase):
    '''
    Tests the releaselib ABNR plugin
    '''

    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.validate_inputs')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_defined')
    @patch('dmx.abnrlib.flows.releasedeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig.search')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.get_group_details')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def setUp(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_get_group_details, mock_get_family_for_icmproject, mock_search, mock_create_from_icm, mock_libtype_defined, mock_validate_inputs, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists):
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = True
        mock_config_exists.return_value = True
        mock_libtype_defined.return_value = True
        mock_validate_inputs.return_value = None
        mock_search.return_value = True

        mock_get_family_for_icmproject.return_value = MockFamily('family')
        mock_get_family_for_thread.return_value = MockFamily('family')
        mock_get_roadmap_for_thread.return_value = MockRoadmap(MockFamily('family'), 'Roadmap')
        mock_get_group_details.return_value = {'users': [os.getenv('USER')]}
        '''
        ipspec = SimpleConfig('dev', 'project', 'variant', 'ipspec',
                              'dev', 'release', preview=True,
                              use_db=False)
        mock_create_from_icm.return_value = CompositeConfig('config', 'project', 'variant', [ipspec])
        '''
        ipspec = IcmLibrary('project', 'variant', 'ipspec', 'dev', 'release', preview=True)
        mock_create_from_icm.return_value = IcmConfig('config', 'project', 'variant', [ipspec])
        self.runner = ReleaseDeliverable('project', 'variant', 'ipspec', 'config', 'milestone',
                                       'thread', 'description', 'label', 
                                       preview=True)
        self.runner_prel = ReleaseDeliverable('project', 'variant', 'prel_a:ipspec', 'config', 'milestone',
                                       'thread', 'description', 'label', 
                                       preview=True)

    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.project_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_001___init_project_does_not_exist(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_project_exists):
        mock_project_exists.return_value = False
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'

        with self.assertRaises(ReleaseDeliverableError):
            ReleaseDeliverable('project', 'variant', 'ipspec', 'config', 'milestone',
                           'thread', 'description', 'label', preview=True,
                           )

    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.variant_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_002___init_variant_does_not_exist(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_variant_exists, mock_project_exists):
        '''
        Tests releaselib init when the variant does not exist        
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = False
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'

        with self.assertRaises(ReleaseDeliverableError):
            ReleaseDeliverable('project', 'variant', 'ipspec', 'config', 'milestone',
                           'thread', 'description', 'label', preview=True,
                           )

    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_003___init_libtype_does_not_exist(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_libtype_exists, mock_variant_exists, mock_project_exists):
        '''
        Tests releaselib init when the libtype does not exist        
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = False
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'

        with self.assertRaises(ReleaseDeliverableError):
            ReleaseDeliverable('project', 'variant', 'ipspec', 'config', 'milestone',
                           'thread', 'description', 'label', preview=True,
                           )            

    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.config_exists')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_004___init_config_does_not_exist(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists):
        '''
        Tests releaselib init when the libtype does not exist        
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = True
        mock_config_exists.return_value = False
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'

        with self.assertRaises(ReleaseDeliverableError):
            ReleaseDeliverable('project', 'variant', 'ipspec', 'config', 'milestone',
                           'thread', 'description', 'label', preview=True,
                           )                

    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.validate_inputs')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_defined')
    @patch('dmx.abnrlib.flows.releasedeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig.search')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.get_group_details')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_005___init_bad_inputs(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_get_group_details, mock_get_family_for_icmproject, mock_search, mock_create_from_icm, mock_libtype_defined, mock_validate_inputs, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists):
        '''
        Tests releaselib init when the standard inputs are bad
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = True
        mock_config_exists.return_value = True
        mock_libtype_defined.return_value = True
        mock_validate_inputs.side_effect = RoadmapValidationError('Bad roadmap')
        mock_search.return_value = True
        mock_create_from_icm.return_value = IcmConfig('config', 'project', 'variant', [])
        class Family(object):
            def __init__(self, family):
                self._family = family
                self._icmgroup = 'icmgroup'
            @property                
            def icmgroup(self):
                return self._icmgroup    
            @property                
            def family(self):
                return self._family
        mock_get_family_for_icmproject.return_value = MockFamily('family')  
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        mock_get_group_details.return_value = {'users': [os.getenv('USER')]}

        with self.assertRaises(RoadmapValidationError):
            ReleaseDeliverable('project', 'variant', 'ipspec', 'config', 'milestone',
                           'thread', 'description', 'label', preview=True,
                           )

    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_defined')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.get_group_details')
    @patch('dmx.abnrlib.flows.releasedeliverable.validate_inputs')
    def _test_006___init_thread_does_not_match_ip_roadmap(self, mock_validate_inputs, mock_get_group_details, mock_get_family_for_icmproject, mock_libtype_defined, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists):
        '''
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = True
        mock_config_exists.return_value = True
        mock_libtype_defined.return_value = True
        mock_validate_inputs.return_value = None
        mockfamily = MockFamily('family')  
        def get_roadmap(args):
            return MockRoadmap('family', 'roadmap')
        mockfamily.get_roadmap = get_roadmap
        mock_get_family_for_icmproject.return_value = mockfamily
        mock_get_group_details.return_value = {'users': [os.getenv('USER')]}
        with self.assertRaises(ReleaseDeliverableError):
            ReleaseDeliverable('project', 'variant', 'ipspec', 'config', 'milestone',
                           'thread', 'description', 'label', preview=True,
                           )      

    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_defined')
    @patch('dmx.abnrlib.flows.releasedeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig.search')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_007___init_no_ipspec(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_get_family, mock_search, mock_create_from_icm, mock_libtype_defined, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists):
        '''
        Tests that ReleaseDeliverable correctly fails if libtype != ipspec
        and ipspec is None
        '''
        mock_get_family = MockFamily('family')
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = True
        mock_config_exists.return_value = True
        mock_libtype_defined.return_value = True
        mock_search.return_value = []
        mock_create_from_icm.return_value = IcmConfig('config', 'project', 'variant', [])

        with self.assertRaises(ReleaseDeliverableError):
            ReleaseDeliverable('project', 'variant', 'libtype', 'config', 'milestone',
                                       'thread', 'description', 'label', preview=True)         


    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_defined')
    @patch('dmx.abnrlib.flows.releasedeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig.search')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_008___init_no_deliverable_to_release(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_get_family, mock_search, mock_create_from_icm, mock_libtype_defined, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists):
        '''
        Tests that ReleaseDeliverable correctly fails if libtype != ipspec
        and ipspec is None
        '''
        mock_get_family = MockFamily('family')
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = True
        mock_config_exists.return_value = True
        mock_libtype_defined.return_value = True
        mock_create_from_icm.return_value = IcmConfig('config', 'project', 'variant', [])

        def search(project, variant, libtype):
            if libtype == 'ipspec':
                return True
            else:
                return False
        mock_search.side_effect = search
                     
        with self.assertRaises(ReleaseDeliverableError):
            ReleaseDeliverable('project', 'variant', 'libtype', 'config', 'milestone',
                                       'thread', 'description', 'label', preview=True)    



    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.config_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.validate_inputs')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_defined')
    @patch('dmx.abnrlib.flows.releasedeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig.search')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.get_group_details')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_009___releaselib_runner_works_with_blank_label(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_get_group_details, mock_get_family_for_icmproject, mock_search, mock_create_from_icm, mock_libtype_defined,
                                                      mock_validate_inputs, mock_config_exists, mock_libtype_exists, mock_variant_exists, mock_project_exists):
        '''
        Tests that ReleaseDeliverable works if the label is blank
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = True
        mock_config_exists.return_value = True
        mock_libtype_defined.return_value = True
        mock_validate_inputs.return_value = None
        mock_search.return_value = True
        mock_create_from_icm.return_value = IcmConfig('config', 'project', 'variant', [])
        mock_get_family_for_icmproject.return_value = MockFamily('family')  
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'
        mock_get_group_details.return_value = {'users': [os.getenv('USER')]}

        runner = ReleaseDeliverable('project', 'variant', 'ipspec', 'config',
                                  'milestone', 'thread', 
                                  'description', '', preview=True)

        self.assertFalse(runner.label)

    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.libtype_defined')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_roadmap_for_thread')
    def test_010___releaselib_runner_fails_libtype_not_defined(self, mock_get_roadmap_for_thread, mock_get_family_for_thread, mock_libtype_defined,
                                                         mock_libtype_exists, mock_variant_exists, mock_project_exists):
        '''
        Tests that ReleaseDeliverable init fails if the libtype is not defined
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_libtype_exists.return_value = True
        mock_libtype_defined.return_value = False
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_roadmap_for_thread.return_value = 'RM1'

        with self.assertRaises(ReleaseDeliverableError):
            ReleaseDeliverable('project', 'variant', 'libtype', 'config',
                             'milestone', 'thread', 'description', '',
                             preview=True)        

    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.get_next_snap_number')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary.save')
    def _test_011___build_simple_snap_save_fails(self, mock_simple_save, mock_get_next_snap_number):
        mock_simple_save.return_value = False
        mock_get_next_snap_number.return_value = '3'
        src_config = IcmLibrary('config', 'project', 'variant', 'ipspec', 'library', 'release')

        self.assertIsNone(self.runner.build_simple_snap(src_config, 1))

    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.get_next_snap_number')
    @patch('dmx.abnrlib.flows.releasedeliverable.SimpleConfig.save')
    def _test_012___build_simple_snap_save_works(self, mock_simple_save, mock_get_next_snap_number):
        mock_simple_save.return_value = True
        mock_get_next_snap_number.return_value = '3'
        src_config = SimpleConfig('config', 'project', 'variant', 'ipspec', 'library', 'release')

        self.assertIsNotNone(self.runner.build_simple_snap(src_config, 1))            

    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig.save')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.get_next_tnr_placeholder_number')
    def test_013___build_composite_placeholder(self, mock_get_next_tnr_placeholder_number, mock_save):
        '''
        Tests the build_composite_placeholder method
        '''
        mock_save.return_value = True
        mock_get_next_tnr_placeholder_number.return_value = '3'
        src_libtype_config = IcmLibrary('project', 'variant', 'ipspec', 'library', 'config')
        snap_libtype_config = IcmLibrary('project', 'variant', 'ipspec', 'library', 'snap-config')
        src_variant_config = IcmConfig('config', 'project', 'variant', [src_libtype_config])

        snap_config = self.runner.build_composite_placeholder(src_variant_config, src_libtype_config, snap_libtype_config)
        self.assertTrue(len(snap_config.configurations), 1)
        self.assertTrue(snap_config.config, 'tnr-placeholder-variant-ipspec-4')
        for sub_config in snap_config.configurations:
            self.assertEqual(sub_config.project, snap_libtype_config.project)
            self.assertEqual(sub_config.variant, snap_libtype_config.variant)
            self.assertEqual(sub_config.libtype, snap_libtype_config.libtype)
            self.assertEqual(sub_config.library, snap_libtype_config.library)
            self.assertEqual(sub_config.name, snap_libtype_config.name)

    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    @patch('dmx.abnrlib.flows.releasedeliverable.submit_release')
    def test_014___send_to_queue_fails(self, mock_submit_release, mock_composite_config):
        '''
        Tests the send_to_queue method when it fails
        '''
        mock_config = mock_composite_config.return_value
        mock_submit_release.return_value = (False, None)
        self.assertFalse(self.runner.send_to_queue(mock_config, 'libtype'))

    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    @patch('dmx.abnrlib.flows.releasedeliverable.submit_release')
    def test_015___send_to_queue_works(self, mock_submit_release, mock_composite_config):
        '''
        Tests the send_to_queue method when it works
        '''
        mock_config = mock_composite_config.return_value
        mock_submit_release.return_value = (True, None)
        self.assertTrue(self.runner.send_to_queue(mock_config, 'libtype'))

    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseJobHandler')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    @patch('dmx.abnrlib.flows.releasedeliverable.submit_release')
    def test_016___send_to_queue_with_wait(self, mock_submit_release, mock_composite_config, mock_rel_queue_handler):
        '''
        Tests the send_to_queue method with wait when it works
        '''
        rel_config = 'REL1.0'
        mock_config = mock_composite_config.return_value
        mock_submit_release.return_value = (True, None)
        mock_q_handler = mock_rel_queue_handler.return_value
        mock_q_handler.register_callback.return_value = True
        mock_q_handler.rel_config = rel_config
        self.runner.wait = True
        self.runner.preview = False
        self.assertTrue(self.runner.send_to_queue(mock_config, 'libtype'))
        self.assertEqual(self.runner.rel_config, rel_config)

    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseJobHandler')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    @patch('dmx.abnrlib.flows.releasedeliverable.submit_release')
    def test_017___send_to_queue_with_wait_no_rel(self, mock_submit_release, mock_composite_config, mock_rel_queue_handler):
        '''
        Tests the send_to_queue method with wait when a REL is not created
        '''
        mock_config = mock_composite_config.return_value
        mock_submit_release.return_value = (True, None)
        mock_q_handler = mock_rel_queue_handler.return_value
        mock_q_handler.register_callback.return_value = True
        mock_q_handler.rel_config = None
        self.runner.wait = True
        self.runner.preview = False
        self.assertFalse(self.runner.send_to_queue(mock_config, 'libtype'))
        self.assertIsNone(self.runner.rel_config)

    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    @patch('dmx.abnrlib.flows.releasedeliverable.submit_release')
    def test_018___send_to_queue_with_waiver_files(self, mock_submit_release, mock_composite_config):
        '''
        Tests the send_to_queue method when there are waiver files
        '''
        mock_config = mock_composite_config.return_value
        mock_submit_release.return_value = (True, None)
        self.waivers = WaiverFile()
        self.assertTrue(self.runner.send_to_queue(mock_config, 'libtype'))            

    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.get_last_library_release_number')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.process_config_without_existing_release')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.get_previous_snaps_with_matching_content')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    def test_019___process_config_with_existing_release_no_snaps(self, mock_composite_config, mock_get_previous_snaps,
        mock_simple_config, mock_process_without_rel, mock_get_last_release):
        '''
        Tests the process_config_with_existing_release method when there
        are no matching REL or snap- configs. Creating the snap fails
        '''
        mock_simple = mock_simple_config.return_value
        mock_composite = mock_composite_config.return_value
        mock_get_previous_snaps.return_value = []
        mock_get_last_release.return_value = 12
        mock_process_without_rel.return_value = False
        self.assertFalse(self.runner.process_config_with_existing_release(mock_composite, mock_simple))

    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.send_to_queue')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.get_previous_snaps_with_matching_content')
    def test_020___process_config_with_existing_release_queue_fails(self, mock_get_previous_snaps,
        mock_simple_config, mock_send_to_queue, mock_composite_config):
        '''
        Tests the process_config_with_existing_release method when a matching
        snap is found but the queue fails
        '''
        mock_send_to_queue.return_value = False
        mock_composite = mock_composite_config.return_value
        mock_simple = mock_simple_config.return_value
        mock_get_previous_snaps.return_value = ['snap-1', 'snap-2']
        self.assertFalse(self.runner.process_config_with_existing_release(mock_composite, mock_simple))
        self.assertIsNone(self.runner.rel_config)

    @patch('dmx.abnrlib.flows.releasedeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.build_composite_placeholder')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.send_to_queue')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.get_previous_snaps_with_matching_content')
    def test_021___process_config_with_existing_release_queue_works(self, mock_get_previous_snaps,
        mock_simple_config, mock_send_to_queue, mock_build_composite_placeholder,
        mock_composite_config, mock_create_from_icm):
        '''
        Tests the process_config_with_existing_release method when a matching
        snap is found and the queue works
        '''
        mock_send_to_queue.return_value = True
        mock_simple = mock_simple_config.return_value
        mock_composite = mock_composite_config.return_value
        mock_create_from_icm.return_value = mock_simple
        mock_get_previous_snaps.return_value = ['snap-1', 'snap-2']
        mock_build_composite_placeholder.return_value = mock_composite_config.return_value
        self.assertTrue(self.runner.process_config_with_existing_release(mock_composite, mock_simple))

    @patch('dmx.abnrlib.flows.releasedeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.build_composite_placeholder')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.send_to_queue')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI.get_previous_snaps_with_matching_content')
    def test_022___process_config_with_existing_release_queue_fails(self, mock_get_previous_snaps,
        mock_simple_config, mock_send_to_queue, mock_build_composite_placeholder,
        mock_composite_config, mock_create_from_icm):
        '''
        Tests the process_config_with_existing_release method when a matching
        snap is found and the queue failss
        '''
        mock_send_to_queue.return_value = False
        mock_simple = mock_simple_config.return_value
        mock_composite = mock_composite_config.return_value
        mock_create_from_icm.return_value = mock_simple
        mock_get_previous_snaps.return_value = ['snap-1', 'snap-2']
        mock_build_composite_placeholder.return_value = mock_composite_config.return_value
        self.assertFalse(self.runner.process_config_with_existing_release(mock_composite, mock_simple))
        self.assertIsNone(self.runner.rel_config)

    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_thread')
    @patch('dmx.ecolib.ecosphere.EcoSphere.get_family_for_icmproject')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.build_simple_snap')
    def test_023___process_config_without_existing_release_failed_to_build_simple_snap_cfg(self,
        mock_build_simple_snap, mock_simple_config, mock_composite_config, mock_get_family_for_icmproject, mock_get_family_for_thread):
        '''
        Tests the process_config_without_existing_release method when it fails
        to build a simple snap configuration
        '''
        mock_get_family_for_thread.return_value = MockFamily('family')  
        mock_get_family_for_icmproject.return_value = MockFamily('family')  
        mock_simple = mock_simple_config.return_value
        mock_simple_2 = mock_simple_config.return_value
        mock_composite = mock_composite_config.return_value
        mock_build_simple_snap.return_value = None
        self.assertTrue(self.runner.process_config_without_existing_release(mock_composite, mock_simple, mock_simple_2))

    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.build_composite_placeholder')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.build_simple_snap')
    def test_024___process_config_without_existing_release_failed_to_build_composite_placeholder_cfg(self,
        mock_build_simple_snap, mock_simple_config, mock_build_composite_placeholder, mock_composite_config):
        '''
        Tests the process_config_without_existing_release method when it fails
        to build a composite snap configuration
        '''
        mock_simple = mock_simple_config.return_value
        mock_composite = mock_composite_config.return_value
        mock_build_simple_snap.return_value = mock_simple
        mock_build_composite_placeholder.return_value = None
        self.assertFalse(self.runner.process_config_without_existing_release(mock_composite, mock_simple, 'release'))

    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.build_composite_placeholder')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.send_to_queue')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.build_simple_snap')
    def test_025___process_config_without_existing_release_queue_fails(self,
        mock_build_simple_snap, mock_simple_config, mock_send_to_queue,
        mock_build_composite_placeholder, mock_composite_config):
        '''
        Tests the process_config_without_existing_release method when it fails
        to queue the snap configuration
        '''
        mock_send_to_queue.return_value = False
        mock_simple = mock_simple_config.return_value
        mock_composite = mock_composite_config.return_value
        mock_build_simple_snap.return_value = mock_simple
        mock_build_composite_placeholder.return_value = mock_composite
        self.assertFalse(self.runner.process_config_without_existing_release(mock_composite, mock_simple, 'release'))

    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.build_composite_placeholder')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.send_to_queue')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.build_simple_snap')
    def test_026___process_config_without_existing_release_queue_works(self,
        mock_build_simple_snap, mock_simple_config, mock_send_to_queue,
        mock_build_composite_placeholder, mock_composite_config):
        '''
        Tests the process_config_without_existing_release method when it queues
        the snap configuration
        '''
        mock_send_to_queue.return_value = True
        mock_simple = mock_simple_config.return_value
        mock_composite = mock_composite_config.return_value
        mock_build_simple_snap.return_value = mock_simple
        mock_build_composite_placeholder.return_value = mock_composite
        self.assertTrue(self.runner.process_config_without_existing_release(mock_composite, mock_simple, 'release'))

    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.process_config_without_existing_release')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig.search')
    def test_027___process_config_active_dev_outstanding_changes_fails(self, mock_search, mock_icm_cli,
        mock_process_config_without_release, mock_simple_config):
        '''
        Tests the process_config method with a config that is pointing at
        #ActiveDev, has outstanding changes but fails
        '''
        mock_simple = mock_simple_config.return_value
        mock_search.return_value = mock_simple
        mock_simple.is_active_dev.return_value = True
        mock_process_config_without_release.return_value = False
        mock_cli = mock_icm_cli.return_value
        mock_cli.add_library_release_from_activedev.return_value = '1'
        mock_cli.preview.return_value = True
        self.runner.cli = mock_cli
        self.assertEqual(self.runner.process_config(), 1)

    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.process_config_without_existing_release')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig.search')
    def test_028___process_config_active_dev_outstanding_changes_works(self, mock_search, mock_icm_cli,
        mock_process_config_without_release, mock_simple_config):
        '''
        Tests the process_config method with a config that is pointing at
        #ActiveDev, has outstanding changes and works
        '''
        mock_simple = mock_simple_config.return_value
        mock_search.return_value = mock_simple
        mock_simple.is_active_dev.return_value = True
        mock_process_config_without_release.return_value = True
        mock_cli = mock_icm_cli.return_value
        mock_cli.add_library_release_from_activedev.return_value = '1'
        mock_cli.preview.return_value = True
        self.runner.cli = mock_cli
        self.assertEqual(self.runner.process_config(), 0)

    @patch('dmx.abnrlib.flows.releasedeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.process_config_with_existing_release')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI')
    def test_029___process_config_active_dev_no_outstanding_changes_works(self, mock_icm_cli,
        mock_process_config_with_release, mock_simple_config, mock_create_from_icm):
        '''
        Tests the process_config method with a config that is pointing at
        #ActiveDev, no outstanding changes and works
        '''
        mock_simple = mock_simple_config.return_value
        mock_create_from_icm.return_value = mock_simple
        mock_simple.is_active_dev.return_value = True
        mock_process_config_with_release.return_value = True
        mock_cli = mock_icm_cli.return_value
        mock_cli.add_library_release_from_activedev.return_value = 0
        mock_cli.preview.return_value = True
        self.runner.cli = mock_cli
        self.assertEqual(self.runner.process_config(), 1)

    @patch('dmx.abnrlib.flows.releasedeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.process_config_with_existing_release')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI')
    def test_030___process_config_active_dev_no_outstanding_changes_fails(self, mock_icm_cli,
        mock_process_config_with_release, mock_simple_config, mock_create_from_icm):
        '''
        Tests the process_config method with a config that is pointing at
        #ActiveDev, no outstanding changes but fails
        '''
        mock_simple = mock_simple_config.return_value
        mock_create_from_icm.return_value = mock_simple
        mock_simple.is_active_dev.return_value = True
        mock_process_config_with_release.return_value = False
        mock_cli = mock_icm_cli.return_value
        mock_cli.add_library_release_from_activedev.return_value = 0
        mock_cli.preview.return_value = True
        self.runner.cli = mock_cli
        self.assertEqual(self.runner.process_config(), 1)

    @patch('dmx.abnrlib.flows.releasedeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.process_config_with_existing_release')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI')
    def test_031___process_config_named_release_fails(self, mock_icm_cli,
        mock_process_config_with_release, mock_simple_config, mock_composite_config,
        mock_create_from_icm):
        '''
        Tests the process_config method with a config that is pointing at
        a named release and fails
        '''
        mock_composite_config.return_value.search.return_value = [mock_simple_config.return_value]
        mock_create_from_icm.return_value = mock_composite_config.return_value
        mock_simple_config.return_value.is_active_dev.return_value = False
        mock_simple_config.return_value.lib_release.return_value = 2
        mock_process_config_with_release.return_value = False
        mock_cli = mock_icm_cli.return_value
        self.runner.cli = mock_cli
        self.assertEqual(self.runner.process_config(), 1)

    @patch('dmx.abnrlib.flows.releasedeliverable.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmConfig')
    @patch('dmx.abnrlib.flows.releasedeliverable.IcmLibrary')
    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.process_config_with_existing_release')
    @patch('dmx.abnrlib.flows.releasedeliverable.ICManageCLI')
    def test_032___process_config_named_release_works(self, mock_icm_cli,
        mock_process_config_with_release, mock_simple_config, mock_composite_config,
        mock_create_from_icm):
        '''
        Tests the process_config method with a config that is pointing at
        a named release and works
        '''
        mock_composite_config.return_value.search.return_value = [mock_simple_config.return_value]
        mock_create_from_icm.return_value = mock_composite_config.return_value
        mock_simple_config.return_value.is_active_dev.return_value = False
        mock_simple_config.return_value.lib_release.return_value = 2
        mock_process_config_with_release.return_value = True
        mock_cli = mock_icm_cli.return_value
        self.runner.cli = mock_cli
        self.assertEqual(self.runner.process_config(), 1)        

    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.process_config')
    def test_033___run_mutable_config_bad_return(self, mock_proc):
        '''
        Tests the run method when there's a problem
        '''
        mock_proc.return_value = 1
        self.assertEqual(self.runner.run(), 1)

    @patch('dmx.abnrlib.flows.releasedeliverable.ReleaseDeliverable.process_config')
    def test_034___run_mutable_config_good_return(self, mock_proc):
        '''
        Tests the run method when there's not a problem
        '''
        mock_proc.return_value = 0
        self.assertEqual(self.runner.run(), 0)        

    def test_035___propert_when_non_prel(self):
        self.assertEqual(self.runner.libtype, 'ipspec')
        self.assertEqual(self.runner.prel, None)

    def test_036___propert_when_with_prel(self):
        self.assertEqual(self.runner_prel.libtype, 'ipspec')
        self.assertEqual(self.runner_prel.prel, 'prel_a')

if __name__ == '__main__':
    if '-v' in sys.argv:
        level = logging.DEBUG
    else:
        level = logging.ERROR
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=level)
    unittest.main()
