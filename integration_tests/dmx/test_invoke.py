#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/integration_tests/dmx/test_invoke.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import os, sys

'''
This test is to be run once before deploy and once after deploy
If this test is run before deploy, it should be run in a shell without dmx/main. Test will import python modules and run binary from user's local workspace
If this test is run after deploy, it should run in a shell with dmx/main. Test will import python modules and run binary from production area (/tools or /p/psg/flows/common)
'''
BIN = os.path.join(os.getenv('DMX_ROOT', os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))), 'bin')
LIB = os.getenv('DMX_LIB', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python'))
sys.path.insert(0, LIB)
from dmx.utillib.utils import run_command

class TestInvoke(unittest.TestCase):
    def test_invoke_python_binary(self):
        checklist = [
            'dmx.py', 'audit_tcl.py', 'get_waivers.py', 'get_waivers_es.py', 'md5tnr.py',
            'release_status.py', 'saveworkspace.py', 'sion.py', 'syncpoint.py', 'syncpoint_user.py',
            'update_rel_config_request_id.py'
        ]

        for file in checklist:
            python_binary = os.path.join(BIN, file)
            command = ['python', python_binary, '-h']
            command = ' '.join(command)
            print "command: {}".format(command)
            print "file: {}".format(file)

            ### Only test the following binaries
            if file in checklist:
                exitcode, stdout, stderr = run_command(command)
                self.assertEqual(0, exitcode)
                                            
if __name__ == '__main__':
    unittest.main()
