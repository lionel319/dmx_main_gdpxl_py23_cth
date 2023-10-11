#!/usr/bin/env python
# 2015 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the Falcon_Mesa librarian IC Manage armor rules
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/armor_tests/fm/_test_falcon_mesa_librarian_rules.py $
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

class TestFalcon_MesaIntegratorRUles(unittest.TestCase):
    '''
    Tests the IC Manage rules applied to the falcon_mesa.librarian Perforce group
    '''

    def setUp(self):
        self.cli = ICManageCLI()
        self.user = 'fmlibrarian'
        self.prefix = 'falcon_mesa_librarian_testing'
        self.original_user = os.environ['USER']

    def tearDown(self):
        os.environ['USER'] = self.original_user
        projects = ['Falcon_Mesa', 'i10socfm']
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

    def test_falcon_mesa_librarian_can_create_variant_in_falcon_mesa(self):
        '''
        Tests that a falcon_mesa_librarian can create a variant in the Falcon_Mesa project
        '''
        project = 'Falcon_Mesa'
        variant = 'this_should_get_added'

        with run_as_user(self.user):
            self.cli.add_variant(project, variant)

        self.assertTrue(self.cli.variant_exists(project, variant))

    def test_falcon_mesa_librarian_can_create_variant_in_i10socfm(self):
        '''
        Tests that a falcon_mesa_librarian can create a variant in the i10socfm project
        '''
        project = 'i10socfm'
        variant = 'this_should_get_added'

        with run_as_user(self.user):           
            self.cli.add_variant(project, variant)

        self.assertTrue(self.cli.variant_exists(project, variant))

    def test_falcon_mesa_librarian_cannot_delete_variant_in_falcon_mesa(self):
        '''
        Tests that a falcon_mesa_librarian cannot delete a variant in the Falcon_Mesa project
        '''
        project = 'Falcon_Mesa'
        variant = 'this_should_get_added'

        with run_as_user(self.user):            
            self.cli.add_variant(project, variant)            
            self.assertTrue(self.cli.variant_exists(project, variant))
            with self.assertRaises(ICManageError):
                self.cli.del_variant(project, variant)                          

    def test_falcon_mesa_librarian_cannot_delete_variant_in_i10socfm(self):
        '''
        Tests that a falcon_mesa_librarian cannot delete a variant in the i10socfm project
        '''
        project = 'i10socfm'
        variant = 'this_should_get_added'

        with run_as_user(self.user):            
            self.cli.add_variant(project, variant)            
            self.assertTrue(self.cli.variant_exists(project, variant))
            with self.assertRaises(ICManageError):
                self.cli.del_variant(project, variant)             

    def test_falcon_mesa_librarian_can_add_libtype_to_variant_in_falcon_mesa(self):
        '''
        Tests that a falcon_mesa_librarian can add a libtype to a variant in Falcon_Mesa
        '''
        project = 'Falcon_Mesa'
        variant = 'armor_testing'
        libtype = 'ipspec'

        with run_as_user(self.user):
            self.cli.add_libtypes_to_variant(project, variant, [libtype])

        self.assertTrue(self.cli.libtype_exists(project, variant, libtype))

    def test_falcon_mesa_librarian_can_add_libtype_to_variant_in_i10socfm(self):
        '''
        Tests that a falcon_mesa_librarian cat add a libtype to a variant in i10socfm
        '''
        project = 'i10socfm'
        variant = 'armor_testing'
        libtype = 'ipspec'

        with run_as_user(self.user):
            self.cli.add_libtypes_to_variant(project, variant, [libtype])

        self.assertTrue(self.cli.libtype_exists(project, variant, libtype))

    
    def test_falcon_mesa_librarian_can_add_library_in_falcon_mesa(self):
        '''
        Tests that a falcon_mesa librarian can add a library within the Falcon_Mesa project
        '''
        project = 'Falcon_Mesa'
        variant = 'armor_testing'
        libtype = 'rtl'
        library = '{0}_add_library'.format(self.prefix)

        with run_as_user(self.user):
            self.cli.add_libraries(project, variant, [libtype], library)

        self.assertTrue(self.cli.library_exists(project, variant, libtype, library))

    def test_falcon_mesa_librarian_can_add_library_in_i10socfm(self):
        '''
        Tests that a falcon_mesa librarian can add a library within the i10socfm project
        '''
        project = 'i10socfm'
        variant = 'armor_testing'
        libtype = 'rtl'
        library = '{0}_add_library'.format(self.prefix)

        with run_as_user(self.user):
            self.cli.add_libraries(project, variant, [libtype], library)

        self.assertTrue(self.cli.library_exists(project, variant, libtype, library))

    def test_falcon_mesa_librarian_can_branch_a_library_in_falcon_mesa(self):
        '''
        Tests that a falcon_mesa librarian can branch an IC Manage library within the Falcon_Mesa project
        '''
        project = 'Falcon_Mesa'
        variant = 'armor_testing'
        libtype = 'rtl'
        source_library = 'dev'
        target_library = '{0}_branched_library'.format(self.prefix)

        with run_as_user(self.user):
            self.cli.branch_library(project, variant, libtype, source_library,
                                    target_library)

        self.assertTrue(self.cli.library_exists(project, variant, libtype, target_library))

    def test_falcon_mesa_librarian_can_branch_a_library_in_i10socfm(self):
        '''
        Tests that a falcon_mesa librarian can branch an IC Manage library within the i10socfm project
        '''
        project = 'i10socfm'
        variant = 'armor_testing'
        libtype = 'rtl'
        source_library = 'dev'
        target_library = '{0}_branched_library'.format(self.prefix)

        with run_as_user(self.user):
            self.cli.branch_library(project, variant, libtype, source_library,
                                    target_library)

        self.assertTrue(self.cli.library_exists(project, variant, libtype, target_library))

    def test_falcon_mesa_librarian_cannot_delete_library_in_falcon_mesa(self):
        '''
        Tests that a falcon_mesa librarian cannot delete an IC Manage library within the Falcon_Mesa project
        '''
        project = 'Falcon_Mesa'
        variant = 'armor_testing'
        libtype = 'rtl'
        library = 'dev'

        with run_as_user(self.user):
            with self.assertRaises(ICManageError):
                self.cli.delete_library(project, variant, libtype, library)

    def test_falcon_mesa_librarian_cannot_delete_library_in_i10socfm(self):
        '''
        Tests that a falcon_mesa librarian cannot delete an IC Manage library within the i10socfm project
        '''
        project = 'i10socfm'
        variant = 'armor_testing'
        libtype = 'rtl'
        library = 'dev'

        with run_as_user(self.user):
            with self.assertRaises(ICManageError):
                self.cli.delete_library(project, variant, libtype, library)

    def test_falcon_mesa_librarian_can_edit_ipspec(self):
        project = 'Falcon_Mesa'                
        variant = 'armor_testing'
        libtype = 'ipspec'
        config = 'dev'
        wsdir = os.path.realpath('/p/psg/da/infra/regression/falcon/{}'.format(os.getenv('USER')))
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
        with run_as_user(self.user):
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
