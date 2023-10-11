#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/utillib/test_utils.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
import inspect
import os
import sys
import re
import logging
from mock import patch

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.utils as u


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.datadir = os.path.join(os.path.dirname(__file__), 'data')

    def test_010___get_release_ver_map___not_found(self):
        os.environ['DMX_SETTING_FILES_DIR'] = self.datadir
        ret = u.get_release_ver_map('abc', 'def')
        del os.environ['DMX_SETTING_FILES_DIR']
        self.assertEqual(ret, [])

    def test_020___get_release_ver_map___found(self):
        os.environ['DMX_SETTING_FILES_DIR'] = self.datadir
        ret = u.get_release_ver_map('FM4revC3', '6.0')
        del os.environ['DMX_SETTING_FILES_DIR']
        self.assertEqual(ret, ['5.0', '5.1'])

    def test_030___get_dmx_setting_files_dir___with_DMX_SETTING_FILES_DIR_defined(self):
        os.environ["DMX_SETTING_FILES_DIR"] = "/a/b/c"
        ret = u.get_dmx_setting_files_dir()
        del os.environ['DMX_SETTING_FILES_DIR']
        self.assertEqual(ret, '/a/b/c')

    def test_040___get_dmx_setting_files_dir___with_DMX_SETTING_FILES_DIR_undefined(self):
        try:
            del os.environ['DMX_SETTING_FILES_DIR']
        except:
            pass
           
        ret = u.get_dmx_setting_files_dir()
        if 'DMX_ROOT' in os.environ and os.environ['DMX_ROOT']:
            ans = os.path.realpath(os.path.join(os.environ['DMX_ROOT'], '..', 'dmx_setting_files'))
            self.assertEqual(ret, ans)

    def test_050___load_release_ver_map(self):
        os.environ['DMX_SETTING_FILES_DIR'] = self.datadir
        ret = u.load_release_ver_map()
        del os.environ['DMX_SETTING_FILES_DIR']
        self.assertEqual(ret, {u'FM4revC3': {u'6.0': {u'dmx': u'5.0', u'dmxdata': u'5.1'}}})

    def test_060___is_string_icm_command___icmp4_true(self):
        self.assertTrue(u.is_string_icm_command('icmp4 submit -d "testing" ...'))

    def test_060___is_string_icm_command___underscore_icmp4_true(self):
        self.assertTrue(u.is_string_icm_command('_icmp4 submit -d "testing" ...'))

    def test_060___is_string_icm_command___pm_true(self):
        self.assertTrue(u.is_string_icm_command('pm workspace -l -u lionelta'))

    def test_060___is_string_icm_command___false(self):
        self.assertFalse(u.is_string_icm_command('echo "icmp4 info"'))

    def test_065___does_icm_meet_retry_condition___true_1(self):
        ''' Unknown MySQL server host '''
        exitcode, stdout, stderr = [0,
            'bla bla Unknown MySQL server host haha',
            '']
        self.assertTrue(u.does_result_meet_retry_condition(exitcode, stdout, stderr, u.get_icm_error_list()))
        
    def test_065___does_icm_meet_retry_condition___true_2(self):
        ''' Too many connections .*:Unable to connect '''
        exitcode, stdout, stderr = [0,
            'bla bla Too many connections haha hoho',
            'hello :Unable to connect lionel tan']
        self.assertTrue(u.does_result_meet_retry_condition(exitcode, stdout, stderr, u.get_icm_error_list()))
        
    def test_065___does_icm_meet_retry_condition___false(self):
        ''' Too many connections .*:Unable to connect '''
        exitcode, stdout, stderr = [0,
            'bla bla connections haha hoho',
            'hello connect lionel tan']
        self.assertFalse(u.does_result_meet_retry_condition(exitcode, stdout, stderr, u.get_icm_error_list()))
        
    def test_070___run_command___no_retry_because_not_icm_command(self):
        cmd = 'no_such_cmd lala'
        pattern = 'Tried .* times, .* more times for retry' 
        exitcode, stdout, stderr = u.run_command(cmd, maxtry=1, delay_in_sec=0)
        print("exitcode:{}\nstdout:{}\nstderr:{}".format(exitcode, stdout, stderr))
        self.assertFalse(re.search(pattern, stdout+stderr, re.MULTILINE|re.DOTALL))

    def test_070___run_command___no_retry_because_can_connect_to_icm(self):
        cmd = 'icmp4 info'
        pattern = 'Tried .* times, .* more times for retry' 
        exitcode, stdout, stderr = u.run_command(cmd, maxtry=1, delay_in_sec=0)
        print("exitcode:{}\nstdout:{}\nstderr:{}".format(exitcode, stdout, stderr))
        self.assertFalse(re.search(pattern, stdout+stderr, re.MULTILINE|re.DOTALL))

    @patch('dmx.utillib.utils.LOGGER')
    @patch('dmx.utillib.utils.is_string_icm_command')
    @patch('dmx.utillib.utils.does_result_meet_retry_condition')
    def test_070___run_command___retry_because_can_not_connect_to_icm___maxtry_1(self, mocka, mockb, mock_logging):
        cmd = 'dummy_cmd'
        exitcode, stdout, stderr = u.run_command(cmd, maxtry=1, delay_in_sec=0)
        print("exitcode:{}\nstdout:{}\nstderr:{}".format(exitcode, stdout, stderr))
        mock_logging.info.assert_called_with('Tried 0 times, 1 more times for retry ...')

    @patch('dmx.utillib.utils.LOGGER')
    @patch('dmx.utillib.utils.is_string_icm_command')
    @patch('dmx.utillib.utils.does_result_meet_retry_condition')
    def test_070___run_command___retry_because_can_not_connect_to_icm___maxtry_3(self, mocka, mockb, mock_logging):
        cmd = 'dummy_cmd'
        mocka.return_value = True
        mockb.return_value = True
        exitcode, stdout, stderr = u.run_command(cmd, maxtry=3, delay_in_sec=0)
        print("exitcode:{}\nstdout:{}\nstderr:{}".format(exitcode, stdout, stderr))
        print("call_count:{}".format(mock_logging.info.call_count))
        mock_logging.info.assert_any_call('Tried 2 times, 1 more times for retry ...')
        mock_logging.info.assert_any_call('Tried 1 times, 2 more times for retry ...')
        mock_logging.info.assert_any_call('Tried 0 times, 3 more times for retry ...')

    def test_070___run_command___test_timeout_works___timeout_not_activated(self):
        cmd = 'echo "start"; sleep 1; echo "end"'
        exitcode, stdout, stderr = u.run_command(cmd, timeout=10)
        print("exitcode:{}\nstdout:{}\nstderr:{}".format(exitcode, stdout, stderr))
        self.assertNotEqual(exitcode, None)

    def test_070___run_command___test_timeout_works___timeout_activated(self):
        cmd = 'echo "start"; sleep 2; echo "end"'
        exitcode, stdout, stderr = u.run_command(cmd, timeout=1)
        print("exitcode:{}\nstdout:{}\nstderr:{}".format(exitcode, stdout, stderr))
        self.assertEqual(exitcode, None)


    @patch('dmx.utillib.utils.run_command')
    def test_080___run_command_get_arc_job_id(self, mock_run_command):
        jobid = '12345678'
        exitcode = 0 
        stdout = '''
{}
Job <7213626> is submitted to queue <ice>.
'''.format(jobid)
        stderr = 'my name is lionel'
        mock_run_command.return_value = [exitcode, stdout, stderr]
        ret = u.run_command_get_arc_job_id('dummy_cmd')
        self.assertEqual(ret, (jobid, exitcode, stdout, stderr))


    def test_090___is_pice_env(self):
        self.assertTrue(u.is_pice_env())

    def test_100___get_thread_and_milestone_from_rel_config___pass(self):
        ret = u.get_thread_and_milestone_from_rel_config('REL4.0FM6revB0__15ww123a')
        self.assertEqual(ret, ('FM6revB0', '4.0'))

    def test_100___get_thread_and_milestone_from_rel_config___fail(self):
        ret = u.get_thread_and_milestone_from_rel_config('PREL4.0FM6revB0__15ww123a')
        self.assertEqual(ret, (None, None))
    
    def test_101___get_thread_and_milestone_from_prel_config_strict_REL___fail(self):
        ret = u.get_thread_and_milestone_from_prel_config('REL4.0FM6revB0__15ww123a', strict=True)
        self.assertEqual(ret, (None, None))

    def test_101___get_thread_and_milestone_from_prel_config_strict_PREL___pass(self):
        ret = u.get_thread_and_milestone_from_prel_config('PREL4.0FM6revB0__15ww123a', strict=True)
        self.assertEqual(ret, ('FM6revB0', '4.0'))

    def test_101___get_thread_and_milestone_from_prel_config_nostrict_REL___pass(self):
        ret = u.get_thread_and_milestone_from_prel_config('REL4.0FM6revB0__15ww123a')
        self.assertEqual(ret, ('FM6revB0', '4.0'))

    def test_101___get_thread_and_milestone_from_prel_config_nostrict_PREL___pass(self):
        ret = u.get_thread_and_milestone_from_prel_config('PREL4.0FM6revB0__15ww123a')
        self.assertEqual(ret, ('FM6revB0', '4.0'))

    def test_110___get_default_dev_config(self):
        self.assertEqual(u.get_default_dev_config(family='Falcon', icmproject='i10socfm'), 'fmx_dev')
        self.assertEqual(u.get_default_dev_config(family='Falcon', icmproject='hpsi10'), 'fmx_dev')
        self.assertEqual(u.get_default_dev_config(family='Falconpark', icmproject='i10socfm'), 'fp8_dev')
        self.assertEqual(u.get_default_dev_config(family='Falconpark', icmproject='hpsi10'), 'fp8_dev')
        self.assertEqual(u.get_default_dev_config(thread='GDRrevB0', icmproject='gdr'), 'gdr_revB0_dev')
        self.assertEqual(u.get_default_dev_config(thread='xxx', icmproject='xxx'), 'dev')



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
