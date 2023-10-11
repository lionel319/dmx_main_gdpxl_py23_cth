#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/successor_test.py#1 $

"""
Test the Successor class. Most of the tests are performed using doctest
via the doctest-unittest interface.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

import unittest
import doctest
import dmx.dmlib.templateset.successor
from dmx.dmlib.templateset.verifier import Verifier



def load_tests(loader, tests, ignore): # pylint: disable=W0613
    '''Load the Successor doctest tests into unittest.'''
    tests.addTests(doctest.DocTestSuite(dmx.dmlib.templateset.successor))
    return tests

class TestSuccessor(unittest.TestCase): # pylint: disable=R0904
    """Test the Successor class."""

    def setUp(self):
        pass
    
    def tearDown(self):
        pass


#    def test_empty(self):
#        passSuccessor

      
    def test_allPresent(self):
        '''Check that all deliverables are present.
        The error,
            self.assertEqual(actual, expected)
            AssertionError: 'GLNPOSTPNR' != 'FUNCRBA'
        means one of two things:
            - GLNPOSTPNR is defined when it should not be
            - FUNCRBA is not defined when it should be
        '''
        actual = dmx.dmlib.templateset.successor.Successor.getNames()
        self.assertItemsEqual(actual,
                              Verifier.allDeliverableNames)
          
#    def test_Verifier(self):
#        '''Verify the successsor relationships with Verifier.
#        '''
#        deliverableSet = Templateset('Full', '2.0')
#        verifier = Verifier(deliverableSet.toxml(), doVerifyEveryTemplatePresent=True)
#        self.assertEqual(verifier.errors, [])
                  
        
if __name__ == "__main__":
    unittest.main()
