#!/usr/bin/env python
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/dmxcmd/test_dmx_snap_systemtest.py $
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

class TestSnapSystemtest(unittest.TestCase):
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
        self.dconfig = 'snap-for_test_dmx_snap_systemtest___'
        self.delfilter = ['ipspec', 'reldoc']
        
    def tearDown(self):
        pass

    def test_001___dmx_snap_systemtest(self):
        print("\n##############################\n### Cleaning up .......")
        cmd = 'gdp {} delete /intel/{}/{}/{}'.format(self.asadmin, self.project, self.variant, self.dconfig)
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
       


    def test_002___dmx_snap_systemtest(self):
        print("\n##############################\n### Snapping .......")
        cmd = '{} snap -p {} -i {} -b {} --deliverable-filter {} -s {} --debug '.format(self.dmx, self.project, self.variant, self.sconfig, ' '.join(self.delfilter), self.dconfig)
        print("- running: {}".format(cmd))
        out = self.rc(cmd, maxtry=1)
        self._print(out)
        print("\n##############################\n### Verifying Snapping ... ......")
        cmd = '{} report list -p {} -i {} -b {}'.format(self.dmx, self.project, self.variant, self.dconfig)
        print("- running: {}".format(cmd))
        out = self.rc(cmd, maxtry=1)
        self._print(out)
        self.assertIn("Found 1 match", out[1]+out[2])
        print("\n##############################\n### PASS: Span Verified!") 
    

    def test_003___dmx_snap_systemtest(self):
        print("\n##############################\n### Verifying Snapping ... ......")
        cmd = '{} report content -p {} -i {} -b {}'.format(self.dmx, self.project, self.variant, self.dconfig)
        print("- running: {}".format(cmd))
        out = self.rc(cmd, maxtry=1)
        self._print(out)
        ### Raton_Mesa/rtmliotest1/ipspec/dev/snap-for_test_dmx_snap_systemtest___
        self.assertIn("{}/{}:{}@{}".format(self.project, self.variant, self.delfilter[0], self.dconfig), out[1]+out[2])
        self.assertIn("{}/{}:{}@{}".format(self.project, self.variant, self.delfilter[1], self.dconfig), out[1]+out[2])
        print("\n##############################\n### PASS: Span Verified!") 
       

       
    def test_004___dmx_snap_systemtest(self):
        print("\n##############################\n### Cleaning up .......")
        cmd = 'gdp {} delete /intel/{}/{}/{}'.format(self.asadmin, self.project, self.variant, self.dconfig)
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
       




        


    def _print(self, output):
        exitcode, stdout, stderr = output
        print("exitcode: {}\n".format(exitcode))
        print("stdout: {}\n".format(stdout))
        print("stderr: {}\n".format(stderr))


if __name__ == '__main__':
    unittest.main()
