#!/usr/bin/env python
# 2015 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the functions in the multiproc.py library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_multiproc.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

import unittest
import itertools
import os, sys

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.utillib.multiproc import run_mp

def square(x):
    '''
    Basic helper function for testing the mp execution
    '''
    return x*x

def divide(x, y):
    '''
    Basic helper function for testing mp execution and raising exceptions
    '''
    return x/y

class TestMultiproc(unittest.TestCase):
    '''
    Tests the abnr multiproc library
    '''
    def test_run_mp_all_work(self):
        '''
        Tests the run_mp function when all jobs work
        '''
        inputs = [
            [1],
            [2],
            [3],
        ]

        results = run_mp(square, inputs)

        self.assertEqual(len(inputs), len(results))
        for input in itertools.chain.from_iterable(inputs):
            self.assertIn(square(input), results)

    def test_run_mp_exceptions(self):
        '''
        Tests the run_mp function when there's an exception
        '''
        inputs = [
            [2, 1],
            [4, 2],
            [6, 0],
        ]

        with self.assertRaises(ZeroDivisionError):
            run_mp(divide, inputs)


if __name__ == '__main__':
    unittest.main()
