#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/plugins/derivebom.py#1 $
$Change: 7477267 $
$DateTime: 2023/02/09 18:35:51 $
$Author: wplim $

Description: plugin for "dmx derive libraries"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''

import sys
import logging
import textwrap
import itertools
import os
from cmx.abnrlib.command import Command, Runner
from cmx.utillib.utils import add_common_args, dispatch_cmd_to_other_tool, get_old_dmx_exe_from_folder
import cmx.abnrlib.flows.derivebom

LOGGER = logging.getLogger(__name__)

### Import DMX API
dmxlibdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, dmxlibdir)

from dmx.abnrlib.flows.branchlibrary import BranchLibrary
import dmx.utillib.admin

class DeriveBomError(Exception): pass

class DeriveBom(Command):
    '''plugin for "dmx branch"'''

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx derive bom help"'''
        myhelp = '''\
            Derive BOM to a new thread from an immutable BOM
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser this subcommand'''
        add_common_args(parser)
        # generic argument
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None)
        parser.add_argument('-i', '--ip', metavar='ip', required=True)
        parser.add_argument('-b', '--bom', metavar='bom', required=True)
        parser.add_argument('-t', '--thread', metavar='thread', required=True,
                            help='Thread to derive to')
        parser.add_argument('--desc',  metavar='description', required=False,
                            help='The description of the new library')
        parser.add_argument('--directory', metavar='directory', required=False, 
                            help = 'OPTIONAL. Directory to create workspace. Only use this option if the scratch disk for the project is not available.')

        # branchlibrary argument
        parser.add_argument('-d', '--deliverable', metavar='deliverable', required=False)

        # branchlibraries argument
        parser.add_argument('--reuse', required=False, default=True,
                            action='store_true',
                            #help='Reuse existing threads of the same name. If not specified and threads of the same name already exist, an error will be generated.')
                            help='DEPRECATED: Now, By default, will be reusing existing threads of the same name.')
        
        parser.add_argument('-e', '--exact', required=False, default=False,
            action='store_true', help='when specified, will create the icm-library name and config name exactly given in --thread.')
        parser.add_argument('--hierarchy', required=False, default=False,
            action='store_true', help='when specified, will branch out everything hierarchically.')

        parser.add_argument('--derivative', required=False, default=False,
            action='store_true', help='ADMIN only option. When specified, will do the branching following a set of rules. Please refer detail help for details.')

        


    @classmethod
    def extra_help(cls):
        '''extra narrative for dmx help derive bom'''
        extra_help = '''\
            derive bom is used to create BOMs in the provided thread from source bom.

            Thread will differentiate whether the newly created BOMs are targetting which 
            particular thread.            
            Optionally, a "--desc" option can specify a description for the newly created boms.  
            If provided, it should specify the purpose of the new BOMs.

            The source bom must be an immutable bom.
    	    PLEASE NOTE: This behavior is new in dmx compared to abnr (Nadder).
    	    In the past, any bom could be used as the starting point; 
    	    now, only an immutable bom can be used.  Why the change?
    	    It's much easier to trace back to the origin if an immutable bom
    	    is used.  

            All newly created boms will be named in the following way:
                b<normalized_immutable_bom>__<thread>__dev

            Example
            =======
            $ dmx derive bom -p i10socfm -i cw_lib -b REL2.0FM8revA0__17ww032a --thread FM4revA0 --desc "Branch for FM4revA0 development"
            * The new boms would be named bREL2.0FM8revA0-17ww032a__FM4revA0__dev




            ==================================================
            Detail Technical Explanation For The Advance Users
            ==================================================
            Given the following source configuration:-

                i10socfm/liotestfc1@REL5.0FM6revA0__18ww444a
                    i10socfm/liotestfc1:bumps@REL5.0FM6revA0__18ww444b
                    i10socfm/liotestfc1:ipspec@REL5.0FM6revA0__18ww444a
                    i10socfm/liotestfc1:reldoc@REL5.0FM6revA0__18ww444b
                    i10socfm/liotest1@REL5.0FM8revA0--TestSyncpoint__17ww404a
                            i10socfm/liotest1:ipspec@REL5.0FM8revA0__17ww182a
                            i10socfm/liotest1:rdf@REL5.0FM8revA0--TestSyncpoint__17ww404a
                            i10socfm/liotest1:sta@REL5.0FM8revA0--TestSyncpoint__17ww404a


            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            option:   --hierarchy
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Running the following command:-
                $dmx derive bom -p i10socfm -i liotestfc1 -b REL5.0FM6revA0__18ww444a --thread test1_dev  --hierarchy

            Would produce the following result:-
                i10socfm/liotestfc1@bREL5.0FM6revA0-18ww444a__test1_dev__dev
                        i10socfm/liotestfc1:bumps@bREL5.0FM6revA0-18ww444a__test1_dev__dev
                        i10socfm/liotestfc1:ipspec@bREL5.0FM6revA0-18ww444a__test1_dev__dev
                        i10socfm/liotestfc1:reldoc@bREL5.0FM6revA0-18ww444a__test1_dev__dev
                        i10socfm/liotest1@bREL5.0FM6revA0-18ww444a__test1_dev__dev
                                i10socfm/liotest1:ipspec@bREL5.0FM6revA0-18ww444a__test1_dev__dev
                                i10socfm/liotest1:rdf@bREL5.0FM6revA0-18ww444a__test1_dev__dev
                                i10socfm/liotest1:sta@bREL5.0FM6revA0-18ww444a__test1_dev__dev
            
                //depot/icm/proj/i10socfm/liotest1/ipspec/test1_dev_19ww134/...@16771500
                //depot/icm/proj/i10socfm/liotest1/rdf/test1_dev_19ww134/...@16771536
                //depot/icm/proj/i10socfm/liotest1/sta/test1_dev_19ww134/...@16771525
                //depot/icm/proj/i10socfm/liotestfc1/bumps/test1_dev_19ww134/...@16771498
                //depot/icm/proj/i10socfm/liotestfc1/ipspec/test1_dev_19ww134/...@16771499
                //depot/icm/proj/i10socfm/liotestfc1/reldoc/test1_dev_19ww134/...@16771535
           

            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            option:   --exact
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            If the --exact option is provided, 
                $dmx derive bom -p i10socfm -i liotestfc1 -b REL5.0FM6revA0__18ww444a --thread test2_dev  --hierarchy --exact

            This would be the outcome:-
                >dmx report content -p i10socfm -i liotestfc1 -b test2_dev --hier
                i10socfm/liotestfc1@test2_dev
                        i10socfm/liotestfc1:bumps@test2_dev
                        i10socfm/liotestfc1:ipspec@test2_dev
                        i10socfm/liotestfc1:reldoc@test2_dev
                        i10socfm/liotest1@test2_dev
                                i10socfm/liotest1:ipspec@test2_dev
                                i10socfm/liotest1:rdf@test2_dev
                                i10socfm/liotest1:sta@test2_dev

                >dmx report content -p i10socfm -i liotestfc1 -b test2_dev --hier --ver
                //depot/icm/proj/i10socfm/liotest1/ipspec/test2_dev/...@16771649
                //depot/icm/proj/i10socfm/liotest1/rdf/test2_dev/...@16771698
                //depot/icm/proj/i10socfm/liotest1/sta/test2_dev/...@16771692
                //depot/icm/proj/i10socfm/liotestfc1/bumps/test2_dev/...@16771648
                //depot/icm/proj/i10socfm/liotestfc1/ipspec/test2_dev/...@16771650
                //depot/icm/proj/i10socfm/liotestfc1/reldoc/test2_dev/...@16771693


            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            option:   (--hierarchy not provided)
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Running this:-
                $dmx derive bom -p i10socfm -i liotestfc1 -b REL5.0FM6revA0__18ww444a --thread test4_dev --exact

            Produces this output:-
                >$dmx report content -p i10socfm -i liotestfc1 -b test4_dev --hier
                i10socfm/liotestfc1@test4_dev
                        i10socfm/liotestfc1:bumps@test4_dev
                        i10socfm/liotestfc1:ipspec@test4_dev
                        i10socfm/liotestfc1:reldoc@test4_dev
                        i10socfm/liotest1@REL5.0FM8revA0--TestSyncpoint__17ww404a
                                i10socfm/liotest1:ipspec@REL5.0FM8revA0__17ww182a
                                i10socfm/liotest1:rdf@REL5.0FM8revA0--TestSyncpoint__17ww404a
                                i10socfm/liotest1:sta@REL5.0FM8revA0--TestSyncpoint__17ww404a
                
                >$dmx report content -p i10socfm -i liotestfc1 -b test4_dev --hier --ver
                //depot/icm/proj/i10socfm/liotest1/ipspec/dev/...@9578724
                //depot/icm/proj/i10socfm/liotest1/rdf/dev/...@9240477
                //depot/icm/proj/i10socfm/liotest1/sta/dev/...@9173783
                //depot/icm/proj/i10socfm/liotestfc1/bumps/test4_dev/...@16773708
                //depot/icm/proj/i10socfm/liotestfc1/ipspec/test4_dev/...@16773709
                //depot/icm/proj/i10socfm/liotestfc1/reldoc/test4_dev/...@16773707


'''

        admin_help = '''\
            ==================================================
            Following Options Are Only Available To DMX Admins
            ==================================================

            Assuming the following input cofiguration is used:-
                >dmx report content -p i10socfm -i liotestfc1 --hier -b snap-branch-derivative1
                i10socfm/liotestfc1@snap-branch-derivative1
                        i10socfm/liotestfc1:bumps@snap-branch-derivative1
                        i10socfm/liotestfc1:cdl@snap-branch-derivative1
                        i10socfm/liotestfc1:ipspec@snap-branch-derivative1
                        i10socfm/liotestfc1:reldoc@snap-branch-derivative1
                        i10socfm/liotest1@REL5.0FM6revA0__18ww503a
                                i10socfm/liotest1:ipspec@REL5.0FM8revA0--LionelTest__17ww472a
                                i10socfm/liotest1:rdf@REL5.0FM6revA0--LionelTest__18ww425a
                                i10socfm/liotest1:reldoc@REL5.0FM8revA0__17ww474a
                                i10socfm/liotest1:sta@REL5.0FM8revA0--LionelTest__16ww511a

                >dmx report content -p i10socfm -i liotestfc1 --hier -b snap-branch-derivative1 --ver
                //depot/icm/proj/i10socfm/liotest1/ipspec/dev/...@10823134
                //depot/icm/proj/i10socfm/liotest1/rdf/dev/...@13334427
                //depot/icm/proj/i10socfm/liotest1/reldoc/dev/...@10852147
                //depot/icm/proj/i10socfm/liotest1/sta/dev/...@9173783
                //depot/icm/proj/i10socfm/liotestfc1/bumps/dev/...@16791090
                //depot/icm/proj/i10socfm/liotestfc1/cdl/lay/...@16790891
                //depot/icm/proj/i10socfm/liotestfc1/ipspec/ciw/...@16790854
                //depot/icm/proj/i10socfm/liotestfc1/reldoc/test5_dev/...@16773785

            
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            option:   --derivative
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            When this opion is specified, it follows the following rules:-
                - if the source of the libtype's icm-library is 'dev', 
                    then new branchname/configname == <--thread>_dev
                - if the source of the libtype's icm-library is 'lay', 
                    then new branchname/configname == <--thread>_lay
                - if the source of the libtype's icm-library is 'ciw', 
                    then new branchname/configname == <--thread>_ciw
                - if the source of the libtype's icm-library is 'something else', 
                    then new branchname/configname == <--thread>_ciw
                - all composite configname == <--thread>_dev



            Running this (without --hierarchy):-
                $dmx derive bom -p i10socfm -i liotestfc1 -b snap-branch-derivative1 --thread LTX --derivative

            Produces this:-
                >dmx report content -p i10socfm -i liotestfc1 --hier -b LTX_dev
                i10socfm/liotestfc1@LTX_dev
                        i10socfm/liotestfc1:bumps@LTX_dev
                        i10socfm/liotestfc1:cdl@LTX_lay
                        i10socfm/liotestfc1:ipspec@LTX_ciw
                        i10socfm/liotestfc1:reldoc@LTX_dev
                        i10socfm/liotest1@REL5.0FM6revA0__18ww503a
                                i10socfm/liotest1:ipspec@REL5.0FM8revA0--LionelTest__17ww472a
                                i10socfm/liotest1:rdf@REL5.0FM6revA0--LionelTest__18ww425a
                                i10socfm/liotest1:reldoc@REL5.0FM8revA0__17ww474a
                                i10socfm/liotest1:sta@REL5.0FM8revA0--LionelTest__16ww511a

                >dmx report content -p i10socfm -i liotestfc1 --hier -b LTX_dev --ver
                //depot/icm/proj/i10socfm/liotest1/ipspec/dev/...@10823134
                //depot/icm/proj/i10socfm/liotest1/rdf/dev/...@13334427
                //depot/icm/proj/i10socfm/liotest1/reldoc/dev/...@10852147
                //depot/icm/proj/i10socfm/liotest1/sta/dev/...@9173783
                //depot/icm/proj/i10socfm/liotestfc1/bumps/LTX_dev/...@16792064
                //depot/icm/proj/i10socfm/liotestfc1/cdl/LTX_lay/...@16792091
                //depot/icm/proj/i10socfm/liotestfc1/ipspec/LTX_ciw/...@16792062
                //depot/icm/proj/i10socfm/liotestfc1/reldoc/LTX_dev/...@16792063


            Running this (with --hierarchy):-
                $dmx derive bom -p i10socfm -i liotestfc1 -b snap-branch-derivative1 --thread LT1 --derivative --hier

            Produces this:-
                >dmx report content -p i10socfm -i liotestfc1 --hier -b LT1_dev
                i10socfm/liotestfc1@LT1_dev
                        i10socfm/liotestfc1:bumps@LT1_dev
                        i10socfm/liotestfc1:cdl@LT1_lay
                        i10socfm/liotestfc1:ipspec@LT1_ciw
                        i10socfm/liotestfc1:reldoc@LT1_dev
                        i10socfm/liotest1@LT1_dev
                                i10socfm/liotest1:ipspec@LT1_dev
                                i10socfm/liotest1:rdf@LT1_dev
                                i10socfm/liotest1:reldoc@LT1_dev
                                i10socfm/liotest1:sta@LT1_dev

                >dmx report content -p i10socfm -i liotestfc1 --hier -b LT1_dev --ver
                //depot/icm/proj/i10socfm/liotest1/ipspec/LT1_dev/...@16792178
                //depot/icm/proj/i10socfm/liotest1/rdf/LT1_dev/...@16792150
                //depot/icm/proj/i10socfm/liotest1/reldoc/LT1_dev/...@16792120
                //depot/icm/proj/i10socfm/liotest1/sta/LT1_dev/...@16792145
                //depot/icm/proj/i10socfm/liotestfc1/bumps/LT1_dev/...@16792144
                //depot/icm/proj/i10socfm/liotestfc1/cdl/LT1_lay/...@16792177
                //depot/icm/proj/i10socfm/liotestfc1/ipspec/LT1_ciw/...@16792119
                //depot/icm/proj/i10socfm/liotestfc1/reldoc/LT1_dev/...@16792121

        '''

        extra_help += admin_help

        return textwrap.dedent(extra_help)
    
    @classmethod
    def command(cls, args):
        '''the "derive bom" subcommand'''
        ret = dispatch_cmd_to_other_tool(get_old_dmx_exe_from_folder('plugins'), sys.argv)
        if ret == 0:
            LOGGER.info("Running Cheetah Derive")
            wu = cmx.abnrlib.flows.derivebom.DeriveBom(args.project, args.ip, args.bom, args.thread, args.deliverable, args.exact, args.hierarchy)
            ret = wu.run()


        return ret

