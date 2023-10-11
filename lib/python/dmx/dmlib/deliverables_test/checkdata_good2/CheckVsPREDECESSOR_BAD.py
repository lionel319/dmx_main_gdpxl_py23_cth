#!/usr/bin/env python
# Copyright 2012 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/deliverables_test/checkdata_good2/CheckVsPREDECESSOR_BAD.py#1 $

"""
Verification Platform check that always fails.
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
    
    def test_alwaysFail(self):
        """Test that always fails"""
        self.assertTrue(False, 'CHECKDATA_GOOD2 vs. PREDECESSOR_BAD context check that always fails')
