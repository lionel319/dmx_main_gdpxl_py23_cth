#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/helplib/help.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Copyright (c) Altera Corporation 2016
All rights reserved.
'''
from __future__ import print_function

from builtins import str
import os
import argparse
import logging
import re

from dmx.utillib.version import Version
from dmx.utillib.utils import *
VERSION = Version()

def helpmap_command(args):
    import dmx.helplib.help_plugins.map
    print(get_support_url())

def help_command(args):
    if args.subcommands is None or not args.subcommand:
        ''' 
        dmx help 
        Prints list of available commands/subcommands and their brief descriptions       
        '''
        print("+-----------------------------------------------------------------------+")
        print("DMX bundle version:")
        Version(debug=args.debug).print_version()
        print("+-----------------------------------------------------------------------+")
        print()
        print("For detail/summary help of each command:")
        print("\tdmx help <command>")
        print("\tdmx help <command> <subcommand>\n")
        print('Glossary:')
        print('\tProject                 = ICManage Project')
        print('\tIP                      = ICManage Variant')
        print('\tDeliverable             = ICManage Libtype')
        print('\tBOM (Bill of Materials) = ICManage Configuration\n')
        print('For more help on commands/options mapping or missing ABNR commands from Nadder days, please run:')
        print('\tdmx helpmap')
        print('\tdmx help map')
        print()
        print('For more help on developer or admin options (only useful if you are a DMX developer or admin), please run:')
        print('\tdmx help admin\n')        

        for cmd in sorted(args.subcommands.keys()):
            print('---------------')
            print('{}'.format(cmd))
            print('---------------')
            print(args.subcommands[cmd].get_help())
        print(get_support_url())
    elif len(args.subcommand) == 1: 
        ''' 
        dmx help command 
        Prints detailed help messages for given command (including it's subcommands)
        If command doesn't exist, prints list of valid commands
        '''       
        # This special section is only for help_plugins
        # We do not want to put this under wrappers as these help plugins are not supposed to be lumped with ordinary dmx plugins
        help_plugins_dir = os.path.join(os.path.dirname(__file__), "help_plugins")
        help_plugins = [x[:-3] for x in os.listdir(help_plugins_dir) if x.endswith('.py') and x[0] != '_']
        for plugin in help_plugins:
            if args.subcommand[0] == str(plugin):
                __import__("dmx.helplib.help_plugins." + plugin)
                print(get_support_url())
                # Why a break here? So We don't execute the else function
                break
        else:                
            if args.subcommand[0] in args.subparsers:
                print(args.subcommands[args.subcommand[0]].command_help())
                print(get_support_url())
                print('(dmx help {})'.format(args.subcommand[0])) 
            else:
                print('Valid commands are: {}'.format(sorted([x for x in args.subparsers])))      
                sys.exit(1)
    elif len(args.subcommand) == 2:
        '''
        dmx help command subcommand
        Prints detailed help messages for given subcommand 
        If command doesn't exist, prints list of valid commands
        If subcommand doesn't exist, prints list of valid subcommands for the given command        
        '''
        if args.subcommand[0] not in args.subparsers:
            print('Valid commands are: {}'.format(sorted([x for x in args.subparsers])))
            sys.exit(1)          
        
        full_plugin_name = ''.join(args.subcommand)            
        if full_plugin_name in args.subplugins:
            print(args.subcommands[args.subcommand[0]].subcommand_help(args.subcommand))
            print(get_support_url())    
            print('(dmx help {} {})'.format(args.subcommand[0], args.subcommand[1]))  
        else:
            if args.subcommand[0] in args.subparsers:
                subplugins = [x.split(args.subcommand[0])[1] for x in args.subplugins if x.startswith(args.subcommand[0])]
                print('Valid commands are: {}'.format(sorted(['{} {}'.format(args.subcommand[0], x) for x in subplugins])))
                sys.exit(1)                        
            else:
                print('Valid commands are: {}'.format(sorted([x for x in args.subparsers])))
                sys.exit(1)                                
    else:        
        print('You have provided invalid inputs to \'dmx help\'.')
        print('Please consult \'dmx help\' for usage models.')
        sys.exit(1)

def get_support_url():
    MORE_HELP = ''    
    if is_pice_env():
        MORE_HELP = "For more information about DMX, please refer to:\
                     \n* http://goto.intel.com/psg-dmx \
                     \n* http://psg-sc-arc.sc.intel.com/p/psg/flows/common/dmx/{0}/doc/dmx/html \
                     \nFor developer: \
                     \n* http://psg-sc-arc.sc.intel.com/p/psg/flows/common/dmx/{0}/doc/dmx/html/QuickStart.html'\n".format(VERSION.dmx)
    else:        
        if os.environ['ARC_SITE'] == 'pn':
            site = 'pg'
        else:
            site = 'sj'        
        MORE_HELP = "For more information about DMX (or ABNR), please refer to:\
                     \n* https://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/ABNR \
                     \n* https://{0}-arc.altera.com/tools/dmx/{1}/doc/dmx/html \
                     \nFor developer: \
                     \n* https://{0}-arc.altera.com/tools/dmx/{1}/doc/dmx/html/QuickStart.html\n".format(site, VERSION.dmx)
    return MORE_HELP
