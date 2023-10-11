#!/usr/bin/env python
# Copyright 2012 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/deliverables_test/example1/CheckData.py#1 $

"""
Verification Platform data check example using Python unit test.

File dm/deliverables_test/example1/CheckData.py, unit tested
in dm.Vp_test.test_example1CheckType().

Do not modify this file in order to test functionality because it is
specifically for use in the vp.py documentation.
"""

__author__ = "John McGehee, (jmcgehee@altera.com)"
__version__ = "$Revision: #1 $"

# pylint: disable=R0201
import unittest
from dm.Vp import Vp

# enable parallel execution of tests
_multiprocess_can_split_ = True

class Check(unittest.TestCase): #pylint: disable-msg=R0904
    """Data check for deliverable EXAMPLE1"""
    
    def SetUp(self):
        pass

    def TearDown(self):
        pass


    def test_Content(self):
        """Check 'file' file contents"""
        # Use the dm.DeliverableParser API to get file names from the templateset
        manifest = Vp.manifest
        # Get the files in deliverable EXAMPLE1 with id="file"
        fileNames = manifest.getDeliverablePattern('EXAMPLE1', 'file')
        for fileName in fileNames:
            f = open(fileName)
            contents = f.read().strip().lower()
            f.close()
            self.assertEqual(contents, 'supercalifragilisticexpialidocious',
                             msg='EXAMPLE1 file content mismatch')

    # Add as many tests as you like, all with names starting with 'test_'.
    # For example, this trivial test always passes. 
    def test_alwaysPass(self):
        """Test that always passes"""
        self.assertTrue(True, msg='EXAMPLE1 data check that always passes')
