#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/gencompositefilelist_test.py#1 $

"""
Test the gencompositefilelist class. More tests are performed using doctest
via the doctest-unittest interface.
"""

import os
import unittest

import pyfakefs.fake_filesystem_unittest
import dmx.dmlib.gencompositefilelist
from dmx.dmlib.ICManageWorkspaceMock import ICManageWorkspaceMock
from dmx.dmlib.templateset.verifier import Verifier
from dmx.dmlib.CheckType import CheckType
from dmx.dmlib.VpMock import VpMock
from dmx.dmlib.VpNadder import _expandFilelistForVp_TS
from dmx.dmlib.dmError import dmError


def load_tests(loader, tests, ignore): # pylint: disable=W0613
    '''Load the gencompositefilelist.py doctest tests into unittest.'''
    return pyfakefs.fake_filesystem_unittest.load_doctests(loader, 
                                                           tests, 
                                                           ignore,
                                                           dmx.dmlib.gencompositefilelist)
    
class TestUtils (unittest.TestCase):
    def test_Utils(self):
        
        # pylint: disable = W0212
        replaceOne = dmx.dmlib.gencompositefilelist._replaceEnvVarMatches # abbreviation
        
        env = { 'a': 'A', 
                'c': 'C',
                '@': 'Z'}

        repl1 = replaceOne (text = 'text $a $b text', 
                            env  = env)
        self.assertEqual (repl1, "text A $b text")
        
        repl2 = replaceOne (text = 'text ${a} ${b} text', 
                            env  = env)
        self.assertEqual (repl2, "text A ${b} text")
        
        repl3 = replaceOne (text = 'text ${@} ${b} text', 
                            env  = env)
        self.assertEqual (repl3, "text ${@} ${b} text")
        

#@unittest.skip ('Testing other stuff')
class TestGencompositefilelist(pyfakefs.fake_filesystem_unittest.TestCase):
    '''Test the gencompositefilelist class.'''

    _templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="28468" id="IPSPEC">
          <description>
            List of top level cells within the IP and list of deliverables for the IP. Since this deliverable drives VP, VP cannot verify it.
          </description>
          <pattern id="cell_names">
            &ip_name;/ipspec/&ip_name;.cell_names.txt
          </pattern>
          </template>
          <template caseid="24166" id="RTL">
            <description>
              Verilog register transfer level behavioral code.
            </description>
            <filelist id="cell_filelist">
              &ip_name;/rtl/filelist/&cell_name;.f
            </filelist>
            <filelist id="cell_filelist_dv" minimum="0">
              &ip_name;/rtl/filelists/dv/&cell_name;.f
            </filelist>
            <filelist id="cell_filelist_syn" minimum="0">
              &ip_name;/rtl/filelists/syn/&cell_name;.f
            </filelist>
          </template>
          <template caseid="24175" id="GLNPOSTPNR">
            <description> Post place and route Verilog gate-level netlist. </description>
            <filelist id="hierarchical_filelist">
              &ip_name;/glnpostpnr/filelist/&cell_name;.f
            </filelist>
          </template>
          <template caseid="36918" id="FCVNETLIST">
            <description> Test two filelists </description>
            <filelist id="hierarchical_filelist">
              &ip_name;/fcvnetlist/filelist/&cell_name;.f
            </filelist>
          </template>
        </templateset>'''
    
    def setUp(self):
        self.maxDiff = None
        self.setUpPyfakefs()

    # RTL files for empty IP
        self.fs.CreateFile('/test/testworkspace/empty/rtl/filelist/empty.f')

    # ip1
        self.fs.CreateFile('/test/testworkspace/ip1/ipspec/ip1.cell_names.txt',
                             contents=('cella\n'
                                       'cellb\n'))
        # RTL files for ip1, cella
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/filelist/cella.f',
                             contents=('+incdir+wkspace_root/ip1/rtl/include\n'
                                       'wkspace_root/ip1/rtl/cella.v\n'
                                       'wkspace_root/ip1/rtl/a1.v\n'
                                       'wkspace_root/ip1/rtl/a2.v\n'
                                       'wkspace_root/ip1/rtl/common/v.v\n'
                                       'wkspace_root/ip1/rtl/common/w.v\n'
                                       '-f wkspace_root/ip2/rtl/filelist/cellc.f\n'))
        self.fs.CreateDirectory('/test/testworkspace/ip1/rtl/include')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/cella.v')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/a1.v')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/a2.v')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/common/v.v')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/common/w.v')

        # RTL files for ip1, cellb
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/filelist/cellb.f',
                             contents=('+incdir+wkspace_root/ip1/rtl/include\n'
                                       'wkspace_root/ip1/rtl/cellb.v\n'
                                       'wkspace_root/ip1/rtl/b1.v\n'
                                       'wkspace_root/ip1/rtl/b2.v\n'
                                       'wkspace_root/ip1/rtl/common/v.v\n'
                                       'wkspace_root/ip1/rtl/common/w.v\n'
                                       '-f wkspace_root/ip3/rtl/filelist/ip3.f\n'))
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/cellb.v')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/b1.v')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/b2.v')

    # ip2
        self.fs.CreateFile('/test/testworkspace/ip1/ipspec/ip2.cell_names.txt',
                             contents=('cellc\n'
                                       'celld\n'))
        # RTL files for ip2, cellc
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/filelist/cellc.f',
                             contents=('wkspace_root/ip2/rtl/cellc.v\n'
                                       'wkspace_root/ip2/rtl/c1.v\n'
                                       'wkspace_root/ip2/rtl/c2.v\n'
                                       'wkspace_root/ip2/rtl/common/x.v\n'
                                       'wkspace_root/ip2/rtl/common/y.v\n'
                                       '-f wkspace_root/ip3/rtl/filelist/ip3.f\n'))
        self.fs.CreateDirectory('/test/testworkspace/ip2/rtl/include')
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/cellc.v')
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/c1.v')
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/c2.v')
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/common/x.v')
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/common/y.v')

        # RTL files for ip2, celld
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/filelist/celld.f',
                             contents=('+incdir+wkspace_root/ip2/rtl/include\n'
                                       'wkspace_root/ip2/rtl/celld.v\n'
                                       'wkspace_root/ip2/rtl/d1.v\n'
                                       'wkspace_root/ip2/rtl/d2.v\n'
                                       'wkspace_root/ip2/rtl/common/x.v\n'
                                       'wkspace_root/ip2/rtl/common/y.v\n'
                                       '-f wkspace_root/ip3/rtl/filelist/ip3.f\n'))
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/celld.v')
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/d1.v')
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/d2.v')


    # GLNPOSTPNR files for ip2
        self.fs.CreateFile('/test/testworkspace/ip2/glnpostpnr/filelist/ip2.f',
                             contents=('wkspace_root/ip3/glnpostpnr/h_gln.v\n'
                                       'wkspace_root/ip3/glnpostpnr/i_gln.v\n'))
        self.fs.CreateFile('/test/testworkspace/ip2/glnpostpnr/h_gln.v')
        self.fs.CreateFile('/test/testworkspace/ip2/glnpostpnr/i_gln.v')

    # RTL files for ip3
        self.fs.CreateFile('/test/testworkspace/ip3/rtl/filelist/ip3.f',
                             contents=('wkspace_root/ip3/rtl/ip3.v\n'
                                       'wkspace_root/ip3/rtl/p.v\n'
                                       'wkspace_root/ip3/rtl/q.v\n'
                                       'wkspace_root/ip3/rtl/level5/r.v\n'
                                       'wkspace_root/ip3/rtl/level6/eng/s.v\n'))
        self.fs.CreateFile('/test/testworkspace/ip3/rtl/ip3.v')
        self.fs.CreateFile('/test/testworkspace/ip3/rtl/p.v')
        self.fs.CreateFile('/test/testworkspace/ip3/rtl/q.v')
        self.fs.CreateFile('/test/testworkspace/ip3/rtl/level5/r.v')
        self.fs.CreateFile('/test/testworkspace/ip3/rtl/level6/eng/s.v')

    # Create workspace
        self._ws = ICManageWorkspaceMock('ip1',
                                         '/test/testworkspace',
                                         cellNamesDict={'ip1': set(['cella', 'cellb']),
                                                        'ip2': set(['cellc', 'celld']),
                                                        'ip3': set(['ip3'])})
        
        

    # RTL files for ip4 ("separated  RTL filelists)
        self.fs.CreateFile('/test/testworkspace/ip4/ipspec/cell_names.txt',
                             contents=('cella\n'
                                       'cellb\n'))
        self.fs.CreateFile('/test/testworkspace/ip4/rtl/cella.v')
        self.fs.CreateFile('/test/testworkspace/ip4/rtl/a1.v')
        self.fs.CreateFile('/test/testworkspace/ip4/rtl/a2.v')
        self.fs.CreateFile('/test/testworkspace/ip4/rtl/cella_.v')
        self.fs.CreateFile('/test/testworkspace/ip4/rtl/a1_.v')
        self.fs.CreateFile('/test/testworkspace/ip4/rtl/a2_.v')

        # RTL files for ip1, cella
        self.fs.CreateFile('/test/testworkspace/ip4/rtl/filelists/dv/cella.f',
                             contents=('wkspace_root/ip4/rtl/cella.v\n'
                                       'wkspace_root/ip4/rtl/a1.v\n'
                                       'wkspace_root/ip4/rtl/a2.v\n'))
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/filelists/dv/cellb.f',
                             contents=('wkspace_root/ip4/rtl/cella_.v\n'
                                       'wkspace_root/ip4/rtl/a1_.v\n'
                                       'wkspace_root/ip4/rtl/a2_.v\n'))

    # Create workspace
        self._ws_ip4 = ICManageWorkspaceMock('ip4',
                                             '/test/testworkspace',
                                             cellNamesDict={'ip4': set(['cella', 'cellb'])})

    
    def tearDown(self):
        self.tearDownPyfakefs()
        

    # Leading "0" causes this test to run first.
    def test_0setup(self):
        '''Test the test case created by setUp()'''
        self.maxDiff = None

        templatesetChecker = Verifier(self._templatesetXML)
        self.assertTrue(templatesetChecker.isCorrect, 'The test templateset is correct.')
        
        os.chdir('/test/testworkspace')
        typeChecker = CheckType(VpMock('ip1', 'cella', templatesetString=self._templatesetXML))
        typeChecker.checkType('RTL',False)
        self.assertEqual(typeChecker.errors, [])

        typeChecker = CheckType(VpMock('ip1', 'cellb', templatesetString=self._templatesetXML))
        typeChecker.checkType('RTL',False)
        self.assertEqual(typeChecker.errors, [])

        typeChecker = CheckType(VpMock('ip2', 'cellc', templatesetString=self._templatesetXML))
        typeChecker.checkType('RTL',False)
        self.assertEqual(typeChecker.errors, [])

        typeChecker = CheckType(VpMock('ip2', 'celld', templatesetString=self._templatesetXML))
        typeChecker.checkType('RTL',False)
        self.assertEqual(typeChecker.errors, [])

        os.chdir('/test/testworkspace')
        typeChecker = CheckType(VpMock('ip3', templatesetString=self._templatesetXML))
        typeChecker.checkType('RTL',False)
        self.assertEqual(typeChecker.errors, [])
        
    def test_1empty(self):
        '''Test an empty filelist'''
        # Default working directory
        ws = ICManageWorkspaceMock('empty', '/test/testworkspace')
        self.fs.CreateFile('empty/rtl/filelist/empty.f')
        
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/empty/rtl/expanded.f',
                                 ws,
                                 templatesetString=self._templatesetXML)
        expander.expandCells(['empty'])
        with open('/test/testworkspace/empty/rtl/expanded.f') as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            '// . Beginning filelist /test/testworkspace/empty/rtl/filelist/empty.f\n',
            '// . Ending filelist /test/testworkspace/empty/rtl/filelist/empty.f\n'])
        
        
    def test_getFilelistName_NEW(self):
        '''Test filelist indexing'''
        # The filelist indexing methods do not look at the file system
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip4/rtl/expanded.f',
                                 self._ws_ip4,
                                 itemName = 'cell_filelist_dv',
                                 templatesetString=self._templatesetXML)
        self.assertItemsEqual(expander.cellNames, 
                              set(['cella', 'cellb']))
        self.assertEqual(expander.getFilelistName('cella'), 
                         '/test/testworkspace/ip4/rtl/filelists/dv/cella.f')
        self.assertEqual(expander.getFilelistName('cellb'),   
                         '/test/testworkspace/ip4/rtl/filelists/dv/cellb.f')
        

    def test_getFilelistName(self):
        '''Test filelist indexing'''
        # The filelist indexing methods do not look at the file system
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 templatesetString=self._templatesetXML)
        self.assertItemsEqual(expander.cellNames, 
                              set(['cella', 'cellb', 'cellc', 'celld', 'ip3']))
        self.assertEqual(expander.getFilelistName('cella'), '/test/testworkspace/ip1/rtl/filelist/cella.f')
        self.assertEqual(expander.getFilelistName('cellb'), '/test/testworkspace/ip1/rtl/filelist/cellb.f')
        self.assertEqual(expander.getFilelistName('cellc'), '/test/testworkspace/ip2/rtl/filelist/cellc.f')
        self.assertEqual(expander.getFilelistName('celld'), '/test/testworkspace/ip2/rtl/filelist/celld.f')
        self.assertEqual(expander.getFilelistName('ip3'),   '/test/testworkspace/ip3/rtl/filelist/ip3.f')


    def test_parseModulelistFileName(self):
        '''Test the parseModulelistFileName() method'''
        os.remove('/test/testworkspace/ip1/ipspec/ip1.cell_names.txt')
        self.fs.CreateFile('/test/testworkspace/ip1/ipspec/ip1.cell_names.txt',
                             contents=('// comment\n'
                                       'cella  ignore extra fields\n'
                                       '  cellb   \n'))
        cellNames = dmx.dmlib.gencompositefilelist.GenCompositeFilelist.parseCellListFile(
                                '/test/testworkspace/ip1/ipspec/ip1.cell_names.txt')
        self.assertEqual(cellNames, ['cella', 'cellb'])
    
    def test_expandOneModule(self):
        '''Generate a full composite filelist'''
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 templatesetString=self._templatesetXML)
        expander.expandCells(['cella'])
        with open('/test/testworkspace/ip1/rtl/expanded.f') as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            '// . Beginning filelist /test/testworkspace/ip1/rtl/filelist/cella.f\n',
            '+incdir+/test/testworkspace/ip1/rtl/include\n',
            '/test/testworkspace/ip1/rtl/cella.v\n',
            '/test/testworkspace/ip1/rtl/a1.v\n',
            '/test/testworkspace/ip1/rtl/a2.v\n',
            '/test/testworkspace/ip1/rtl/common/v.v\n',
            '/test/testworkspace/ip1/rtl/common/w.v\n',
            '// .. Beginning filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n',
            '/test/testworkspace/ip2/rtl/cellc.v\n',
            '/test/testworkspace/ip2/rtl/c1.v\n',
            '/test/testworkspace/ip2/rtl/c2.v\n',
            '/test/testworkspace/ip2/rtl/common/x.v\n',
            '/test/testworkspace/ip2/rtl/common/y.v\n',
            '// ... Beginning filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '/test/testworkspace/ip3/rtl/ip3.v\n',
            '/test/testworkspace/ip3/rtl/p.v\n',
            '/test/testworkspace/ip3/rtl/q.v\n',
            '/test/testworkspace/ip3/rtl/level5/r.v\n',
            '/test/testworkspace/ip3/rtl/level6/eng/s.v\n',
            '// ... Ending filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '// .. Ending filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n',
            '// . Ending filelist /test/testworkspace/ip1/rtl/filelist/cella.f\n'])

    def test_expandTwoModules(self):
        '''Generate a full composite filelist'''
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 templatesetString=self._templatesetXML)
        expander.expandCells(['cella', 'cellb'])
        with open('/test/testworkspace/ip1/rtl/expanded.f') as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            '// . Beginning filelist /test/testworkspace/ip1/rtl/filelist/cella.f\n',
            '+incdir+/test/testworkspace/ip1/rtl/include\n',
            '/test/testworkspace/ip1/rtl/cella.v\n',
            '/test/testworkspace/ip1/rtl/a1.v\n',
            '/test/testworkspace/ip1/rtl/a2.v\n',
            '/test/testworkspace/ip1/rtl/common/v.v\n',
            '/test/testworkspace/ip1/rtl/common/w.v\n',
            '// .. Beginning filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n',
            '/test/testworkspace/ip2/rtl/cellc.v\n',
            '/test/testworkspace/ip2/rtl/c1.v\n',
            '/test/testworkspace/ip2/rtl/c2.v\n',
            '/test/testworkspace/ip2/rtl/common/x.v\n',
            '/test/testworkspace/ip2/rtl/common/y.v\n',
            '// ... Beginning filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '/test/testworkspace/ip3/rtl/ip3.v\n',
            '/test/testworkspace/ip3/rtl/p.v\n',
            '/test/testworkspace/ip3/rtl/q.v\n',
            '/test/testworkspace/ip3/rtl/level5/r.v\n',
            '/test/testworkspace/ip3/rtl/level6/eng/s.v\n',
            '// ... Ending filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '// .. Ending filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n',
            '// . Ending filelist /test/testworkspace/ip1/rtl/filelist/cella.f\n',
            '// . Beginning filelist /test/testworkspace/ip1/rtl/filelist/cellb.f\n',
            '// duplicate +incdir+/test/testworkspace/ip1/rtl/include\n',
            '/test/testworkspace/ip1/rtl/cellb.v\n',
            '/test/testworkspace/ip1/rtl/b1.v\n',
            '/test/testworkspace/ip1/rtl/b2.v\n',
            '// duplicate /test/testworkspace/ip1/rtl/common/v.v\n',
            '// duplicate /test/testworkspace/ip1/rtl/common/w.v\n',
            '// duplicate -f /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '// . Ending filelist /test/testworkspace/ip1/rtl/filelist/cellb.f\n'])
                                
    def test_preExpandedFilelist(self):
        '''Test a filelist that has Verilog files from other IPs and cells'''
        # Replace the filelist for ip1, cella with a filelist that
        # contains .v files from other IPs
        os.remove('/test/testworkspace/ip1/rtl/filelist/cella.f')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/filelist/cella.f',
            contents=(
            'wkspace_root/ip1/rtl/cella.v\n'
            'wkspace_root/ip2/rtl/cellc.v\n'
            'wkspace_root/ip3/rtl/ip3.v\n'))
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 templatesetString=self._templatesetXML)
        expander.expandCells(['cella'])
        with open('/test/testworkspace/ip1/rtl/expanded.f') as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            '// . Beginning filelist /test/testworkspace/ip1/rtl/filelist/cella.f\n',
            '/test/testworkspace/ip1/rtl/cella.v\n',
            '/test/testworkspace/ip2/rtl/cellc.v\n',
            '/test/testworkspace/ip3/rtl/ip3.v\n',
            '// . Ending filelist /test/testworkspace/ip1/rtl/filelist/cella.f\n'])

    def test_parseModulelistFile(self):
        '''Test the operation of the modulelist file parser'''
        os.remove('/test/testworkspace/ip1/ipspec/ip1.cell_names.txt')
        self.fs.CreateFile('/test/testworkspace/ip1/ipspec/ip1.cell_names.txt',
                             contents=('// Comment\n'
                                       'cella ignore extra tokens\n'
                                       'cellb\n'))
        
        cellNames = dmx.dmlib.gencompositefilelist.GenCompositeFilelist.parseCellListFile(
                                '/test/testworkspace/ip1/ipspec/ip1.cell_names.txt')
        self.assertEqual(cellNames, ['cella', 'cellb'])
        cellNames = dmx.dmlib.gencompositefilelist.GenCompositeFilelist.parseCellListFile(None)
        self.assertEqual(cellNames, [])
        
    def test_nonexistentModule(self):
        '''Ask for a filelist for a nonexistent module'''
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 templatesetString=self._templatesetXML)
        with self.assertRaises(dmError):
            expander.expandCells(['nonexistent'])
        
    def test_missingTopFilelist(self):
        '''Ask for a cell with a nonexistent filelist'''
        self.fs.RemoveObject('/test/testworkspace/ip1/rtl/filelist/cella.f')
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 templatesetString=self._templatesetXML)
        with self.assertRaises(dmError):
            expander.expandCells(['cella'])

    def test_missingHierFilelist(self):
        '''Ask for a cell with a nonexistent filelist in its hierarchy'''
        self.fs.RemoveObject('/test/testworkspace/ip3/rtl/filelist/ip3.f')
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 templatesetString=self._templatesetXML)
        with self.assertRaises(dmError):
            expander.expandCells(['cella'])

    def test_rtllec(self):
        '''Test the operation of the doRtllec option'''
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 templatesetString=self._templatesetXML)
        # Test the baseline, without any RTLLEC files existing
        expander.expandCells(['cellc'], doRtllec=True)
        with open('/test/testworkspace/ip1/rtl/expanded.f') as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            '// . Beginning filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n',
            '/test/testworkspace/ip2/rtl/cellc.v\n',
            '/test/testworkspace/ip2/rtl/c1.v\n',
            '/test/testworkspace/ip2/rtl/c2.v\n',
            '/test/testworkspace/ip2/rtl/common/x.v\n',
            '/test/testworkspace/ip2/rtl/common/y.v\n',
            '// .. Beginning filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '/test/testworkspace/ip3/rtl/ip3.v\n',
            '/test/testworkspace/ip3/rtl/p.v\n',
            '/test/testworkspace/ip3/rtl/q.v\n',
            '/test/testworkspace/ip3/rtl/level5/r.v\n',
            '/test/testworkspace/ip3/rtl/level6/eng/s.v\n',
            '// .. Ending filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '// . Ending filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n'])

        # Create one RTLLEC file
        self.fs.CreateFile('/test/testworkspace/ip2/rtllec/cellc.v')
        expander.expandCells(['cellc'], doRtllec=True)
        with open('/test/testworkspace/ip1/rtl/expanded.f') as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            '// . Beginning filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n',
            '/test/testworkspace/ip2/rtllec/cellc.v\n',
            '/test/testworkspace/ip2/rtl/c1.v\n',
            '/test/testworkspace/ip2/rtl/c2.v\n',
            '/test/testworkspace/ip2/rtl/common/x.v\n',
            '/test/testworkspace/ip2/rtl/common/y.v\n',
            '// .. Beginning filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '/test/testworkspace/ip3/rtl/ip3.v\n',
            '/test/testworkspace/ip3/rtl/p.v\n',
            '/test/testworkspace/ip3/rtl/q.v\n',
            '/test/testworkspace/ip3/rtl/level5/r.v\n',
            '/test/testworkspace/ip3/rtl/level6/eng/s.v\n',
            '// .. Ending filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '// . Ending filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n'])
                                  
        # Add another RTLLEC file
        self.fs.CreateFile('/test/testworkspace/ip3/rtllec/ip3.v')
        expander.expandCells(['cellc'], doRtllec=True)
        with open('/test/testworkspace/ip1/rtl/expanded.f') as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            '// . Beginning filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n',
            '/test/testworkspace/ip2/rtllec/cellc.v\n',
            '/test/testworkspace/ip2/rtl/c1.v\n',
            '/test/testworkspace/ip2/rtl/c2.v\n',
            '/test/testworkspace/ip2/rtl/common/x.v\n',
            '/test/testworkspace/ip2/rtl/common/y.v\n',
            '// .. Beginning filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '/test/testworkspace/ip3/rtllec/ip3.v\n',
            '/test/testworkspace/ip3/rtl/p.v\n',
            '/test/testworkspace/ip3/rtl/q.v\n',
            '/test/testworkspace/ip3/rtl/level5/r.v\n',
            '/test/testworkspace/ip3/rtl/level6/eng/s.v\n',
            '// .. Ending filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '// . Ending filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n'])
                                  
    def test_parseBlackboxFile(self):
        '''Test the operation of the blackbox file list parser'''
        self.fs.CreateFile('/test/testworkspace/blackbox.txt',
                             contents=('// Comment\n'
                                       '/test/testworkspace/ip1/rtl/black/cella.v\n'
                                       '/test/testworkspace/ip1/rtl/black/cellb.v\n'))
        
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/black/cella.v')

        files = dmx.dmlib.gencompositefilelist.GenCompositeFilelist.parseBlackboxFile('/test/testworkspace/blackbox.txt')
        self.assertEqual(files, ['/test/testworkspace/ip1/rtl/black/cella.v',
                                 '/test/testworkspace/ip1/rtl/black/cellb.v'])
        files = dmx.dmlib.gencompositefilelist.GenCompositeFilelist.parseBlackboxFile(None)
        self.assertEqual(files, [])
        
    def test_getBlackboxFileName(self):
        '''Test black box file indexing'''
        # The filelist indexing methods do not look at the file system
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 blackboxFiles=['wkspace_root/ip1/rtl/black/cella.v',
                                                '/test/testworkspace/ip1/rtl/black/cellb.v'],
                                 templatesetString=self._templatesetXML)
        self.assertItemsEqual(expander.blackboxModules, ['cella', 'cellb'])
        self.assertEqual(expander.getBlackboxFileName('cella'), '/test/testworkspace/ip1/rtl/black/cella.v')
        self.assertEqual(expander.getBlackboxFileName('cellb'), '/test/testworkspace/ip1/rtl/black/cellb.v')

    def test_blackbox(self):
        '''Test the operation of the blackbox file list'''
        
        # Make the top module a black box
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/black/cella.v')
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 blackboxFiles=['wkspace_root/ip1/rtl/black/cella.v'],
                                 templatesetString=self._templatesetXML)
        expander.expandCells(['cella'])
        with open('/test/testworkspace/ip1/rtl/expanded.f') as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            '// substitute black box for -f /test/testworkspace/ip1/rtl/filelist/cella.f\n',
            '/test/testworkspace/ip1/rtl/black/cella.v\n'])

        # Make an intermediate module a black box
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/black/cellc.v')
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 blackboxFiles=['wkspace_root/ip2/rtl/black/cellc.v'],
                                 templatesetString=self._templatesetXML)
        expander.expandCells(['cella'])
        with open('/test/testworkspace/ip1/rtl/expanded.f') as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            '// . Beginning filelist /test/testworkspace/ip1/rtl/filelist/cella.f\n',
            '+incdir+/test/testworkspace/ip1/rtl/include\n',
            '/test/testworkspace/ip1/rtl/cella.v\n',
            '/test/testworkspace/ip1/rtl/a1.v\n',
            '/test/testworkspace/ip1/rtl/a2.v\n',
            '/test/testworkspace/ip1/rtl/common/v.v\n',
            '/test/testworkspace/ip1/rtl/common/w.v\n',
            '// substitute black box for -f /test/testworkspace/ip2/rtl/filelist/cellc.f\n',
            '/test/testworkspace/ip2/rtl/black/cellc.v\n',
            '// . Ending filelist /test/testworkspace/ip1/rtl/filelist/cella.f\n'])

        # Make an arbitrary .v file a black box
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/black/x.v')
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 blackboxFiles=['wkspace_root/ip2/rtl/black/x.v'],
                                 templatesetString=self._templatesetXML)
        expander.expandCells(['cella'])
        with open('/test/testworkspace/ip1/rtl/expanded.f') as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            "// . Beginning filelist /test/testworkspace/ip1/rtl/filelist/cella.f\n",
            '+incdir+/test/testworkspace/ip1/rtl/include\n',
            '/test/testworkspace/ip1/rtl/cella.v\n',
            '/test/testworkspace/ip1/rtl/a1.v\n',
            '/test/testworkspace/ip1/rtl/a2.v\n',
            '/test/testworkspace/ip1/rtl/common/v.v\n',
            '/test/testworkspace/ip1/rtl/common/w.v\n',
            '// .. Beginning filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n',
            '/test/testworkspace/ip2/rtl/cellc.v\n',
            '/test/testworkspace/ip2/rtl/c1.v\n',
            '/test/testworkspace/ip2/rtl/c2.v\n',
            '// substitute black box for /test/testworkspace/ip2/rtl/common/x.v\n',
            '/test/testworkspace/ip2/rtl/black/x.v\n',
            '/test/testworkspace/ip2/rtl/common/y.v\n',
            '// ... Beginning filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '/test/testworkspace/ip3/rtl/ip3.v\n',
            '/test/testworkspace/ip3/rtl/p.v\n',
            '/test/testworkspace/ip3/rtl/q.v\n',
            '/test/testworkspace/ip3/rtl/level5/r.v\n',
            '/test/testworkspace/ip3/rtl/level6/eng/s.v\n',
            '// ... Ending filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '// .. Ending filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n',
            '// . Ending filelist /test/testworkspace/ip1/rtl/filelist/cella.f\n'])

    def test_initialFilelist(self):
        '''Test the operation of the initial filelist'''
        os.chdir('/test')
        
        self.fs.CreateFile('/test/testworkspace/extra.f',
                             contents=('+define+var1\n'
                                       '+define+var2\n'))
        
        # Check the initialFilelist default
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 templatesetString=self._templatesetXML)
        self.assertEqual(expander.initialFilelist, None)

        # Make sure that initialFilelist='wkspace_root/..' works
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 initialFilelist='wkspace_root/extra.f',
                                 templatesetString=self._templatesetXML)
        self.assertEqual(expander.initialFilelist, '/test/testworkspace/extra.f')

        # Make sure that initialFilelist='relativePath/..' works
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 initialFilelist='testworkspace/extra.f',
                                 templatesetString=self._templatesetXML)
        self.assertEqual(expander.initialFilelist, '/test/testworkspace/extra.f')

        # Make sure that initialFilelist='/absolutePath/..' works
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 initialFilelist='/test/testworkspace/extra.f',
                                 templatesetString=self._templatesetXML)
        self.assertEqual(expander.initialFilelist, '/test/testworkspace/extra.f')

        # Now test the output
        expander.expandCells(['ip3'])
        with open('/test/testworkspace/ip1/rtl/expanded.f') as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            '// . Beginning filelist /test/testworkspace/extra.f\n',
            '+define+var1\n',
            '+define+var2\n',
            '// . Ending filelist /test/testworkspace/extra.f\n',
            '// . Beginning filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '/test/testworkspace/ip3/rtl/ip3.v\n',
            '/test/testworkspace/ip3/rtl/p.v\n',
            '/test/testworkspace/ip3/rtl/q.v\n',
            '/test/testworkspace/ip3/rtl/level5/r.v\n',
            '/test/testworkspace/ip3/rtl/level6/eng/s.v\n',
            '// . Ending filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n'])

    def test_extra(self):
        '''Test the operation of the extra file list'''
        
        # Check the extraFiles default
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 templatesetString=self._templatesetXML)
        self.assertEqual(expander.extraFiles, [])

        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 extraFiles=['wkspace_root/ip1/rtl/extra1.v',
                                             'wkspace_root/ip1/rtl/extra2.v'],
                                 templatesetString=self._templatesetXML)

        self.assertEqual(expander.extraFiles, [
            '/test/testworkspace/ip1/rtl/extra1.v',
            '/test/testworkspace/ip1/rtl/extra2.v'])

        expander.expandCells(['ip3'])
        with open('/test/testworkspace/ip1/rtl/expanded.f') as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            '// . Beginning filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '/test/testworkspace/ip3/rtl/ip3.v\n',
            '/test/testworkspace/ip3/rtl/p.v\n',
            '/test/testworkspace/ip3/rtl/q.v\n',
            '/test/testworkspace/ip3/rtl/level5/r.v\n',
            '/test/testworkspace/ip3/rtl/level6/eng/s.v\n',
            '// . Ending filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '// Start extra files\n',
            '/test/testworkspace/ip1/rtl/extra1.v\n',
            '/test/testworkspace/ip1/rtl/extra2.v\n',
            '// End extra files\n'])

    def test_parseExtraFile(self):
        '''Test the operation of the extra file list parser'''
        self.fs.CreateFile('/test/testworkspace/extra.txt',
                             contents=('// Comment\n'
                                       '/test/testworkspace/ip1/rtl/extra/cella.v\n'
                                       '/test/testworkspace/ip1/rtl/extra/cellb.v\n'))
        
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/extra/cella.v')

        files = dmx.dmlib.gencompositefilelist.GenCompositeFilelist.parseExtraFile('/test/testworkspace/extra.txt')
        self.assertEqual(files, ['/test/testworkspace/ip1/rtl/extra/cella.v',
                                 '/test/testworkspace/ip1/rtl/extra/cellb.v'])
        files = dmx.dmlib.gencompositefilelist.GenCompositeFilelist.parseExtraFile(None)
        self.assertEqual(files, [])
        
    def test_getFilelistLines(self):
        '''Test the getFilelistLines() method'''
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/filelist/ip1.f',
                             contents=('// RTL filelist containing three files\n'
                                       '//Test comment at the beginning of the line followed by non-whitespace\n'
                                       'wkspace_root/ip1/rtl/one.v       // Relative path\n'
                                       'wkspace_root/ip1/rtl/dir/two.v   // Relative path\n'
                                       '/full/path/to/three.v            // Full path\n'))
        
        lines = dmx.dmlib.gencompositefilelist.GenCompositeFilelist.getFilelistLines('/test/testworkspace/ip1/rtl/filelist/ip1.f',
                                                                             '/path/to/workspace')
        self.assertEqual(lines, [
            '/path/to/workspace/ip1/rtl/one.v',
            '/path/to/workspace/ip1/rtl/dir/two.v',
            '/full/path/to/three.v'])

        self.fs.RemoveObject('/test/testworkspace/ip1/rtl/filelist/ip1.f')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/filelist/ip1.f',
                             contents=('// Most VCS options are just passed through\n'
                                       '-anyMinusOption\n'
                                       '+anyPlusOption\n'
                                       '// These VCS options have relative paths in their arguments adjusted\n'
                                       '+incdir+wkspace_root/relpath/to/four.v+/full/path/to/five.v\n'
                                       '-f wkspace_root/relpath/to//six.v\n'
                                       '-y wkspace_root/relpath/to/./seven.v\n'
                                       '// For the -v VCS option, the -v is removed, and the argument is treated as an ordinary file\n'
                                       '-v wkspace_root/relpath/to/eight.v\n'
                                       'wkspace_root/plainFile.v\n'))

        lines = dmx.dmlib.gencompositefilelist.GenCompositeFilelist.getFilelistLines('/test/testworkspace/ip1/rtl/filelist/ip1.f',
                                                                              '/path/to/workspace')
        self.assertEqual(lines, ['-anyMinusOption',
                                 '+anyPlusOption',
                                 '+incdir+/path/to/workspace/relpath/to/four.v+/full/path/to/five.v',
                                 '-f /path/to/workspace/relpath/to/six.v',
                                 '-y /path/to/workspace/relpath/to/seven.v',
                                 '/path/to/workspace/relpath/to/eight.v',
                                 '/path/to/workspace/plainFile.v'])

        lines = dmx.dmlib.gencompositefilelist.GenCompositeFilelist.getFilelistLines(
                                    '/test/testworkspace/ip1/rtl/filelist/ip1.f',
                                    '/path/to/workspace', doKeepVCSOptions=False)
        self.assertEqual(lines, ['/path/to/workspace/plainFile.v'])


    def test_convertStyle(self):
        '''Test the conversion from the old to new style .f filelist.'''
        # Create an old style .f filelist for ip1, cella
        os.remove('/test/testworkspace/ip1/rtl/filelist/cella.f')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/filelist/cella.f',
                             contents=('+incdir+wkspace_root/ip1/rtl/include\n'
                                       'wkspace_root/ip1/rtl/cella.v\n'
                                       'wkspace_root/ip1/rtl/a1.v\n'
                                       'wkspace_root/ip1/rtl/a2.v\n'
                                       'wkspace_root/ip1/rtl/common/v.v\n'
                                       'wkspace_root/ip1/rtl/common/w.v\n'
                                       'wkspace_root/ip2/rtl/cellc.v\n'))
        # Create an old style .f filelist for ip1, cellb
        os.remove('/test/testworkspace/ip1/rtl/filelist/cellb.f')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/filelist/cellb.f',
                             contents=('+incdir+wkspace_root/ip1/rtl/include\n'
                                       'wkspace_root/ip1/rtl/cellb.v\n'
                                       'wkspace_root/ip1/rtl/b1.v\n'
                                       'wkspace_root/ip1/rtl/b2.v\n'
                                       'wkspace_root/ip1/rtl/common/v.v\n'
                                       'wkspace_root/ip1/rtl/common/w.v\n'
                                       'wkspace_root/ip3/rtl/ip3.v\n'))
        
        expander = dmx.dmlib.gencompositefilelist.GenCompositeFilelist('RTL',
                                 '/test/testworkspace/ip1/rtl/expanded.f',
                                 self._ws,
                                 templatesetString=self._templatesetXML)
        expander.convertFilelists(['cella', 'cellb'])

        self.assertTrue(os.path.exists('/test/testworkspace/ip1/rtl/filelist/cella.oldstyle.f'))
        self.assertTrue(os.path.exists('/test/testworkspace/ip1/rtl/filelist/cellb.oldstyle.f'))
        
        with open('/test/testworkspace/ip1/rtl/filelist/cella.f') as f:
            lines = f.readlines()
        self.assertEqual(lines, ['+incdir+wkspace_root/ip1/rtl/include\n',
                                 'wkspace_root/ip1/rtl/cella.v\n',
                                 'wkspace_root/ip1/rtl/a1.v\n',
                                 'wkspace_root/ip1/rtl/a2.v\n',
                                 'wkspace_root/ip1/rtl/common/v.v\n',
                                 'wkspace_root/ip1/rtl/common/w.v\n',
                                 '-f wkspace_root/ip2/rtl/filelist/cellc.f\n'])

        with open('/test/testworkspace/ip1/rtl/filelist/cellb.f') as f:
            lines = f.readlines()
        self.assertEqual(lines, ['+incdir+wkspace_root/ip1/rtl/include\n',
                                 'wkspace_root/ip1/rtl/cellb.v\n',
                                 'wkspace_root/ip1/rtl/b1.v\n',
                                 'wkspace_root/ip1/rtl/b2.v\n',
                                 'wkspace_root/ip1/rtl/common/v.v\n',
                                 'wkspace_root/ip1/rtl/common/w.v\n',
                                 '-f wkspace_root/ip3/rtl/filelist/ip3.f\n'])

    def test_expandFilelistForVp_RTL(self):
        '''Test dmx.dmlib.VpNadder.expandFilelistForVp() with .f filelists and RTL'''
        # Initialize VpNadder class variables
        os.chdir('/test/testworkspace')
           
        vp = VpMock('ip2',
                    cell_name='cellc',
                    ws=self._ws,
                    deliverableName='RTL',
                    templatesetString=self._templatesetXML)
        
        filelistName = _expandFilelistForVp_TS ('RTL',
                                                vp,
                                                templatesetString=self._templatesetXML)
        with open(filelistName) as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            '// . Beginning filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n',
            '/test/testworkspace/ip2/rtl/cellc.v\n',
            '/test/testworkspace/ip2/rtl/c1.v\n',
            '/test/testworkspace/ip2/rtl/c2.v\n',
            '/test/testworkspace/ip2/rtl/common/x.v\n',
            '/test/testworkspace/ip2/rtl/common/y.v\n',
            '// .. Beginning filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '/test/testworkspace/ip3/rtl/ip3.v\n',
            '/test/testworkspace/ip3/rtl/p.v\n',
            '/test/testworkspace/ip3/rtl/q.v\n',
            '/test/testworkspace/ip3/rtl/level5/r.v\n',
            '/test/testworkspace/ip3/rtl/level6/eng/s.v\n',
            '// .. Ending filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '// . Ending filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n'])
                                  
    def test_expandFilelistForVp_RTLLEC(self):
        '''Test dmx.dmlib.VpNadder.expandFilelistForVp() with .f filelists and RTLLEC'''
        # Initialize VpNadder class variables
        os.chdir('/test/testworkspace')
        
        self.fs.CreateFile('/test/testworkspace/ip2/rtllec/cellc.v')
        self.fs.CreateFile('/test/testworkspace/ip3/rtllec/ip3.v')

        vp = VpMock ('ip2',
                     cell_name='cellc',
                     deliverableName='RTLLEC',
                     ws=self._ws,
                     templatesetString=self._templatesetXML)
        
        filelistName = _expandFilelistForVp_TS ('RTLLEC',
                                                vp,
                                                templatesetString=self._templatesetXML)
        with open(filelistName) as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            '// . Beginning filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n',
            '/test/testworkspace/ip2/rtllec/cellc.v\n',
            '/test/testworkspace/ip2/rtl/c1.v\n',
            '/test/testworkspace/ip2/rtl/c2.v\n',
            '/test/testworkspace/ip2/rtl/common/x.v\n',
            '/test/testworkspace/ip2/rtl/common/y.v\n',
            '// .. Beginning filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '/test/testworkspace/ip3/rtllec/ip3.v\n',
            '/test/testworkspace/ip3/rtl/p.v\n',
            '/test/testworkspace/ip3/rtl/q.v\n',
            '/test/testworkspace/ip3/rtl/level5/r.v\n',
            '/test/testworkspace/ip3/rtl/level6/eng/s.v\n',
            '// .. Ending filelist /test/testworkspace/ip3/rtl/filelist/ip3.f\n',
            '// . Ending filelist /test/testworkspace/ip2/rtl/filelist/cellc.f\n'])
                                  
        
if __name__ == "__main__":
    unittest.main(verbosity=2)
