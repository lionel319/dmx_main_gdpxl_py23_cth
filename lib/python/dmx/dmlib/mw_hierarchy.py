#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/mw_hierarchy.py#1 $

"""
`dmx.dmlib.mw_hierarchy` gets information about the Milkyway hierarchy by executing the
procedures in the `mw_hierarchy` Tcl package in `../tcl/mw_hierarchy.tcl`.

It does this by creating a Tcl script, executing it in IC Compiler to create a
JSON file containing the data, then reading the JSON file into instance variables.
Then, client programs retrieve the data via `mw_hierarchy` properties.
"""

__author__ = "John McGehee (jmcgehee@altera.com)"
__revision__ = "$Revision: #1 $"
__date__ = "$Date: 2022/12/13 $"
__copyright__ = "Copyright 2011 Altera Corporation"

import json
import os

from dmx.dmlib.dmError import dmError
from dmx.dmlib.deliverables.utils.MilkywayUtils import runICCompiler
from dmx.dmlib.CheckType import CheckType

class MwHierarchy(object):
    '''Extract the hierarchy of the specified Milkyway cell.
    
    Create temporary files in and run IC Compiler in the specified
    `workingDirName`.  Create `workingDirName` if it does not exist.
    
    Also produce a reference library control file if it is specified.  This
    somewhat unrelated functionality is included to economize on run time so
    that IC Compiler need only be run once.
    
    It is an error to specify a nonexistent library or cell.
    '''
    
    tclScriptFileName = 'mw_hierarchy.run.tcl'
    jsonFileName = 'mw_hierarchy.json'
    
    def __init__(self, libraryPath, cellName,
                 workingDirName='.',
                 referenceControlFileName=None):
        self._libraryPath = os.path.abspath(libraryPath)
        if not CheckType.isMilkywayLibrary(self._libraryPath):
            raise dmError("Milkyway library '{}' does not exist".format(self._libraryPath))
        self._cellName = cellName
        self._workingDirName = os.path.abspath(workingDirName)
        self._referenceControlFileName = referenceControlFileName
        
        self._tclScriptPath = os.path.join(self._workingDirName, self.tclScriptFileName)
        self._jsonFilePath  = os.path.join(self._workingDirName, self.jsonFileName)

        self._topDesign = []
        self._hardMacros = set()
        self._softMacros = set()
        
        self._traverse()
        assert os.path.samefile(self._topDesign[0], libraryPath), \
                "Library name came back from ICC unchanged"
        assert self._topDesign[1] == unicode(cellName), "Cell name came back from ICC unchanged"
        
    @property
    def topDesign(self):
        '''The top design in the hierarchical traversal in the form::
        
        [libraryPath cellName]
        
        This is the same library and cell name specified in the constructor.
        
        The names are unicode strings.
        '''
        return self._topDesign

    @property
    def hardMacros(self):
        '''The set of hard macro (leaf cell) names found after traversing the
        hierarchy of the cell specified in the constructor.
        
        The names are unicode strings.
        '''
        return self._hardMacros

    @property
    def softMacros(self):
        '''The set of soft macro (hierarchical, non-leaf cell) names found after
        traversing the hierarchy of the cell specified in the constructor.
        
        The names are unicode strings.
        '''
        return self._softMacros

    def _traverse(self):
        '''Create a script utilizing the ../tcl/mw_hierarchy.tcl package and
        run it in IC Compiler.   Store the results in instance variables.
        '''
        self._createTclScript(self._libraryPath, self._cellName,
                              self._referenceControlFileName,
                              workingDirName=self._workingDirName)
        isSuccess = runICCompiler(self._tclScriptPath,
                                  self._workingDirName,
                                  'mw_hierarchy',
                                  removeLockFileFromLibrary=self._libraryPath)
        if not isSuccess:
            raise dmError("An error occurred while running IC Compiler")
        self._readJsonResult()
    
        
    @classmethod
    def writeReferenceControlFile(cls, libraryPath, referenceControlFileName,
                                  workingDirName='.'):
        '''Create a Milkyway reference library control file.
    
        It is an error to specify a nonexistent library.
        '''
        absLibraryPath = os.path.abspath(libraryPath)
        absWorkingDirName = os.path.abspath(workingDirName)
        if not CheckType.isMilkywayLibrary(absLibraryPath):
            raise dmError("Milkyway library '{}' does not exist".format(absLibraryPath))
        cls._createTclScript(absLibraryPath,
                             referenceControlFileName=referenceControlFileName,
                             workingDirName=absWorkingDirName)
        tclScriptPath = os.path.join(absWorkingDirName, cls.tclScriptFileName)
        runICCompiler(tclScriptPath, absWorkingDirName, 'mw_hierarchy', removeLockFileFromLibrary=libraryPath)
    
    @classmethod
    def _createTclScript(cls, libraryPath, cellName=None,
                         referenceControlFileName=None, workingDirName='.'):
        '''Create the IC Compiler Tcl script utilizing ../tcl/mw_hierarchy.tcl.
        
        If the `cellName` argument is specified, include the
        `::mw_hierarchy::report_macros` command.
        
        If the `referenceControlFileName` argument is specified, include the
        `::mw_hierarchy::write_reference_control_file` command.
        '''
        absWorkingDirName = os.path.abspath(workingDirName)
        if not os.path.exists(absWorkingDirName):
            os.makedirs(absWorkingDirName)
        assert os.path.isabs(libraryPath), \
                "For safety, the library path should be an absolute path"
        dmRoot = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        mwHierarchyLibraryScriptName = os.path.join(dmRoot, 'tcl', 'mw_hierarchy.tcl')
        assert os.path.exists(mwHierarchyLibraryScriptName), "../tcl/mw_hierarchy.tcl exists"
        tclScriptPath = os.path.join(absWorkingDirName, cls.tclScriptFileName)
        with open(tclScriptPath, 'w') as f:
            f.write('# Extract the hierarchy from a Milkyway cell using dm/tcl/mw_hierarchy.tcl.\n')
            f.write('# This script is automatically created by Python module dmx.dmlib.mw_hierarchy.\n')
            f.write('\n')
            f.write('source "{}"\n'.format(mwHierarchyLibraryScriptName))
            if cellName is not None:
                f.write('::mw_hierarchy::report_macros "{}" "{}" "{}"\n'
                        ''.format(libraryPath, cellName, cls.jsonFileName))
            if referenceControlFileName is not None:
                f.write('::mw_hierarchy::write_reference_control_file "{}" "{}"\n'
                        ''.format(libraryPath, os.path.abspath(referenceControlFileName)))
            f.write('\n')
            f.write('exit\n')

    def _readJsonResult(self):
        '''Read the JSON file produced by the Tcl script.'''
        try:
            f = open(self._jsonFilePath)
        except:
            raise dmError(
                "Cannot load the Milkyway hierarchy from JSON file '{}'\n"
                "    because it is not readable.".format(self._jsonFilePath)) 
        if not os.path.getsize(self._jsonFilePath):
            raise dmError(
                "Cannot load the Milkyway hierarchy from JSON file '{}'\n"
                "    because the file is empty.  This is probably because \n"
                "    cell '{}' in library '{}' could not be opened."
                "".format(self._jsonFilePath, self._cellName, self._libraryPath)) 
        result = json.load(f)
        f.close()
        
        self._topDesign = result["top_design"]
        self._hardMacros = set(result["hard_macros"])
        self._softMacros = set(result["soft_macros"])
    

if __name__ == "__main__":
    # Running mw_hierarchy_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod()
