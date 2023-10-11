#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/listecosphere.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr ecosphere
Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2016
All rights reserved.
'''
from __future__ import print_function

from builtins import object
import sys
import logging
import textwrap
import getpass
import time
import re

from dmx.abnrlib.icm import ICManageCLI
import dmx.ecolib.ecosphere as ecosphere

class ListEcosphereError(Exception): pass

class ListEcosphere(object):
    '''
    Handles running the ecosphere command
    '''

    def __init__(self, family, project, product, revision, ip, 
                 ip_type, milestone, deliverable, flow, subflow,
                 check, cell, unneeded, history, bom, view, roadmap, production=True, thread=False):
        self.family = family
        self.project = project
        self.product = product
        self.revision = revision
        self.ip = ip
        self.ip_type = ip_type
        self.milestone = milestone
        self.deliverable = deliverable        
        self.flow = flow
        self.subflow = subflow
        self.check = check
        self.cell = cell
        self.unneeded = unneeded
        self.history = history
        self.bom = bom
        self.view = view
        self.roadmap = roadmap
        self.production = production
        self.thread = thread

        self.cli = ICManageCLI(preview=True)
        self.logger = logging.getLogger(__name__)
        self.ecosphere = ecosphere.EcoSphere(production=self.production)

        # project must be specified if ip is given
        if self.ip and not self.project:
            raise ListEcosphereError("PROJECT must be provided when IP value is given.")

        # IP and ip-type argument cannot be given together
        if self.ip and self.ip_type:
            raise ListEcosphereError("IP and IP Type cannot be given together.")

        if self.family:
            self.familyobj = self.ecosphere.get_family(self.family)
        else:
            self.familyobj = self.ecosphere.get_family()

        # Assign roadmap if product is given
        if self.product and self.product != True:
            self.roadmap = self.familyobj.get_product(self.product).roadmap

        if ((self.deliverable==True and self.ip) or (self.cell and not self.deliverable) or self.unneeded):
            try:
                workspace = self.ecosphere.workspace
            except:            
                self.logger.debug('Current working directory is not an ICM workspace, reading from --bom instead')
                if not self.bom:
                    self.logger.error('Please look at \'dmx help roadmap\' on how to provide --bom')
                    raise ListEcosphereError('Please provide a BOM to --bom for dmx to pull ipspec info from')

    def print_results(self):
        '''
        Prints the desired results to terminal
        '''

        if self.thread:
            self.print_all_available_threads_for_all_families()

        elif self.unneeded:
            if self.cell:
                unneeded_deliverables = self.familyobj.get_ip(self.ip, self.project).get_cell(self.cell, bom=self.bom, local=False).get_unneeded_deliverables(bom=self.bom, local=False)
            elif self.ip:
                unneeded_deliverables = self.familyobj.get_ip(self.ip, self.project).get_unneeded_deliverables(bom=self.bom, local=False)
            for deliverable in unneeded_deliverables:
                print(deliverable)
        elif self.cell and not self.deliverable:
            if self.cell == True:
                if self.ip:
                    product = "" if self.product == None else self.product
                    cells = self.familyobj.get_ip(self.ip, self.project).get_cells_names(product_filter=product, bom=self.bom, local=False)
                    for cell in cells:
                        print(cell)
                else:
                    raise ListEcosphereError('IP needs to be provided to list cells.')                        
            else:
                if self.ip:
                    cell = self.familyobj.get_ip(self.ip, self.project).get_cell(self.cell, bom=self.bom, local=False)
                else:
                    raise ListEcosphereError('IP needs to be provided to list cells.')
                self.print_ecosphere_object(cell, bom=self.bom)                
        elif self.check or self.flow or self.subflow:        
            if self.check == True or self.flow == True or self.subflow == True:
                check = '' if self.check == True or self.check == None else self.check
                flow = '' if self.flow == True or self.flow == None else self.flow
                subflow = '' if self.subflow == True or self.subflow == None else self.subflow
                if self.deliverable:
                    milestone = self.milestone if self.milestone else '99'
                    if self.ip:
                        checkers = self.familyobj.get_ip(self.ip, self.project).get_deliverable(self.deliverable).get_checkers(flow_filter=flow, 
                        subflow_filter=subflow,
                        checker_filter=check,
                        milestone=milestone)
                    elif self.ip_type:
                        checkers = self.familyobj.get_iptype(self.ip_type).get_deliverable(self.deliverable, roadmap=self.roadmap).get_checkers(flow_filter=flow,
                        subflow_filter=subflow,
                        checker_filter=check,
                        milestone=milestone)
                    else:
                        raise ListEcosphereError('IP or IP Type needs to be provided to list checkers.')                            
                elif self.milestone:                    
                    if self.product:
                        checkers = self.familyobj.get_product(self.product).get_milestone(self.milestone).get_checkers(flow_filter=flow,
                              subflow_filter=subflow,
                              checker_filter=check)
                    else:
                        raise ListEcosphereError('Product needs to be provided to list checkers for a specific milestone.')
                else:
                    raise ListEcosphereError('IP(or Type)/Deliverable or Milestone needs to be provided to list checkers.')                
                for checker in checkers:
                    print(checker)   
            else:
                check = '' if self.check == True or self.check == None else self.check
                flow = '' if self.flow == True or self.flow == None else self.flow
                subflow = '' if self.subflow == True or self.subflow == None else self.subflow
                if self.deliverable:
                    if self.ip:
                        checkers = self.familyobj.get_ip(self.ip, self.project).get_deliverable(self.deliverable).get_checkers(flow_filter=flow,
                                                                                                                   subflow_filter=subflow,
                                                                                                                   checker_filter=check)
                    elif self.ip_type:
                        checkers = self.familyobj.get_iptype(self.ip_type).get_deliverable(self.deliverable, roadmap=self.roadmap).get_checkers(flow_filter=flow,
                                                                                                                   subflow_filter=subflow,
                                                                                                                   checker_filter=check)
                    else:
                        raise ListEcosphereError('IP or ip-type needs to be provided to list checkers.')                            
                elif self.milestone:                    
                    checkers = self.familyobj.get_product(self.product).get_milestone(self.milestone).get_checkers(flow_filter=flow,
                                                                                      subflow_filter=subflow,
                                                                                      checker_filter=check)
                else:
                    raise ListEcosphereError('IP(or Type)/Deliverable or Milestone needs to be provided to list checkers.')                
                for checker in checkers:
                    print("===== {} =====".format(checker))
                    self.print_ecosphere_object(checker)                                                                            
        elif self.deliverable:
            milestone = self.milestone if self.milestone else '99'
            if self.deliverable == True:
                if self.ip_type:                
                    if not self.roadmap:
                        raise ListEcosphereError('Roadmap needs to be provided to get a deliverable of an IPType.')
                    if self.view:
                        if self.view != True:
                            deliverables = self.familyobj.get_iptype(self.ip_type).get_all_deliverables(milestone=milestone, roadmap=self.roadmap, views=[self.view])
                        else:
                            raise ListEcosphereError('--view needs to be provided with a value')
                    else:                                            
                        deliverables = self.familyobj.get_iptype(self.ip_type).get_all_deliverables(milestone=milestone, roadmap=self.roadmap)
                elif self.ip:
                    if self.bom:
                        deliverables = [x.deliverable for x in self.familyobj.get_ip(self.ip, self.project).get_deliverables(milestone=milestone, bom=self.bom, local=False)]
                    else:
                        deliverables = [x.deliverable for x in self.familyobj.get_ip(self.ip, self.project).get_deliverables(milestone=milestone)]
                elif self.view:
                    if self.view != True:
                        deliverables = self.familyobj.get_view(self.view).get_deliverables()
                    else:
                        raise ListEcosphereError('--view needs to be provided with a value')
                else:
                    raise ListEcosphereError('IP or ip-type needs to be provided to list deliverables.')                
                for deliverable in deliverables:
                    print(deliverable)
            else:
                if self.view:
                    if self.view == True:
                        # View deserves it's own section as this mode prints the list of views that a deliverable is part of, not printing the deliverable object itself
                        views = self.familyobj.get_views()
                        results = []
                        for view in views:
                            deliverables = [x.deliverable for x in view.get_deliverables()]
                            if self.deliverable in deliverables:
                                results.append(view)                                     
                        for view in results:
                            print(view)
                    else:
                        raise ListEcosphereError('This mode is not supported. To get a deliverable object info, please use \'--ip <IP> --deliverable {}\''.format(self.deliverable))
                else:                    
                    if self.ip_type:                
                        if self.roadmap:
                            if ':' in self.deliverable:
                                deliverable, slice = self.deliverable.split(':')
                                deliverable = self.familyobj.get_iptype(self.ip_type).get_deliverable(deliverable, roadmap=self.roadmap).get_slice(slice)
                            else:
                                deliverable = self.familyobj.get_iptype(self.ip_type).get_deliverable(self.deliverable, roadmap=self.roadmap)                    
                        else:
                            raise ListEcosphereError('Roadmap needs to be provided to get a deliverable of an IPType.')                                
                    elif self.ip:
                        if ':' in self.deliverable:
                            deliverable, slice = self.deliverable.split(':')
                            deliverable = self.familyobj.get_ip(self.ip, self.project).get_deliverable(deliverable).get_slice(slice)
                        else:
                            deliverable = self.familyobj.get_ip(self.ip, self.project).get_deliverable(self.deliverable)                  
                        cell = self.cell if self.cell else ''
                        deliverable._pattern = deliverable.get_patterns(ip=self.ip, cell=self.cell)
                        deliverable._filelist = deliverable.get_filelists(ip=self.ip, cell=self.cell)
                    else:
                        raise ListEcosphereError('IP or ip-type needs to be provided to list deliverables.')                
                    self.print_ecosphere_object(deliverable) 
        elif self.ip_type:
            if self.ip_type == True:
                ip_types = self.familyobj.get_iptypes()
                for type in ip_types:
                    print(type)
            else:
                ip_type = self.familyobj.get_iptype(self.ip_type)
                self.print_ecosphere_object(ip_type)                     
        elif self.ip:
            if self.ip == True:
                product = "" if self.product == None else self.product
                ips = self.familyobj.get_ips_names(product_filter=product)
                for ip in ips:
                    print(ip)
            else:
                ip = self.familyobj.get_ip(self.ip, self.project) 
                self.print_ecosphere_object(ip) 
        elif self.revision:
            if self.revision == True:
                if self.product and self.product != True:
                    revisions = self.familyobj.get_product(self.product).get_revisions()
                else:
                    raise ListEcosphereError('Product needs to be provided to list revisions')                
                for revision in revisions:
                    print(revision)
            else:
                if self.product:
                    revision = self.familyobj.get_product(self.product).get_revision(self.revision)
                else:
                    raise ListEcosphereError('Product needs to be provided to list revisions')              
                self.print_ecosphere_object(revision)        
        elif self.product:
            if self.product == True:
                products = self.familyobj.get_products()
                for product in products:
                    print(product) 
            else:
                if self.milestone:
                    if self.milestone == '99':
                        milestones = self.familyobj.get_product(self.product).get_milestones()
                        for milestone in milestones:
                            print(milestone)
                    else:
                        milestone = self.familyobj.get_product(self.product).get_milestone(self.milestone) 
                        self.print_ecosphere_object(milestone)
                else:                        
                    product = self.familyobj.get_product(self.product)                    
                    self.print_ecosphere_object(product)
        elif self.roadmap:
            if self.roadmap == True:
                roadmaps = self.familyobj.get_roadmaps()
                for roadmap in roadmaps:
                    print(roadmap)
            else:
                roadmap = self.familyobj.get_roadmap(self.roadmap)
                self.print_ecosphere_object(roadmap)                              
        elif self.view:
            if self.view == True:
                views = self.familyobj.get_views()
                for view in views:
                    print(view)
            else:
                view = self.familyobj.get_view(self.view)
                self.print_ecosphere_object(view)
        elif self.project:
            if self.project == True:
                projects = self.familyobj.get_icmprojects()
                for project in projects:
                    print(project)
            else:
                project = self.familyobj.get_icmproject(self.project)                    
                self.print_ecosphere_object(project)
        elif self.family:
            if self.family == True:
                families = self.ecosphere.get_families()
                for family in families:
                    print(family)
            else:
                self.print_ecosphere_object(self.familyobj)
        else:
            families = self.ecosphere.get_families()
            for family in families:
                print(family)
            
        return 0            


    def print_all_available_threads_for_all_families(self):
        families = self.ecosphere.get_families()
        for f in families:
            print(f)
            print('===============')
            for ms,thread in f.get_valid_milestones_threads():
                if ms != '99':
                    print('- {}/{}'.format(thread, ms))
            print()


    def print_ecosphere_object(self, object, bom=None):
        try:
            if bom:
                # Some objects require bom to be passed in to preload the object
                # for example, cell
                object._preload(bom=bom)
            else:                
                object._preload()
        except Exception as e:
            raise ListEcosphereError(e)
        dict = object.__dict__            
        keys_to_skip = ['preview', 'preloaded', 'obj', 'properties_loaded']
        for key in sorted(dict.keys()):
            skip = False
            for key_to_skip in keys_to_skip:
                if key_to_skip in key:
                    skip = True
            if not skip:                    
                value = dict[key]
                if value:                    
                    print(self.format_ecosphere_values_for_print(key.strip('_'), value))

    def format_ecosphere_values_for_print(self, key, value):
        if type(value) is dict:
            results = '{}:\n'.format(key)
            for num, key2 in enumerate(sorted(value.keys())):
                num_of_key2s = len(list(value.keys()))
                if type(value[key2]) is list:
                    results = '{}\t{}:'.format(results, key2)
                    for value2 in value[key2]: 
                        results = '{} {}'.format(results, value2)
                elif type(value[key2]) is dict:
                    results = '{}\t{}:\n\t\t'.format(results, key2)
                    for num2, key3 in enumerate(sorted(value[key2].keys())):
                        num_of_key3s = len(list(value[key2].keys()))
                        results = '{}{}: {}'.format(results, key3, value[key2][key3])
                        if num2 != (num_of_key3s - 1):
                            results = '{}\n\t\t'.format(results)
                if num != (num_of_key2s - 1):
                    results = '{}\n'.format(results)                        
        elif type(value) is list:
            results = '{}:'.format(key)
            for num, value2 in enumerate(value):
                num_of_values = len(value)                
                results = '{} {}'.format(results, value2)
                if num != (num_of_values - 1):
                    results = '{},'.format(results)
        else:
            results = '{}: {}'.format(key, value)
                        
        return results

    def run(self):
        '''
        Runs the ecosphere command
        '''
        ret = 1

        ret = self.print_results()
        return ret
