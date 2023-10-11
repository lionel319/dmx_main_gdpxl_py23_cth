#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/bomclone.py#1 $
$Change: 7463577 $
$DateTime: 2023/01/31 01:08:26 $
$Author: lionelta $

Description: plugin for "dmx clonboms"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import sys
import logging
import textwrap

from cmx.abnrlib.command import Command
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder 

logger = logging.getLogger(__name__)

class BomCloneError(Exception): pass

class BomClone(Command):
    '''plugin for "dmx bom clone"'''

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help"'''
        myhelp = '''\
            Clone an existing BOM to a new BOM
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx bom clone" subcommand'''
        add_common_args(parser)
        # generic arguments
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None)
        parser.add_argument('-i', '--ip', metavar='ip', required=True)
        parser.add_argument('-b', '--bom',  metavar='src_bom', required=True)
        parser.add_argument('--dstbom',  metavar='dst_bom', required=False)

        # cloneconfigs arguments
        parser.add_argument('-d', '--deliverable', metavar='deliverable')

        ### Lionel disabled this. I don't think this option make sense at all. Here's my thought process:
        ### - in Legacy, when a simple-config is cloned:
        ###   > the simple-config is cloned, but it is still pointing to the same library. What's the point?
        ### - in GDPXL, when a library/release is cloned:
        ###   > a new empty library(branch) is created.
        ### In both cases, if a new branch is needed, then user should use 'dmx derive'
        #parser.add_argument('--clone-deliverable',  action='store_true', help='clone deliverables to dstbom')
        
        parser.add_argument('--clone-immutable',  action='store_true', help='clone immutable boms instead of reusing them')
        parser.add_argument('--reuse',  action='store_true', help='reuse all boms. Does not work with --clone-deliverable and --clone-immutable')

        # cloneconfigswithrels arguments
        parser.add_argument('--replace-with-rels', action='store_true', required=False,
                            help='If specified, bom clone will replace sub-boms with latest REL boms for that IP')
        parser.add_argument('-m', '--milestone',
                            metavar='milestone', required=False,
                            help='Milestone for REL to replace with')
        parser.add_argument('-t', '--thread',
                            metavar='thread', required=False,
                            help='Thread for REL to replace with')
        parser.add_argument('-s', '--stop',
                            required=False,
                            help='Stop if no REL bom could be found for a sub-bom.',
                            action='store_true')
        parser.add_argument('-u', '--use-labeled',
                            required=False, action='store_true',
                            help='Use labeled REL boms if no non-labeled REL boms are available')

        # --emptybranch arguments
        parser.add_argument('--emptybranch', action='store_true', required=False, default=False,
            help='''Create a branch for each of the newly cloned config, whereby the icm-library(branch) name follows the newly cloned config name.
            If the newly-tobe-cloned config exists, it will be reused. (reuse is always on, regardless of the --reuse option specified)''')


    @classmethod
    def extra_help(cls):
        '''extra narrative for dmx help bom clone'''
        extra_help = '''\
            ---------------------------------------------------------------
            Cloning BOM hierarchically (without --replace-with-rels option)
            ---------------------------------------------------------------
            "bom clone" is used to clone source bom hierarchically to new set of boms.
            
            Common usage for bom clone includes:
            * Cloning a immutable (RELxxx) boms to mutable (non-RELxxx) boms.
            * Cloning a development boms prior to editing them with "dmx bom edit".
  
            The "-p/--project", -i/--ip", and "-b/--bom" options are required
            and specify the source bom to clone.

            The "--dstbom" option is also required, and it specifies the name for all
            the newly created boms.
            * It is a fatal error if the top-most BOM with the same destination name already exist.
            * Command will reuse sub-boms if they already exist with the same destination name
            * --dstbom cannot create a new REL bom. Only the
                release commands can create REL boms.
            * --dstbom cannot create a new snap bom. Only the
                snap commands can create snap boms.
            ** Starting from dmx/13.5, --dstbom is no longer a required param, if no --dstbom specified,
            the dstbom will be sourcebom__{yy}WW{ww}{day}{number}

            By default, "bom clone" only clones the IPs.  
            If the "--clone-deliverable" option is also specified, it will also clone the 
            deliverables.

            By default, "bom clone" does not clone immutable BOMs (REL/snap).
            If the "--clone-immutable" option is specified, REL or snap- boms will be cloned.

            If the "--reuse" option is specified, only the top-level BOM would be cloned, every BOM underneath would be re-used as it is. This option does not work together with --clone-deliverable and --clone-immutable

            Example
            =======
            $dmx bom clone -p i10socfm -i cw_lib -b dev --dstbom testing
            * Clone i10socfm/cw_lib@dev into i10socfm/cw_lib@testing and all of its sub-IP-boms (deliverables are not cloned)

            $dmx bom clone -p i10socfm -i cw_lib -b dev --dstbom testing --reuse
            * Clone i10socfm/cw_lib@dev into i10socfm/cw_lib@testing. 
            * i10socfm/cw_lib@testing will reuse sub-boms in dev.

            $dmx bom clone -p i10socfm -i cw_lib -b dev --dstbom testing --clone-immutable
            * Clone i10socfm/cw_lib@dev into i10socfm/cw_lib@testing. 
            * Instead of reusing REL/snap sub-boms in dev, command will clone them into 
              testing and use these boms in i10socfm/cw_lib@dev
            * Only the IP-boms will be cloned. 
            
            $dmx bom clone -p i10socfm -i cw_lib -b dev --dstbom testing --clone-deliverable
            * Clone i10socfm/cw_lib@dev into i10socfm/cw_lib@testing. 
            * Instead of reusing deliverables, command will clone them into testing and 
              use them in i10socfm/cw_lib@dev

            $dmx bom clone -p i10socfm -i cw_lib -l rtl -b dev --dstbom testing
            * Clone i10socfm/cw_lib:rtl@dev into i10socfm/cw_lib:rtl@testing.

            -----------------------------------------------------------
            Cloning BOM and replacing sub-boms with latest released BOM 
            (with --replace-with-rels option)
            -----------------------------------------------------------
            "bom clone --replace-with-rels" clones a bom and replaces sub-boms with
            the latest REL for the specified thread/milestone.

            If no REL can be found for a given ip/thread/milestone, the default
            behaviour is to continue using the bom from the source bom. If
            you want bom clonewithrels to stop if no REL is available, use the --stop flag.

            Default behaviour is to only consider REL boms that do not have a label. 
            In some cases there will be labeled REL boms, but no non-labeled REL boms. 
            If, in this scenario you would like to use the labeled REL bom use the
            --use-labeled flag.

            Example
            =======
            $ dmx bom clone --replace-with-rels --project i10socfm --ip cw_lib --bom dev --dstbom RC2.0 --milestone 2.0 --thread FM8revA0
            * Clone i10socfm/cw_lib@dev into i10socfm/cw_lib@RC2.0 and replaces every BOMs found in i10socfm/cw_lib@RC2.0 to it's respective latest REL BOM of milestone 2.0 and thread FM8revA0



            ---------------------------------------------------------------
            Cloning BOM with --emptybranch 
            ---------------------------------------------------------------
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
           

            Example (without -d option):
            ============================
                $dmx bom clone --emptybranch -p i10socfm -i liotestfc1 -b test3_dev --dstbom test11_dev
    
            Output:
                >dmx report content -p i10socfm -i liotestfc1 -b test11_dev --hier
                Project: i10socfm, IP: liotestfc1, BOM: test11_dev
                        Last modified: 2019/07/17 00:59:12 (in server timezone)
                i10socfm/liotestfc1@test11_dev
                        i10socfm/liotestfc1:bumps@test11_dev
                        i10socfm/liotestfc1:ipspec@test11_dev
                        i10socfm/liotestfc1:reldoc@test11_dev
                        i10socfm/liotest1@test11_dev
                                i10socfm/liotest1:ipspec@test11_dev
                                i10socfm/liotest1:rdf@test11_dev
                                i10socfm/liotest1:sta@test11_dev
                
                >dmx report content -p i10socfm -i liotestfc1 -b test11_dev --hier --verb
                //depot/icm/proj/i10socfm/liotest1/ipspec/test11_dev/...@18052784
                //depot/icm/proj/i10socfm/liotest1/rdf/test11_dev/...@18052968
                //depot/icm/proj/i10socfm/liotest1/sta/test11_dev/...@18052960
                //depot/icm/proj/i10socfm/liotestfc1/bumps/test11_dev/...@18052964
                //depot/icm/proj/i10socfm/liotestfc1/ipspec/test11_dev/...@18052953
                //depot/icm/proj/i10socfm/liotestfc1/reldoc/test11_dev/...@18052984


            Example (with -d option):
            ============================
                $dmx bom clone --emptybranch -p i10socfm -i liotest1 -b REL5.0FM8revA0__17ww182a --dstbom test11_dev -d ipspec

            output:
                >dmx report content -p i10socfm -i liotest1 -b test11_dev --hier --verb -d ipspec
                //depot/icm/proj/i10socfm/liotest1/ipspec/test11_dev/...@18052784

        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        return dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)
        
