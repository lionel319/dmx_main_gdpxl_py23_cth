#!/usr/intel/pkgs/python3/3.9.6/bin/python3

'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/bin/cmx.py#3 $
$Change: 7621000 $
$DateTime: 2023/05/19 01:12:32 $
$Author: lionelta $

Description:  abnr: Altera Build 'N Release
              command with subcommands for simplifying use of ICManage
              all subcommands are loaded from the abnrlib/plugins directory

Author: Anthony Galdes (ICManage)
        Rudy Albachten

Copyright (c) Altera Corporation 2012
All rights reserved.
'''
import UsrIntel.R1

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

import os
import sys
import argparse
import logging
import re
import textwrap
import glob
LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)
import cmx.abnrlib.command
import cmx.utillib.loggingutils 
from cmx.utillib.version import Version
import cmx.helplib.help
VERSION = Version()
from logging.handlers import RotatingFileHandler

from datetime import date
from pprint import pprint
import cmx.utillib.loggingutils

def main():

    ### Make sure we are in correct environment by checking $P4CONFIG
    p4config = os.getenv("P4CONFIG", "")
    if p4config != '.icmconfig':
        print("-FATAL-: Your environment is incorrect. Make sure you are in PSG environment before running dmx.")
        print("Exiting ...")
        return 1

    parser = argparse.ArgumentParser(
        prog='cmx', 
        usage='\tWelcome to Cth Management Exchange (CMX) platform.\n\tPlease perform \'cmx help\' first to get started.')
    parser.add_argument("-V", "--version", action='version', version='cmx: ({}) dmxdata: ({})'.format(VERSION.cmx, VERSION.dmxdata))
    subparsers = parser.add_subparsers(title='subcommands',
                     description='Note: For subcommand help: %(prog)s help subcommand',
                     metavar="command", help='additional help')

    help_parser = subparsers.add_parser('help', help="Show list of commands or get help for a subcommand")
    help_parser.add_argument('subcommand', nargs='*')
    help_parser.add_argument('--debug', action='store_true')
    help_parser.set_defaults(func=cmx.helplib.help.help_command)

    # import plugins
    plugins_dir = os.path.join(LIB, "cmx", "wrappers")
    if not os.path.isdir(plugins_dir):
        print("Cannot find plugins directory!")
        #sys.exit(1)
    plugins = [x[:-3] for x in os.listdir(plugins_dir) if x.endswith('.py') and x[0] != '_']
    for plugin in plugins:
        __import__("cmx.wrappers." + plugin)
    
    # register commands
    command_table = {}
    parser_table = {}
    for cmd in cmx.abnrlib.cmdwrapper.CMDWrapper.__subclasses__():
        cmd_name = cmd.__name__.lower()
        command_table[cmd_name] = cmd
        cmd_help = cmd.get_help()
        cmd_parser = subparsers.add_parser(cmd_name, help=cmd_help, add_help=False, conflict_handler='resolve')
        cmd_parser.set_defaults(func=cmd.command)
        parser_table[cmd_name] = cmd_parser

    # import sub-plugins
    subplugins_dir = os.path.join(LIB, "cmx", "plugins")
    if not os.path.isdir(subplugins_dir):
        print("Cannot find sub-plugins directory!")
        #sys.exit(1)
    subplugins = [x[:-3] for x in os.listdir(subplugins_dir) if x.endswith('.py') and x[0] != '_']
    for subplugin in subplugins:
        __import__("cmx.plugins." + subplugin)
    
    pluginparser = argparse.ArgumentParser(prog='cmx')
    subpluginparser = pluginparser.add_subparsers()
    
    # register commands' sub_plugins
    subplugin_table = {}
    subplugin_parser_table = {}
    for cmd in cmx.abnrlib.command.Command.__subclasses__():
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
            
    cmx.abnrlib.command.Command.echo = not 'quiet' in args or not args.quiet
    cmx.abnrlib.command.Command.execute = not 'preview' in args or not args.preview
    
    if 'options' in args:
        if '-n' in args.options or '--preview' in args.options:
            levelname = '%(levelname)s-PREVIEW'     
        else:            
            levelname = '%(levelname)s' 

        # set up logger
        LOGGER = cmx.utillib.loggingutils.get_logger('', levelname, args)


    if 'help' in str(args.func):
        m = re.match('.* (.*?)_command.*', str(args.func)) 
        command = m.group(1)
        if command == 'help':
            if args.subcommand:
                command = '{} {}'.format(command, ' '.join(args.subcommand))
    else:            
        m = re.match('.*cmx\.wrappers\.(.*?)\..*', str(args.func)) 
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
            command = wrapper

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
        LOGGER.error('DMX has run into errors. For more details on the command, please run \'cmx help {}\''.format(command))
        if 'options' in args:
            if '--debug' in args.options:
                raise  
        sys.exit(1)  
        
    if 'options' in args:
        #If --preview is set, print an informative message
        if '-n' in args.options or '--preview' in args.options:
            LOGGER.info('This was a preview (dry-run) mode, no changes have been made.')

    if '--debug' not in args.options:
        LOGGER.setLevel(logging.ERROR)

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




if __name__ == '__main__':
    sys.exit(main())
