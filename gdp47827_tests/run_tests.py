#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/run_tests.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Wrapper script around running the abnr/quick test suites

Author: Lee Cartwright
Copyright (c) Altera Corporation 2016
All rights reserved.
'''

import os
import sys
import nose

# Add this scripts directory the beginning of PYTHONPATH so we always
# get the right versions of the libraries
sys.path = [os.path.abspath(os.path.dirname(__file__))] + sys.path

if __name__ == '__main__':
    nose.main(argv=sys.argv)
