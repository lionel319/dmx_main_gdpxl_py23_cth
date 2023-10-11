#!/usr/bin/env python
'''
Description: plugin for sion "list"

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

class ListError(Exception): pass

class ListRunner(Runner):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, project, variant, libtype, config):
        self.user = getpass.getuser()        
        self.command = 'list'                
        self.project = project        
        self.variant = variant
        self.libtype = libtype
        self.config = config

    def run(self):
        ret = 1

        ret = run_as_headless_user(command = self.command, user = self.user, project= self.project, variant = self.variant, libtype = self.libtype, config = self.config)

        return ret

class List(Command):
    '''plugin for "sion list"'''
    
    LOGGER = logging.getLogger(__name__)
        
    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "sion list"'''
        return 'List ICM project/variant/configurations'

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            Description
            ===========
            Sion list allows user to list ICM project/variant/configuration.            
            For more information, visit https://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/SynchronizingICMDataOnNetwork.
                                                
            Usage
            =====
            sion list -p i14socnd -v ar_lib -c dev
            Returns i14socnd/ar_lib/dev if the composite configuration exists

            sion list -p i14socnd -v ar_lib -l rtl -c dev
            Returns i14socnd/ar_lib/rtl/dev if the simple configuration exists

            sion list -p i14socnd -v ar_lib -c 
            Returns a list of configurations for i14socnd/ar_lib

            sion list -p i14socnd -v ar_lib -c REL*
            Returns a list of configurations for i14socnd/ar_lib that starts with REL

            sion list -p i14socnd -v 
            Returns a list of variants for i14socnd

            sion list -p i14socnd -v ar_lib -l
            Returns a list of libtypes for i14socnd/ar_lib
    
            sion list -p i14socnd -v ar_lib -l rtl -L
            Returns a list of libraries for i14socnd/ar_lib/rtl

            sion list -p i14socnd -v ar_lib -l rtl -L dev -r
            Returns a list of releases for i14socnd/ar_lib/rtl/dev
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "sion list" subcommand'''
        add_common_args(parser)
        parser.add_argument('-p', '--project', metavar='project', nargs='?', const="'*'", help='Project')
        parser.add_argument('-v', '--variant', metavar='variant', nargs='?', const="'*'", help='Variant')
        parser.add_argument('-l', '--libtype', metavar='libtype', nargs='?', const="'*'", help='Libtype')
        parser.add_argument('-c', '--config', metavar='config', nargs='?', const="'*'", help='Configuration')

    @classmethod
    def command(cls, args):
        '''sion list command'''
         
        project = args.project
        variant = args.variant
        libtype = args.libtype
        config = args.config
        
        ret = 1
        runner = ListRunner(project, variant, libtype, config)
        ret = runner.run()
                 
        sys.exit(ret)
        
