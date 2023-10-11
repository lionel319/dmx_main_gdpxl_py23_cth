#!/usr/bin/env python
# Copyright 2012 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/deliverables_test/zz_test02/CheckVsZZ_TEST01.py#1 $

"""
Verification Platform predecessor check example using Python unit test.

This checker has nothing to do with the real BDS or RTL.  The names "BDS" and
"RTL" are used merely to avoid creating check list property names for imaginary
deliverables.  The property names are global and will therefore be seen by the
user.
"""

__author__ = "John McGehee, (jmcgehee@altera.com)"
__version__ = "$Revision: #1 $"

# pylint: disable=R0201
import unittest
from dm.Vp import Vp

# enable parallel execution of tests
_multiprocess_can_split_ = True

class Check(unittest.TestCase): #pylint: disable-msg=R0904
    """Check deliverable ZZ_TEST01 vs. predecessor ZZ_TEST02"""
    
    def test_content(self):
        """Compare 'txt' file contents, case sensitive."""
        
        # Use the dm.DeliverableParser API to get file names from the manifestset
        manifest = Vp.manifest
        # Get the files in deliverables BDS and RTL
        fileNames1 = manifest.getDeliverablePattern('ZZ_TEST01', 'file')
        fileNames2 = manifest.getDeliverablePattern('ZZ_TEST02', 'file')
        assert len(fileNames1) == len(fileNames2), 'Equal number of files expected'

        for fileName1, fileName2 in zip(fileNames1, fileNames2):

            f1 = open(fileName1)
            contents1 = f1.read().strip()
            f1.close()

            f2 = open(fileName2)
            contents2 = f2.read().strip()
            f2.close()
            
            self.assertEqual(contents1, contents2, msg='File content mismatch')
