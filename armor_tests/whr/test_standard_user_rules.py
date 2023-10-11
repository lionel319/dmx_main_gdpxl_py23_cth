#!/usr/bin/env python
# 2015 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the classes in the namevalidator.py file
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/armor_tests/whr/test_standard_user_rules.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import os
import sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

from dmx.abnrlib.icm import ICManageCLI, ICManageError
from dmx.utillib.utils import run_as_user, run_command

class TestStandardUserRules(unittest.TestCase):
    '''
    Tests the operations that standard users can/cannot perform in whr
    '''
    def setUp(self):
        self.cli = ICManageCLI()
        self.standard_user = 'icmtester'
        self.prefix = 'standard_user_testing'
        self.original_user = os.environ['USER']

    def tearDown(self):
        os.environ['USER'] = self.original_user
        projects = ['whr']
        variant = 'armor_testing'

        for project in projects:
            for composite_config in self.cli.get_configs(project, variant):
                if composite_config.startswith(self.prefix):
                    self.cli.del_config(project, variant, composite_config)

            for libtype in self.cli.get_libtypes(project, variant):
                for simple_config in self.cli.get_configs(project, variant, libtype=libtype):
                    if simple_config.startswith(self.prefix):
                        self.cli.del_config(project, variant, simple_config,
                                            libtype=libtype)

                for library in self.cli.get_libraries(project, variant, libtype):
                    if library.startswith(self.prefix):
                        self.cli.delete_library(project, variant, libtype, library)

        test_variant = 'armor_testing'
        test_libtype = ['rtl', 'ipspec']

        for project in projects:
            for variant in self.cli.get_variants(project):
                if variant == test_variant or variant.startswith(self.prefix):
                    for composite_config in self.cli.get_configs(project, variant):
                        if composite_config.startswith(self.prefix):
                            self.cli.del_config(project, variant, composite_config)

                    for libtype in self.cli.get_libtypes(project, variant):
                        for simple_config in self.cli.get_configs(project, variant, libtype=libtype):
                            if simple_config.startswith(self.prefix):
                                self.cli.del_config(project, variant, simple_config,
                                                    libtype=libtype)
                        for library in self.cli.get_libraries(project, variant, libtype):
                            if library.startswith(self.prefix):
                                self.cli.delete_library(project, variant, libtype, library)

                        if libtype not in test_libtype:
                            self.cli.delete_libtype(project, variant, libtype)

                    if variant.startswith(self.prefix):
                        self.cli.del_variant(project, variant)
                        

    # Disabled per http://pg-rdjira:8080/browse/DI-1348
    def _test_standard_user_cannot_create_variant_in_whr(self):
        '''
        Tests that a standard user cannot create a variant in the whr project
        '''
        project = 'whr'
        variant = 'this_should_not_get_added'

        with run_as_user(self.standard_user):
            with self.assertRaises(ICManageError):
                self.cli.add_variant(project, variant)

        self.assertFalse(self.cli.variant_exists(project, variant))

    def test_standard_user_can_add_libtype_to_variant_in_whr(self):
        '''
        Tests that a standard user can add a libtype to a variant in whr
        '''
        project = 'whr'
        variant = 'armor_testing'
        libtype = 'ipspec'

        with run_as_user(self.standard_user):
            self.cli.add_libtypes_to_variant(project, variant, [libtype])

        self.assertTrue(self.cli.libtype_exists(project, variant, libtype))

    def test_standard_user_can_add_libraries_in_whr(self):
        '''
        Tests that a standard user can add a library in whr
        '''
        project = 'whr'
        variant = 'armor_testing'
        libtype = 'rtl'
        library = '{0}_new_library'.format(self.prefix)

        with run_as_user(self.standard_user):
            self.cli.add_libraries(project, variant, [libtype], library=library)

        self.assertTrue(self.cli.library_exists(project, variant, libtype, library))

    def test_standard_user_can_branch_libraries_in_whr(self):
        '''
        Tests that a standard user can branch a library in whr
        '''
        project = 'whr'
        variant = 'armor_testing'
        libtype = 'rtl'
        source_library = 'dev'
        target_library = '{0}_new_branch'.format(self.prefix)

        with run_as_user(self.standard_user):
            self.cli.branch_library(project, variant, libtype, source_library,
                                    target_library)

        self.assertTrue(self.cli.library_exists(project, variant, libtype, target_library))

    def test_standard_user_cannot_delete_a_library_in_whr(self):
        '''
        Tests that a standard user cannot delete a library in whr
        '''
        project = 'whr'
        variant = 'armor_testing'
        libtype = 'rtl'
        library = 'dev'

        with run_as_user(self.standard_user):
            with self.assertRaises(ICManageError):
                self.cli.delete_library(project, variant, libtype, library)

        self.assertTrue(self.cli.library_exists(project, variant, libtype, library))

    def test_standard_user_can_create_mutable_simple_config_in_whr(self):
        '''
        Tests that a standard user can create a mutable simple config in whr
        '''
        project = 'whr'
        variant = 'armor_testing'
        libtype = 'rtl'
        library = 'dev'
        config = '{0}_create_mutable_simple_config'.format(self.prefix)

        with run_as_user(self.standard_user):
            self.cli.add_simple_config(project, variant, libtype, config,
                                       '#ActiveDev', library=library)

        self.assertTrue(self.cli.config_exists(project, variant, config,
                                               libtype=libtype))

    def test_standard_user_can_create_mutable_composite_config_in_whr(self):
        '''
        Tests that a standard user can create a mutable composite config in whr
        '''
        project = 'whr'
        variant = 'armor_testing'
        libtype = 'rtl'
        config = '{0}_create_mutable_composite_config'.format(self.prefix)
        simple_config = 'dev@{0}'.format(libtype)

        with run_as_user(self.standard_user):
            self.cli.add_composite_config(project, variant, config, [simple_config])

        self.assertTrue(self.cli.config_exists(project, variant, config))

    def test_standard_user_can_create_a_library_release_in_whr(self):
        '''
        Tests that a standard user can create a library release in whr
        '''
        project = 'whr'
        variant = 'armor_testing'
        libtype = 'rtl'
        library = '{0}_release_testing'.format(self.prefix)

        self.cli.add_libraries(project, variant, [libtype], library=library)
        self.assertTrue(self.cli.library_exists(project, variant, libtype, library))

        with run_as_user(self.standard_user):
            release = self.cli.add_library_release_from_activedev(project, variant, libtype,
                                                                  'armor_testing',
                                                                   library=library)
            self.assertTrue(self.cli.release_exists(project, variant, libtype, library,
                                                    release))

    # Disabled per http://pg-rdjira:8080/browse/DI-1348
    def _test_standard_user_cannot_edit_ipspec(self):
        project = 'whr'                
        variant = 'armor_testing'
        libtype = 'ipspec'
        config = 'dev'
        wsdir = os.path.realpath('/p/psg/da/infra/regression/whr/{}'.format(os.getenv('USER')))
        orig_cwd = os.getcwd()

        if not os.path.exists(wsdir):
            os.mkdir(wsdir)

        workspace = self.cli.add_workspace(project, variant, config, dirname=wsdir, libtype=libtype)
        wsroot = '{}/{}'.format(wsdir, workspace)

        self.assertFalse(self.cli.sync_workspace(workspace))
        ipspec_dir = '{}/{}/{}'.format(wsroot, variant, libtype)
        os.chdir(ipspec_dir)

        file = 'test.txt'
        command = 'icmp4 add {}'.format(file)
        with run_as_user(self.standard_user):
            exitcode, stdout, stderr = run_command(command)
            self.assertFalse(exitcode)
            self.assertIn('no permission for operation on file', stderr)
        os.chdir(orig_cwd)

        self.assertTrue(self.cli.del_workspace(workspace, preserve=False, force=True))

    # The following tests are ported from test_wharfrock_librarian_rules
    def test_standard_user_can_create_variant_in_whr(self):
        '''
        Tests that a standard_user can create a variant in the whr project
        '''
        project = 'whr'
        variant = 'this_should_get_added'

        with run_as_user(self.standard_user):
            self.cli.add_variant(project, variant)

        self.assertTrue(self.cli.variant_exists(project, variant))

    def test_standard_user_cannot_delete_variant_in_whr(self):
        '''
        Tests that a standard_user cannot delete a variant in the whr project
        '''
        project = 'whr'
        variant = 'this_should_get_added'

        with run_as_user(self.standard_user):            
            self.cli.add_variant(project, variant)            
            self.assertTrue(self.cli.variant_exists(project, variant))
            with self.assertRaises(ICManageError):
                self.cli.del_variant(project, variant)                          

    def test_standard_user_can_add_libtype_to_variant_in_whr(self):
        '''
        Tests that a standard_user can add a libtype to a variant in whr
        '''
        project = 'whr'
        variant = 'armor_testing'
        libtype = 'ipspec'

        with run_as_user(self.standard_user):
            self.cli.add_libtypes_to_variant(project, variant, [libtype])

        self.assertTrue(self.cli.libtype_exists(project, variant, libtype))

    def test_standard_user_can_add_library_in_whr(self):
        '''
        Tests that a whr standard user can add a library within the whr project
        '''
        project = 'whr'
        variant = 'armor_testing'
        libtype = 'rtl'
        library = '{0}_add_library'.format(self.prefix)

        with run_as_user(self.standard_user):
            self.cli.add_libraries(project, variant, [libtype], library)

        self.assertTrue(self.cli.library_exists(project, variant, libtype, library))

    def test_standard_user_can_branch_a_library_in_whr(self):
        '''
        Tests that a whr standard user can branch an IC Manage library within the whr project
        '''
        project = 'whr'
        variant = 'armor_testing'
        libtype = 'rtl'
        source_library = 'dev'
        target_library = '{0}_branched_library'.format(self.prefix)

        with run_as_user(self.standard_user):
            self.cli.branch_library(project, variant, libtype, source_library,
                                    target_library)

        self.assertTrue(self.cli.library_exists(project, variant, libtype, target_library))

    def test_standard_user_cannot_delete_library_in_whr(self):
        '''
        Tests that a whr standard user cannot delete an IC Manage library within the whr project
        '''
        project = 'whr'
        variant = 'armor_testing'
        libtype = 'rtl'
        library = 'dev'

        with run_as_user(self.standard_user):
            with self.assertRaises(ICManageError):
                self.cli.delete_library(project, variant, libtype, library)

    def test_standard_user_can_edit_ipspec(self):
        project = 'whr'                
        variant = 'armor_testing'
        libtype = 'ipspec'
        config = 'dev'
        wsdir = os.path.realpath('/p/psg/da/infra/regression/whr/{}'.format(os.getenv('USER')))
        orig_cwd = os.getcwd()

        if not os.path.exists(wsdir):
            os.mkdir(wsdir)

        workspace = self.cli.add_workspace(project, variant, config, dirname=wsdir, libtype=libtype)
        wsroot = '{}/{}'.format(wsdir, workspace)

        self.assertFalse(self.cli.sync_workspace(workspace))
        ipspec_dir = '{}/{}/{}'.format(wsroot, variant, libtype)
        os.chdir(ipspec_dir)

        file = 'test.txt'
        command = 'icmp4 add {}'.format(file)
        with run_as_user(self.standard_user):
            exitcode, stdout, stderr = run_command(command)
            self.assertFalse(exitcode)
            self.assertIn('opened for add', stdout)
            command = 'icmp4 revert {}'.format(file)
            exitcode, stdout, stderr = run_command(command)
            self.assertFalse(exitcode)

        os.chdir(orig_cwd)

        self.assertTrue(self.cli.del_workspace(workspace, preserve=False, force=True))


if __name__ == '__main__':
    unittest.main()

