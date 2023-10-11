#!/usr/bin/env python

## @addtogroup ecolib
## @{

import sys, os
import logging
import dmx.ecolib.loader
import dmx.ecolib.deliverable

LOGGER = logging.getLogger(__name__)

class PrelError(Exception): pass

class Prel(object):  

    ## load the dictionary information from prels.json
    ##
    ## @param self The object pointer. 
    ## @param family The family name (str). 
    ## @param self The prel name (str). 
    ## @return NA
    def __init__(self, family, prel, preview=True):
        self._family = family
        if not prel.startswith('prel_'):
            raise ViewError('Prel ({}) does not begin with \'prel_\'. prel must begin with \'prel_\''.format(prel))
        self._prel = prel.lower()        
        self._preview = preview
        self._deliverables = []
        
    @property
    def name(self):
        return self._prel

    @property
    def family(self):
        return self._family

    @property
    def prel(self):
        return self._prel

    ## Preloads local variables
    ## self._deliverables
    ##
    ## @param self The object pointer. 
    def _preload(self):
        self._deliverables = self._get_deliverables()        

    # Returns a list of Deliverable objects associated with the IPType
    ##
    ## @param self The object pointer. 
    ## @return list of Deliverable objects
    def _get_deliverables(self):
        if not self._deliverables:
            prelsdict = dmx.ecolib.loader.load_prels(self._family)
            for deliverable in prelsdict[self._prel]:
                self._deliverables.append(dmx.ecolib.deliverable.Deliverable(self._family, str(deliverable.lower())))

        return self._deliverables                        

    ## Return a list of deliverable objects for this view
    ##
    ## @param self The object pointer. 
    ## @return [deliverable_obj, deliverable_obj, ...]
    def get_deliverables(self):
        results = self._get_deliverables()
        return sorted(list(set(results)), key=lambda deliverable: deliverable.deliverable)

    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{}".format(self._prel)

## @}
