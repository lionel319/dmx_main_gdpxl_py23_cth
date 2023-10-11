#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_cloneconfigsemptybranch.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
import unittest
from mock import patch
from datetime import date
import os, sys
import logging
import socket
import datetime
from pprint import pprint

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'lib', 'python')
sys.path.insert(0, LIB)

import dmx.utillib.loggingutils
LOGGER = dmx.utillib.loggingutils.setup_logger(level=logging.DEBUG)
import dmx.abnrlib.icm
import dmx.abnrlib.flows.cloneconfigsemptybranch

class TestFlowsCloneConfigsEmptyBranch(unittest.TestCase):

    def setUp(self):
        pass


    def test_001___cloneconfigsemptybranch___variant(self):
        p = 'Raton_Mesa'
        i = 'rtmliotest1'
        b = 'REL1.0RTMrevA0__22ww135a'
        db = '__xx__'
        l = None 
        cc = dmx.abnrlib.flows.cloneconfigsemptybranch.CloneConfigsEmptyBranch(p, i, b, db, libtype=l, preview=True)
        cc.run()
        ret = cc.newcf.report()
        print(ret)
        self.assertEqual(ret, 'Raton_Mesa/rtmliotest1/__xx__\n\tRaton_Mesa/rtmliotest1/ipspec/__xx__\n\tRaton_Mesa/rtmliotest1/reldoc/__xx__\n')



if __name__ == '__main__':
    unittest.main()
