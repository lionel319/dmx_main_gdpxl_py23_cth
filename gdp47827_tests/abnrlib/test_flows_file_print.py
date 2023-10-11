#!/usr/bin/env python
# 2015 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr showconfig plugin
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_file_print.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import os
import sys
import unittest
from mock import patch

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

from dmx.abnrlib.flows.file_print import Print, PrintError
from dmx.abnrlib.config_factory import ConfigFactory, ConfigFactoryError
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.icm import ICManageCLI

class TestPrint(unittest.TestCase):

    @patch('dmx.abnrlib.flows.file_print.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.file_print.ICManageCLI.variant_exists')
    @patch('dmx.abnrlib.flows.file_print.ICManageCLI.library_exists')
    @patch.object(ConfigFactory, 'create_from_icm')
    def setUp(self, mock_create_from_icm, mock_library_exists, 
              mock_variant_exists, mock_project_exists):
        self.project = 'project'
        self.variant = 'variant'
        self.libtype = 'libtype'
        self.library = 'library'
        self.config = 'config'
        self.filespec = '{0}/{1}/{2}/{3}/this.is/a/bogus.path'.format(
            self.project, self.variant, self.libtype, self.library
        )
        self.filespec = '{}/{}/this.is/a/bogus.path'.format(self.variant, self.libtype)

        bogus_config = IcmConfig(self.config, self.project, self.variant, [], preview=True)
        mock_create_from_icm.return_value = bogus_config
        mock_library_exists.return_value = True
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True

        self.runner = Print(self.project, self.variant, self.config, self.filespec,
                                  True, False)

    @patch('dmx.abnrlib.flows.file_print.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.file_print.ICManageCLI.variant_exists')
    @patch.object(ConfigFactory, 'create_from_icm')
    def test_init_config_does_not_exist(self, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the init method when the config does not exist
        '''
        mock_create_from_icm.side_effect = ConfigFactoryError('bad config')
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True

        with self.assertRaises(ConfigFactoryError):
            Print('project', 'variant', 'config', 'project/variant/libtype/library/file',
                        True, True)
    
    @patch('dmx.abnrlib.flows.file_print.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.file_print.ICManageCLI.variant_exists')
    def test_init_variant_does_not_exist(self, mock_variant_exists, mock_project_exists):
        '''
        Tests the init method when the variant does not exist
        '''
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = False

        with self.assertRaises(PrintError):
            Print('project', 'variant', 'config', 'project/variant/libtype/library/file',
                        True, True)

    @patch('dmx.abnrlib.flows.file_print.ICManageCLI.project_exists')
    def test_init_project_does_not_exist(self, mock_project_exists):
        '''
        Tests the init method when the project does not exist
        '''
        mock_project_exists.return_value = False

        with self.assertRaises(PrintError):
            Print('project', 'variant', 'config', 'project/variant/libtype/library/file',
                        True, True)

    @patch('dmx.abnrlib.flows.file_print.ICManageCLI.project_exists')
    @patch('dmx.abnrlib.flows.file_print.ICManageCLI.variant_exists')
    @patch.object(ConfigFactory, 'create_from_icm')
    @patch('dmx.abnrlib.flows.file_print.ICManageCLI.library_exists')
    def _test_init_library_does_not_exist(self, mock_library_exists, mock_create_from_icm, mock_variant_exists, mock_project_exists):
        '''
        Tests the init method when the library does not exist
        '''
        mock_create_from_icm.return_value = True
        mock_library_exists.return_value = False
        mock_project_exists.return_value = True
        mock_variant_exists.return_value = True

        with self.assertRaises(PrintError):
            Print('project', 'variant', 'config', 'project/variant/libtype/library/file',
                        True, True)

    @patch('dmx.abnrlib.flows.file_print.ICManageCLI.p4_print')
    @patch('dmx.abnrlib.flows.file_print.Print.get_filespec_with_changenum')
    def test_run_no_print_output(self, mock_get_filespec_with_changenum,
                                 mock_p4_print):
        '''
        Tests the run method when no output is returned from the print
        '''
        mock_get_filespec_with_changenum.return_value = 'filespec'
        mock_p4_print.return_value = ''

        with self.assertRaises(PrintError):
            self.runner.run()

    @patch('dmx.abnrlib.flows.file_print.ICManageCLI.p4_print')
    @patch('dmx.abnrlib.flows.file_print.Print.get_filespec_with_changenum')
    def test_run_with_print_output(self, mock_get_filespec_with_changenum,
                                   mock_p4_print):
        '''
        Tests the run method when p4 print works
        '''
        mock_get_filespec_with_changenum.return_value = 'filespec'
        mock_p4_print.return_value = 'printed filespec'

        self.assertEqual(self.runner.run(), 0)

    @patch.object(IcmLibrary, 'get_bom')
    @patch('dmx.abnrlib.flows.file_print.Print.get_simple_config')
    def test_get_filespec_with_changenum(self, mock_get_simple_config, mock_get_bom):
        '''
        Tests the get_filespec_with_changenum method
        '''
        simple_config = IcmLibrary(self.project, self.variant, self.libtype,
                                     self.library, '', preview=True, use_db=False)
        p = '/intel/{}/{}/{}/{}'.format(self.project, self.variant, self.libtype, self.library)
        simple_config._defprops = {u'name': u'fmx_dev', u'created': u'2021-08-03T04:48:01.206Z', u'created-by': u'lionelta', u'path': p, u'libtype': u'ipspec', u'type': u'library', u'id': u'L1108770', u'change': u'@now'}

        mock_get_simple_config.return_value = simple_config
        bom = '//depot/gdpxl/intel/{}/{}/{}/{}/this.is/a/bogus.path@now'.format(self.project, self.variant, self.libtype, self.library)
        mock_get_bom.return_value = [bom]

        full_filespec = self.runner.get_filespec_with_changenum()

        self.assertEqual(full_filespec, bom)

    def test_get_simple_config_no_matching_configs(self):
        '''
        Tests the get_simple_config method when there are no matching simple configs
        '''
        bogus_simple = IcmLibrary(self.project, self.variant,
                                    'not-this-libtype', self.library, self.config,
                                    preview=True, use_db=False)
        self.runner.config.add_configuration(bogus_simple)

        with self.assertRaises(PrintError):
            self.runner.get_simple_config()

    @patch.object(IcmLibrary, 'search')
    def test_get_simple_config_multiple_matching_configs(self, mock_search):
        '''
        Tests the get_simple_config method when there are no matching simple configs
        '''
        bogus_simple = IcmLibrary(self.project, self.variant,
                                    'not-this-libtype', self.library, self.config,
                                    preview=True, use_db=False)
        mock_search.return_value = [bogus_simple, bogus_simple]

        with self.assertRaises(PrintError):
            self.runner.get_simple_config()

    def test_get_simple_config_works(self):
        '''
        Tests the get_simple_config method when it works
        '''
        good_simple = IcmLibrary(self.project, self.variant,
                                    self.libtype, self.library, self.config,
                                    preview=True, use_db=False)
        self.runner.config.add_configuration(good_simple)

        self.assertEqual(self.runner.get_simple_config(), good_simple)

if __name__ == '__main__':
    unittest.main()
