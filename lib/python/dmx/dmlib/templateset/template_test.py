#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/templateset/template_test.py#1 $

"""
Test the Template class. Most of the tests are performed using doctest
via the doctest-unittest interface.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

import unittest
#import doctest
import dmx.dmlib.pyfakefs.fake_filesystem_unittest

import dmx.dmlib.templateset.template
from dmx.dmlib.templateset.verifier import Verifier


def load_tests(loader, tests, ignore): # pylint: disable=W0613
    '''Load the Template.py doctest tests into unittest.'''
    return dmx.dmlib.pyfakefs.fake_filesystem_unittest.load_doctests(loader, tests, ignore,
                                                           dmx.dmlib.templateset.template)

class TestTemplate(dmx.dmlib.pyfakefs.fake_filesystem_unittest.TestCase): # pylint: disable=R0904
    """Test the Template class."""

    def test_allPresent(self):
        '''Check that all deliverables are present.
        The error,
            self.assertEqual(actual, expected)
            AssertionError: 'TESTPINS' != 'TIMING'
        means one of two things:
            - TESTPINS is defined when it should not be
            - TIMING is not defined when it should be
        '''
        actual = dmx.dmlib.templateset.template.Template.getNames()
        self.assertItemsEqual(actual,
                              Verifier.allDeliverableNames)
                
        
if __name__ == "__main__":
    unittest.main()
