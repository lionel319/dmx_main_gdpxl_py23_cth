#!/usr/bin/env python
'''
Description: plugin for sion "printconfig"

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
from dmx.sionlib.sion_utils import run_as_psginfraadm

class PrintconfigError(Exception): pass

class PrintconfigRunner(Runner):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, project, variant, config, show_simple, show_libraries):
        self.user = getpass.getuser()        
        self.command = 'printconfig'                
        self.project = project        
        self.variant = variant
        self.config = config
        self.show_simple = show_simple
        self.show_libraries = show_libraries

    def run(self):
        ret = 1

        misc = "'show_simple':'%s','show_libraries':'%s'" % (self.show_simple, self.show_libraries)
        ret = run_as_psginfraadm(command = self.command, user = self.user, project= self.project, variant = self.variant, config = self.config, misc = misc)

        return ret

class Printconfig(Command):
    '''plugin for "sion printconfig"'''
    
    LOGGER = logging.getLogger(__name__)
        
    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "sion printconfig"'''
        return 'Returns a tree of project/variant/configurations'

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            Description
            ===========
            Sion printconfig allows user to describe ICM project/variant/configuration.            
            For more information, visit https://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/SynchronizingICMDataOnNetwork.
                                                
            Usage
            =====
            sion printconfig -p i14socnd -v ar_lib -c dev
            Returns tree of configuration of i14socnd/ar_lib/dev 
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "sion printconfig" subcommand'''
        add_common_args(parser)
        parser.add_argument('-p', '--project', metavar='project', required=True, help='Project')
        parser.add_argument('-v', '--variant', metavar='variant', required=True, help='Variant')
        parser.add_argument('-c', '--config', metavar='config', required=True, help='Configuration')
        parser.add_argument('--show-simple', action='store_true', help='Include simple configurations in the output')
        parser.add_argument('--show-libraries', action='store_true', help='Show library and release information. \
                                                                           Implies show-simple is also True.')

    @classmethod
    def command(cls, args):
        '''sion printconfig command'''
         
        project = args.project
        variant = args.variant
        config = args.config
        show_simple = args.show_simple
        show_libraries = args.show_libraries
        
        ret = 1
        runner = PrintconfigRunner(project, variant, config, show_simple, show_libraries)
        ret = runner.run()
                 
        sys.exit(ret)
        
