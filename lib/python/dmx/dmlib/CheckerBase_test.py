#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/CheckerBase_test.py#1 $

"""
Test the CheckerBase class. Most of the tests are performed using doctest
via the doctest-unittest interface.
"""

import unittest
import doctest
import os, sys
import dmx.dmlib.CheckerBase


def load_tests(loader, tests, ignore): # pylint: disable = W0613
    '''Load the CheckerBase.py doctest tests into unittest.'''
    tests.addTests(doctest.DocTestSuite(dmx.dmlib.CheckerBase))
    return tests

class TestCheckerBase(unittest.TestCase):
    """Test the CheckerBase class."""

    def setUp(self):
        pass
    
    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()
