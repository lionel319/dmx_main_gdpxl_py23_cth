#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/ExpandFilelist_test.py#1 $

"""
Test the ExpandFilelist class. Most of the tests are performed using doctest
via the doctest-unittest interface.
"""

import os
import re
import unittest
import shutil
import dmx.dmlib.pyfakefs.fake_filesystem_unittest

import dmx.dmlib.ExpandFilelist
import dmx.dmlib.templateset.verifier
from dmx.dmlib.CheckType import CheckType
from dmx.dmlib.VpMock import VpMock
from dmx.dmlib.dmError import dmError
from dmx.dmlib.ICManageWorkspaceMock import ICManageWorkspaceMock
from dmx.dmlib.VpNadder import _expandFilelistForVp_TS

def load_tests(loader, tests, ignore): # pylint: disable=W0613
    '''Load the ExpandFilelist doctest tests into unittest.'''
    return dmx.dmlib.pyfakefs.fake_filesystem_unittest.load_doctests(loader, 
                                                           tests, 
                                                           ignore,
                                                           dmx.dmlib.ExpandFilelist)

@unittest.skip ("Works inside eclispe, not in Makefile.pyunittest - R.G.")
class TestFileListExpander(dmx.dmlib.pyfakefs.fake_filesystem_unittest.TestCase): # pylint: disable=R0904
    """Test the FileListExpander class."""

    _templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
        <templateset>
          <template caseid="24166" id="RTL">
            <description>
              Verilog register transfer level behavioral code.
            </description>
            <filelist id="filelist">
              &ip_name;/rtl/&ip_name;.rtl.filelist
            </filelist>
            <filelist id="cell_filelist" minimum="0">
              &ip_name;/rtl/filelist/&cell_name;.f
            </filelist>
          </template>
          <template caseid="24175" id="GLNPOSTPNR">
            <description> Post place and route Verilog gate-level netlist. </description>
            <filelist id="filelist">
              &ip_name;/glnpostpnr/&ip_name;.glnpostpnr.filelist
            </filelist>
          </template>
          <template caseid="36918" id="FCVNETLIST">
            <description> Test two filelists </description>
            <filelist id="fullcore">
              &ip_name;/fcvnetlist/&ip_name;.fcvnetlist.filelist
            </filelist>
            <filelist id="coreless">
              &ip_name;/fcvnetlist/&ip_name;.fcvnetlist.coreless.filelist
            </filelist>
          </template>
        <template caseid="41780" id="RDF">
          <description> RDF data </description>
          <filelist id="filelist">
            &ip_name;/rdf/&ip_name;.rdf.filelist
          </filelist>
          <pattern id="bcm_rdf_map" mimetype="text/tab-separated-values">
            &ip_name;/rdf/&cell_name;.bcm_rdf_map.tsv
          </pattern>
        </template>
      </templateset>'''
        
    def setUp(self):
        self.maxDiff = None
        self.setUpPyfakefs()
                
        # RTL files for empty IP
        self.fs.CreateFile('/test/testworkspace/empty/rtl/empty.rtl.filelist')

        # RTL files for ip1
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/ip1.rtl.filelist',
                             contents=('+incdir+include\n'
                                       'a.v\n'
                                       'b.v\n'
                                       'level1/c.v\n'
                                       'level2/d.v\n'))
        self.fs.CreateDirectory('/test/testworkspace/ip1/rtl/include')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/a.v')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/b.v')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/level1/c.v')
        self.fs.CreateFile('/test/testworkspace/ip1/rtl/level2/d.v')

        # RDF files for ip1
        self.fs.CreateFile('/test/testworkspace/ip1/rdf/ip1.rdf.filelist',
                             contents=('ip1.rdf.xlsx\n'))
        
        # RTL files for ip2
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/ip2.rtl.filelist',
                             contents=('h.v\n'
                                       'i.v\n'
                                       'level3/j.v\n'
                                       'level4/k.v\n'))
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/h.v')
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/i.v')
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/level3/j.v')
        self.fs.CreateFile('/test/testworkspace/ip2/rtl/level4/k.v')

        # RDF files for ip2
        self.fs.CreateFile('/test/testworkspace/ip2/rdf/ip2.rdf.filelist',
                             contents=('ip2a.rdf.xlsx\n'
                                       'ip2b.rdf.xlsx\n'))

        # GLNPOSTPNR files for ip2
        self.fs.CreateFile('/test/testworkspace/ip2/glnpostpnr/ip2.glnpostpnr.filelist',
                             contents=('h_gln.v\n'
                                       'i_gln.v\n'))
        self.fs.CreateFile('/test/testworkspace/ip2/glnpostpnr/h_gln.v')
        self.fs.CreateFile('/test/testworkspace/ip2/glnpostpnr/i_gln.v')

        # RTL files for ip3
        self.fs.CreateFile('/test/testworkspace/ip3/rtl/ip3.rtl.filelist',
                             contents=('p.v\n'
                                       'q.v\n'
                                       'level5/r.v\n'
                                       'level6/s.v\n'))
        self.fs.CreateFile('/test/testworkspace/ip3/rtl/p.v')
        self.fs.CreateFile('/test/testworkspace/ip3/rtl/q.v')
        self.fs.CreateFile('/test/testworkspace/ip3/rtl/level5/r.v')
        self.fs.CreateFile('/test/testworkspace/ip3/rtl/level6/s.v')

        # RDF files for ip3
        self.fs.CreateFile('/test/testworkspace/ip3/rdf/ip3.rdf.filelist',
                             contents=('p.rdf\n'
                                       'q.rdf\n'
                                       'level5/r.rdf\n'
                                       'level6/s.rdf\n'))
        self.fs.CreateFile('/test/testworkspace/ip3/rdf/p.rdf')
        self.fs.CreateFile('/test/testworkspace/ip3/rdf/q.rdf')
        self.fs.CreateFile('/test/testworkspace/ip3/rdf/level5/r.rdf')
        self.fs.CreateFile('/test/testworkspace/ip3/rdf/level6/s.rdf')

        # RTL files for testsubsubip5
        self.fs.CreateFile('/test/testworkspace/testsubsubip5/rtl/testsubsubip5.rtl.filelist',
                             contents=('-anyMinusOption\n'
                                       '+anyPlusOption\n'
                                       '-f u.v\n'
                                       '+incdir+v.v\n'
                                       '-v level7/w.v\n'
                                       '-y level8/x.v\n'))
        self.fs.CreateFile('/test/testworkspace/testsubsubip5/rtl/u.v')
        self.fs.CreateFile('/test/testworkspace/testsubsubip5/rtl/v.v')
        self.fs.CreateFile('/test/testworkspace/testsubsubip5/rtl/level7/w.v')
        self.fs.CreateFile('/test/testworkspace/testsubsubip5/rtl/level8/x.v')

        # FCVNETLIST files for znum
        self.fs.CreateFile('/test/testworkspace/znum/fcvnetlist/znum.fcvnetlist.filelist',
                             contents=('d.v\n'
                                       'e.v\n'))
        self.fs.CreateFile('/test/testworkspace/znum/fcvnetlist/znum.fcvnetlist.coreless.filelist',
                             contents=('f.v\n'
                                       'g.v\n'))
        

        os.chdir('/test')

        
    def tearDown(self):
        self.tearDownPyfakefs()
    

    # Leading "0" causes this test to run first.
    def test_0setup(self):
        '''Test the test case created by setUp()'''
        os.chdir('/test/testworkspace')

        templatesetChecker = dmx.dmlib.templateset.verifier.Verifier(self._templatesetXML)
        self.assertTrue(templatesetChecker.isCorrect, 'The test templateset is correct.')
        
        typeChecker = CheckType(VpMock('ip1', templatesetString=self._templatesetXML))
        typeChecker.check('RTL')
        self.assertEqual(typeChecker.errors, [])

        typeChecker = CheckType(VpMock('ip2', templatesetString=self._templatesetXML))
        typeChecker.check('RTL')
        self.assertEqual(typeChecker.errors, [])

        typeChecker = CheckType(VpMock('ip3', templatesetString=self._templatesetXML))
        typeChecker.check('RTL')
        self.assertEqual(typeChecker.errors, [])
        
    def test_1empty(self):
        '''Test an empty filelist'''
        # Working directory /test
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('RTL',
                                                    'testworkspace/empty/rtl/expanded.rtl.filelist',
                                                    templatesetString=self._templatesetXML)
        expander.expandFilelists(['testworkspace/empty/rtl/empty.rtl.filelist'])
        f = open('testworkspace/empty/rtl/expanded.rtl.filelist')
        actualExpanded = f.read()
        f.close()
        self.assertEqual(actualExpanded, "// Start files from filelist 'testworkspace/empty/rtl/empty.rtl.filelist'\n"
                                         "// End files from filelist 'testworkspace/empty/rtl/empty.rtl.filelist'\n")
        
        # Working directory /test/testworkspace/
        os.chdir('/test/testworkspace')
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('RTL',
                                                    'empty/rtl/expanded.rtl.filelist',
                                                    templatesetString=self._templatesetXML)
        expander.expandFilelists(['empty/rtl/empty.rtl.filelist'])
        f = open('empty/rtl/expanded.rtl.filelist')
        actualExpanded = f.read()
        f.close()
        self.assertEqual(actualExpanded, "// Start files from filelist 'empty/rtl/empty.rtl.filelist'\n"
                                         "// End files from filelist 'empty/rtl/empty.rtl.filelist'\n")
    
    # The expected results have long lines, so allow long lines
    # pylint: disable=C0301
    
    def test_expandAll_RTL(self):
        '''Expand the RTLs for all IPs in ICManage workspace
        jmcgehee+zz_dm_test+ip1+9.
        
        This test depends on the actual ICManage test workspace.
        '''
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('RTL',
                                                    'testworkspace/ip1.expanded.rtl.filelist',
                                                    '/',
                                                    templatesetString=self._templatesetXML)
        ws = ICManageWorkspaceMock('ip1',
                                   '/test/testworkspace',
                                   hierarchy={'ip1': ['ip2'],
                                              'ip2': []})
        expander.expandAll(ws)
        
        with open('testworkspace/ip1.expanded.rtl.filelist') as f:
            actualExpanded = f.readlines()
        
        expectedExpanded = [
            "// Start files from filelist '/test/testworkspace/ip2/rtl/ip2.rtl.filelist'\n",
            "/test/testworkspace/ip2/rtl/h.v\n",
            "/test/testworkspace/ip2/rtl/i.v\n",
            "/test/testworkspace/ip2/rtl/level3/j.v\n",
            "/test/testworkspace/ip2/rtl/level4/k.v\n",
            "// End files from filelist '/test/testworkspace/ip2/rtl/ip2.rtl.filelist'\n",
            "\n",
            "// Start files from filelist '/test/testworkspace/ip1/rtl/ip1.rtl.filelist'\n",
            "+incdir+/test/testworkspace/ip1/rtl/include\n",
            "/test/testworkspace/ip1/rtl/a.v\n",
            "/test/testworkspace/ip1/rtl/b.v\n",
            "/test/testworkspace/ip1/rtl/level1/c.v\n",
            "/test/testworkspace/ip1/rtl/level2/d.v\n",
            "// End files from filelist '/test/testworkspace/ip1/rtl/ip1.rtl.filelist'\n"]
        self.assertEqual(actualExpanded, expectedExpanded)

    def test_expandAll_TwoFilelists(self):
        '''Expand the FCVNETLIST for each of the two filelists in FCVNETLIST'''
        # Expand the 'fullcore' filelist
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('FCVNETLIST',
                                                    'testworkspace/znum.expanded.fcvnetlist.filelist',
                                                    '/',
                                                    itemName='fullcore',
                                                    templatesetString=self._templatesetXML)
        ws = ICManageWorkspaceMock('znum',
                                   '/test/testworkspace')
        expander.expandAll(ws)
        
        with open('testworkspace/znum.expanded.fcvnetlist.filelist') as f:
            actualExpanded = f.readlines()
        
        self.maxDiff = None
        expectedExpanded = [
            "// Start files from filelist '/test/testworkspace/znum/fcvnetlist/znum.fcvnetlist.filelist'\n",
            '/test/testworkspace/znum/fcvnetlist/d.v\n',
            '/test/testworkspace/znum/fcvnetlist/e.v\n',
            "// End files from filelist '/test/testworkspace/znum/fcvnetlist/znum.fcvnetlist.filelist'\n"]
        self.assertEqual(actualExpanded, expectedExpanded)

        # Expand the 'coreless' filelist
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('FCVNETLIST',
                                                    'testworkspace/znum.expanded.fcvnetlist.coreless.filelist',
                                                    '/',
                                                    itemName='coreless',
                                                    templatesetString=self._templatesetXML)
        expander.expandAll(ws)
        
        with open('testworkspace/znum.expanded.fcvnetlist.coreless.filelist') as f:
            actualExpanded = f.readlines()
        
        self.maxDiff = None
        expectedExpanded = [
            "// Start files from filelist '/test/testworkspace/znum/fcvnetlist/znum.fcvnetlist.coreless.filelist'\n",
            '/test/testworkspace/znum/fcvnetlist/f.v\n',
            '/test/testworkspace/znum/fcvnetlist/g.v\n',
            "// End files from filelist '/test/testworkspace/znum/fcvnetlist/znum.fcvnetlist.coreless.filelist'\n"]
        self.assertEqual(actualExpanded, expectedExpanded)


    def test_expandAll_RTL_ip_name(self):
        '''Expand the RTLs for all IPs in ICManage workspace
        jmcgehee+zz_dm_test+ip1+9.
        
        This test depends on the actual ICManage test workspace.
        '''
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('RTL',
                                                    'testworkspace/ip1.expanded.rtl.filelist',
                                                    '/',
                                                    templatesetString=self._templatesetXML)
        ws = ICManageWorkspaceMock('ip2',
                                   '/test/testworkspace',
                                   hierarchy={'ip2': []})
        expander.expandAll(ws)
        
        with open('testworkspace/ip1.expanded.rtl.filelist') as f:
            actualExpanded = f.readlines()
        
        expectedExpanded = [
            "// Start files from filelist '/test/testworkspace/ip2/rtl/ip2.rtl.filelist'\n",
            "/test/testworkspace/ip2/rtl/h.v\n",
            "/test/testworkspace/ip2/rtl/i.v\n",
            "/test/testworkspace/ip2/rtl/level3/j.v\n",
            "/test/testworkspace/ip2/rtl/level4/k.v\n",
            "// End files from filelist '/test/testworkspace/ip2/rtl/ip2.rtl.filelist'\n"]
        self.assertEqual(actualExpanded, expectedExpanded)

    def test_expandAll_RDF(self):
        '''Expand the RDFs for all IPs in ICManage workspace
        jmcgehee+zz_dm_test+ip1+9.
        
        This test depends on the actual ICManage test workspace.
        '''
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('RDF',
                                                    'testworkspace/ip1.expanded.rtl.filelist',
                                                    '/',
                                                    templatesetString=self._templatesetXML)
        ws = ICManageWorkspaceMock('ip1',
                                   '/test/testworkspace',
                                   hierarchy={'ip1': ['ip2'],
                                              'ip2': []})
        expander.expandAll(ws)
        
        with open('testworkspace/ip1.expanded.rtl.filelist') as f:
            actualExpanded = f.readlines()
        
        expectedExpanded = [
            "// Start files from filelist '/test/testworkspace/ip2/rdf/ip2.rdf.filelist'\n",
            "/test/testworkspace/ip2/rdf/ip2a.rdf.xlsx\n",
            "/test/testworkspace/ip2/rdf/ip2b.rdf.xlsx\n",
            "// End files from filelist '/test/testworkspace/ip2/rdf/ip2.rdf.filelist'\n",
            "\n",
            "// Start files from filelist '/test/testworkspace/ip1/rdf/ip1.rdf.filelist'\n",
            "/test/testworkspace/ip1/rdf/ip1.rdf.xlsx\n",
            "// End files from filelist '/test/testworkspace/ip1/rdf/ip1.rdf.filelist'\n"]
        self.assertEqual(actualExpanded, expectedExpanded)

    def test_expandIPs_RTL(self):
        '''Expand the RTLs for one IP in ICManage workspace
        jmcgehee+zz_dm_test+ip1+9.
        
        This test depends on the actual ICManage test workspace.
        '''
        # Default working directory
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('RTL',
                                                    'testworkspace/ip1.expanded.rtl.filelist',
                                                    '/',
                                                    templatesetString=self._templatesetXML)
        ws = ICManageWorkspaceMock('ip1',
                                   '/test/testworkspace',
                                   hierarchy={'ip1': ['ip2'],
                                              'ip2': []})
        expander.expandIPs(['ip1'], ws)
        
        with open('testworkspace/ip1.expanded.rtl.filelist') as f:
            actualExpanded = f.readlines()
        
        expectedExpanded = [
            "// Start files from filelist '/test/testworkspace/ip1/rtl/ip1.rtl.filelist'\n",
            "+incdir+/test/testworkspace/ip1/rtl/include\n",
            "/test/testworkspace/ip1/rtl/a.v\n",
            "/test/testworkspace/ip1/rtl/b.v\n",
            "/test/testworkspace/ip1/rtl/level1/c.v\n",
            "/test/testworkspace/ip1/rtl/level2/d.v\n",
            "// End files from filelist '/test/testworkspace/ip1/rtl/ip1.rtl.filelist'\n",
        ]
        self.assertEqual(actualExpanded, expectedExpanded)

    def test_expandIPs_RDF(self):
        '''Expand the RDFs for one IP in ICManage workspace
        jmcgehee+zz_dm_test+ip1+9.
        
        This test depends on the actual ICManage test workspace.
        '''
        # Default working directory
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('RDF',
                                                    'testworkspace/ip2.expanded.rdf.filelist',
                                                    '/',
                                                    templatesetString=self._templatesetXML)
        ws = ICManageWorkspaceMock('ip1',
                                   '/test/testworkspace',
                                   hierarchy={'ip1': ['ip2'],
                                              'ip2': []})
        expander.expandIPs(['ip2'], ws)
        
        with open('testworkspace/ip2.expanded.rdf.filelist') as f:
            actualExpanded = f.readlines()
        
        expectedExpanded = [
            "// Start files from filelist '/test/testworkspace/ip2/rdf/ip2.rdf.filelist'\n",
            "/test/testworkspace/ip2/rdf/ip2a.rdf.xlsx\n",
            "/test/testworkspace/ip2/rdf/ip2b.rdf.xlsx\n",
            "// End files from filelist '/test/testworkspace/ip2/rdf/ip2.rdf.filelist'\n"]
        self.assertEqual(actualExpanded, expectedExpanded)

    def test_expandFilelists_RTL(self):
        '''Expand a list of filelists without an ICManage workspace'''
        # Default working directory
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('RTL',
                                                    'testworkspace/ip1/rtl/expanded.rtl.filelist',
                                                    templatesetString=self._templatesetXML)
        expander.expandFilelists(['testworkspace/ip1/rtl/ip1.rtl.filelist',
                                  'testworkspace/ip2/rtl/ip2.rtl.filelist',
                                  'testworkspace/ip3/rtl/ip3.rtl.filelist'])
        f = open('testworkspace/ip1/rtl/expanded.rtl.filelist')
        actualExpanded = f.read()
        f.close()
        self.assertEqual(actualExpanded, "// Start files from filelist 'testworkspace/ip1/rtl/ip1.rtl.filelist'\n"
                                              "+incdir+testworkspace/ip1/rtl/include\n"
                                              "testworkspace/ip1/rtl/a.v\n"
                                              "testworkspace/ip1/rtl/b.v\n"
                                              "testworkspace/ip1/rtl/level1/c.v\n"
                                              "testworkspace/ip1/rtl/level2/d.v\n"
                                              "// End files from filelist 'testworkspace/ip1/rtl/ip1.rtl.filelist'\n"
                                              "\n"
                                              "// Start files from filelist 'testworkspace/ip2/rtl/ip2.rtl.filelist'\n"
                                              "testworkspace/ip2/rtl/h.v\n"
                                              "testworkspace/ip2/rtl/i.v\n"
                                              "testworkspace/ip2/rtl/level3/j.v\n"
                                              "testworkspace/ip2/rtl/level4/k.v\n"
                                              "// End files from filelist 'testworkspace/ip2/rtl/ip2.rtl.filelist'\n"
                                              "\n"
                                              "// Start files from filelist 'testworkspace/ip3/rtl/ip3.rtl.filelist'\n"
                                              "testworkspace/ip3/rtl/p.v\n"
                                              "testworkspace/ip3/rtl/q.v\n"
                                              "testworkspace/ip3/rtl/level5/r.v\n"
                                              "testworkspace/ip3/rtl/level6/s.v\n"
                                              "// End files from filelist 'testworkspace/ip3/rtl/ip3.rtl.filelist'\n")
        with open('testworkspace/ip1/rtl/expanded.rtl.filelist', 'r') as f:
            for line in f:
                fileName = re.sub(r'^//.*|^#.*|\s//\s.*|\s#\s.*', '', line)
                fileName = fileName.strip()
                if not fileName:
                    continue
                if re.match(r'^\+incdir\+', fileName):
                    continue
                self.assertTrue(os.path.exists(fileName))
        
        # Working directory testworkspace/
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('RTL',
                                                    'testworkspace/ip1/rtl/expanded.rtl.filelist',
                                                    'testworkspace',
                                                    templatesetString=self._templatesetXML)
        expander.expandFilelists(['testworkspace/ip1/rtl/ip1.rtl.filelist',
                                  'testworkspace/ip2/rtl/ip2.rtl.filelist'])
        f = open('testworkspace/ip1/rtl/expanded.rtl.filelist')
        actualExpanded = f.read()
        f.close()
        self.assertEqual(actualExpanded, "// Start files from filelist 'testworkspace/ip1/rtl/ip1.rtl.filelist'\n"
                                              "+incdir+ip1/rtl/include\n"
                                              "ip1/rtl/a.v\n"
                                              "ip1/rtl/b.v\n"
                                              "ip1/rtl/level1/c.v\n"
                                              "ip1/rtl/level2/d.v\n"
                                              "// End files from filelist 'testworkspace/ip1/rtl/ip1.rtl.filelist'\n"
                                              "\n"
                                              "// Start files from filelist 'testworkspace/ip2/rtl/ip2.rtl.filelist'\n"
                                              "ip2/rtl/h.v\n"
                                              "ip2/rtl/i.v\n"
                                              "ip2/rtl/level3/j.v\n"
                                              "ip2/rtl/level4/k.v\n"
                                              "// End files from filelist 'testworkspace/ip2/rtl/ip2.rtl.filelist'\n")
        
    def test_expandFilelists_RDF(self):
        '''Expand a list of filelists without an ICManage workspace'''
        # Default working directory
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('RDF', 
                                                    'testworkspace/ip1/rtl/expanded.rtl.filelist',
                                                    templatesetString=self._templatesetXML)
        expander.expandFilelists(['testworkspace/ip1/rtl/ip1.rtl.filelist',
                                  'testworkspace/ip2/rtl/ip2.rtl.filelist',
                                  'testworkspace/ip3/rtl/ip3.rtl.filelist'])
        f = open('testworkspace/ip1/rtl/expanded.rtl.filelist')
        actualExpanded = f.read()
        f.close()
        self.assertEqual(actualExpanded, "// Start files from filelist 'testworkspace/ip1/rtl/ip1.rtl.filelist'\n"
                                              "testworkspace/ip1/rtl/a.v\n"
                                              "testworkspace/ip1/rtl/b.v\n"
                                              "testworkspace/ip1/rtl/level1/c.v\n"
                                              "testworkspace/ip1/rtl/level2/d.v\n"
                                              "// End files from filelist 'testworkspace/ip1/rtl/ip1.rtl.filelist'\n"
                                              "\n"
                                              "// Start files from filelist 'testworkspace/ip2/rtl/ip2.rtl.filelist'\n"
                                              "testworkspace/ip2/rtl/h.v\n"
                                              "testworkspace/ip2/rtl/i.v\n"
                                              "testworkspace/ip2/rtl/level3/j.v\n"
                                              "testworkspace/ip2/rtl/level4/k.v\n"
                                              "// End files from filelist 'testworkspace/ip2/rtl/ip2.rtl.filelist'\n"
                                              "\n"
                                              "// Start files from filelist 'testworkspace/ip3/rtl/ip3.rtl.filelist'\n"
                                              "testworkspace/ip3/rtl/p.v\n"
                                              "testworkspace/ip3/rtl/q.v\n"
                                              "testworkspace/ip3/rtl/level5/r.v\n"
                                              "testworkspace/ip3/rtl/level6/s.v\n"
                                              "// End files from filelist 'testworkspace/ip3/rtl/ip3.rtl.filelist'\n")
        with open('testworkspace/ip1/rtl/expanded.rtl.filelist', 'r') as f:
            for line in f:
                fileName = re.sub(r'^//.*|^#.*|\s//\s.*|\s#\s.*', '', line)
                fileName = fileName.strip()
                if not fileName:
                    continue
                if re.match(r'^\+incdir\+', fileName):
                    continue
                self.assertTrue(os.path.exists(fileName))
        
    def test_expandFilelists_otherdeliverable(self):
        '''Expand RTL filelist for all IPs except GLNPOSTPNR for ip2
        in ICManage workspace jmcgehee+zz_dm_test+ip1+9.
        
        This test depends on the actual ICManage test workspace.
        '''
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('RTL',
                                                    'testworkspace/ip1.expanded.rtl.filelist',
                                                    '/',
                                                    otherDeliverableName='GLNPOSTPNR',
                                                    otherIPs=['ip2'],
                                                    templatesetString=self._templatesetXML)
        ws = ICManageWorkspaceMock('ip1',
                                   '/test/testworkspace',
                                   hierarchy={'ip1': ['ip2'],
                                              'ip2': []})
        expander.expandAll(ws)
        
        with open('testworkspace/ip1.expanded.rtl.filelist') as f:
            actualExpanded = f.readlines()
        
        expectedExpanded = [
            "// Start files from filelist '/test/testworkspace/ip2/glnpostpnr/ip2.glnpostpnr.filelist'\n",
            "/test/testworkspace/ip2/glnpostpnr/h_gln.v\n",
            "/test/testworkspace/ip2/glnpostpnr/i_gln.v\n",
            "// End files from filelist '/test/testworkspace/ip2/glnpostpnr/ip2.glnpostpnr.filelist'\n",
            "\n",
            "// Start files from filelist '/test/testworkspace/ip1/rtl/ip1.rtl.filelist'\n",
            "+incdir+/test/testworkspace/ip1/rtl/include\n",
            "/test/testworkspace/ip1/rtl/a.v\n",
            "/test/testworkspace/ip1/rtl/b.v\n",
            "/test/testworkspace/ip1/rtl/level1/c.v\n",
            "/test/testworkspace/ip1/rtl/level2/d.v\n",
            "// End files from filelist '/test/testworkspace/ip1/rtl/ip1.rtl.filelist'\n"]
        self.assertEqual(actualExpanded, expectedExpanded)

        
    def test_expandFilelistComments(self):
        '''Check the comment parsing portion of the getFilelistLines() method.
        
        See the doctest for this method for a test of paths relative to the
        filelist.
        '''
        if os.path.exists('nonexistent.filelist'):
            shutil.rmtree('nonexistent.filelist')
        with self.assertRaises(IOError):
            dmx.dmlib.ExpandFilelist.ExpandFilelist.getFilelistLines('nonexistent.filelist')
        
        f = open('test.filelist', 'w')
        f.write('// Full line // comment\n')
        f.write('/unix/style/fileName\n')
        f.write(r'C:\windows\style\file name.txt' + '\n')
        f.write('  leading/and/trailing/spaces   \n')
        f.write('  fileName1 // trailing comment\n')
        f.write('comment/is//part of file name\n')
        f.write('      ')
        f.close()
        filelistContents = dmx.dmlib.ExpandFilelist.ExpandFilelist.getFilelistLines('test.filelist')
        self.assertEqual(filelistContents, ['/unix/style/fileName',
                                            r'C:\windows\style\file name.txt',
                                            'leading/and/trailing/spaces',
                                            'fileName1',
                                            'comment/is/part of file name'])

    def test_expandFilelistOptions(self):
        '''Test the processing of VCS options'''
        # Default working directory
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('RTL', 
                                                    'testworkspace/testsubsubip5/rtl/expanded.rtl.filelist',
                                                    templatesetString=self._templatesetXML)
        expander.expandFilelists(['testworkspace/testsubsubip5/rtl/testsubsubip5.rtl.filelist'])
        with open('testworkspace/testsubsubip5/rtl/expanded.rtl.filelist') as f:
            actualExpanded = f.readlines()
        self.assertEqual(actualExpanded, ["// Start files from filelist 'testworkspace/testsubsubip5/rtl/testsubsubip5.rtl.filelist'\n",
                                          "-anyMinusOption\n",
                                          "+anyPlusOption\n",
                                          "-f testworkspace/testsubsubip5/rtl/u.v\n",
                                          "+incdir+testworkspace/testsubsubip5/rtl/v.v\n",
                                          "testworkspace/testsubsubip5/rtl/level7/w.v\n",
                                          "-y testworkspace/testsubsubip5/rtl/level8/x.v\n",
                                          "// End files from filelist 'testworkspace/testsubsubip5/rtl/testsubsubip5.rtl.filelist'\n"])

    def test_commentOutDuplicates(self):
        '''Test the processing of duplicate files and options'''
        # Default working directory
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('RTL', 
                                                    'testworkspace/ip1/rtl/expanded.rtl.filelist',
                                                    templatesetString=self._templatesetXML)
        expander.expandFilelists(['testworkspace/ip1/rtl/ip1.rtl.filelist',
                                         'testworkspace/ip1/rtl/ip1.rtl.filelist',
                                         'testworkspace/testsubsubip5/rtl/testsubsubip5.rtl.filelist',
                                         'testworkspace/testsubsubip5/rtl/testsubsubip5.rtl.filelist'])
        with open('testworkspace/ip1/rtl/expanded.rtl.filelist') as f:
            actualExpanded = f.readlines()
        self.assertEqual(actualExpanded, ["// Start files from filelist 'testworkspace/ip1/rtl/ip1.rtl.filelist'\n",
                                          "+incdir+testworkspace/ip1/rtl/include\n",
                                          "testworkspace/ip1/rtl/a.v\n",
                                          "testworkspace/ip1/rtl/b.v\n",
                                          "testworkspace/ip1/rtl/level1/c.v\n",
                                          "testworkspace/ip1/rtl/level2/d.v\n",
                                          "// End files from filelist 'testworkspace/ip1/rtl/ip1.rtl.filelist'\n",
                                          "\n",
                                          "// Start files from filelist 'testworkspace/ip1/rtl/ip1.rtl.filelist'\n",
                                          "// duplicate +incdir+testworkspace/ip1/rtl/include\n",
                                          "// duplicate testworkspace/ip1/rtl/a.v\n",
                                          "// duplicate testworkspace/ip1/rtl/b.v\n",
                                          "// duplicate testworkspace/ip1/rtl/level1/c.v\n",
                                          "// duplicate testworkspace/ip1/rtl/level2/d.v\n",
                                          "// End files from filelist 'testworkspace/ip1/rtl/ip1.rtl.filelist'\n",
                                          "\n",
                                          "// Start files from filelist 'testworkspace/testsubsubip5/rtl/testsubsubip5.rtl.filelist'\n",
                                          "-anyMinusOption\n",
                                          "+anyPlusOption\n",
                                          "-f testworkspace/testsubsubip5/rtl/u.v\n",
                                          "+incdir+testworkspace/testsubsubip5/rtl/v.v\n",
                                          "testworkspace/testsubsubip5/rtl/level7/w.v\n",
                                          "-y testworkspace/testsubsubip5/rtl/level8/x.v\n",
                                          "// End files from filelist 'testworkspace/testsubsubip5/rtl/testsubsubip5.rtl.filelist'\n",
                                          "\n",
                                          "// Start files from filelist 'testworkspace/testsubsubip5/rtl/testsubsubip5.rtl.filelist'\n",
                                          "// duplicate -anyMinusOption\n",
                                          "// duplicate +anyPlusOption\n",
                                          "// duplicate -f testworkspace/testsubsubip5/rtl/u.v\n",
                                          "// duplicate +incdir+testworkspace/testsubsubip5/rtl/v.v\n",
                                          "// duplicate testworkspace/testsubsubip5/rtl/level7/w.v\n",
                                          "// duplicate -y testworkspace/testsubsubip5/rtl/level8/x.v\n",
                                          "// End files from filelist 'testworkspace/testsubsubip5/rtl/testsubsubip5.rtl.filelist'\n"])

    def test_missingFilelist(self):
        '''Expand a list of filelists, one of which does not exist.'''
        os.remove('testworkspace/ip3/rtl/ip3.rtl.filelist')
        expander = dmx.dmlib.ExpandFilelist.ExpandFilelist('RTL', 
                                                    'testworkspace/ip1/rtl/expanded.rtl.filelist',
                                                    templatesetString=self._templatesetXML)
        with self.assertRaises(dmError) as excp:
            expander.expandFilelists(['testworkspace/ip1/rtl/ip1.rtl.filelist',
                                      'testworkspace/ip2/rtl/ip2.rtl.filelist',
                                      'testworkspace/ip3/rtl/ip3.rtl.filelist'])
        self.assertRegexpMatches(excp.exception.message, r"Filelist '.*ip3.rtl.filelist' .* is not readable.")

    @unittest.skip ("Tests not ported to new style filelists")
    def test_expandFilelistForVp_RTL(self):
        '''Test dmx.dmlib.VpNadder.expandFilelistForVp() with .filelists and RTL'''
        os.chdir('/test/testworkspace')
        
        ws = ICManageWorkspaceMock('ip1',
                                    '/test/testworkspace',
                                    hierarchy={'ip1' : ['ip2'],
                                               'ip2' : []})
    
        vp = VpMock('ip2',
                    cell_name='cellc',
                    deliverableName='RTL',
                    ws=ws,
                    templatesetString=self._templatesetXML)
        
        filelistName = _expandFilelistForVp_TS ('RTL',
                                                vp,
                                                templatesetString=self._templatesetXML)

        with open(filelistName) as f:
            actualExpanded = f.readlines()
        
        expectedExpanded = [
            "// Start files from filelist '/test/testworkspace/ip2/rtl/ip2.rtl.filelist'\n",
            "/test/testworkspace/ip2/rtl/h.v\n",
            "/test/testworkspace/ip2/rtl/i.v\n",
            "/test/testworkspace/ip2/rtl/level3/j.v\n",
            "/test/testworkspace/ip2/rtl/level4/k.v\n",
            "// End files from filelist '/test/testworkspace/ip2/rtl/ip2.rtl.filelist'\n",
            "\n",
            "// Start files from filelist '/test/testworkspace/ip1/rtl/ip1.rtl.filelist'\n",
            "+incdir+/test/testworkspace/ip1/rtl/include\n",
            "/test/testworkspace/ip1/rtl/a.v\n",
            "/test/testworkspace/ip1/rtl/b.v\n",
            "/test/testworkspace/ip1/rtl/level1/c.v\n",
            "/test/testworkspace/ip1/rtl/level2/d.v\n",
            "// End files from filelist '/test/testworkspace/ip1/rtl/ip1.rtl.filelist'\n"]
        self.assertEqual(actualExpanded, expectedExpanded)

    @unittest.skip ("Tests not ported to new style filelists")
    def test_expandFilelistForVp_RTLLEC(self):
        '''Test dmx.dmlib.VpNadder.expandFilelistForVp() with .filelists and RTLLEC'''
        os.chdir('/test/testworkspace')
        
        ws = ICManageWorkspaceMock('ip1',
                                    '/test/testworkspace',
                                    hierarchy={'ip1': ['ip2'],
                                                'ip2': []})
    
        vp = VpMock('ip2',
                    cell_name='cellc',
                    deliverableName='RTL',
                    ws=ws,
                    templatesetString=self._templatesetXML)
        
        self.fs.CreateFile('/test/testworkspace/ip2/rtllec/h.v')
        self.fs.CreateFile('/test/testworkspace/ip1/rtllec/b.v')

        filelistName = _expandFilelistForVp_TS('RTLLEC',
                                               vp,
                                               templatesetString=self._templatesetXML)

        with open(filelistName) as f:
            actualExpanded = f.readlines()
        
        expectedExpanded = [
            "// Replaced RTL path with RTLLEC path:\n",
            "/test/testworkspace/ip2/rtllec/h.v\n",
            "/test/testworkspace/ip2/rtl/i.v\n",
            "/test/testworkspace/ip2/rtl/level3/j.v\n",
            "/test/testworkspace/ip2/rtl/level4/k.v\n",
            "+incdir+/test/testworkspace/ip1/rtl/include\n",
            "/test/testworkspace/ip1/rtl/a.v\n",
            "// Replaced RTL path with RTLLEC path:\n",
            "/test/testworkspace/ip1/rtllec/b.v\n",
            "/test/testworkspace/ip1/rtl/level1/c.v\n",
            "/test/testworkspace/ip1/rtl/level2/d.v\n"]
        self.assertEqual(actualExpanded, expectedExpanded)

    def test_expandFilelistForVp_RDF(self):
        '''Test dmx.dmlib.VpNadder.expandFilelistForVp() with .filelists and RDF'''
        os.chdir('/test/testworkspace')
    
        self.fs.CreateFile('/test/testworkspace/ip2/rtllec/h.v')
        self.fs.CreateFile('/test/testworkspace/ip1/rtllec/b.v')
        
        ws = ICManageWorkspaceMock('ip1',
                                   '/test/testworkspace',
                                   hierarchy={'ip1': ['ip2'],
                                              'ip2': []})

        vp = VpMock('ip2',
                    cell_name='cellc',
                    deliverableName='RDF',
                    ws=ws,
                    templatesetString=self._templatesetXML)

        filelistName = _expandFilelistForVp_TS ('RDF',
                                                vp,
                                                templatesetString=self._templatesetXML)

        with open(filelistName) as f:
            actualExpanded = f.readlines()
            
#        print actualExpanded
#            
#        
#        expectedExpanded = [
#            "// Start files from filelist '/test/testworkspace/ip2/rdf/ip2.rdf.filelist'\n",
#            "/test/testworkspace/ip2/rdf/ip2a.rdf.xlsx\n",
#            "/test/testworkspace/ip2/rdf/ip2b.rdf.xlsx\n",
#            "// End files from filelist '/test/testworkspace/ip2/rdf/ip2.rdf.filelist'\n",
#            "\n",
#            "// Start files from filelist '/test/testworkspace/ip1/rdf/ip1.rdf.filelist'\n",
#            "/test/testworkspace/ip1/rdf/ip1.rdf.xlsx\n",
#            "// End files from filelist '/test/testworkspace/ip1/rdf/ip1.rdf.filelist'\n"]

        expectedExpanded = [
            "// Start files from filelist '/test/testworkspace/ip2/rdf/ip2.rdf.filelist'\n",
            "/test/testworkspace/ip2/rdf/ip2a.rdf.xlsx\n",
            "/test/testworkspace/ip2/rdf/ip2b.rdf.xlsx\n",
            "// End files from filelist '/test/testworkspace/ip2/rdf/ip2.rdf.filelist'\n"]
        self.assertEqual(actualExpanded, expectedExpanded)


if __name__ == "__main__":
    unittest.main()
