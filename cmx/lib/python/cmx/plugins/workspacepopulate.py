#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/workspacepopulate.py#17 $
$Change: 7744897 $
$DateTime: 2023/08/17 02:03:13 $
$Author: wplim $

Description: plugin for "dmx newws"

Author: Lionel Tan Yoke-Liang
Copyright (c) Altera Corporation 2014
All rights reserved.

'''

# pylint: disable=C0301,F0401,E1103,R0914,R0912,R0915

from future import standard_library
standard_library.install_aliases()
import os
import sys
import logging
import textwrap
import argparse
import io
import glob
from pprint import pprint

lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, lib)

from cmx.abnrlib.command import Command, Runner
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder, get_icm_wsroot_from_workarea_envvar 
import cmx.abnrlib.flows.workspacepopulate
LOGGER = logging.getLogger(__name__)

class WorkspacePopulate(Command):
    '''
    '''
    @classmethod
    def get_help(cls):
        '''
        Short help for the subcommand
        '''
        myhelp = ''' Create Workspace.
        '''
        return textwrap.dedent(myhelp)

    @classmethod
    def extra_help(cls):
        ''' Extra help '''
        myhelp = '''\
        Create and Sync the workspace.
        >dmx workspace populate -p <project> -i <ip> -b <bom

        Example:-
        >dmx workspace populate -p SZR -i avmm_lib -b dev
        .
        '''
        return textwrap.dedent(myhelp)


    @classmethod
    def add_args(cls, parser):
        add_common_args(parser)
        parser.add_argument('-p', '--project',  required=True) 
        parser.add_argument('-i', '--ip',  required=True) 
        parser.add_argument('-b', '--bom',  required=True)
        parser.add_argument('-f', '--force', action='store_true')
        #parser.add_argument('-d', '--deliverable', required=True, choices=["cthfe", 'febe', 'r2g', 'ipde', 'psas']) 
        #parser.add_argument('-w', '--wsname', default=":icm:", help=argparse.SUPPRESS) 
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-d', '--deliverable', choices=["cthfe", 'febe', 'r2g', 'ipde']) 
        group.add_argument('--hier', action='store_true') 
        #group.add_argument('-d', '--deliverable',  choices=["cthfe", 'r2g', 'ipde', 'psas']) 
        #group.add_argument('-c', '--cfgfile',  required=False, default='') 

    @classmethod
    def command(cls, args):
        #wspath = get_icm_wsroot_from_workarea_envvar()
        #if wspath:
        #    raise Exception("Workspace(s) already exists. {}\nOnly 1 workspace is allowed.".format(wspath))
   
        os.environ['DMX_WORKSPACE'] = f"{os.getenv('WORKAREA')}"
        #os.system('mkdir -p {}/psg'.format(os.getenv("WORKAREA")))

        #ret = dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)
        #ret = 1
        LOGGER.info("Cheetah Workspace Population")
        wp = cmx.abnrlib.flows.workspacepopulate.WorkspacePopulate(args.project, args.ip, args.bom, deliverable=args.deliverable, preview=args.preview, debug=args.debug, hier=args.hier, force=args.force)
        ret = wp.run()
        return ret
