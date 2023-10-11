#!/usr/bin/env python
# Copyright 2012 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/deliverables_test/example2/CheckData.py#1 $

"""
Verification Platform data check example using a shell script to test.

File dm/deliverables_test/example2/CheckData.py, unit tested
in dm.Vp_test.test_example2CheckType().

Do not modify this file in order to test functionality because it is
specifically for use in the vp.py documentation.
"""

__author__ = "John McGehee, (jmcgehee@altera.com)"
__version__ = "$Revision: #1 $"

# pylint: disable=R0201
import os
import unittest
import subprocess
from dm.Vp import Vp

# enable parallel execution of tests
_multiprocess_can_split_ = True

class Check(unittest.TestCase): #pylint: disable-msg=R0904
    """Data check for deliverable EXAMPLE2"""
    
    def SetUp(self):
        pass

    def TearDown(self):
        pass


    def test_content(self):
        """Check 'file' file contents"""

        # Use the dm.DeliverableParser API to get file names from the templateset
        manifest = Vp.manifest
        # Get the files in deliverable EXAMPLE2 with id="file"
        fileNames = manifest.getDeliverablePattern('EXAMPLE2', 'file')
        assert len(fileNames) == 1, 'Only one file expected'

        # Run CheckDataShellScript.sh in a subprocess,
        # capturing the output in a log file.
        logFileName = os.path.join(Vp.getLogDirName(), 'EXAMPLE2.dataCheck.log')
        logFile = open(logFileName, 'w')
        programName = os.path.join(os.path.dirname(__file__), 'CheckDataShellScript.sh')
        status = subprocess.call(
            "{} {}".format(programName, fileNames.pop()),
            stdout=logFile,
            stderr=subprocess.STDOUT,
            shell=True)
        logFile.close()
        
        self.assertFalse(status, 'CheckDataShellScript.sh found file content mismatch')

    # Add as many tests as you like, all with names starting with 'test_'.
    # For example, this trivial test always passes. 
    def test_alwaysPass(self):
        """Test that always passes"""
        self.assertTrue(True, msg='EXAMPLE2 data check that always passes')
