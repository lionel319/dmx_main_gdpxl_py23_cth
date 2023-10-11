#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/VpNadder.py#1 $

"""
Port of what used to be Verification Platform (VP) in project Nightfury to Nadder.

Will end up with stripping everything that is not applicable to Nadder, possibly 
accompanied by some refactoring and API changed. When finished, VP.py will be retired.
"""

import os
import unittest
import datetime
import time
import shutil 
import sys
import subprocess
import collections
import logging

import dmx.dmlib.junitxml
import dmx.dmlib.CheckType
from dmx.dmlib.ICManageWorkspace import ICManageWorkspace
from dmx.dmlib.ICManageWorkspaceMock import ICManageWorkspaceMock
from dmx.dmlib.Manifest import Manifest
from dmx.dmlib.dmError import dmError
import dmx.dmlib.deliverables.utils.General as General
from dmx.dmlib.ExpandFilelist import ExpandFilelist
from dmx.dmlib.gencompositefilelist import GenCompositeFilelist
import dmx.dmlib.TopCells
#from dmx.dmlib.deliverables.rtllec.RtllecUtils import editFilelist

# Using 'Exception': pylint: disable = W0703
# Protected member': pylint: disable = W0212 
# Outside __init__ : pylint: disable = W0201

allCheckKinds = set(['typeCheck', 
                     'dataCheck'])


def _changeErrorToFailures (contents):
    '''
    In xunit out file, change errors to failures
        <testsuite errors="3" failures="5" name="" tests="1">
        ->
        <testsuite errors="0" failures="8" name="" tests="1">
    '''       
    
    # Also replace '"errors" with "failures"
    if "<error type" not in contents:
        return contents
        
    v1 = contents.replace ("<error type", "<failure type")
    v2 = v1.replace ("</error>", "</failure>")
    
    a = v2.find ('"', 0)
    b = v2.find ('"', a+1)
    c = contents.find ('"', b+1)
    d = contents.find ('"', c+1)
    
    assert 0 < a < b < c < d
    
    errors   = int (v2 [a+1:b])
    failures = int (v2 [c+1:d])
    
    ret = v2 [0:a+1] + "0" + v2 [b:c+1] + str (errors + failures) + v2 [d:]
    
    return ret

def expandFilelistForVp (deliverableName, vp):
    '''
    Expand the filelist for the specified deliverable.
    Return the absolute path to the resulting filelist.
    
    The `templatesetString` argument is exclusively for testing.
    Use this inside VP checks.
    
    If the specified deliverable name is `RTL` or `RTLLEC` and there is a new
    style RTL .f filelist for the top IP,
    :py:class:`dmx.dmlib.gencompositefilelist` will be used to expand the filelist, and
    a `.f` style filelist will result.
    
    If the specified deliverable name other than `RTL` or there is no new style
    RTL .f filelist,
    :py:class:`dmx.dmlib.ExpandFilelist` will be used to expand the filelist, and
    a `.filelist` style filelist will result.
    
    This method is tested in `dm/ExpandFilelist_test.py` and
    `dm/gencompositefilelist_test.py`because that is where the filelist testing
    infrastructure is.
    '''
    # Try to determine 'templateset' string from elsewhere
    
    templatesetString = None

    # A: try using 'vp.manifest':
    if vp and hasattr (vp, "manifest"):
        manifest = vp.manifest
        if hasattr (manifest, "_templatesetStringArg"):
            templatesetString = manifest._templatesetStringArg
    
    # B: try using VpNadder.manifest':        
    if not templatesetString:
        if hasattr (VpNadder, "manifest"):
            manifest = vp.manifest
            if hasattr (manifest, "_templatesetStringArg"):
                templatesetString = manifest._templatesetStringArg
                
    return _expandFilelistForVp_TS (deliverableName, 
                                    vp, 
                                    templatesetString = templatesetString)     


def _expandFilelistForVp_TS (deliverableName, vp, templatesetString):    
    assert vp.ip_name is not None, 'vp.ip_name must be initialized by VpNadder.check()'
    assert vp.cell_name is not None, 'vp.cell_name must be initialized by VpNadder.check()'
    assert (not vp.isUsingICManage) or (vp._ws is not None), \
        'If using IC Manage, vp._ws must be initialized by VpNadder.check()'
    assert vp.workspaceDirName is not None, \
            'vp.workspaceDirName must be initialized by VpNadder.check()'
    assert vp.manifest is not None, 'vp.manifest must be initialized by VpNadder.check()'
    
    dirName = vp.getLogDirName()
    if not os.path.exists(dirName):
        os.makedirs(dirName)
        time.sleep(1.0)

    if vp.isUsingICManage:
        ws = vp.ws
    else:
        # Expand the filelist for the top IP only.  This is chiefly for testing.
        ws = ICManageWorkspaceMock(vp.ip_name, workspacePath=vp.workspaceDirName)
        
    if deliverableName in ['RTL', 'RTLLEC']:
        assert _hasNewStyleFilelist('RTL', vp.manifest), "Old style filelist deprecated"
        expandedFilelistPathName = _genCompositeFilelistForVp(
                                      'RTL',
                                      vp,
                                      ws,
                                      dirName,
                                      doRtllec = (deliverableName == 'RTLLEC'),
                                      templatesetString=templatesetString)
    else:   # All other deliverables use expandfilelist
        expandedFilelistPathName = _expandFilelistForVp (deliverableName,
                                                         vp,
                                                         ws,
                                                         dirName,
                                                         templatesetString)
    return expandedFilelistPathName


def genCompositeFilelistForVp_Static_TS (deliverableName,
                                         cellName,
                                         ipName,
                                         ws,
                                         nonIcmanageWorkspaceDir,
                                         dirName):    
    if ws is None:
        # Expand the filelist for the top IP only.  This is chiefly for testing.
        ws = ICManageWorkspaceMock(ipName, workspacePath=nonIcmanageWorkspaceDir)
        
    if deliverableName in ['RTL', 'RTLLEC']:
#        assert _hasNewStyleFilelist('RTL', vp.manifest), "Old style filelist deprecated"
        expandedFilelistPathName = _genCompositeFilelistForVp_Static(
                                      'RTL',
                                      cellName,
                                      ws,
                                      dirName,
                                      doRtllec = (deliverableName == 'RTLLEC'))
    else:   # All other deliverables use expandfilelist
        expandedFilelistPathName = _expandFilelistForVp_Static_TS(
                                        deliverableName, 
                                        cellName, 
                                        ipName,
                                        ws,                 
                                        nonIcmanageWorkspaceDir,  
                                        dirName,
                                        templatesetString=None)
        
    return expandedFilelistPathName


def _genCompositeFilelistForVp_Static (deliverableName, 
                                       cell_name, 
                                       ws, 
                                       dirName, 
                                       doRtllec):
    '''
    Expand the filelist for the specified deliverable using 
    :py:class:`dmx.dmlib.gencompositefilelist`.

    Return the absolute path to the resulting .f style filelist.
    
    This method is tested in `dm/gencompositefilelist_test.py`because that
    is where the filelist testing infrastructure is.
    '''
    
    
    expandedFilellstRelPathName = '{}.composite.{}.f'.format (cell_name,
                                                              deliverableName)
    expandedFilelistPathName = os.path.abspath (os.path.join (dirName,
                                                              expandedFilellstRelPathName))
    expander = GenCompositeFilelist (deliverableName, 
                                     expandedFilelistPathName,
                                     ws,
                                     itemName="cell_filelist_dv",
                                     templatesetString=None) # Will *IGNORE* passed arg
    expander.expandCells([cell_name], doRtllec)
        
    return expandedFilelistPathName


def _hasNewStyleFilelist(deliverableName, manifest):
    """Return `True` if the specified deliverable has the new style ".f"
    style filelist.
    """ 
    filelistName = ''
    try:
        filelistName = manifest.getFilelist(deliverableName, 'cell_filelist')
    except dmError:
        # This deliverable never has a new style filelist
        return False
    
    hasNewStyleFilelist = os.path.exists(filelistName)
    if not hasNewStyleFilelist:
        logging.warn ("VpInfo: Top IP '{}' cell '{}' deliverable '{}' "
                        "has no .f style filelist '{}', \n"
                      "    so using the old .filelist style '{}'."
                      "".format(manifest.ip_name, 
                                manifest.ip_name,
                                deliverableName, 
                                filelistName,
                                manifest.getFilelist(deliverableName)))
    return hasNewStyleFilelist


def _genCompositeFilelistForVp(deliverableName, 
                               vp, 
                               ws, 
                               dirName, 
                               doRtllec, 
                               templatesetString):
    '''
    Expand the filelist for the specified deliverable using 
    :py:class:`dmx.dmlib.gencompositefilelist`.

    Return the absolute path to the resulting .f style filelist.
    
    This method is tested in `dm/gencompositefilelist_test.py`because that
    is where the filelist testing infrastructure is.
    '''
    expandedFilellstRelPathName = '{}.composite.{}.f'.format(vp.cell_name,
                                                             deliverableName)
    expandedFilelistPathName = os.path.abspath(os.path.join(dirName,
                                                            expandedFilellstRelPathName))
    expander = GenCompositeFilelist(deliverableName, 
                                    expandedFilelistPathName,
                                    ws,
                                    templatesetString=templatesetString)
    expander.expandCells([vp.cell_name], doRtllec)
        
    return expandedFilelistPathName


def expandFilelistForVp_Static (deliverableName, 
                                cellName, 
                                ipName,
                                ws,                 # If none, uses cellName/ipName
                                nonIcmanageWorkspaceDir, # If 'ws', not used 
                                dirName):

    '''
    Example usage:
       - deliverable, cell, ipName - you should know
       - ws: ICManageWorkspace ("your directory")
         or
         ws = None
       - nonIcmanageWorkspaceDir: directory that is *NOT* is manage (with ws = None)
       - dirName - you should know
       - templatesetString
    '''
    return _expandFilelistForVp_Static_TS (deliverableName, 
                                           cellName, 
                                           ipName,
                                           ws,                 
                                           nonIcmanageWorkspaceDir,  
                                           dirName,
                                           templatesetString = None)
    
    
def _expandFilelistForVp_Static_TS (deliverableName, 
                                    cellName, 
                                    ipName,
                                    ws,                 # If none, uses cellName/ipName
                                    nonIcmanageWorkspaceDir, # If 'ws', not used 
                                    dirName,            # Of the resulting file
                                    templatesetString): # Normally None (uses 'real' one)
    assert ws is None or type (ws) is ICManageWorkspace
    assert dirName and ipName and deliverableName and cellName
    
    expandedFilellstRelPathName = '{}.expanded.{}.filelist'.format (cellName,
                                                                    deliverableName)
    expandedFilelistPathName = os.path.abspath(
                                    os.path.join (dirName,
                                                  expandedFilellstRelPathName))
    
    expander = ExpandFilelist (deliverableName, 
                               expandedFilelistPathName,
                               workingDirName='/',
                               templatesetString=templatesetString)
    if ws:
        expander.expandAll(ws)
    else:
        # Expand the filelist for the top IP only.  This is chiefly for testing.
        manifest = Manifest (ipName, 
                             cellName, 
                             deliverableName,
                             templatesetString = templatesetString)
        
        relativeInputFilelist = manifest.getFilelist (deliverableName, 'filelist')
        inputFilelist = os.path.join (nonIcmanageWorkspaceDir, relativeInputFilelist) 
        expander.expandFilelists([inputFilelist])

    return expandedFilelistPathName
        

def _expandFilelistForVp (deliverableName, vp, ws, dirName, templatesetString):
    '''
    Expand the filelist for the specified deliverable using
    :py:class:`dmx.dmlib.ExpandFilelist`.
    
    Return the absolute path to the resulting filelist.
            
    This method is tested in `dm/ExpandFilelist_test.py` because that is
    where the filelist testing infrastructure is.
    '''
    
    assert vp
    assert ws
    assert type (dirName) is str
    
    cellName = vp.cell_name ; assert cellName
    ipName = vp.ip_name; assert ipName
    nonIcmanageWorkspaceDir = vp.workspaceDirName
    passedWs = ws if type (ws) is ICManageWorkspace and vp.isUsingICManage else None
    #manifest = vp.manifest ; assert manifest
    
    expandedFilelistPathName = _expandFilelistForVp_Static_TS (deliverableName, 
                                                               cellName,
                                                               ipName, 
                                                               passedWs,        
                                                               nonIcmanageWorkspaceDir, 
                                                               dirName, 
                                                               templatesetString)
    return expandedFilelistPathName 


def _makeUniqueDirName (dirName):
    '''Create unique output dir name by catenating '.<int>' to dirName'''
    ret = dirName + '.old.1'
    for sufix in range (100, 0, -1):
        candidate = dirName + '.old.' + str (sufix)
        if os.path.exists (candidate):
            ret = dirName + '.old.' + str (sufix + 1)
            break 
    return ret
    

class VpCheckType(unittest.TestCase): #pylint: disable-msg=R0904
    """Run the type check as a unit test within VP."""
    
    def test_CheckType(self): # pylint: disable=R0904
        """Type check to make sure all files are present in the workspace."""
        checker = dmx.dmlib.CheckType.CheckType(VpNadder.self_)
        checker.checkType(VpNadder.deliverableName, False)
        if not checker.errors:
            return # OK
        
        msg = "Found problems with the files described in the templateset:\n  "
        msg += '\n  '.join (checker.errors)
        logging.error ("VpError:" + msg)
        sys.stdout.flush()
        self.fail (msg)


class VpNadder(object):
    '''
    Construct a Verification Platform (VP) to check the validity of deliverables for
    the specified IP in the specified workspace.
        
    The check modules will be retrieved from `deliverableCheckModule`.  This
    argument is chiefly for the sake of testing.
    '''
    
    # These class variables serve as "global" variables that can be accessed from 
    # anywhere, inside the unit tests in particular.
    self_ = None
    ip_name = None
    cell_name = None
    manifest = None

    workspaceDirName = None
    _ws = None
    isUsingICManage = True
    restoreDirName = None
    _outputPathRoot = ''
    _uniqueTempFolderPrefix = ''
    
    deliverableName = None
    topCells = None
    
    # Exit statuses
    successStatus = 0
    generalFailStatus = 1
    dataCheckFailStatus = 2
    predecessorCheckFailStatus = 3
    successorCheckFailStatus = 4
    typeCheckFailStatus = 5
    argumentErrorStatus = 126
    multipleDeliverableFailStatus = 127
    statusMessage = {successStatus : 'succeeded',
                     typeCheckFailStatus : 'failed the type check',
                     dataCheckFailStatus : 'failed the data check',
                     predecessorCheckFailStatus : 'failed the predecessor check(s)',
                     successorCheckFailStatus : 'failed the successor check(s)',
                     argumentErrorStatus : 
                          'found a problem in the vp command argument(s)',
                     multipleDeliverableFailStatus : 
                          'failed one or more checks for multiple deliverables'}

    def __init__(self,
                 ip_name,
                 workspaceDirName=None,
                 noICManage=False,
                 deliverableCheckModule='dmx.dmlib.deliverables',
                 doOnlyTypeCheck=False,
                 doOnlyDataCheck=False,
                 createUniqueTempFolder=False,
                 restoreDirName=None,
                 outputPathRoot=None,
                 doOnlyCell=None,
                 doEarlyFail=None,
                 customizedCheckers=None):
        VpNadder.self_ = self
        VpNadder.ip_name = ip_name
        VpNadder.cell_name = None
        VpNadder.isUsingICManage = not noICManage
        self.isUsingICManage = not noICManage
        if outputPathRoot is not None:
            VpNadder._outputPathRoot = os.path.abspath(outputPathRoot)
        VpNadder.doOnlyCell = doOnlyCell
        VpNadder.doEarlyFail = doEarlyFail
        
        # Map of 'original' to 'customized' checker names (Python module names)
        VpNadder._customizedCheckers = customizedCheckers  
        
        VpNadder.commandLineCwd = None
        VpNadder.startTimeAsString = None
#        self._isDryRun = isDryRun
        self._deliverableCheckModule = deliverableCheckModule
        self._result = None
        self._xunitFile = None
        self._checksPerformed = list()
        self._checksRunTimes = {}
        self._checksMemoryUsage = {}
        self._checksResults = {}

        self._totalStartTime = time.time()
        self._totalStartClock = time.clock()
        VpNadder._failedPrerequisites = {}
#        self._dashboard = VpDashboardInterface()
        self.topCellsObject_ = None
        
        VpNadder._createUniqueTempFolder = createUniqueTempFolder
        if createUniqueTempFolder:
            VpNadder._uniqueTempFolderPrefix = (datetime.datetime.now().
                                                   strftime ("%H.%M.%S"))
        if restoreDirName is None:
            VpNadder.restoreDirName = ICManageWorkspace.defaultSaveDirectoryName
        else:
            VpNadder.restoreDirName = restoreDirName

        VpNadder.workspaceDirName = ICManageWorkspace.getAbsPathOrCwd(workspaceDirName)
        if self.isUsingICManage:
            self._ws = ICManageWorkspace(workspaceDirName,
                                         self.ip_name,
                                         VpNadder.restoreDirName)
            VpNadder.workspaceDirName = self._ws.path
        else:
            self._ws = None  
        VpNadder._ws = self._ws
              
        assert noICManage == (self._ws is None), "Invariant"
        assert self.isUsingICManage == (self._ws is not None), "Invariant"
        
        self._doTypeCheck = True
        self._doDataCheck = True
        if doOnlyTypeCheck:
            logging.warn("VpWarning: As specified on the command line, "
                         "only the type check will be run.")
            self._doTypeCheck = True
            self._doDataCheck = False
        elif doOnlyDataCheck:
            logging.warn("VpWarning: As specified on the command line, "
                         "only the data check will be run.")
            self._doTypeCheck = False
            self._doDataCheck = True
        VpNadder.ignoreFailedPrerequisites_ = False

    @property
    def ws(self):
        assert self.isUsingICManage, ("It is unwise to use the ws property without "
                                      "using IC Manage.  Check the isUsingICManage "
                                      "property first.")
        return self._ws
    
    @property
    def checksPerformed(self):
        '''Get the list of checks that have been performed thus far.
        
        This property is chiefly for the sake of testing the VpNadder class--it
        reveals at what point the checking stopped.
        '''
        return self._checksPerformed
                
    @property
    def result(self):
        '''Get the current instance of JUnitXmlResult, which is set by `check()`.
        This property is chiefly for the sake of testing the VpNadder class.
        '''
        return self._result
        
    @classmethod
    def _getIpOutputDirName(cls, ip_name, createIfNotThere = False):
        '''Return the name of the output directory for the IP.
        If the directory does not exist, AND if 'createIfNotThere, create it.
        ''' 
        assert type (ip_name) is str               
        sRet = os.path.join (cls._outputPathRoot, 
                             ip_name, 
                            'vpout',
                             cls._uniqueTempFolderPrefix)
        
        if createIfNotThere:
            if not os.path.exists (sRet):
                sys.stdout.flush()
                os.makedirs (sRet)
                time.sleep (1.0)
            assert os.path.exists (sRet)
            
        return sRet
    
    @classmethod
    def getLogDirName(cls, 
                      ip_name=None,   # use cls.ip_name is None
                      cell_name=None): 
        '''Return the name of the output directory for the IP name and cell name.
        
        * Before an instance of VpNadder is created, the ip_name arg must be specified
        * Before `VpNadder.check()` is used, the cell_name argument must be specified
        '''
        ipName   = ip_name if ip_name is not None else cls.ip_name
        assert ipName, \
            "VpNadder has not yet been instantiated, so an IP name must be specified"

        cellName = cls.cell_name if cell_name is None else cell_name
        assert cellName, \
            "VpNadder.check() has not yet been invoked, so a cell name must be specified"

        return os.path.join (cls._getIpOutputDirName (ipName, 
                                                      createIfNotThere = True), 
                             cellName)

    @classmethod
    def getCellTempDirName(cls, ip_name=None, cell_name=None, absolute=False):
        '''
        Return the directory name for the ip and cell. 
        If specified, 'ip_name' and `cell_name` will be used in place of 
        the current ip/cell names.
        if absolute is True, will return absolute directory.
        '''
        ret = os.path.join (cls.getLogDirName(ip_name, 
                                              cell_name), 
                            'temp')
        if absolute:
            ret = os.path.abspath(ret)
        return ret
    
    @classmethod
    def getXUnitFileName(cls, deliverableName, ip_name=None, cell_name=None):
        '''
        Return the name of the XUnit output file for the specified
        IP and deliverable name.
        
        The optional `cell_name` argument is chiefly for use by 
        the `_deleteXUnitFiles()` method.
        If specified, 'ip_name' and `cell_name` 
        will be used in place of the current ip/cell names.
        '''
        return os.path.join (cls.getLogDirName(ip_name, cell_name), 
                             deliverableName + '.xunit.xml')

    @classmethod
    def getReportFileName(cls):
        '''Return the name of the VP summary report file for the specified IP.
        '''
        onlyFile = cls.manifest.ip_name + "/vpout/PerformedChecksReport.txt"
        
        if cls._uniqueTempFolderPrefix:
            onlyFile += '.' + cls._uniqueTempFolderPrefix
        
        fileName = os.path.join (cls._outputPathRoot, onlyFile) 
        return fileName

    def _deleteOneCellXUnitFile(self, cell_name, deliverableNames):
        '''Delete the XUnit output files for the given deliverables.
        
        * Before an instance of VpNadder is created the ip_name argument must be specified
        * Before `VpNadder.check()` is used, the cell_name argument must be specified
        '''
        logging.info("VpInfo: Deleting XUnit output files "
                     "for the specified deliverables.")
        
        for deliverableName in deliverableNames:
            xunitFileName = self.getXUnitFileName(deliverableName, cell_name=cell_name)
            if os.path.exists(xunitFileName):
                os.remove(xunitFileName)
         
        # Remove the contents of 'getCellTempDirName()' but make sure it exist:   
        tempDirName = self.getCellTempDirName (cell_name=cell_name)
        if os.path.exists (tempDirName):
            shutil.rmtree (tempDirName)
        os.makedirs (tempDirName)
        time.sleep(1.0)
        
    @classmethod
    def prepareVpoutForRun(cls, ip_name, vpInstance):
        '''
        Tries to prepare the 'vpout' for tests:
           - if present, tries to rename it to unique file name
           - then tries to create it
        Returns: True if OK, False if not.
        '''
        standardOutputName = os.path.join (ip_name, 'vpout')
        actualOutputName = cls._getIpOutputDirName (ip_name, createIfNotThere = False)
        actualOutputName = actualOutputName.rstrip ('/')
        
        # 1. Try to rename 'vpout':
        
        if actualOutputName == standardOutputName and os.path.exists (actualOutputName):

            archiveName = _makeUniqueDirName (standardOutputName)
                                        
            logging.info ("VpInfo: renaming 'vpout' to '%s'", archiveName) 
            try:
                os.rename (actualOutputName, archiveName)
                time.sleep (5.0) 
            except Exception, e:
                try: 
                    logging.warn ("Output backup quota exceeded, overwriting '%s'",
                                      actualOutputName)
                    shutil.rmtree (actualOutputName)
                except Exception, e:
                    logging.error ("VpError (fatal):" + str (e))
                    return False
            
        # 2. Make sure report file would be writable; fill it up with initial info:
        
        # 2a: Ensure its directory is there
        cls._getIpOutputDirName (ip_name, 
                                 createIfNotThere = True)
        
        # 2b: Try-write to it, fill it with stub message:
        reportFileName = cls.getReportFileName()
        try:         
            with open (reportFileName, 'w') as f:
                initialReport = vpInstance.\
                                    _createPerformedChecksReport (fatalErrors = None, 
                                                                  preliminaryOnly = True)
                f.write (initialReport)
                
        except Exception, e:
            logging.error ("VpError (fatal):" + str (e))
            return False
        
        # OK
        return True
        
        
    def _doMainVpCellLoop (self, 
                           initialManifest,
                           cellNames,
                           deliverableNames,
                           templatesetString):
        '''
        The 'classic' style main loop.
        Returns the overall accumulated exit status (sum of individual statuses)   
        '''
        assert type (cellNames is list) and cellNames
        
        overallExitStatus = 0
                                 
        for VpNadder.cell_name in cellNames:
            
#            deliverableNames = deliverableNames_0
#            if not deliverableNames:
#                continue # Entire loop should have been stripped but still OK - R.G.
            
            thisCellExitStatus = 0
            
            self._deleteOneCellXUnitFile (VpNadder.cell_name, deliverableNames)
            
            if VpNadder.cell_name == initialManifest.cell_name:
                manifest = initialManifest
            else:
                manifest = Manifest (self.ip_name, 
                                     VpNadder.cell_name, 
                                     templatesetString=templatesetString)
            
            if self.ignoreFailedPrerequisites_:
                for deliverableName in deliverableNames:
                    logging.info("\nVpInfo: Beginning all check(s)"
                                 " for cell '{}', deliverable '{}'". 
                                    format(VpNadder.cell_name, deliverableName))
                    thisCellExitStatus += self.checkOneDeliverableInOneCell (
                                             manifest, 
                                             deliverableName,
                                             allowedCheckKinds = ['typeCheck'])
                    thisCellExitStatus += self.checkOneDeliverableInOneCell (
                                             manifest, 
                                             deliverableName,
                                             allowedCheckKinds = ['dataCheck'])
                    if VpNadder.doEarlyFail and thisCellExitStatus > 0:
                        break
                    
            else:
                # FIRST: ALL-deliverables' type- and data- checks for this cell. 
                if self._doTypeCheck or self._doDataCheck:
                    for deliverableName in deliverableNames:
                        if self._doTypeCheck and self._doDataCheck:
                            kind = 'type- and data-' 
                        elif self._doTypeCheck:
                            kind = 'type'
                        else:
                            kind = 'data' 
                        
                        msg = ("\nVpInfo: Beginning {} check(s)"
                                     " for cell '{}', deliverable '{}'". 
                                        format (kind, 
                                                VpNadder.cell_name, 
                                                deliverableName))
                        logging.info (msg)
                        
                        thisCellExitStatus += self.checkOneDeliverableInOneCell (
                                                 manifest, 
                                                 deliverableName,
                                                 allowedCheckKinds = ['typeCheck'])
                        thisCellExitStatus += self.checkOneDeliverableInOneCell (
                                                 manifest, 
                                                 deliverableName,
                                                 allowedCheckKinds = ['dataCheck'])
                        
            overallExitStatus += thisCellExitStatus
                
            if VpNadder.doEarlyFail and overallExitStatus > 0:
                break
        
        sys.stdout.flush()
        
        return overallExitStatus

    def check(self, 
              unexpandedDeliverableNames, 
              templatesetString=None):
        '''
        Check the specified deliverables in all the cells in the IP.
        
        Argument unexpandedDeliverableNames must be a non-string Iterable,
        like a list or a set.
        
        Returns: 0 if all the check passed, 
                 if a single-check was run (and failed), the specific error status, 
                 if multiple checks were performed (and *some* failed) - 
                     VpNadder.multipleDeliverableFailStatus
                 
        Note: this return value is used as exit code for 'vp'-command line app. 
        '''
        assert (isinstance(unexpandedDeliverableNames, collections.Iterable) and \
               not isinstance(unexpandedDeliverableNames, basestring)), \
            "unexpandedDeliverableNames argument must be iterable, but not a string."
        initialManifest = Manifest(self.ip_name, 
                                   self.ip_name,
                                   templatesetString=templatesetString)

        # Convert all aliases to deliverable names
        trueDeliverableNames = list (initialManifest.\
                                   getDeliverableAliases (unexpandedDeliverableNames))

        # Sort deliverables topologically, making sure successors come first
        sortedDeliverableNames = initialManifest. \
                                    sortDeliverablesTopologically (trueDeliverableNames)
        if type (sortedDeliverableNames) is str: # So error
            logging.error ("VpError: topo-sort failed for:" + str (trueDeliverableNames))
            deliverableNames_0 = trueDeliverableNames 
        else:
            deliverableNames_0 = sortedDeliverableNames [::-1] # Reverse it

        assert len (deliverableNames_0) == len (trueDeliverableNames)
        
        overalExitStatus = 0
        
        topCellsObject = self._createTopCellsOjbect (useOnlyCellIfSoRequested=True)
        self.topCellsObject_ = topCellsObject 
        
        topCellFileParsingErrors = topCellsObject.generateErrorString()
        if topCellFileParsingErrors:
            overalExitStatus = 99
            
        # Some checks require 'real' top cells, as in ipspec/cell_names.txt:
        realTopCellsObject = self._createTopCellsOjbect (useOnlyCellIfSoRequested=False)
        VpNadder.topCells = realTopCellsObject.allCells_.keys() 
        
        VpNadder.manifest = Manifest (self.ip_name, 
                                      self.ip_name,
                                      templatesetString=templatesetString)
        cellNames = topCellsObject.allCells_.keys() if not topCellFileParsingErrors else []
        
        if cellNames:
            logging.info ("VpInfo: starting main loop with %d top cells", len (cellNames))
        else:
            logging.warn ("VpWarning: EMPTY top cell list - NO CHECKS PREFRORMED")
            VpNadder.manifest = Manifest (self.ip_name, 
                                          self.ip_name,
                                          templatesetString=templatesetString)
            
        if not VpNadder.prepareVpoutForRun (self.ip_name, self):
            return 101
        
        # CELL-list loop:
        if cellNames and deliverableNames_0:
            mainLoopExitStatus = self._doMainVpCellLoop (initialManifest, 
                                                         cellNames, 
                                                         deliverableNames_0, 
                                                         templatesetString)
            overalExitStatus += mainLoopExitStatus

        # Create a report:
        report = self._createPerformedChecksReport (topCellFileParsingErrors, 
                                                    preliminaryOnly = False )
        
        logging.info ('\nVpInfo:\n' + report)
        
        reportFileName = os.path.abspath (self.getReportFileName())
        s = ("\n --------------- Report also stored in file:\n     '%s'\n" % 
                      reportFileName)
        logging.info (s) 
        
        sys.stdout.flush()

        if not os.path.isdir (os.path.dirname (reportFileName)): 
            os.makedirs (os.path.dirname (reportFileName))
            time.sleep (1.0)
        with open (reportFileName, 'w') as f:
            f.write (report)
            f.write ("\n\nThis file is:\n    '%s'\n" % reportFileName)
            
        if overalExitStatus == 99:
            return overalExitStatus

        if overalExitStatus == VpNadder.successStatus:
            return VpNadder.successStatus
        
        if (not VpNadder.doEarlyFail and (len (deliverableNames_0) > 1 
              or len (cellNames) > 1)):
            return VpNadder.multipleDeliverableFailStatus
        
        return overalExitStatus
    
    
    def _getCellNames(self, ipName):
        '''Get the cell names from the IPSPEC deliverable.  If there are none,
        return `[ip_name]`.
        '''
        if self.doOnlyCell:
            logging.warn ("VpWarning: Using cell name = '{}' because "
                          "'--cell' option was used.\n".
                            format (self.doOnlyCell))
            return [self.doOnlyCell]

        workingDirName = self._ws.path if self.isUsingICManage \
                                       else VpNadder.workspaceDirName        
        ret = dmx.dmlib.TopCells.getCellNamesForIPNameAndPath (ipName = ipName, 
                                                        path   = workingDirName, 
                                                        quiet  = False,
                                                        returnIpIfEmpty = True)
        return ret
        
        
    def _createTopCellsOjbect (self, useOnlyCellIfSoRequested):
        '''
        Get the cell names from the IPSPEC deliverable.  If there are none,
        return `[ip_name]`.
        Returns a correctly-constructed TopCells.TopCells ojbect
        '''
        if self.doOnlyCell:
            logging.warn ("VpWarning: Using cell name = '{}' "
                          "because '--cell' option was used.\n".
                            format (self.doOnlyCell))
            
        m = Manifest ('dummyIp')
        allDeliverables = m.allDeliverables
        
        workspacePath = self._ws.path if self.isUsingICManage \
                                      else VpNadder.workspaceDirName        
        topCellFileName = dmx.dmlib.TopCells.getTopCellsFileNameForPath (self.ip_name, 
                                                                  workspacePath)
        if not os.path.exists (topCellFileName):
            logging.info ( "VpInfo: topcell file name '%s' not present", topCellFileName)
            topCellFileName = None                                                                
                                                             
        singleCellName = self.doOnlyCell if useOnlyCellIfSoRequested else None
                                                               
        topCells = dmx.dmlib.TopCells.TopCells (ipName                = self.ip_name,
                                         topCellFileName       = topCellFileName,
                                         singleCellName        = singleCellName,
                                         validDeliverableNames = allDeliverables) 
        return topCells                                     
    

    def _setupJUnit(self, deliverableName):
        '''
           Create the XUnit output file and instantiate the junitxml instance, 
          if not yet done.
        '''
        
        if self._xunitFile:
            return False # Was already done

        xunitFileName = self.getXUnitFileName(deliverableName)
        xunitDirName = os.path.dirname(xunitFileName)
        if not os.path.isdir(xunitDirName):
            os.makedirs(xunitDirName)
            time.sleep (1.0)
            
        self._xunitFileName = xunitFileName
        self._xunitFile = open (xunitFileName, 'w')

        self._result = dmx.dmlib.junitxml.JUnitXmlResult(self._xunitFile)
        self._result.startTestRun()
        
        return True # Was done at this call

    
    def checkOneDeliverableInOneCell (self,
                                      manifest,
                                      deliverableName,
                                      allowedCheckKinds=None):
        '''
        Perform the checks on the specified deliverable.  Return the cumulative
        exit status to be added to accumulated one in the main loop.

        Argument `allowedCheckKinds` specifies which checks are to be run.  It
        is any combination of:
        
        >>> allCheckKinds
        set(['typeCheck', 'dataCheck'])
        
        The default is to do all checks.  See the :doc:`vp` documentation for a
        complete explanation of these arguments.
        '''
        if allowedCheckKinds is None:
            allowedCheckKinds = allCheckKinds
        else:
            allowedCheckKinds = set(allowedCheckKinds)
            assert allowedCheckKinds & allCheckKinds == allowedCheckKinds
        
        # Class variable.
        VpNadder.manifest = manifest
        assert VpNadder.ip_name == manifest.ip_name

        VpNadder.cell_name = manifest.cell_name
        VpNadder.deliverableName = deliverableName
        
        signature = VpNadder.ip_name + '/' + VpNadder.cell_name + '/' + deliverableName
        
        if 'typeCheck' in allowedCheckKinds:
            bRet = self._setupJUnit(deliverableName)
            assert bRet # MUST have been done NOW
        
        ################ Type check: #################
        if self._doTypeCheck and 'typeCheck' in allowedCheckKinds:
            problemCountBeforeCheck = self._problemCount
            self._typeCheck (deliverableName)
            if self._problemCount != problemCountBeforeCheck:
                if not VpNadder.ignoreFailedPrerequisites_:
                    VpNadder._failedPrerequisites [signature] = 'typeCheck'
                return self._finishChecking (self.typeCheckFailStatus, 
                                             closeXUnitFile = 
                                                not VpNadder.ignoreFailedPrerequisites_)
            sys.stdout.flush()
            
            
        ######################## Data check: ###################
        willDoDataCheck = (not VpNadder._failedPrerequisites.get (signature)  
                              and self._doDataCheck 
                              and 'dataCheck' in allowedCheckKinds)
        
        if willDoDataCheck:
            self._setupJUnit(deliverableName)
            problemCountBeforeCheck = self._problemCount
            self._dataCheck (deliverableName)
            if self._problemCount != problemCountBeforeCheck:
                if not VpNadder.ignoreFailedPrerequisites_:
                    VpNadder._failedPrerequisites [signature] = 'dataCheck'
                return self._finishChecking (self.dataCheckFailStatus, 
                                             closeXUnitFile = 
                                                not VpNadder.ignoreFailedPrerequisites_)
            sys.stdout.flush()
 
        return self._finishChecking (0,  
                                     closeXUnitFile = True)

    @property
    def _wasSuccessful(self):
        '''Thus far, has *any* test failed or have there been any errors?'''
        assert self._result, "_wasSuccessful requires that _result be instantiated"
        return self._result.wasSuccessful()

    @property
    def _problemCount(self):
        '''The sum of errors and failures that have been found thus far.'''
        assert self._result, "_problemCount requires that _result be instantiated"
        return len(self._result.failures) + len(self._result.errors)
    
    def _finishChecking(self, exitStatus, closeXUnitFile):
        '''Clean up after check(), and return True if all checks passed.'''
        if self._xunitFile and closeXUnitFile:
            self._result.stopTestRun()
            self._xunitFile.close()
            
            # Replace 'AssertionError' with something less-scary:
            with open (self._xunitFileName, 'r') as f:
                contents = f.read()
                if 'self.fail' in contents or 'self.assert' in contents:
                    contents = contents.replace ("AssertionError", "Verification Failure")
                    
            contents_2 = _changeErrorToFailures (contents)

            with open (self._xunitFileName, 'w') as f:
                f.write (contents_2)  
            
            self._xunitFile = None
        
        logging.info ('==============================================================')
        
        if exitStatus == VpNadder.successStatus:
            exitMessage = ("Deliverable '{}' {} on IP '{}', cell '{}'."
                           "".format(VpNadder.deliverableName,
                                    VpNadder.statusMessage[exitStatus],
                                    VpNadder.ip_name,
                                    VpNadder.cell_name))
            logging.info(exitMessage)
        else:
            if not exitStatus in VpNadder.statusMessage.keys():
                exitStatus = VpNadder.multipleDeliverableFailStatus
            exitMessage = ("Deliverable '{}' {} on IP '{}', cell '{}'."
                           "".format(VpNadder.deliverableName,
                                     VpNadder.statusMessage[exitStatus],
                                     VpNadder.ip_name,
                                     VpNadder.cell_name))
            logging.error ("VpError: {}".format(exitMessage))
        logging.info ('==============================================================')

        sys.stdout.flush()
        
        return exitStatus
            
        
    @classmethod
    def _getCustomizedCheckModule(self, checkModuleName):
        ''' 
        If self._customizedCheckers is not None and _customizedCheckers [checkModuleName]: 
            returns customizedChecks [checkModuleName]
         else:
            returns checkModuleName
        Used in the optional 'customization' of any check.
        See http://fogbugz.altera.com/default.asp?106956
        '''
        if VpNadder._customizedCheckers:
            return VpNadder._customizedCheckers.get (checkModuleName, checkModuleName)
        else:
            return checkModuleName
    
    def _typeCheck(self, deliverableName):
        '''Perform the type check on the specified deliverable.'''
        
        ipWide = False
        if ipWide:
            checkName = "'{}' type check (ip-wide with cell '{}')".\
                            format (deliverableName, VpNadder.cell_name)
        else:
            checkName = "'{}' type check for cell '{}'".format (deliverableName, 
                                                                VpNadder.cell_name)
        
        if self._isCheckAlreadyPerformed(checkName):
            return
        moduleName = 'dmx.dmlib.VpNadder.VpCheckType'        
        suite = unittest.TestLoader().loadTestsFromName(moduleName)
        logging.info ("VpInfo: Running the {} ({})'.".format(checkName, moduleName))
        
        startTime = time.time()
        suite.run(self._result)
        self._xunitFile.flush()
        
#        self._dashboard.setTypeCheck(deliverableName, self._wasSuccessful)

        self._checksPerformed.append(checkName)
        self._checksMemoryUsage [checkName] = General.getProcessMemory()
        self._checksResults [checkName] = self._wasSuccessful
        self._checksRunTimes [checkName] = time.time() - startTime
        
        
    def _dataCheck(self, deliverableName):
        '''Perform the data check on the specified deliverable.'''
        
        checkName = "'{}' data check for cell '{}'".format (deliverableName, 
                                                            VpNadder.cell_name)
        if self._isCheckAlreadyPerformed(checkName):
            return
        
        # Deal with FB 104272 (data checks in a dedicated list are no-op and *pass*
        doFakePassingCheck = False # deliverableName in VpNadder._fakePassingDataChecks

        # Dealing with FB 88506 (data checks fail if not implemented):
        doFakeFailingCheck = False 
        failingCheckPyModule = '{}.fake.CheckData_FailAlways'.\
                                 format (self._deliverableCheckModule)
        passingCheckPyModule = '{}.fake.CheckData_PassAlways'.\
                                 format (self._deliverableCheckModule)
        
        for retryWithFailing in [False, True]: 
            doFakeFailingCheck = doFakeFailingCheck or retryWithFailing 
            
            if doFakePassingCheck:
                moduleName = passingCheckPyModule
            elif doFakeFailingCheck:
                moduleName = failingCheckPyModule
            else:
                moduleName = '{}.{}.CheckData'.format (self._deliverableCheckModule, 
                                                       deliverableName.lower())
                moduleName = VpNadder._getCustomizedCheckModule(moduleName)
        
            try:
                suite = unittest.TestLoader().loadTestsFromName(moduleName)
                break # i.e. successfully loaded; go on
            
            except AttributeError:
                self._printModuleNotFoundMessage ('data check', 
                                                  deliverableName, 
                                                  moduleName)
                if doFakePassingCheck or doFakeFailingCheck:
                    return # i.e. failed to load; give up
        
        logging.info("VpInfo: Running the {} ({})'.".format(checkName, moduleName))
        
        startTime = time.time()
        suite.run(self._result)
        self._xunitFile.flush()
        
#        self._dashboard.setDataCheck(deliverableName, self._wasSuccessful)

        self._checksPerformed.append(checkName)
        self._checksMemoryUsage [checkName] = General.getProcessMemory()
        self._checksResults [checkName] = self._wasSuccessful
        self._checksRunTimes [checkName] = time.time() - startTime
        

    def _isCheckAlreadyPerformed(self, checkName):
        "Return True if this check has already been performed."
        if checkName in self._checksPerformed:
            logging.info ("VpInfo: Not re-doing {} because it has already been performed.".
                          format(checkName))
            return True
        return False
   
    @classmethod
    def _printModuleNotFoundMessage(cls, checkName, deliverableName, moduleDotClass):
        '''Print the message saying that the module could not be found.'''
        components = moduleDotClass.split('.')
        moduleComponents = components[:-1]
        moduleName = '.'.join(moduleComponents)
        
        className = components[-1]
        logging.warn ("VpWarning: The {} for deliverable '{}' will be skipped\n"
                      "    because module '{}.{}' could not be imported.".
                            format (checkName,
                                    deliverableName,
                                   moduleName,
                                     className))

    def _createPerformedChecksReport (self, fatalErrors, preliminaryOnly):
        '''Return a string containing a report of the checks that were performed.
        '''
        sRet = "----------------------- Consolidated VP report -------------------\n\n"
        sRet += "Command line:\n    '{}'\n".format (' '.join (sys.argv))
        sRet += "Working directory:\n    '{}'\n".format (VpNadder.commandLineCwd)
        
        if self.isUsingICManage:
            configurationName = self._ws.configurationName
            sRet += "ICM configuration:  '{}'\n".format (configurationName)
            
            try:
                icmp4CallOutput = subprocess.check_output(['icmp4', 'opened'])
            except subprocess.CalledProcessError as err:
                areFilesOpen = "Cannot tell because {}".format(err.output)
            else:
                if 'not opened on this client' in icmp4CallOutput:
                    areFilesOpen = "no"
                else:
                    areFilesOpen = 'YES' 
            sRet += "ICMP4 opened files:  %s\n" % areFilesOpen 
            
        # See FB 121840:
        #Was: sRet += "Host:               '{}'\n".format (os.environ ["HOST"])
        sRet += "Host:               '{}'\n".format (os.uname()[1])
        try: 
            resources = subprocess.check_output (['arc', 'job-info', 'resources'])
        except subprocess.CalledProcessError as err:
            resources = "Cannot tell because {}".format(err.output)
        sRet += "Arc resources:      '{}'\n".format (resources)
        sRet += "Start time:         {}\n\n".format (VpNadder.startTimeAsString)
        
        if preliminaryOnly:
            sRet += '\n\n ***** VP check results are not available yet *******\n'
            return sRet
        
        if fatalErrors:
            assert not self._checksPerformed
            sRet += " ******** Fatal errors encountered - no checks performed *********\n"
            sRet += fatalErrors
            return sRet
        
        sRet += "****************** PERFORMED CHECK / RESULT / TIME (sec) / MEM (GB) "\
                "******************\n"
          
        sumTime = 0     
        
        passCount = 0
        failCount = 0
        
        for check in self._checksPerformed:
            if self._checksResults.get (check):
                result = "pass"
                passCount += 1
            else:
                result = "FAIL"
                failCount += 1
            
            thisCheckTime = self._checksRunTimes.get (check)
            sumTime += thisCheckTime

            thisCheckMemGb = self._checksMemoryUsage.get (check) * 1e-9
            
            sLine = '%-70s %5s %8.1f  %5.2f' \
                        % (check,
                           result,
                           thisCheckTime,
                           thisCheckMemGb)
            sRet += sLine + '\n'
        
        sRet += '\n**** Overall counts: %d passed, %d failed ****\n' % (passCount, 
                                                                        failCount)
        if failCount > 0 and VpNadder.doEarlyFail:
            assert failCount == 1
            sRet += "      (but option '--earlyfail' was in use.)\n"
            
        overalCpuClockTime = time.clock() - self._totalStartClock
        overalWalClocklTime = time.time() - self._totalStartTime

        
        sRet += '\n**** CPU total time: %.1f sec (%s) ****\n' % (
                    overalCpuClockTime, 
                    General.secondsToHMS (overalCpuClockTime))
        utilizationInPercent = (overalCpuClockTime * 100.0 / (1 + overalWalClocklTime)) 
        sRet += '    CPU utilization: %.1f%%\n' % utilizationInPercent

        sRet += '\n**** Wall-clock total time: %.1f sec (%s) ****\n' % (
                    overalWalClocklTime, 
                    General.secondsToHMS (overalWalClocklTime))
        
        sRet += '    Checks wall-clock SUM time: %.1f sec (%s)\n' % (
                        sumTime, 
                        General.secondsToHMS (sumTime))
        sRet += '    Accounted time: %.1f%%' % (sumTime*100.0 / (overalWalClocklTime+1))
        
        return sRet
    

def getDeliverableFileSpec (deliverable, ip, cell, indicateFilelists):
    '''
    Return a list of filespecs for the specified deliverable, something like:
      [ 'ip/rtl/cell/*.v', 'ip/rtl/ip_cel.filelist' ]
      
    If 'indicateFilelists' is True, the entries corresponding to filelists
    are suffixed by ' (f)', e.g. 'ip/rtl/ip_cel.filelist (f)'
    
    See http://fogbugz/default.asp?290185
    '''
    assert type (deliverable) is str and type (ip) is str and type (cell) is str
    assert deliverable and ip and cell
    assert indicateFilelists in (True, False)
    
    manifest = Manifest (ip_name=ip, cell_name=cell)
    ret = manifest.reportDeliverableFilePatterns (deliverable, 
                                                  indicateFilelists=indicateFilelists)
    return ret


    
    
