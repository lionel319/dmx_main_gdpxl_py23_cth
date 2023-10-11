#!/usr/bin/env python

from __future__ import print_function
from builtins import object
import sys, os
import re
import logging
import dmx.ecolib.ecosphere
from dmx.abnrlib.config_factory import ConfigFactory
import dmx.abnrlib.workspace
from dmx.dmlib.CheckType import CheckType
LOGGER = logging.getLogger(__name__)

class ManifestCheckError(Exception): pass

class ManifestCheck(object):
    def __init__(self, wsdir, ips=[], deliverables=[], cells=[], verbose=False, roadmap='', prel=None):
        self.ws = dmx.abnrlib.workspace.Workspace(wsdir)
        self.verbose = verbose
        self.roadmap = roadmap
        self.prel = prel

        self.config = ConfigFactory.create_from_icm(self.ws._project, self.ws._ip, self.ws._bom)

        if not ips:
            ips = [[x.project, x.variant] for x in self.config.flatten_tree() if x.is_composite()]
        self.ips = ips

        if not deliverables:
            deliverables = True
        self.deliverables = deliverables

        if not cells:
            cells = True
        self.cells = cells   

        self.checkers = []
        self.results = []
       
        self.eco = dmx.ecolib.ecosphere.EcoSphere(workspace=self.ws)
        self.family = self.eco.get_family_for_roadmap(self.roadmap)


    def _get_family(self, ip):
        project = self.config.search(variant=ip)[0].project
        family = self.eco.get_family_for_roadmap(self.roadmap)
        return family

    def runChecks(self):
        cwd = os.getcwd()
        self.setupTypeChecks()                        
        os.chdir(self.ws._workspaceroot)
        self.runTypeChecks()
        os.chdir(cwd)        

    def setupTypeChecks(self):
        for project, ip in self.ips:
            family = self.eco.get_family_for_roadmap(self.roadmap)
            ecoip = family.get_ip(ip, project)
            if self.cells == True:
                cells = ecoip.get_cells_names()
            else:
                cells = self.cells

            for cell in cells:
                # We pass in dmlib.ICManageWorkspace object instead of abnrlib.Workspace object as CheckType object is expecting ICManageWorkspace object
                self.checkers.append(CheckType(self.ws._workspace, ecoip, cell, roadmap=self.roadmap, prel=self.prel))

    def runTypeChecks(self):        
        results = []
        
        for check in self.checkers:
            deliverables = [x.libtype for x in self.config.flatten_tree() if x.is_simple() and x.variant == check.ip_name] if self.deliverables == True else self.deliverables
            ip_required_deliverables = [x.deliverable for x in check._ip.get_all_deliverables(roadmap=self.roadmap)]
            cells_needed_deliverables = [x.deliverable for x in check._ip.get_cell(check.cell_name).get_deliverables(roadmap=self.roadmap)]
            for deliverable in deliverables:
                LOGGER.debug('Running type-check for {}/{}:{}/{}'.format(self.ws._project, 
                                                                        check.ip_name,
                                                                        deliverable,
                                                                        check.cell_name))
                if deliverable not in ip_required_deliverables or deliverable not in cells_needed_deliverables:
                    LOGGER.debug("SKIP: {} is not part of the ip_required_deliverables:{} or cells_needed_deliverables:{}".format(
                        deliverables, ip_required_deliverables, cells_needed_deliverables))
                    errors = []
                elif not check.checkType(deliverable, self.verbose):
                    errors = [x.strip() for x in check._errors]
                else:                    
                    errors = []                    
                results.append((self.ws._project, check.ip_name, deliverable, check.cell_name, errors))
        self.results = results                
    
    def getResults(self):
        return self.results

    def getPassingResults(self):
        passingResults = []
        if self.results:
            for project, ip, deliverable, cell, errors in self.results:
                if not errors:
                    passingResults.append((project, ip, deliverable, cell))
        return passingResults                    

    def getFailingResults(self):
        failingResults = []
        if self.results:
            for project, ip, deliverable, cell, errors in self.results:
                if errors:
                    failingResults.append((project, ip, deliverable, cell, errors))
        return failingResults         

    def printErrors(self):        
        for project, ip, deliverable, cell, errors in self.results:
            if errors:
                print('Errors for {}/{}/{}/{}'.format(project, ip, deliverable, cell))
                for error in errors:
                    print('\t{}'.format(error))
                print()                

    def printResults(self):
        print()
        print('======================== RESULTS ========================')
        print()
        maxlen = 0
        for project, ip, deliverable, cell, errors in self.results:
            length = len('Type-check for {}/{}/{}/{}'.format(project, ip, deliverable, cell))
            if length > maxlen:
                maxlen = length

        for project, ip, deliverable, cell, errors in self.results:
            key = 'Type-check for {}/{}/{}/{}'.format(project, ip, deliverable, cell)
            print('{:{}} : {}'.format(key, maxlen, 'FAIL' if errors else 'pass'))

                            
                        
                         


        
        


