#!/usr/bin/env python

import sys, os
import re
import logging

LOGGER = logging.getLogger(__name__)

class ProjectError(Exception): pass

class Project(object):  
    def __init__(self, family, project, preview = True):
        self._family = family
        self._project = project
        self._preview = preview

    @property
    def name(self):
        return self._project        

    @property
    def family(self):
        return self._family

    @property
    def project(self):
        return self._project

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
        return "{}".format(self._project)
