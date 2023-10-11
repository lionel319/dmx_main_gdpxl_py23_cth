#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_utils.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from future import standard_library
standard_library.install_aliases()
import unittest
from mock import patch
from datetime import date
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.utillib.utils import *
import io

#
# Shamelessly stolen from:
# http://www.williamjohnbert.com/2011/07/how-to-unit-testing-in-django-with-mocking-and-patching/
# We cannot directly mock out getting the ww from the datetime library, so we
# have to create a fake class
#
class FakeDate(date):
    '''
    A fake replace dor datetime that can be mocked for testing
    '''
    def __new__(cls, *args, **kwargs):
        return date.__new__(date, *args, **kwargs)

class TestUtils(unittest.TestCase):
    '''
    Tests the dmx.utillib.utils library
    '''
    def test_get_abnr_id(self):
        '''
        Tests the get_abnr_id function
        '''
        timestamp = int(time.time())
        user = getpass.getuser()
        hostname = socket.gethostname()
        pid = os.getpid()

        abnr_id = get_abnr_id()
        self.assertTrue(abnr_id.startswith('{0}_{1}_{2}_'.format(hostname, user, pid)))
        # Chop off the timestamp and make sure it's greater than or equal to ours
        id_details = abnr_id.split('_')
        self.assertGreaterEqual(timestamp, int(id_details[-1]))

    def test_minmaxsplit_exact_number_of_fields(self):
        '''
        Tests the minmaxsplit function with the exact number of
        fields we want
        '''
        line = "this is a test line"
        num_wanted = len(line.split())
        fields = minmaxsplit(line, num_wanted)
        self.assertEqual(fields, line.split(' '))

    def test_minmaxsplit_more_fields_exact_count_true(self):
        '''
        Tests the minmaxsplit function with more fields and exact count
        is True
        '''
        line = "this is a test line"
        num_wanted = len(line.split()) - 1
        with self.assertRaises(Exception):
            minmaxsplit(line, num_wanted)

    def test_minmaxsplit_more_fields_exact_count_false(self):
        '''
        Tests the minmaxsplit function with more fields than we want and exact
        count is False
        '''
        line = "this is a test line"
        num_wanted = len(line.split()) - 1
        fields = minmaxsplit(line, num_wanted, exact_count=False)
        self.assertEqual(len(fields), num_wanted)

    def test_minmaxsplit_less_fields_exact_count_true(self):
        '''
        Tests the minmaxsplit function with less fields than we want and exact
        count is True
        '''
        line = "this is a test line"
        num_wanted = len(line.split()) + 10
        with self.assertRaises(Exception):
            minmaxsplit(line, num_wanted)

    def test_minmaxsplit_less_fields_exact_count_false(self):
        '''
        Tests the minmaxsplit function with less fields than we want and exact
        count is False
        '''
        line = "this is a test line"
        num_wanted = len(line.split()) + 10
        with self.assertRaises(Exception):
            minmaxsplit(line, num_wanted, exact_count=False)

    def test_natural_sort_works(self):
        '''
        Tests the natural_sort method
        '''
        unsorted = ['snap-1', 'snap-2', 'snap-10', 'snap-100', 'snap-9']
        sorted = natural_sort(unsorted)
        self.assertEqual(unsorted[0], sorted[0])
        self.assertEqual(unsorted[1], sorted[1])
        self.assertEqual(unsorted[2], sorted[3])
        self.assertEqual(unsorted[3], sorted[4])
        self.assertEqual(unsorted[4], sorted[2])

    def test_get_thread_and_milestone_from_rel_config_non_rel_config(self):
        '''
        Tests the get_thread_and_milestone_from_rel_config method with a non-REL config
        '''
        config = 'dev'
        (thread, milestone) = get_thread_and_milestone_from_rel_config(config)
        self.assertIsNone(thread)
        self.assertIsNone(milestone)

    def test_get_thread_and_milestone_from_rel_config_snap_config(self):
        '''
        Tests the get_thread_and_milestone_from_rel_config method with a snap config
        '''
        config = 'snap-2'
        (thread, milestone) = get_thread_and_milestone_from_rel_config(config)
        self.assertIsNone(thread)
        self.assertIsNone(milestone)

    def test_get_thread_and_milestone_from_rel_config_no_label(self):
        '''
        Tests the get_thread_and_milestone_from_rel_config method when the config
        name does not contain a label
        '''
        config = 'REL3.0ND5revB__14ww265a'
        (thread, milestone) = get_thread_and_milestone_from_rel_config(config)
        self.assertEqual(thread, 'ND5revB')
        self.assertEqual(milestone, '3.0')

    def test_get_thread_and_milestone_from_rel_config_with_label(self):
        '''
        Tests the get_thread_and_milestone_from_rel_config method when the config
        name does contain a label
        '''
        config = 'REL3.0ND5revB--Testing__14ww265a'
        (thread, milestone) = get_thread_and_milestone_from_rel_config(config)
        self.assertEqual(thread, 'ND5revB')
        self.assertEqual(milestone, '3.0')

    def test_get_thread_and_milestone_from_rel_config_branched(self):
        '''
        Tests the get_thread_and_milestone_from_rel_config method when the
        config is a branched REL config - i.e. begins bREL
        '''
        config = 'bREL1.5ND5revA-UID-CLK-14ww363a__bblanc_trial__dev'
        (thread, milestone) = get_thread_and_milestone_from_rel_config(config)
        self.assertEqual(thread, 'ND5revA')
        self.assertEqual(milestone, '1.5')

    @patch('dmx.utillib.utils.get_thread_and_milestone_from_rel_config')
    def test_is_rel_config_against_this_thread_and_milestone_different_thread(self,
                                                                              mock_get_thread_and_milestone_from_rel_config):
        '''
        Tests the is_rel_config_against_this_thread_and_milestone when the thread
        is different
        '''
        mock_get_thread_and_milestone_from_rel_config.return_value = ('not_thread', 'milestone')
        self.assertFalse(is_rel_config_against_this_thread_and_milestone('rel_config', 'thread', 'milestone'))

    @patch('dmx.utillib.utils.get_thread_and_milestone_from_rel_config')
    def test_is_rel_config_against_this_thread_and_milestone_different_milestone(self,
                                                                              mock_get_thread_and_milestone_from_rel_config):
        '''
        Tests the is_rel_config_against_this_thread_and_milestone when the milestone
        is different
        '''
        mock_get_thread_and_milestone_from_rel_config.return_value = ('thread', 'not_milestone')
        self.assertFalse(is_rel_config_against_this_thread_and_milestone('rel_config', 'thread', 'milestone'))

    @patch('dmx.utillib.utils.get_thread_and_milestone_from_rel_config')
    def test_is_rel_config_against_this_thread_and_milestone_match(self,
                                                                              mock_get_thread_and_milestone_from_rel_config):
        '''
        Tests the is_rel_config_against_this_thread_and_milestone when they match
        '''
        rel_config = 'REL3.0ND5revA__14ww123a'
        thread = 'ND5revA'
        milestone = '3.0'
        mock_get_thread_and_milestone_from_rel_config.return_value = (thread, milestone)
        self.assertTrue(is_rel_config_against_this_thread_and_milestone(rel_config, thread, milestone))

    def test_normalize_config_name_non_rel(self):
        '''
        Tests the normalize_config_name function with a non-REL name
        '''
        config_name = 'dev'
        normalized_name = normalize_config_name(config_name)
        self.assertEqual(config_name, normalized_name)

    def test_normalize_config_name_snap(self):
        '''
        Tests the normalize_config_name function with a snap- config name
        '''
        config_name = 'snap-foo-bar'
        normalized_name = normalize_config_name(config_name)
        self.assertEqual(config_name, normalized_name)

    def test_normalize_config_name_works(self):
        '''
        Tests the normalize_rel_config_name function with a REL config
        '''
        config_name = 'REL3.0--THREAD-LABEL__14ww123asd'
        normalized_name = 'REL3.0-THREAD-LABEL-14ww123asd'
        self.assertEqual(normalize_config_name(config_name), normalized_name)

    @patch('dmx.utillib.utils.utildt.date', FakeDate)
    def test_get_ww_details(self):
        '''
        Tests the get_ww_details method
        '''
        from datetime import date
        FakeDate.today = classmethod(lambda cls: date(2016, 12, 19))

        self.assertEqual(get_ww_details(), ('16', '52', '1'))

    @patch('dmx.utillib.utils.utildt.date', FakeDate)
    def test_get_ww_details_single_digit_ww(self):
        '''
        Tests the get_ww_details method with a single digit ww
        '''
        from datetime import date
        FakeDate.today = classmethod(lambda cls: date(2016, 1, 4))

        self.assertEqual(get_ww_details(), ('16', '02', '1'))


    def test_run_as_user(self):
        '''
        Tests the run_as_user contextmanager method
        '''
        default_user = os.getenv('P4USER', False)

        original_user = 'fake.user'
        os.environ['P4USER'] = original_user
        forced_user = 'not.a.real.user'

        with run_as_user(forced_user):
            self.assertEqual(os.environ['P4USER'], forced_user)

        self.assertEqual(os.environ['P4USER'], original_user)

        ### rollback to default environment settings, otherwise all following tests will fail
        if default_user:
            os.environ['P4USER'] = default_user
        else:
            del os.environ['P4USER']


    def test_format_configuration_name_for_printing_simple(self):
        '''
        Tests the format_configuration_name_for_printing function with a simple config
        '''
        project = 'project'
        variant = 'variant'
        libtype = 'libtype'
        config = 'config'

        formatted_config = format_configuration_name_for_printing(project, variant, config,
                                                                  libtype=libtype)

        self.assertEqual(formatted_config, '{0}/{1}:{2}@{3}'.format(
            project, variant, libtype, config
        ))

    def test_format_configuration_name_for_printing_composite(self):
        '''
        Tests the format_configuration_name_for_printing function with a composite config
        '''
        project = 'project'
        variant = 'variant'
        config = 'config'

        formatted_config = format_configuration_name_for_printing(project, variant, config)

        self.assertEqual(formatted_config, '{0}/{1}@{2}'.format(
            project, variant, config
        ))

    def test_split_pv(self):
        '''
        Tests the split_pv function
        '''
        project = 'project'
        variant = 'variant'

        (ret_project, ret_variant) = split_pv('{0}/{1}'.format(project, variant))

        self.assertEqual(project, ret_project)
        self.assertEqual(variant, ret_variant)

    def test_split_pvc(self):
        '''
        Tests the split_pvc function
        '''
        project = 'project'
        variant = 'variant'
        config = 'config'

        (ret_project, ret_variant, ret_config) = split_pvc('{0}/{1}@{2}'.format(project,
                                                                                variant,
                                                                                config))

        self.assertEqual(project, ret_project)
        self.assertEqual(variant, ret_variant)
        self.assertEqual(config, ret_config)

    def test_split_pvl(self):
        '''
        Tests the split_pvl function
        '''
        project = 'project'
        variant = 'variant'
        libtype = 'libtype'

        (ret_project, ret_variant, ret_libtype) = split_pvl('{0}/{1}:{2}'.format(project,
                                                                                 variant,
                                                                                 libtype))

        self.assertEqual(project, ret_project)
        self.assertEqual(variant, ret_variant)
        self.assertEqual(libtype, ret_libtype)

    def test_split_pvlc(self):
        '''
        Tests the split_pvlc function
        '''
        project = 'project'
        variant = 'variant'
        libtype = 'libtype'
        config = 'config'

        (ret_project, ret_variant, ret_libtype, ret_config) = split_pvlc('{0}/{1}:{2}@{3}'.format(
            project, variant, libtype, config))

        self.assertEqual(project, ret_project)
        self.assertEqual(variant, ret_variant)
        self.assertEqual(libtype, ret_libtype)
        self.assertEqual(config, ret_config)

    def test_print_errors(self):
        cmd = 'my cmd'
        exitcode = '99'
        stdout = 'my stdout'
        stderr = 'my stderr'

        if sys.version_info[0] > 2:
            capturedOutput = io.StringIO()
        else:
            import cStringIO
            capturedOutput = cStringIO.StringIO() 
        sys.stdout = capturedOutput
        print_errors(cmd, exitcode, stdout, stderr, exit=False)
        sys.stdout = sys.__stdout__                  
        self.assertEqual('Command: my cmd\nExitcode: 99\nStdout: my stdout\nStderr: my stderr\n', capturedOutput.getvalue())

    def _test_get_psg_id_search_idsid_by_wwid__got_user(self):
        '''
        This test is only True if user 'wplim' still in this company
        '''
        USER_WPLIM_EXISTS = True
        cmd = 'finger wplim'
        result = subprocess.check_output(cmd, shell=True)
        if 'no such user' in result:
            USER_WPLIM_EXISTS = False

        if USER_WPLIM_EXISTS:
            self.assertEqual('wplim', get_psg_id_search_idsid_by_wwid('11644910'))

    def _test_get_psg_id_search_idsid_by_wwid__no_user(self):
        self.assertEqual('', get_psg_id_search_idsid_by_wwid('12836'))
    
    def _test_get_psg_id_search_info_by_userid_got_user(self):
        '''
        This test is only True if user 'wplim' still in this company
        '''
        infokeys = ['mailNickname', 'cn', 'intelSuperGroupCode', 'intelDivisionCode', 'userPrincipalName', 'manager', 'intelExportCountryGroup', 'intelBldgCode', 'employeeID', 'employeeType', 'intelOrgUnitDescr', 'intelOrgUnitCode', 'intelRegionCode', 'intelCostCenterShortName', 'department', 'mail', 'mgrWWID', 'dn', 'intelGroupDescr', 'sAMAccountName', 'intelSuperGroupDescr', 'physicalDeliveryOfficeName', 'intelExportCountryCode', 'displayName', 'name', 'l', 'intelGroupCode', 'sn', 'intelDivisionDescr']
        USER_WPLIM_EXISTS = True
        cmd = 'finger wplim'
        result = subprocess.check_output(cmd, shell=True)
        if 'no such user' in result:
            USER_WPLIM_EXISTS = False

        if USER_WPLIM_EXISTS:
            self.assertEqual(infokeys, list(get_psg_id_search_info_by_userid('wplim').keys()))

    def _test_get_psg_id_search_info_by_userid_got_user(self):
        with self.assertRaises(Exception):
            list(get_psg_id_search_info_by_userid('no_such_user').keys())

    @patch('dmx.utillib.utils.get_site', return_value='png')
    def _test__get_proj_disk(self, mock_get_site):
        result = ['/nfs/site/disks/da_i10', '/nfs/site/disks/da_regressioni10_', '/nfs/site/disks/fm8_', '/nfs/site/disks/fm6_', '/nfs/site/disks/fm5_', '/nfs/site/disks/fm3_', '/nfs/site/disks/fln_', '/nfs/site/disks/falcon_', '/nfs/site/disks/falcon_dmx_1', '/nfs/site/disks/fln_scratch_1', '/nfs/site/disks/fln_sion_1', '/nfs/site/disks/fln_scratch_1', '/nfs/site/disks/tech_modelingi10_1', '/nfs/site/disks/tech_processi10_1', '/nfs/site/disks/da_infra_1', '/nfs/site/disks/da_fbi10_1', '/nfs/site/disks/da_scratch_1', '/nfs/site/disks/da_i10dmetric_1', '/nfs/site/disks/da_NBSJ_1', '/nfs/site/disks/da_NBSC_1', '/nfs/site/disks/psg_sion_1', '/nfs/site/disks/psg_dmx_1', '/nfs/site/disks/psg_tnr_1', '/nfs/site/disks/psg_cicq_', '/nfs/site/disks/da_infra_']
        self.assertTrue(set(result).issuperset(set(get_proj_disk('i10socfm'))))

    def test__get_site__sc(self):
        self.assertEqual('sc',get_site('sjicmdev1.sc.intel.com:1666'))

    def test__get_site__png(self):
        self.assertEqual('png',get_site('ppgicm.png.intel.com:1666'))

    def test__check_proj_restrict(self):
        self.assertEqual(1, check_proj_restrict('i10socfm','/nfs/site/disks/da_i10/blabla'))

if __name__ == '__main__':
    unittest.main()
