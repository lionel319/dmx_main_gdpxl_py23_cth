#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/Graph_test.py#1 $

"""
Test the Graph class. More tests are performed using doctest
via the doctest-unittest interface.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

import unittest
import doctest

from Manifest import Manifest
from dmx.dmlib.dmError import dmError
import Graph

def load_tests(loader, tests, ignore): # pylint: disable = W0613
    '''Load the Graph.py doctest tests into unittest.'''
    tests.addTests(doctest.DocTestSuite(Graph))
    return tests


class TestGraph(unittest.TestCase):
    """Test the Graph class."""

    def setUp(self):
        manifestSetXml = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template id="UNCONNECTED"/>

          <template id="SHALLOW">
            <pattern id="shallow">
              shallow.txt
            </pattern>
          </template>

          <template id="RANK1A">
            <pattern id="rank1aId">
              &ip_name;/rank1/rank1a.txt
            </pattern>
          </template>
          <template id="RANK1B">
            <pattern id="rank1bId">
              &ip_name;/rank1/rank1b.txt
            </pattern>
          </template>
          <template id="RANK1C">
            <openaccess id="rank1cId">
              <libpath>
                &ip_name;/rank1/&ip_name;
              </libpath>
              <lib>
                &ip_name;
              </lib>
            </openaccess>
          </template>

          <template id="RANK2A">
            <filelist id="rank2aId">
              &ip_name;/rank2/&ip_name;.filelist
            </filelist>
          </template>
          
          <template id="RANK3A">
            <pattern id="rank3aId">
              &ip_name;/rank3/rank3a.txt
            </pattern>
          </template>
          <template id="RANK3B">
            <milkyway id="rank3bId">
              <libpath>
                &ip_name;/rank3/&ip_name;
              </libpath>
            </milkyway>
          </template>
          
          <successor id="RANK2A">
            <predecessor>RANK1A</predecessor>
            <predecessor>RANK1B</predecessor>
            <predecessor>RANK1C</predecessor>
          </successor>
                    
          <successor id="RANK3A">
            <predecessor>RANK2A</predecessor>
          </successor>
          <successor id="RANK3B">
            <predecessor>RANK2A</predecessor>
          </successor>

        </templateset>'''
        self._manifest = Manifest('ip1', templatesetString=manifestSetXml)
        self._graph = Graph.Graph(self._manifest)
        
    def tearDown(self):
        pass


    ##### Test the predecessor graph #####
    
    def test_emptyPredecessorGraph(self):
        '''Check a predecessor graph with no nodes.'''
        self._graph.createPredecessorGraph(set())
        self._graph.render('png', 'test_emptyPredecessorGraph.png')
        dotList = self._graph.dotList
        self.assertEqual(len(dotList), 7)
        
    def test_NonexistentPredecessorNodeError(self):
        '''Check a predecessor graph with a nonexistent node.'''
        with self.assertRaises(dmError):
            self._graph.createPredecessorGraph(set(['RANK1A', 'NONEXISTENT']))
        
    def test_unconnectedPredecessorGraph(self):
        '''Check a predecessor graph with a single unconnected node.'''
        self._graph.createPredecessorGraph(set(['UNCONNECTED']))
        self._graph.render('png', 'test_unconnectedPredecessorGraph.png')
        dotList = self._graph.dotList
        self.assertEqual(len(dotList), 8)
        self.assertTrue('    UNCONNECTED;' in dotList)

    def test_dotError(self):
        '''Check the reaction to an error from dot.'''
        self._graph._dotList = ['PurposelyErroneousDotStatement']
        with self.assertRaises(dmError):
            self._graph.render('png', 'test_dotError.png')
        
    def test_connectedPredecessorGraph(self):
        '''Check a predecessor graph with multiple connected nodes.'''
        self._graph.createPredecessorGraph(set(['RANK1A', 'RANK1B', 'RANK1C',
                                                   'RANK2A', 'RANK3A', 'RANK3B']))
        self._graph.render('png', 'test_connectedPredecessorGraph.png')
        dotList = self._graph.dotList
        self.assertEqual(len(dotList), 18)
        self.assertTrue('    RANK3A;' in dotList)
        self.assertTrue('    RANK2A -> RANK3A;' in dotList)
        self.assertTrue('    RANK2A;' in dotList)
        self.assertTrue('    RANK1C -> RANK2A;' in dotList)
        self.assertTrue('    RANK1B -> RANK2A;' in dotList)
        self.assertTrue('    RANK1A -> RANK2A;' in dotList)
        self.assertTrue('    RANK3B;' in dotList)
        self.assertTrue('    RANK2A -> RANK3B;' in dotList)
        self.assertTrue('    RANK1C;' in dotList)
        self.assertTrue('    RANK1B;' in dotList)
        self.assertTrue('    RANK1A;' in dotList)

    
    ##### Test the file hierarchy graph #####
    
    def test_emptyFileHierGraph(self):
        '''Check a file hierarchy graph with no nodes.'''
        self._graph.createFileHierGraph(set())
        self._graph.render('png', 'test_emptyFileHierGraph.png')
        dotList = self._graph.dotList
        self.assertEqual(len(dotList), 7)
        
    def test_NonexistentFileHierNodeError(self):
        '''Check a file hierarchy graph with a nonexistent node.'''
        with self.assertRaises(dmError):
            self._graph.createFileHierGraph(set(['RANK1A', 'NONEXISTENT']))
        
    def test_unconnectedFileHierGraph(self):
        '''Check a file hierarchy graph with a deliverable that contains no files.'''
        self._graph.createFileHierGraph(set(['UNCONNECTED']))
        self._graph.render('png', 'test_unconnectedFileHierGraph.png')
        dotList = self._graph.dotList
        self.assertEqual(len(dotList), 7)
        self.assertFalse('    UNCONNECTED;' in dotList)

    def test_connectedFileHierGraph(self):
        '''Check a file hierarchy graph with multiple connected nodes.'''
        self._graph.createFileHierGraph(set(['RANK1A', 'RANK1B', 'RANK1C',
                                                   'RANK2A', 'RANK3A', 'RANK3B']))
        self._graph.render('png', 'test_connectedFileHierGraph.png')
        dotList = self._graph.dotList
        self.assertEqual(len(dotList), 43)
        self.assertTrue(r'    "ip1"[label="ip1"];' in dotList)
        self.assertTrue(r'    "ip1/rank3"[label="rank3"];' in dotList)
        self.assertTrue(r'    "ip1" -> "ip1/rank3";' in dotList)
        self.assertTrue(r'    "ip1/rank3/rank3a.txt"[label="rank3a.txt"];' in dotList)
        self.assertTrue(r'    "ip1/rank3" -> "ip1/rank3/rank3a.txt";' in dotList)
        self.assertTrue(r'    "ip1/rank3/rank3a.txt"[label="rank3a.txt\nRANK3A" shape=box, fontname=Courier, style=filled, fillcolor=white];' in dotList)
        self.assertTrue(r'    "ip1"[label="ip1"];' in dotList)
        self.assertTrue(r'    "ip1/rank2"[label="rank2"];' in dotList)
        self.assertTrue(r'    "ip1" -> "ip1/rank2";' in dotList)
        self.assertTrue(r'    "ip1/rank2/ip1.filelist"[label="ip1.filelist"];' in dotList)
        self.assertTrue(r'    "ip1/rank2" -> "ip1/rank2/ip1.filelist";' in dotList)
        self.assertTrue(r'    "ip1/rank2/ip1.filelist"[label="ip1.filelist\nRANK2A" shape=box, fontname=Courier, style=filled, fillcolor=grey];' in dotList)
        self.assertTrue(r'    "ip1"[label="ip1"];' in dotList)
        self.assertTrue(r'    "ip1/rank3"[label="rank3"];' in dotList)
        self.assertTrue(r'    "ip1" -> "ip1/rank3";' in dotList)
        self.assertTrue(r'    "ip1/rank3/ip1"[label="ip1"];' in dotList)
        self.assertTrue(r'    "ip1/rank3" -> "ip1/rank3/ip1";' in dotList)
        self.assertTrue(r'    "ip1/rank3/ip1"[label="ip1\nRANK3B" shape=folder, fontname=Courier, style=filled, fillcolor=orchid];' in dotList)
        self.assertTrue(r'    "ip1"[label="ip1"];' in dotList)
        self.assertTrue(r'    "ip1/rank1"[label="rank1"];' in dotList)
        self.assertTrue(r'    "ip1" -> "ip1/rank1";' in dotList)
        self.assertTrue(r'    "ip1/rank1/ip1"[label="ip1"];' in dotList)
        self.assertTrue(r'    "ip1/rank1" -> "ip1/rank1/ip1";' in dotList)
        self.assertTrue(r'    "ip1/rank1/ip1"[label="ip1\nRANK1C" shape=folder, fontname=Courier, style=filled, fillcolor=red];' in dotList)
        self.assertTrue(r'    "ip1"[label="ip1"];' in dotList)
        self.assertTrue(r'    "ip1/rank1"[label="rank1"];' in dotList)
        self.assertTrue(r'    "ip1" -> "ip1/rank1";' in dotList)
        self.assertTrue(r'    "ip1/rank1/rank1b.txt"[label="rank1b.txt"];' in dotList)
        self.assertTrue(r'    "ip1/rank1" -> "ip1/rank1/rank1b.txt";' in dotList)
        self.assertTrue(r'    "ip1/rank1/rank1b.txt"[label="rank1b.txt\nRANK1B" shape=box, fontname=Courier, style=filled, fillcolor=white];' in dotList)
        self.assertTrue(r'    "ip1"[label="ip1"];' in dotList)
        self.assertTrue(r'    "ip1/rank1"[label="rank1"];' in dotList)
        self.assertTrue(r'    "ip1" -> "ip1/rank1";' in dotList)
        self.assertTrue(r'    "ip1/rank1/rank1a.txt"[label="rank1a.txt"];' in dotList)
        self.assertTrue(r'    "ip1/rank1" -> "ip1/rank1/rank1a.txt";' in dotList)
        self.assertTrue(r'    "ip1/rank1/rank1a.txt"[label="rank1a.txt\nRANK1A" shape=box, fontname=Courier, style=filled, fillcolor=white];' in dotList)

    def test_shallowFileHierGraph(self):
        '''Check a file hierarchy graph with a file not in a directory.'''
        self._graph.createFileHierGraph(set(['SHALLOW']))
        self._graph.render('png', 'test_shallowFileHierGraph.png')
        dotList = self._graph.dotList
        self.assertEqual(len(dotList), 9)
        self.assertTrue(r'    "shallow.txt"[label="shallow.txt\nSHALLOW" shape=box, fontname=Courier, style=filled, fillcolor=white];' in dotList)
    


if __name__ == "__main__":
    unittest.main()
