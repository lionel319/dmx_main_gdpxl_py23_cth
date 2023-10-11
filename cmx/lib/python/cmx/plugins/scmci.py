#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/scmci.py#6 $
$Change: 7798106 $
$DateTime: 2023/09/27 00:42:33 $
$Author: wplim $

Description: plugin for "dmx newws"

Author: Lionel Tan Yoke-Liang
Copyright (c) Altera Corporation 2014
All rights reserved.

'''
from __future__ import print_function

# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915

import os
import sys
import logging
import textwrap
import argparse
from threading import Thread

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(1, LIB)
from cmx.abnrlib.command import Command, Runner
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder, \
    is_belongs_to_arcpl_related_deliverables
import cmx.abnrlib.flows.scmci

LOGGER = logging.getLogger(__name__)

class SCMCI(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = '''\
            Checks in large data to repository
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        dmx scm ci command checks-in file in a workspace to PROJ_ARCHIVE

        If --r2gbomcfg is provided, command will check-in files based on the default pattern file in $DMXDATA_ROOT/$DB_FAMILY/bomcfgfiles/default.r2g.cfg 
        If --ipdebomcfg is provided, command will check-in files based on the default pattern file in $DMXDATA_ROOT/$DB_FAMILY/bomcfgfiles/default.ipde.cfg 
        The above switch is to checks-in the file needed for onebom

        The below switch is mutually-exclusive with above switch
        Command will work similar to 'eouMGR --archive/archie put' commad.
        If --cell is provided, command will check-in for the particular cells only
        If --stage is provided, command will check-in for the particular stage only
        Command must be run in a workspace where files are supposed to be checked-in.

        Examples
        ========
        $ cd $WORKAREA
        $ dmx scm ci --r2gbomcfg
        Check-in files based on the default pattern file defined in DMXDATA(default.r2g.cfg)

        $ cd $WORKAREA
        $ dmx scm ci --ipdebomcfg
        Check-in files based on the default pattern file defined in DMXDATA(default.ipde.cfg)

        $ cd $WORKAREA 
        $ dmx scm ci -c avmm_power_controller
        Check-in to all stages that defined in [cico] in avmm_power_controller.design.cfg

        $ cd $WORKAREA 
        $ dmx scm ci -s finish
        Check-in to finish stages that defined in [cico] in $DUT.design.cfg

        $ cd $WORKAREA 
        $ dmx scm ci -c avmm_power_controller -s finish
        Check-in to finish stage that defined in [cico] in avmm_power_controller.design.cfg
        '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx workspace" subcommand'''
        
        no_option_needed =  False if os.environ.get('IPDE_SESSION_ID') else True

        add_common_args(parser)
        parser.add_argument('-c', '--cell',  metavar='cell', required=False, nargs='+', default=[],
                            help='Cell to checkin. If not provided, every cell will be checkin.')
        parser.add_argument('-s', '--stage',  metavar='stage', required=False, nargs='+', default=[],
                            help='Stage to checkin. If not provided, every stage will be checkin.')
        parser.add_argument('--for_release_bomname',  metavar='for_release_bomname', required=False, help=argparse.SUPPRESS)
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--r2gbomcfg', action='store_true', help='checkin r2gbomcfg content')
        group.add_argument('--ipdebomcfg', action='store_true', help='checkin ipdebomcfg content')

    @classmethod
    def command(cls, args):
        '''the "scm" subcommand'''

        if args.r2gbomcfg or args.ipdebomcfg:
            if args.cell or args.stage:
                raise Exception('--r2gbomcfg/--ipdebomcfg is mutually exclusive with --cell/--stage.')

        LOGGER.info("Running SCM check-in operation")
        if args.r2gbomcfg:
            sc = cmx.abnrlib.flows.scmci.ScmCi(args.cell, args.stage, 'r2g', args.preview, args.for_release_bomname)
        elif args.ipdebomcfg:
            sc = cmx.abnrlib.flows.scmci.ScmCi(args.cell, args.stage, 'ipde', args.preview, args.for_release_bomname)
        else:
            sc = cmx.abnrlib.flows.scmci.ScmCi(args.cell, args.stage, 'backend',  args.preview, args.for_release_bomname)
        ret = sc.run()

        return ret
