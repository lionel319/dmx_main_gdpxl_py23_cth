#!/usr/bin/env python
'''
Description: plugin for "syncpoint_user list"

Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
from __future__ import print_function
# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915,W0511
import sys
import os
import textwrap
import logging
import getpass
import subprocess
from dmx.abnrlib.command import Command, Runner
from dmx.syncpointlib.syncpoint_webapi import SyncpointWebAPI, SyncpointWebAPIError
from dmx.utillib.utils import get_altera_userid

class ListError(Exception): pass

class ListRunner(Runner):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, user, role):
        self.sp = SyncpointWebAPI()               
        self.user = get_altera_userid(user) if user else ''
        self.role = role

        if not self.user and not self.role:
            raise ListError("Please provide either -u user or -r role argument")
        elif self.user:
            if not self.user_exists(user):
                raise ListError("User {0} does not exist".format(user))
           
    def run(self):
        ret = 1

        if self.user:
            roles = self.sp.get_user_roles(self.user)
            if roles:
                for role in roles:
                    print(role)
            else:
                self.LOGGER.info("{0} has no roles in syncpoint".format(self.user))
        
        if self.role:
            users = self.sp.get_users_by_role(self.role)
            if users:
                for user in users:
                    print(user)
            else:
                self.LOGGER.info("{0} has no users in syncpoint".format(self.role))
        ret = 0                                
        return ret

    def user_exists(self, user):
        cmd = "finger {0}".format(user)
        (exitcode, stdout, stderr) = self.run_command(cmd)
        if exitcode == 0:
            if stderr.find("no such user") != -1:
                return False
            elif stderr:
                raise DeleteError("stdout: {0}\nstderr: {1}".format(stdout,stderr))
        else:
            raise DeleteError("stdout: {0}\nstderr: {1}".format(stdout,stderr))
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
        return (exitcode, stdout.decode(), stderr.decode())

class List(Command):
    '''plugin for "syncpoint_user list"'''
    
    LOGGER = logging.getLogger(__name__)
        
    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "syncpoint_user list"'''
        return "Returns user's roles and users by roles"

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            Description
            ===========
            Syncpoint_user list command returns user's roles and users by roles.
            There are 3 roles:
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
            For more information, visit https://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/Syncpoint
            
            Usage
            =====
            syncpoint_user list -u <user>
            List user's roles

            syncpoint_user list -r <role>
            List users by roles

            Example
            =====
            syncpoint_user list -u abc
            List abc's roles

            syncpoint_user list -r admin
            List users with admin role
            ...
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "syncpoint_user list" subcommand'''
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-u', '--user', metavar='user',
            help='User ID')
        group.add_argument('-r', '--role', metavar='role', choices = ['admin', 'fclead', 'sslead', 'owner', 'user'], 
            help='Syncpoint_user role')
        parser.add_argument('--debug',   action='store_true', help='enable developer debugging')

    @classmethod
    def command(cls, args):
        '''syncpoint_user list command'''

        user = args.user
        role = args.role
         
        ret = 1
        runner = ListRunner(user, role)
        ret = runner.run()
                 
        sys.exit(ret)

       



            







