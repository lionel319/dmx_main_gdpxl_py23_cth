#!/usr/bin/env python
# Copyright 2012 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/deliverables_test/checkdata_bad/CheckVsPREDECESSOR_GOOD1.py#1 $


"""
Verification Platform check that always passes.
"""

__author__ = "John McGehee, (jmcgehee@altera.com)"
__version__ = "$Revision: #1 $"

# Which pylint checks should be disabled?
# pylint: disable=R0201
import unittest

# enable parallel execution of tests
_multiprocess_can_split_ = True

class Check(unittest.TestCase): #pylint: disable-msg=R0904
    """ Verification Platform check that always fails"""
    
    def test_alwaysPass(self):
        """Test that always passes"""
        self.assertTrue(True, 'CHECKDATA_BAD vs. PREDECESSOR_GOOD1 context check that always passes')
