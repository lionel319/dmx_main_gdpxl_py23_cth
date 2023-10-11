#!/usr/bin/env python
# 2015 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr diffconfigs plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_diffconfigs.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from future import standard_library
standard_library.install_aliases()
import sys
import os
import unittest
from mock import patch
if sys.version_info[0] > 2:
    from io import StringIO
else:
    from StringIO import StringIO
import io
from tempfile import NamedTemporaryFile
from pprint import pprint

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.diffconfigs import DiffConfigs, DiffConfigsError, ConfigPair, ConfigPairError, HTMLParser, is_file_text, is_file_identical
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.config_factory import ConfigFactoryError

class TestConfigPair(unittest.TestCase):
    '''
    Tests the ConfigPair class
    '''

    def _setUp(self):
        if sys.version_info[0] > 2:
            self.iolib = io.StringIO
        else:
            self.iolib = StringIO.StringIO

    def test_generate_key(self):
        '''
        Tests the generate_key class method
        '''
        project = 'test_project'
        variant = 'test_variant'
        libtype = 'test_libtype'

        self.assertEqual(ConfigPair.generate_key(project, variant, libtype),
                                                 '{0}/{1}:{2}'.format(
                                                     project, variant,
                                                     libtype
                                                 ))

    def test_key(self):
        '''
        Tests that the key method returns the correct string
        '''
        project = 'test_project'
        variant = 'test_variant'
        libtype = 'test_libtype'

        pair = ConfigPair(project, variant, libtype)
        self.assertEqual(pair.key, ConfigPair.generate_key(project, variant, libtype))

    def test_key_with_diff_pv(self):
        '''
        Tests that the key method returns the correct string with different project/variant pair
        '''
        project = 'test_project'
        variant = 'test_variant'
        libtype = 'test_libtype'
        second_project = 'test_second_project'
        second_variant = 'test_second_variant'
        key = '{}/{}--{}/{}:{}'.format(project, variant, second_project, second_variant, libtype)
        
        self.assertEqual(key, ConfigPair.generate_key_diff_projects(project, variant, 
            second_project, second_variant, libtype))

    def test_diff_pv(self):
        project = 'test_project'
        variant = 'test_variant'
        libtype = 'test_libtype'
        second_project = 'test_second_project'
        second_variant = 'test_second_variant'
        key = '{}/{}--{}/{}:{}'.format(project, variant, second_project, second_variant, libtype)
        pair = ConfigPair('project', 'variant', 'libtype')
        pair.key = key
        
        self.assertTrue(pair.diff_pv())            
        
    def test_first_only_no_configs(self):
        '''
        Tests the first_only method when there are no configs in the ConfigPair
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        self.assertFalse(pair.first_only())

    def test_first_only_both_configs(self):
        '''
        Tests the first_only method when both configs in the ConfigPair
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        pair.first_config = 'foo'
        pair.second_config = 'bar'
        self.assertFalse(pair.first_only())

    def test_first_only_second_config_only(self):
        '''
        Tests the first_only method when there is only a second config in the ConfigPair
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        pair.second_config = 'bar'
        self.assertFalse(pair.first_only())

    def test_first_only_only_first_config(self):
        '''
        Tests the first_only method when there is only the first config
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        pair.first_config = 'foo'
        self.assertTrue(pair.first_only())

    def test_second_only_no_configs(self):
        '''
        Tests the second_only method when there are no configs in the ConfigPair
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        self.assertFalse(pair.second_only())

    def test_second_only_both_configs(self):
        '''
        Tests the second_only method when both configs in the ConfigPair
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        pair.first_config = 'foo'
        pair.second_config = 'bar'
        self.assertFalse(pair.second_only())

    def test_second_only_first_config_only(self):
        '''
        Tests the second_only method when there is only a first config in the ConfigPair
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        pair.first_config = 'bar'
        self.assertFalse(pair.second_only())

    def test_second_only_only_second_config(self):
        '''
        Tests the second_only method when there is only the second config
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        pair.second_config = 'foo'
        self.assertTrue(pair.second_only())

    def test_both_configs_no_configs(self):
        '''
        Tests the both_configs method when there are no configs
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        self.assertFalse(pair.both_configs())

    def test_both_configs_only_first_config(self):
        '''
        Tests the both_configs method when there is only a first config
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        pair.first_config = 'foo'
        self.assertFalse(pair.both_configs())

    def test_both_configs_only_second_config(self):
        '''
        Tests the both_configs method when there is only a second config
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        pair.second_config = 'bar'
        self.assertFalse(pair.both_configs())

    def test_both_configs_with_two_configs(self):
        '''
        Tests the both_configs method when both configs are set
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        pair.first_config = 'foo'
        pair.second_config = 'bar'
        self.assertTrue(pair.both_configs())

    def test_differ_not_both_configs(self):
        '''
        Tests the differ command when both configs are not set
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        with self.assertRaises(ConfigPairError):
            pair.differ()

    def test_differ_config_names_are_different(self):
        '''
        Tests the differ command when the config names are different
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        first_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'config_1',
                                    preview=True, use_db=False)
        second_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'config_2',
                                    preview=True, use_db=False)
        pair.first_config = first_config
        pair.second_config = second_config

        self.assertTrue(pair.differ())

    def test_generate_files_dict_with_exception(self):
        '''
        Test generation of files dict with exception
        '''
        pair = ConfigPair('project', 'variant', 'libtype', include_files=True)
        first_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        second_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        pair.first_config = first_config
        pair.second_config = second_config
        with self.assertRaises(Exception):
            pair.generate_files_dict()
   
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.get_dict_of_files')
    def test_generate_files_dict_only_first_files(self, mock_get_dict_of_files):
        '''
        Test generation of first files dict
        '''
        mock_get_dict_of_files.return_value = {1:1}
        pair = ConfigPair('project', 'variant', 'libtype', include_files=True)
        first_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        second_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        pair.first_config = first_config
        pair.generate_files_dict()
        self.assertEqual(pair.first_files, {1:1})
        self.assertEqual(pair.second_files, dict())   

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.get_dict_of_files')
    def test_generate_files_dict_only_second_files(self, mock_get_dict_of_files):
        '''
        Test generation of second files dict
        '''
        mock_get_dict_of_files.return_value = {1:1}
        pair = ConfigPair('project', 'variant', 'libtype', include_files=True)
        first_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        second_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        pair.second_config = first_config
        pair.generate_files_dict()
        self.assertEqual(pair.first_files, dict())
        self.assertEqual(pair.second_files, {1:1})   
 
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.get_dict_of_files')
    def test_generate_files_dict(self, mock_get_dict_of_files):
        '''
        Test generation of files dict
        '''
        mock_get_dict_of_files.return_value = {1:1}
        pair = ConfigPair('project', 'variant', 'libtype', include_files=True)
        first_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        second_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        pair.first_config = first_config
        pair.second_config = second_config
        pair.generate_files_dict()
        self.assertEqual(pair.first_files, {1:1})
        self.assertEqual(pair.second_files, {1:1})   

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.get_file_type')
    def test_is_file_text(self, mock_get_file_type):
        '''
        Test is_file_text method
        '''
        mock_get_file_type.return_value = 'text-kl'
        filespec = 'this/should/not/exist'
        self.assertTrue(is_file_text(filespec))

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.get_file_type')
    def test_is_file_not_text(self, mock_get_file_type):
        '''
        Test is_file_text method
        '''
        mock_get_file_type.return_value = 'binary'
        filespec = 'this/should/not/exist_too'
        self.assertFalse(is_file_text(filespec))

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.get_file_type')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.get_file_diff')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.get_file_digest')
    def test_is_file_identical(self, mock_get_file_digest, mock_get_file_diff, mock_get_file_type):
        '''
        Test is_file_text method
        '''
        first_filespec = 'this/should/not/exist#1'
        second_filespec = 'this/should/not/exist#1'
        self.assertTrue(is_file_identical(first_filespec, second_filespec))

        first_filespec = 'this/should/not/exist#1'
        second_filespec = 'this/should/not/exist#2'
        mock_get_file_digest.side_effect = ['abc123', 'abc123']
        self.assertTrue(is_file_identical(first_filespec, second_filespec))
        
        first_filespec = 'this/should/not/exist#2'
        second_filespec = 'this/should/not/exist#3'
        mock_get_file_diff.return_value = ''
        mock_get_file_digest.side_effect = ['abc123', 'abc124']
        mock_get_file_type.side_effect = ['text', 'text']
        self.assertTrue(is_file_identical(first_filespec, second_filespec))

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.get_file_type')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.get_file_diff')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.get_file_digest')
    def test_is_file_not_identical(self, mock_get_file_digest, mock_get_file_diff, mock_get_file_type):
        '''
        Test is_file_text method
        '''
        first_filespec = 'this/should/not/exist#3'
        second_filespec = 'this/should/not/exist#4'
        mock_get_file_digest.side_effect = ['abc123', 'abc124']
        mock_get_file_type.return_value = 'binary'
        self.assertFalse(is_file_identical(first_filespec, second_filespec))

        first_filespec = 'this/should/not/exist#4'
        second_filespec = 'this/should/not/exist#5'
        mock_get_file_digest.side_effect = ['abc123', 'abc124']
        mock_get_file_diff.return_value = 'abc'
        mock_get_file_type.return_value = 'text'
        self.assertFalse(is_file_identical(first_filespec, second_filespec))
        
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.get_dict_of_files')
    @patch('dmx.abnrlib.flows.diffconfigs.is_file_identical')
    def test_differ_files(self, mock_is_file_identical, mock_get_dict_of_files):
        '''
        Test differ files
        '''
        mock_get_dict_of_files.side_effect = [{'abc.txt':{'library':'dev', 'version':'1', 'directory':'//depot/', 'type':'text', 'filename':'abc.txt'}},
                                            {'abc.txt':{'library':'dev', 'version':'2', 'directory':'//depot/', 'type':'text', 'filename':'abc.txt'}}]
        mock_is_file_identical.return_value = False                                            
        pair = ConfigPair('project', 'variant', 'libtype', include_files=True)
        first_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        second_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        pair.first_config = first_config
        pair.second_config = second_config
        self.assertTrue(pair.differ_files(10, 10))

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.get_dict_of_files')
    @patch('dmx.abnrlib.flows.diffconfigs.is_file_identical')
    def test_differ_files_no_change(self, mock_is_file_identical, mock_get_dict_of_files):
        '''
        Test differ files no change
        '''
        mock_get_dict_of_files.side_effect = [{'abc.txt':{'version':'1', 'directory':'//depot/', 'type':'text', 'filename':'abc.txt'}},
                                            {'abc.txt':{'version':'1', 'directory':'//depot/', 'type':'text', 'filename':'abc.txt'}}]
        mock_is_file_identical.return_value = True
        pair = ConfigPair('project', 'variant', 'libtype', include_files=True)
        first_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        second_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        pair.first_config = first_config
        pair.second_config = second_config
        self.assertFalse(pair.differ_files(10, 10))

    def test_differ_config_names_are_not_different(self):
        '''
        Tests the differ command when the config names are not different
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        first_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        second_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        pair.first_config = first_config
        pair.second_config = second_config

        self.assertFalse(pair.differ())

    def test_differ_different_library(self):
        '''
        Tests the differ method when the libraries are different
        '''
        pair = ConfigPair('project', 'variant', 'libtype',
                          ignore_config_names=True)
        first_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library_one', 'release',
                                    preview=True, use_db=False)
        second_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library_two', 'release',
                                    preview=True, use_db=False)
        pair.first_config = first_config
        pair.second_config = second_config

        self.assertTrue(pair.differ())

    def test_differ_different_release(self):
        '''
        Tests the differ method when the releases are different
        '''
        pair = ConfigPair('project', 'variant', 'libtype',
                          ignore_config_names=True)
        first_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', '#ActiveDev',
                                    preview=True, use_db=False)
        second_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', '10',
                                    preview=True, use_db=False)
        pair.first_config = first_config
        pair.second_config = second_config

        self.assertTrue(pair.differ())

    def test_generate_and_print_diff_both_configs_with_difference(self):
        '''
        Tests the generate_and_print_diff method when both configs are set and they differ
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        first_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release1',
                                    preview=True, use_db=False)
        second_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release2',
                                    preview=True, use_db=False)
        pair.first_config = first_config
        pair.second_config = second_config

        with patch('sys.stdout', new_callable=StringIO) as new_stdout:
            pair.generate_and_print_diff(2, 2)
            output = new_stdout.getvalue()
            lines = output.splitlines()
            self.assertEqual(len(lines), 1)
            self.assertTrue(lines[0].startswith('! {0}/{1}/{2}'.format(pair.project, pair.variant, pair.libtype)))

    def test_generate_and_print_diff_both_configs_no_difference(self):
        '''
        Tests the generate_and_print_diff method when both configs are set and they don't differ
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        first_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        second_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        pair.first_config = first_config
        pair.second_config = second_config

        with patch('sys.stdout', new_callable=StringIO) as new_stdout:
            pair.generate_and_print_diff(2, 2)
            output = new_stdout.getvalue()
            self.assertFalse(output)

    def test_generate_and_print_diff_only_first_config(self):
        '''
        Tests the generate_and_print_diff method when only the first config is set
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        first_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        pair.first_config = first_config

        with patch('sys.stdout', new_callable=StringIO) as new_stdout:
            pair.generate_and_print_diff(2, 2)
            output = new_stdout.getvalue()
            self.assertTrue(output.startswith('- {0}/{1}/{2}'.format(pair.project, pair.variant, pair.libtype)))

    def test_generate_and_print_diff_only_second_config(self):
        '''
        Tests the generate_and_print_diff method when only the second config is set
        '''
        pair = ConfigPair('project', 'variant', 'libtype')
        second_config = IcmLibrary(pair.project, pair.variant,
                                    pair.libtype, 'library', 'release',
                                    preview=True, use_db=False)
        pair.second_config = second_config

        with patch('sys.stdout', new_callable=StringIO) as new_stdout:
            pair.generate_and_print_diff(2, 2)
            output = new_stdout.getvalue()
            self.assertTrue(output.startswith('+ {0}/{1}/{2}'.format(pair.project, pair.variant, pair.libtype)))

class TestHTMLParser(unittest.TestCase):
    '''
    Tests the HTMLParser class
    '''

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigPair.generate_files_dict')
    def test_build_lookup_dict(self, mock_generate_files_dict, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        mock_create_from_icm.return_value = None
        mock_generate_files_dict.return_value = None
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True

        # Mock up look_up pair
        project = 'project'
        variant = 'variant'
        identical_libtype = 'identical_libtype'
        first_only_libtype = 'first_libtype'
        second_only_libtype = 'second_libtype'
        different_libtype = 'different_libtype'

        parent_simple_config = IcmLibrary(project, variant, 
                                            'parent_simple_config', 'library', 'parent_simple_config',
                                            preview=True, use_db=False)
        parent_simple_configs = [parent_simple_config]
        parent_config = IcmConfig('parent_config', project, variant, parent_simple_configs, 
                                        preview=True)
        identical_config = IcmLibrary(project, variant, identical_libtype,
                                        'library', 'identical_config', preview=True, use_db=False)
        first_only_config = IcmLibrary(project, variant, first_only_libtype,
                                         'library', 'first_only', preview=True, use_db=False)
        second_only_config = IcmLibrary(project, variant, second_only_libtype,
                                          'library', 'second_only', preview=True, use_db=False)
        first_different_config = IcmLibrary(project, variant, different_libtype,
                                              'library', 'first_diff', preview=True, use_db=False)
        second_different_config = IcmLibrary(project, variant, different_libtype,
                                               'library', 'second_diff', preview=True, use_db=False)
        first_set = set([identical_config, first_only_config, first_different_config])
        second_set = set([identical_config, second_only_config, second_different_config])
        first_config_dict = {parent_config:first_set}
        second_config_dict = {parent_config:second_set}
        first = IcmConfig('first', project, variant, 
            [identical_config, first_only_config, first_different_config], preview=True)
        second = IcmConfig('second', project, variant, 
            [identical_config, second_only_config, second_different_config], preview=True)

        mock_create_from_icm.side_effect = [first, second]

        runner = DiffConfigs(project, variant, first, second, None, None,
                                   False, False, False, False, False, False, False, True)
        lookup_table = runner.build_pair_lookup(first_config_dict, second_config_dict)
        html = HTMLParser(project, variant, 'config1', 'config2', lookup_table, False)

        html.build_lookup_dict()
        pv = '{}/{}'.format(project, variant)
        self.assertEqual([pv], list(html.lookup_dict.keys()))
        self.assertEqual('parent_config', html.lookup_dict[pv]['first_config'])
        self.assertEqual('parent_config', html.lookup_dict[pv]['second_config'])
        self.assertIsInstance(list(html.lookup_dict[pv]['ConfigPairs'].values())[0], ConfigPair)

    @patch('dmx.abnrlib.flows.diffconfigs.is_file_identical')
    def test_get_file_comparison(self, mock_is_file_identical):
        mock_is_file_identical.return_value = False

        html = HTMLParser('project', 'variant', 'config1', 'config2', None, False)
        first_files = {'path1:file1':
                        {
                            'type':'text',
                            'directory': 'path1',
                            'version' : 2,
                            'filename': 'file1'
                        },
                       'path2:file2':
                        {
                            'type':'binary',
                            'directory': 'path2',
                            'version' : 3,
                            'filename': 'file2'
                        },
                      }
        second_files = {'path1:file1':
                        {
                            'type':'text',
                            'directory': 'path1',
                            'version' : 5,
                            'filename': 'file1'
                        }
                       }
        expected = '<tr><td><font color="green">---file1</font></td><td>2</td><td>5</td><td><a href="!!{}/bin/difficm.py path1/file1#2 path1/file1#5 &">Show Diff</a></td></tr><tr><td><font color="green">---file2</font></td><td>3</td><td></td><td></td></tr>'.format(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
        
        output = html.get_file_comparison(first_files, second_files)                      
        self.assertEqual(expected, output)

    def test_is_audit(self):
        html = HTMLParser('project', 'variant', 'config1', 'config2', None, False)
        file = {'filename':'audit.abc.xml'}
        self.assertTrue(html.is_audit(file))

    def test_is_not_audit(self):
        html = HTMLParser('project', 'variant', 'config1', 'config2', None, False)
        file = {'filename':'abc.xml'}
        self.assertFalse(html.is_audit(file))

class TestDiffConfigs(unittest.TestCase):
    '''
    Tests the DiffConfigs class
    '''
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_init_diff_configs_config_does_not_exist(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the diff_configs init method when project/variant@config does not exist
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_create_from_icm.side_effect = ConfigFactoryError('bad configuration')

        with self.assertRaises(ConfigFactoryError):
            runner = DiffConfigs('project', 'variant', 'first_config', 'second_config', 
                                   None, None, True, False, False, False, False, False, 
                                   False, True)

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    def test_init_diff_configs_variant_does_not_exist(self, mock_variant_exists, mock_project_exists):
        '''
        Tests the diff_configs init method when project/variant does not exist
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = False

        with self.assertRaises(DiffConfigsError):
            runner = DiffConfigs('project', 'variant', 'first_config', 'second_config', 
                                   None, None, True, False, False, False, False, False, 
                                   False, True)
            
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    def test_init_diff_configs_project_does_not_exist(self, mock_project_exists):
        '''
        Tests the diff_configs init method when project does not exist
        '''
        mock_project_exists.return_value = False

        with self.assertRaises(DiffConfigsError):
            runner = DiffConfigs('project', 'variant', 'first_config', 'second_config', 
                                   None, None, True, False, False, False, False, False, 
                                   False, True)            

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_init_diff_configs_second_config_does_not_exist(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the diff_configs init method when second_project/second_variant@second_config does not exist
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_create_from_icm.side_effect = [True, ConfigFactoryError('bad configuration')]

        with self.assertRaises(ConfigFactoryError):
            runner = DiffConfigs('project', 'variant', 'first_config', 'second_config', 
                                   'second_project', 'second_variant', True, False, False, False, False, False, 
                                   False, True)

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_init_diff_configs_second_variant_does_not_exist(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the diff_configs init method when second_project/second_variant does not exist
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.side_effect = [True, False]
        mock_create_from_icm.side_effect = [True, ConfigFactoryError('bad configuration')]

        with self.assertRaises(DiffConfigsError):
            runner = DiffConfigs('project', 'variant', 'first_config', 'second_config', 
                                   'second_project', 'second_variant', True, False, False, False, False, False, 
                                   False, True)
            
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_init_diff_configs_second_project_does_not_exist(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the diff_configs init method when second_project does not exist
        '''
        mock_project_exists.side_effect = [True, False]
        mock_variant_exists.return_value = True
        mock_create_from_icm.side_effect = [True, ConfigFactoryError('bad configuration')]

        with self.assertRaises(DiffConfigsError):
            runner = DiffConfigs('project', 'variant', 'first_config', 'second_config', 
                                  'second_project', 'second_variant', True, False, False, False, False, False, 
                                   False, True)                   

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_init_diff_configs_second_config_of_first_project_does_not_exist(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the diff_configs init method when project/variant@second_config does not exist
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_create_from_icm.side_effect = [True, ConfigFactoryError('bad configuration')]

        with self.assertRaises(ConfigFactoryError):
            runner = DiffConfigs('project', 'variant', 'first_config', 'second_config', 
                                   None, None, True, False, False, False, False, False, 
                                   False, True)

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_init_diff_configs_wrong_deliverable_exist(self, mock_create_from_icm, mock_variant_exists, mock_project_exists, mock_libtype_exists):
        '''
        Tests the diff_configs init method when wrong deliverable input
        '''
        mock_libtype_exists.return_value = True
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_create_from_icm.side_effect = ConfigFactoryError('bad configuration') 

        with self.assertRaises(ConfigFactoryError):
            runner = DiffConfigs('project', 'variant', 'first_config', 'second_config', 
                                   None, None, True, False, False, False, False, False, 
                                   False, True, 'WrongDeliverable' )

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_init_diff_configs_deliverable_does_not_exist(self, mock_create_from_icm, mock_variant_exists, mock_project_exists, mock_libtype_exists):
        '''
        Tests the diff_configs init method when deliverable does not exists
        '''
        mock_libtype_exists.return_value = True
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_create_from_icm.return_value = IcmConfig('config', 'project', 'variant',
                                                            [], preview=True)
 
        self.assertTrue(DiffConfigs('project', 'variant', 'first_config', 'second_config', None, None, True, False, False, False, False, False, False, True ))

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.libtype_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_init_diff_configs_deliverable_exist(self, mock_create_from_icm, mock_variant_exists, mock_project_exists, mock_libtype_exists):
        '''
        Tests the diff_configs init method when deliverable exists
        '''
        mock_libtype_exists.return_value = True
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        mock_create_from_icm.return_value = IcmConfig('config', 'project', 'variant',
                                                            [], preview=True)
 
        self.assertTrue(DiffConfigs('project', 'variant', 'first_config', 'second_config', None, None, True, False, False, False, False, False, False, True, 'lint' ))


    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.diffconfigs.DiffConfigs.tkdiff_configs')
    def test_diff_configs_tkdiff_mode(self, mock_tkdiff_configs, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the diff_configs method in tkdiff mode
        '''
        mock_tkdiff_configs.return_value = None
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True

        mock_create_from_icm.return_value = IcmConfig('config', 'project', 'variant',
                                                            [], preview=True)

        runner = DiffConfigs('project', 'variant', 'first_config', 'second_config', 
                                   None, None, True, False, False, False, False, False, 
                                   False, True)
        runner.diff_configs()

        self.assertEqual(mock_tkdiff_configs.call_count, 1)

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    @patch('dmx.abnrlib.flows.diffconfigs.DiffConfigs.build_pair_lookup')
    @patch('dmx.abnrlib.flows.diffconfigs.HTMLParser')
    @patch('dmx.abnrlib.flows.diffconfigs.HTMLParser.build_lookup_dict')
    @patch('dmx.abnrlib.flows.diffconfigs.DiffConfigs.launch_html')
    def test_diff_configs_html_mode(self, mock_launch_html, mock_build_lookup_dict, mock_HTMLParser, mock_build_pair_lookup, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the diff_configs method in html mode
        '''      
        mock_launch_html.return_value = None
        mock_build_lookup_dict.return_value = None
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True

        mock_HTMLParser.return_value = HTMLParser('project', 'variant', 'config1', 'config2', [], False)
        mock_build_pair_lookup.return_value = None
        mock_create_from_icm.return_value = IcmConfig('config', 'project', 'variant',
                                                            [], preview=True)

        runner = DiffConfigs('project', 'variant', 'first_config', 'second_config',
                                   None, None, False, False, False, True, False, False, 
                                   False, True)
        runner.diff_configs()

        self.assertEqual(mock_launch_html.call_count, 1)

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_diff_configs_non_tkdiff_mode(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the diff_configs method in non-tkdiff mode
        '''
        # We need to have a very simple configuration tree for the test flow
        # For simplicity we'll have the same simple config in both trees
        project = 'project'
        variant = 'variant'
        libtype = 'libtype'
        simple_config = IcmLibrary(project, variant, libtype,
                                     'library', 'simple_config', preview=True, use_db=False)
        first_config = IcmConfig('first_config', project, variant, [simple_config],
                                       preview=True)
        second_config = IcmConfig('second_config', project, variant, [simple_config],
                                        preview=True)

        def side_effect(project, variant, config, preview, libtype):
            if config == first_config.config:
                return first_config
            elif config == second_config.config:
                return second_config
            else:
                raise Exception('Bad config name in side_effect')

        mock_create_from_icm.side_effect = side_effect
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True

        runner = DiffConfigs(project, variant, first_config.config, second_config.config,
                                   None, None, False, False, False, False, False, False, 
                                   False, True)

        with patch('sys.stdout', new_callable=StringIO) as new_stdout:
            runner.diff_configs()
            output = new_stdout.getvalue()
            # Expect output even if both configs are the same
            self.assertTrue(output)

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_build_pair_lookup(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the build_pair_lookup method
        '''        
        # We need some simple configurations to generate the lookup table from
        # We want to cover a few different scenarios:
        # Identical configs in both sets
        # Config in first but not second
        # Config in second but not first
        # Differing configs
        project = 'project'
        variant = 'variant'
        identical_libtype = 'identical_libtype'
        first_only_libtype = 'first_libtype'
        second_only_libtype = 'second_libtype'
        different_libtype = 'different_libtype'

        parent_simple_config = IcmLibrary(project, variant, 
                                            'parent_simple_config', 'library', 'parent_simple_config',
                                            preview=True, use_db=False)
        parent_simple_configs = [parent_simple_config]
        parent_config = IcmConfig('parent_config', project, variant, parent_simple_configs, 
                                        preview=True)
        identical_config = IcmLibrary(project, variant, identical_libtype,
                                        'library', 'identical_config', preview=True, use_db=False)
        first_only_config = IcmLibrary(project, variant, first_only_libtype,
                                         'library', 'first_only', preview=True, use_db=False)
        second_only_config = IcmLibrary(project, variant, second_only_libtype,
                                          'library', 'second_only', preview=True, use_db=False)
        first_different_config = IcmLibrary(project, variant, different_libtype,
                                              'library', 'first_diff', preview=True, use_db=False)
        second_different_config = IcmLibrary(project, variant, different_libtype,
                                               'library', 'second_diff', preview=True, use_db=False)
        first = IcmConfig('first', project, variant, 
            [identical_config, first_only_config, first_different_config], preview=True)
        second = IcmConfig('second', project, variant, 
            [identical_config, second_only_config, second_different_config], preview=True)

        mock_create_from_icm.side_effect = [first, second]
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True


        first_set = set([identical_config, first_only_config, first_different_config])
        second_set = set([identical_config, second_only_config, second_different_config])
        first_config_dict = {parent_config:first_set}
        second_config_dict = {parent_config:second_set}

        runner = DiffConfigs(project, variant, first, second, None, None,
                                   False, False, False, False, False, False, False, True, None)

        lookup_table = runner.build_pair_lookup(first_config_dict, second_config_dict)

        identical_key = ConfigPair.generate_key(project, variant, identical_libtype)
        first_only_key = ConfigPair.generate_key(project, variant, first_only_libtype)
        second_only_key = ConfigPair.generate_key(project, variant, second_only_libtype)
        different_key = ConfigPair.generate_key(project, variant, different_libtype)

        self.assertIn(identical_key, lookup_table)
        self.assertEqual(lookup_table[identical_key].first_config,
                         lookup_table[identical_key].second_config)
        self.assertEqual(lookup_table[identical_key].first_config, identical_config)

        self.assertIn(first_only_key, lookup_table)
        self.assertEqual(lookup_table[first_only_key].first_config, first_only_config)
        self.assertIsNone(lookup_table[first_only_key].second_config)

        self.assertIn(second_only_key, lookup_table)
        self.assertEqual(lookup_table[second_only_key].second_config, second_only_config)
        self.assertIsNone(lookup_table[second_only_key].first_config)

        self.assertIn(different_key, lookup_table)
        self.assertEqual(lookup_table[different_key].first_config, first_different_config)
        self.assertEqual(lookup_table[different_key].second_config, second_different_config)

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_write_config_file(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the write_config_file method
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True

        first_simple_config = IcmLibrary('project', 'variant', 'libtype',
                                              'library', 'first_simple', preview=True, use_db=False)
        second_simple_config = IcmLibrary('project', 'variant', 'libtype',
                                               'library', 'second_simple', preview=True, use_db=False)
        first = IcmConfig('first', 'project', 'variant', 
            [first_simple_config], preview=True)
        second = IcmConfig('second', 'project', 'variant', 
            [second_simple_config], preview=True)
        mock_create_from_icm.side_effect = [first, second]

        runner = DiffConfigs('project', 'variant', first, second, None, None,
                                   False, False, False, False, False, False, False, True)
        # Create a simple configuration to be written out
        dict = {first:[first_simple_config]}

        try:
            tf = NamedTemporaryFile(delete=False)
            runner.write_config_file(tf.name, dict)

            with open(tf.name, 'r') as fd:
                file_content = fd.readlines()

            pprint(file_content)
            self.assertEqual(len(file_content), 2)
            self.assertIn('{0}/{1}/{2}'.format(first_simple_config.project, first_simple_config.variant,
                                               first_simple_config.libtype), file_content[0])
            self.assertIn('library={0} release={1} config={2}'.format(first_simple_config.library,
                          first_simple_config.lib_release, first_simple_config.name), file_content[1])
        finally:
            if tf and os.path.exists(tf.name):
                os.unlink(tf.name)

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_build_configs_dict(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the test_build_configs_dict method
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True

        first_simple_config_1 = IcmLibrary('project', 'variant', 'libtype1',
                                             'library', 'first_simple_1', preview=True, use_db=False)
        first_simple_config_2 = IcmLibrary('project', 'variant', 'libtype2',
                                             'library', 'first_simple_2', preview=True, use_db=False)
        second_simple_config_1 = IcmLibrary('project', 'variant', 'libtype1',
                                              'library', 'second_simple_1', preview=True, use_db=False)
        second_simple_config_2 = IcmLibrary('project', 'variant', 'libtype2',
                                              'library', 'second_simple_2', preview=True, use_db=False)
        first = IcmConfig('first', 'project', 'variant', 
            [first_simple_config_1, first_simple_config_2], preview=True)
        second = IcmConfig('second', 'project', 'variant', 
            [second_simple_config_1, second_simple_config_2], preview=True)
        mock_create_from_icm.side_effect = [first, second]

        runner = DiffConfigs('project', 'variant', first, second, None, None,
                             False, False, False, False, False, False, False, True)
        config_dict = runner.build_configs_dict(first)
        self.assertEqual(set(config_dict[first]), set([first_simple_config_1, first_simple_config_2]))

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_build_configs_dict_with_filter_variants(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the test_build_configs_dict method
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True

        first_simple_config_1 = IcmLibrary('project', 'variant1', 'libtype1',
                                             'library', 'first_simple_1', preview=True, use_db=False)
        first_simple_config_2 = IcmLibrary('project', 'variant1', 'libtype2',
                                             'library', 'first_simple_2', preview=True, use_db=False)
        second_simple_config_1 = IcmLibrary('project', 'variant1', 'libtype1',
                                              'library', 'second_simple_1', preview=True, use_db=False)
        second_simple_config_2 = IcmLibrary('project', 'variant1', 'libtype2',
                                              'library', 'second_simple_2', preview=True, use_db=False)
        third_simple_config = IcmLibrary('project', 'variant2', 'libtype',
                                           'library', 'third_simple', preview=True, use_db=False)

        third = IcmConfig('third', 'project', 'variant2', 
            [third_simple_config], preview=True)
        first = IcmConfig('first', 'project', 'variant1', 
            [first_simple_config_1, first_simple_config_2, third], preview=True)
        second = IcmConfig('second', 'project', 'variant1', 
            [second_simple_config_1, second_simple_config_2], preview=True)

        mock_create_from_icm.side_effect = [first, second]
        filter_variants = ['variant1']
        runner = DiffConfigs('project', 'variant', first, second, None, None,
                                   False, False, False, False, False, filter_variants, False, True)
        config_dict = runner.build_configs_dict(first)
        self.assertEqual(set(config_dict[first]), set([first_simple_config_1, first_simple_config_2]))

        mock_create_from_icm.side_effect = [first, second]
        filter_variants = ['variant2']
        runner = DiffConfigs('project', 'variant', first, second, None, None,
                                   False, False, False, False, False, filter_variants, False, True)
        config_dict = runner.build_configs_dict(first)
        self.assertEqual(set(config_dict[third]), set([third_simple_config]))

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_build_configs_dict_with_filter_libtypes(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the test_build_configs_dict_with_filter_libtypes method
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True

        first_simple_config_1 = IcmLibrary('project', 'variant', 'libtype1',
                                             'library', 'first_simple_1', preview=True, use_db=False)
        first_simple_config_2 = IcmLibrary('project', 'variant', 'libtype2',
                                             'library', 'first_simple_2', preview=True, use_db=False)
        second_simple_config_1 = IcmLibrary('project', 'variant', 'libtype1',
                                              'library', 'second_simple_1', preview=True, use_db=False)
        second_simple_config_2 = IcmLibrary('project', 'variant', 'libtype2',
                                              'library', 'second_simple_2', preview=True, use_db=False)
        first = IcmConfig('first', 'project', 'variant', 
            [first_simple_config_1, first_simple_config_2], preview=True)
        second = IcmConfig('second', 'project', 'variant', 
            [second_simple_config_1, second_simple_config_2], preview=True)

        mock_create_from_icm.side_effect = [first, second]
        filter_libtypes = ['libtype1']
        runner = DiffConfigs('project', 'variant', first, second, None, None,
                                   False, False, False, False, False, False, filter_libtypes, True)
        config_dict = runner.build_configs_dict(first)
        self.assertEqual(set(config_dict[first]), set([first_simple_config_1]))


    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_100___is_large_data_deliverable(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        ''' '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        first_simple_config_1 = IcmLibrary('project', 'variant', 'libtype1',
                                             'library', 'first_simple_1', preview=True, use_db=False)
        first_simple_config_2 = IcmLibrary('project', 'variant', 'libtype2',
                                             'library', 'first_simple_2', preview=True, use_db=False)
        second_simple_config_1 = IcmLibrary('project', 'variant', 'libtype1',
                                              'library', 'second_simple_1', preview=True, use_db=False)
        second_simple_config_2 = IcmLibrary('project', 'variant', 'libtype2',
                                              'library', 'second_simple_2', preview=True, use_db=False)
        first = IcmConfig('first', 'project', 'variant', 
            [first_simple_config_1, first_simple_config_2], preview=True)
        second = IcmConfig('second', 'project', 'variant', 
            [second_simple_config_1, second_simple_config_2], preview=True)
        mock_create_from_icm.side_effect = [first, second]
        runner = DiffConfigs('project', 'variant', first, second, None, None,
                                   False, False, False, False, False, False, None, True)
        ret = runner.is_large_data_deliverable('ipspec')
        self.assertFalse(ret, 'family:{}/libtype:ipspec FAILED! (expecting False)'.format(os.getenv("DB_FAMILY")))

        ret = runner.is_large_data_deliverable('rcxt')
        self.assertTrue(ret, 'family:{}/libtype:rcxt FAILED! (expecting True)'.format(os.getenv("DB_FAMILY")))

    
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def _test_110___get_large_data_deliverable_file_md5sum(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        ''' '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        first_simple_config_1 = IcmLibrary('project', 'variant', 'libtype1',
                                             'library', 'first_simple_1', preview=True, use_db=False)
        first_simple_config_2 = IcmLibrary('project', 'variant', 'libtype2',
                                             'library', 'first_simple_2', preview=True, use_db=False)
        second_simple_config_1 = IcmLibrary('project', 'variant', 'libtype1',
                                              'library', 'second_simple_1', preview=True, use_db=False)
        second_simple_config_2 = IcmLibrary('project', 'variant', 'libtype2',
                                              'library', 'second_simple_2', preview=True, use_db=False)
        first = IcmConfig('first', 'project', 'variant', 
            [first_simple_config_1, first_simple_config_2], preview=True)
        second = IcmConfig('second', 'project', 'variant', 
            [second_simple_config_1, second_simple_config_2], preview=True)
        mock_create_from_icm.side_effect = [first, second]
        runner = DiffConfigs('project', 'variant', first, second, None, None,
                                   False, False, False, False, False, False, None, True)

        files = [
            ['//depot/icm/proj/i10socfm/fmio96pls_lib/rcxt/fmx_dev/audit/audit.fmio96pls_wr.rcxt_rv.f#3', 'd41d8cd98f00b204e9800998ecf8427e'],
            ['//depot/icm/proj/i10socfm/fmio96pls_lib/rcxt/dev/audit/audit.fmio96pls_wr.rcxt_rv.f#1', 'd41d8cd98f00b204e9800998ecf8427e'],
            ['//depot/icm/proj/i10socfm/fmio96pls_lib/rcxt/dev/results/timingspef_e/fmio96pls_wr/fmio96pls_wr.0.prcs.spef.gz#4', '7740480616147e9efdbbf3d663993575']
        ]

        self.longMessage = True
        for f in files:
            ret = runner.get_large_data_deliverable_file_md5sum(f[0])
            self.assertEqual(ret, f[1], "FAILED for file {}".format(f[0]))

        

    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.diffconfigs.ConfigFactory.create_from_icm')
    def test_120___massage_large_data_deliverable_stdout(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        ''' '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True
        first_simple_config_1 = IcmLibrary('project', 'variant', 'libtype1',
                                             'library', 'first_simple_1', preview=True, use_db=False)
        first_simple_config_2 = IcmLibrary('project', 'variant', 'libtype2',
                                             'library', 'first_simple_2', preview=True, use_db=False)
        second_simple_config_1 = IcmLibrary('project', 'variant', 'libtype1',
                                              'library', 'second_simple_1', preview=True, use_db=False)
        second_simple_config_2 = IcmLibrary('project', 'variant', 'libtype2',
                                              'library', 'second_simple_2', preview=True, use_db=False)
        first = IcmConfig('first', 'project', 'variant', 
            [first_simple_config_1, first_simple_config_2], preview=True)
        second = IcmConfig('second', 'project', 'variant', 
            [second_simple_config_1, second_simple_config_2], preview=True)
        mock_create_from_icm.side_effect = [first, second]
        runner = DiffConfigs('project', 'variant', first, second, None, None,
                                   False, False, False, False, False, False, None, True)

        stdout = '''
        ==== //depot/icm/proj/i10socfm/liotest1/ipspec/dev/aib_ssm.unneeded_deliverables.txt#9 (text+kl) - //depot/icm/proj/i10socfm/liotest1/ipspec/test2_dev/aib_ssm.unneeded_deliverables.txt#1 (text+kl) ==== content
        ==== //depot/icm/proj/i10socfm/liotest1/ipspec/dev/dummy.txt#1 - <none> ===
        ==== //depot/icm/proj/i10socfm/fmio96pls_lib/rcxt/fmx_dev/audit/audit.fmio96pls_wr.rcxt_rv.f#3 (symlink) - //depot/icm/proj/i10socfm/fmio96pls_lib/rcxt/dev/audit/audit.fmio96pls_wr.rcxt_rv.f#1 (symlink) ==== content
        ==== //depot/icm/proj/i10socfm/fmio96pls_lib/rcxt/fmx_dev/audit/audit.fmio96pls_wr.rcxt_rv.f#3 (symlink) - //depot/icm/proj/i10socfm/fmio96pls_lib/rcxt/dev/results/timingspef_e/fmio96pls_wr/fmio96pls_wr.0.prcs.spef.gz#4 (symlink) ==== content
        ==== <none> - //depot/icm/proj/i10socfm/liotest1/ipspec/test2_dev/test2_dev.txt#1 ====
        '''
        ans = '''
        ==== //depot/icm/proj/i10socfm/liotest1/ipspec/dev/dummy.txt#1 - <none> ===
        ==== //depot/icm/proj/i10socfm/fmio96pls_lib/rcxt/fmx_dev/audit/audit.fmio96pls_wr.rcxt_rv.f#3 (symlink) - //depot/icm/proj/i10socfm/fmio96pls_lib/rcxt/dev/results/timingspef_e/fmio96pls_wr/fmio96pls_wr.0.prcs.spef.gz#4 (symlink) ==== content
        ==== <none> - //depot/icm/proj/i10socfm/liotest1/ipspec/test2_dev/test2_dev.txt#1 ====
        '''
        ans = '\n        ==== //depot/icm/proj/i10socfm/liotest1/ipspec/dev/dummy.txt#1 - <none> ===\n        ==== <none> - //depot/icm/proj/i10socfm/liotest1/ipspec/test2_dev/test2_dev.txt#1 ====\n        '
        ret = runner.massage_large_data_deliverable_stdout(stdout)
        pprint(ret)
        self.assertEqual(ret, ans)




if __name__ == '__main__':
    unittest.main()
