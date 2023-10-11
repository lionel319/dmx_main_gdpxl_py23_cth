#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_releasesubmit.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $


from __future__ import print_function
from builtins import object
import unittest
from mock import patch
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.releasesubmit import *
from dmx.utillib.utils import is_pice_env

class TestReleaseQueue(unittest.TestCase):
    '''
    Tests the functions in the releasesubmit library
    '''
    @patch('dmx.abnrlib.releasesubmit.Server')
    def setUp(self, mock_server):
        self.handler = ReleaseJobHandler('id')

    @patch('dmx.abnrlib.releasesubmit.Server')
    @patch('dmx.abnrlib.releasesubmit.run_command')
    @patch('dmx.abnrlib.releasesubmit.IcmConfig')
    @patch('dmx.ecolib.ecosphere.EcoSphere')
    def test_001___submit_release_stdout_less_than_2_lines(self, mock_eco, mock_composite_config, mock_run_command, mock_server):
        '''
        Tests the submit_release function when it fails
        '''
        mock_run_command.return_value = (1, 'a', '')
        mock_config = mock_composite_config.return_value
        with self.assertRaises(ReleaseQueueError):
            submit_release(mock_config, 'input_config', 'milestone', 'thread', 'label', '123')

    @patch('dmx.abnrlib.releasesubmit.Server')
    @patch('dmx.abnrlib.releasesubmit.run_command')
    @patch('dmx.abnrlib.releasesubmit.IcmConfig')
    @patch('dmx.ecolib.ecosphere.EcoSphere')
    def test_002___submit_release_fails(self, mock_eco, mock_composite_config, mock_run_command, mock_server):
        '''
        Tests the submit_release function when it fails
        '''
        mock_run_command.return_value = (1, 'a\nb', '')
        mock_config = mock_composite_config.return_value
        with self.assertRaisesRegexp(ReleaseQueueError, 'Problem Dispatching Job'):
            submit_release(mock_config, 'input_config', 'milestone', 'thread', 'label', '123')


    @patch('dmx.abnrlib.releasesubmit.Server')
    @patch('dmx.abnrlib.releasesubmit.run_command')
    @patch('dmx.abnrlib.releasesubmit.IcmConfig')
    @patch('dmx.ecolib.ecosphere.EcoSphere')
    def test_003___submit_release_works(self, mock_eco, mock_composite_config, mock_run_command, mock_server):
        '''
        Tests the submit_release function when it works
        '''
        stdout = '123\nJob submitted to queue xxx'
        mock_run_command.return_value = (0, stdout, '')
        mock_config = mock_composite_config.return_value
        self.assertEqual((True, '123'), 
                          submit_release(mock_config, 'input_config', 'milestone', 'thread', 'label',
                          '234'))

    @patch('dmx.abnrlib.releasesubmit.Server')
    @patch('dmx.abnrlib.releasesubmit.run_command')
    @patch('dmx.abnrlib.releasesubmit.IcmConfig')
    @patch('dmx.ecolib.ecosphere.EcoSphere')
    def test_004___submit_release_preview(self, mock_eco, mock_composite_config, mock_run_command, mock_server):
        '''
        Tests the submit_release function in preview mode
        '''
        mock_run_command.return_value = (0, '', '')
        mock_config = mock_composite_config.return_value
        self.assertEqual((True, None), 
                          submit_release(mock_config, 'input_config', 'milestone', 'thread', 'label',
                          '123', preview=True))       

    @patch('dmx.abnrlib.releasesubmit.WaiverFile.load_from_file')
    def test_005___convert_waiver_files(self, mock_load_from_file):
        '''
        Tests the convert_waiver_files function
        '''
        mock_load_from_file.return_value = True
        waiver_files = ['file1', 'file2', 'file3']

        wf = convert_waiver_files(waiver_files)

        self.assertTrue(wf)

    @patch('dmx.abnrlib.releasesubmit.WaiverFile.load_from_file')
    def test_006___convert_waiver_files_file_in_bad_format(self, mock_load_from_file):
        '''
        Tests the convert_waiver_files function when the waiver file is in
        a bad format
        '''
        mock_load_from_file.side_effect = IndexError('bad times')

        with self.assertRaises(ReleaseQueueError):
            convert_waiver_files(['file1'])

    def _test_007___get_tnr_dashboard_url_for_id(self):
        '''
        Tests the get_tnr_dashboard_url_for_id function
        '''
        abnr_id = 'test_id'
        project = 'test_project'
        variant = 'test_variant'
        requestor = 'test_requestor'
        libtype = 'test_libtype'
        ret = get_tnr_dashboard_url_for_id(abnr_id, project, requestor, variant, libtype)
        print(ret)
        if is_pice_env():
            suffix = '?form.project={0}&form.user={1}&form.variant={2}&form.libtype={3}'.format(project, requestor, variant, libtype)
            self.assertTrue(get_tnr_dashboard_url_for_id(abnr_id, project, requestor, variant, libtype).endswith(suffix))
        else:            
            self.assertTrue(get_tnr_dashboard_url_for_id(abnr_id).endswith('?abnr_release_id={0}'.format(abnr_id)))

    @patch('dmx.abnrlib.releasesubmit.run_command')
    def _test_008___get_job_status_works(self, mock_run_command):
        '''
        Tests the get_job_status function when it works
        '''
        mock_run_command.return_value = (0, 'status', '')
        self.assertEqual('status', self.handler.get_job_status())

    @patch('dmx.abnrlib.releasesubmit.run_command')
    def test_009___get_job_status_fails(self, mock_run_command):
        '''
        Tests the get_job_status function when it fails
        '''
        mock_run_command.return_value = (1, '', '')
        with self.assertRaises(Exception):
            self.handler.get_job_status()

    @patch('dmx.abnrlib.releasesubmit.run_command')
    def _test_010___get_job_stdout_works(self, mock_run_command):
        '''
        Tests the get_job_stdout function when it works
        '''
        mock_run_command.return_value = (0, 'line1\nline2', '')
        self.assertEqual('line1', self.handler.get_job_stdout()[0])
        self.assertEqual('line2', self.handler.get_job_stdout()[1])

    @patch('dmx.abnrlib.releasesubmit.run_command')
    def test_011___get_job_stdout_fails(self, mock_run_command):
        '''
        Tests the get_job_stdout function when it fails
        '''
        mock_run_command.return_value = (1, '', '')
        with self.assertRaises(Exception):
            self.handler.get_job_stdout()

    @patch('dmx.abnrlib.releasesubmit.ReleaseJobHandler.get_job_stdout')
    @patch('dmx.abnrlib.releasesubmit.ReleaseJobHandler.get_job_status')
    @patch('dmx.abnrlib.releasesubmit.time.sleep')
    def test_012___wait_for_job_completion_done(self, mock_sleep, mock_get_job_status, mock_get_job_stdout):
        '''
        Tests the wait_for_job_completion if the job is done
        '''
        mock_sleep.return_value = None
        mock_get_job_status.side_effect = ['queued', 'running', 'done']
        mock_get_job_stdout.return_value = ['line1', 'Rel Config: REL123']
        self.assertFalse(self.handler.wait_for_job_completion())
        self.assertEqual(self.handler.rel_config, 'REL123')

    @patch('dmx.abnrlib.releasesubmit.ReleaseJobHandler.get_job_status')
    @patch('dmx.abnrlib.releasesubmit.time.sleep')
    def test_013___wait_for_job_completion_failed(self, mock_sleep, mock_get_job_status):
        '''
        Tests the wait_for_job_completion if the job failed
        '''
        mock_sleep.return_value = None
        mock_get_job_status.side_effect = ['queued', 'running', 'failed']
        self.assertFalse(self.handler.wait_for_job_completion())
        self.assertEqual(self.handler.rel_config, None)
                          
    def test_014___views_and_prel_cannot_submit_together___failed(self):
        class immutable_config(object): pass
        immutable_config.project = 'i10socfm'
        immutable_config.variant = 'liotest1'
        immutable_config.config = 'dev'
        with self.assertRaisesRegexp(ReleaseQueueError, "can not be used together"):
            submit_release(immutable_config, 'dev', '3.0', 'FM6revB0', 'haha',                
                  'abnr_id', libtype=None, preview=False, 
                  waivers=None, description="", views=['view_1'],
                  syncpoint='', skipsyncpoint='', skipmscheck='', regmode=False,
                  prel='prel_1')


if __name__ == '__main__':
    unittest.main()
