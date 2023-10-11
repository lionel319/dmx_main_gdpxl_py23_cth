#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr icm library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/integration_tests/dmx/test_import.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import os, sys

'''
This test is to be run once before deploy and once after deploy
If this test is run before deploy, it should be run in a shell without dmx/main. Test will import python modules from user's local workspace
If this test is run after deploy, it should run in a shell with dmx/main. Test will import python modules from production area (/tools or /p/psg/flows/common)
'''
LIB = os.getenv('DMX_LIB', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python'))
sys.path.insert(0, LIB)

class TestImport(unittest.TestCase):
    def test_import_python_modules(self):
        '''
        Verify all python modules able to be imported
        '''
        for root, dirs, files in os.walk(LIB):
            # Skipped IPQC as they are written in python 3
            if 'ipqc' in root or 'python_common' in root:
                continue                            
            for file in files:          
                print "file:{}".format(file)
                # Skip this file as this file is meant to be run from another location, not from dmx.syncpointlib
                if 'syncpoint_cron_run' in file:
                    continue
                # Skip all modules from splunk_sdk tnrlib                     
                if 'splunk_sdk' in root:
                    continue                    
                if 'setup' in file or 'ipspec_check'in file:
                    continue
                if 'django' in file or 'models.py' in file:
                    ''' http://pg-rdjira:8080/browse/DI-1037 '''
                    continue
                if 'mw_submit' in file:
                    continue
                if 'icm_login2.0' in file:
                    continue
                if 'connection_cext' in file:
                    continue
                if 'cursor_cext' in file:
                    continue
                if file.endswith('.py') and not root.split('/')[-1].startswith('_') and os.path.exists(os.path.join(root, '__init__.py')):
                    python_module = '.'.join(root.split('/python/')[1:] + [file]).split('.py')[0].replace('/', '.')
                    print "python_module:{}".format(python_module)
                    if 'django' in python_module:
                        continue
                    self.assertTrue(__import__(python_module))
                                            
    def test_import_dm_softlink(self):
        '''
        Verify all dm modules able to be imported from dm softlink
        '''
        dm_path = os.path.join(LIB, 'dm')
        for root, dirs, files in os.walk(dm_path):
            for file in files:                
                if file.endswith('.py') and not root.split('/')[-1].startswith('_') and os.path.exists(os.path.join(root, '__init__.py')):
                    if 'setup' in file:
                        continue
                    if 'mw_submit' in file:
                        continue
                    python_module = '.'.join(root.split('/python/')[1:] + [file]).split('.py')[0].replace('/', '.')
                    print python_module
                    self.assertIn('dmx', str(__import__(python_module)))

    def test_import_abnrlib_softlink(self):
        '''
        Verify all abnrlib modules able to be imported from abnrlib softlink
        '''
        dm_path = os.path.join(LIB, 'abnrlib')
        for root, dirs, files in os.walk(dm_path):
            for file in files:                
                if file.endswith('.py') and not root.split('/')[-1].startswith('_') and os.path.exists(os.path.join(root, '__init__.py')):
                    python_module = '.'.join(root.split('/python/')[1:] + [file]).split('.py')[0].replace('/', '.')
                    self.assertIn('dmx', str(__import__(python_module)))

    def test_import_dmxlib_softlink(self):
        '''
        Verify all abnrlib modules able to be imported from dmxlib softlink
        '''
        dm_path = os.path.join(LIB, 'dmx', 'dmxlib')
        for root, dirs, files in os.walk(dm_path):
            for file in files:                
                if file.endswith('.py') and not root.split('/')[-1].startswith('_') and os.path.exists(os.path.join(root, '__init__.py')):
                    python_module = '.'.join(root.split('/python/')[1:] + [file]).split('.py')[0].replace('/', '.')
                    self.assertTrue(__import__(python_module))

if __name__ == '__main__':
    unittest.main()
