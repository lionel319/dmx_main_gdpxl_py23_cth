#!/usr/bin/env python
'''
Description:  syncpoint_user: Tool to add/delete/list users for syncpoint operation

Author: Kevin Lim Khai - Wern

Copyright (c) Altera Corporation 2015
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
import logging.handlers

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.command import Command

LOGGER = logging.getLogger()

class CustomHelpFormatter(argparse.HelpFormatter):
    '''Custom help formatter class to sort the subcommands for "syncpoint help"'''
    def _iter_indented_subactions(self, action):
        try:
            get_subactions = action._get_subactions # pylint: disable=W0212
        except AttributeError:
            pass
        else:
            self._indent()
            if isinstance(action, argparse._SubParsersAction): # pylint: disable=W0212
                for subaction in sorted(get_subactions(), key=lambda x: x.dest):
                    yield subaction
            else:
                for subaction in get_subactions():
                    yield subaction
            self._dedent()

def help_command(args):
    if args.subcommand is None or args.subcommand == "help":
        args.parser.print_help()
    elif args.subcommand in args.subparsers:
        args.subparsers[args.subcommand].print_help()
        extra_help = args.subcommands[args.subcommand].extra_help()
        if extra_help:
            print()
            print(extra_help)
    else:
        args.parser.print_usage()
        print("Error:", args.subcommand, "is not a valid subcommand")

def main():
    parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter,description="Syncpoint_user tool to help manage user's roles in syncpoint tool. For more information, visit https://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/Syncpoint")
    subparsers = parser.add_subparsers(title='subcommands',
                     description='Note: For subcommand help: %(prog)s help subcommand',
                     metavar="command", help='additional help')

    help_parser = subparsers.add_parser('help', help="Show list of commands or get help for a subcommand")
    help_parser.add_argument('subcommand', nargs='?')
    help_parser.set_defaults(func=help_command)

    # import plugins
    plugins_dir = os.path.join(LIB, "dmx", "syncpointlib", "syncpoint_user_plugins")
    if not os.path.isdir(plugins_dir):
        print("Cannot find syncpoint_user_plugins directory!")
        sys.exit(1)
    plugins = [x[:-3] for x in os.listdir(plugins_dir) if x.endswith('.py') and x[0] != '_']
    for plugin in plugins:
        hiddenplugins = []
        if plugin not in hiddenplugins:
            __import__("dmx.syncpointlib.syncpoint_user_plugins." + plugin)
    
    # register commands
    command_table = {}
    parser_table = {}
    for cmd in Command.__subclasses__(): # pylint: disable=E1101
        cmd_name = cmd.__name__.lower()
        command_table[cmd_name] = cmd
        cmd_help = cmd.get_help()
        cmd_parser = subparsers.add_parser(cmd_name, help=cmd_help, add_help=False)
        cmd.add_args(cmd_parser)
        cmd_parser.set_defaults(func=cmd.command)
        parser_table[cmd_name] = cmd_parser

    # store globals in args
    parser.set_defaults(parser=parser)
    parser.set_defaults(subcommands=command_table)
    parser.set_defaults(subparsers=parser_table)
    
    # parse args
    args = parser.parse_args()

    # set up logger
    LOGGER.setLevel(logging.INFO)
    stream = logging.StreamHandler()
    stream.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    if 'debug' in args and args.debug:
        stream.setLevel(logging.DEBUG)
        LOGGER.setLevel(logging.DEBUG)

    if os.access(os.getcwd(), os.W_OK):
        handler = logging.handlers.RotatingFileHandler('.syncpoint.log', maxBytes=1048576, backupCount=3)
        handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s:%(message)s'))
        handler.setLevel(logging.DEBUG)
        LOGGER.addHandler(handler)
    LOGGER.addHandler(stream)
    LOGGER.debug(' '.join(sys.argv))

    # dispatch...
    try:
        args.func(args)
    except Exception as e: # pylint: disable=W0703
        if ('debug' in args and args.debug) or str(e) == '':
            raise
        LOGGER.error(str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()
    sys.exit(0)
