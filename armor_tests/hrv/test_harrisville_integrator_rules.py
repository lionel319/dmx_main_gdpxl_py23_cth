#!/usr/bin/env python
# 2015 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the HRV integrator IC Manage armor rules
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/armor_tests/hrv/test_harrisville_integrator_rules.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import os

from abnrlib.icm import ICManageCLI, ICManageError
from abnrlib.utils import run_as_user

class TestHRVIntegratorRUles(unittest.TestCase):
    '''
    Tests the IC Manage rules applied to the hrv.integrator Perforce group
    '''

    def setUp(self):
        self.cli = ICManageCLI()
        self.user = 'hrvintegrator'
        self.prefix = 'hrv_integrator_testing'
        self.original_user = os.environ['USER']

    def tearDown(self):
        os.environ['USER'] = self.original_user
        projects = ['HRV', 'i22ulphrv']
        test_variant = 'armor_testing'
        test_libtype = 'rtl'

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

                        if libtype != test_libtype:
                            self.cli.delete_libtype(project, variant, libtype)

                    if variant.startswith(self.prefix):
                        self.cli.del_variant(project, variant)

    def test_hrv_integrator_can_add_variant_in_hrv(self):
        '''
        Tests that a hrv integrator can add a variant in the HRV project
        '''
        project = 'HRV'
        variant = '{0}_can_add_variant'.format(self.prefix)

        with run_as_user(self.user):
            self.cli.add_variant(project, variant)

        self.assertTrue(self.cli.variant_exists(project, variant))

    def test_hrv_integrator_can_add_variant_in_i22ulphrv(self):
        '''
        Tests that a hrv integrator can add a variant in the i22ulphrv project
        '''
        project = 'i22ulphrv'
        variant = '{0}_can_add_variant'.format(self.prefix)

        with run_as_user(self.user):
            self.cli.add_variant(project, variant)

        self.assertTrue(self.cli.variant_exists(project, variant))

    def test_hrv_integrator_can_add_libtype_to_variant_in_hrv(self):
        '''
        Tests that a hrv integrator can add a libtype to a variant within the HRV project
        '''
        project = 'HRV'
        variant = 'armor_testing'
        libtype = 'ipspec'

        with run_as_user(self.user):
            self.cli.add_libtypes_to_variant(project, variant, [libtype])

        self.assertTrue(self.cli.libtype_exists(project, variant, libtype))

    def test_hrv_integrator_can_add_libtype_to_variant_in_i22ulphrv(self):
        '''
        Tests that a hrv integrator can add a libtype to a variant within the i22ulphrv project
        '''
        project = 'i22ulphrv'
        variant = 'armor_testing'
        libtype = 'ipspec'

        with run_as_user(self.user):
            self.cli.add_libtypes_to_variant(project, variant, [libtype])

        self.assertTrue(self.cli.libtype_exists(project, variant, libtype))

    def test_hrv_integrator_can_add_library_in_hrv(self):
        '''
        Tests that a hrv integrator can add a library within the HRV project
        '''
        project = 'HRV'
        variant = 'armor_testing'
        libtype = 'rtl'
        library = '{0}_add_library'.format(self.prefix)

        with run_as_user(self.user):
            self.cli.add_libraries(project, variant, [libtype], library)

        self.assertTrue(self.cli.library_exists(project, variant, libtype, library))

    def test_hrv_integrator_can_add_library_in_i22ulphrv(self):
        '''
        Tests that a hrv integrator can add a library within the i22ulphrv project
        '''
        project = 'i22ulphrv'
        variant = 'armor_testing'
        libtype = 'rtl'
        library = '{0}_add_library'.format(self.prefix)

        with run_as_user(self.user):
            self.cli.add_libraries(project, variant, [libtype], library)

        self.assertTrue(self.cli.library_exists(project, variant, libtype, library))

    def test_hrv_integrator_can_branch_a_library_in_hrv(self):
        '''
        Tests that a hrv integrator can branch an IC Manage library within the HRV project
        '''
        project = 'HRV'
        variant = 'armor_testing'
        libtype = 'rtl'
        source_library = 'dev'
        target_library = '{0}_branched_library'.format(self.prefix)

        with run_as_user(self.user):
            self.cli.branch_library(project, variant, libtype, source_library,
                                    target_library)

        self.assertTrue(self.cli.library_exists(project, variant, libtype, target_library))

    def test_hrv_integrator_can_branch_a_library_in_i22ulphrv(self):
        '''
        Tests that a hrv integrator can branch an IC Manage library within the i22ulphrv project
        '''
        project = 'i22ulphrv'
        variant = 'armor_testing'
        libtype = 'rtl'
        source_library = 'dev'
        target_library = '{0}_branched_library'.format(self.prefix)

        with run_as_user(self.user):
            self.cli.branch_library(project, variant, libtype, source_library,
                                    target_library)

        self.assertTrue(self.cli.library_exists(project, variant, libtype, target_library))

    def test_hrv_integrator_cannot_delete_library_in_hrv(self):
        '''
        Tests that a hrv integrator cannot delete an IC Manage library within the HRV project
        '''
        project = 'HRV'
        variant = 'armor_testing'
        libtype = 'rtl'
        library = 'dev'

        with run_as_user(self.user):
            with self.assertRaises(ICManageError):
                self.cli.delete_library(project, variant, libtype, library)

    def test_hrv_integrator_cannot_delete_library_in_i22ulphrv(self):
        '''
        Tests that a hrv integrator cannot delete an IC Manage library within the i22ulphrv project
        '''
        project = 'i22ulphrv'
        variant = 'armor_testing'
        libtype = 'rtl'
        library = 'dev'

        with run_as_user(self.user):
            with self.assertRaises(ICManageError):
                self.cli.delete_library(project, variant, libtype, library)

if __name__ == '__main__':
    unittest.main()
