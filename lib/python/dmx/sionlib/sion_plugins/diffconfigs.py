#!/usr/bin/env python
'''
Description: plugin for sion "diffconfigs"

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

class DiffConfigsError(Exception): pass

class DiffConfigsRunner(Runner):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, project, variant, first_config, second_config):
        self.user = getpass.getuser()        
        self.command = 'diffconfigs'                
        self.project = project        
        self.variant = variant
        self.first_config  = first_config
        self.second_config  = second_config

    def run(self):
        ret = 1

        misc = "'second_config':'%s'"% (self.second_config)
        ret = run_as_headless_user(command = self.command, user = self.user, project= self.project, variant = self.variant, config = self.first_config, misc = misc)

        return ret

class DiffConfigs(Command):
    '''plugin for "sion diffconfigs"'''
    
    LOGGER = logging.getLogger(__name__)
        
    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "sion diffconfigs"'''
        return 'Returns differences between 2 ICM configurations'

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
            Description
            ===========
            Sion diffconfigs allows user to compare between 2 ICM configurations.
            For more information, visit https://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/SynchronizingICMDataOnNetwork.
                                                
            Usage
            =====
            sion diffconfig -p i14socnd -v ar_lib -c dev -c2 dev2
            Returns differences between i14socnd/ar_lib@dev and i14socnd/ar_lib@dev2
            '''

        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "sion diffconfigs" subcommand'''
        add_common_args(parser)
        parser.add_argument('-p', '--project', metavar='project', required=True, help='Project')
        parser.add_argument('-v', '--variant', metavar='variant', required=True, help='Variant')
        parser.add_argument('-c', '--config1', metavar='config1', required=True, help='Configuration')
        parser.add_argument('-c2', '--config2',  metavar='config2',  required=True)

    @classmethod
    def command(cls, args):
        '''sion diffconfigs command'''
        project = args.project
        variant = args.variant
        config1  = args.config1
        config2  = args.config2
        
        ret = 1
        runner = DiffConfigsRunner(project, variant, config1, config2)
        ret = runner.run()
                 
        sys.exit(ret)
        
