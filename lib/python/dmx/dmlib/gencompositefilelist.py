#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/gencompositefilelist.py#1 $

"""
GenCompositeFilelist creates a composite file list from a set of filelists,
replacing the special directory name "{}" with the corresponding full path.

For the greatest detail, see the 
`full specification and usage instructions for GenCompositeFilelist 
<http://sw-wiki.altera.com/twiki/bin/view/Altera/AlteraDMZIPLIST>_`

GenCompositeFilelist depends on the convention that each Verilog module is in
a separate file named `module`.v.
 
Command Line Interface
=======================
`GenCompositeFilelist` is exposed as a command line application as the
:doc:`gencompositefilelist`.
"""

import os
import string #pylint: disable = W0402
import copy
import logging

from dmx.dmlib.expandfilelist_base import ExpandFilelistBase
from dmx.dmlib.parsers import parseFilelist, parseCellNamesFile
from dmx.dmlib.Manifest import Manifest
from dmx.dmlib.dmError import dmError


_enironmentVariables = copy.deepcopy(os.environ)
 


def _replaceEnvVarMatches (text, env):
    '''
    In 'text':
       - expand all *PRESENT* environment variables $X or ${X}
       - leaves everything else intact
    See http://fogbugz.altera.com/default.asp?215840
    '''
    
    text = copy.copy(text)
    for e in env:

        # Only replace 'word' variables
        if not e.replace ('_','1').isalnum():
            continue

        if e in text:
            subst = env[e]
            text = text.replace ('${%s}' % e, subst) 
            text = text.replace ('$%s'   % e, subst)
        
    return text
    

class GenCompositeFilelist(ExpandFilelistBase):
    """
    Instantiate a composite filelist expander to expand the filelists for the
    specified deliverable, and put the result in file `outputFileName`.
    
    Use the `expandCells()` method to perform the expansion.
    
    When `deliverableName` is not a deliverable containing Verilog files (like
    RDF), discard VCS options that appear in the input filelists (VCS options
    begin with '-' or '+').
 
    # TO_DO: outputFileName should be an argument of expandCells()
    
    Argument `ws` is an instance of either :py:class`dmx.dmlib.ICManageWorkspace` or
    :py:class`dmx.dmlib.ICManageWorkspaceMock`.  Use :py:class`dmx.dmlib.ICManageWorkspace` in
    functional code and :py:class`dmx.dmlib.ICManageWorkspaceMock` for testing.
    
    The `blackBox` argument specifies a list of paths to black box files that
    replace the entire hierarchy for the corresponding Verilog module.

    The `extraFiles` argument specifies a list of additional Verilog files to be
    added to the output filelist.
    
    `itemName` is the deliverable item name that identifies the filelist
    definition in the templateset.  The default is "{}".
    
    `templatesetString` allows you to use to specify a templateset.  This is
    chiefly for testing.
    
    `dmx.dmlib.gencompositefilelist` is exposed as a command line application as the
    :doc:`gencompositefilelist`.  See :doc:`gencompositefilelist` for more detailed
    documentation.
    """
    
    rootPrefix = 'wkspace_root/'
    defaultItemName = 'cell_filelist'
    
    def __init__(self,
                 deliverableName,
                 outputFileName, 
                 ws,
                 blackboxFiles=None,
                 initialFilelist=None,
                 extraFiles=None,
                 itemName=None,
                 templatesetString=None):
        if itemName is None:
            itemName = self.defaultItemName
        super(GenCompositeFilelist, self).__init__(deliverableName,
                                                   outputFileName,
                                                   itemName)
        self._ws = ws    # Might be ICManageWorkspaceMock
        self._templateManifest = Manifest('${ipName}', '${cellName}',
                                          templatesetString=templatesetString)
        filelistTemplateString = self._templateManifest.getFilelist(deliverableName,
                                                                    self._itemName)
        self._filelistTemplate = string.Template(filelistTemplateString)
        self._doneFilelists = set()
        self._doRtllec = False
        self._blackboxFiles = blackboxFiles
        if self._blackboxFiles is None:
            self._blackboxFiles = []
        if initialFilelist is not None:
            initialFilelist = self.adjustPath(initialFilelist, self._ws.path,
                                              doRequireRootPrefix=False)
        self.initialFilelist = initialFilelist
        if extraFiles is None:
            extraFiles = []
        self.extraFiles = [self.adjustPath(extraFile, self._ws.path) 
                              for extraFile in extraFiles]
            
        # These attributes should only be accessed via the corresponding
        # property, even from within this class
        self._filelistIndexAccessOnlyViaProperty = None
        self._cellNamesAccessOnlyViaProperty = None
        self._blackboxIndexAccessOnlyViaProperty = None
        
    def getFilelistName(self, moduleName):
        '''Return the file name of the filelist for the given Verilog module.
        There is no guarantee that the filelist file named in the value actually
        exists.

        Return `None` if the named module is not a cell in the workspace, and
        therefore can have no filelist defined.
        '''
        return self._filelistIndex.get(moduleName)
    
    @property
    def cellNames(self):
        '''All cell names in the IC Manage workspace.'''
        if self._cellNamesAccessOnlyViaProperty is None:
            self._cellNamesAccessOnlyViaProperty = self._filelistIndex.keys()
        return self._cellNamesAccessOnlyViaProperty
    
    @property
    def _filelistIndex(self):
        '''A dictionary whose key is the cell name (Verilog module name), and
        whose value is the path to the corresponding filelist, for all
        combinations of `ipName` and `cellName` in the workspace.

        There is no guarantee that the filelist file named in the value actually
        exists.
        '''
        if self._filelistIndexAccessOnlyViaProperty is None:
            self._filelistIndexAccessOnlyViaProperty = dict()
            libType = self._ws.getLibType(self._deliverableName)
            ipNames = self._ws.getIpNames(libType)
            for ipName in ipNames:
                cellNames = self._ws.getCellNamesForIPName(ipName)
                for cellName in cellNames:
                    if cellName in self._filelistIndexAccessOnlyViaProperty.keys():
                        logging.warn("Cell '{}' is not unique.  It appears in "
                                     "IP '{}' and some others.".format(cellName, ipName))
                    filelistName = self._createFilelistPath(ipName, cellName)
                    self._filelistIndexAccessOnlyViaProperty[cellName] = filelistName
        return self._filelistIndexAccessOnlyViaProperty

    @property
    def blackboxModules(self):
        '''The list of modules that have black box files defined.'''
        return self._blackboxIndex.keys()
         
    def getBlackboxFileName(self, moduleName):
        '''Return the file name of the black box file for the given Verilog cell.

        Return `None` if there is no black box file defined for this module.
        '''
        return self._blackboxIndex.get(moduleName)
    
    @property
    def _blackboxIndex(self):
        '''A dictionary whose key is the cell name (Verilog module name), and
        whose value is the absolute path to the corresponding blackbox
        definition file specified upon instantiation.
        '''
        if self._blackboxIndexAccessOnlyViaProperty is None:
            self._blackboxIndexAccessOnlyViaProperty = dict()
            for blackboxFileName in self._blackboxFiles:
                blackboxFileName = self.adjustPath(blackboxFileName, self._ws.path)
                moduleName = self._parseModuleNameFromPath(blackboxFileName, '.v')
                if moduleName is None:
                    raise dmError("No module name could be parsed from "
                                  "the black box Verilog file name '{}'."
                                  "".format(blackboxFileName))
                self._blackboxIndexAccessOnlyViaProperty[moduleName] =  blackboxFileName
        return self._blackboxIndexAccessOnlyViaProperty
    
    @classmethod
    def parseBlackboxFile(cls, fileName):
        '''Parse the black box file and return the list of path names it
        contains as-is.
        
        As a convenience for working with the command line parser, return the
        empty list if the file name is `None`.
        '''
        if fileName is None:
            return []
        return parseCellNamesFile(fileName)
    
    def _createFilelistPath(self, ipName, cellName):
        '''Given an IP and cell name, return the absolute path to the cell
        filelist file name.
        
        The existence or readability of this file is not checked.
        '''
        pathWithinWorkspace = self._filelistTemplate.substitute(ipName=ipName,
                                                                cellName=cellName)
        filelistPath = os.path.join(self._ws.path, pathWithinWorkspace)
        return filelistPath
    
    @classmethod
    def parseExtraFile(cls, fileName):
        '''Parse the extra file and return the list of path names it
        contains as-is.
        
        As a convenience for working with the command line parser, return the
        empty list if the file name is `None`.
        '''
        return cls.parseBlackboxFile(fileName)
    
    def convertFilelists(self, cellNames):
        '''Convert the filelists for the specified cells from the old style .f
        filelist (as described in the Version 1.0 spec) to the new style .f
        filelist (as described in the Version 1.1 spec).
        
        Retain a backup copy of the old style filelist in the file
        `cellName.oldstyle.f`.
        '''
        assert self._deliverableName == 'RTL', \
            "The --convert option can only be used with deliverable RTL"
                    
        for cellName in set(cellNames):
            cellFilelistName = self.getFilelistName(cellName)
            savedCellFilelistName = self._saveCellFilelist(cellFilelistName, cellName)
            if savedCellFilelistName is None:
                # _saveCellFilelist() already printed messages
                continue
            
            oldLines = parseFilelist(savedCellFilelistName)
            newLines = []
            for oldLine in oldLines:
                newLine = oldLine
                if (not oldLine.startswith(('+', '-'))) and oldLine.endswith('.v'):
                    submoduleName = self._parseModuleNameFromPath(oldLine, '.v')
                    if submoduleName != cellName:
                        subcellFilelistName = self.getFilelistName(submoduleName)
                        # subcellFilelistName is an absolute path.  Get the relative path.
                        if subcellFilelistName is not None:
                            subcellFilelistRelName = subcellFilelistName[
                                                        len(self._ws.path) + 1:]
                            newLine = "-f {}{}".format(self.rootPrefix,
                                                        subcellFilelistRelName)
                            logging.info ("Converting the line:\n"
                                          "        {}\n"
                                          "    to:\n"
                                          "        {}"
                                "".format(oldLine, newLine))
                            if not os.path.exists(subcellFilelistName):
                                logging.warn ("The filelist in the converted line:\n"
                                              "        {}\n"
                                              "    does not exist."
                                              "".format(newLine))
        
                newLines.append(newLine)

            newLines.append("")
            self._writeListToFile(newLines, cellFilelistName)

    def _saveCellFilelist(self, cellFilelistName, cellName):
        '''Save the filelist for the specified cell to `cellName.oldstyle.f`.

        Return the file name to which it was saved, or `None` if it could not
        be saved.  Print diagnostic messages.
        '''
        if cellFilelistName is None:
            logging.error ("The filelist for cell '{}' cannot "
                           "be converted because '{}'\n"
                           "    is not a single-cell IP or a cell defined in any "
                           "cell_names.txt file in the workspace."
                           "".format(cellName, cellName))
            return None
        if not os.path.exists(cellFilelistName):
            logging.error ("Filelist '{}' for cell '{}' does not "
                           "exist and will be skipped.'\n"
                           "".format(cellFilelistName, cellName))
            return None
        savedCellFilelistName = cellFilelistName[:-len('.f')] + '.oldstyle.f'
        logging.info("\n"
              "Saving old style filelist:\n"
              "        {}\n"
              "    as:\n"
              "        {}".format(cellFilelistName, savedCellFilelistName))
        try:
            os.rename(cellFilelistName, savedCellFilelistName)
        except OSError as err:
            logging.error("Cannot save filelist '{}' as '{}', because\n"
                  "    {}."
                  "    Perhaps this is because you have not done 'icmp4 edit {}'."
                  "".format(cellFilelistName, savedCellFilelistName, err,
                            cellFilelistName))
            return None
        return savedCellFilelistName

    def expandCells(self, cellNames, doRtllec=False):
        '''Recursively expand the filelists for the specified cells.
        
        If you want to read the list of cells from a file, use
        `parseCellListFile()` to parse a cell list file into a list of modules.
        '''
        assert (self._deliverableName == 'RTL') if doRtllec else True, \
            "The --rtllec option can only be used with deliverable RTL"
        self._doRtllec = doRtllec

        self._doneFilelists.clear()
        self._filelistDepth = 0
        lines = []
        if self.initialFilelist is not None:
            fakeFilelistLine = '-f {}'.format(self.initialFilelist)
            subLines = self._expandRecursive(fakeFilelistLine)
            lines.extend(subLines)
            
        for cellName in cellNames:
            if cellName not in self.cellNames:
                raise dmError("A filelist cannot be created for cell '{}' because '{}'\n"
                    "    is not a single-cell IP or a cell defined "
                    "in any cell_names.txt file in the workspace."
                    "".format(cellName, cellName))
            # _expandRecursive() takes a filelist line, so make up one
            cellFilelistName = self.getFilelistName(cellName)
            # The main purpose of this is to add cellFilelistName to self._doneFilelists
            if self._isFilelistDone(cellName):
                # A duplicate in cellNames is inappropriate, but not enough for an error
                continue
            
            fakeFilelistLine = '-f {}'.format(cellFilelistName)
            subLines = self._expandRecursive(fakeFilelistLine)
            lines.extend(subLines)

        if self.extraFiles:
            lines.append('// Start extra files')
            lines.extend(self.extraFiles)
            lines.append('// End extra files')
#        self.checkResult(lines)
        lines.append("")
        linesWithDuplicatesCommented = self._commentOutDuplicates(lines)
        self._writeListToFile(linesWithDuplicatesCommented, self._outputFileName)
    
    def _expandRecursive(self, superLine):
        '''If the specified line from the filelist is a `-f` option, recursively
        expand it and return the resulting lines.
        
        Otherwise, return the specified line.
        '''
        lines = []
        
        filelistName = self._parseFilelistFromLine(superLine)
        if filelistName is None:
            # This is not a recursive -f filelist call
            if superLine.startswith(('+', '-')):
                # This is some VCS option other than -f
                lines.append(superLine)
            else:
                # This is an ordinary Verilog file name
                moduleName = self._parseModuleNameFromPath(superLine, '.v')
                blackboxFileName = self.getBlackboxFileName(moduleName)
                if blackboxFileName is not None:
                    lines.append('// substitute black box for {}'.format(superLine))
                    lines.append(blackboxFileName)
                else:
                    editedSuperLine = self._editCellVerilogFilePath(superLine)
                    lines.append(editedSuperLine)
        else:
            # This is a recursive -f filelist call
            if self._isFilelistDone(filelistName):
                # This filelist has already been expanded
                lines.append('// duplicate {}'.format(superLine))
            else:
                # This filelist has not yet be expanded
                moduleName = self._parseModuleNameFromPath(filelistName, '.f')
                blackboxFileName = self.getBlackboxFileName(moduleName)
                if blackboxFileName is not None:
                    # It's a black box, so substitute rather than expand
                    lines.append('// substitute black box for {}'.format(superLine))
                    lines.append(blackboxFileName)
                else:
                    self._checkFilelist(filelistName) # Can raise exception
                    lines.append(self._getFilelistStartComment(filelistName))
                    filelistLines = self.getFilelistLines(filelistName, self._ws.path)
                    for filelistLine in filelistLines:
                        subLines = self._expandRecursive(filelistLine)
                        lines.extend(subLines)
                    lines.append(self._getFilelistEndComment(filelistName))
        return lines
    
    def _isFilelistDone(self, filelistName):
        '''Return `True` if this method has ever been run on the specified
        filelist.
        '''
        if filelistName in self._doneFilelists:
            return True
        self._doneFilelists.add(filelistName)

    def _editCellVerilogFilePath(self, pathName):
        '''Edit the given path according to:
        
        * Whether RTLLEC file needs to be used
        '''
        if self._doRtllec:
            rtllecPathName =  self._getRtllecPathName(pathName)
            if os.path.isfile(rtllecPathName) and os.access(rtllecPathName, os.R_OK):
                pathName = rtllecPathName
        # Add more edits here.
        return pathName

    def _getFilelistStartComment(self, filelistName):
        '''Return a comment indicating that a new recursive filelist is being
        started.
        '''
        self._filelistDepth += 1
        dots = '.' * self._filelistDepth
        return '// {} Beginning filelist {}'.format(dots, filelistName)
    
    def _getFilelistEndComment(self, filelistName):
        '''Return a comment indicating that a recursive filelist has ended.'''
        dots = '.' * self._filelistDepth
        self._filelistDepth -= 1
        return '// {} Ending filelist {}'.format(dots, filelistName)

    @classmethod
    def _getRtllecPathName(cls, pathName):
        '''Return the RTLLEC path name corresponding to the given RTL path.
        
        TO_DO: This replaces the first '/rtl/', so there may be trouble if there
        are multiple occurrences of '/rtl/'.
        
        >>> GenCompositeFilelist._getRtllecPathName('/path/to/workspace/rtl/ip1.v')
        '/path/to/workspace/rtllec/ip1.v'
        >>> GenCompositeFilelist._getRtllecPathName('/path/to/workspace/notrtl/ip1.v')
        '/path/to/workspace/notrtl/ip1.v'
        >>> GenCompositeFilelist._getRtllecPathName('/path/to/workspace/rtl/rtl/ip1.v')
        '/path/to/workspace/rtllec/rtl/ip1.v'
        '''
        return pathName.replace('/rtl/', '/rtllec/', 1)

    @classmethod
    def parseCellListFile(cls, fileName):
        '''Parse the cell list file and return a list of the cell names that it
        contains.
        
        As a convenience for working with the command line parser, return the
        empty list if the file name is `None`.
        
        Only the first token on each line is used so that this is compatible
        with a `cell_names.txt` file.
        '''
        if fileName is None:
            return []
        lines = parseCellNamesFile(fileName)
        moduleNames = []
        for line in lines:
            tokens = line.split()
            moduleNames.append(tokens[0])
        return moduleNames
    
    @classmethod
    def _parseModuleNameFromPath(cls, path, fileExtension):
        '''Return the module name parsed from the specified file with the
        specified file name extension.

        >>> GenCompositeFilelist._parseModuleNameFromPath('/path/to/module.v', '.v')
        'module'
        >>> GenCompositeFilelist._parseModuleNameFromPath('module.v', '.v')
        'module'
        >>> GenCompositeFilelist._parseModuleNameFromPath('module.output.v', '.v')
        'module'

        Return `None` if the module name cannot be extracted.

        >>> GenCompositeFilelist._parseModuleNameFromPath('/path/to/file.v', '.vs')
                
        '''
        assert not path.startswith(('+', '-')), 'Path name must not be a VCS option'
        assert fileExtension.startswith('.'), "File extension must start with '.'"
        if not path.endswith(fileExtension):
            # Wrong file type
            return None
        fileName = os.path.basename(path)
        moduleName = fileName[:fileName.index('.')]
        return moduleName

    @classmethod
    def _parseFilelistFromLine(cls, line):
        '''Parse the filelist name from the specified line of the format::
        
            -f filelistName
        
        >>> GenCompositeFilelist._parseFilelistFromLine('-f filelist.f')
        'filelist.f'

        If the line is not this format, return `None`.

        >>> GenCompositeFilelist._parseFilelistFromLine('verilogFile.v') # Returns None

        '''
        tokens = line.split()
        if tokens[0] == '-f' and len(tokens) == 2:
            return tokens[1]
        return None

    @classmethod
    def getFilelistLines(cls, 
                         filelistFileName, 
                         workspacePath=None, 
                         doKeepVCSOptions=True):
        """Return a list of the lines appearing in the specified filelist file.
        
        A filelist contains file paths, one per line.  Every path is expected to
        start with "wkspace_root/", followed by a path within a workspace.
        
        Each line will be adjusted to convert the prefix "wkspace_root/" to an
        absolute path.
        
        A filelist can contain comments.  Comments start at,
        
        * `//` at the beginning of the line
        * `//` surrounded by white space

        Comments terminate at the end of the line.
        
        When the `doKeepVCSOptions` argument is True (the default), include
        lines that begin with '-' or '+' after removing leading white space.
        If `doKeepVCSOptions` is false, discard them.
        
        Use the `dmx.dmlib.parsers.parseFilelist()` function if you want to merely
        parse the filelist file and discard comments without adjusting the paths.
        """
        if workspacePath is None:
            workspacePath = ExpandFilelistBase.workingDirNameDefault
        outputLines = []
        for line in parseFilelist(filelistFileName, doKeepVCSOptions):
            outputLines.append(cls._adjustLinePath(line, workspacePath))
        return outputLines

    @classmethod
    def _adjustLinePath(cls, line, workspacePath):
        '''Adjust the input line according to special circumstances like +incdir+.'''

        # Expand env vars; See http://fogbugz.altera.com/default.asp?215840 
        line = _replaceEnvVarMatches (line, os.environ)
        
        if not line.startswith(('-', '+')):
            # line is just a path, not a vcs option
            return cls.adjustPath(line, workspacePath)
        
        if line.startswith('-v'):
            # Remove the -v and process as an ordinary file
            tokens = line.split()
            return cls.adjustPath(tokens[1], workspacePath)
        
        if line.startswith(('-f', '-y')):
            tokens = line.split()
            return "{} {}".format(tokens[0], cls.adjustPath(tokens[1], workspacePath))

        if line.startswith('+incdir+'):
            adjustedIncDirs = []
            incDirs = line.split('+')
            for pathName in incDirs[2:]:
                adjustedIncDirs.append(cls.adjustPath(pathName, workspacePath))
            return '+incdir+{}'.format('+'.join(adjustedIncDirs))
        
        # It's a VCS option that needs no adjustment
        return line

    @classmethod
    def adjustPath(cls, path, workspacePath, doRequireRootPrefix=True):
        '''Return the absolute path corresponding to the argument `path`:
        
        If `path` is already an absolute path, return it as-is irrespective
        of `workspacePath`:
        
        >>> GenCompositeFilelist.adjustPath('/path/to/workspace/ip1/rtl/one.v', '/unused')
        '/path/to/workspace/ip1/rtl/one.v'
        
        If `path` begins with "wkspace_root/", remove "wkspace_root/" and
        prepend the specified `workspacePath`.
        
        >>> GenCompositeFilelist.adjustPath('wkspace_root/ip1/rtl/one.v', '/path/to/workspace')
        '/path/to/workspace/ip1/rtl/one.v'
        
        >>> actual = GenCompositeFilelist.adjustPath('wkspace_root/ip1/rtl/one.v', 'relative/path/to/workspace')
        >>> expected = os.path.abspath(os.path.join(os.path.curdir,
        ...                            'relative/path/to/workspace/ip1/rtl/one.v'))
        >>> actual == expected
        True
        
        Otherwise, raise an exception because all paths in a filelist must
        begin with "wkspace_root/".
        
        >>> actual = GenCompositeFilelist.adjustPath('ip1/rtl/one.v', '/path/to/workspace') #doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        dmError: ... must begin with ...

        However, when the `doRequireRootPrefix` argument is `False`, relax the
        requirement that the path begin with "wkspace_root/":
        
        >>> actual = GenCompositeFilelist.adjustPath('ip1/rtl/filelist/one.f', '/path/to/workspace', doRequireRootPrefix=False )
        >>> expected = os.path.abspath(os.path.join('ip1/rtl/filelist/one.f'))
        >>> actual == expected
        True
        '''
        if os.path.isabs(path):
            return path
        if path.startswith(cls.rootPrefix):
            fullPathName = os.path.join(workspacePath, path[len(cls.rootPrefix):])
        else:
            if doRequireRootPrefix:
                raise dmError("Path '{}' in filelist must begin with '{}'.".
                                 format(path, cls.rootPrefix))
            fullPathName = path
        return os.path.abspath(fullPathName)

