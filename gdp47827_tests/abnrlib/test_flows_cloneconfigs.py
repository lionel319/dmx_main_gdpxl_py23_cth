#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_cloneconfigs.py $
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
import dmx.abnrlib.flows.cloneconfigs

class TestFlowsCloneConfigs(unittest.TestCase):

    def setUp(self):
        pass


    def test_001___clone_libtype___dstbom_exist(self):
        p = 'Raton_Mesa'
        i = 'rtmliotest1'
        b = 'dev'
        db = 'liotest1'
        l = 'ipspec'
        cc = dmx.abnrlib.flows.cloneconfigs.CloneConfigs(p, i, b, db,
            libtype=l, clone_simple=False, clone_immutable=False, reuse=False, preview=True)
        with self.assertRaisesRegexp(Exception, 'it already exist'):
            cc.run()

    def test_002___clone_config___dstbom_exist(self):
        p = 'Raton_Mesa'
        i = 'rtmliotest1'
        b = 'dev'
        db = 'for_regtest_cloneconfig_1'
        l = None
        cc = dmx.abnrlib.flows.cloneconfigs.CloneConfigs(p, i, b, db,
            libtype=l, clone_simple=False, clone_immutable=False, reuse=False, preview=True)
        with self.assertRaisesRegexp(Exception, 'it already exist'):
            cc.run()
    
    def test_010___clone_config___no_option(self):
        '''
        Raton_Mesa/liotest1/snap-2
                Raton_Mesa/liotest1/ipspec/dev/snap-2
                Raton_Mesa/liotest1/rdf/dev/snap-2
                Raton_Mesa/liotest1/reldoc/dev/snap-2
                Raton_Mesa/liotest1/sta/dev/snap-2
                Raton_Mesa/liotest3/snap-2
                        Raton_Mesa/liotest3/ipspec/dev/snap-1
                        Raton_Mesa/liotest3/rdf/dev/snap-2
                        Raton_Mesa/liotest3/reldoc/dev/snap-2
                        Raton_Mesa/liotest3/sta/dev/snap-2
        '''
        p = 'Raton_Mesa'
        i = 'rtmliotest1'
        b = 'REL1.0RTMrevA0__22ww135a'
        db = '__xxxx__'
        l = None
        cc = dmx.abnrlib.flows.cloneconfigs.CloneConfigs(p, i, b, db,
            libtype=l, clone_simple=False, clone_immutable=False, reuse=False, preview=True)
        cc.run()
        ret = cc.clone.report()
        print(ret)
        ans = 'Raton_Mesa/rtmliotest1/__xxxx__\n\tRaton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d\n'
        self.assertEqual(ret, ans)

    def test_011___clone_config___clone_immutable(self):
        '''
        Raton_Mesa/liotest1/snap-2
                Raton_Mesa/liotest1/ipspec/dev/snap-2
                Raton_Mesa/liotest1/rdf/dev/snap-2
                Raton_Mesa/liotest1/reldoc/dev/snap-2
                Raton_Mesa/liotest1/sta/dev/snap-2
                Raton_Mesa/liotest3/snap-2
                        Raton_Mesa/liotest3/ipspec/dev/snap-1
                        Raton_Mesa/liotest3/rdf/dev/snap-2
                        Raton_Mesa/liotest3/reldoc/dev/snap-2
                        Raton_Mesa/liotest3/sta/dev/snap-2
        '''
        p = 'Raton_Mesa'
        i = 'rtmliotest1'
        b = 'REL1.0RTMrevA0__22ww135a'
        db = '__xxxx__'
        l = None
        cc = dmx.abnrlib.flows.cloneconfigs.CloneConfigs(p, i, b, db,
            libtype=l, clone_simple=False, clone_immutable=True, reuse=False, preview=True)
        cc.run()
        ret = cc.clone.report()
        print(ret)
        ans = 'Raton_Mesa/rtmliotest1/__xxxx__\n\tRaton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a\n\tRaton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d\n'
        self.assertEqual(ret, ans)




if __name__ == '__main__':
    unittest.main()
