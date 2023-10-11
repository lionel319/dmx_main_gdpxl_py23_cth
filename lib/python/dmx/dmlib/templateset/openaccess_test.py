#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/openaccess_test.py#1 $

"""
Test the OpenAccess class. Most of the tests are performed using doctest
via the doctest-unittest interface.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

import unittest
import doctest
import dmx.dmlib.templateset.openaccess
from dmx.dmlib.dmError import dmError

def load_tests(loader, tests, ignore): # pylint: disable=W0613
    '''Load the OpenAccess.py doctest tests into unittest.'''
    tests.addTests(doctest.DocTestSuite(dmx.dmlib.templateset.openaccess))
    return tests

class TestOpenAccess(unittest.TestCase): # pylint: disable=R0904
    """Test the OpenAccess class."""

    def setUp(self):
        pass
    
    def tearDown(self):
        pass


#    def test_empty(self):
#        pass

    def test_badViewType(self):
        '''Check that an exception is thrown if viewType is bad.'''
        with self.assertRaises(dmError):
            dmx.dmlib.templateset.openaccess.OpenAccess('path/to/libName',
                                                 'libName', 'cellName', 'viewName',
                                                 'oacBadViewType')
                
        
if __name__ == "__main__":
    unittest.main()
