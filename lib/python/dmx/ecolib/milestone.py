#!/usr/bin/env python

## @addtogroup ecolib
## @{

import inspect
import sys, os
import re
import logging
import dmx.ecolib.loader
import dmx.ecolib.checker
from dmx.utillib.arcenv import ARCEnv

LOGGER = logging.getLogger(__name__)

class MilestoneError(Exception): pass

class Milestone(object):  
    def __init__(self, family, milestone, roadmap=None, preview = True):
        self._family = family
        self._milestone = milestone
        self._roadmap = roadmap
        self._preview = preview
        self._checkers = {}

        if not roadmap:
            # Loading ARC environment's variable for consumption
            self._arc_project, self._arc_family, self._arc_thread, self._arc_device, self._arc_process = ARCEnv().get_arc_vars()
            self._roadmap = dmx.ecolib.product.Product(self._family, self._arc_device).roadmap if self._arc_device else ''
        else:
            self._roadmap = roadmap         

    @property
    def name(self):
        return self._milestone        

    @property
    def family(self):
        return self._family

    @property
    def milestone(self):
        return self._milestone

    ## Preloads local variables
    ## self._checkers
    ##
    ## @param self The object pointer. 
    def _preload(self):
        self._checkers = self.get_checkers()        
       
    # Returns a list of Checker objects associated with the milestone
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
                milestones = checkers[checker]['Milestones']
                for roadmap in milestones:
                    if roadmap not in self._checkers:
                        self._checkers[str(roadmap)] = []
                    self._checkers[roadmap].append(checkerobj)
        return self._checkers                    
          
    ## Returns a list of Checker objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param flow_filter Filter by flow
    ## @param subflow_filter Filter by subflow
    ## @param checker_filter Filter by checker name
    ## @param deliverable Filter by deliverable
    ## @param roadmap Filter by roadmap
    ## @exception dmx::ecolib::family::FamilyError Raise if filter cannot be compiled
    ## @return list of Checker objects            
    def get_checkers(self, flow_filter = '', subflow_filter = '', checker_filter = '', deliverable = '', roadmap = ''):
        try:
            re.compile(flow_filter)
            re.compile(subflow_filter)
            re.compile(checker_filter)
        except:
            raise MilestoneError('{}/{}/{} cannot be compiled'.format(flow_filter, subflow_filter, checker_filter))        
       
        if deliverable: 
            deliverable_filter = '^{}$'.format(deliverable)
        else:  
            deliverable_filter = '{}'.format(deliverable)                                                    

        roadmap = roadmap if roadmap else self._roadmap
        if not roadmap:
            raise MilestoneError('{}.{} requires roadmap option to be specified'.format(self.__class__.__name__, inspect.stack()[0][3]))            
     
        results = []
        checkers = self._get_checkers()
        if roadmap not in checkers.keys():
            LOGGER.warning('Roadmap {} does not exist'.format(roadmap))
            raise MilestoneError('Valid roadmaps for Family {} are: {}'.format(self.family, sorted(checkers.keys())))

        for checker in checkers[roadmap]:
            if re.match(checker_filter, checker.checkname) and re.match(flow_filter, checker.flow) and re.match(subflow_filter, checker.subflow) and re.match(deliverable_filter, checker.deliverable):
                results.append(checker)

        return sorted(list(set(results)), key=lambda checker: checker.flow)
        
    ## Returns True if flow/subflow/checker exists, otherwise False
    ##
    ## @param self The object pointer. 
    ## @param flow Flow
    ## @param subflow Subflow
    ## @param checker Checker's name
    ## @return True if checker exists, otherwise False
    def has_checker(self, flow, subflow, checker, roadmap=''): 
        try:
            self.get_checker(flow, subflow, checker, roadmap=roadmap)
        except:
            return False
        return True            

    # Returns Checker objects that matches flow,subflow,checker's name and deliverable
    ##
    ## @param self The object pointer. 
    ## @param flow Flow
    ## @param subflow Subflow
    ## @param checker Checker's name
    ## @param deliverable Deliverable
    ## @exception dmx::ecolib::deliverable::DeliverableError Raise if filter regex cannot be compiled or checker cannot be found
    ## @return a Checker object 
    def get_checker(self, flow, subflow, checker, deliverable = '', roadmap = ''):
        if re.search('[^A-Za-z0-9_]', flow) or re.search('[^A-Za-z0-9_]', subflow) or re.search('[^A-Za-z0-9_]', checker):
            raise MilestoneError('Flow, SubFlow and Checker can contain only alphabets, numbers and underscores.')

        results = self.get_checkers('^{}$'.format(flow), '^{}$'.format(subflow), '^{}$'.format(checker), deliverable, roadmap=roadmap)
        
        if results:
            return results[0]
        else:
            LOGGER.error('Flow/Subflow/Checker {}/{}/{} does not exist'.format(flow, subflow, roadmap))
            raise MilestoneError('Valid checkers for Milestone {}/{} are: {}'.format(self._family, self._milestone, self.get_checkers(roadmap=roadmap)))            

    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{}".format(self._milestone)

## @}
