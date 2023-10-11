#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/deliverables/ipspec/CheckData.py#1 $

"""
The unneeded_deliverables file should be validated by ensuring 
all entries are valid deliverables. The IPSPEC deliverable must not be listed.

See also: http://fogbugz/default.asp?238224 (Enhancement request)

"""

from dm.VpNadder import VpNadder
import dm.deliverables.utils.General as General
import dm.parsers

import unittest
import os
import logging
import glob

class Check(unittest.TestCase): #pylint: disable-msg=R0904
    """Data check for deliverable IPSPEC"""
    
    def _test_unneededDeliverables(self):
        '''
        The unneeded_deliverables file should be validated by ensuring 
        all entries are valid deliverables. The IPSPEC deliverable must not be listed.
        
        Returns: a string containing the error text (empty string if no errors)
        '''
        unneededDeliverablesFile = (VpNadder.manifest). \
                                      getDeliverablePatternFirst ("IPSPEC", 
                                                                  'unneeded_deliverables')
        unneededDeliverablesFile = os.path.abspath (unneededDeliverablesFile)
        
        if not os.path.isfile (unneededDeliverablesFile):
            return ''# No 'unneeded_deliverables'; OK
      
        # Read 'unneededDeliverables'      
        unneededDeliverables = []  
        
        with open (unneededDeliverablesFile, 'r') as f:

            lines_0 = [x.strip() for x in f.readlines()]
            lines = [x for x in lines_0 
                        if (x and not x.startswith ('//')
                              and not x.startswith ('#'))]
            for l in lines:
                d_0 = General.tsplit (l, (' ', '\t', ','))
                d_1 = [x.strip().upper() for x in d_0 if x.strip()]
                unneededDeliverables += d_1
             
        asSorted = sorted (set (unneededDeliverables))
        
        validDeliverables = (VpNadder.manifest).allDeliverables
        
        msg = ''
        for u in asSorted:
            if u == 'IPSPEC':
                msg += "   'IPSPEC' cannot appear as unneeded deliverable\n"
                continue
                
            if u not in validDeliverables:
                msg += "   '%s' is not valid deliverable\n" % u
                
        return msg


    def _test_exxessiveUnneededDeliverables_FB250433(self, topCells):
        '''
        http://fogbugz.altera.com/default.asp?250433
            glob <IP>/ipspec/*.unneeded_deliverables.txt'
            Verify that * expansion is subset of 'topCells'
            Only do it once for 'topCells'
        '''
        unneededDeliverablesFile = (VpNadder.manifest). \
                                      getDeliverablePatternFirst ("IPSPEC", 
                                                                  'unneeded_deliverables')
        pattern = unneededDeliverablesFile.replace ('/ipspec/' + VpNadder.cell_name + '.', 
                                                    '/ipspec/' + '*'                + '.')
        
        abs_pattern = os.path.abspath (pattern)
                                      
        actualUnneededDeliverableFiles = glob.glob (abs_pattern)
        
        expectedUnneededDeliverables = []
        for tc in topCells:
            expectedUnneededDeliverables.append (abs_pattern.replace ('*', tc))
        
        excessiveUnneededDeliverables = set (actualUnneededDeliverableFiles) - \
                                        set (expectedUnneededDeliverables)
                                        
        msg = ''
        if excessiveUnneededDeliverables:
            msg += "Files without corresponding top cells (FB:250433):\n  "
            msg += '\n  '.join (excessiveUnneededDeliverables) 
            
        return msg


    def _test_elementsMoleculesMatch_FB238224_1 (self):
        '''
        1. When both $cell.molecules.txt and $cell.elements.txt exist for a $cell, 
        then $cell.molecules.txt must contain one entry and that entry must be $cell        
        
        Returns: a string containing the error text (empty string if no errors)
        '''
        # Read 'molecules':
        moleculesFile = (VpNadder.manifest).getDeliverablePatternFirst ("IPSPEC", 
                                                                        'molecules')
        moleculesFile = os.path.abspath (moleculesFile)
        if not os.path.isfile (moleculesFile):
            return '' # No 'moleculesFile'; OK
        molecules = dm.parsers.parseCellNamesFile (moleculesFile)
        assert type (molecules) is list
        
        # Read 'elements':
        elementsFile = (VpNadder.manifest).getDeliverablePatternFirst ("IPSPEC", 
                                                                       'elements')
        elementsFile = os.path.abspath (elementsFile)
        if not os.path.isfile (elementsFile):
            return '' # No 'elements'; OK
        
        elements = dm.parsers.parseCellNamesFile (elementsFile)
        assert type (elements) is list
        
        errorMsg = ("When both $cell.molecules.txt and $cell.elements.txt exist for \n"
                    "   a $cell, then $cell.molecules.txt must contain exactly one \n" 
                    "   entry, and that entry must be $cell (FB238224-1).\n")
        
        cellName = (VpNadder.manifest).cell_name

        if len (molecules) != 1 or molecules [0] != cellName:
            err = errorMsg + "  molecules == " + str (molecules) + "\n"
            logging.error (err)
            return err

# The following code was placed incorrectly and used to cause http://fogbugz/default.asp?305847         
#        if len (elements) != 1 or elements [0] != cellName:
#            err =  errorMsg + "  elements == " + str (elements) + "\n"
#            logging.error (err)
#            return err 
        
        return '' # All OK  
             
    def _test_elementsMoleculesMatch_FB238224_2 (self):
        '''
        2. Entries in molecules or elements list should be of the form 
        cellname or libname cellname. Any other formats should be flagged as an error.
        
        Returns: a string containing the error text (empty string if no errors)
        '''
        errorsSoFar = ''
        for itemToCheck in ('molecules', 'elements'):
            theFile = (VpNadder.manifest).getDeliverablePatternFirst ("IPSPEC", 
                                                                      itemToCheck)
            theFile = os.path.abspath (theFile)
            if not os.path.isfile (theFile):
                continue # These are optional
            
            items = dm.parsers.parseCellNamesFile (theFile)
            assert type (items) is list
            
            for i in items:
                tokens = i.split()
                if not (1 <= len (tokens) <= 2):
                    errorsSoFar += "    " + itemToCheck + ": '" + str (i) + "'\n"
                    
        if not errorsSoFar:
            return '' # OK
        
        err = ("Entries in molecules or elements list should be of the form: \n" 
               "   cellname or libname cellname. Any other formats should be \n" 
               "   flagged as an error (FB238224-2):\n") + errorsSoFar
               
        return err
    
    
    def test_ALL(self):
        msg = (self._test_unneededDeliverables() +
               self._test_elementsMoleculesMatch_FB238224_1() + 
               self._test_elementsMoleculesMatch_FB238224_2() + 
               self._test_exxessiveUnneededDeliverables_FB250433 (VpNadder.topCells))               
        if msg:
            logging.error ("VpError:\n" + msg)
            self.fail (msg)
                   
    
