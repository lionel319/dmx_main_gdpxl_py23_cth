#!/usr/bin/env python
# 2015 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the classes in the namevalidator.py file
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/armor_tests/hrv/test_immutable_config_rules.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import os

from abnrlib.icm import ICManageCLI, ICManageError
from abnrlib.utils import run_as_user

class TestRELCreation(unittest.TestCase):
    '''
    Tests that the creation of REL configurations behaves as expected
    '''

    def setUp(self):
        self.cli = ICManageCLI()
        self.standard_user = 'icmtester'
        self.original_user = os.environ['USER']

    def tearDown(self):
        os.environ['USER'] = self.original_user
        # Remove any REL configs that were created
        projects = ['HRV', 'i22ulphrv']
        variant = 'armor_testing'
        libtype = 'rtl'

        for project in projects:
            for composite_config in self.cli.get_configs(project, variant):
                if composite_config.startswith(('REL', 'snap-')):
                    self.cli.del_config(project, variant, composite_config)

            for simple_config in self.cli.get_configs(project, variant,
                                                      libtype=libtype):
                if simple_config.startswith(('REL', 'snap-')):
                    self.cli.del_config(project, variant, simple_config, libtype=libtype)

    def test_standard_user_cannot_create_simple_REL_in_HRV(self):
        '''
        Tests that a standard user cannot create a simple REL config within the HRV project
        '''
                      
        with run_as_user(self.standard_user):
            with self.assertRaises(ICManageError):       
                self.cli.add_simple_config('HRV', 'armor_testing', 'rtl', 'REL1.0ND5revA__15ww123a',
                                           '#ActiveDev')

    def test_standard_user_cannot_create_simple_REL_in_i22ulphrv(self):
        '''
        Tests that a standard user cannot create a simple REL config within the i22ulphrv project
        '''
        with run_as_user(self.standard_user):
            with self.assertRaises(ICManageError):
                self.cli.add_simple_config('i22ulphrv', 'armor_testing', 'rtl', 'REL1.0ND5revA__15ww123a',
                                           '#ActiveDev')

    def test_standard_user_cannot_create_composite_REL_in_HRV(self):
        '''
        Tests that a standard user cannot create a composite REL config within the HRV project
        '''
        simple_config = 'dev@rtl'
        with run_as_user(self.standard_user):
            with self.assertRaises(ICManageError):
                self.cli.add_composite_config('HRV', 'armor_testing', 'REL1.0ND5revA__15ww123a',
                                              [simple_config])

    def test_standard_user_cannot_create_composite_REL_in_i22ulphrv(self):
        '''
        Tests that a standard user cannot create a composite REL config within the i22ulphrv project
        '''
        simple_config = 'dev@rtl'
        with run_as_user(self.standard_user):        
            with self.assertRaises(ICManageError):
                self.cli.add_composite_config('i22ulphrv', 'armor_testing', 'REL1.0ND5revA__15ww123a',
                                              [simple_config])

    def test_standard_user_cannot_create_simple_snap_in_HRV(self):
        '''
        Tests that a standard user cannot create a simple snap- config within the HRV project
        '''
        # Call ICManageCLI.add_simple_config won't test this for us as it detects
        # that the config is snap and automatically switches user to immutable
        # We need to invoke pm directly
        with run_as_user(self.standard_user):
            command = ['pm', 'configuration', '-t', 'rtl', 'HRV', 'armor_testing',
                       'snap-armor-testing', 'dev@#dev', ]
            (exitcode, stdout, stderr) = self.cli._ICManageCLI__run_write_command(command)
    
            self.assertNotEqual(exitcode, 0)
            self.assertTrue('No permission for operation' in stderr)
            self.assertFalse(stdout)

    def test_standard_user_cannot_create_simple_snap_in_i22ulphrv(self):
        '''
        Tests that a standard user cannot create a simple snap config within the i22ulphrv project
        '''
        # Call ICManageCLI.add_simple_config won't test this for us as it detects
        # that the config is snap and automatically switches user to immutable
        # We need to invoke pm directly
        with run_as_user(self.standard_user):        
            command = ['pm', 'configuration', '-t', 'rtl', 'i22ulphrv', 'armor_testing',
                       'snap-armor-testing', 'dev@#dev', ]
            (exitcode, stdout, stderr) = self.cli._ICManageCLI__run_write_command(command)
    
            self.assertNotEqual(exitcode, 0)
            self.assertTrue('No permission for operation' in stderr)
            self.assertFalse(stdout)

    def test_standard_user_cannot_create_composite_snap_in_HRV(self):
        '''
        Tests that a standard user cannot create a composite snap config within the HRV project
        '''
        simple_config = 'dev@rtl'
        # Call ICManageCLI.composite_simple_config won't test this for us as it detects
        # that the config is snap and automatically switches user to immutable
        with run_as_user(self.standard_user):
            # We need to invoke pm directly
            command = ['pm', 'configuration', 'HRV', 'armor_testing',
                       'snap-armor-testing', '{}'.format(simple_config), ]
            (exitcode, stdout, stderr) = self.cli._ICManageCLI__run_write_command(command)
    
            self.assertNotEqual(exitcode, 0)
            self.assertTrue('No permission for operation' in stderr)
            self.assertFalse(stdout)

    def test_standard_user_cannot_create_composite_snap_in_i22ulphrv(self):
        '''
        Tests that a standard user cannot create a composite snap config within the i22ulphrv project
        '''
        simple_config = 'dev@rtl'
        simple_config = 'dev@rtl'
        with run_as_user(self.standard_user):
            # Call ICManageCLI.composite_simple_config won't test this for us as it detects
            # that the config is snap and automatically switches user to immutable
            # We need to invoke pm directly
            command = ['pm', 'configuration', 'i22ulphrv', 'armor_testing',
                       'snap-armor-testing', '{}'.format(simple_config), ]
            (exitcode, stdout, stderr) = self.cli._ICManageCLI__run_write_command(command)
    
            self.assertNotEqual(exitcode, 0)
            self.assertTrue('No permission for operation' in stderr)
            self.assertFalse(stdout)

    def test_icetnr_can_create_simple_REL_in_HRV(self):
        '''
        Tests that the icetnr user can create a simple REL config within the HRV project
        '''
        project = 'HRV'
        variant = 'armor_testing'
        libtype = 'rtl'
        config = 'REL1.0ND5revA__15ww123a'

        with run_as_user('icetnr'):
            self.assertTrue(self.cli.add_simple_config(project, variant, libtype,
                                                       config, '#ActiveDev'))
            self.assertTrue(self.cli.config_exists(project, variant, config,
                                                   libtype=libtype))

    def test_icetnr_can_create_simple_REL_in_i22ulphrv(self):
        '''
        Tests that the icetnr user can create a simple REL config within the i22ulphrv project
        '''
        project = 'i22ulphrv'
        variant = 'armor_testing'
        libtype = 'rtl'
        config = 'REL1.0ND5revA__15ww123a'

        with run_as_user('icetnr'):
            self.assertTrue(self.cli.add_simple_config(project, variant, libtype,
                                                       config, '#ActiveDev'))
            self.assertTrue(self.cli.config_exists(project, variant, config,
                                                   libtype=libtype))

    def test_icetnr_can_create_composite_REL_in_HRV(self):
        '''
        Tests that the icetnr user can create a composite REL config within the HRV project
        '''
        project = 'HRV'
        variant = 'armor_testing'
        libtype = 'rtl'
        config = 'REL1.0ND5revA__15ww123a'

        with run_as_user('icetnr'):
            self.assertTrue(self.cli.add_composite_config(project, variant,
                                                          config, ['dev@{0}'.format(libtype)]))
            self.assertTrue(self.cli.config_exists(project, variant, config))

    def test_icetnr_can_create_composite_REL_in_i22ulphrv(self):
        '''
        Tests that the icetnr user can create a composite REL config within the i22ulphrv project
        '''
        project = 'i22ulphrv'
        variant = 'armor_testing'
        libtype = 'rtl'
        config = 'REL1.0ND5revA__15ww123a'

        with run_as_user('icetnr'):
            self.assertTrue(self.cli.add_composite_config(project, variant,
                                                          config, ['dev@{0}'.format(libtype)]))
            self.assertTrue(self.cli.config_exists(project, variant, config))

    def test_immutable_can_create_simple_snap_in_HRV(self):
        '''
        Tests that the immutable user can create a simple snap config within the HRV project
        '''
        project = 'HRV'
        variant = 'armor_testing'
        libtype = 'rtl'
        config = 'snap-armor-testing'

        self.assertTrue(self.cli.add_simple_config(project, variant, libtype,
                                                   config, '#ActiveDev'))
        self.assertTrue(self.cli.config_exists(project, variant, config,
                                               libtype=libtype))

    def test_immutable_can_create_simple_snap_in_i22ulphrv(self):
        '''
        Tests that the immutable user can create a simple snap config within the i22ulphrv project
        '''
        project = 'i22ulphrv'
        variant = 'armor_testing'
        libtype = 'rtl'
        config = 'snap-armor-testing'

        self.assertTrue(self.cli.add_simple_config(project, variant, libtype,
                                                   config, '#ActiveDev'))
        self.assertTrue(self.cli.config_exists(project, variant, config,
                                               libtype=libtype))

    def test_immutable_can_create_composite_snap_in_HRV(self):
        '''
        Tests that the immutable user can create a composite snap config within the HRV project
        '''
        project = 'HRV'
        variant = 'armor_testing'
        libtype = 'rtl'
        config = 'snap-armor-testing'

        self.assertTrue(self.cli.add_composite_config(project, variant,
                                                      config, ['dev@{0}'.format(libtype)]))
        self.assertTrue(self.cli.config_exists(project, variant, config))

    def test_immutable_can_create_composite_snap_in_i22ulphrv(self):
        '''
        Tests that the immutable user can create a composite snap config within the i22ulphrv project
        '''
        project = 'i22ulphrv'
        variant = 'armor_testing'
        libtype = 'rtl'
        config = 'snap-armor-testing'

        self.assertTrue(self.cli.add_composite_config(project, variant,
                                                      config, ['dev@{0}'.format(libtype)]))
        self.assertTrue(self.cli.config_exists(project, variant, config))

if __name__ == '__main__':
    unittest.main()
