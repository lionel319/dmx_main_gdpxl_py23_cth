#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/reportowner.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: dmx "owner" subcommand plugin
Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2016
All rights reserved.
'''
import sys
import logging
import textwrap
import pwd
import re
import csv

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.owner import Owner as OwnerRunner

class ReportOwner(Command):
    '''plugin for "dmx report owner"'''

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help"'''
        myhelp = '''\
            Print/Set the ownership of project/ip or BOM            
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        '''
        Extra help for dmx help owner
        '''
        extra_help = '''\
            Print the ownership of project/ip/bom

            If --set-owner is provided, command will update the ownership of the desired element:
            * If --bom/-b is provided, ownership of the BOM is updated
            * If --bom/-b is not provided, ownership of the IP is updated

            Example
            =======
            $ dmx report owner -p i10socfm -i cw_lib
            Owner: snerlika (shilpa.nerlikar)
            Time: 2016/04/23 01:29:00
        
            $ dmx report owner -p i10socfm -i cw_lib -b REL2.0FM8revA0__17ww032a
            Owner: chialinh (chialin.hsing)
            Creator: icetnr ()
            Time: 2017/01/18 11:26:47

            $ dmx report owner -p i10socfm -i cw_lib -b dev
            Owner: snerlika (shilpa.nerlikar)
            Creator: snerlika (shilpa.nerlikar)
            Designer: snerlika (shilpa.nerlikar)
            Time: 2016/04/22 10:38:21

            $ dmx report owner -p i10socfm -i cw_lib -b dev --all
            .
            .
            .
            [12]
            Creator: snerlika (shilpa.nerlikar)
            Designer: ajangity ()
            Time: 2016/09/29 11:54:00
            [13]
            Owner: snerlika (shilpa.nerlikar)
            Creator: snerlika (shilpa.nerlikar)
            Designer: snerlika (shilpa.nerlikar)
            Time: 2016/10/06 11:16:21
            
            $ dmx report owner -p i10socfm -i cw_lib -b dev --set-owner abc
            Set the ownership of i10socfm/cw_lib@dev to abc

            $ dmx report owner -p i10socfm -i cw_lib --set-owner abc
            Set the ownership of i10socfm/cw_lib to abc
            '''
        return textwrap.dedent(extra_help)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx report owner" subcommand'''
        add_common_args(parser)
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None)
        parser.add_argument('-i', '--ip', metavar='ip', required=True)
        parser.add_argument('-d', '--deliverable', metavar='deliverable', required=False)
        parser.add_argument('-b', '--bom',  metavar='bom', required=False)
        parser.add_argument('--all', required=False, action='store_true',
                            help='Show all records for bom including updaters.')
        parser.add_argument('--format', required=False, choices=['csv'], 
                            help='Format the output into the desired format.')
        parser.add_argument('--owner', required=False, action='store_true', 
                            help='Returns only the owner value.')
        parser.add_argument('--creator', required=False, action='store_true', 
                            help='Returns only the creator value.')
        parser.add_argument('--designer', required=False, action='store_true', 
                            help='Returns only the designer/last updater value.')
        parser.add_argument('--set-owner', metavar='setowner', required=False, 
                            help='When specified, given value will be used to set the Owner property value.')        

    @classmethod
    def command(cls, args):
        '''the "owner" subcommand'''
        project = args.project
        ip = args.ip
        bom = args.bom
        deliverable = args.deliverable
        all = args.all
        format = args.format
        owner = args.owner
        creator = args.creator
        designer = args.designer
        setowner = args.set_owner
        preview = args.preview

        runner = OwnerRunner(project, ip, config_or_library_or_release=bom, libtype=deliverable, all=all, format=format,
                             owner=owner, creator=creator, designer=designer, setowner=setowner, 
                             preview=preview)
        return (runner.run())
