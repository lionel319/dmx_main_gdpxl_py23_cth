#!/usr/bin/env python

import unittest
from mock import patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.multireleases import *
from dmx.abnrlib.icmconfig import IcmConfig

class TestReleases(unittest.TestCase):
    @patch('dmx.abnrlib.multireleases.ReleaseLibrary')
    def test_release_simple_config_fails(self, mock_releaselib):
        '''
        Tests the release_simple_config function when releaselib  fails
        '''
        mock_run = mock_releaselib.return_value
        mock_run.run.return_value = 1
        with self.assertRaises(ReleaseError):
            release_simple_config('project', 'variant', 'libtype', 'config',
                                  'ipspec', 'milestone', 'thread', 'label',
                                  'description', True, [],
                                  False)

    @patch('dmx.abnrlib.multireleases.ReleaseLibrary')
    def test_release_simple_config_works_but_no_rel_config(self, mock_releaselib):
        '''
        Tests the release_simple_config function when releaselib  works
        but there is no rel_config
        '''
        mock_run = mock_releaselib.return_value
        mock_run.run.return_value = 0
        mock_run.rel_config = None
        with self.assertRaises(ReleaseError):
            release_simple_config('project', 'variant', 'libtype', 'config',
                                  'ipspec', 'milestone', 'thread', 'label',
                                  'description', True, [],
                                  False)

    @patch('dmx.abnrlib.multireleases.ReleaseLibrary')
    def test_release_simple_config_works(self, mock_releaselib):
        '''
        Tests the release_simple_config method when releaselib  works
        '''
        project = 'test_project'
        variant = 'test_variant'
        libtype = 'libtype'
        config = 'original_config'

        rel_config_name = 'REL-foo'
        mock_run = mock_releaselib.return_value
        mock_run.run.return_value = 0
        mock_run.rel_config = rel_config_name
        result = release_simple_config(project, variant, libtype, config,
                                       'ipspec', 'milestone', 'thread', 'label',
                                       'description', True, [],
                                       False)

        self.assertTrue(result['success'])
        self.assertEqual(result['project'], project)
        self.assertEqual(result['variant'], variant)
        self.assertEqual(result['libtype'], libtype)
        self.assertEqual(result['original_config'], config)
        self.assertEqual(result['released_config'], rel_config_name)

    @patch('dmx.abnrlib.multireleases.ReleaseLibrary')
    def test_release_simple_config_with_waiver_files(self, mock_releaselib):
        '''
        Tests the release_simple_config method with waiver files
        '''
        project = 'test_project'
        variant = 'test_variant'
        libtype = 'libtype'
        config = 'original_config'

        rel_config_name = 'REL-foo'
        mock_run = mock_releaselib.return_value
        mock_run.run.return_value = 0
        mock_run.rel_config = rel_config_name

        result = release_simple_config(project, variant, libtype, config,
                                       'ipspec', 'milestone', 'thread', 'label',
                                       'description', True, 
                                       ['file1', 'file2'], 
                                       False)

        self.assertTrue(result['success'])
        self.assertEqual(result['project'], project)
        self.assertEqual(result['variant'], variant)
        self.assertEqual(result['libtype'], libtype)
        self.assertEqual(result['original_config'], config)
        self.assertEqual(result['released_config'], rel_config_name)

    @patch('dmx.abnrlib.multireleases.ReleaseDeliverable')
    def test_release_deliverable_fails(self, mock_releasedeliverable):
        '''
        Tests the release_deliverable function when releasedeliverable  fails
        '''
        mock_run = mock_releasedeliverable.return_value
        mock_run.run.return_value = 1
        with self.assertRaises(ReleaseError):
            release_deliverable('project', 'variant', 'libtype', 'config',
                                'milestone', 'thread', 'label',
                                'description', True, False)

    @patch('dmx.abnrlib.multireleases.ReleaseDeliverable')
    def test_release_deliverable_works_but_no_rel_config(self, mock_releasedeliverable):
        '''
        Tests the release_deliverable function when releasedeliverable  works
        but there is no rel_config
        '''
        mock_run = mock_releasedeliverable.return_value
        mock_run.run.return_value = 0
        mock_run.rel_config = None
        with self.assertRaises(ReleaseError):
            release_deliverable('project', 'variant', 'libtype', 'config',
                                 'milestone', 'thread', 'label',
                                  'description', True, 
                                  False)

    @patch('dmx.abnrlib.multireleases.ReleaseDeliverable')
    def test_release_deliverable_works(self, mock_releasedeliverable):
        '''
        Tests the release_deliverable method when releasedeliverable  works
        '''
        project = 'test_project'
        variant = 'test_variant'
        libtype = 'libtype'
        config = 'original_config'

        rel_config_name = 'REL-foo'
        mock_run = mock_releasedeliverable.return_value
        mock_run.run.return_value = 0
        mock_run.rel_config = rel_config_name
        result = release_deliverable(project, variant, libtype, config,
                                      'milestone', 'thread', 'label',
                                       'description', True, 
                                       False)

        self.assertTrue(result['success'])
        self.assertEqual(result['project'], project)
        self.assertEqual(result['variant'], variant)
        self.assertEqual(result['libtype'], libtype)
        self.assertEqual(result['original_config'], config)
        self.assertEqual(result['released_config'], rel_config_name)          

    @patch('dmx.abnrlib.multireleases.build_composite_snap')
    @patch('dmx.abnrlib.multireleases.ReleaseVariant')
    def test_release_composite_config_release_fails(self, mock_releasevar,
                                                    mock_build_composite_snap):
        '''
        Tests the release_composite_config function when releasing fails.
        '''
        project = 'test_project'
        variant = 'test_variant'

        mock_build_composite_snap.return_value = IcmConfig('snap-test', project, variant,
                                                                 [], preview=True)
        mock_releaselib = mock_releasevar.return_value
        mock_releaselib.run.return_value = 1
        mock_releaselib.rel_config = None

        with self.assertRaises(ReleaseError):
            release_composite_config(project, variant, ['list', 'of', 'configs'],
                                     'milestone', 'thread', 'label',
                                     'description', True, [],
                                     False)

    @patch('dmx.abnrlib.multireleases.build_composite_snap')
    @patch('dmx.abnrlib.multireleases.ReleaseVariant')
    def test_release_composite_config_release_works(self, mock_releasevar,
                                                    mock_build_composite_snap):
        '''
        Tests the release_composite_config function when releasing works.
        '''
        project = 'test_project'
        variant = 'test_variant'
        released_config = 'REL__test'

        mock_build_composite_snap.return_value = IcmConfig('snap-test', project, variant,
                                                                 [], preview=True)
        mock_releaselib = mock_releasevar.return_value
        mock_releaselib.run.return_value = 0
        mock_releaselib.rel_config = released_config

        result = release_composite_config(project, variant, ['list', 'of', 'configs'],
                                          'milestone', 'thread', 'label',
                                          'description', True, [],
                                          False)

        self.assertTrue(result['success'])
        self.assertEqual(result['project'], project)
        self.assertEqual(result['variant'], variant)
        self.assertEqual(result['released_config'], released_config)

    @patch('dmx.abnrlib.multireleases.ConfigFactory.create_config_from_full_name')
    @patch('dmx.abnrlib.multireleases.IcmConfig.save')
    @patch('dmx.abnrlib.multireleases.ICManageCLI.get_next_snap_number')
    def test_build_composite_snap_fails(self, mock_get_next_snap_number, mock_save,
                                        mock_create_config_from_full_name):
        '''
        Tests the build_composite_snap function when building the snap fails
        '''
        mock_get_next_snap_number.return_value = 123
        mock_save.return_value = False
        mock_create_config_from_full_name.return_value = IcmConfig('REL1.0', 'other_project',
                                                                  'other_variant', [],
                                                                  preview=True)

        with self.assertRaises(ReleaseError):
            build_composite_snap('project', 'variant', ['project/variant:libtype@sub_config'], False)

    @patch('dmx.abnrlib.multireleases.ConfigFactory.create_config_from_full_name')
    @patch('dmx.abnrlib.multireleases.IcmConfig.save')
    @patch('dmx.abnrlib.multireleases.ICManageCLI.get_next_snap_number')
    def test_build_composite_snap_works(self, mock_get_next_snap_number, mock_save,
                                        mock_create_config_from_full_name):
        '''
        Tests the build_composite_snap function when building the snap works
        '''
        snap_number = 123
        mock_get_next_snap_number.return_value = snap_number
        mock_save.return_value = True
        snap_config_name = 'snap-{}'.format(snap_number)
        mock_create_config_from_full_name.return_value = IcmConfig('REL1.0', 'other_project',
                                                                  'other_variant', [],
                                                                  preview=True)

        snap = build_composite_snap('project', 'variant', ['project/variant:libtype@sub_config'], False)
        self.assertEqual(snap.config, snap_config_name)

if __name__ == '__main__':
    unittest.main()
