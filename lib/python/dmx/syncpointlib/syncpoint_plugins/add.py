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

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, LIB)

import dmx.syncpointlib.syncpointlock_api
from dmx.abnrlib.command import Command, Runner
from dmx.abnrlib.icm import ICManageCLI
from dmx.syncpointlib.syncpoint_webapi import SyncpointWebAPI, SyncpointWebAPIError
from dmx.utillib.utils import get_altera_userid
ACCESS_LEVEL = {
                'admin' :1,
                'fclead':2,
                'sslead':3,
                'owner' :4,
                'user' :5,             
               }

class AddError(Exception): pass

class AddRunner(Runner):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, syncpoint, project, variant):
        #get alteraid if we are in PICE env
        self.user = get_altera_userid(os.getenv('USER'))
        self.syncpoint = syncpoint
        self.project = project
        self.variant = variant        
        self.sp = SyncpointWebAPI()       
        self.icm = ICManageCLI()

        dmx.syncpointlib.syncpointlock_api.SyncpointLockApi().connect().raise_error_if_syncpoint_is_locked(self.syncpoint)

        #check if syncpoint exists
        if not self.sp.syncpoint_exists(syncpoint):
            raise AddError("Syncpoint {0} does not exist".format(self.syncpoint))
      
        #check if project/variant exists  
        if not self.icm.variant_exists(self.project, self.variant):
            if not self.icm.project_exists(self.project):
                raise AddError('Project {0} does not exist'.format(self.project))
            else:
                raise AddError('Variant {0} does not exist in project {1}'.format(self.variant, self.project))

        #check if project/variant already in the given syncpoint
        if self.sp.project_variant_exists(self.syncpoint, self.project,self.variant):
            raise AddError("Project/Variant {0}/{1} already exists for syncpoint {2}".format(self.project, self.variant,self.syncpoint))

        #get user's access level       
        user_roles = self.sp.get_user_roles(self.user)       
        self.user_highest_access_level = ACCESS_LEVEL['user']
        for user_role in user_roles:
            if self.user_highest_access_level >= ACCESS_LEVEL[user_role]:
                self.user_highest_access_level = ACCESS_LEVEL[user_role]

        #check if user has permission to add a project/variant
        #only 'fclead' may add a project/variant
        if not self.user_highest_access_level <= ACCESS_LEVEL['fclead']:
            raise AddError("You do not have permission to add a project/variant.\nOnly fclead may add a new project/variant to syncpoint.")

    def run(self):
        ret = 1
      
        #add the project/variant to the syncpoint
        ret = self.sp.add_syncpoint(self.syncpoint, self.project, self.variant, self.user)
        if not ret:
            self.LOGGER.info("Project/variant {0}/{1} has been successfully added to syncpoint {2}".format(self.project, self.variant, self.syncpoint))

        return ret

class Add(Command):
    '''plugin for "syncpoint add"'''
    
    LOGGER = logging.getLogger(__name__)
        
    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "syncpoint add"'''
        return 'Associate a given project and variant to a given syncpoint'

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            Description
            ===========
            Syncpoint add command associates a given project and variant to a given syncpoint.
            Syncpoint add does not add release configuration to the syncpoint.
            After adding the project/variant, user may do syncpoint release command to update release configuration of the given project/variant.
            For more information, visit https://wiki.ith.intel.com/display/tdmaInfra/Syncpoint+-+Coordinating+revisions+for+shared+collateral
                        
            Usage
            =====
            syncpoint add -s <syncpoint> -p <project> -v <variant>
            Adds a new project/variant pair to syncpoint
            
            Example
            =====
            syncpoint add -s MS1.0 -p i14socnd -v ar_lib
            Adds i14socnd/ar_lib pair to MS1.0
            ...
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "syncpoint add" subcommand'''
        parser.add_argument('-s', '--syncpoint', metavar='syncpoint',required=True,
            help='Syncpoint name')
        parser.add_argument('-p', '--project', metavar='project', required=True,
            help='ICM Project to be queried')
        parser.add_argument('-v', '--variant', metavar='variant', required=True,
            help='ICM Variant to be queried')
        parser.add_argument('--debug',   action='store_true', help='enable developer debugging')

    @classmethod
    def command(cls, args):
        '''syncpoint add command'''

        syncpoint = args.syncpoint
        project = args.project
        variant = args.variant
        
        ret = 1
        runner = AddRunner(syncpoint, project, variant)
        ret = runner.run()
                 
        sys.exit(ret)
        
