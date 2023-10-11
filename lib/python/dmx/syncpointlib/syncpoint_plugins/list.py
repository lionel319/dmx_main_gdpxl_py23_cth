#!/usr/bin/env python
'''
Description: plugin for "syncpoint list"

Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
from __future__ import print_function
# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915,W0511
from builtins import str
import sys
import os
import textwrap
import logging
from dmx.abnrlib.command import Command, Runner
from dmx.abnrlib.icm import ICManageCLI
from dmx.syncpointlib.syncpoint_webapi import SyncpointWebAPI, SyncpointWebAPIError

class ListError(Exception): pass

class ListRunner(Runner):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, syncpoint, syncpoint_category, project, variant, force, debug):
        self.syncpoint = syncpoint
        self.syncpoint_category = syncpoint_category
        self.project = project
        self.variant = variant
        self.force = force
        self.debug = debug
        self.sp = SyncpointWebAPI()
        self.icm = ICManageCLI()
         
        #check if syncpoint exists
        if self.syncpoint:
            if not self.sp.syncpoint_exists(syncpoint):
                raise ListError("Syncpoint {0} does not exist".format(self.syncpoint))
      
        #if syncpoint-category is given, check if it exists
        if self.syncpoint_category:
            if not self.sp.syncpoint_category_exists(syncpoint_category):
                raise ListError("Syncpoint-category {0} does not exist".format(self.syncpoint_category))

        #errors out if variant is given but not project
        if self.variant and not self.project:
            raise ListError("Please ensure that project is provided as well together with variant")

        if not self.force: 
            #if force swithc is off, check if project/variant exists 
            if self.variant:
                if not self.icm.variant_exists(self.project, self.variant):
                    raise ListError('Variant {0} does not exist in project {1}'.format(self.variant, self.project))

            if self.project: 
                if not self.icm.project_exists(self.project):
                    raise ListError('Project {0} does not exist'.format(self.project))

    def run(self):
        if self.syncpoint and self.project and self.variant:
            print(self.get_list_of_releases(self.syncpoint, self.project, self.variant))
        elif self.syncpoint and self.project and not self.variant:
            ret = self.get_list_of_releases(self.syncpoint, self.project)
            print("Variant/Release Configuration:")
            for (v,c) in ret:
                print("{0}/{1}".format(v,c))
        elif self.syncpoint and not self.project and not self.variant:
            ret = self.get_list_of_releases(self.syncpoint, self.project, self.variant)
            print("Project/Variant/Release Configuration:")
            for (p,v,c) in ret:
                print("{0}/{1}@{2}".format(p,v,c))
        elif self.syncpoint_category:
            ret = self.get_list_of_syncpoints(self.syncpoint_category)
            for s in ret:
                print(s)
        else:
            ret = self.get_list_of_syncpoints()
            print("Syncpoint-category/Syncpoint:")
            for (sc,c) in ret:
                #list test category only if debug switch is turned on
                if "test" in sc and not self.debug:
                    continue
                print("{0}/{1}".format(sc,c))
        return 0

    def get_list_of_syncpoints(self, syncpoint_category = None):
        '''
        Gets a list of syncpoints
        If syncpoint-category is not given, returns a list of all syncpoints
        If syncpoint-category is given, returns a list of all syncpoints associated with the given syncpoint-category
        '''
        ret = []
        results = self.sp.get_syncpoints()       
        results.sort()

        for (s, sc) in results:
            if sc == syncpoint_category:
                ret.append(str(s))
            elif not syncpoint_category:
                ret.append([str(sc), str(s)])
        return ret
    
    def get_list_of_releases(self, syncpoint, project = None, variant = None):
        '''
        Gets a list of configurations associated with the given syncpoint
        If project and variant are not given, returns a list of project/variant/configurations associated with the given syncpoint
        If project is given, returns a list of variant/configurations associated with the given syncpoint/project
        If project and variant is given, returns configuration associated with the given syncpoint/project/variant
        '''
        ret = []
        results = self.sp.get_releases_from_syncpoint(syncpoint)
        results.sort()
            
        for (p,v,c) in results:
            if p == project and v == variant:
                return str(c)
            elif p == project and not variant:
                ret.append([str(v),str(c)])
            elif not project and not variant:
                ret.append([str(p),str(v),str(c)])

        return ret

class List(Command):
    '''plugin for "syncpoint list"'''
    
    LOGGER = logging.getLogger(__name__)
        
    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "syncpoint list"'''
        return 'Returns all the sycnpoints and its project/variant/configuration'

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            Description
            ===========
            Syncpoint list command returns all the syncpoints and its project/variant/configurations.
            For more information, visit https://wiki.ith.intel.com/display/tdmaInfra/Syncpoint+-+Coordinating+revisions+for+shared+collateral
            
            Usage
            =====
            syncpoint list 
            List all the registered syncpoints

            syncpoint list -sp <syncpoint-category>
            List all the registered syncpoints for the selected syncpoint-category

            syncpoint list -s <syncpoint>
            List the variant/release configurations associated with the selected syncpoint

            syncpoint list -s <syncpoint> -p <project> -v <variant>
            List the release configuration associated with the selected syncpoint, project and variant

            Example
            =====
            syncpoint list 
            Category        Syncpoint
            my_syncpoint    MS1.1_for_testing
            kwlim_sync      MS2.0_for_prod
            ...

            syncpoint list -sc my_syncpoint
            MS1.1_for_testing
            ...

            syncpoint list -s  MS1.1_for_testing
            Project/Variant/Release Configuration
            i14socnd/ar_lib/REL2.0
            i14socnd/cc_lib/REL3.0
            ...

            syncpoint list -s  MS1.1_for_testing -p i14socnd -v ar_lib 
            REL2.0
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "syncpoint list" subcommand'''
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-s', '--syncpoint', metavar='syncpoint',
            help='Syncpoint name')
        group.add_argument('-sc', '--syncpoint-category', metavar='syncpoint-category',
            help='Syncpoint-category to be queried')
        parser.add_argument('-p', '--project', metavar='project', 
            help='ICM Project to be queried')
        parser.add_argument('-v', '--variant', metavar='variant', 
            help='ICM Variant to be queried')
        parser.add_argument('-f', '--force', action='store_true',
            help='Force syncpoint list to list project/variant that does not exists in ICM')
        parser.add_argument('--debug',   action='store_true', help='enable developer debugging')

    @classmethod
    def command(cls, args):
        '''syncpoint list command'''

        syncpoint = args.syncpoint
        syncpoint_category = args.syncpoint_category
        project = args.project
        variant = args.variant
        force = args.force
        debug = args.debug
        
        ret = 1
        runner = ListRunner(syncpoint, syncpoint_category, project, variant, force, debug)
        ret = runner.run()

        sys.exit(ret)



