#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/dmError_test.py#1 $

"""
Test the dmError class. Most of the tests are performed using doctest
via the doctest-unittest interface.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

#import re
import unittest
import doctest
import dmError


# Unused parameters; pylint: disable = W0613
def load_tests(loader, tests, ignore):
    '''Load the dmError.py doctest tests into unittest.'''
    tests.addTests(doctest.DocTestSuite(dmError))
    return tests

class TestdmError(unittest.TestCase):
    """Test the dmError class."""

    def setUp(self):
        pass
    
    def tearDown(self):
        pass


#    def test_empty(self):
#        pass

    def test_dmError(self):
        '''Check the dmError exception class.'''
        with self.assertRaises(dmError.dmError):
            raise dmError.dmError('text')
                
if __name__ == "__main__":
    unittest.main()
