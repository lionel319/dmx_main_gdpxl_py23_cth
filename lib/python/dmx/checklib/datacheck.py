#!/usr/bin/env python

from __future__ import print_function
from builtins import object
import sys, os
import re
import logging
import unittest
import dmx.ecolib.ecosphere
from dmx.abnrlib.config_factory import ConfigFactory
import dmx.abnrlib.workspace
from dmx.dmlib.deliverables.ipspec.CheckDataNew import Check as CheckDataIPSPEC
supported_deliverables = ['ipspec']
LOGGER = logging.getLogger(__name__)

class DataCheckError(Exception): pass

class DataCheck(object):
    def __init__(self, wsdir, ips=[], deliverables=[], cells=[], verbose=False, roadmap=''):
        self.ws = dmx.abnrlib.workspace.Workspace(wsdir)
        self.verbose = verbose
        self.roadmap = roadmap

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
        self.family = dmx.ecolib.ecosphere.EcoSphere(workspace=self.ws, workspaceroot=wsdir).get_family_for_roadmap(self.roadmap)


    def _get_family_and_project(self, ipname):
        project = self.config.search(variant='^{}$'.format(ipname))[0].project
        family = dmx.ecolib.ecosphere.EcoSphere().get_family_for_roadmap(self.roadmap)
        return [family, project]


    def runChecks(self):
        cwd = os.getcwd()
        self.setupDataChecks()
        os.chdir(self.ws._workspaceroot)
        self.runDataChecks()
        os.chdir(cwd)        

    def setupDataChecks(self):
        for project, ip in self.ips:
            #family, project = self._get_family_and_project(ip)
            family = dmx.ecolib.ecosphere.EcoSphere().get_family_for_roadmap(self.roadmap)
            ecoip = family.get_ip(ip, project)
            deliverables = [x.libtype for x in self.config.flatten_tree() if x.is_simple() and x.variant == ip] if self.deliverables == True else self.deliverables
            for deliverable in deliverables:                
                if deliverable not in supported_deliverables:
                    print ('{} does not have datacheck registered'.format(deliverable))
                elif deliverable == 'ipspec': 
                    ecodeliverable = ecoip.get_deliverable('ipspec', roadmap=self.roadmap)
                    if self.cells == True:
                        cells = ecoip.get_cells_names()
                    else:
                        cells = self.cells
                    for cell in cells:
                        self.checkers.append((deliverable, CheckDataIPSPEC(self.ws._project, ip, cell, ecoip, ecodeliverable, workspace=self.ws, roadmap=self.roadmap)))

    def runDataChecks(self):
        for (deliverable, checker) in self.checkers:                    
            LOGGER.debug('Running data-check for {}/{}:{}/{}'.format(checker.project, 
                                                               checker.ip,
                                                               deliverable,
                                                               checker.cell))
            results = checker.run()
            results = [x.strip() for x in results]
            self.results.append((checker.project, checker.ip, deliverable, checker.cell, results))
                
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
            length = len('Data-check for {}/{}/{}/{}'.format(project, ip, deliverable, cell))
            if length > maxlen:
                maxlen = length

        for project, ip, deliverable, cell, errors in self.results:
            key = 'Data-check for {}/{}/{}/{}'.format(project, ip, deliverable, cell)
            print('{:{}} : {}'.format(key, maxlen, 'FAIL' if errors else 'pass'))

                            
                        
                         


        
        


