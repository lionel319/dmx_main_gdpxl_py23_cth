#!/usr/bin/env python

import sys, os
import re
import logging

LOGGER = logging.getLogger(__name__)

class RevisionError(Exception): pass

class Revision(object):  
    def __init__(self, family, product, revision, preview = True):
        self._family = family
        self._product = product
        self._revision = "rev{}".format(revision)
        self._preview = preview

    @property
    def name(self):
        return self._revision
    
    @property
    def family(self):
        return self._family

    @property
    def product(self):
        return self._product        

    @property
    def revision(self):
        return self._revision

    ## Preloads local variables
    ##
    ##
    ## @param self The object pointer.         
    def _preload(self):
        pass
        
    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{}".format(self._revision)
