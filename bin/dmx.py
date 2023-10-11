#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/bin/dmx.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description:  abnr: Altera Build 'N Release
              command with subcommands for simplifying use of ICManage
              all subcommands are loaded from the abnrlib/plugins directory

Author: Anthony Galdes (ICManage)
        Rudy Albachten

Copyright (c) Altera Corporation 2012
All rights reserved.
'''
from __future__ import print_function

from builtins import str
import sys
if sys.version_info < (2, 7):
    print("Must use python 2.7+ - did you forget to load an ARC environment?")
    sys.exit(1)

import os
import argparse
import logging
import re
import textwrap
import glob
LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)
import dmx.abnrlib.command
import dmx.utillib.loggingutils 
from dmx.utillib.logstash import LogStash
from dmx.helplib.help import *
from dmx.utillib.version import Version
VERSION = Version()
from logging.handlers import RotatingFileHandler

from datetime import date
import dmx.abnrlib.flows.environmentinfo
from pprint import pprint
import dmx.utillib.loggingutils

def main():
    parser = argparse.ArgumentParser(
        prog='dmx', 
        usage='\tWelcome to Data Management Exchange (DMX) platform.\n\tPlease perform \'dmx help\' first to get started.')
    parser.add_argument("-V", "--version", action='version', version='dmx: ({}) dmxdata: ({})'.format(VERSION.dmx, VERSION.dmxdata))
    subparsers = parser.add_subparsers(title='subcommands',
                     description='Note: For subcommand help: %(prog)s help subcommand',
                     metavar="command", help='additional help')

    help_parser = subparsers.add_parser('help', help="Show list of commands or get help for a subcommand")
    help_parser.add_argument('subcommand', nargs='*')
    help_parser.add_argument('--debug', action='store_true')
    help_parser.set_defaults(func=help_command)

    # This section will be refactored to 'dmx help map'
    # Leaving this section for backwards compatibility
    help_parser = subparsers.add_parser('helpmap', help="Show list of commands/options mapping from Nadder days")
    help_parser.set_defaults(func=helpmap_command)

    # Change ICM_TMPDIR directory away from ARC_TEMP_STORAGE
    # Please refer to function docstring for more detail.
    change_icm_tmpdir()


    # import plugins
    plugins_dir = os.path.join(LIB, "dmx", "wrappers")
    if not os.path.isdir(plugins_dir):
        print("Cannot find plugins directory!")
        #sys.exit(1)
    plugins = [x[:-3] for x in os.listdir(plugins_dir) if x.endswith('.py') and x[0] != '_']
    for plugin in plugins:
        __import__("dmx.wrappers." + plugin)
    
    # register commands
    command_table = {}
    parser_table = {}
    for cmd in dmx.abnrlib.cmdwrapper.CMDWrapper.__subclasses__(): # pylint: disable=E1101
        cmd_name = cmd.__name__.lower()
        command_table[cmd_name] = cmd
        cmd_help = cmd.get_help()
        cmd_parser = subparsers.add_parser(cmd_name, help=cmd_help, add_help=False, conflict_handler='resolve')
        cmd_parser.set_defaults(func=cmd.command)
        parser_table[cmd_name] = cmd_parser

    # import sub-plugins
    subplugins_dir = os.path.join(LIB, "dmx", "plugins")
    if not os.path.isdir(subplugins_dir):
        print("Cannot find sub-plugins directory!")
        #sys.exit(1)
    subplugins = [x[:-3] for x in os.listdir(subplugins_dir) if x.endswith('.py') and x[0] != '_']
    for subplugin in subplugins:
        __import__("dmx.plugins." + subplugin)
    
    pluginparser = argparse.ArgumentParser(prog='dmx')
    subpluginparser = pluginparser.add_subparsers()
    
    # register commands' sub_plugins
    subplugin_table = {}
    subplugin_parser_table = {}
    for cmd in dmx.abnrlib.command.Command.__subclasses__():
        cmd_name = cmd.__name__.lower()
        subplugin_table[cmd_name] = cmd
        cmd_help = cmd.get_help()
        cmd_parser = subpluginparser.add_parser(cmd_name, help=cmd_help, add_help=False)
        cmd.add_args(cmd_parser)
        cmd_parser.set_defaults(func=cmd.command)
        subplugin_parser_table[cmd_name] = cmd_parser
    
    # store globals in args
    parser.set_defaults(parser=parser)
    parser.set_defaults(subcommands=command_table)
    parser.set_defaults(subparsers=parser_table)
    parser.set_defaults(subplugins=subplugin_table)
    parser.set_defaults(subpluginparsers=subplugin_parser_table)

    # parse args
    args, options = parser.parse_known_args()
    args.options = options
            
    dmx.abnrlib.command.Command.echo = not 'quiet' in args or not args.quiet
    dmx.abnrlib.command.Command.execute = not 'preview' in args or not args.preview
    
    if 'options' in args:
        # Make sure we don't run on NightFury projects
        nightfury_projects = ['NightFury', 't20socanf', 't20socand', 'Crete']
        for project in nightfury_projects:
            if project in args.options:
                print("You are trying to operate on NightFury project {0}".format(project))
                print("Please use the version of abnr from project/nightfury")
                print("DMX is only reserved for Falcon project and beyond")
                sys.exit(1)

        # If --preview is set, indicate in logger's levelname
        if '-n' in args.options or '--preview' in args.options:
            levelname = '%(levelname)s-PREVIEW'     
        else:            
            levelname = '%(levelname)s' 

        # set up logger
        LOGGER = dmx.utillib.loggingutils.get_logger('dmx', levelname, args)
        info = dmx.abnrlib.flows.environmentinfo.EnvironmentInfo().get_dmx_info()
        log_dmx_info(info)

    # print DMX-id
    LOGGER.info('DMX-id: {}'.format(dmx.utillib.loggingutils.get_dmx_id()))

    # Splunk logging    
    if 'help' in str(args.func):
        m = re.match('.* (.*?)_command.*', str(args.func)) 
        command = m.group(1)
        if command == 'help':
            if args.subcommand:
                command = '{} {}'.format(command, ' '.join(args.subcommand))
    else:            
        m = re.match('.*dmx\.wrappers\.(.*?)\..*', str(args.func)) 
        try:
            wrapper = m.group(1)
        except:
            print('Unrecognized command')
            valid_commands = ['{}'.format(x for x in parser_table)]
            print('Valid commands: {}'.format(valid_commands))
            sys.exit(1)

        if options:
            if not options[0].startswith('-'):
                command = '{} {}'.format(wrapper, options[0])
            else:
                command = wrapper        
        else:
            #print 'Invalid command usage. Please refer to dmx help on how to use the commands'
            #sys.exit(1)
            command = wrapper

    logstash = LogStash(command)
    logstashdev = LogStash(command, testserver=True)

    if 'options' in args:
        #If --preview is set, print an informative message
        if '-n' in args.options or '--preview' in args.options:
            LOGGER.info('This is a preview (dry-run) mode, no changes will be made.')

    # dispatch...
    try:
        ret = args.func(args)
    except Exception as e: # pylint: disable=W0703
        #unicode_error = str(str(e), 'utf-8')
        unicode_error = str(e)
        LOGGER.error(unicode_error)
        LOGGER.error('DMX has run into errors. For more details on the command, please run \'dmx help {}\''.format(command))
        logstash.exception_log()
        logstashdev.exception_log()
        if 'options' in args:
            if '--debug' in args.options:
                raise  
        sys.exit(1)  
        
    if 'options' in args:
        #If --preview is set, print an informative message
        if '-n' in args.options or '--preview' in args.options:
            LOGGER.info('This was a preview (dry-run) mode, no changes have been made.')

    ### User should not be seeing any logging warnings/errors if it fails to connect to dashboard.
    ### This info collection process should be transparent to users.
    ### Since all the splunk/logstash modules are emitting the connection errors in logging.warn() level,
    ### we can setLevel(ERROR) to mute those errors.
    if '--debug' not in args.options:
        LOGGER.setLevel(logging.ERROR)
    logstash.final_log(ret)
    logstashdev.final_log(ret)

    return ret

def log_dmx_info(info):
    for k,v in sorted(info.items()):
        if type(v) is dict:
            for k1, v1 in list(info[k].items()) :
                if type(v1) is list:
                    LOGGER.debug('{} : {}'.format(k, k1))
                    for each_v in v1:
                        LOGGER.debug('{} : {}'.format(k1, each_v))
                else:
                    LOGGER.debug('{} : {}'.format(k1,v1))
        else:
            LOGGER.debug('{} : {}'.format(k,v))


def change_icm_tmpdir():
    '''
    https://jira.devtools.intel.com/browse/PSGDMX-2095
    https://jira.devtools.intel.com/browse/PSGDMX-2434
    Due to the fact that arc will kill the job if ARC_TEMP_STORAGE is >70G,
    we need to make sure that ICM_TMPDIR is not set to ARC_TEMP_STORAGE.
    '''
    os.environ['ICM_TMPDIR'] = os.getenv("ARC_TEMP_STORAGE") + '_dmx_ICM_TMPDIR'
    os.system("mkdir -p {}".format(os.environ['ICM_TMPDIR']))





if __name__ == '__main__':
    sys.exit(main())
