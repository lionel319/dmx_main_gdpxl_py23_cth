#!/usr/bin/env python

import sys
import os
import logging
import unittest

rootdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'python')
sys.path.insert(0, rootdir)

import dmx.abnrlib.goldenarc_db


class TestGoldenarcDb(unittest.TestCase):
   
    @classmethod
    def setUpClass(cls):
        cls.a = dmx.abnrlib.goldenarc_db.GoldenarcDb(prod=False)
        cls.a.connect()
        cls.a.col = cls.a.db.db['RegtestGoldenArc']     ### Hack to use regtest collection instead of official one.

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_000___make_sure_correct_module_is_loaded(self):
        self.assertIn(rootdir, dmx.abnrlib.goldenarc_db.__file__)


    def test_010___verify_arc_resource___True(self):
        self.assertTrue(self.a.verify_arc_resource('dmx/9.0'))

    def _test_011___verify_arc_resource___False(self):
        with self.assertRaises(Exception):
            self.a.verify_arc_resource('dmx/123.456')

    def test_100___get_tools_by_checker___True(self):
        ret = self.a.get_tools_by_checker("FM8revA0", "4.0", "lint", "mustfix")
        self.assertEqual(ret, [[u'python', u'/2.7.1'], [u'atrenta_sgmaster', u'/2020WW04']])

    def test_101___get_tools_by_checker___False(self):
        ret = self.a.get_tools_by_checker('FM8revA0', '4.0', 'xxx', '')
        self.assertEqual(ret, [])


    def test_120___is_goldenarc_exist___True(self):
        ret = self.a.is_goldenarc_exist('FM8revA0', '4.0', 'lint', 'mustfix', 'python', '/2.7.1')
        self.assertTrue(ret)

    def test_121___is_goldenarc_exist___False(self):
        ret = self.a.is_goldenarc_exist('FM8revA0', '4.0', 'lint', 'mustfix', 'xxx', '/2.7.1')
        self.assertFalse(ret)

    def test_130___get_goldenarc_list___True(self):
        ret = self.a.get_goldenarc_list(thread="FM8revA0", milestone="3.0")
        ### Remove all the _id keys so that we can do a dict compare efficiently
        for r in ret:
            r.pop("_id")
        self.assertEqual(ret, [{u'flow': u'rdf',                                                                                                        
  u'milestone': u'3.0',                                                                                                   
  u'subflow': u'',                                                                                                        
  u'thread': u'FM8revA0',
  u'tool': u'my_cshrc',
  u'version': u'/1.0'},
 {u'flow': u'reldoc',
  u'milestone': u'3.0',
  u'subflow': u'',
  u'thread': u'FM8revA0',
  u'tool': u'dmx',
  u'version': u'/main'},
 {u'flow': u'sta',
  u'milestone': u'3.0',
  u'subflow': u'',
  u'thread': u'FM8revA0',
  u'tool': u'my_cshrc',
  u'version': u'/1.0'}]
)


if __name__ == "__main__":
    if '-v' in sys.argv:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG) 
    else:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.ERROR) 
    unittest.main()
