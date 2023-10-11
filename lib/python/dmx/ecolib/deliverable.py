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
import dmx.ecolib.slice
from dmx.utillib.arcenv import ARCEnv
from dmx.utillib.utils import run_command
import functools

LOGGER = logging.getLogger(__name__)

class DeliverableError(Exception): pass

@functools.total_ordering
class Deliverable(dmx.ecolib.manifest.Manifest):  
    def __init__(self, family, deliverable, 
                 roadmap='',
                 preview=True):
        self._family = family
        self._deliverable = deliverable.lower()
        self._preview = preview
        self._checkers = {}
        self._slices = []
        self._bom = ''
        # ipqc report
        self._report = None
        self._waived = False
        self._is_unneeded = False
        self._err    = ''
        self._roadmap = roadmap
        self._owner = ''
        self._view = ''
        self._status = ''
        self._waivers = []
        self._nb_fail       = 0
        self._nb_pass       = 0
        self._nb_fatal      = 0
        self._nb_warning    = 0
        self._nb_unneeded   = 0
        self._nb_na         = 0

        # Deliverable inherits from Manifest, since for every Deliverable, there will always be a Manifest
        super(Deliverable, self).__init__(self._family,
                                          self._deliverable,
                                          self._preview)

    @property
    def name(self):
        return self._deliverable        
                
    @property
    def family(self):
        return self._family

    @property
    def deliverable(self):
        return self._deliverable
        
    ## Preloads local variables
    ## self._checkers
    ##
    ## @param self The object pointer. 
    def _preload(self):
        self._checkers = self.get_checkers()        

    ## Returns a list of Slice objects associated with the deliverable
    ##
    ## @param self The object pointer. 
    ## @return list of Slice objects
    def _get_slices(self):
        if not self._slices:
            for deliverableslice in self._slice:
                deliverable, slice = deliverableslice.split(':')
                self._slices.append(dmx.ecolib.slice.Slice(self._family, self._deliverable, slice))
        return self._slices

    ## Returns a list of Slice objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @exception dmx::ecolib::deliverable::DeliverableError Raise if filter regex cannot be compiled
    ## @return list of Slice objects
    def get_slices(self, slice_filter = ''):
        try:
            re.compile(slice_filter)
        except:
            raise DeliverableError('{} cannot be compiled'.format(slice_filter))        
        results = []
        slices = self._get_slices()
        for slice in slices:
            if re.match(slice_filter, slice.slice):
                results.append(slice)

        return sorted(list(set(results)), key=lambda slice: slice.slice)
        
    ## Returns True if slice exists, otherwise False
    ##
    ## @param self The object pointer. 
    ## @param checker Slice's name
    ## @return True if slice exists, otherwise False
    def has_slice(self, slice): 
        try:
            self.get_slice(slice)
        except:
            return False
        return True                            

    ## Returns Slice objects that matches slice's name
    ##
    ## @param self The object pointer. 
    ## @param slice Slice's name
    ## @exception dmx::ecolib::deliverable::DeliverableError Raise if slice cannot be found
    ## @return a Slice object 
    def get_slice(self, slice):
        results = self.get_slices('^{}$'.format(slice))
        if results:
            return results[0]
        else:
            LOGGER.error('Slice {} does not exist'.format(slice))
            raise DeliverableError('Valid slices for Deliverable {}/{} are: {}'.format(self._family, self._deliverable, self.get_slices()))

    ## Returns a list of Checker objects associated with the deliverable
    ##
    ## @param self The object pointer. 
    ## @return list of Checker objects
    def _get_checkers(self):
        if not self._checkers:
            if not self._roadmap:
                # Loading ARC environment's variable for consumption
                self._arc_project, self._arc_family, self._arc_thread, self._arc_device, self._arc_process = ARCEnv().get_arc_vars()
                self._roadmap = dmx.ecolib.product.Product(self._family, self._arc_device).roadmap if self._arc_device else ''

            checkers = dmx.ecolib.loader.load_checkers(self._family)
            for checker in checkers:
                if self._deliverable == str(checkers[checker]['Deliverable'].lower()):
                    checkerobj = dmx.ecolib.checker.Checker(self._family, 
                                                 str(checkers[checker]['Flow']),
                                                 str(checkers[checker]['SubFlow']),
                                                 roadmap = self._roadmap,
                                                 preview = self._preview)
                    milestones = checkers[checker]['Milestones']
                    for roadmap in milestones:
                        if roadmap not in self._checkers:
                            self._checkers[str(roadmap)] = {}
                        for milestone in milestones[roadmap]:
                            if milestone not in self._checkers[roadmap]:
                                self._checkers[str(roadmap)][str(milestone)] = []                                       
                            self._checkers[roadmap][milestone].append(checkerobj)
        return self._checkers                               

    ## Returns a list of Checker objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param flow_filter Filter by flow
    ## @param subflow_filter Filter by subflow
    ## @param checker_filter Filter by checker name
    ## @param milestone Filter by milestone. Defaults to 99, 99 means All
    ## @exception dmx::ecolib::deliverable::DeliverableError Raise if filter regex cannot be compiled
    ## @return list of Checker objects
    def get_checkers(self, flow_filter = '', subflow_filter = '', checker_filter = '', milestone = '99', roadmap = '', iptype_filter='', prel_filter=''):
        try:
            re.compile(flow_filter)
            re.compile(subflow_filter)
            re.compile(checker_filter)
            re.compile(iptype_filter)
            re.compile(prel_filter)
        except:
            raise DeliverableError('{}/{}/{}/{} cannot be compiled'.format(flow_filter, subflow_filter, checker_filter, prel_filter))        
        results = []
        checkers = self._get_checkers()
        roadmap = roadmap if roadmap else self._roadmap
        valid_roadmaps = [x.roadmap for x in dmx.ecolib.family.Family(self._family).get_roadmaps()]
        if not roadmap:
            raise DeliverableError('{}.{} requires roadmap option to be specified'.format(self.__class__.__name__, inspect.stack()[0][3]))
        if roadmap not in valid_roadmaps:
            LOGGER.warning('Roadmap {} does not exist'.format(roadmap))
            raise DeliverableError('Valid roadmaps for Family {} are: {}'.format(self.family, sorted(valid_roadmaps)))
        valid_milestones = [x.milestone for x in dmx.ecolib.roadmap.Roadmap(self._family, roadmap).get_milestones()]            
        if milestone not in valid_milestones:
            LOGGER.error('Milestone {} does not exist'.format(milestone))
            raise DeliverableError('Valid milestones for Roadmap {}/{} are: {}'.format(self.family, roadmap, sorted(valid_milestones)))
        if roadmap in checkers:
            if milestone in checkers[roadmap]:
                for checker in checkers[roadmap][milestone]:
                    if re.match(checker_filter, checker.checkname) and re.match(flow_filter, checker.flow) and re.match(subflow_filter, checker.subflow):
                        if not iptype_filter or not checker.iptypes or [iptype for iptype in checker.iptypes if re.match(iptype_filter, iptype)]:
                            if not prel_filter or checker.prels == None or [prel for prel in checker.prels if re.match(prel_filter, prel)]:
                                results.append(checker)

        return sorted(list(set(results)), key=lambda checker: checker.checkname)
        
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

    ## Returns Checker objects that matches flow,subflow,checker's name and milestone
    ##
    ## @param self The object pointer. 
    ## @param flow Flow
    ## @param subflow Subflow
    ## @param checker Checker's name
    ## @param milestone Milestone. Defaults to 99, 99 means All
    ## @exception dmx::ecolib::deliverable::DeliverableError Raise if filter regex cannot be compiled or checker cannot be found
    ## @return a Checker object 
    def get_checker(self, flow, subflow, checker, milestone = '99', roadmap = ''):
        if re.search('[^A-Za-z0-9_]', flow) or re.search('[^A-Za-z0-9_]', subflow) or re.search('[^A-Za-z0-9_]', checker):
            raise DeliverableError('Flow, SubFlow and Checker can contain only alphabets, numbers and underscores.')

        results = self.get_checkers('^{}$'.format(flow), '^{}$'.format(subflow), '^{}$'.format(checker), milestone, roadmap=roadmap)
        if results:
            return results[0]
        else:
            LOGGER.error('Flow/Subflow/Checker {}/{}/{} does not exist'.format(flow, subflow, checker))
            raise DeliverableError('Valid checkers for Deliverable {}/{} are: {}'.format(self._family, self._deliverable, self.get_checkers()))


    def get_deliverable_owner(self, project, ip, deliverable, config):
        (code, out, err) = run_command("pm propval -l {} {} {} {} | grep Owner" .format(project, ip, deliverable, config))
        if code != 0:
            (code, out, err) = run_command("pm propval -l {} {} {} {} -C | grep Owner" .format(project, ip, deliverable, config))
            if code != 0:
                return ''
            else:
                out = out.strip()
                l = out.split()
                for e in l:
                    if e.find("Value=") != -1:
                        match = re.search('Value="(\S+)"', e)
                        if match:
                            owner = match.group(1)
                            return owner
        else:
            out = out.strip()
            l = out.split()
            for e in l:
                if e.find("Value=") != -1:
                    match = re.search('Value="(\S+)"', e)
                    if match:
                        owner = match.group(1)
                        return owner
        return ''



    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{}".format(self._deliverable)

    # return the status of the checker
    @property
    def bom(self):
        return self._bom

    @bom.setter
    def bom(self, value):
        self._bom = value

    # return the status of the checker
    @property
    def report(self):
        return self._report

    @report.setter
    def report(self, value):
        self._report = value

    # return the status of the checker
    @property
    def waived(self):
        return self._waived

    @waived.setter
    def waived(self, value):
        self._waived = value        

    @property
    def err(self):
        return self._err

    @err.setter
    def err(self, value):
        self._err = value

    @property
    def is_unneeded(self):
        return self._is_unneeded

    @is_unneeded.setter
    def is_unneeded(self, value):
         self._is_unneeded = value

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, value):
         self._owner = value       

    @property
    def view(self):
        return self._view

    @view.setter
    def view(self, value):
         self._view = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
         self._status = value

    @property
    def waivers(self):
        return self._waivers

    @waivers.setter
    def waivers(self, value):
         self._waivers = value

    @property
    def nb_fail(self):
        return self._nb_fail

    @nb_fail.setter
    def nb_fail(self, value):
        self._nb_fail = value

    @property
    def nb_pass(self):
        return self._nb_pass

    @nb_pass.setter
    def nb_pass(self, value):
        self._nb_pass = value

    @property
    def nb_fatal(self):
        return self._nb_fatal

    @nb_fatal.setter
    def nb_fatal(self, value):
        self._nb_fatal = value

    @property
    def nb_warning(self):
        return self._nb_warning

    @nb_warning.setter
    def nb_warning(self, value):
        self._nb_warning = value

    @property
    def nb_unneeded(self):
        return self._nb_unneeded

    @nb_unneeded.setter
    def nb_unneeded(self, value):
        self._nb_unneeded = value

    @property
    def nb_na(self):
        return self._nb_na

    @nb_na.setter
    def nb_na(self, value):
        self._nb_na = value

    ### needed for python 3
    def __lt__(self, other):
        return self.name < other.name

## @}        
