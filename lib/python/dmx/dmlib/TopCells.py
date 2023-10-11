#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/TopCells.py#1 $

# ('XXX'): pylint: disable = W0511

"""
Various aspects about dealing with 'top cells' for vp, including
(but probably not limited) to 
   http://fogbugz.altera.com/default.asp?113877
  
The 'top cells' file is: 
<pattern id="cell_names">
    &ip_name;/ipspec/cell_names.txt
</pattern>
     
   
Here's an excerpt:
File 'cellnames.txt' in deliverable IPSPEC (if present) specifies both the names 
of the top-cell names as well as optional restrictions of the set of deliverables, 
on per-cell basis.

The format of the file is ascii, with one cell per line.

The general syntax of each line is:

<cell>
<cell> &= <deliverable_subset>
<cell> -= <deliverable_subset>

<deliverable_subset> is non-empty coma-separated list of deliverables.

Example:

myTopCell &= RTL, RDF  # restrict checker to RTL and RDF
otherTopCell -= RDF    # skip *any* RDF- and RDF_XXX checks


Spaces and tabs are allowed outside of cell- and deliverable- names. They are ignored

A '#' character means everything till the end of the line is a comment.

Empty lines are allowed and ignored.

The meaning of each line is:

(A) <cell>
The check for the particular cell will use the full set of the deliverables specified on  the command line. This is the existing behaviour.

(B) <cell> &= <deliverable_subset>
The cell is checked agains the (set) intersection of <deliverable_subset> and the command-line set

(C) <cell> -= <deliverable_subset>
The cell is checked against the difference between command-line set and <deliverable_subset>
"""

from builtins import str
from builtins import range
from past.builtins import basestring
from builtins import object
import string # (deprecated; actualy pylint bug): pylint: disable = W0402
import os
import logging
logger = logging.getLogger(__name__)

##########################################################################################
def _parseDeliverableList (commaSeparatedDeliverables, allValidDeliberables):
    '''
    Parses 'A,B,C' as ['A', 'B', 'C']
    Returns: 
        string list if OK, 
        error text (a string) on errors
    '''
    commaSeparatedDeliverables = commaSeparatedDeliverables.replace (',',' ')
    tokens = [x.upper() for x in commaSeparatedDeliverables.split()]
    
    if len (tokens) != len (set (tokens)):
        return 'duplicated'
    
    invalid = ''
    for t in tokens:
        if not t in allValidDeliberables:
            if invalid:
                invalid += ' '
            invalid += "invalid: %s" % t
    
    if invalid:
        return invalid
    
    return tokens # OK
    
     

##########################################################################################
class ParsedLine (object):
    '''
    Represent a parsed representation of a single line in cell_names.txt 
     ''' 
    def __init__ (self, 
                  lineNumber,  # line # in file 
                  fullText,    # as in file, WITHOUT the '\n'   
                  cellName = None, 
                  operator = None,  # one of: None, '&=' and '-=' 
                  rhs      = None,  # the rhs side, list of strings (deliverable names)
                  comment  = None,  # Anything after (and including) a '#'
                  error    = None): # error text by
        self.lineNumber_ = lineNumber
        self.fullText_   = fullText
        self.cellName_   = cellName
        self.operator_   = operator
        self.rhs_        = rhs
        self.comment_    = comment
        self.error_      = error
        
    def __str__(self):
        ret = {'cell'   : self.cellName_,
               'op'     : self.operator_,
               'rhs'    : self.rhs_,
               'comment': self.comment_,
               'error'  : self.error_}
        
        for k in list(ret.keys()):
            if not ret[k]:
                del ret[k]
        
        s = str (ret)[1:-1]
        return s
                 

    @staticmethod 
    def parseLine (lineNo, lineText, allValidDeliverables, existingCellsSoFar):
        ''' 
        Parse a line. Returns a ParsedLine.
        The additional parameters are used for checking for:
            - invalid deliverables
            - duplicated cells
        ''' 
        assert lineNo >= 0 and type (lineText) is type('')
        assert type (allValidDeliverables) in [list, set]
        assert type (existingCellsSoFar) in [list, set]
        
        if lineText and lineText [-1] == '\n':
            lineText = lineText [:-1]

        fullText = lineText
        comment = None
        cellName = None
        operator = None
        rhs = None
        
        
        se = "Syntax error"
        
        # Recognize/stript comments
        for commentPrefix in ['#', '//']:
            if commentPrefix in lineText:
                commentIndex = lineText.find (commentPrefix)
                comment  = lineText [commentIndex:]
                lineText = lineText [:commentIndex]
            
#        noSpaces = lineText.translate (string.maketrans('',''), 
#                                       string.whitespace)
        
        eq = lineText.find ('=')
        if eq != -1:
            if eq == 0:
                return ParsedLine (lineNo, fullText, error = se)
            elif lineText[eq-1] == '-':
                operator = '-='
            elif lineText[eq-1] == '&':
                operator = '&='
            else:
                return ParsedLine (lineNo, fullText, error = se)
                
            cellName = lineText [:eq-1].strip()
            
            rhsRaw = lineText [eq + 1:]
            rhsParsed = _parseDeliverableList (rhsRaw, allValidDeliverables)
            if type (rhsParsed) is type(""): # so error
                return ParsedLine (lineNo, 
                                   fullText, 
                                   error = "Rhs deliverables: " + rhsParsed)
            assert type (rhsParsed) is list
            rhs = rhsParsed
        else:
            cellName = lineText.strip()

        assert type (cellName) is type("")
        # Check cell name for invalid symbols:
        invalidChars = set (string.punctuation)
        invalidChars.remove('_')
    
        for c in cellName:
            if c in invalidChars:
                return ParsedLine (lineNo, fullText, se)
                
             
        # Check cell name for duplication
        error = None
        if cellName:
            if cellName in existingCellsSoFar:
                error = 'Duplicated cell name %s' % cellName 

        if not cellName:
            cellName = None
        
        # all done:
        return ParsedLine (lineNo, 
                           fullText,
                           cellName, 
                           operator, 
                           rhs,
                           comment,
                           error)
                
    @staticmethod
    def _test_ParseLine():
        '''
        Unittest for 'parseLine()'
        ''' 
        validDeliverables = ['A','B','C']
        existingCells = ['1','2']
        
        parse = ParsedLine.parseLine
        
        tests = [('',''),
                 ('#comment',     "'comment': '#comment'"),
                 ('3',            "'cell': '3'"),
                 ('2',            "'cell': '2', 'error': 'Duplicated cell name 2'"), 
                 ('3 &= A',       "'cell': '3', 'rhs': ['A'], 'op': '&='"),
                 ('3 -= A, B',    "'cell': '3', 'rhs': ['A', 'B'], 'op': '-='"), 
                 ('3 -= A   B ',  "'cell': '3', 'rhs': ['A', 'B'], 'op': '-='"), 
                 ('3 += A',       "'error': 'Syntax error'"), 
                 ('3 &= A, A',    "'error': 'Rhs deliverables: duplicated'"),
                 ('3 &= A, B, F', "'error': 'Rhs deliverables: invalid: F'")
                 ]
                 
        for src,expected in tests:
            actual = str (parse (1, src, validDeliverables, existingCells))
            if actual != expected:
                logger.info (actual)
                logger.info (expected)
            assert actual == expected   
            
    def deliverableIsAllowed (self, deliverableName):
        line = self
        if line.operator_ is None:
            return True
        elif line.operator_ == '&=':
            return deliverableName in line.rhs_
        elif line.operator_ == '-=':
            return deliverableName not in line.rhs_
        else:
            # We shouldn't get there
            assert False
            
    def filterDeliverables (self, deliverableNames):
        ret = set()
        for d in deliverableNames:
            if self.deliverableIsAllowed(d):
                ret.add (d)
        return ret

class TopCells(object):
    '''Represents the collection of the top cells'''
    
    def __init__ (self, 
                  ipName,           # None or string
                  topCellFileName,  # None or string
                  singleCellName,   # None or string  
                  validDeliverableNames): # string set
        '''
        Tries to create one out of whatever is thrown at it.
        Never fails (expect for 'non existing topCellFilename').
        '''        
        assert ipName is None or isinstance(ipName, basestring), \
            "ipName argument must be a string or None"
        assert topCellFileName is None or isinstance(topCellFileName, basestring), \
            "topCellFileName argument must be a string or None"
        assert singleCellName is None or isinstance(singleCellName, basestring), \
            "singleCellName argument must be a string or None"
            
        if not topCellFileName and not singleCellName:
            singleCellName = ipName
            
        assert singleCellName or topCellFileName
        
        self.ipName_ = ipName
        self.topCellFileName_ = topCellFileName
        self.singleCellName_ = singleCellName
        
        self.allErrors_ = {}  # Dictionary line no->error text  
        self.allCells_ = {}   # Dictionary: cell name->ParsedLine
        self.parsedLines_ = []
        
        if singleCellName: # Has precedence over 'topCellFileName'
            pl = ParsedLine (lineNumber = 0, 
                             fullText   = singleCellName,
                             cellName =   singleCellName)
            self.parsedLines_ = [pl]
            self.allCells_ [singleCellName] = pl
        else:
            with open (topCellFileName) as f:
                lines = f.readlines()
                
                for i in range (len (lines)):
                    pl = ParsedLine.parseLine (
                                       lineNo               = i + 1, 
                                       lineText             = lines [i], 
                                       allValidDeliverables = validDeliverableNames, 
                                       existingCellsSoFar   = list(self.allCells_.keys()))
                    if pl.cellName_:
                        self.allCells_ [pl.cellName_] = pl
                    self.parsedLines_.append (pl)
        
        for pl in self.parsedLines_:                 
            if pl.error_:
                self.allErrors_ [pl.lineNumber_] = pl.error_
        
    def __str__(self):
        ret = '*********** TopCells ***********\n'
        
        for pl in self.parsedLines_:
            ret += '\n %3d: ' % pl.lineNumber_ + str (pl)
        
        ret += '\n\n  line count:  %d' % len (self.parsedLines_)
        ret +=   '\n  cell count:  %d' % len (self.allCells_)
        ret +=   '\n  error count: %d\n' % len (self.allErrors_)
        
        return ret

    def generateErrorString (self):
        if not self.allErrors_:
            return None
        
        ret = "'Top cells' filename: '%s'\n" % str (self.topCellFileName_)
        ret += "Errors:\n"
        
        for l in self.allErrors_:
            line = self.parsedLines_ [l-1] # Line# is 1-based
            ret += "   line #%d: %-50s: %s\n" % (line.lineNumber_, 
                                                 line.fullText_, 
                                                 line.error_)
        return ret
    
    def filterDeliverables (self, cellName, deliverableNames):
        line = self.allCells_ [cellName]
        ret = line.filterDeliverables (deliverableNames)
        return ret
    
    @staticmethod
    def _testTopCells():
        'A unit test'
        
        validDeliverableNames = ['A','B','C','D','E','F']
        
        ts1 = TopCells ('ip', 
                        topCellFileName = None, 
                        singleCellName = None,
                        validDeliverableNames = validDeliverableNames)
        logger.info (ts1)
        
        ts2 = TopCells ('ip', 
                        topCellFileName = 'shouldntMatter', 
                        singleCellName = 'single',
                        validDeliverableNames = validDeliverableNames)
        logger.info (ts2)
        
        fn3 = '../inputData/IPSPEC/test/TopCells3.txt'
        if os.path.exists(fn3):
            ts3 = TopCells ('ip', 
                            topCellFileName = fn3,
                            singleCellName = None, 
                            validDeliverableNames = validDeliverableNames)
            logger.info (ts3)
            logger.info (ts3.generateErrorString())
            
        fn4 = '../inputData/IPSPEC/test/TopCells4.txt'
        if os.path.exists(fn4):
            ts4 = TopCells ('ip', 
                            topCellFileName = fn4,
                            singleCellName = None, 
                            validDeliverableNames = validDeliverableNames)
            logger.info (ts4)
            logger.info (ts4.generateErrorString())


########################### Legacy/compatibility code ####################################        
        
##########################################################################################
def getTopCellsFileNameForPath (ipName, workspacePath):
    '''Returns the full name of the 'cell_names.txt' file for a given workspacePath'''
    fileName = os.path.join( ipName, 'ipspec', 'cell_names.txt')
    fullName = os.path.join(workspacePath, fileName)
    return fullName
    

##########################################################################################    
def getCellNamesForIPNameAndPath(ipName, path, quiet, returnIpIfEmpty):
    '''
    This is the class method version of `getCellNamesForIPName()` for
    use when there is no instance of `workspace` available.
    
    See `getCellNamesForIPName()` for documentation and tests.
    '''
    cellNameFileName = getTopCellsFileNameForPath (ipName, path)
    if not os.path.exists(cellNameFileName):
        if returnIpIfEmpty:
            if not quiet:
                logger.info ("VpInfo: Using cell name = IP name = '{}' "
                              "because there is no\n"
                              "    cell name file '{}'.".
                                format(ipName, cellNameFileName))
            return set([ipName])
        else:
            return set()
    
    ts = TopCells (ipName          = ipName,  
                   topCellFileName = cellNameFileName, 
                   singleCellName  = None,   
                   validDeliverableNames = set())
    cellNames = list(ts.allCells_.keys())
    if not cellNames:
        if not quiet:
            logger.warning ("Warning: Using cell name = IP name = '{}' "
                             "because the cell name\n"
                             "    file '{}' contains no cell names.".
                                format (ipName, cellNameFileName))
        return set([ipName])
    
    return set(cellNames)
    
    
# Unittests
if __name__ == '__main__':
    #pylint: disable = W0212
    ParsedLine._test_ParseLine()
    TopCells._testTopCells()
    
    
        
