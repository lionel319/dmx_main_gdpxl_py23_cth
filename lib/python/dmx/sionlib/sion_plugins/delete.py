#!/usr/bin/env python
'''
Description: plugin for sion "delete"

Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915,W0511
import sys
import pwd
import os
import textwrap
import logging
import getpass
from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.sionlib.sion_utils import run_as_headless_user

class DeleteError(Exception): pass

class DeleteRunner(Runner):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, dir):
        self.user = getpass.getuser()
        self.dir = dir
        self.command = 'delete'

        if not os.path.isdir(self.dir):
            raise DeleteError("Please ensure the given path is a directory.")

    def run(self):
        ret = 1

        ret = run_as_headless_user(dir = self.dir, command = self.command, user = self.user)

        return ret

class Delete(Command):
    '''plugin for "sion delete"'''
    
    LOGGER = logging.getLogger(__name__)
        
    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "sion delete"'''
        return 'Removes ICM data synced by psginfraadm from a user\'s local directory'

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            Description
            ===========
            Sion delete allows user to delete ICM data synced by psginfraadm.            
            For more information, visit https://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/SynchronizingICMDataOnNetwork.
                                                
            Usage
            =====
            sion delete -d user's local directory
            Deletes ICM data populated by psginfraadm onto user's local directory
           
            Example
            =====
            sion delete -d /home/kwlim/i14socnd/ar_lib/dev
            Deletes the directory dev from /home/kwlim/i14socnd/ar_lib. Delete will only be successful if this directory is created by psginfraadm.
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "sion delete" subcommand'''
        add_common_args(parser)
        parser.add_argument('-d', '--dir', metavar='user\'s local directory', required=True,
            help='User\'s local directory')

    @classmethod
    def command(cls, args):
        '''sion delete command'''
        
        dir = args.dir
        
        ret = 1
        runner = DeleteRunner(dir)
        ret = runner.run()
                 
        sys.exit(ret)
        
