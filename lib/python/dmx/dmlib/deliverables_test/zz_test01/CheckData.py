#!/usr/bin/env python
# Copyright 2012 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/deliverables_test/zz_test01/CheckData.py#1 $

"""
Verification Platform fake data check used in testing IC Manage check lists.

This checker has nothing to do with the real BDS.  The name "BDS" is used
merely to avoid creating check list property names for imaginary deliverables.
The property names are global and will therefore be seen by the user.
"""

__author__ = "John McGehee, (jmcgehee@altera.com)"
__version__ = "$Revision: #1 $"

# pylint: disable=R0201
import unittest
from dm.Vp import Vp

# enable parallel execution of tests
_multiprocess_can_split_ = True

class Check(unittest.TestCase): #pylint: disable-msg=R0904
    """Data check for fake BDS"""
    
    def test_Content(self):
        """Check for 'file' file contents equal to 'pass'"""

        # Use the dm.DeliverableParser API to get file names from the manifestset
        manifest = Vp.manifest
        # Get the files in deliverable EXAMPLE1 with id="file"
        fileNames = manifest.getDeliverablePattern('ZZ_TEST01', 'file')
        for fileName in fileNames:
            f = open(fileName)
            contents = f.read().strip().lower()
            f.close()
            self.assertEqual(contents, 'pass')
