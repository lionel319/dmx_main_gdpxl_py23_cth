#!/usr/bin/env python

from builtins import str
import sys, os
import re
import logging
import dmx.ecolib.loader
import dmx.ecolib.revision
import dmx.ecolib.roadmap
import functools

LOGGER = logging.getLogger(__name__)

class ProductError(Exception): pass

@functools.total_ordering
class Product(dmx.ecolib.roadmap.Roadmap):  
    def __init__(self, family, product, preview = True):
        self._family = family
        self._product = product
        self._preview = preview

        self._roadmap = self.get_product_properties()        
        self._revisions = []
        self._milestones = []
        self._deliverables = {}
        self._checkers = {}

    @property
    def name(self):
        return self._product        

    @property
    def family(self):
        return self._family

    @property
    def product(self):
        return self._product

    @property
    def roadmap(self):
        return self._roadmap        
    
    ## Preloads local variables
    ## self._revisions
    ##
    ## @param self The object pointer.         
    def _preload(self):
        self._revisions = self.get_revisions()          
        self._milestones = self.get_milestones()

    ## Returns product's properties
    ##
    ## @param self The object pointer.
    ## @return Product properties
    def get_product_properties(self):
        products = dmx.ecolib.loader.load_roadmap_and_revisions_by_product(self._family)
        return products[self._product]['roadmap']

    ## Returns a list of Revision objects associated with the Product
    ##
    ## @param self The object pointer. 
    ## @return list of Revision objects        
    def _get_revisions(self):
        if not self._revisions:
            products = dmx.ecolib.loader.load_roadmap_and_revisions_by_product(self._family)
            revisions = products[self._product]['revisions']
            for revision in revisions:
                self._revisions.append(dmx.ecolib.revision.Revision(self._family,
                                                         self._product,
                                                         str(revision)))
                                            
        return self._revisions

    ## Returns a list of Revision objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param revision_filter Filter by revision
    ## @exception dmx::ecolib::revision::RevisionError Raise if filter cannot be compiled
    ## @return list of Revision objects
    def get_revisions(self, revision_filter = ''):
        try:
            re.compile(revision_filter)
        except:
            raise ProductError('{} cannot be compiled'.format(revision_filter))        
                
        results = []                        
        for revision in self._get_revisions():
            if re.match(revision_filter, revision.revision):
                results.append(revision)                                   

        return sorted(list(set(results)), key=lambda revision: revision.revision)

    ## Returns True if revision exists, otherwise False
    ##
    ## @param self The object pointer. 
    ## @param revision Revision
    ## @return True if revision exists, otherwise False
    def has_revision(self, revision): 
        try:
            self.get_revision(revision)
        except:
            return False
        return True                        

    ## Returns a Revision object that matches the revision name
    ##
    ## @param self The object pointer. 
    ## @param revision Revision
    ## @exception dmx::ecolib::revision::RevisionError Raise if revision contains illegal characters or revision cannot be found
    ## @return Revision object
    def get_revision(self, revision):
        if re.search('[^a-zA-Z0-9]', revision):
            raise ProductError('Revision can contain only alphabets and numbers')

        results = self.get_revisions('^{}$'.format(revision))
        if results:
            return results[0]
        else:
            LOGGER.error('Revision {} does not exist'.format(revision))
            raise ProductError('Valid revisions for Product {}/{} are: {}'.format(self._family, self._product, self.get_revisions()))

    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{}".format(self._product)

    def __lt__(self, other):
        return self.name < other.name
