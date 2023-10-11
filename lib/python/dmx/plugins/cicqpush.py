#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/cicqpush.py#1 $
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
import argparse

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOTDIR)

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
import dmx.abnrlib.flows.cicqpush
import dmx.utillib.arcjob


LOGGER = logging.getLogger(__name__)

class CicqPushError(Exception): pass

class CicqPush(Command):
    '''plugin for "dmx cicq push"'''

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help"'''
        myhelp = '''\
            Push(overlay/integrate) content from a source bom to the cicq-backend-boms(CBB) landing_zone(LZ) config.
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser for "dmx bom clone" subcommand'''
        add_common_args(parser)
        # generic arguments
        parser.add_argument('filespec',  metavar='filespec', nargs='*', help='File pattern to indicate files to overlay. Follows Perforce pattern convention.')
        parser.add_argument('-p', '--project', metavar='project', required=True)
        parser.add_argument('-i', '--ip', metavar='ip', required=True)
        parser.add_argument('-b', '--bom',  metavar='ip_bom', required=True, help='This is the ip-bom, not the deliverable-bom.')
        parser.add_argument('-d', '--deliverables', required=False, nargs='+',
            help='Only push the list of deliverables.', default=None)
        parser.add_argument('--hier', required=False, default=False, action='store_true',
            help='Push the content hierarchically, if option is given.')
        parser.add_argument("-t", "--thread", required=False, default=[''], nargs='+')
        parser.add_argument('--wait', required=False, default=False, action='store_true',
            help='DEPRECATED!!! From now on, this command will always return prompt only after all jobs are completed.(this option is retained on purpose for backward compatibility)')
        parser.add_argument('--dstbom', required=False, default=None, 
            help=argparse.SUPPRESS)


    @classmethod
    def extra_help(cls):
        '''extra narrative for dmx help bom clone'''
        extra_help = '''\
            "dmx cicq push" is used to push (overlay/integrate/copy) content from a source to the cicq-backend-boms(CBB) landing_zone(LZ) config.
            (Note: By default, source-bom which are immutable will be skipped)

           
            Here's the detail of how it works:-

            For all the examples below, we will be using the following source bom:-

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





            -----------------------------------------------------------------------------
            Push A single deliverable (OPTION: -d)
            -----------------------------------------------------------------------------
            Example
            =======
            $ dmx cicq push -p i10socfm -i liotestfc1 -b test3_dev -d ipspec -t aaa
   
            Description
            ===========
            Copy the content 
                from i10socfm/liotestfc1:ipspec@test3_dev
                to   i10socfm/liotestfc1:ipspec@landing_zone_aaa


            -----------------------------------------------------------------------------
            Push deliverables hierarchically (OPTION: -d --hier)
            -----------------------------------------------------------------------------
            Example
            =======
            $ dmx cicq push -p i10socfm -i liotestfc1 -b test3_dev -d ipspec sta --hier -t aaa
   
            Description
            ===========
            Copy the content 

                from i10socfm/liotestfc1:ipspec@test3_dev
                to   i10socfm/liotestfc11:ipspec@landing_zone_aaa


            These will not be done, as the source-bom are immutables:

                from i10socfm/liotest1:ipspec@REL5.0FM8revA0__17ww182a 
                to   i10socfm/liotest1:ipspec@landing_zone_aaa

                from i10socfm/liotest1:sta@REL5.0FM8revA0--TestSyncpoint__17ww404a
                to   i10socfm/liotest1:sta@landing_zone_aaa


            -----------------------------------------------------------------------------
            Push all deliverables in an IP (OPTION: none)
            -----------------------------------------------------------------------------
            Example
            =======
            $ dmx cicq push -p i10socfm -i liotestfc1 -b test3_dev -t aaa
   
            Description
            ===========
            Copy the content 

                from
                   i10socfm/liotestfc1:bumps@test3_dev
                   i10socfm/liotestfc1:ipspec@test3_dev
                   i10socfm/liotestfc1:reldoc@test3_dev
                to 
                   i10socfm/liotestfc1:bumps@landing_zone_aaa
                   i10socfm/liotestfc1:ipspec@landing_zone_aaa
                   i10socfm/liotestfc1:reldoc@landing_zone_aaa


            -----------------------------------------------------------------------------
            Push everything throughout the entire tree (OPTION: --hier)
            -----------------------------------------------------------------------------
            Example
            =======
            $ dmx cicq push -p i10socfm -i liotestfc1 -b test3_dev --hier -t aaa
   
            Description
            ===========
            Copy the content 
                from 
                    i10socfm/liotestfc1:bumps@test3_dev
                    i10socfm/liotestfc1:ipspec@test3_dev
                    i10socfm/liotestfc1:reldoc@test3_dev
                to 
                    i10socfm/liotestfc1:bumps@landing_zone_aaa
                    i10socfm/liotestfc1:ipspec@landing_zone_aaa
                    i10socfm/liotestfc1:reldoc@landing_zone_aaa

            These will not be done, as the source-bom are immutables:
                from 
                    i10socfm/liotest1:ipspec@REL5.0FM8revA0__17ww182a
                    i10socfm/liotest1:rdf@REL5.0FM8revA0--TestSyncpoint__17ww404a
                    i10socfm/liotest1:sta@REL5.0FM8revA0--TestSyncpoint__17ww404a
                to 
                    i10socfm/liotest1:ipspec@landing_zone_aaa
                    i10socfm/liotest1:rdf@landing_zone_aaa
                    i10socfm/liotest1:sta@landing_zone_aaa

        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''the "bom clone" subcommand'''
        # generic arugments
        filespec = args.filespec
        project = args.project
        ip = args.ip
        bom = args.bom
        deliverables = args.deliverables
        hier = args.hier
        threads = args.thread
        preview = args.preview
        wait = True
        dstbom = args.dstbom

        ### we do not allow deliverable and filespec exists together as it might create conflict
        if deliverables and filespec:
            raise Exception('--deliverable/--deliverable_filter cannot be used with filespec')
        if len(threads) > 1 and filespec:
            raise Exception('Only one thread can be used with filespec')


        ### --thread is a compulsory option for normal usage.
        ### However, we allow empty --thread when --dstbom is used (this is used in CICQ)
        ### Which is why we can not specify --thread required=True in argparse.
        if not threads[0] and not dstbom:
            raise Exception("""
                dmx cicq push: error: --thread is a compulsory argument and can not be empty.""")
      
        LOGGER.debug("threads: {}".format(threads))

        if len(threads) == 1:
            ci = dmx.abnrlib.flows.cicqpush.CicqPush(project, ip, bom, deliverables=deliverables, hier=hier,
                thread=threads[0], preview=preview, wait=wait, dstconfig=dstbom, filespec=filespec)
            ret = ci.run()
            
        else:

            finalcmd = ''
            dmxexe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'bin', 'dmx')

            for thread in threads:
                cmd = '{} cicq push -p {} -i {} -b {} -t {} --debug'.format(dmxexe, project, ip, bom, thread)
                if preview:
                    cmd += ' -n'
                if hier:
                    cmd += ' --hier'
                if deliverables:
                    cmd += ' -d {}'.format(' '.join(deliverables))
                arccmd = 'arc submit --test name={} -- "{}";'.format(thread, cmd)
                finalcmd += arccmd

            LOGGER.info("Submitting jobs to farm ...")
            LOGGER.debug("Running cmd: {}".format(finalcmd))
            finalcmd = """ arc submit -- '{}' """.format(finalcmd)
            exitcode, stdout, stderr = dmx.utillib.utils.run_command(finalcmd)
            LOGGER.debug("""
                exitcode: {}
                stdout: {}
                stderr: {}
            """.format(exitcode, stdout, stderr))
            arcjobid = stdout.splitlines()[0]

            LOGGER.info("Job submitted to farm. Waiting for job {} to complete ...".format(arcjobid))
            waitcmd = 'arc wait {}'.format(arcjobid)
            LOGGER.debug("Running cmd: {}".format(waitcmd))
            exitcode, stdout, stderr = dmx.utillib.utils.run_command(waitcmd)
            LOGGER.debug("""
                exitcode: {}
                stdout: {}
                stderr: {}
            """.format(exitcode, stdout, stderr))

            LOGGER.info("Job {} completed. Please goto arc dashboard to review job status.". format(arcjobid))
            ret = exitcode

            a = dmx.utillib.arcjob.ArcJob()
            stdoutfile, stderrfile = a.concat_children_output(arcjobid)
            LOGGER.info("Concatenated stdout files downloaded at {}".format(stdoutfile))
            LOGGER.info("Concatenated stderr files downloaded at {}".format(stderrfile))

        return ret

