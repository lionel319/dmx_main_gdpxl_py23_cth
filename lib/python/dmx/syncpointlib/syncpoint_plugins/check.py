#!/usr/bin/env python
'''
Description: plugin for "syncpoint add"

Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915,W0511
import sys
import os
import textwrap
import logging
import getpass
import datetime
from pprint import pprint, pformat

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from dmx.abnrlib.command import Command, Runner
#why do we use this? why not dmx.abnrlib.icmcompositeconfig.py?
#the effort to move to icmcompositeconfig is significantly higher, to explore in the future
from dmx.syncpointlib.composite_configs import CompositeConfigHierarchy
from dmx.syncpointlib.syncpoint_webapi import SyncpointWebAPI, SyncpointWebAPIError
import dmx.abnrlib.config_factory

import dmx.abnrlib.flows.checkconfigs


class CheckError(Exception): pass

class CheckRunner(Runner):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, syncpoint):
        self.syncpoint = syncpoint
        self.sp = SyncpointWebAPI()
              
        #check if syncpoint exists
        if not self.sp.syncpoint_exists(syncpoint):
            raise CheckError("Syncpoint {0} does not exist".format(self.syncpoint))

    def run(self):
        cc = dmx.abnrlib.flows.checkconfigs.CheckConfigs(syncpoints=[self.syncpoint])
        self.conflicts = cc.run()
        if self.conflicts:
            self.LOGGER.error("Conflicts found !")
            self.LOGGER.error(pformat(self.conflicts))

    def run_old(self):
        ret = 1
       
        checkconflict = CheckConflict(self.syncpoint)
         
        conflicts = checkconflict.get_list_of_conflicts()
        if conflicts:    
            #print conflicts
            checkconflict.print_conflicts()
            raise CheckError("There is/are %s conflicts in syncpoint %s. Please resolve the conflicts before performing any further abnr or syncpoint commands with this syncpoint." % (len(conflicts), self.syncpoint))
        else:
            self.LOGGER.info("There is no configuration error in syncpoint {0}".format(self.syncpoint))

        return ret

class CheckConflict():
    LOGGER = logging.getLogger(__name__)

    def __init__(self, syncpoint):
        self.syncpoint = syncpoint
        self.sp = SyncpointWebAPI()
        self.dict = {}
        self.conflicts = []
        
        #build dict of syncpoints and all its project,variant,configuration tree
        self.build_config_dict() 
        
        #check if there is any conflict in the configuration associated with syncpoint
        self.check_config_conflict()  
        
    def get_list_of_conflicts(self):
        return self.conflicts      
    
    def print_conflicts(self):
        for conflict in self.conflicts:
            (psp,psv,psc),(csp,csv,csc) = conflict['src']
            (pdp,pdv,pdc),(cdp,cdv,cdc) = conflict['dest']
            self.LOGGER.info("%s/%s@%s -> %s/%s@%s conflicts with\n\t%s/%s@%s -> %s/%s@%s\n" % (psp,psv,psc,csp,csv,csc,pdp,pdv,pdc,cdp,cdv,cdc))
        
    def build_config_dict(self):
        pvc = self.get_list_of_releases(self.syncpoint)     
        for p,v,c in pvc:
            if p not in self.dict:
                self.dict[p] = {}
            if v not in self.dict[p]:
                self.dict[p][v] = {}
            self.dict[p][v][c] = []

            #expand configuration tree
            if c:
                cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(p, v, c)
                for cc in cf.flatten_tree():
                    if cc.is_config():
                        self.dict[p][v][c].append([cc.project, cc.variant, cc.config])

        return self.dict

    def check_config_conflict(self, project=None, variant=None, config=None):
        conflicts = []
        dict_to_check = self.dict
        if project and variant and config:
            tree = []
            cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(project, variant, config)
            for cc in cf.flatten_tree():
                if not cc.is_simple():
                    tree.append([cc.project, cc.variant, cc.config])

            #if a variant is already released, we need to delete the release fron the dict first before appending the new release into the dict             
            if project in dict_to_check and variant in dict_to_check[project]:
                existing_config = dict_to_check[project][variant].keys()[0]
                del dict_to_check[project][variant][existing_config]
            else:
                if project not in dict_to_check:
                    dict_to_check[project] = {}
                if variant not in dict_to_check[project]:                    
                    dict_to_check[project][variant] = {}
            dict_to_check[project][variant][config] = tree

        for pp in dict_to_check:
            for vv in dict_to_check[pp]:
                for cc in dict_to_check[pp][vv]:
                    for p,v,c in dict_to_check[pp][vv][cc]:
                        dests = self.find_config_conflict(p,v,c)
                        src = [(pp,vv,cc),(p,v,c)]
                        if dests:
                            for dest in dests:
                                #remove duplicate entries
                                if {'src':dest,'dest':src} not in conflicts:
                                    conflicts.append({'src':src,'dest':dest})
        self.conflicts = conflicts
        return self.conflicts

    def find_config_conflict(self, project, variant, config):    
        conflicts = []
        for p in self.dict:
            for v in self.dict[p]:
                for c in self.dict[p][v]:
                    for p2,v2,c2 in self.dict[p][v][c]:
                        if project == p2 and variant == v2 and config != c2:
                            if [(p,v,c),(p2,v2,c2)] not in conflicts:                            
                                conflicts.append([(p,v,c),(p2,v2,c2)])
        return conflicts

    def get_list_of_releases(self, syncpoint):
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
            ret.append([str(p),str(v),str(c)])

        return ret

class Check(Command):
    '''plugin for "syncpoint check"'''
    
    LOGGER = logging.getLogger(__name__)
        
    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "syncpoint check"'''
        return 'Check for configuration conflicts in the given syncpoint'

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            Description
            ===========
            Syncpoint check command checks for configuration conflicts in the configuration tree of the given syncpoint.
            As syncpoint could associate project/variant of any REL configs, conflict may arise when a variantA@REL1 of a project/variantB@REL2 conflicts with another variantA@REL2 of a project/variantC@REL2           
            For more information, visit https://wiki.ith.intel.com/display/tdmaInfra/Syncpoint+-+Coordinating+revisions+for+shared+collateral
           
            Usage
            =====
            syncpoint check -s <syncpoint> 
            Checks for configuration conflict of syncpoint s
            
            Example
            =====
            syncpoint check -s MS1.0
            Checks syncpoint MS1.0 for any configuration conflict in all its project/variant@configuration
            ...
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "syncpoint check" subcommand'''
        parser.add_argument('-s', '--syncpoint', metavar='syncpoint',required=True,
            help='Syncpoint to be checked')
        parser.add_argument('--debug',   action='store_true', help='enable developer debugging')

    @classmethod
    def command(cls, args):
        '''syncpoint check command'''

        syncpoint = args.syncpoint
            
        ret = 1
        runner = CheckRunner(syncpoint)
        ret = runner.run()

        sys.exit(ret)


        

                


