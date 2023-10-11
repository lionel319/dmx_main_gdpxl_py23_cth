#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/snap.py#5 $
$Change: 7760012 $
$DateTime: 2023/08/28 19:47:26 $
$Author: lionelta $

Description: dmx "snaplibrary" subcommand plugin
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import sys
import os
import logging
import textwrap
import itertools
from pprint import pprint

rootdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, rootdir)

from cmx.abnrlib.command import Command, Runner
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder, is_belongs_to_arcpl_related_deliverables
import cmx.abnrlib.flows.snap
LOGGER = logging.getLogger(__name__)

class SnapError(Exception): pass

class Snap(Command):
    '''dmx subcommand plugin class"'''

    @classmethod
    def get_help(cls):
        '''short subcommand description'''
        myhelp = '''\
            Create a snapshot (non-editable) of a deliverable or IP
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''subcommand arguments'''
        add_common_args(parser)
        # generic arguments
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None)
        parser.add_argument('-i', '--ip', metavar='ip', required=False)
        parser.add_argument('-b', '--bom', metavar='bom', required=False,
            help='Source BOM, must not be REL/snap')
        parser.add_argument('-s', '--snapshot', metavar='snapshot', required=False,
            help='The name of the snap bom you want to create. Must begin with snap-. If not given, snap command will generate it\'s own snap with this format snap-<normalized_source_bom>_<year>ww<week><day>')

        # snaplibrary arguments
        parser.add_argument('-d', '--deliverable', metavar='deliverable',
                            action='append', nargs='+', required=False,
                            default=[])

        parser.add_argument('--force', action='store_true', default=False, required=False, 
                help="Force create the new snapshot despite the same snap content already exist.")

        # snaptree arguments        
        parser.add_argument('--desc', metavar='description', required=False,
            help='The description that will be attached to each new snap- bom.')
        parser.add_argument('--changelist', required=False, default=0,
                            help='Specify a changelist to snap against.')
        parser.add_argument('--deliverable-filter', metavar='deliverable_filter', required=False,
                            action='append', nargs='+',
                            help='Only snap the specified deliverables')
        parser.add_argument('--ip-filter', metavar='ip_filter', required=False,
                            action='append', nargs='+',
                            help='Only snap boms within the specified ips')

        # http://pg-rdjira:8080/browse/DI-746
        # Disabled per Bertrand's request, --reuse is now turned on by default
        # http://pg-rdjira:8080/browse/DI-812
        # Re-enabled for backwards compatibility, option is already deprecated
        parser.add_argument('--reuse', required=False, action='store_true',
                            help='Option is DEPRECATED. --reuse is now enabled by default')

        parser.add_argument('--flowcfg', required=False, default=False, action='store_true',
            help='You could ask dmx to read the inputs from $WORKAREA/flows/dmx/flow.cfg file instead. For an example, kindly refer to <here>')

    @classmethod
    def extra_help(cls):
        '''
        Extra help for dmx help snaplibrary
        '''
        extra_help = '''\
            ---------------------------------------------------------------
            Create a deliverable snapshot (with --deliverable or -d option)
            ---------------------------------------------------------------
            This command is used to create a deliverable snap bom.
            work in progress ... 
            '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):

        if args.flowcfg:
            import cmx.tnrlib.utils
            data = cmx.tnrlib.utils.parse_flowcfg()['workspace_check']
            mysysargv = ['dmx', 'snap', '-p', data['project'], '-i', data['ip'], '-d', data['deliverable'], '-b', data['bom']]
            if args.debug:
                mysysargv.append('--debug')
            if args.preview:
                mysysargv.append('--preview')
            args.deliverable = [data['deliverable']]
        else:
            mysysargv = sys.argv
       
        ### We purposely make --force option to always be True because we want it to ALWAYS
        ### successfully create a snap in old_dmx when -d is ipde/r2g.
        ret = dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), mysysargv + ['--force'])


        ### Only continue if old_dmx snap passes
        if not ret:
            LOGGER.info("Running Cheetah Snap")
            if args.deliverable:
                for dlv in args.deliverable:
                    if is_belongs_to_arcpl_related_deliverables(dlv[0]): 
                        sn = cmx.abnrlib.flows.snap.Snap(args.project, args.ip, args.bom, dlv[0], args.snapshot)
                        ret = sn.run()
            else:
                sn = cmx.abnrlib.flows.snap.Snap(args.project, args.ip, args.bom, args.deliverable, args.snapshot)
                ret = sn.run()

        return ret
                     

