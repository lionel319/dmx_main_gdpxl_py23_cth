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
import dmx.ecolib.deliverable
import dmx.ecolib.family
from dmx.utillib.arcenv import ARCEnv

LOGGER = logging.getLogger(__name__)

class IPTypeError(Exception): pass

class IPType(object):  
    def __init__(self, family, iptype, roadmap='', preview = True):
        self._family = family
        self._iptype = iptype
        self._preview = preview
        self._deliverables = {}
    
        if not roadmap:
            # Loading ARC environment's variable for consumption
            self._arc_project, self._arc_family, self._arc_thread, self._arc_device, self._arc_process = ARCEnv().get_arc_vars()
            self._roadmap = dmx.ecolib.product.Product(self._family, self._arc_device).roadmap if self._arc_device else ''
        else:
            self._roadmap = roadmap

    @property
    def name(self):
        return self._iptype        

    @property
    def family(self):
        return self._family

    @property
    def iptype(self):
        return self._iptype

    ## Preloads local variables
    ## self._deliverables
    ##
    ## @param self The object pointer. 
    def _preload(self):
        self._deliverables = self._get_deliverables()        

    ## Returns a list of Deliverable objects associated with the IPType
    ##
    ## @param self The object pointer. 
    ## @param roadmap Product 
    ## @return list of Deliverable objects
    def _get_deliverables(self, roadmap=''):
        if not self._deliverables:
            deliverables = dmx.ecolib.loader.load_deliverables_by_ip_type(self.family)
            roadmaps = dmx.ecolib.loader.load_roadmaps(self.family)
            for roadmap in roadmaps:
                if roadmap not in self._deliverables:
                    self._deliverables[str(roadmap)] = {}
                for milestone in roadmaps[roadmap]:
                    if milestone not in self._deliverables[str(roadmap)]:
                        self._deliverables[str(roadmap)][str(milestone)] = []
                    for deliverable in roadmaps[roadmap][milestone]:
                        if deliverable in deliverables[self.iptype]:
                            self._deliverables[str(roadmap)][str(milestone)].append(dmx.ecolib.deliverable.Deliverable(
                                family = self.family,
                                deliverable = str(deliverable),
                                roadmap = roadmap,
                                preview = self._preview))
        return self._deliverables                                

    ## Returns a list of Deliverable objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param deliverable_filter Filter by deliverable
    ## @param milestone Defaults to 99, 99 means All
    ## @param views Filter by view, view must be a list
    ## @param roadmap Filter by roadmap
    ## @param prels Filter by prel. prels must be a list
    ## @exception dmx::ecolib::family::FamilyError Raise if filter cannot be compiled
    ## @return list of Deliverable objects
    def get_all_deliverables(self, deliverable_filter='', milestone='99', views=None, roadmap='', prels=None):
        try:
            re.compile(deliverable_filter)
        except:
            raise IPTypeError('{} cannot be compiled'.format(deliverable_filter))        

        roadmap = roadmap if roadmap else self._roadmap
        if not roadmap:
            raise IPTypeError('{}.{} requires roadmap option to be specified'.format(self.__class__.__name__, inspect.stack()[0][3]))
        deliverables = self._get_deliverables(roadmap=roadmap)
        if roadmap not in deliverables:
            LOGGER.warning('Roadmap {} does not exist'.format(roadmap))
            raise IPTypeError('Valid roadmaps for Family {} are: {}'.format(self.family, sorted(deliverables)))
        if milestone not in deliverables[roadmap]:
            LOGGER.error('Milestone {} does not exist'.format(milestone))
            raise IPTypeError('Valid milestones for Family {} are: {}'.format(self.family, sorted(deliverables[roadmap].keys())))

        if views and prels:
            errmsg = 'Prels:{} and views:{} can not be used together at the same time.'.format(prels, views)
            LOGGER.error(errmsg)
            raise IPTypeError(errmsg)

        results = []  
        found = []
        if views:
            for view in views:
                view = dmx.ecolib.family.Family(self._family).get_view(view)
                deliverables_of_view = [x.deliverable for x in view.get_deliverables()]
                for deliverable in deliverables[roadmap][milestone]:
                    if deliverable.deliverable in deliverables_of_view:
                        found.append(deliverable)
        elif prels:
            for prel in prels:
                prel = dmx.ecolib.family.Family(self._family).get_prel(prel)
                deliverables_of_prel = [x.deliverable for x in prel.get_deliverables()]
                for deliverable in deliverables[roadmap][milestone]:
                    if deliverable.deliverable in deliverables_of_prel:
                        found.append(deliverable)
        else:
            found = deliverables[roadmap][milestone]
            
        for deliverable in found:
            if re.match(deliverable_filter, deliverable.deliverable):
                results.append(deliverable)                                   

        return sorted(list(set(results)), key=lambda deliverable: deliverable.deliverable)

    ## Returns True if deliverable exists, otherwise False
    ##
    ## @param self The object pointer. 
    ## @param deliverable Deliverable
    ## @param milestone Defaults to 99, 99 means all
    ## @return True if deliverable exists, otherwise False    
    def has_deliverable(self, deliverable, milestone = '99', roadmap = ''):
        try:
            self.get_deliverable(deliverable, milestone, roadmap=roadmap) 
        except:
            return False
        return True                        

    ## Returns a Deliverable object that matches the deliverable and milestone
    ##
    ## @param self The object pointer. 
    ## @param deliverable Deliverable
    ## @param milestone Defaults to 99, 99 means all
    ## @exception dmx::ecolib::family::FamilyError Raise if deliverable contains illegal characters
    ## @return Deliverable object
    def get_deliverable(self, deliverable, milestone = '99', roadmap = ''):  
        if re.search('[^A-Za-z0-9_]', deliverable):
            raise IPTypeError('Deliverable can contain only alphabets, numbers and underscores.')

        results = self.get_all_deliverables('^{}$'.format(deliverable), milestone, roadmap=roadmap)
        if results:
            return results[0]
        else:
            # disable due to https://jira01.devtools.intel.com/browse/PSGDMX-1444
            #LOGGER.error('Deliverable {} does not exist'.format(deliverable))
            raise IPTypeError('Deliverable {} does not exist. Valid deliverables for IPType {}/{} Milestone {} Roadmap {} are: {}'.format(deliverable, self.family, self.iptype, milestone, roadmap, self.get_all_deliverables(roadmap=roadmap, milestone=milestone)))

    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{}".format(self.iptype)

## @}
