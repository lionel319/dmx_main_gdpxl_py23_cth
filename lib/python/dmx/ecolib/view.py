#!/usr/bin/env python

## @addtogroup ecolib
## @{

from builtins import str
from builtins import object
import sys, os
import logging
import dmx.ecolib.loader
import dmx.ecolib.deliverable

LOGGER = logging.getLogger(__name__)

class ViewError(Exception): pass

class View(object):  

    ## load the dictionary information from views.json
    ##
    ## @param self The object pointer. 
    ## @param family The family name (str). 
    ## @param self The view name (str). 
    ## @return NA
    def __init__(self, family, view, preview=True):
        self._family = family
        if not view.startswith('view_'):
            raise ViewError('View ({}) does not begin with \'view_\'. View must begin with \'view_\''.format(view))
        self._view = view.lower()        
        self._preview = preview
        self._deliverables = []
        
    @property
    def name(self):
        return self._view

    @property
    def family(self):
        return self._family

    @property
    def view(self):
        return self._view

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
            viewsdict = dmx.ecolib.loader.load_views(self._family)
            for deliverable in viewsdict[self._view]:
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
        return "{}".format(self._view)

## @}
