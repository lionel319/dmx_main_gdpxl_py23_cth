#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011-2015 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/dmlib/CheckType.py#2 $

"""
Check a workspace to make sure that all files described in the deliverable manifest
set XML are present and readable.

TO_DO: The `<filelist minimum>` attribute is only checked for wildcards
recognized by Python :py:class:glob.glob`.  Namely, it does not check
the number of files matched by the `...` pattern.
"""

from __future__ import absolute_import

import os
import sys
import glob
import logging
logging = logging.getLogger(__name__)

CMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, os.getenv("DMXLIB"))
sys.path.insert(0, os.getenv("CMXLIB"))

from cmx.dmlib.CheckerBase import CheckerBase

class CheckType(CheckerBase):
    '''Construct a verifier for the specified template set XML and verify it.'''
     
    failureException = AssertionError

    def __init__(self, ipname, cell, roadmap='', prel=None, workarea=None, familyobj=None):
        super(CheckType, self).__init__(ipname, cell, workarea=workarea)
        self._deliverableName = None
        self._topCells = None # Alternatively: a list of all top cells
        self._roadmap = roadmap
        self.prel = prel

        '''
        ### These are defined in CheckerBase base-class
        self.ip_name = ipname
        self.cell_name = cell
        '''
        self.familyobj = familyobj
         
    def __str__(self):
        '''English language name of this check.'''
        return "{} type check".format(self._deliverableName)

    def checkType(self, deliverableName, verbose):
        '''
        Reset the checker and run the type check on the specified
        `deliverableName`.  This `check()` method is unique in that it has a
        `deliverableName` argument.  All the other checkers use the `check()`
        method defined in :py:class:`dm.CheckerBase`.
        
        The method returns True if the check passed, and False if it failed.
        '''
        self._deliverableName = deliverableName
        return super(CheckType, self).check(verbose)

    def _check(self):
        '''Perform a type check on the deliverable specified in the `check()`
        method,  The type check makes sure that all deliverable items exist and
        are readable.
        '''
        self._checkPattern(self._deliverableName)
        self._checkFilelist(self._deliverableName)
        if self._verbose:
            if self.isCorrect:
                logging.info("Verified that the files are present as described in "
                             "the manifest set for deliverable '{}'.".
                                format(self._deliverableName))
            else:
                logging.error ("Found problems with the files described in the manifest"
                      " set for deliverable '{}':".format(self._deliverableName))
                for error in self.errors:
                    logging.error ('  ' + error)
        return self.isCorrect

    def get_deliverable_obj(self, deliverable_name=None):
        if not deliverable_name:
            deliverable_name = self._deliverableName
        return self.familyobj.get_deliverable(deliverable_name)

    def _checkPattern(self, deliverableName):
        '''Perform a type check on the `<pattern>` items within the specified
        deliverable to make sure that all files exist and are readable.
        '''
        iptype = None

        if self.prel:
            prel_filter = '^{}$'.format(self.prel)
        else:
            prel_filter = ''

        patterns = self.get_deliverable_obj().get_patterns(ip=self.ip_name, cell=self.cell_name)
        logging.debug("patterns:{}".format(patterns))

        for pattern in patterns:
            # http://pg-rdjira.altera.com:8080/browse/DI-545
            # minimum renamed to optional and is a boolean 
            # to support backward compatibility, dmlib will read optional as boolean
            # and convert to integer
            # true = 1, false = 0
            if 'optional' in patterns[pattern]:
                minimum = 0 if patterns[pattern]['optional'] else 1
            else:                
                # Support for families that are still using minimum properties
                minimum = patterns[pattern]['minimum']
                # if minimum is blank, it's compulsory
                minimum = int(minimum) if minimum else 1

            if pattern.count('...') > 0:
                self._checkDotDotDotPattern(pattern, minimum, deliverableName)
            else:
                # patterns that contain only glob wild cards, or no wild card at all
                self._checkAsteriskPattern(pattern, minimum, deliverableName)

    def _checkAsteriskPattern(self, pattern, minimum, deliverableName):
        '''Perform a type check on a single `<pattern>` that contains only a 
        Python wild card, or no wild card at all.
        '''
        assert pattern.count('...') == 0, \
            "'...' combined with glob wild cards like '*' and '?' is not supported"

        fileNames = glob.iglob(pattern)
        count = 0
        for fileName in fileNames:
            #331883: File type check should filter out directory.
            if not os.path.isdir(fileName):
                if self._checkFile(fileName, deliverableName, 'pattern file'):
                    count += 1

        # Check the minimum number of files
        if count < minimum:
            if minimum == 1:
                self._errors.append("pattern file '{}' does not exist.".
                                        format(pattern))
                return
            self._errors.append("minimum of {} pattern "
                                 "files '{}' does not exist.".
                                 format(minimum, pattern))                
            
    def _checkDotDotDotPattern(self, pattern, minimum, deliverableName):
        '''Perform a type check on a single `<pattern>` that contains the Perforce
        '...' wild card.
        '''
        assert (pattern.count('*') == 0) and (pattern.count('?') == 0), \
            "Glob wild cards like '*' and '?' combined with '...' are not supported"

        (startDir, startFileName) = os.path.split(pattern)
        assert (startFileName.count('...') == 1) and startFileName.startswith('...'), \
                    ("'...' is only handled at the beginning of the "
                    "file name in a <pattern>")
        assert not startDir.count('...'), ("'...' in <pattern> directories "
                                          "is not supported.")
        
        count = 0
        # Strip off the leading ...
        ext = startFileName[3:]
        for root, dirs, fileNames in os.walk(startDir): 
            if dirs: pass # suppress a warning
            for fileName in fileNames: 
                if fileName.endswith(ext):
                    pathName = os.path.join(root, fileName)
                    if self._checkFile(pathName, deliverableName, 'pattern file'):
                        count += 1

        # Check the minimum number of files
        if count < minimum:
            if minimum == 1:
                self._errors.append("pattern file '{}' does not exist.".
                                       format(pattern))
                return
            self._errors.append("minimum of {} "
                                    "pattern files '{}' does not exist.".
                                format(minimum, pattern))                
            
    def _checkFilelist(self, deliverableName):
        '''Perform a type check on the `<filelist>` items within the specified
        deliverable to make sure that all filelists and the files listed within
        the filelists exist and are readable.
        '''
        filelists = self.get_deliverable_obj().get_filelists(ip=self.ip_name, cell=self.cell_name)
        logging.debug("filelists:{}".format(filelists))
        for filelist in filelists:
            # http://pg-rdjira.altera.com:8080/browse/DI-545
            # minimum renamed to optional and is a boolean 
            # to support backward compatibility, dmlib will read optional as boolean
            # and convert to integer
            # true = 1, false = 0
            if 'optional' in filelists[filelist]:
                minimum = 0 if filelists[filelist]['optional'] else 1
            else:                
                # Support for families that are still using minimum properties
                minimum = filelists[filelist]['minimum']
                # if minimum is blank, it's compulsory
                minimum = int(minimum) if minimum else 1

            # Check the files that do exist for readability
            # And count them
            filelistFileNames = glob.glob(filelist)
            count = 0
            for filelistFileName in filelistFileNames:
                if self._checkFile(filelistFileName, deliverableName, 'filelist file'):
                    # Filelist file exists and is readable
                    count += 1
                    
            # Check the minimum number of filelists
            if count < minimum:
                if minimum == 1:
                    self._errors.append("filelist '{}' does not exist.".
                                            format(filelist))
                    return
                self._errors.append("minimum of {} "
                                        "filelists '{}' does not exist.".
                                    format(minimum, filelist))                


if __name__ == "__main__":
    # Running CheckType_test.py is the preferred test method,
    # but run doctest alone if the user requests.
    import doctest
    doctest.testmod(verbose=2)
