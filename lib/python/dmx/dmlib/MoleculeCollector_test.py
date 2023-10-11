#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/MoleculeCollector_test.py#1 $

"""
Test the CollectMolecules class. More tests are performed using doctest
via the doctest-unittest interface.
"""

__author__ = "Priya Rajachidambaram (srajachi@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2013 Altera Corporation"

#import os

# Imports for testing with pyfakefs 
import unittest
import pyfakefs.fake_filesystem_unittest

from dmx.dmlib.MoleculeCollector import MoleculeCollector
from dmx.dmlib.ICManageWorkspaceMock import ICManageWorkspaceMock
from dmx.dmlib.dmError import dmError

#pylint: disable = W0511

class TestCollectMolecules(pyfakefs.fake_filesystem_unittest.TestCase): 
    '''Test the CollectMolecules class.'''

    def test_molecules(self):

        '''Test molecule parsing from molecules.txt. Both <cellname> and <libnam> <cellname> formats are tested'''
        ws = ICManageWorkspaceMock('ip1',
                                   cellNamesDict={'ip1' : set(['cella', 'cellb']),
                                                  'ip2' : set(['cellc', 'celld']),
                                                  'ip3' : set(['ip3'])},
                                   moleculesDict={'cella' : set(['cella1', 'cella2']),
                                                  'cellb' : set(['cellb1', 'ip2 cellc']),
                                                  'cellc' : set(['cellc1', 'ip3 ip3']),
                                                  'celld' : set([]),
                                                  'ip3'   : set(['ip31'])},
                                   elementsDict={'cella' : set([]),
                                                 'cellb' : set([]),
                                                 'cellc' : set([]),
                                                 'celld' : set([]),
                                                 'ip3'   : set([])})
        mc = MoleculeCollector(ws)
        molecules = mc.collectMolecules('lvs')
        self.assertItemsEqual(molecules, set(['cella1', 'cella2', 'cellb1', 'cellc1', 'ip31']))
        
 
             
    def test_molecules_elements(self):

        '''Test molecule parsing when both molecule and elements information exists for the same cell'''
        ws = ICManageWorkspaceMock('ip1',
                                   cellNamesDict={'ip1' : set(['cella', 'cellb']),
                                                  'ip2' : set(['cellc', 'celld']),
                                                  'ip3' : set(['ip3'])},
                                   moleculesDict={'cella' : set(['cella']),
                                                  'cellb' : set(['cellb1', 'ip2 cellc']),
                                                  'cellc' : set(['cellc1', 'ip3 ip3']),
                                                  'celld' : set(['celld1']),
                                                  'ip3'   : set(['ip31'])},
                                   elementsDict={'cella' : set(['cellaa', 'cellab', 'ip2 celld']),
                                                 'cellb' : set([]),
                                                 'cellc' : set([]),
                                                 'celld' : set([]),
                                                 'ip3'   : set([])})
        
        mc = MoleculeCollector(ws)
        molecules = mc.collectMolecules('lvs')
        self.assertItemsEqual(molecules, set(['cella', 'cellaa', 'cellab', 'cellb1', 'cellc1', 'celld1', 'ip31']))      
        
    def test_no_molecules_elements(self):
        
        '''Test error output from molecule parsing when both molecules.txt and elements.txt are missing for an IP'''
        with self.assertRaises(dmError) as excp:
        
            ws = ICManageWorkspaceMock('ip2',
                                       cellNamesDict={'ip1' : set(['cella', 'cellb']),
                                                      'ip2' : set(['cellc', 'celld']),
                                                      'ip3' : set(['ip3'])},
                                       moleculesDict={'cella' : set(['cella']),
                                                      'cellb' : set(['cellb1', 'ip2 cellc']),
                                                      'cellc' : set(['cellc1', 'ip3 ip3']),
                                                      'celld' : set([]),
                                                      'ip3'   : set(['ip31'])},
                                       elementsDict={'cella' : set(['cellaa', 'cellab']),
                                                     'cellb' : set([]),
                                                     'cellc' : set([]),
                                                     'celld' : set([]),
                                                     'ip3'   : set([])})   
            mc = MoleculeCollector(ws)
            molecules = mc.collectMolecules('lvs') 
            _ = molecules  
        self.assertRegexpMatches(excp.exception.message, r"Either molecule list or element list must be present for 'celld'.")

        
    def test_format_molecules_elements(self):
        #pylint: disable = W0511
        '''Test error output when the entry in molecules.txt is not in <cellname> or <libname> <cellname> format'''
        with self.assertRaises(dmError) as excp:
            ws = ICManageWorkspaceMock('ip1',
                                       cellNamesDict={'ip1' : set(['cella', 'cellb']),
                                                      'ip2' : set(['cellc', 'celld']),
                                                      'ip3' : set(['ip3'])},
                                       moleculesDict={'cella' : set(['cella']),
                                                      'cellb' : set(['cellb1 XXX YYYY', 'ip2 cellc']),
                                                      'cellc' : set(['cellc1', 'ip3 ip3']),
                                                      'celld' : set([]),
                                                      'ip3'   : set(['ip31'])},
                                       elementsDict={'cella' : set(['cellaa', 'cellab']),
                                                     'cellb' : set([]),
                                                     'cellc' : set([]),
                                                     'celld' : set([]),
                                                     'ip3'   : set([])})   
            mc = MoleculeCollector(ws)
            molecules = mc.collectMolecules('lvs') 
            _ = molecules
        #pylint: disable = W0511
        self.assertEqual(excp.exception.message.replace('\n',''), 
                         "Entry in molecules or elements list must be in <cellname> or <libname> <cellname> format.    Found '['cellb1', 'XXX', 'YYYY']'")
       
              
    def test_format_cell_names(self):

        '''Test error output when the entry in cell_names.txt is not in <cellname> format'''
        with self.assertRaises(dmError) as excp:
            ws = ICManageWorkspaceMock('ip1',
                                       cellNamesDict={'ip1' : set(['cella XXX', 'cellb']),
                                                      'ip2' : set(['cellc', 'celld']),
                                                      'ip3' : set(['ip3'])},
                                       moleculesDict={'cella' : set(['cella']),
                                                      'cellb' : set(['cellb1', 'ip2 cellc']),
                                                      'cellc' : set(['cellc1', 'ip3 ip3']),
                                                      'celld' : set([]),
                                                      'ip3'   : set(['ip31'])},
                                       elementsDict={'cella' : set(['cellaa', 'cellab']),
                                                     'cellb' : set([]),
                                                     'cellc' : set([]),
                                                     'celld' : set([]),
                                                     'ip3'   : set([])})   
            mc = MoleculeCollector(ws)
            molecules = mc.collectMolecules('lvs')
            _ = molecules
        print excp.exception.message.replace('\n', '')
        self.assertRegexpMatches(excp.exception.message.replace('\n', ''), r"Entry in cell_names.txt must be in <cellname> format.    Found 'cella XXX'")
        
    def test_missing_cell_names(self):
        
        '''Test error output when the entry in cell_names.txt is not in <cellname> format'''
        with self.assertRaises(dmError) as excp:
            ws = ICManageWorkspaceMock('ip1',
                                       cellNamesDict={'ip1' : set([]),
                                                      'ip2' : set(['cellc', 'celld']),
                                                      'ip3' : set(['ip3'])},
                                       moleculesDict={'cella' : set(['cella']),
                                                      'cellb' : set(['cellb1', 'ip2 cellc']),
                                                      'cellc' : set(['cellc1', 'ip3 ip3']),
                                                      'celld' : set([]),
                                                      'ip3'   : set(['ip31'])},
                                       elementsDict={'cella' : set(['cellaa', 'cellab']),
                                                     'cellb' : set([]),
                                                     'cellc' : set([]),
                                                     'celld' : set([]),
                                                     'ip3'   : set([])})   
            mc = MoleculeCollector(ws)
            molecules = mc.collectMolecules('lvs')
            _ = molecules
        self.assertRegexpMatches(excp.exception.message.replace('\n', ''), r"Either molecule list or element list must be present for 'ip1'.")
                    
if __name__ == "__main__":
    unittest.main()
