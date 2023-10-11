#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/ICManageBase_test.py#1 $

"""
Test the dm.ICManageBase module. Most of the tests are performed using
doctest via the doctest-unittest interface.
"""

import unittest
import doctest

import dm.ICManageBase

def load_tests(loader, tests, ignore): # pylint: disable = W0613
    '''Load the doctest tests into unittest.'''
    tests.addTests (doctest.DocTestSuite (dm.ICManageBase))
    return tests

class TestICManageBase(unittest.TestCase):
    """Test the dm.ICManageBase.ICManageBase class."""
    
    def test_isUserLoggedIn(self):
        self.assertTrue (dm.ICManageBase.isUserLoggedIn())

if __name__ == "__main__":
    # import cProfile
    # cProfile.run("unittest.main()", '/home/jmcgehee/workspace/dm/profile.txt')
    unittest.main (verbosity=2, failfast=True)
