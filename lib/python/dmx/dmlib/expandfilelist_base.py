#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/expandfilelist_base.py#1 $

"""
`ExpandFilelistBase` is the base class for the filelist expanders like
`:py:class:dmx.dmlib.ExpandFilelist` and `:py:class:dmx.dmlib.gencompositefilelist`.
"""

import sys
import logging

from dmx.dmlib.dmError import dmError

class ExpandFilelistBase(object):
    """
    Instantiate a filelist expander to expand the filelists for the specified
    deliverable, and put the result in file `outputFileName`.
    
    Relative paths in the input filelists will be adjusted to be relative to
    `workingDirName`.  If you specify '/', all paths will be made absolute
    paths. The default is the current working directory.
    
    When `deliverableName` is not 'RTL', discard VCS options that appear in the
    input filelists (VCS options begin with '-' or '+').
 
    Note that there is no restriction on the relationship between the paths
    `outputFileName` and `workingDirName`.
    
    If `otherDeliverableName` and `otherIPs` are specified:
    
    * The specified `otherDeliverableName` filelist will be used for the IPs in \
      the list `otherIPs`
    * The `deliverableName` filelist will be used for the remaining IPs 

    `dmx.dmlib.ExpandFilelist` is exposed as a command line application as the
    :doc:`expandfilelist`.  See :doc:`expandfilelist` for more detailed
    documentation.
    """
    
    workingDirNameDefault = '.'
    
    def __init__(self,
                 deliverableName,
                 outputFileName,
                 itemName):
        self._deliverableName = deliverableName.upper()
        self._doKeepVCSOptions = (deliverableName in ['RTL', 
                                                      'ABX2GLN', 
                                                      'FCVNETLIST',
                                                      'GLNPREPNR',
                                                      'GLNPOSTPNR'])
        self._outputFileName = outputFileName
        self._itemName = itemName
            
        self._missingFileExplanation = None
        self._filelistDepth = 0
        

    def _setMissingFileExplanation(self, explanation):
        """Set the explanation for an exception if one is thrown."""
        if self._missingFileExplanation is None:
            self._missingFileExplanation = explanation

    def _checkFilelist(self, filelist):
        """Check the filelist to see if it is ready to be read.
        
        Throw an exception if a problem is found.
        """
        try:
            f = open(filelist, 'r')
        except IOError:
            if self._missingFileExplanation is None:
                self._missingFileExplanation = ""
            raise dmError("Filelist '{}' does not exist or is not readable.{}"
                          "".format(filelist, self._missingFileExplanation))
        f.close()
        
    def _checkFile(self, fileName):
        """Check the file to see if it is ready to be read.
        
        Throw an exception if a problem is found.
        """
        try:
            f = open(fileName, 'r')
        except:
            if self._missingFileExplanation is None:
                self._missingFileExplanation = ""
            raise dmError("File '{}' is not readable.{}".format(fileName,
                                                                self._missingFileExplanation))
        f.close()
        
    @classmethod
    def _commentOutDuplicates(cls, lines):
        """Comment out repeated lines."""
        result = []
        seenLines = set()
        for line in lines:
            if (not line) or line.startswith('//'):
                # Always pass through empty lines and comments
                result.append(line)
            elif line in seenLines:
                result.append('// duplicate {}'.format(line))
            else:
                result.append(line)
                seenLines.add(line)
        return result
        
    @classmethod
    def _writeListToFile(cls, li, fileName):
        '''Write list `li` to the specified file, or write to stdout if `fileName` is None.'''
        if None in li:
            logging.info (str (li))
        fileContents = '\n'.join(li)
        if fileName is None:
            sys.stdout.write(fileContents)
        else:
            f = open(fileName, 'w')
            f.write(fileContents)
            f.close()

