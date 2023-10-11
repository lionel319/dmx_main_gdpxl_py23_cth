#!/usr/bin/env python
# Copyright 2012 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/deliverables_test/example2/CheckVsEXAMPLE1.py#1 $

"""
Verification Platform predecessor check example using Python unit test.

File dm/deliverables_test/example2/CheckVsEXAMPLE1.py, unit tested
in dm.Vp_test.test_example2CheckVsEXAMPLE1().

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
    """Check deliverable EXAMPLE2 vs. predecessor EXAMPLE1"""
    
    def SetUp(self):
        pass

    def TearDown(self):
        pass

    def test_content(self):
        """Compare 'txt' file contents, case sensitive."""
        
        # Use the dm.DeliverableParser API to get file names from the templateset
        manifest = Vp.manifest
        # Get the files in deliverables EXAMPLE1 and EXAMPLE2
        fileNames1 = manifest.getDeliverablePattern('EXAMPLE1', 'file')
        fileNames2 = manifest.getDeliverablePattern('EXAMPLE2', 'file')
        assert len(fileNames1) == len(fileNames2), 'Equal number of files expected'

        for fileName1, fileName2 in zip(fileNames1, fileNames2):

            f1 = open(fileName1)
            contents1 = f1.read().strip()
            f1.close()

            f2 = open(fileName2)
            contents2 = f2.read().strip()
            f2.close()
            
            self.assertEqual(contents1, contents2, msg='File content mismatch')

    # Add as many tests as you like, all with names starting with 'test_'.
    # For example, this trivial test always passes. 
    def test_alwaysPass(self):
        """Test that always passes"""
        self.assertTrue(True, msg='EXAMPLE1 vs. EXAMPLE2 context check that always passes')
