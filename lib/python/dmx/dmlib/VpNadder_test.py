#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011-2015 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/VpNadder_test.py#1 $

"""
Test the VpNadder class. Most of the tests are performed using doctest
via the doctest-unittest interface.
"""


import os
import glob
import unittest
import doctest
import shutil
import dmx.dmlib.VpNadder


from dmx.dmlib.templateset.verifier import Verifier
from dmx.dmlib.Manifest import Manifest

# pylint: disable=W0212

# Root directory for the entire project:
_dmRoot = os.path.dirname(os.path.dirname(__file__))
manifestSetFileName = os.path.join (_dmRoot, 
                                   'dm/deliverables_test/exampleManifestSetDataCheck.xml')

skipMostTests = False

def load_tests(loader, tests, ignore): # pylint: disable=W0613
    '''Load the VpNadder.py doctest tests into unittest.'''
    # pylint: disable=W0613
    tests.addTests(doctest.DocTestSuite(dmx.dmlib.VpNadder))
    return tests


#@unittest.skipIf (skipMostTests, 'skipMostTests')
class TestVp(unittest.TestCase): # pylint: disable=R0904
    """Test the VpNadder class."""

    _expectedChecksForCHECKDATA_GOOD1 = (
        "'CHECKDATA_GOOD1' type check for cell 'testip1'",
        "'CHECKDATA_GOOD1' data check for cell 'testip1'")
     

    def setUp(self):
        _abscurdir = os.path.abspath(os.curdir)
        assert os.path.basename(_abscurdir) == 'test', "Test should run in test/"

        reload(dmx.dmlib.VpNadder)
        os.chdir(self._abscurdir)
        assert os.path.basename(os.path.abspath(os.curdir)) == 'test', \
                   "Test should start in 'test/'"
        
        self._cleanUp()

        # The *.xunit.xml files should be in testip1/vpout/testip1/*.xunit.xml,
        # but delete them from ./ just in case.
        for xunitFileName in glob.glob('*.xunit.xml'):
            os.remove(xunitFileName)

        self._createTestFile('.icmconfig')
        self._createTestFile('testip1/icc/CHECKDATA_GOOD1.txt')
        self._createTestFile('testip1/icc/CHECKDATA_GOOD2.txt')
        self._createTestFile('testip1/icc/CHECKDATA_BAD.txt')
        self._createTestFile('testip1/icc/EXAMPLE1.txt',
                             contents=['Supercalifragilisticexpialidocious'])
        self._createTestFile('testip1/icc/EXAMPLE2.txt',
                             contents=['Supercalifragilisticexpialidocious'])
    
        self._templatesetString = '''<?xml version="1.0" encoding="utf-8"?>
            <templateset>

              <template caseid="100" id="EMPTY1">
                <description>
                  No checks whatsoever defined.
                </description>
              </template>
              
              <template caseid="101" id="CHECKDATA_GOOD1">
                <description>
                  Data and predecessor checks will pass.
                </description>
                <pattern id="file">
                  testip1/icc/CHECKDATA_GOOD1.txt
                </pattern>
              </template>
              
              <template caseid="102" id="CHECKDATA_GOOD2">
                <description>
                  Data check passes, but predecessor check will fail.
                </description>
                <pattern id="file">
                  testip1/icc/CHECKDATA_GOOD2.txt
                </pattern>
              </template>
              
              <template caseid="103" id="CHECKDATA_BAD">
                <description>
                  Data check will fail, but predecessor checks will pass
                </description>
                <pattern id="file">
                  testip1/icc/CHECKDATA_BAD.txt
                </pattern>
              </template>
              
              <template caseid="104" id="PREDECESSOR_GOOD1">
                <description>
                  Good predecessor.
                </description>
                <pattern id="file">
                  testip1/icc/PREDECESSOR_GOOD1.txt
                </pattern>
              </template>
              <template caseid="105" id="PREDECESSOR_GOOD2">
                <description>
                  Good predecessor.
                </description>
                <pattern id="file">
                  testip1/icc/PREDECESSOR_GOOD2.txt
                </pattern>
              </template>
              <template caseid="106" id="PREDECESSOR_BAD">
                <description>
                  Bad predecessor.
                </description>
                <pattern id="file">
                  testip1/icc/PREDECESSOR_BAD.txt
                </pattern>
              </template>
              
              <alias id="ALL">
                <member>CHECKDATA_GOOD1</member>
                <member>CHECKDATA_GOOD2</member>
                <member>CHECKDATA_BAD</member>
                <member>PREDECESSOR_GOOD1</member>
                <member>PREDECESSOR_GOOD2</member>
                <member>PREDECESSOR_BAD</member>
              </alias>
                              
              <alias id="SOME">
                <member>CHECKDATA_GOOD1</member>
                <member>CHECKDATA_GOOD2</member>
                <member>CHECKDATA_BAD</member>
              </alias>
                              
              <successor id="CHECKDATA_GOOD1">
                <predecessor>PREDECESSOR_GOOD1</predecessor>
                <predecessor>PREDECESSOR_GOOD2</predecessor>
              </successor>
              <successor id="CHECKDATA_GOOD2">
                <predecessor>PREDECESSOR_GOOD1</predecessor>
                <predecessor>PREDECESSOR_BAD</predecessor>
              </successor>
              <successor id="CHECKDATA_BAD">
                <predecessor>PREDECESSOR_GOOD1</predecessor>
                <predecessor>PREDECESSOR_GOOD2</predecessor>
              </successor>
              
              <template caseid="107" id="VPOUT">
                <description>
                  Verification Platform (VP) results.
                </description>
                <pattern id="report">
                  &ip_name;/vpout/PerformedChecksReport.txt
                </pattern>
                <pattern id="xunit">
                  &ip_name;/vpout/&cell_name;/&deliverable_name;.xunit.xml
                </pattern>
              </template>
              <successor id="VPOUT"/>
            </templateset>'''
        self._manifest = Manifest('testip1', templatesetString=self._templatesetString)

        if os.path.exists('testip2'):
            shutil.rmtree('testip2')

        self._createTestFile('.icmconfig')
        self._createTestFile('testip2/icc/cella.multi.txt')
        self._createTestFile('testip2/icc/cellb.multi.txt')
        self._createTestFile('testip2/icc/testip2.multi.txt')
        self._createTestFile('testip2/ipspec/cell_names.txt',
                             contents=['cella', 'cellb', 'testip2'])
        self._multiCellTemplatesetString = '''<?xml version="1.0" encoding="utf-8"?>
            <templateset>
              <template caseid="100" id="MULTI">
                <description>
                  Good predecessor.
                </description>
                <pattern id="file">
                  &ip_name;/icc/&cell_name;.multi.txt
                </pattern>
              </template>
              <successor id="MULTI"/>
              <template caseid="101" id="IPSPEC">
                <description>
                  Good predecessor.
                </description>
                <pattern id="cell_names" minimum="0">
                  &ip_name;/ipspec/cell_names.txt
                </pattern>
              </template>
              <successor id="IPSPEC"/>
              
              <template caseid="84746" id="VPOUT">
                <description>
                  Verification Platform (VP) results.
                </description>
                <pattern id="report">
                  &ip_name;/vpout/PerformedChecksReport.txt
                </pattern>
                <pattern id="xunit">
                  &ip_name;/vpout/&cell_name;/&deliverable_name;.xunit.xml
                </pattern>
              </template>
              <successor id="VPOUT"/>
          </templateset>'''

        
    def tearDown(self):
        self._cleanUp()

    def _cleanUp(self):
        '''Clean up files.'''
        
        vp02OutPath = '/ice_da/infra/icm/workspace/VP_ws/rgetov.zz_dm_test.vp02.6857/vp02/vpout'
        if os.path.exists(vp02OutPath):
            #assert False
            shutil.rmtree(vp02OutPath)
            
        testip1Path = os.path.join(self._abscurdir, 'testip1')
        if os.path.exists(testip1Path):
            shutil.rmtree(testip1Path)
            
        icmconfigPath = os.path.join(self._abscurdir, '.icmconfig')
        if os.path.exists(icmconfigPath):
            os.remove(icmconfigPath)

    @classmethod
    def _createTestFile(cls, fileName, contents=('')):
        '''Create the specified test file.
        Add the specified contents to the file, one per line.
        '''
        dirName = os.path.dirname(fileName)
        if dirName and not os.path.exists(dirName):
            os.makedirs(dirName)
        f = open(fileName, 'w')
        for content in contents:
            f.write(content)
            f.write('\n')
        f.close()


    # Leading "0" causes empty test to run first.
    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_00_verifyTestTemplatesets(self):
        '''Check that the test templateset is valid'''
        self.assertTrue(Verifier(self._templatesetString).isCorrect,
                        'The test templateset is correct.')
        self.assertTrue(Verifier(self._multiCellTemplatesetString).isCorrect,
                        'The multi cell test templateset is correct.')

    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_01_empty(self):
        '''Test what happens when you do nothing'''
        vp = dmx.dmlib.VpNadder.VpNadder (ip_name = 'testip1', 
                                   noICManage=True, 
                                   deliverableCheckModule='dmx.dmlib.deliverables_test')
        self.assertEqual(vp.checkOneDeliverableInOneCell(self._manifest, 
                                                         'EMPTY1', 
                                                         dmx.dmlib.VpNadder.allCheckKinds), 
                        dmx.dmlib.VpNadder.VpNadder.successStatus)
        self.assertEqual(vp.checksPerformed, ["'EMPTY1' type check for cell 'testip1'"])
        self.assertTrue(os.path.exists('testip1/vpout/testip1/EMPTY1.xunit.xml'))

    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_02_exitStatus(self):
        '''Test exit status values'''
        self.assertEqual(dmx.dmlib.VpNadder.VpNadder.successStatus, 0)
        self.assertEqual(dmx.dmlib.VpNadder.VpNadder.generalFailStatus, 1)
        self.assertEqual(dmx.dmlib.VpNadder.VpNadder.dataCheckFailStatus, 2)
        self.assertEqual(dmx.dmlib.VpNadder.VpNadder.predecessorCheckFailStatus, 3)
        self.assertEqual(dmx.dmlib.VpNadder.VpNadder.successorCheckFailStatus, 4)
        self.assertEqual(dmx.dmlib.VpNadder.VpNadder.typeCheckFailStatus, 5)
        self.assertEqual(dmx.dmlib.VpNadder.VpNadder.argumentErrorStatus, 126)
        self.assertEqual(dmx.dmlib.VpNadder.VpNadder.multipleDeliverableFailStatus, 127)
        self.assertEqual(len(dmx.dmlib.VpNadder.VpNadder.statusMessage), 7)


    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_03_hasNewStyleFilelist(self):
        '''Test the _hasNewStyleFilelist() function'''
        templatesetXML = '''<?xml version="1.0" encoding="utf-8"?>
         <templateset>
            <template caseid="24166" id="RTL">
               <description>
                 Has the new style filelist.
               </description>
               <filelist id="filelist" minimum="0">
                 &ip_name;/rtl/&ip_name;.rtl.filelist
               </filelist>
               <filelist id="cell_filelist" minimum="0">
                 &ip_name;/rtl/filelist/&cell_name;.f
               </filelist>
             </template>
            <template caseid="24166" id="OLDRTL">
               <description>
                 Does not have the new style filelist.
               </description>
               <filelist id="filelist">
                 &ip_name;/oldrtl/&ip_name;.oldrtl.filelist
               </filelist>
             </template>
        </templateset>'''
        manifest = Manifest('testip1', templatesetString=templatesetXML)
        self.assertFalse(dmx.dmlib.VpNadder._hasNewStyleFilelist('RTL', manifest))
        self._createTestFile('testip1/rtl/testip1.rtl.filelist')
        self.assertFalse(dmx.dmlib.VpNadder._hasNewStyleFilelist('RTL', manifest))
        self._createTestFile('testip1/rtl/filelist/testip1.f')
        self.assertTrue(dmx.dmlib.VpNadder._hasNewStyleFilelist('RTL', manifest))
        
        # OLDRTL never has a new style .f filelist
        self._createTestFile('testip1/oldrtl/testip1.oldrtl.filelist')
        self._createTestFile('testip1/oldrtl/filelist/testip1.f')
        self.assertFalse(dmx.dmlib.VpNadder._hasNewStyleFilelist('OLDRTL', manifest))

    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def SKIP_test_workspaceDirName(self): 
        '''Test the retreival of the path to the top of the workspace'''
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'vp02',
                                  doOnlyTypeCheck='True',
                                  workspaceDirName='/ice_da/infra/icm/workspace/VP_ws/rgetov.zz_dm_test.vp02.6857')
        self.assertEqual(vp.workspaceDirName, '/ice_da/infra/icm/workspace/VP_ws/rgetov.zz_dm_test.vp02.6857')
                
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'vp02', 
                                  doOnlyTypeCheck='True',
                                  workspaceDirName='/ice_da/infra/icm/workspace/VP_ws/rgetov.zz_dm_test.vp02.6857/vp02')
        self.assertEqual(vp.workspaceDirName, '/ice_da/infra/icm/workspace/VP_ws/rgetov.zz_dm_test.vp02.6857')
                
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'vp02', 
                                  doOnlyTypeCheck='True',
                                  workspaceDirName='/ice_da/infra/icm/workspace/VP_ws/rgetov.zz_dm_test.vp02.6857/vp02')
        self.assertEqual(vp.workspaceDirName, '/ice_da/infra/icm/workspace/VP_ws/rgetov.zz_dm_test.vp02.6857')        


    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_05_getLogDirName(self):
        '''Test the getLogDirName() method.'''
        # Test the pure class method behavior before instantiating VP
        self.assertEqual(dmx.dmlib.VpNadder.VpNadder.getLogDirName('testip1', 'cellx'),
                         os.path.join('testip1', 'vpout', 'cellx'))
        
        vp = dmx.dmlib.VpNadder.VpNadder (ip_name = 'testip2', 
                                   noICManage = True,
                                   workspaceDirName = None)
        manifest = Manifest('testip2', 'cella', self._multiCellTemplatesetString)
        # Run a check just to set the cell name--we don't care what the result of the check is
        vp.checkOneDeliverableInOneCell(manifest, 'MULTI')
        self.assertEqual(dmx.dmlib.VpNadder.VpNadder.getLogDirName(),
                         os.path.join('testip2', 'vpout', 'cella'))
        self.assertEqual(dmx.dmlib.VpNadder.VpNadder.getLogDirName(cell_name='cellz'),
                         os.path.join('testip2', 'vpout', 'cellz'))
        
        # Test the pure class method behavior after instantiating VP
        self.assertEqual(dmx.dmlib.VpNadder.VpNadder.getLogDirName('testip3', 'cell1'),
                         os.path.join('testip3', 'vpout', 'cell1'))

    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_06_getXUnitFileName(self):
        '''Test the getXUnitFileName() method.'''
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name    = 'testip2', 
                                  noICManage =True)
        manifest = Manifest('testip2', 'cella', self._multiCellTemplatesetString)
        # Run a check just to set the cell name--we don't care what the result of the check is
        vp.checkOneDeliverableInOneCell(manifest, 'MULTI')
        self.assertTrue(os.path.samefile(dmx.dmlib.VpNadder.VpNadder.getXUnitFileName('MULTI'),
                                          os.path.join('testip2', 'vpout', 'cella', 'MULTI.xunit.xml')))
        self.assertEqual(dmx.dmlib.VpNadder.VpNadder.getXUnitFileName('MULTI', cell_name='cellz'),
                         os.path.join('testip2', 'vpout', 'cellz', 'MULTI.xunit.xml'))

    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_07_getReportFileName(self):
        '''Test the getReportFileName() method.'''
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip2', 
                                  noICManage=True)
        manifest = Manifest('testip2', 'cella', self._multiCellTemplatesetString)
        # Run a check just to set the cell name--we don't care what the result of the check is
        vp.checkOneDeliverableInOneCell(manifest, 'MULTI')
        self.assertEqual(dmx.dmlib.VpNadder.VpNadder.getReportFileName(),
                         os.path.join('testip2', 'vpout', 'PerformedChecksReport.txt'))

    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_08_checkType(self):
        '''Test the VP type check.'''
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test')
        actualStatus = vp.checkOneDeliverableInOneCell(self._manifest, 'CHECKDATA_GOOD1')
        self.assertEqual(actualStatus, dmx.dmlib.VpNadder.VpNadder.successStatus)
        self.assertItemsEqual(vp.checksPerformed, ["'CHECKDATA_GOOD1' type check for cell 'testip1'",
                                                   "'CHECKDATA_GOOD1' data check for cell 'testip1'"])

        os.remove('testip1/icc/CHECKDATA_GOOD1.txt')
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test')
        self.assertEqual(vp.checkOneDeliverableInOneCell(self._manifest, 'CHECKDATA_GOOD1'), 
                         dmx.dmlib.VpNadder.VpNadder.typeCheckFailStatus)
        self.assertEqual(vp.checksPerformed, ["'CHECKDATA_GOOD1' type check for cell 'testip1'"])
        self.assertEqual(len(vp.result.failures), 1)
        self.assertEqual(len(vp.result.errors), 0)
        self.assertTrue(os.path.exists('testip1/vpout/testip1/CHECKDATA_GOOD1.xunit.xml'))

    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_09_checkData(self):
        '''Test the VP data check.'''
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test')
        self.assertEqual(vp.checkOneDeliverableInOneCell(self._manifest, 
                                                         'CHECKDATA_GOOD1'), 
                                                         dmx.dmlib.VpNadder.VpNadder.successStatus)
        self.assertItemsEqual(vp.checksPerformed, self._expectedChecksForCHECKDATA_GOOD1)
        self.assertTrue(os.path.exists('testip1/vpout/testip1/CHECKDATA_GOOD1.xunit.xml'))
        
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test')
        self.assertEqual(vp.checkOneDeliverableInOneCell(self._manifest, 'CHECKDATA_BAD'), 
                         dmx.dmlib.VpNadder.VpNadder.dataCheckFailStatus)
        self.assertEqual(vp.checksPerformed, ["'CHECKDATA_BAD' type check for cell 'testip1'",
                                              "'CHECKDATA_BAD' data check for cell 'testip1'"])
        self.assertEqual(len(vp.result.failures), 1)
        self.assertEqual(len(vp.result.errors), 0)
        self.assertTrue(os.path.exists('testip1/vpout/testip1/CHECKDATA_BAD.xunit.xml'))
        
 
    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_10_doOnlyTypeCheck(self):
        '''Test the VP doOnlyTypeCheck option.'''
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test')
        self.assertEqual(vp.checkOneDeliverableInOneCell(self._manifest, 'CHECKDATA_GOOD1'), 
                         dmx.dmlib.VpNadder.VpNadder.successStatus)
        self.assertItemsEqual(vp.checksPerformed, self._expectedChecksForCHECKDATA_GOOD1)
       
        # Data check failure ignored
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test', 
                                  doOnlyTypeCheck=True)
        self.assertEqual(vp.checkOneDeliverableInOneCell(self._manifest, 'CHECKDATA_BAD'),
                         dmx.dmlib.VpNadder.VpNadder.successStatus, 'Failure in data check ignored')
        self.assertItemsEqual(vp.checksPerformed, ["'CHECKDATA_BAD' type check for cell 'testip1'"])
        
        # Context check failure ignored
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test', 
                                  doOnlyTypeCheck=True)
        self.assertEqual(vp.checkOneDeliverableInOneCell(self._manifest, 'CHECKDATA_GOOD2'),
                         dmx.dmlib.VpNadder.VpNadder.successStatus, 
                         'Failure in context check ignored')
        self.assertItemsEqual(vp.checksPerformed, 
                              ["'CHECKDATA_GOOD2' type check for cell 'testip1'"])
        os.remove('testip1/icc/CHECKDATA_GOOD1.txt')

        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test', 
                                  doOnlyTypeCheck=True)
        self.assertEqual(vp.checkOneDeliverableInOneCell(self._manifest, 'CHECKDATA_GOOD1'),
                         dmx.dmlib.VpNadder.VpNadder.typeCheckFailStatus, 
                         'Failure in type check detected')
        self.assertItemsEqual(vp.checksPerformed, 
                              ["'CHECKDATA_GOOD1' type check for cell 'testip1'"])
        self.assertEqual(len(vp.result.failures), 1)
        self.assertEqual(len(vp.result.errors), 0)
        self.assertTrue(os.path.exists('testip1/vpout/testip1/CHECKDATA_GOOD1.xunit.xml'))

    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_11_doOnlyDataCheck(self):
        '''Test the VP doOnlyDataCheck option.'''
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test')
        self.assertEqual(vp.checkOneDeliverableInOneCell(self._manifest, 'CHECKDATA_GOOD1'), 
                         dmx.dmlib.VpNadder.VpNadder.successStatus)
        self.assertItemsEqual(vp.checksPerformed, self._expectedChecksForCHECKDATA_GOOD1)
        
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test', 
                                  doOnlyDataCheck=True)
        os.remove('testip1/icc/CHECKDATA_GOOD1.txt')
        self.assertEqual(vp.checkOneDeliverableInOneCell(self._manifest, 'CHECKDATA_GOOD1'),
                         dmx.dmlib.VpNadder.VpNadder.successStatus, 'Failure in type check ignored')
        self.assertItemsEqual(vp.checksPerformed, ["'CHECKDATA_GOOD1' data check for cell 'testip1'"])
        self._createTestFile('testip1/icc/CHECKDATA_GOOD1.txt')

        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test', 
                                  doOnlyDataCheck=True)
        self.assertEqual(vp.checkOneDeliverableInOneCell(self._manifest, 'CHECKDATA_GOOD2'),
                         dmx.dmlib.VpNadder.VpNadder.successStatus, 'Failure in context check ignored')
        self.assertItemsEqual(vp.checksPerformed, ["'CHECKDATA_GOOD2' data check for cell 'testip1'"])

        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test', 
                                  doOnlyDataCheck=True)
        self.assertEqual(vp.checkOneDeliverableInOneCell(self._manifest, 'CHECKDATA_BAD'),
                         dmx.dmlib.VpNadder.VpNadder.dataCheckFailStatus, 'Failure in type check detected')
        self.assertItemsEqual(vp.checksPerformed, ["'CHECKDATA_BAD' data check for cell 'testip1'"])
        self.assertEqual(len(vp.result.failures), 1)
        self.assertEqual(len(vp.result.errors), 0)
        self.assertTrue(os.path.exists('testip1/vpout/testip1/CHECKDATA_BAD.xunit.xml'))

    
    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_12_getCellNames(self):
        '''Make sure VP reads the IPSPEC cell_names file correctly.'''
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip2', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test')
        self.assertItemsEqual(vp._getCellNames('testip2'),
                              ['cella', 'cellb', 'testip2'])
        # No cell_name file
        os.remove('testip2/ipspec/cell_names.txt')
        self.assertItemsEqual(vp._getCellNames('testip2'), ['testip2'])
        # Empty cell_name file
        self._createTestFile('testip2/ipspec/cell_names.txt')
        self.assertItemsEqual(vp._getCellNames('testip2'), ['testip2'])
        

    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_13_multipleCells(self):
        '''Make sure VP checks multiple cells in one IP.'''
        
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip2', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test')
        self.assertEqual(vp.check(['MULTI'], templatesetString=self._multiCellTemplatesetString), 
                         dmx.dmlib.VpNadder.VpNadder.successStatus)
        self.assertItemsEqual(vp.checksPerformed, ["'MULTI' type check for cell 'cella'",
                                                   "'MULTI' type check for cell 'cellb'",
                                                   "'MULTI' type check for cell 'testip2'"])
  
        self._createTestFile('testip2/ipspec/cell_names.txt',
                             contents=['cella', 'nonexistent'])
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip2', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test')
        self.assertEqual(vp.check(['MULTI'], templatesetString=self._multiCellTemplatesetString), 
                         dmx.dmlib.VpNadder.VpNadder.multipleDeliverableFailStatus)
        self.assertItemsEqual(vp.checksPerformed, ["'MULTI' type check for cell 'cella'",
                                                   "'MULTI' type check for cell 'nonexistent'"])
  
        os.remove('testip2/ipspec/cell_names.txt')
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip2', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test')
        self.assertEqual(vp.check(['MULTI'], templatesetString=self._multiCellTemplatesetString), 
                         dmx.dmlib.VpNadder.VpNadder.successStatus)
        self.assertItemsEqual(vp.checksPerformed, ["'MULTI' type check for cell 'testip2'"])
  

        
        
    #####################################################################
    # Test the examples in the vp.py developer documentation.
    # Test only the documentation examples below.  Add functional tests above.
    #####################################################################
    
    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_14_exampleManifestSetDataCheckXML(self):
        '''Test manifestset file exampleManifestSetDataCheck.xml.
        Test only the documentation example in this `test_*()` method.
        '''

        # Set up VpNadder
        #dmRoot = os.path.dirname(os.path.dirname(__file__))
        #manifestSetFileName = os.path.join(dmRoot, 'dm/deliverables_test/exampleManifestSetDataCheck.xml')
        mf = open(manifestSetFileName)
        verifier = Verifier(mf.read())
        mf.close()
        self.assertTrue(verifier.isCorrect,
                        'The exampleManifestSetDataCheck.xml test manifestset is correct.')
        
    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_15_example1CheckType(self):
        '''Test vp documentation EXAMPLE1 data check.
        Test only the documentation example in this `test_*()` method.
        '''
        # Set up VpNadder
        #dmRoot = os.path.dirname(os.path.dirname(__file__))
        #manifestSetFileName = os.path.join(dmRoot, 'dm/deliverables_test/exampleManifestSetDataCheck.xml')
        mf = open(manifestSetFileName)
        manifest = Manifest('testip1', templatesetString=mf.read())
        mf.close()
        
        # Correct EXAMPLE1.txt files
        # EXAMPLE2.txt also has to be changed to match so that the precedence check does not fail
        self._createTestFile('testip1/icc/EXAMPLE1.txt', contents=['supercalifragilisticexpialidocious'])
        self._createTestFile('testip1/icc/EXAMPLE2.txt', contents=['supercalifragilisticexpialidocious'])
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test')
        ret = vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE1'); _ = ret
        #self.assertEqual(ret, dmx.dmlib.VpNadder.VpNadder.successStatus)
        
        self._createTestFile('testip1/icc/EXAMPLE1.txt', contents=['Supercalifragilisticexpialidocious'])
        self._createTestFile('testip1/icc/EXAMPLE2.txt', contents=['Supercalifragilisticexpialidocious'])
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test')
        #self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE1'), dmx.dmlib.VpNadder.VpNadder.successStatus)
        
        self._createTestFile('testip1/icc/EXAMPLE1.txt', contents=['SUPERCALIFRAGILISTICEXPIALIDOCIOUS'])
        self._createTestFile('testip1/icc/EXAMPLE2.txt', contents=['SUPERCALIFRAGILISTICEXPIALIDOCIOUS'])
        vp = dmx.dmlib.VpNadder.VpNadder(ip_name = 'testip1', 
                                  noICManage=True, 
                                  deliverableCheckModule='dmx.dmlib.deliverables_test')
        #self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE1'), dmx.dmlib.VpNadder.VpNadder.successStatus)

        self.assertTrue(os.path.exists('testip1/vpout/testip1/EXAMPLE1.xunit.xml'))
        
        # Erroneous EXAMPLE1 file - SKIPPED UNTIL DATA CHECKS ARE RESURRECTED
#        self._createTestFile('testip1/icc/EXAMPLE1.txt', contents=['Not correct'])
#        self._createTestFile('testip1/icc/EXAMPLE2.txt', contents=['Not correct'])
#        vp = dmx.dmlib.VpNadder.VpNadder('testip1', 'ALL', noICManage=True, deliverableCheckModule='dmx.dmlib.deliverables_test')
#        self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE1'), dmx.dmlib.VpNadder.VpNadder.dataCheckFailStatus)
#
#        self.assertTrue(os.path.exists('testip1/vpout/testip1/EXAMPLE1.xunit.xml'))
        
    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def TO_DO_test_example2CheckType(self):
        '''Test vp documentation EXAMPLE2 data check.
        Test only the documentation example in this `test_*()` method.
        
        (Temporary off until data checks are resurrected)
        '''
        # Set up VpNadder
        #dmRoot = os.path.dirname(os.path.dirname(__file__))
        #manifestSetFileName = os.path.join(dmRoot, 'dm/deliverables_test/exampleManifestSetDataCheck.xml')
        mf = open(manifestSetFileName)
        manifest = Manifest('testip1', templatesetString=mf.read())
        mf.close()
        
        # Correct EXAMPLE2.txt files
        # EXAMPLE1.txt also has to be changed to match so that the precedence check does not fail
        self._createTestFile('testip1/icc/EXAMPLE1.txt', contents=['supercalifragilisticexpialidocious'])
        self._createTestFile('testip1/icc/EXAMPLE2.txt', contents=['supercalifragilisticexpialidocious'])
        vp = dmx.dmlib.VpNadder.VpNadder('testip1', 'ALL', noICManage=True, deliverableCheckModule='dmx.dmlib.deliverables_test', doOnlyDataCheck=True)
        self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE2'), dmx.dmlib.VpNadder.VpNadder.successStatus)
        
        self._createTestFile('testip1/icc/EXAMPLE1.txt', contents=['Supercalifragilisticexpialidocious'])
        self._createTestFile('testip1/icc/EXAMPLE2.txt', contents=['Supercalifragilisticexpialidocious'])
        vp = dmx.dmlib.VpNadder.VpNadder('testip1', 'ALL', noICManage=True, deliverableCheckModule='dmx.dmlib.deliverables_test')
        self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE2'), dmx.dmlib.VpNadder.VpNadder.successStatus)
        
        self._createTestFile('testip1/icc/EXAMPLE1.txt', contents=['SUPERCALIFRAGILISTICEXPIALIDOCIOUS'])
        self._createTestFile('testip1/icc/EXAMPLE2.txt', contents=['SUPERCALIFRAGILISTICEXPIALIDOCIOUS'])
        vp = dmx.dmlib.VpNadder.VpNadder('testip1', 'ALL', noICManage=True, deliverableCheckModule='dmx.dmlib.deliverables_test')
        self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE2'), dmx.dmlib.VpNadder.VpNadder.successStatus)

        self.assertTrue(os.path.exists('testip1/vpout/testip1/EXAMPLE2.xunit.xml'))
        
        # Erroneous EXAMPLE2 file
        self._createTestFile('testip1/icc/EXAMPLE1.txt', contents=['Not correct'])
        self._createTestFile('testip1/icc/EXAMPLE2.txt', contents=['Not correct'])
        vp = dmx.dmlib.VpNadder.VpNadder('testip1', 'ALL', noICManage=True, deliverableCheckModule='dmx.dmlib.deliverables_test')
        self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE2'), dmx.dmlib.VpNadder.VpNadder.dataCheckFailStatus)

        self.assertTrue(os.path.exists('testip1/vpout/testip1/EXAMPLE2.xunit.xml'))
        
#    @unittest.skipIf (skipMostTests, 'skipMostTests')
#    def FAILS_test_example2CheckVsEXAMPLE1(self):
#        '''Test vp documentation predecessor check.
#        Test only the documentation example in this `test_*()` method.
#        '''
#        # Set up VpNadder 
#        # No Methodics workspace for this test
#        if os.path.exists('.methodics'):
#            shutil.rmtree('.methodics')
#
#        #dmRoot = os.path.dirname(os.path.dirname(__file__))
#        #manifestSetFileName = os.path.join(dmRoot, 'dm/deliverables_test/exampleManifestSetDataCheck.xml')
#        mf = open(manifestSetFileName)
#        manifest = Manifest('testip1', templatesetString=mf.read())
#        mf.close()
#        
#        # Matching files
#        self._createTestFile('testip1/icc/EXAMPLE1.txt', contents=['supercalifragilisticexpialidocious'])
#        self._createTestFile('testip1/icc/EXAMPLE2.txt', contents=['supercalifragilisticexpialidocious'])
#        vp = dmx.dmlib.VpNadder.VpNadder('testip1', 'ALL', noICManage=True, deliverableCheckModule='dmx.dmlib.deliverables_test')
#        self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE2'), dmx.dmlib.VpNadder.VpNadder.successStatus)
#        
#        self._createTestFile('testip1/icc/EXAMPLE1.txt', contents=['Supercalifragilisticexpialidocious'])
#        self._createTestFile('testip1/icc/EXAMPLE2.txt', contents=['Supercalifragilisticexpialidocious'])
#        vp = dmx.dmlib.VpNadder.VpNadder('testip1', 'ALL', noICManage=True, deliverableCheckModule='dmx.dmlib.deliverables_test')
#        self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE2'), dmx.dmlib.VpNadder.VpNadder.successStatus)
#        
#        self._createTestFile('testip1/icc/EXAMPLE1.txt', contents=['SUPERCALIFRAGILISTICEXPIALIDOCIOUS'])
#        self._createTestFile('testip1/icc/EXAMPLE2.txt', contents=['SUPERCALIFRAGILISTICEXPIALIDOCIOUS'])
#        vp = dmx.dmlib.VpNadder.VpNadder('testip1', 'ALL', noICManage=True, deliverableCheckModule='dmx.dmlib.deliverables_test')
#        self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE2'), dmx.dmlib.VpNadder.VpNadder.successStatus)
#
#        self.assertTrue(os.path.exists('testip1/vpout/testip1/EXAMPLE2.xunit.xml'))
#        
#        # File do not match
#        self._createTestFile('testip1/icc/EXAMPLE1.txt', contents=['Supercalifragilisticexpialidocious'])
#        self._createTestFile('testip1/icc/EXAMPLE2.txt', contents=['SUPERCALIFRAGILISTICEXPIALIDOCIOUS'])
#        # There is no IC Manage  workspace, so all deliverables in exampleManifestSetDataCheck.xml are presumed connected
#        vp = dmx.dmlib.VpNadder.VpNadder('testip1', 'ALL', noICManage=True, deliverableCheckModule='dmx.dmlib.deliverables_test')
#        self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE2'), dmx.dmlib.VpNadder.VpNadder.predecessorCheckFailStatus)
#
#        self.assertTrue(os.path.exists('testip1/vpout/testip1/EXAMPLE2.xunit.xml'))
        
#    #@unittest.skipIf (skipMostTests, 'skipMostTests')
#    def FAILS_test_example2CheckVsEXAMPLE1_typeCheckOtherDeliverable(self):
#        '''Test vp documentation predecessor check.
#        Test only the documentation example in this `test_*()` method.
#        '''
#        # Set up VpNadder
#        #dmRoot = os.path.dirname(os.path.dirname(__file__))
#        #manifestSetFileName = os.path.join(dmRoot, 'dm/deliverables_test/exampleManifestSetDataCheck.xml')
#        mf = open(manifestSetFileName)
#        manifest = Manifest('testip1', templatesetString=mf.read())
#        mf.close()
#        
#        # Matching files
#        self._createTestFile('testip1/icc/EXAMPLE1.txt', contents=['supercalifragilisticexpialidocious'])
#        self._createTestFile('testip1/icc/EXAMPLE2.txt', contents=['supercalifragilisticexpialidocious'])
#        vp = dmx.dmlib.VpNadder.VpNadder('testip1', 'ALL', noICManage=True, deliverableCheckModule='dmx.dmlib.deliverables_test', onlyContextCheck='EXAMPLE1')
#        self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE2'), dmx.dmlib.VpNadder.VpNadder.successStatus)
#        vp = dmx.dmlib.VpNadder.VpNadder('testip1', 'ALL', noICManage=True, deliverableCheckModule='dmx.dmlib.deliverables_test', onlyContextCheck='EXAMPLE2')
#        self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE1'), dmx.dmlib.VpNadder.VpNadder.successStatus)
#        
#        os.remove('testip1/icc/EXAMPLE1.txt')
#        vp = dmx.dmlib.VpNadder.VpNadder('testip1', 'ALL', noICManage=True, deliverableCheckModule='dmx.dmlib.deliverables_test', onlyContextCheck='EXAMPLE1')
#        self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE2'), dmx.dmlib.VpNadder.VpNadder.predecessorCheckFailStatus)
#        vp = dmx.dmlib.VpNadder.VpNadder('testip1', 'ALL', noICManage=True, deliverableCheckModule='dmx.dmlib.deliverables_test', onlyContextCheck='EXAMPLE2')
#        self.assertEqual(vp.checkOneDeliverableInOneCell(manifest, 'EXAMPLE1'), dmx.dmlib.VpNadder.VpNadder.successorCheckFailStatus)
#        
#        self.assertTrue(os.path.exists('testip1/vpout/testip1/EXAMPLE2.xunit.xml'))
        

    @unittest.skipIf (skipMostTests, 'skipMostTests')
    def test_16_getDeliverableFileSpec(self):
        ''
        expected = ['<ip>/bcmrbc/*.bcm_substitute.config', 
                    '<ip>/bcmrbc/....di.filelist', 
                    '<ip>/bcmrbc/<cell>.bcm.xml', 
                    '<ip>/bcmrbc/<cell>.rbc.sv', 
                    '<ip>/bcmrbc/addbcm.config']                    
        actual = dmx.dmlib.VpNadder.getDeliverableFileSpec (deliverable='BCMRBC', 
                                                     ip='<ip>', 
                                                     cell='<cell>',
                                                     indicateFilelists=False)

        self.assertEqual (expected, actual)

        actual2 = dmx.dmlib.VpNadder.getDeliverableFileSpec (deliverable='RTL', 
                                                     ip='<ip>', 
                                                     cell='<cell>',
                                                     indicateFilelists=True)
        
        self.assertTrue ('<ip>/rtl/filelists/dv/<cell>.f (f)' in actual2)

if __name__ == "__main__":
    unittest.main (verbosity=2, failfast=True) 
