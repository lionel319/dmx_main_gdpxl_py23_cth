#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/MoleculeCollector.py#1 $

"""
MoleculeCollector collects molecule information for a given IP using cell_names.txt, molecules.txt and/or elements.txt found in its IPSPEC directory 

Command Line Interface
=======================
`MoleculeCollector` is exposed as a command line application as the
:doc:`moleculecollector`.
"""

#import os
#from dmx.dmlib.Manifest import Manifest
from dmx.dmlib.dmError import dmError

class MoleculeCollector(object):
    ''' 
    Instantiate a timing molecule collector to collect timing molecule names from the current IP's IPSPEC directory contents.
    Argument `ws` may be `ICManageWorkspace` or for testing, `ICManageWorkspaceMock`.
        '''
    def __init__(self, ws):
        self._ws = ws
        self.moleculeList = set()
                 
    def collectMolecules(self,program):
        '''Initiates the function call to collect timing molecule names from molecule and elements.txt files.
        Identifies top IP Name for this workspace based on the workspace argument passed to this function.
        Reads in cell_names.txt file in the IPSPEC directory in the given workspace.
        Iterates over the cell names specified in IPSPEC/cell_names.txt and then issues a call to collectMoleculeList function''' 
                        
        topIpName= self._ws.ipName
        cellNamesList=self._ws.getCellsInList(topIpName, 'cell_names')
               
        if len(cellNamesList)> 0:
            for name in cellNamesList:
                if len(name.split()) > 1:
                    raise dmError("Entry in cell_names.txt must be in <cellname> format.\n"
                        "    Found '{}'\n"
                        "".format(name))
                else:
                    tmp=self.collectMoleculeList(topIpName, name, program)
            return tmp
        else:
            raise dmError("cell_names.txt doesn't exist for '{}'.\n"
                "".format(topIpName))

    
    def collectMoleculeList(self, ipName,cellName, program):
        '''Collects timing molecule names from molecules.txt or elements.txt files
        Reads in ipName.molecules.txt and ipName.elements.txt files using getCellsInList function
        A set containing timing molecule names is returned if the file is found and an empty set is returned if the file is not found or is empty
        
        If both elements.txt and molecule.txt file have molecule name(s), then the timing molecule names in elements.txt is collected
        If molecule.txt has molecule names and elements.txt is empty, then the timing molecule names in molecules.txt is collected
        If both files are absent, then an error message is issued and the program terminates
        
        The collected timing molecule list is iterated -
        If the length of an entry is > 2, an error is issued stating "ERROR: Entry in molecule list and elements list file must be either the cellname or libname cellname. Found: '%s'" %(name)"     
        If the length of an entry is 2, which means the entry is in libname cellname format, a call is issued back to this same function
        If the length of an entry is 1, which means it is a leaf cell, the name is stored in the dataStructure that stores the final molecule list names.
             
        '''
    
        tmp1=self._ws.getCellsInList(ipName, 'molecules', cellName)
        tmp2=self._ws.getCellsInList(ipName, 'elements', cellName)

        if len(tmp1)> 0 and len(tmp2) >0:
            if len(tmp1) > 1:
                raise dmError("'{}'.molecules.txt must have only one entry since it also has '{}'.elements.txt.\n".format(cellName, cellName))
            else:
                if cellName not in tmp1:
                    raise dmError("{}.molecules.txt must contain only one entry which must be {} since {}.elements.txt also exists. Molecules.txt contains {}\n".format(cellName, cellName, cellName, tmp1))
            if program == 'lvs':
                self.moleculeList.add(cellName)
                namesList=tmp2
            else:
                namesList=tmp1
            
        elif len(tmp1) > 0 and len(tmp2) == 0:
            namesList=tmp1
        else:
            raise dmError("Either molecule list or element list must be present for '{}'.\n".format(cellName))
                       
        for name in namesList:
            name=name.split()
            if len(name) > 2:
                raise dmError("Entry in molecules or elements list must be in <cellname> or <libname> <cellname> format.\n"
                        "    Found '{}'\n"
                        "".format(name))
            elif len(name) == 2:
                self.collectMoleculeList(name[0], name[1], program)
            else:
                self.moleculeList.add(name[0])
        return self.moleculeList




    def parseCellLists(self, listNames):
        
        '''Parses file containing list of newline separated cell names and returns a set containing the parsed cell names 
        '''
        dataStruct = set([])
        for eachlist in listNames:
            filehandle = open(eachlist, 'r')
            for eachline in filehandle:
                eachline=eachline.strip()
                if len(eachline.split()) > 1:
                    raise dmError("Every entry in '{}' expected to have one cellname per line. \n"
                        "Found '{}'\n"
                        "".format(eachlist, eachline))
                else:
                    dataStruct.add(eachline)
            filehandle.close()
        return dataStruct



        
