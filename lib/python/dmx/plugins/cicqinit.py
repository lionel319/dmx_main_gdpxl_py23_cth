#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/cicqinit.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "dmx clonboms"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import sys
import os
import logging
import textwrap

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOTDIR)

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
import dmx.abnrlib.flows.cicqupdate

LOGGER = logging.getLogger(__name__)
class CicqInitError(Exception): pass

class CicqInit(Command):
    '''plugin for "dmx cicq init"'''

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help"'''
        myhelp = '''\
            Makes all cicq backend configs aligned (full tree) with the given bom.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx bom clone" subcommand'''
        add_common_args(parser)
        # generic arguments
        parser.add_argument('-p', '--project', metavar='project', required=True)
        parser.add_argument('-i', '--ip', metavar='ip', required=True)
        parser.add_argument('-b', '--bom',  metavar='src_bom', required=True)
        parser.add_argument('-t', '--thread', required=True)
        parser.add_argument('-c', '--cfgfile', required=True)


    @classmethod
    def extra_help(cls):
        '''extra narrative for dmx help bom clone'''
        extra_help = '''\
            "cicq init" is used align all the cicq backend boms with the given bom.

            The current cicq-backend-boms(cbb) are
            - landing_zone
            - cicq_integration
            - always_clean 
           
            --------------------------------------------------------------
            Here's the detail of how it works:-
            --------------------------------------------------------------
            from the given source bom, make sure that all the cbb(cicq-backend-boms) also have the similar tree structure.
            - if the libtype-bom exist in the cbb, reuse it
            - if the libtype-bom does not exist in the cbb, 
                > create an empty branch same name as the cbb
                > create a config same ame as the cbb (which holds the empty branch)
            - if any of the variant-bom does not exist
                > create it
            - if any of the variant-bom tree structure is not aligned with source-bom
                > make it align


            For all the examples beflow, we will be using the following source bom:-

                >dmx report content -p i10socfm -i liotestfc1 -b test3_dev --hier
                Project: i10socfm, IP: liotestfc1, BOM: test3_dev
                        Last modified: 2019/03/29 00:20:06 (in server timezone)
                i10socfm/liotestfc1@test3_dev
                        i10socfm/liotestfc1:bumps@test3_dev
                        i10socfm/liotestfc1:ipspec@test3_dev
                        i10socfm/liotestfc1:reldoc@test3_dev
                        i10socfm/liotest1@test3_dev
                                i10socfm/liotest1:ipspec@REL5.0FM8revA0__17ww182a
                                i10socfm/liotest1:rdf@REL5.0FM8revA0--TestSyncpoint__17ww404a
                                i10socfm/liotest1:sta@REL5.0FM8revA0--TestSyncpoint__17ww404a

                >dmx report content -p i10socfm -i liotestfc1 -b test3_dev --hier --verb
                //depot/icm/proj/i10socfm/liotest1/ipspec/dev/...@9578724
                //depot/icm/proj/i10socfm/liotest1/rdf/dev/...@9240477
                //depot/icm/proj/i10socfm/liotest1/sta/dev/...@9173783
                //depot/icm/proj/i10socfm/liotestfc1/bumps/test3_dev/...@16773498
                //depot/icm/proj/i10socfm/liotestfc1/ipspec/test3_dev/...@16773496
                //depot/icm/proj/i10socfm/liotestfc1/reldoc/test3_dev/...@16773497

            Example
            =======
            $ dmx cicq init --project i10socfm --ip liotestfc1 --bom test3_dev 
    
            Output:
                >dmx report content -p i10socfm -i liotestfc1 -b landing_zone --hier
                Project: i10socfm, IP: liotestfc1, BOM: landing_zone
                        Last modified: 2019/07/17 00:59:12 (in server timezone)
                i10socfm/liotestfc1@landing_zone
                        i10socfm/liotestfc1:bumps@landing_zone
                        i10socfm/liotestfc1:ipspec@landing_zone
                        i10socfm/liotestfc1:reldoc@landing_zone
                        i10socfm/liotest1@landing_zone
                                i10socfm/liotest1:ipspec@landing_zone
                                i10socfm/liotest1:rdf@landing_zone
                                i10socfm/liotest1:sta@landing_zone
                
                >dmx report content -p i10socfm -i liotestfc1 -b landing_Zone --hier --verb
                //depot/icm/proj/i10socfm/liotest1/ipspec/landing_zone/...@18052784
                //depot/icm/proj/i10socfm/liotest1/rdf/landing_zone/...@18052968
                //depot/icm/proj/i10socfm/liotest1/sta/landing_zone/...@18052960
                //depot/icm/proj/i10socfm/liotestfc1/bumps/landing_zone/...@18052964
                //depot/icm/proj/i10socfm/liotestfc1/ipspec/landing_zone/...@18052953
                //depot/icm/proj/i10socfm/liotestfc1/reldoc/landing_zone/...@18052984


        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''the "bom clone" subcommand'''
        # generic arugments
        project = args.project
        ip = args.ip
        bom = args.bom
        thread = args.thread
        preview = args.preview
        cfgfile = args.cfgfile
        dryrun = args.preview

        ci = dmx.abnrlib.flows.cicqupdate.CicqUpdate(project, ip, bom, suffix=thread, cfgfile=cfgfile, init=True, dryrun=dryrun)
        ret = ci.run()
                    
        return ret

