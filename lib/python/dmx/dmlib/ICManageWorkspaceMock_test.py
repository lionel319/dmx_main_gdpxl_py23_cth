#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/ICManageWorkspaceMock_test.py#1 $

"""
Test the ICManageWorkspaceMock class. Most of the tests are performed using
doctest via the doctest-unittest interface.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

import unittest
import doctest
import dmx.dmlib.ICManageWorkspaceMock


def load_tests(loader, tests, ignore): # pylint: disable=W0613
    '''Load the FileListExpander.py doctest tests into unittest.'''
    tests.addTests(doctest.DocTestSuite(dmx.dmlib.ICManageWorkspaceMock))
    return tests


if __name__ == "__main__":
    unittest.main()
