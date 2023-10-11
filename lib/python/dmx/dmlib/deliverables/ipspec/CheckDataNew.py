#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/deliverables/ipspec/CheckDataNew.py#1 $

"""
The unneeded_deliverables file should be validated by ensuring 
all entries are valid deliverables. The IPSPEC deliverable must not be listed.

See also: http://fogbugz/default.asp?238224 (Enhancement request)

"""

from builtins import str
from builtins import object
import dmx.dmlib.deliverables.utils.General as General
import dmx.dmlib.parsers
import dmx.ecolib.ecosphere

import os
import logging
import glob
LOGGER = logging.getLogger(__name__)

class Check(object): #pylint: disable-msg=R0904
    """Data check for deliverable IPSPEC"""
    def __init__(self, project, ip, cell, ipobj=None, deliverableobj=None, workspace=None, roadmap=''):
        self.workspace = workspace
        self.family = dmx.ecolib.ecosphere.EcoSphere(workspace=workspace).get_family_for_roadmap(roadmap)
        self.ip = ip
        self.project = project
        self.cell = cell
        self.roadmap = roadmap
        self.IP = ipobj if ipobj else self.family.get_ip(self.ip, self.project)
        self.Deliverable = deliverableobj if deliverableobj else self.IP.get_deliverable('ipspec', roadmap=self.roadmap)
    
    def _test_unneededDeliverables(self):
        '''
        The unneeded_deliverables file should be validated by ensuring 
        all entries are valid deliverables. The IPSPEC deliverable must not be listed.
        
        Returns: a string containing the error text (empty string if no errors)
        '''
        unneededDeliverablesFile = [x for x in self.Deliverable.get_patterns(ip=self.ip, cell=self.cell) if 'unneeded' in x][0]
        unneededDeliverablesFile = os.path.abspath (unneededDeliverablesFile)
        
        if not os.path.isfile (unneededDeliverablesFile):
            return []# No 'unneeded_deliverables'; OK
      
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
             
        asSorted = [x.lower() for x in sorted (set (unneededDeliverables))]
       
        ### Allow libtypes defined in manifest.json to be defined in unneeded_deliverables.txt
        ### https://jira.devtools.intel.com/browse/PSGDMX-1583
        #validDeliverables = [x.deliverable for x in self.IP.get_all_deliverables(roadmap=self.roadmap)]
        validDeliverables = [x for x in dmx.ecolib.loader.load_manifest(self.family.name)]

        msg = []
        for u in asSorted:
            if u == 'ipspec':
                msg.append("'IPSPEC' cannot appear as unneeded deliverable\n")
                continue
                
            if u not in validDeliverables:
                msg.append("'%s' is not valid deliverable\n" % u)
                
        return msg


    def _test_exxessiveUnneededDeliverables_FB250433(self):
        '''
        http://fogbugz.altera.com/default.asp?250433
            glob <IP>/ipspec/*.unneeded_deliverables.txt'
            Verify that * expansion is subset of 'topCells'
            Only do it once for 'topCells'
        '''
        unneededDeliverablesFile = [x for x in self.Deliverable.get_patterns(ip=self.ip, cell=self.cell) if 'unneeded' in x][0]

        pattern = unneededDeliverablesFile.replace ('/ipspec/' + self.cell + '.', 
                                                    '/ipspec/' + '*'                + '.')
        
        abs_pattern = os.path.abspath (pattern)
                                      
        actualUnneededDeliverableFiles = glob.glob (abs_pattern)
        
        expectedUnneededDeliverables = []
        cells = self.IP.get_cells_names()
        for tc in cells:
            expectedUnneededDeliverables.append (abs_pattern.replace ('*', tc))
        
        excessiveUnneededDeliverables = set (actualUnneededDeliverableFiles) - \
                                        set (expectedUnneededDeliverables)
                                        
        msg = []
        if excessiveUnneededDeliverables:
            msg.append("Files without corresponding top cells (FB:250433):\n  " + "\n  ".join (excessiveUnneededDeliverables))
            
        return msg


    def _test_elementsMoleculesMatch_FB238224_1 (self):
        '''
        1. When both $cell.molecules.txt and $cell.elements.txt exist for a $cell, 
        then $cell.molecules.txt must contain one entry and that entry must be $cell        
        
        Returns: a string containing the error text (empty string if no errors)
        '''
        # Read 'molecules':
        moleculesFile = [x for x in self.Deliverable.get_patterns(ip=self.ip, cell=self.cell) if '{}.molecules.txt'.format(self.cell) in x][0]
        moleculesFile = os.path.abspath (moleculesFile)
        if not os.path.isfile (moleculesFile):
            return [] # No 'moleculesFile'; OK
        molecules = dmx.dmlib.parsers.parseCellNamesFile (moleculesFile)
        assert type (molecules) is list
        
        # Read 'elements':
        elementsFile = [x for x in self.Deliverable.get_patterns(ip=self.ip, cell=self.cell) if '{}.elements.txt'.format(self.cell) in x][0]
        elementsFile = os.path.abspath (elementsFile)
        if not os.path.isfile (elementsFile):
            return [] # No 'elements'; OK
        
        elements = dmx.dmlib.parsers.parseCellNamesFile (elementsFile)
        assert type (elements) is list
        
        errorMsg = ("When both $cell.molecules.txt and $cell.elements.txt exist for \n"
                    "   a $cell, then $cell.molecules.txt must contain exactly one \n" 
                    "   entry, and that entry must be $cell (FB238224-1).\n")
        
        cellName = self.cell

        if len (molecules) != 1 or molecules [0] != cellName:
            err = errorMsg + "  molecules == " + str (molecules) + "\n"
            logging.error (err)
            return [err]

# The following code was placed incorrectly and used to cause http://fogbugz/default.asp?305847         
#        if len (elements) != 1 or elements [0] != cellName:
#            err =  errorMsg + "  elements == " + str (elements) + "\n"
#            logging.error (err)
#            return err 
        
        return [] # All OK  
             
    def _test_elementsMoleculesMatch_FB238224_2 (self):
        '''
        2. Entries in molecules or elements list should be of the form 
        cellname or libname cellname. Any other formats should be flagged as an error.
        
        Returns: a string containing the error text (empty string if no errors)
        '''
        errorsSoFar = ''
        for itemToCheck in ('molecules', 'elements'):
            theFile = [x for x in self.Deliverable.get_patterns(ip=self.ip, cell=self.cell) if itemToCheck in x][0]

            theFile = os.path.abspath (theFile)
            if not os.path.isfile (theFile):
                continue # These are optional
            
            items = dmx.dmlib.parsers.parseCellNamesFile (theFile)
            assert type (items) is list
            
            for i in items:
                tokens = i.split()
                if not (1 <= len (tokens) <= 2):
                    errorsSoFar += "    " + itemToCheck + ": '" + str (i) + "'\n"
                    
        if not errorsSoFar:
            return [] # OK
        
        err = ("Entries in molecules or elements list should be of the form: \n" 
               "   cellname or libname cellname. Any other formats should be \n" 
               "   flagged as an error (FB238224-2):\n") + errorsSoFar
               
        return [err]
    
    
    def run(self):
        msg = (self._test_unneededDeliverables() +
               self._test_elementsMoleculesMatch_FB238224_2() + 
               self._test_exxessiveUnneededDeliverables_FB250433())               
        return msg
                   
    
