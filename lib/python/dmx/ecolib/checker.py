#!/usr/bin/env python

## @addtogroup ecolib
## @{

''' axc
This is documentation

@author Lionel Tan, Kevin Lim
@image html dmx.ecolib.png 

-the end-
'''

import os, sys
import inspect
import re
import json
from dmx.utillib.decorators import memoized
import logging
import dmx.ecolib.loader
import dmx.ecolib.milestone
from dmx.utillib.arcenv import ARCEnv
import dmx.ecolib.product


LOGGER = logging.getLogger(__name__)

class CheckerError(Exception): pass
      
class Checker(object):  
    def __init__(self, family, flow, subflow,
                 roadmap='',
                 preview=True):
        self._family = family
        self._flow = flow.lower()
        self._subflow = subflow.lower()
        self._preview = preview

        if not roadmap:
            # Loading ARC environment's variable for consumption
            self._arc_project, self._arc_family, self._arc_thread, self._arc_device, self._arc_process = ARCEnv().get_arc_vars()
            self._roadmap = dmx.ecolib.product.Product(self._family, self._arc_device).roadmap if self._arc_device else ''
        else:
            self._roadmap = roadmap

        (checkname, deliverable, wrapper_name, documentation, dependencies, type, user, checker_execution, audit_verification, milestones, iptypes, prels, checkerlevel) = self.get_check_info()
        self._checkname = checkname
        self._wrapper_name = wrapper_name
        self._deliverable = deliverable.lower()
        self._documentation = documentation
        self._dependencies = dependencies
        self._type = type
        self._user = user
        self._checker_execution = checker_execution
        self._audit_verification = audit_verification
        self._milestones = milestones
        self._iptypes = iptypes
        self._prels = prels
        self._checkerlevel = checkerlevel
        
        # Compute the checker name 
        if self._subflow:
            self._checker = "{}/{}/{}".format(self._flow, self._subflow, self.checkname)
        else:
            self._checker = "{}/{}".format(self._flow, self._checkname)

    @property
    def name(self):
        return self._checker                    

    @property
    def family(self):
        return self._family

    @property
    def checkname(self):
        return self._checkname

    @property
    def wrapper_name(self):
        return self._wrapper_name

    @property
    def deliverable(self):
        return self._deliverable

    @property
    def documentation(self):
        return self._documentation

    @property
    def flow(self):
        return self._flow

    @property
    def subflow(self):
        return self._subflow

    @property
    def type(self):
        return self._type

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def user(self):
        return self._user

    @property
    def checker_execution(self):
        return self._checker_execution

    @property
    def audit_verification(self):
        return self._audit_verification

    @property
    def milestones(self):
        return self._milestones

    @property
    def iptypes(self):
        return self._iptypes

    @property
    def prels(self):
        return self._prels

    @property
    def checkerlevel(self):
        return self._checkerlevel

    ## Preloads local variables
    ## self._checkers
    ##
    ## @param self The object pointer. 
    def _preload(self):
        pass                      

    ## Returns checker's information 
    ##
    ## @param self The object pointer. 
    ## @return tuple of (checkname, deliverable, documentation, type, user ,milestone)
    def get_check_info(self):    

        checkname = ""
        deliverable = "" 
        wrapper_name = ""
        documentation = "" 
        dependencies = ""
        type = ""
        user = ""
        checker_execution = False
        audit_verification = False
        milestones = {}
        iptypes = []
        prels = []
        checkerlevel = "cell"   # default

        checkers_info = dmx.ecolib.loader.load_checkers(self._family)
        if self._subflow:
            key = "{}_{}".format(self._flow, self._subflow)
        else:
            key = self._flow                        
        for checker_info in checkers_info:
            if key == checker_info:
                checkname = str(checkers_info[checker_info]['Check Name'])
                wrapper_name = str(checkers_info[checker_info]['Wrapper Name']) if 'Wrapper Name' in checkers_info[checker_info] else None
                deliverable = str(checkers_info[checker_info]['Deliverable'])
                documentation = str(checkers_info[checker_info]['Documentation'])
                dependencies = str(checkers_info[checker_info]['Dependencies'])
                type = str(checkers_info[checker_info]['Type'])
                user = str(checkers_info[checker_info]['Unix Userid'])
                checker_execution = bool(checkers_info[checker_info]['Checker Execution']) if 'Checker Execution' in checkers_info[checker_info] else False
                audit_verification = bool(checkers_info[checker_info]['Audit Verification']) if 'Audit Verification' in checkers_info[checker_info] else False
                milestones = {}
                for roadmap in checkers_info[checker_info]['Milestones']:
                    if roadmap not in milestones:
                        milestones[str(roadmap)] = [str(x) for x in checkers_info[checker_info]['Milestones'][roadmap]]

                ### support ip-type aware checks https://jira.devtools.intel.com/browse/PSGDMX-1600
                if 'Iptypes' in checkers_info[checker_info]:
                    iptypes = checkers_info[checker_info]['Iptypes']

                ### support prel aware checks https://jira.devtools.intel.com/browse/PSGDMX-1884
                if 'Prels' in checkers_info[checker_info]:
                    prels = checkers_info[checker_info]['Prels']
                else:
                    prels = None

                ### support "Checker Level" https://jira.devtools.intel.com/browse/PSGDMX-2812
                key = 'Checker Level'
                if key in checkers_info[checker_info]:
                    if checkers_info[checker_info][key]:
                        checkerlevel = checkers_info[checker_info][key]

        return (checkname, deliverable, wrapper_name, documentation, dependencies, type, user, checker_execution, audit_verification, milestones, iptypes, prels, checkerlevel)


    ## Returns a list of Milestone objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param milestone_filter Filter by milestone
    ## @exception dmx::ecolib::family::CheckerError Raise if filter cannot be compiled
    ## @return list of Milestone objects          
    def get_milestones(self, milestone_filter = '', roadmap=''):
        try:
            re.compile(milestone_filter)
        except:
            raise CheckerError('{} cannot be compiled'.format(milestone_filter))              
        roadmap = roadmap if roadmap else self._roadmap
        if not roadmap:
            raise CheckerError('{}.{} requires roadmap option to be specified'.format(self.__class__.__name__, inspect.stack()[0][3]))

        milestoneobjs = []
        for milestone in self.milestones[roadmap]:            
            milestoneobjs.append(dmx.ecolib.milestone.Milestone(self._family,
                                                                str(milestone),
                                                                roadmap=roadmap,
                                                                preview = self._preview))

        results = []
        for milestoneobj in milestoneobjs:
            if re.match(milestone_filter, milestoneobj.milestone):
                results.append(milestoneobj)

        return sorted(list(set(results)), key=lambda milestone: milestone.milestone)
            
    ## Returns a Milestone object that matches the milestone
    ##
    ## @param self The object pointer. 
    ## @param milestone Milestone
    ## @exception dmx::ecolib::family::CheckerError Raise if milestone contains illegal characters or milestone cannot be found
    ## @return Milestone object             
    def get_milestone(self, milestone, roadmap=''):           
        if re.search('[^0-9.]', milestone):
            raise CheckerError('Milestone can contain only numbers and dot.')

        results = self.get_milestones('^{}$'.format(milestone, roadmap=roadmap))
        if results:
            return results[0]
        else:            
            LOGGER.error('Milestone {} does not exist'.format(milestone)) 
            raise CheckerError('Valid milestones for Roadmap {}/{} are: {}'.format(self._family, self._roadmap, self.get_milestones()))                      

    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{}".format(self._checker)
           
## @}      
                                   



