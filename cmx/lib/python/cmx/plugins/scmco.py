#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/scmco.py#4 $
$Change: 7798167 $
$DateTime: 2023/09/27 01:24:54 $
$Author: wplim $

Description: plugin for "dmx newws"

Author: Lionel Tan Yoke-Liang
Copyright (c) Altera Corporation 2014
All rights reserved.

'''

# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915

import os
import sys
import logging
import textwrap
import argparse

from cmx.abnrlib.command import Command
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 

LOGGER = logging.getLogger(__name__)
import cmx.abnrlib.flows.scmco



class SCMCO(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Checks out large data in current workspace
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        dmx scm co command checks-out files in a workspace.
    
        If --r2gbomcfg is provided, command will check-out files based on the default pattern file in $DMXDATA_ROOT/$DB_FAMILY/bomcfgfiles/default.r2g.cfg 
        If --ipdebomcfg is provided, command will check-out files based on the default pattern file in $DMXDATA_ROOT/$DB_FAMILY/bomcfgfiles/default.ipde.cfg 
        The above switch is to checks-out the file needed for onebom

        The below switch is mutually-exclusive with above switch
        Command will work similar to 'eouMGR populate/archie -get'.
        If --cell is provided, command will check-out for the particular cells only
        If --stage is provided, command will check-out for the particular stage only

        Command must be run in a workspace where files are supposed to be checked-out.

        Examples
        ========
        $ cd $WORKAREA
        $ dmx scm co --r2gbomcfg
        Check-out files based on the default pattern file defined in DMXDATA(default.r2g.cfg)

        $ cd $WORKAREA
        $ dmx scm co --ipdebomcfg
        Check-out files based on the default pattern file defined in DMXDATA(default.ipde.cfg)

        $ cd $WORKAREA 
        $ dmx scm co -c avmm_power_controller
        Check-out to all stages that defined in [cico]/[co] in avmm_power_controller.design.cfg

        $ cd $WORKAREA 
        $ dmx scm co -s finish
        Check-out to finish stages that defined in [cico]/[co] in $DUT.design.cfg

        $ cd $WORKAREA 
        $ dmx scm co -c avmm_power_controller -s finish
        Check-out to finish stage that defined in [cico]/[co] in avmm_power_controller.design.cfg

        '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx workspace" subcommand'''

        add_common_args(parser)
        parser.add_argument('-c', '--cell',  metavar='cell', required=False, nargs='+', default=[],
                            help='Cell to checkin. If not provided, every cell will be checkin.')
        parser.add_argument('-s', '--stage',  metavar='stage', required=False, nargs='+', default=[],
                            help='Stage to checkin. If not provided, every stage will be checkin.')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--r2gbomcfg', action='store_true', help='checkin r2gbomcfg content')
        group.add_argument('--ipdebomcfg', action='store_true', help='checkin ipdebomcfg content')

        
    @classmethod
    def command(cls, args):
        if args.r2gbomcfg or args.ipdebomcfg:
            if args.cell or args.stage:
                raise Exception('--r2gbomcfg/--ipdebomcfg is mutually exclusive with --cell/--stage.')

        LOGGER.info("Running SCM check-out operation")
        if args.r2gbomcfg:
            sc = cmx.abnrlib.flows.scmco.ScmCo(args.cell, args.stage, 'r2g', args.preview)
        elif args.ipdebomcfg:
            sc = cmx.abnrlib.flows.scmco.ScmCo(args.cell, args.stage, 'ipde', args.preview)
        else:
            sc = cmx.abnrlib.flows.scmco.ScmCo(args.cell, args.stage, 'backend',  args.preview)
        ret = sc.run()

        return ret

        
