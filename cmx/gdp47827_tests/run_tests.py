#!/usr/intel/pkgs/python3/3.9.6/bin/python3
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/gdp47827_tests/run_tests.py#1 $
$Change: 7461618 $
$DateTime: 2023/01/29 19:30:48 $
$Author: lionelta $

Description: Wrapper script around running the abnr/quick test suites

Author: Lee Cartwright
Copyright (c) Altera Corporation 2016
All rights reserved.
'''
import UsrIntel.R1

import os
import sys
import nose

# Add this scripts directory the beginning of PYTHONPATH so we always
# get the right versions of the libraries
sys.path = [os.path.abspath(os.path.dirname(__file__))] + sys.path

if __name__ == '__main__':
    nose.main(argv=sys.argv)
