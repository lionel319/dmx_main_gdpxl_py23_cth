#!/usr/bin/env python
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_bom_systemtest.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
import inspect
import os
import sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.utillib.utils

class TestDmxBomSystemtest(unittest.TestCase):
    '''
    This systemtest is a REAL test that will execute real 'write' command to the database.
    Here's the strings of commands that will be carried out:-

    - the bom that will be used for this systemtest is 
        > ___for_test_dmx_bom_systemtest___
    - clean up
        > gdp delete <bom>
    - 'dmx clone bom' from 'dev'
        > run 'dmx report content' to validate
    - 'dmx bom edit --delbom ipspec'
        >run 'dmx report content' to validate
    - 'dmx bom edit --addbom ipspec'
        >run 'dmx report content' to validate
    - 'dmx bom delete'
        > run 'dmx report list' to validate

    Summary Of Tested DMX commands:-
    - dmx blone bom
    - dmx edit bom --delbom
    - dmx edit bom --addbom
    - dmx delete bom
    - dmx report list
    - dmx report content
    '''
    def setUp(self):
        self.dmx = os.path.join(LIB, '..', '..', 'bin', 'dmx.py')
        self.rc = dmx.utillib.utils.run_command
        self.asadmin = '--user=icmanage'

        self.project = 'Raton_Mesa'
        self.variant = 'rtmliotest1'
        self.sconfig = 'dev'
        self.dconfig = '___for_test_dmx_bom_systemtest___'
        
    def tearDown(self):
        pass

    def test_001___dmx_bom_systemtest(self):
        print("\n##############################\n### Cleaning up .......")
        cmd = 'gdp delete /intel/{}/{}/{}'.format(self.project, self.variant, self.dconfig)
        print("- running: {}".format(cmd))
        out = self.rc(cmd, maxtry=1)
        self._print(out)
        print("\n##############################\n### Verifying Clean up ......")
        cmd = '{} report list -p {} -i {} -b {}'.format(self.dmx, self.project, self.variant, self.dconfig)
        print("- running: {}".format(cmd))
        out = self.rc(cmd, maxtry=1)
        self._print(out)
        self.assertIn("Found 0 match", out[1]+out[2])
        print("\n##############################\n### PASS: Cleaning Verified!") 
       

    def test_002___dmx_bom_systemtest(self):
        print("\n##############################\n### Cloning Bom ...!") 
        cmd = '{} bom clone -p {} -i {} -b {} --dstbom {} --debug '.format(self.dmx, self.project, self.variant, self.sconfig, self.dconfig)
        print("- running: {}".format(cmd))
        out = self.rc(cmd, maxtry=1)
        self._print(out)
        print("\n##############################\n### Verifying Cloning Bom ...!") 
        cmd = '{} report list -p {} -i {} -b {}'.format(self.dmx, self.project, self.variant, self.dconfig)
        print("- running: {}".format(cmd))
        out = self.rc(cmd, maxtry=1)
        self._print(out)
        self.assertIn("Found 1 match", out[1]+out[2])
        print("\n##############################\n### PASS: Cloning Bom Verified!") 


    def test_003___dmx_bom_systemtest(self):
        print("\n##############################\n### Edit Bom (--delbom) ...!") 
        cmd = '{} bom edit -p {} -i {} -b {} --delbom {}/{}:ipspec --debug --inplace'.format(self.dmx, self.project, self.variant, self.dconfig, self.project, self.variant)
        print("- running: {}".format(cmd))
        out = self.rc(cmd, maxtry=1)
        self._print(out)
        print("\n##############################\n### Verifying Bom Edit (--delbom)...!") 
        cmd = '{} report content -p {} -i {} -b {}'.format(self.dmx, self.project, self.variant, self.dconfig)
        print("- running: {}".format(cmd))
        out = self.rc(cmd, maxtry=1)
        self._print(out)
        self.assertFalse('Raton_Mesa/rtmliotest1:ipspec' in out[1]+out[2])
        print("\n##############################\n### PASS: Bom Edit (--delbom) Verified!") 


    def test_004___dmx_bom_systemtest(self):
        print("\n##############################\n### Edit Bom (--addbom) ...!") 
        cmd = '{} bom edit -p {} -i {} -b {} --addbom {}/{}:ipspec@dev --debug --inplace'.format(self.dmx, self.project, self.variant, self.dconfig, self.project, self.variant)
        print("- running: {}".format(cmd))
        out = self.rc(cmd, maxtry=1)
        self._print(out)
        print("\n##############################\n### Verifying Bom Edit (--delbom)...!") 
        cmd = '{} report content -p {} -i {} -b {}'.format(self.dmx, self.project, self.variant, self.dconfig)
        print("- running: {}".format(cmd))
        out = self.rc(cmd, maxtry=1)
        self._print(out)
        self.assertTrue('Raton_Mesa/rtmliotest1:ipspec' in out[1]+out[2])
        print("\n##############################\n### PASS: Bom Edit (--addbom) Verified!") 


    def test_005___dmx_bom_systemtest(self):
        print("\n##############################\n### Bom Delete ...!") 
        cmd = '{} bom delete -p {} -i {} -b {} --debug '.format(self.dmx, self.project, self.variant, self.dconfig)
        print("- running: {}".format(cmd))
        out = self.rc(cmd, maxtry=1)
        self._print(out)
        print("\n##############################\n### Verifying Bom Delete...!") 
        cmd = '{} report list -p {} -i {} -b {}'.format(self.dmx, self.project, self.variant, self.dconfig)
        print("- running: {}".format(cmd))
        out = self.rc(cmd, maxtry=1)
        self._print(out)
        self.assertIn("Found 0 match", out[1]+out[2])
        print("\n##############################\n### PASS: Bom Delete Verified!") 


        


    def _print(self, output):
        exitcode, stdout, stderr = output
        print("exitcode: {}\n".format(exitcode))
        print("stdout: {}\n".format(stdout))
        print("stderr: {}\n".format(stderr))


if __name__ == '__main__':
    unittest.main()
