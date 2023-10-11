#!/usr/bin/env python
'''
Description: plugin for sion "command"

Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915,W0511
import sys
import os
import re
import grp
import textwrap
import logging
import getpass
from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.sionlib.sion_utils import run_as_psginfraadm, run_command, print_errors
from dmx.sionlib.workspace_helper import get_var_prot_group, get_proj_prot_group
default_release_directory = "/p/psg/falcon/sion"
ICM_READONLY_CMDS = ['changes','changelists','describe','diff2','dirs','filelog','files','fstat','grep','integrated','interchanges','labels','print','sizes','users']

class CommandError(Exception): pass

class CommandRunner(Runner):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, icm_command):
        self.icm_command = icm_command
        self.command = "command"
        
        if self.icm_command.startswith("icmp4 "):
            icmp4_cmd = self.icm_command.split()[1]
            if icmp4_cmd not in ICM_READONLY_CMDS:
                raise CommandError("{0} is not allowed to be run by sion. Only selected ICM commands may be run by sion.".format(icmp4_cmd))    

            #check if the depot path given by user is accessible by user
            project = ""
            m = re.match(r".*depot\/icm\/proj\/(.*?)\/.*",self.icm_command)            
            if m:
                project = m.group(1)
            m = re.match(r".*depot\/icm\/proj\/(.*?)\/(.*?)\/(.*?)/.*",self.icm_command)
            variant = ""
            if m:
                if m.group(2) == "icmrel":
                    variant = m.group(3)
                else:
                    variant = m.group(2)
            
            required_group = ""
            if project and variant:
                required_group = get_var_prot_group(project,variant)   
            elif project and not variant:
                required_group = get_proj_prot_group(project)  

            if required_group:
                user = os.getenv('USER')
                user_groups = self.get_unix_groups(user)
                if required_group not in user_groups:
                    raise CommandError("{0} is not allowed to run {1} because user has no permission to view this file".format(user, self.icm_command))  

        else:
            raise CommandError("ICM command must always start with icmp4. Example: icmp4 files //depot/...")

    def run(self):
        ret = 1
        
        #pad icm commands so that it can be passed as a full string
        self.icm_command = "=MaGiC=".join(self.icm_command.split(" "))
        
        ret = run_as_psginfraadm(command = self.command, icm_command = self.icm_command)

        return ret

    def get_unix_groups(self, user):
        cmd = "groups %s" % user
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)
        user_groups = stdout.strip().split(" ")[2:]
        return user_groups        

class Command(Command):
    '''plugin for "sion command"'''
    
    LOGGER = logging.getLogger(__name__)
        
    def __init__(self):
        ''' for pylint '''
        pass

    @classmethod
    def get_help(cls):
        '''one-line description for "sion command"'''
        return 'Runs selected icmp4 commands'

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        Description
        ===========
        Sion command allows ICM-savvy users to run ICM commands via sion. Only selected ICM commands are supported by sion. 
        The list of commands supported by sion:
        changes
        changelists
        describe
        diff2
        dirs
        filelog
        files
        fstat
        grep
        integrated
        interchanges
        labels
        print
        sizes
        users
        
        WARNING: As ICM commands are complex, users without advanced knowledge of ICM are not encouraged to use this command.
                        
        Usage
        =====
        sion command -c "<icmp4 commands>"
        Runs icmp4 commands in the double-quotation mark only if the command is allowed to be run by sion.

        Example
        =======
        sion command -c "icmp4 dirs //depot/icm/proj/*"
        Runs "icmp4 dirs //depot/icm/proj/*"
        '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "sion command" subcommand'''
        add_common_args(parser)
        parser.add_argument('-c', '--command', metavar='command', required=True,
            help='ICM Command for sion to run')

    @classmethod
    def command(cls, args):
        '''sion command command'''
        
        icm_command = args.command
        
        ret = 1
        runner = CommandRunner(icm_command)
        ret = runner.run()
                 
        sys.exit(ret)
        
