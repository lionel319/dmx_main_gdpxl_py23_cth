#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/mw_submit_test.py#1 $

"""
Test the mw_submit class. Most of the tests are performed using doctest
via the doctest-unittest interface.
"""

import os
import unittest
import doctest
import subprocess
import random
import getpass
import shutil

from P4 import P4Exception
import dmx.dmlib.mw_submit
from dmx.dmlib.dmError import dmError

# unused argument: pylint: disable = W0613
# accessing protected member: pylint: disable = W0212

skipMostTests=False # flip it for debugging
if skipMostTests:
    print "********* Warning: in %s, skipMostTests==True! ***************" % __file__

def load_tests(loader, tests, ignore):
    '''Load the mw_submit.py doctest tests into unittest.'''
    tests.addTests(doctest.DocTestSuite(dmx.dmlib.mw_submit))
    return tests

class TestMwSubmit(unittest.TestCase): # pylint: disable=R0904
    """Test the MwSubmit class."""

    _workspaceName = None
    _workspacePath = None
    _releaseLibraryPath = None
    
    @classmethod
    def setUpClass(cls):
        '''Set up the test workspace.'''
        cls._workspaceName = cls._createAndSyncWorkspace('zz_dm_test',
                                                        'icmp4mwsubmit_lib',
                                                        'dev',
                                                        '.')     
#        print "WS NAME:", cls._workspaceName 
        cls._workspacePath = os.path.abspath(cls._workspaceName)
        cls._releaseLibraryPath = os.path.join(cls._workspacePath,
                                               'icmp4mwsubmit_lib/pnr/icmp4mwsubmit_lib')
        # The "upper" workspace is the workspace that models the workspace for
        # the designers whose IP instantiates the design submitted to  _workspacePath.
        cls._upperWorkspaceName = cls._createAndSyncWorkspace('zz_dm_test',
                                                              'icmp4mwsubmit',
                                                              'dev',
                                                              '.')     
        cls._upperWorkspacePath = os.path.abspath(cls._upperWorkspaceName)
        cls._upperReleaseLibraryPath = os.path.join(cls._upperWorkspacePath,
                                               'icmp4mwsubmit_lib/pnr/icmp4mwsubmit_lib')        

    @classmethod
    def tearDownClass(cls):
        '''Tear down the test workspace.'''
        cls._deleteWorkspace(cls._workspaceName, cls._workspacePath)

    @classmethod
    def _createAndSyncWorkspace(cls, projectName, variantName, configurationName,
                                workspacePath):
        '''Create and sync a workspace to the specified path.  Return the
        workspace path.
        '''
        userName = getpass.getuser()
        command = ['pm', 'workspace', projectName, variantName,
                   configurationName, userName, workspacePath]
        creationMessage = ''
        try:
            creationMessage = subprocess.check_output(command)
        except subprocess.CalledProcessError:
            raise dmError('Could not create an IC Manage workspace')
        workspaceName = creationMessage.split()[1]

        command = ['pm', 'workspace', '-s', workspaceName]
        try:
            subprocess.check_output(command)
        except subprocess.CalledProcessError:
            raise dmError("Could not sync the new IC Manage workspace '{}'".format(workspaceName))
        
        return workspaceName 

    @classmethod
    def _deleteWorkspace(cls, workspaceName, workspacePath):
        '''Delete the specified workspace and all the files in it.
        
        TO_DO: Check if `_workspaceName` and `_workspacePath` actually match.
        '''
        command = ['icmp4', 'revert', os.path.join(workspacePath, '...')]
        try:
            result = subprocess.check_output(command)
            _ = result # suppress 'unused' message
        except subprocess.CalledProcessError:
            pass
        command = ['pm', 'workspace', '-x', workspaceName]
        try:
            subprocess.check_output(command)
        except subprocess.CalledProcessError:
            if os.path.exists(workspacePath):
                shutil.rmtree(workspacePath)
            raise Exception("This is a problem with mw_submit_test (not mw_submit):\n"
                            "Could not delete the workspace from IC Manage using the command:\n"
                            "    {}".format(' '.join(command)))

        if os.path.exists(workspacePath):
            shutil.rmtree(workspacePath)
                
    def setUp(self):
        '''Set up the test'''
        assert self._workspaceName, "Should be set by setUpClass()"
        assert self._workspacePath, "Should be set by setUpClass()"
        assert self._releaseLibraryPath, "Should be set by setUpClass()"
        assert self._upperWorkspaceName, "Should be set by setUpClass()"
        assert self._upperWorkspacePath, "Should be set by setUpClass()"
        assert self._upperReleaseLibraryPath, "Should be set by setUpClass()"
        
        subprocess.call ('icmp4 revert ...; icmp4 sync ...', 
                         shell=True,
                         cwd=os.path.dirname(self._releaseLibraryPath))

        subprocess.call ('icmp4 revert ...; icmp4 sync ...', 
                         shell=True,
                         cwd=os.path.dirname(self._upperReleaseLibraryPath))

        # If the release library exists, make sure it looks like a Milkyway
        # library.
        if os.path.exists(self._releaseLibraryPath):
            if not os.path.exists(os.path.join(self._releaseLibraryPath, 'lib')):
                fileName = os.path.join(self._releaseLibraryPath, "lib")
                with open(fileName, 'w') as f:
                    f.write('lib file\n')
            
#    def tearDown(self):
#        pass


    # Leading "0" causes empty test to run first.
    @unittest.skipIf (skipMostTests, "skipMostTests")
    def test_0_empty(self):
        '''Test initialization on empty instance'''
        submitter = dmx.dmlib.mw_submit.MwSubmit('icmp4mwsubmit_lib',
                                          os.path.join(self._workspacePath,
                                                       'icmp4mwsubmit_lib/icc/icmp4mwsubmit_lib'),
                                          'PNR',
                                          workspacePath=self._workspacePath)
        self.assertEqual(submitter._releaseLibraryPath,
                         os.path.join(self._workspacePath,
                                      'icmp4mwsubmit_lib/pnr/icmp4mwsubmit_lib'))
        self.assertEqual(submitter._iccWorkingDirectory,
                         os.path.join(self._workspacePath,
                                      'icmp4mwsubmit_lib/pnr'))
        self.assertEqual(submitter._workingLibraryPath,
                         os.path.join(self._workspacePath,
                                      'icmp4mwsubmit_lib/icc/icmp4mwsubmit_lib'))
        self.assertSetEqual(submitter._cellNames,
                            set(['testIP', 'testIP_2y', 'testIP_2x', 'testIP_3y']))
        
    @unittest.skipIf (skipMostTests, "skipMostTests")
    def test_1_cellAndViewNames(self):
        '''Test the cell and view names for different deliverables'''
        submitter = dmx.dmlib.mw_submit.MwSubmit('icmp4mwsubmit_lib',
                                          os.path.join(self._workspacePath,
                                                       'icmp4mwsubmit_lib/icc/icmp4mwsubmit_lib'),
                                          'PNR',
                                          workspacePath=self._workspacePath)
        self.assertSetEqual(submitter._cellNames,
                            set(['testIP', 'testIP_2y', 'testIP_2x', 'testIP_3y']))
        self.assertEqual(submitter._viewNames,
                            ('CEL', 'FRAM', 'FILL', 'ILM'))
        
    @unittest.skipIf (skipMostTests, "skipMostTests")
    def test_2_switchoChango(self):
        '''Submit a library containing one file, then submit a library containing another.'''
        submitter = dmx.dmlib.mw_submit.MwSubmit('icmp4mwsubmit_lib',
                                          os.path.join(self._workspacePath,
                                                       'icmp4mwsubmit_lib/icc/icmp4mwsubmit_lib'),
                                          'PNR',
                                          workspacePath=self._workspacePath)
        
        submitter.submit('test_switchoChango: switcho', externalReleaseLibraryCreator=createFirstFile)
        self.assertItemsEqual(_getAllFilesInDirectory(self._releaseLibraryPath),
                              ['lib', 'first.txt', 'common.txt'])
        depotFiles = submitter.p4.run_filelog(os.path.join(self._releaseLibraryPath, '...'))
        submittedFiles = [i.depotFile for i in depotFiles]
        self.assertItemsEqual(submittedFiles, [
            '//depot/icm/proj/zz_dm_test/icmp4mwsubmit_lib/pnr/icmp4mwsubmit_lib/icmp4mwsubmit_lib/lib',
            '//depot/icm/proj/zz_dm_test/icmp4mwsubmit_lib/pnr/icmp4mwsubmit_lib/icmp4mwsubmit_lib/first.txt',
            '//depot/icm/proj/zz_dm_test/icmp4mwsubmit_lib/pnr/icmp4mwsubmit_lib/icmp4mwsubmit_lib/common.txt'])

        submitter.submit('test_switchoChango: chango', externalReleaseLibraryCreator=createSecondFile)
        self.assertItemsEqual(_getAllFilesInDirectory(self._releaseLibraryPath),
                              ['lib', 'second.txt', 'common.txt'])
        depotFiles = submitter.p4.run_filelog(os.path.join(self._releaseLibraryPath, '...'))
        submittedFiles = [i.depotFile for i in depotFiles]
        self.assertItemsEqual(submittedFiles, [
            '//depot/icm/proj/zz_dm_test/icmp4mwsubmit_lib/pnr/icmp4mwsubmit_lib/icmp4mwsubmit_lib/lib',
            '//depot/icm/proj/zz_dm_test/icmp4mwsubmit_lib/pnr/icmp4mwsubmit_lib/icmp4mwsubmit_lib/second.txt',
            '//depot/icm/proj/zz_dm_test/icmp4mwsubmit_lib/pnr/icmp4mwsubmit_lib/icmp4mwsubmit_lib/common.txt'])
        
    @unittest.skipIf (skipMostTests, "skipMostTests")
    def test_3_doSubmit(self):
        '''Test the doSubmit option.'''
        print "***********", self._workspacePath
        submitter = dmx.dmlib.mw_submit.MwSubmit('icmp4mwsubmit_lib',
                                          os.path.join(self._workspacePath,
                                                       'icmp4mwsubmit_lib/icc/icmp4mwsubmit_lib'),
                                          'PNR',
                                          workspacePath=self._workspacePath)
        
        submitter.submit('test_doSubmit', doSubmit=False,
                         externalReleaseLibraryCreator=createFirstFile)
        self.assertItemsEqual(_getAllFilesInDirectory(self._releaseLibraryPath),
                              ['lib', 'first.txt', 'common.txt'])
        with self.assertRaises(P4Exception):
            # Raises exception when nothing was submitted
            submitter.p4.run_filelog(os.path.join(self._releaseLibraryPath, '...'))
        
    @unittest.skipIf (skipMostTests, "skipMostTests")
    def _test_4_openFile(self):
        '''An open file in the release library is an error'''
        submitter = dmx.dmlib.mw_submit.MwSubmit('icmp4mwsubmit_lib',
                                          os.path.join(self._workspacePath,
                                                       'icmp4mwsubmit_lib/icc/icmp4mwsubmit_lib'),
                                          'PNR',
                                          workspacePath=self._workspacePath)
        libFilePath = os.path.join(self._releaseLibraryPath, 'lib')
        if not os.path.exists(self._releaseLibraryPath):
            os.makedirs(self._releaseLibraryPath)
            if not os.path.exists(libFilePath):
                with open(libFilePath, 'w') as f:
                    f.write('lib file\n')
        self.assertTrue(os.path.exists(libFilePath),
                        'The test fixture is expected to contain a lib file')
        submitter.p4.run_open(libFilePath)
        with self.assertRaises(dmError):
            submitter.submit('test_openFile', externalReleaseLibraryCreator=createFirstFile)
        
    @unittest.skipIf (skipMostTests, "skipMostTests")
    def _test_5_unsynced(self):
        '''An un-synced release library is an error'''
        upperSubmitter = dmx.dmlib.mw_submit.MwSubmit('icmp4mwsubmit',
                                               os.path.join(self._workspacePath,
                                                           'icmp4mwsubmit/icc/icmp4mwsubmit'),
                                               'PNR',
                                               workspacePath=self._upperWorkspacePath)
        libFilePath = os.path.join(self._upperReleaseLibraryPath, 'lib')
        if not os.path.exists(self._upperReleaseLibraryPath):
            os.makedirs(self._upperReleaseLibraryPath)
            if not os.path.exists(libFilePath):
                with open(libFilePath, 'w') as f:
                    f.write('lib file\n')
                upperSubmitter.p4.run_add(libFilePath)
        else:
            p4EditResults = upperSubmitter.p4.run_edit(libFilePath)
            if p4EditResults and isinstance(p4EditResults[0], basestring):
                raise Exception("This is a problem with mw_submit_test (not mw_submit): {}".format(p4EditResults))
            with open(libFilePath, 'w') as f:
                f.write('lib file that has updated contents: {}\n'.format(random.random()))
        self.assertTrue(os.path.exists(libFilePath),
                        'The upper release library is expected to contain a lib file')
        upperSubmitter.p4.run_submit('-d', 'submit a changed file to make the other workspace un-synced',
                                     libFilePath)
        # The release library in self._workspacePath is now out of sync
        
        submitter = dmx.dmlib.mw_submit.MwSubmit('icmp4mwsubmit_lib',
                                          os.path.join(self._workspacePath,
                                                       'icmp4mwsubmit_lib/icc/icmp4mwsubmit_lib'),
                                          'PNR',
                                          workspacePath=self._workspacePath)
        with self.assertRaises(dmError):
            submitter.submit('test_unsynced', externalReleaseLibraryCreator=createFirstFile)
        
    @unittest.skipIf (skipMostTests, "skipMostTests")
    def test_6_noPreexistingLibrary(self):
        '''Test the situation where there is no pre-existing release library.'''
        #pass
        submitter = dmx.dmlib.mw_submit.MwSubmit('icmp4mwsubmit_lib',
                                          os.path.join(self._workspacePath,
                                                       'icmp4mwsubmit_lib/icc/icmp4mwsubmit_lib'),
                                          'PNR',
                                          workspacePath=self._workspacePath)
        # Do not set the description this way in ordinary usage
        submitter._description = 'test with no pre-existing release library'
        submitter._removeExistingReleaseLibrary()
        self.assertFalse(os.path.exists(self._releaseLibraryPath),
                        'MwSubmit._removeExistingReleaseLibrary() removed the release library')
        submitter.submit('test_noPreexistingLibrary', externalReleaseLibraryCreator=createFirstFile)
        self.assertItemsEqual(_getAllFilesInDirectory(self._releaseLibraryPath),
                              ['lib', 'first.txt', 'common.txt'])
        depotFiles = submitter.p4.run_filelog(os.path.join(self._releaseLibraryPath, '...'))
        submittedFiles = [i.depotFile for i in depotFiles]
        self.assertItemsEqual(submittedFiles, [
            '//depot/icm/proj/zz_dm_test/icmp4mwsubmit_lib/pnr/icmp4mwsubmit_lib/icmp4mwsubmit_lib/lib',
            '//depot/icm/proj/zz_dm_test/icmp4mwsubmit_lib/pnr/icmp4mwsubmit_lib/icmp4mwsubmit_lib/first.txt',
            '//depot/icm/proj/zz_dm_test/icmp4mwsubmit_lib/pnr/icmp4mwsubmit_lib/icmp4mwsubmit_lib/common.txt'])


def createFirstFile(releaseLibraryPath):
    _createFakeMilkywayLibrary(releaseLibraryPath, ('first.txt', 'common.txt',))

def createSecondFile(releaseLibraryPath):
    _createFakeMilkywayLibrary(releaseLibraryPath, ('second.txt', 'common.txt',))

def _getAllFilesInDirectory(path):
    '''Get a list of all files in the specified directory.
    '''
    allNames = []
    for (root, dirNames, fileNames) in os.walk(path):
        _ = dirNames # Suppress 'unused' warning
        for fileName in fileNames:
            allNames.append(os.path.join(root, fileName))
    return fileNames  # Potential infinite loop; pylint: disable = W0631

def _createFakeMilkywayLibrary(libraryPath, fileNames):
    '''Create a directory that looks enough like a Milkyway library to fool
    `CheckerBase.isMilkywayLibrary()`.  Add the specified files to it.
    '''
    assert not os.path.exists(libraryPath), 'Release library should be gone'
    os.makedirs(libraryPath)
    fileName = os.path.join(libraryPath, "lib")
    with open(fileName, 'w') as f:
        f.write('lib file\n')
    for fileName in fileNames:
        pathName = os.path.join(libraryPath, fileName)
        with open(pathName, 'w') as f:
            f.write('This file created by the mw_submit unit test\n')
           
        
if __name__ == "__main__":
    unittest.main (failfast=True, verbosity=True)
