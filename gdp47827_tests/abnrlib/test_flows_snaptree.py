#!/usr/bin/env python
# 2014 Altera Corporation. All rights reserved. This source code is highly
# confidential and proprietary information of Altera and is to be used for
# internal Altera purposes only.   Altera assumes no responsibility or
# liability arising out of the application or use of this source code for
# non-Altera purposes.
#
# Tests the abnr utils library
#
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/gdp47827_tests/abnrlib/test_flows_snaptree.py $
# $Revision: #1 $
# $Change: 7411538 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $

from __future__ import print_function
from builtins import str
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
import dmx.abnrlib.flows.snaptree
import dmx.abnrlib.config_factory

class TestSnapLibrary(unittest.TestCase):

    def setUp(self):
        self.cli = dmx.abnrlib.icm.ICManageCLI(site='intel')

        if sys.version_info[0] > 2:
            self.assertItemsEqual = self.assertCountEqual
   

    def test_001___snap_exists___libtype_no(self):
        p = 'Raton_Mesa'
        v = 'rtmliotest1'
        l = 'ipspec'
        c = 'dev'
        s = dmx.abnrlib.flows.snaptree.SnapTree(p, v, c, 'snap-xxx', preview=True) 
        ret = s.snap_exists(p, v, l)
        print("ret:{}".format(ret))
        self.assertEqual(ret, '')

    def test_002___snap_exists___libtype_yes(self):
        p = 'Raton_Mesa'
        v = 'rtmliotest1'
        l = 'ipspec'
        c = 'dev'
        s = dmx.abnrlib.flows.snaptree.SnapTree(p, v, c, 'snap-fortnr_1', preview=True) 
        ret = s.snap_exists(p, v, l)
        print("ret:{}".format(ret))
        self.assertEqual(ret, 'dev')

    def test_003___snap_exists___variant_no(self):
        p = 'Raton_Mesa'
        v = 'rtmliotest1'
        l = 'ipspec'
        c = 'dev'
        s = dmx.abnrlib.flows.snaptree.SnapTree(p, v, c, 'snap-xxx', preview=True) 
        ret = s.snap_exists(p, v)
        print(ret)
        self.assertEqual(ret, [])

    def test_004___snap_exists___variant_yes(self):
        p = 'Raton_Mesa'
        v = 'rtmliotest1'
        l = 'ipspec'
        c = 'dev'
        s = dmx.abnrlib.flows.snaptree.SnapTree(p, v, c, 'snap-xxx', preview=True) 
        s.snapshot = 'snap-1'
        ret = s.snap_exists(p, v)
        print(ret)
        ans = [{u'path': u'/intel/Raton_Mesa/rtmliotest1/snap-1'}]
        self.assertEqual(ret, ans)

    def test_010___filter_tree___variant_1(self):
        '''
        >dmx report content -p Raton_Mesa -i rtmliotest2 -b snap-1 --hier
        INFO: DMX-id: dmx_lionelta_20220328_scc919025_16597_sc
        Project: Raton_Mesa, IP: rtmliotest2, BOM: snap-1
                Last modified: 2022/03/25 09:13:41 (in server timezone)
        Raton_Mesa/rtmliotest2/snap-1
                Raton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c
                Raton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a
                Raton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a
                        Raton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a
                        Raton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d
        '''        
        p = 'Raton_Mesa'
        v = 'rtmliotest2'
        c = 'snap-1'
        variants = ['rtmliotest1']
        s = dmx.abnrlib.flows.snaptree.SnapTree(p, v, 'dev', 'snap-xxx', preview=True, variants=variants) 
        cfobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(p, v, c)
        fcfobj = s.filter_tree(cfobj)
        treenames = [str(x) for x in fcfobj.flatten_tree()]
        from pprint import pprint
        print(fcfobj.report(show_simple=True))
        pprint(treenames)
        ans = ['Raton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a',
 'Raton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a',
 'Raton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d',
 'Raton_Mesa/rtmliotest2/snap-1']
        self.assertItemsEqual(treenames, ans)

    def test_010___filter_tree___variant_2(self):
        '''
        >dmx report content -p Raton_Mesa -i rtmliotest2 -b snap-1 --hier
        INFO: DMX-id: dmx_lionelta_20220328_scc919025_16597_sc
        Project: Raton_Mesa, IP: rtmliotest2, BOM: snap-1
                Last modified: 2022/03/25 09:13:41 (in server timezone)
        Raton_Mesa/rtmliotest2/snap-1
                Raton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c
                Raton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a
                Raton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a
                        Raton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a
                        Raton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d
        '''        
        p = 'Raton_Mesa'
        v = 'rtmliotest2'
        c = 'snap-1'
        variants = ['rtmliotest2']
        s = dmx.abnrlib.flows.snaptree.SnapTree(p, v, 'dev', 'snap-xxx', preview=True, variants=variants) 
        cfobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(p, v, c)
        fcfobj = s.filter_tree(cfobj)
        treenames = [str(x) for x in fcfobj.flatten_tree()]
        from pprint import pprint
        print(fcfobj.report(show_simple=True))
        pprint(treenames)
        ans = ['Raton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a',
 'Raton_Mesa/rtmliotest2/snap-1',
 'Raton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c']
        self.assertItemsEqual(treenames, ans)

    def test_010___filter_tree___variant_3(self):
        '''
        >dmx report content -p Raton_Mesa -i rtmliotest2 -b snap-1 --hier
        INFO: DMX-id: dmx_lionelta_20220328_scc919025_16597_sc
        Project: Raton_Mesa, IP: rtmliotest2, BOM: snap-1
                Last modified: 2022/03/25 09:13:41 (in server timezone)
        Raton_Mesa/rtmliotest2/snap-1
                Raton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c
                Raton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a
                Raton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a
                        Raton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a
                        Raton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d
        '''        
        p = 'Raton_Mesa'
        v = 'rtmliotest2'
        c = 'snap-1'
        variants = ['rtmliotest1', 'rtmliotest2']
        s = dmx.abnrlib.flows.snaptree.SnapTree(p, v, 'dev', 'snap-xxx', preview=True, variants=variants) 
        cfobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(p, v, c)
        fcfobj = s.filter_tree(cfobj)
        treenames = [str(x) for x in fcfobj.flatten_tree()]
        from pprint import pprint
        print(fcfobj.report(show_simple=True))
        pprint(treenames)
        ans = ['Raton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a',
 'Raton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a',
 'Raton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a',
 'Raton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c',
 'Raton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d',
 'Raton_Mesa/rtmliotest2/snap-1']
        self.assertItemsEqual(treenames, ans)


    def test_011___filter_tree___libtype_ipspec(self):
        '''
        >dmx report content -p Raton_Mesa -i rtmliotest2 -b snap-1 --hier
        INFO: DMX-id: dmx_lionelta_20220328_scc919025_16597_sc
        Project: Raton_Mesa, IP: rtmliotest2, BOM: snap-1
                Last modified: 2022/03/25 09:13:41 (in server timezone)
        Raton_Mesa/rtmliotest2/snap-1
                Raton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c
                Raton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a
                Raton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a
                        Raton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a
                        Raton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d
        '''        
        p = 'Raton_Mesa'
        v = 'rtmliotest2'
        c = 'for_regtest_1'
        libtypes = ['ipspec']
        s = dmx.abnrlib.flows.snaptree.SnapTree(p, v, c, 'snap-xxx', preview=True, libtypes=libtypes) 
        # need to use 'dev' because otherwise it will not filter out libtypes from immutable configs
        cfobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(p, v, c)   
        fcfobj = s.filter_tree(cfobj)
        treenames = [str(x) for x in fcfobj.flatten_tree()]
        from pprint import pprint
        print(fcfobj.report(show_simple=True))
        pprint(s.libtypes)
        pprint(treenames)
        ans = ['Raton_Mesa/rtmliotest2/ipspec/dev',
 'Raton_Mesa/rtmliotest1/for_regtest_1',
 'Raton_Mesa/rtmliotest1/ipspec/dev',
 'Raton_Mesa/rtmliotest2/for_regtest_1']
        self.assertItemsEqual(treenames, ans)

    def test_012___filter_tree___view(self):
        '''
        >dmx report content -p Raton_Mesa -i rtmliotest2 -b snap-1 --hier
        INFO: DMX-id: dmx_lionelta_20220328_scc919025_16597_sc
        Project: Raton_Mesa, IP: rtmliotest2, BOM: snap-1
                Last modified: 2022/03/25 09:13:41 (in server timezone)
        Raton_Mesa/rtmliotest2/snap-1
                Raton_Mesa/rtmliotest2/ipspec/dev/REL1.0RTMrevA0__22ww135c
                Raton_Mesa/rtmliotest2/reldoc/dev/REL1.0RTMrevA0__22ww135a
                Raton_Mesa/rtmliotest1/REL1.0RTMrevA0__22ww135a
                        Raton_Mesa/rtmliotest1/ipspec/dev/REL1.0RTMrevA0__22ww135a
                        Raton_Mesa/rtmliotest1/reldoc/dev/REL1.0RTMrevA0__22ww135d
        '''
        #os.environ['DB_FAMILY'] = "Ratonmesa"
        p = 'Raton_Mesa'
        v = 'rtmliotest2'
        c = 'for_regtest_1'
        libtypes = ['view_testchip']    # ipspec, oa, reldoc

        import dmx.utillib.contextmgr
        with dmx.utillib.contextmgr.setenv({"DB_FAMILY": "Ratonmesa"}):
            s = dmx.abnrlib.flows.snaptree.SnapTree(p, v, c, 'snap-xxx', preview=True, libtypes=libtypes) 
            # need to use 'dev' because otherwise it will not filter out libtypes from immutable configs
            cfobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(p, v, c)   
            fcfobj = s.filter_tree(cfobj)
            print("____________________________")
            print(os.getenv("DB_FAMILY"))
            print("____________________________")

        print("____________________________")
        print(os.getenv("DB_FAMILY"))
        print("____________________________")
        treenames = [str(x) for x in fcfobj.flatten_tree()]
        from pprint import pprint
        print(fcfobj.report(show_simple=True))
        pprint(s.libtypes)
        self.assertItemsEqual(s.libtypes, ['oa', 'ipspec', 'reldoc'])
        pprint(treenames)
        ans = ['Raton_Mesa/rtmliotest1/reldoc/dev',
 'Raton_Mesa/rtmliotest2/ipspec/dev',
 'Raton_Mesa/rtmliotest2/for_regtest_1',
 'Raton_Mesa/rtmliotest1/for_regtest_1',
 'Raton_Mesa/rtmliotest2/reldoc/dev',
 'Raton_Mesa/rtmliotest2/oa/dev',
 'Raton_Mesa/rtmliotest1/ipspec/dev']
 
        self.assertItemsEqual(treenames, ans)

if __name__ == '__main__':
    unittest.main()
