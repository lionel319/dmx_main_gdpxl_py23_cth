#!/usr/bin/env python
'''
Description: plugin for "syncpoint_user add"

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
import subprocess
from dmx.abnrlib.command import Command, Runner
from dmx.syncpointlib.syncpoint_webapi import SyncpointWebAPI, SyncpointWebAPIError
from dmx.utillib.utils import get_altera_userid, is_pice_env
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

    def __init__(self, users, roles):
        self.sp = SyncpointWebAPI()       
        self.users = [get_altera_userid(x) for x in users]
        self.roles = roles
        self.current_user = get_altera_userid(os.getenv('USER'))

        # if we are in PSG, we check whether user exist or not
        # if we are in PICE, the above API (get_altera_userid) already does the check for us in PICE
        if not is_pice_env():
            for user in self.users:            
                if not self.user_exists(user):
                    raise AddError("User {0} does not exist".format(user))

        current_user_roles = self.sp.get_user_roles(self.current_user)       
        user_highest_access_level =  ACCESS_LEVEL['user']
        for current_user_role in current_user_roles:
            if user_highest_access_level >= ACCESS_LEVEL[current_user_role]:
                user_highest_access_level = ACCESS_LEVEL[current_user_role]

        for role in self.roles:
            if user_highest_access_level > ACCESS_LEVEL[role]:
                raise AddError("{0} does not have permission to add user with {1} role".format(self.current_user, role))

    def run(self):
        ret = 1
        for user in self.users:
            for role in self.roles:
                try:
                    self.sp.add_user(user, role)   
                    self.LOGGER.info("{0} added with {1} role".format(user,role))     
                except SyncpointWebAPIError as e:
                    self.LOGGER.error(e)
                    continue

            #automatically add user to 'user' role if he/she is added as 'fclead,'sslead' or 'owner'
            if 'fclead' in self.roles or 'sslead' in self.roles or 'owner' in self.roles:
                try:
                    self.sp.add_user(user, 'user')   
                    self.LOGGER.info("{0} added with user role".format(user)) 
                except SyncpointWebAPIError as e:
                    self.LOGGER.error(e)
        else:
            ret = 0
       
        return ret

    def user_exists(self, user):
        cmd = "finger {0}".format(user)
        (exitcode, stdout, stderr) = self.run_command(cmd)
        if exitcode == 0:
            if stderr.find("no such user") != -1:
                return False
            elif stderr:
                raise AddError("stdout: {0}\nstderr: {1}".format(stdout,stderr))
        else:
            raise AddError("stdout: {0}\nstderr: {1}".format(stdout,stderr))
        return True

    def run_command(self, command):
        '''
        Run a system command and returns a tuple of (exitcode, stdout, stderr)

        >>> run_command('echo foo')
        (0, 'foo\\n', '')
        >>> run_command('ls /foo/bar')
        (2, '', 'ls: /foo/bar: No such file or directory\\n')
        '''
        proc = subprocess.Popen(command, bufsize=1, shell=True,
                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = proc.communicate(None)
        exitcode = proc.returncode
        return (exitcode, stdout, stderr)

class Add(Command):
    '''plugin for "syncpoint_user add"'''
    
    LOGGER = logging.getLogger(__name__)
        
    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "syncpoint_user add"'''
        return 'Add users and their roles for syncpoint'

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            Description
            ===========
            Syncpoint_user add command adds user and its role to database.
            There are 5 roles:
            Admin - syncpoint system admin
            FCLead - may perform create, delete, release, ,re-release, list ,check , add, copy
                     may add, delete user as fclead, sslead, owner, user
            SSLead - may perform release, re-release, list ,check , 
                     may add, delete user as sslead, owner, user
            Owner - may perform 1st release, list, check
                    may add, delete user as owner, user
            User - may perform list, check
                   may add, delete user as user
                   gets email notification whenever a new release is made
            'user' role is granted automatically when a user is added as fclead, sslead or owner.
            For more information, visit https://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/Syncpoint
            
            Usage
            =====
            syncpoint_user add -u <user> -r <role>
            Add user and its role to database

            Example
            =====
            syncpoint_user add -u abc -r admin
            Add abc with admin access

            syncpoint_user add -u abc def -r admin
            Add abc and def with admin access

            syncpoint_user add -u abc def -r admin user
            Add abc and def with admin and user access
            ...
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "syncpoint_user add" subcommand'''
        parser.add_argument('-u', '--users', metavar='users', nargs='+',required=True,
            help='User ID')
        parser.add_argument('-r', '--roles', metavar='roles', nargs='+', choices = ['admin', 'fclead', 'sslead', 'owner', 'user'],required=True, help='Syncpoint_user role')
        parser.add_argument('--debug',   action='store_true', help='enable developer debugging')

    @classmethod
    def command(cls, args):
        '''syncpoint_user add command'''

        users = args.users
        roles = args.roles
         
        ret = 1
        runner = AddRunner(users, roles)
        ret = runner.run()
                 
        sys.exit(ret)

       



            







