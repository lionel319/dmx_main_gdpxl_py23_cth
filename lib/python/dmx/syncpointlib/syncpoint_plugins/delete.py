#!/usr/bin/env python
'''
Description: plugin for "syncpoint delete"

Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
from __future__ import print_function
# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915,W0511
from builtins import input
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

class DeleteError(Exception): pass

class DeleteRunner(Runner):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, syncpoint, project, variant, yes, force, delete_all):
        self.user = get_altera_userid(os.getenv('USER'))
        self.syncpoint = syncpoint
        self.project = project
        self.variant = variant
        self.yes = yes
        self.force = force
        self.delete_all = delete_all
        self.sp = SyncpointWebAPI()
        self.icm = ICManageCLI()

        dmx.syncpointlib.syncpointlock_api.SyncpointLockApi().connect().raise_error_if_syncpoint_is_locked(self.syncpoint)

        #get user's access level
        user_roles = self.sp.get_user_roles(self.user)       
        self.user_highest_access_level = ACCESS_LEVEL['user']
        for user_role in user_roles:
            if self.user_highest_access_level >= ACCESS_LEVEL[user_role]:
                self.user_highest_access_level = ACCESS_LEVEL[user_role]

        #check if user has permission to use --delete-all switch  
        if self.delete_all: 
            if not self.user_highest_access_level <= ACCESS_LEVEL['fclead']:
                raise DeleteError("You do not have permission to delete a syncpoint without first deleting project/variant in the syncpoint.\nOnly admin may perform delete --delete-all on a syncpoint.")

        #check if syncpoint exists 
        if not self.sp.syncpoint_exists(syncpoint):
            raise DeleteError("Syncpoint {0} does not exist".format(self.syncpoint))
         
        #checks if project and variant are given in the arguments
        if self.project and self.variant:
            if not self.force:
                #if force switch is off, checks if project and variant exists in ICM
                if not self.icm.variant_exists(self.project, self.variant):
                    if not self.icm.project_exists(self.project):
                        raise DeleteError('Project {0} does not exist'.format(self.project))
                    else:
                        raise DeleteError('Variant {0} does not exist in project {1}'.format(self.variant, self.project))                
            #check if project/variant exists in the given syncpoint
            if not self.sp.project_variant_exists(self.syncpoint, self.project, self.variant):
                raise DeleteError("Project/Variant {0}/{1} do not exist for syncpoint {2}".format(self.project,self.variant,self.syncpoint))
        elif self.project or self.variant:
            #errors out if only one of the arguments is given
            raise DeleteError("Please ensure that project and variant are both provided")
        elif not self.project and not self.variant:
            #if --delete-all is specified, skip checking for project/variant in the syncpoint
            if not self.delete_all:
                #if project and variant are not given, user is trying to delete syncpoint
                #check if syncpoint still have project/variant associated with it
                ret = self.sp.get_releases_from_syncpoint(self.syncpoint)
                if ret:
                    #errors out if syncpoint still have project/variant associated with it
                    self.LOGGER.error("Syncpoint {0} still has project/variant associated with it".format(self.syncpoint))
                    print("Project/Variant/Release Configuration:")
                    for (p,v,c) in ret:
                        print("{0}/{1}@{2}".format(p,v,c))
                    raise DeleteError("Delete failed, please delete project/variant from the syncpoint before deleting the syncpoint")
                
        #check if user has permission to delete project/variant or syncpoint
        #only fclead may perform delete 
        if not self.user_highest_access_level <= ACCESS_LEVEL['fclead']:
            raise DeleteError("You do not have permission to delete a project/variant.\nOnly fclead may perform delete on a project/variant or syncpoint.")
        
    def run(self): 
        ret = 1      
        #if --delete-all is specified, deletes all project/variant in the syncpoint then delete the syncpoint
        #else perform a normal deletion 
        if self.delete_all:
            #ask for user confirmation before deleting syncpoint
            #for safety purposes, --yes switch will not bypass this confirmation agreement
            self.LOGGER.warning("Are you sure you would like to delete {0} and all its project/variant?".format(self.syncpoint))
            ans = ""
            while ans != 'y' and ans != 'n':
               ans = input("(y/n)?")

            if ans.lower() == 'y':
                #get pvc of syncpoint
                pvc = self.sp.get_releases_from_syncpoint(self.syncpoint)     
                #delete all project/variant associated with syncpoint
                for p,v,c in pvc:
                    self.sp.delete_syncpoint(self.syncpoint, p, v)
                #delete syncpoint
                ret = self.sp.delete_syncpoint(self.syncpoint)
                if not ret:
                    self.LOGGER.info("Syncpoint {0} has been successfully deleted".format(self.syncpoint))
            else:
                raise DeleteError("Delete aborted")                                         
        else:                                     
            if self.project and self.variant:
                #ask for user confirmation to delete, bypass this check if user turns on yes switch
                if self.yes:
                    ans = 'y'
                else:
                    self.LOGGER.warning("Are you sure you would like to delete {0}/{1}?".format(self.project,self.variant))
                    ans = ""
                    while ans != 'y' and ans != 'n':
                        ans = input("(y/n)?")
    
                if ans.lower() == 'y':
                    #deletes the project/variant from the syncpoint
                    ret = self.sp.delete_syncpoint(self.syncpoint, self.project, self.variant)
                    if not ret:
                        self.LOGGER.info("Project/Variant {0}/{1} has been successfully deleted from syncpoint {2}".format(self.project,self.variant,self.syncpoint))
                else:
                    raise DeleteError("Delete aborted")
            else:
                #ask for user confirmation to delete, bypass this check if user turns on yes switch
                if self.yes:
                    ans = 'y'
                else:
                    self.LOGGER.warning("Are you sure you would like to delete syncpoint {0}".format(self.syncpoint))
                    ans = input("(y/n)?")
    
                if ans.lower() == 'y':
                    #deletes the syncpoint
                    ret = self.sp.delete_syncpoint(self.syncpoint)
                    if not ret:
                        self.LOGGER.info("Syncpoint {0} has been successfully deleted".format(self.syncpoint))
                else:
                    raise DeleteError("Delete aborted")     
        return ret

class Delete(Command):
    '''plugin for "syncpoint delete"'''
    
    LOGGER = logging.getLogger(__name__)
        
    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "syncpoint delete"'''
        return 'Delete a syncpoint or project/variant associated with the syncpoint'

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            Description
            ===========
            Syncpoint delete command deletes syncpoint if project/variant are not provided.
            Syncpoint delete command deletes project/variant associated with the sycnpoint if project/variant are provided.
            For more information, visit https://wiki.ith.intel.com/display/tdmaInfra/Syncpoint+-+Coordinating+revisions+for+shared+collateral
            
            Usage
            =====
            syncpoint delete -s <syncpoint name> 
            Deletes a syncpoint
            Errors if there is at least 1 project/variant still associated with the syncpoint

            syncpoint delete -s <syncpoint name> -p <project> -v <variant>            
            Deletes a project/variant associated with the syncpoint 
                       
            Example
            =====
            syncpoint delete -s MS1.0
            Deletes syncpoint MS1.0 if there is no project/variant associated with it

            syncpoint delete -s MS1.0 -p i14socnd -v ar_lib
            Deletes i14socnd/ar_lib association from MS1.0
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "syncpoint delete" subcommand'''
        parser.add_argument('-s', '--syncpoint', metavar='syncpoint', required=True,
            help='Syncpoint name')
        parser.add_argument('-p', '--project', metavar='project',
            help='Project to be removed')
        parser.add_argument('-v', '--variant', metavar='variant',  
            help='Variant to be removed')
        parser.add_argument('-y', '--yes', action='store_true',
            help='Yes to delete confirmation')
        parser.add_argument('-f', '--force', action='store_true',
            help='Force syncpoint delete to delete project/variant even if they do not exist in ICM')      
        parser.add_argument('--delete-all', action='store_true', 
            help='WARNING: USE WITH CAUTION. Switch to recursively delete all project/variant associated with the syncpoint and delete the syncpoint. Only usable by admin role')
        parser.add_argument('--debug',   action='store_true', help='enable developer debugging')

    @classmethod
    def command(cls, args):
        '''syncpoint create command'''

        syncpoint = args.syncpoint
        project = args.project
        variant = args.variant
        yes = args.yes
        force = args.force
        delete_all = args.delete_all

        ret = 1
        runner = DeleteRunner(syncpoint, project, variant, yes, force, delete_all)
        ret = runner.run()

        sys.exit(ret)
        
                
        
        




    


