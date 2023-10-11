#!/usr/bin/env python

## @addtogroup ecolib
## @{

import sys, os
import re
import logging
import dmx.ecolib.loader
import dmx.ecolib.milestone
import dmx.ecolib.deliverable
import dmx.ecolib.checker

LOGGER = logging.getLogger(__name__)

class RoadmapError(Exception): pass

class Roadmap(object):  
    def __init__(self, family, roadmap, preview = True):
        self._family = family
        self._roadmap = roadmap
        self._preview = preview
        self._milestones = []
        self._deliverables = {}
        self._checkers = {}

    @property
    def name(self):
        return self._roadmap

    @property
    def family(self):
        return self._family

    @property
    def roadmap(self):
        return self._roadmap

    ## Preloads local variables
    ## self._milestones
    ##
    ## @param self The object pointer. 
    def _preload(self):
        self._milestones = self._get_milestones()   
        self._deliverables = self._get_deliverables()     
        self._checkers = self._get_checkers()

    ## Returns a list of Milestone objects associated with the Roadmap
    ##
    ## @param self The object pointer. 
    ## @return list of Milestone objects
    def _get_milestones(self):
        if not self._milestones:
            milestones = dmx.ecolib.loader.load_roadmaps(self._family)[self._roadmap].keys()
                
            results = []                            
            for milestone in set(milestones):                    
                self._milestones.append(dmx.ecolib.milestone.Milestone(self._family,
                                                                       str(milestone),
                                                                       roadmap=self._roadmap,
                                                                       preview = self._preview))

        return self._milestones

    ## Returns a list of Milestone objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param milestone_filter Filter by milestone
    ## @exception dmx::ecolib::family::RoadmapError Raise if filter cannot be compiled
    ## @return list of Milestone objects          
    def get_milestones(self, milestone_filter = ''):
        try:
            re.compile(milestone_filter)
        except:
            raise RoadmapError('{} cannot be compiled'.format(milestone_filter))        

        milestones = []
        for milestone in self._get_milestones():
            if re.match(milestone_filter, milestone.milestone):
                milestones.append(milestone)

        return sorted(list(set(milestones)), key=lambda milestone: milestone.milestone)
            
    ## Returns True if milestone exists, otherwise False
    ##
    ## @param self The object pointer. 
    ## @param milestone Milestone
    ## @return True if milestone exists, otherwise False                     
    def has_milestone(self, milestone):                    
        try:
            self.get_milestone(milestone) 
        except:
            return False
        return True            

    ## Returns a Milestone object that matches the milestone
    ##
    ## @param self The object pointer. 
    ## @param milestone Milestone
    ## @exception dmx::ecolib::family::RoadmapError Raise if milestone contains illegal characters or milestone cannot be found
    ## @return Milestone object             
    def get_milestone(self, milestone):           
        if re.search('[^0-9.]', milestone):
            raise RoadmapError('Milestone can contain only numbers and dot.')

        results = self.get_milestones('^{}$'.format(milestone))
        if results:
            return results[0]
        else:            
            LOGGER.error('Milestone {} does not exist'.format(milestone))
            raise RoadmapError('Valid milestones for Roadmap {}/{} are: {}'.format(self._family, self._roadmap, self.get_milestones()))                   

    ## Returns a list of Deliverable objects associated with the RoadmapError
    ##
    ## @param self The object pointer. 
    ## @return list of Deliverable objects
    def _get_deliverables(self):
        if not self._deliverables:
            roadmaps = dmx.ecolib.loader.load_roadmaps(self.family)
            roadmap = roadmaps[self._roadmap]
            for milestone in roadmap:
                if milestone not in self._deliverables:
                    self._deliverables[milestone] = []
                for deliverable in roadmap[milestone]:
                    self._deliverables[str(milestone)].append(dmx.ecolib.deliverable.Deliverable(
                                family = self.family,
                                deliverable = str(deliverable),
                                roadmap = self._roadmap,
                                preview = self._preview))
        return self._deliverables                                

    ## Returns a list of Deliverable objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param deliverable_filter Filter by deliverable
    ## @param milestone Defaults to 99, 99 means All
    ## @param views Filter by view, view must be a list
    ## @exception dmx::ecolib::family::FamilyError Raise if filter cannot be compiled
    ## @return list of Deliverable objects
    def get_deliverables(self, deliverable_filter = '', milestone = '99', views = []):
        try:
            re.compile(deliverable_filter)
        except:
            raise RoadmapError('{} cannot be compiled'.format(deliverable_filter))        

        if milestone not in self._get_deliverables():
            LOGGER.error('Milestone {} does not exist'.format(milestone))
            raise RoadmapError('Valid milestones for Family {} are: {}'.format(self.family, sorted(self._get_deliverables().keys())))

        results = []  
        found = []
        if views:
            for view in views:
                view = dmx.ecolib.family.Family(self._family).get_view(view)
                deliverables_of_view = [x.deliverable for x in view.get_deliverables()]
                for deliverable in self._get_deliverables()[milestone]:
                    if deliverable.deliverable in deliverables_of_view:
                        found.append(deliverable)
        else:
            found = self._get_deliverables()[milestone]
            
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
    def has_deliverable(self, deliverable, milestone = '99'):
        try:
            self.get_deliverable(deliverable, milestone) 
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
    def get_deliverable(self, deliverable, milestone = '99'):  
        if re.search('[^A-Za-z0-9_]', deliverable):
            raise RoadmapError('Deliverable can contain only alphabets, numbers and underscores.')

        results = self.get_deliverables('^{}$'.format(deliverable), milestone)
        if results:
            return results[0]
        else:
            LOGGER.error('Deliverable {} does not exist'.format(deliverable))
            raise RoadmapError('Valid deliverables for Roadmap {}/{} are: {}'.format(self.family, self.roadmap, self.get_deliverables()))

    ## Returns a list of Checker objects associated with the milestone
    ##
    ## @param self The object pointer. 
    ## @return list of Checker objects      
    def _get_checkers(self):
        if not self._checkers:
            checkers = dmx.ecolib.loader.load_checkers(self._family)
            for checker in checkers:                
                checkerobj = dmx.ecolib.checker.Checker(self._family, 
                                                 str(checkers[checker]['Flow']),
                                                 str(checkers[checker]['SubFlow']),
                                                 preview = self._preview)
                if self._roadmap in checkers[checker]['Milestones']:
                    for milestone in checkers[checker]['Milestones'][self._roadmap]:
                        if milestone not in self._checkers:
                            self._checkers[str(milestone)] = []
                        self._checkers[milestone].append(checkerobj)
        return self._checkers                    
          
    ## Returns a list of Checker objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param flow_filter Filter by flow
    ## @param subflow_filter Filter by subflow
    ## @param checker_filter Filter by checker name
    ## @param milestone Filter by milestone. Defaults to 99, 99 means All
    ## @exception dmx::ecolib::deliverable::RoadmapError Raise if filter regex cannot be compiled
    ## @return list of Checker objects
    def get_checkers(self, flow_filter = '', subflow_filter = '', checker_filter = '', milestone = '99', deliverable = ''):
        try:
            re.compile(flow_filter)
            re.compile(subflow_filter)
            re.compile(checker_filter)
        except:
            raise RoadmapError('{}/{}/{} cannot be compiled'.format(flow_filter, subflow_filter, checker_filter))        
        results = []

        if deliverable: 
            deliverable_filter = '^{}$'.format(deliverable)
        else:  
            deliverable_filter = '{}'.format(deliverable)
            
        checkers = self._get_checkers()
        if milestone not in checkers.keys():
            LOGGER.error('Milestone {} does not exist'.format(milestone))
            raise RoadmapError('Valid milestones for Roadmap {}/{} are: {}'.format(self.family, self._roadmap, sorted(checkers.keys())))

        for checker in checkers[milestone]:
            if re.match(checker_filter, checker.checkname) and \
               re.match(flow_filter, checker.flow) and \
               re.match(subflow_filter, checker.subflow) and \
               re.match(deliverable_filter, checker.deliverable):
                results.append(checker)

        return sorted(list(set(results)), key=lambda checker: checker.checkname)
        
    ## Returns True if flow/subflow/checker exists, otherwise False
    ##
    ## @param self The object pointer. 
    ## @param flow Flow
    ## @param subflow Subflow
    ## @param checker Checker's name
    ## @return True if checker exists, otherwise False
    def has_checker(self, flow, subflow, checker): 
        try:
            self.get_checker(flow, subflow, checker)
        except:
            return False
        return True                            

    ## Returns Checker objects that matches flow,subflow,checker's name and milestone
    ##
    ## @param self The object pointer. 
    ## @param flow Flow
    ## @param subflow Subflow
    ## @param checker Checker's name
    ## @param milestone Milestone. Defaults to 99, 99 means All
    ## @exception dmx::ecolib::deliverable::RoadmapError Raise if filter regex cannot be compiled or checker cannot be found
    ## @return a Checker object 
    def get_checker(self, flow, subflow, checker, milestone = '99'):
        if re.search('[^A-Za-z0-9_]', flow) or re.search('[^A-Za-z0-9_]', subflow) or re.search('[^A-Za-z0-9_]', checker):
            raise RoadmapError('Flow, SubFlow and Checker can contain only alphabets, numbers and underscores.')

        results = self.get_checkers('^{}$'.format(flow), '^{}$'.format(subflow), '^{}$'.format(checker), milestone)
        if results:
            return results[0]
        else:
            LOGGER.error('Flow/Subflow/Checker {}/{}/{} does not exist'.format(flow, subflow, checker))
            raise RoadmapError('Valid checkers for Roadmap {}/{} are: {}'.format(self._family, self._roadmap, self.get_checkers()))

    def is_subset(self, other_roadmap, milestone):
        '''
        Returns True if deliverables for roadmap/milestone is a subset of self.roadmap/milestone
        other_roadmap is a string
        milestone is a string
        '''            
        ret = True
        self._preload()
        other_roadmap = Roadmap(self.family, other_roadmap)
        other_roadmap._preload()
        self_deliverables = [x.deliverable for x in self.get_deliverables(milestone=milestone)]
        other_deliverables = [x.deliverable for x in other_roadmap.get_deliverables(milestone=milestone)]

        for deliverable in other_deliverables:
            if deliverable not in self_deliverables:
                ret = False

        return ret                        
    
    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{}".format(self._roadmap)

    def __eq__(self, other):
        '''
        Compares milestones, deliverables and checkers
        '''       
        self._preload()
        other._preload()
        return self._milestones == other._milestones and \
            self._deliverables == other._deliverables and \
            self._checkers == other._checkers

    def __ne__(self, other):
        '''
        Compares milestones, deliverables and checkers
        '''       
        return not self.__eq__(other)
            
            
### @}
