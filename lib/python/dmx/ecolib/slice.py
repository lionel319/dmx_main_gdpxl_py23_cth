#!/usr/bin/env python

## @addtogroup ecolib
## @{

''' axc
This is documentation

@author Lionel Tan, Kevin Lim
@image html dmx.ecolib.png 

-the end-
'''

import inspect
import sys, os
import re
import logging
import dmx.ecolib.loader
import dmx.ecolib.checker
import dmx.ecolib.manifest
import dmx.ecolib.family

LOGGER = logging.getLogger(__name__)

class SliceError(Exception): pass

class Slice(object):  
    def __init__(self, family, deliverable, slice,
                 roadmap='',
                 preview=True):
        self._family = family
        self._deliverable = deliverable.lower()
        self._slice = slice
        self._preview = preview
    
        (self._pattern, self._filelist) = self._get_slice_properties()

    @property
    def name(self):
        return self._deliverable        
                
    @property
    def family(self):
        return self._family

    @property
    def deliverable(self):
        return self._deliverable

    @property
    def slice(self):
        return self._slice  
        
    @property
    def pattern(self):
        return self._pattern                  
    
    @property
    def filelist(self):
        return self._filelist            
        
    ## Preloads local variables
    ## self._checkers
    ##
    ## @param self The object pointer. 
    def _preload(self):
        pass

    ## Returns a list of file patterns for the ip/manifest/cell
    ##
    ## @param self The object pointer. 
    ## @param ip IP
    ## @param cell Cellname
    ## @return list of strings of file patterns
    def get_patterns(self, ip = None, cell = None):
        patterns = {}
        for pattern in self._pattern:
            newpattern = pattern
            if ip:
                newpattern = pattern.replace('ip_name', ip)
            if 'cell_names' not in newpattern:                      
                if cell:
                    newpattern = newpattern.replace('cell_name', cell)                
            patterns[newpattern] = self._pattern[pattern]
        return patterns

    ## Returns a list of file lists for the ip/manifest/cell
    ##
    ## @param self The object pointer. 
    ## @param ip IP
    ## @param cell Cellname
    ## @return list of strings of file lists
    def get_filelists(self, ip = None, cell = None):
        filelists = {}
        for filelist in self._filelist:
            newfilelist = filelist
            if ip:
                newfilelist = filelist.replace('ip_name', ip)
            if 'cell_names' not in newfilelist:                                            
                if cell:
                    newfilelist = newfilelist.replace('cell_name', cell)                
            filelists[newfilelist] = self._filelist[filelist]
        return filelists        

    ## Returns Slice's properties
    ##
    ## @param self The object pointer. 
    ## @return tuple of properties
    def _get_slice_properties(self):
        slices = dmx.ecolib.loader.load_slices(self._family)
        deliverable = self._deliverable.lower()
        slice = self.__repr__()
        patterns = {}
        filelists = {}
        if slice in slices:
            for pattern in slices[slice]['pattern']:
                if pattern not in patterns:
                    patterns[str(pattern)] = {}
                for key in slices[slice]['pattern'][pattern].keys():
                    if key != 'optional':
                        patterns[pattern][str(key)] = str(slices[slice]['pattern'][pattern][key])
                    else:
                        patterns[pattern][str(key)] = slices[slice]['pattern'][pattern][key]
            if 'filelist' in slices[slice]:                        
                for filelist in slices[slice]['filelist']:
                    if filelist not in filelists:
                        filelists[str(filelist)] = {}
                    for key in slices[slice]['filelist'][filelist].keys():
                        filelists[filelist][str(key)] = str(slices[slice]['filelist'][filelist][key])                        
        return (patterns, filelists)
    
    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{}:{}".format(self._deliverable, self._slice)
        
## @}        
