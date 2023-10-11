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
import re
from dmx.abnrlib.command import Command, Runner
from dmx.syncpointlib.syncpoint_webapi import SyncpointWebAPI, SyncpointWebAPIError
from dmx.utillib.utils import get_altera_userid
ACCESS_LEVEL = {
                'admin' :1,
                'fclead':2,
                'sslead':3,
                'owner' :4,
                'user' :5,             
               }

class CreateError(Exception): pass

class CreateRunner(Runner):
    LOGGER = logging.getLogger(__name__)
     
    def __init__(self, syncpoint, syncpoint_category, description):
        self.user = get_altera_userid(os.getenv('USER'))
        self.syncpoint = syncpoint
        self.description = description
        self.syncpoint_category = syncpoint_category
        self.sp = SyncpointWebAPI()

        #check if syncpoint exists
        if self.sp.syncpoint_exists(syncpoint):
            raise CreateError("Syncpoint {0} already exists".format(self.syncpoint))
        
        #get user's access level
        user_roles = self.sp.get_user_roles(self.user)       
        self.user_highest_access_level = ACCESS_LEVEL['user']
        for user_role in user_roles:
            if self.user_highest_access_level >= ACCESS_LEVEL[user_role]:
                self.user_highest_access_level = ACCESS_LEVEL[user_role]

        #check if user has permission to create a new syncpoint
        #only fclead may create a new syncpoint
        if not self.user_highest_access_level <= ACCESS_LEVEL['fclead']:
            raise CreateError("You do not have permission to create a new syncpoint.\nOnly fclead may create a new syncpoint.")

    def run(self):   
        ret = 1
                       
        ### http://pg-rdjira:8080/browse/DI-1064
        ### Only allow syncpoint name with the following scheme
        kwargs = {
            'letter': '[a-zA-Z]',
            'digit' : '[0-9]',
            'special':'[-_.]'
        }
        regex = '^{letter}({letter}|{digit}|{special})*({letter}|{digit})$'.format(**kwargs)
        match = re.search(regex, self.syncpoint)
        if not match:
            raise CreateError("Illegal synpoint name. \nSyncpoint name must follow strictly with this syntax: {}".format(regex))


        #create the syncpoint
        ret = self.sp.create_syncpoint(self.syncpoint, self.syncpoint_category, self.user, self.description)
        if not ret:
            self.LOGGER.info("Syncpoint {0} has been successfully created for category {1}".format(self.syncpoint, self.syncpoint_category))
         
        return ret
            
class Create(Command):
    '''plugin for "syncpoint create"'''
    
    LOGGER = logging.getLogger(__name__)
        
    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "syncpoint create"'''
        return 'Adds a new syncpoint to the master lists'

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            Description
            ===========
            Syncpoint create command creates a new syncpoint.
            This syncpoint would be used in tandem with abnr buildconfig to build a composite configuration
            based on the list of configurations in the syncpoint.
            For more information, visit https://wiki.ith.intel.com/display/tdmaInfra/Syncpoint+-+Coordinating+revisions+for+shared+collateral
         
            Usage
            =====
            syncpoint create -s <syncpoint name> -d <description> -sc <syncpoint-category>

            Example
            =====
            syncpoint create -s MS2.0 -d <Add new milestone> -sc my_syncpoint
            This creates a new syncpoint named MS2.0 for category my_syncpoint with a description "Add new milestone"
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "syncpoint create" subcommand'''
        parser.add_argument('-s', '--syncpoint', metavar='syncpoint', required=True,
            help='Syncpoint name')
        parser.add_argument('-d', '--description', metavar='description', required=True,
            help='Description of the syncpoint')
        parser.add_argument('-sc', '--syncpoint-category', metavar='syncpoint-category', required=True, 
            help='Category for the new syncpoint')
        parser.add_argument('--debug',   action='store_true', help='enable developer debugging')

    @classmethod
    def command(cls, args):
        '''syncpoint create command'''

        syncpoint = args.syncpoint
        description = args.description
        syncpoint_category = args.syncpoint_category

        ret = 1
        runner = CreateRunner(syncpoint, syncpoint_category, description)
        ret = runner.run()
                
        sys.exit(ret)



       
