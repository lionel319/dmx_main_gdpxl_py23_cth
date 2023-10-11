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

class CopyError(Exception): pass

class CopyRunner(Runner):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, source, destination, description):
        self.user = get_altera_userid(os.getenv('USER'))
        self.source = source
        self.destination= destination
        self.description = description
        self.sp = SyncpointWebAPI()
         
        #check if source syncpoint exists
        if not self.sp.syncpoint_exists(self.source):
            raise CopyError("Syncpoint {0} does not exist".format(self.source))

        #check if destination syncpoint exists
        if self.sp.syncpoint_exists(self.destination):
            raise CopyError("Syncpoint {0} already exist".format(self.destination))
             
        #get user's access level
        user_roles = self.sp.get_user_roles(self.user)       
        self.user_highest_access_level = ACCESS_LEVEL['user']
        for user_role in user_roles:
            if self.user_highest_access_level >= ACCESS_LEVEL[user_role]:
                self.user_highest_access_level = ACCESS_LEVEL[user_role]

        #check if user has permission to copy
        #only fclead may run copy command
        if not self.user_highest_access_level <= ACCESS_LEVEL['fclead']:
            raise CopyError("You do not have permission to copy a syncpoint.\nOnly fclead may run copy command")

    def run(self):
        ret = 1
        #get pvc associated with source syncpoint       
        src_pvc = self.sp.get_releases_from_syncpoint(self.source)
        
        #get source syncpoint info
        category, owner, date, source_description = self.sp.get_syncpoint_info(self.source)
        #create the destination syncpoint
        description = "Copied from {0}. ".format(self.source)
        if self.description:
            description = description + self.description
        self.sp.create_syncpoint(self.destination, category, self.user, description)

        #add project/variant/configuration to destination syncpoint
        for p,v,c in src_pvc:
            self.sp.add_syncpoint(self.destination, p, v, self.user)
            if c:
                self.sp.release_syncpoint(self.destination, p, v, c, self.user)   
        ret = 0     

        return ret

class Copy(Command):
    '''plugin for "syncpoint copy"'''
    
    LOGGER = logging.getLogger(__name__)
        
    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "syncpoint copy"'''
        return 'Copy an existing syncpoint to a new syncpoint'

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            Description
            ===========
            Syncpoint copy command copies an existing syncpoint to a new syncpoint. It will attempt to create an exact copy of a given existing syncpoint and ignore any conflict that exists in the syncpoint. It is the user's responsibilities to ensure that the syncpoint to be copied from is clean and usable.
            For more information, visit https://wiki.ith.intel.com/display/tdmaInfra/Syncpoint+-+Coordinating+revisions+for+shared+collateral
           
            Usage
            =====
            syncpoint copy -src <src-syncpoint> -dst <dest-syncppoint> -d <description>
            Copy src-syncpoint to dest-syncpoint within the same syncpoint-category and append user's description to dest-syncpoint
            
            Example
            =====
            syncpoint copy -src MS1.0 -dst MS1.0_copy -d "Copy ms1.0"
            Copys MS1.0 to MS1.0_copy with the description "Copy ms1.0"
            ...
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "syncpoint copy" subcommand'''
        parser.add_argument('-src', '--src-syncpoint', metavar='src-syncpoint',required=True,
            help='Syncpoint to be copied')
        parser.add_argument('-dst', '--dest-syncpoint', metavar='dest-syncpoint', required=True,
            help='New syncpoint name to be copied to')
        parser.add_argument('-d', '--description', metavar='description', 
            help='Description to be given to the new syncpoint')
        parser.add_argument('--debug',   action='store_true', help='enable developer debugging')

    @classmethod
    def command(cls, args):
        '''syncpoint copy command'''

        src = args.src_syncpoint
        dest = args.dest_syncpoint
        desc = args.description
            
        ret = 1
        runner = CopyRunner(src, dest, desc)
        ret = runner.run()

        sys.exit(ret)


        

                


