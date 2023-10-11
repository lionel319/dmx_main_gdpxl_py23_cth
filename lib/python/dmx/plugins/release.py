#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/release.py#2 $
$Change: 7480179 $
$DateTime: 2023/02/12 18:24:49 $
$Author: lionelta $

Description: dmx "release library" subcommand plugin
Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.
'''
from __future__ import print_function
from builtins import str
import sys
import logging
import textwrap
import itertools
import os

from dmx.abnrlib.command import Command
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.releasedeliverable import ReleaseDeliverable
from dmx.abnrlib.flows.releasedeliverables import ReleaseDeliverables
from dmx.abnrlib.flows.releasevariant import ReleaseVariant
from dmx.abnrlib.flows.releasetree import ReleaseTree
from dmx.abnrlib.flows.releaseview import ReleaseView
from dmx.abnrlib.flows.releaseprel import ReleasePrel
from dmx.utillib.admin import is_admin

class ReleaseError(Exception): pass

class Release(Command):
    '''dmx subcommand plugin class"'''

    @classmethod
    def get_help(cls):
        '''short subcommand description'''
        myhelp = '''\
            Release (create REL) an IP or deliverable
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''subcommand arguments'''
        add_common_args(parser)
        # generic arguments
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None)
        parser.add_argument('-i', '--ip', metavar='ip', required=True)
        parser.add_argument('-b', '--bom', metavar='bom', required=True)
        parser.add_argument('-m', '--milestone', metavar='milestone', required=False, default=None,
            help='Milestone to release to')
        parser.add_argument('-t', '--thread', metavar='thread', required=False, default=None,
            help='Thread to release to')
        parser.add_argument('--label', metavar='label', required=False,
            help='Label to make this release easily identifiable')
        parser.add_argument('--desc',  metavar='description', required=True,
            help='Description that will be added to the release')
        parser.add_argument('--force', required=False, action='store_true',
                            help='Force the creation of a new REL bom even if this content has previously been released for the specified milestone and thread.')        

        # releaselibrary arguments
        parser.add_argument('-d', '--deliverable', metavar='deliverable',
                            action='append', nargs='+', required=False,
                            default=[], help='Deliverable to release')

        # releasetree arguments  
        parser.add_argument('--hierarchy', required=False, action='store_true',
                            help='If --hierarchy is provided, release will release the entire BOM from bottom-up. The final result would be the release BOM for IP given in --ip.')        

        # http://pg-rdjira:8080/browse/DI-1060
        # New syncpoint argument for IP release
        parser.add_argument('--syncpoint', help='If syncpointname is provided, DMX will cross-check the BOM to be released with syncpoint.')
        parser.add_argument('--skipsyncpoint', help='(only available for PREL) If syncpointname is not provided, this argument needs to be provided. String provided to this argument will be the justification reason used to skip syncpoint checking.')

        # http://pg-rdjira:8080/browse/DI-1179
        # Argument to skip milestone checking
        parser.add_argument('--skipmscheck', help='If this argument is specified, release will skip under-delivery milestone checking. String provided to this argument will be the justification reason used to skip the milestone checking.')

        # http://pg-rdjira.altera.com:8080/browse/DI-598
        # Temporary solution until a long-term fix is identified
        parser.add_argument('--nowait', default=False, required=False, action='store_true',
                            help='Does not wait for the completion of release process, returns prompt to user after submitting job to TNR.')

        # Deprecated option
        parser.add_argument('--ipspec', required=False,
                            help='This option is deprecated, please refer to the release description: \'dmx help release\'')

        # regression mode 
        # https://jira01.devtools.intel.com/browse/PSGDMX-29
        parser.add_argument('--regmode', required=False, default=False, action='store_true',
                            help='(For Developers Only) Used for running regressions. When turned on, run will not create splunk dashboard results and REL config.')
        
    @classmethod
    def extra_help(cls):
        '''
        Extra help for dmx help release library
        '''
        extra_help = '''\
            -------------------------------------------------------
            Release a deliverable (With --deliverable or -d option)
            -------------------------------------------------------
            This command is used to create deliverable releases.

            Deliverable will be released from a BOM (-b) provided by the users.
            If the deliverable is not part of the BOM, release will error out.

            IPSPEC no longer needs to be provided as part of release option as the command
            will automatically read in IPSPEC from the BOM provided in -b option.

            You can attempt to release multiple deliverables at a time. 
            This can be done by giving a space delimited list of deliverables to the 
            --deliverable option, or specifying --deliverable multiple times.

            When releasing multiple deliverables each deliverable is processed sequentially.
            Release will stop all processing on the first error encountered. 
            One deliverable is submitted to the gated release system, wait for the
            results, and then continue processing the next deliverable release. 

            The milestone, thread, and label (optional) are used to build the final REL boms 
            using the standard naming convention (spaces inserted for readability):
                REL milestone thread [--label] __ timestamp

            The release command will wait for the gated release system to finish processing a 
            deliverable before proceeding to the next deliverable.
            A message will be printed informing you as to whether or not a REL bom was created.

            Examples:
            $ dmx release -p i10socfm -i cw_lib -d rtl -b dev -m 1.0 -t FM8revA0 --label sample --desc "Clean RTL for 7/7 model spec"
            Release only deliverable cw_lib:rtl from 14socnd/cw_lib@dev BOM

            $ dmx release -p i10socfm -i cw_lib -d rtl oa -b dev -m 1.0 -t FM8revA0 --label sample --desc "Clean RTL for 7/7 model spec"
            Release deliverable cw_lib:rtl and cw_lib:oa from 14socnd/cw_lib@dev BOM

            ------------------------------------------------
            Release a view (With --deliverable or -d option)
            ------------------------------------------------
            This command is used to create view releases.

            As of dmx/6.0, view release is introduced. Users could provide view(s) to --deliverable to release a set of deliverables defined as a view.
            View is defined by methodology as a set of deliverables and is static.

            Normal ICM deliverable cannot be provided together with view. 
            For example: --deliverable view_1 rtl
                         This mode is not supported

            Multiple views can be provided together to --deliverable
            For example: --deliverable view_1 view_2            

            Release command will release every deliverable defined in the provided view(s) and the IP as well. The IP release will only contained the deliverables defined in the view(s).

            As of dmx/8.1, view release now needs to be cross-checked against a syncpoint. 
            Release will be aborted if the BOM to be released has conflicts with the given syncpoint.

            Examples:
            $ dmx release -p i10socfm -i cw_lib -d view_1 -b dev -m 1.0 -t FM8revA0 --label sample --desc "Clean RTL for 7/7 model spec" --syncpoint RTL1.0FM8revA0
            Checks i10socfm/cw_lib@dev agaisnt syncpoint RTL1.0FM8revA0. If there are no conflicts, if view_1 consists of rtl and oa, release deliverable cw_lib:rtl and cw_lib:oa from 14socnd/cw_lib@dev BOM, then release i10socfm/cw_lib which contains only cw_lib:rtl@REL and cw_lib:oa@REL


            ------------------------------------------------
            Release a prel (With --deliverable or -d option)
            ------------------------------------------------
            This command is used to create prel releases.

            As of dmx/13.0, prel release is introduced. Users could provide prel to --deliverable to release a set of deliverables defined as a PREREL.
            Prel is defined by methodology as a set of deliverables and is static.

            The following are not supported:-
            
            prel + icm-deliverable
                eg: --deliverable prel_1 rtl

            More than 1 prel
                eg: --deliverable prel_1 prel_2

            Mixture of prel and views
                eg: --delivearble prel_1 view_1


            The following are supported:-
            
            releasing entire variant with a prel
                eg: --deliverable prel_1
                This will release all libtypes directly under this variant as PREL, and then if successful, will then release the variant as PREL.
                Note:
                    All sub-variants under this variant should be at least a REL* or PREL*
                    This release mode needs to be supplied with the --syncpoint/--skipsyncpoint option.

            releasling a single libtype with only the checks associated with the prel
                eg: --deliverable prel_1:rtl
                This will release the rtl libtype, which will only run the checks associated with prel_1.

            releasing a list of libtypes with only the checks associated with the prel
                eg: --deliverable prel_1:rtl prel_1:sta
                This will release the rtl and sta libtype, which will only run the checks associated with prel_1.



            --------------------------------------------------
            Release an IP (Without --deliverable or -d option)
            --------------------------------------------------
            If deliverables are not given, this command will attempt to create release for 
            an IP instead.
            All sub-boms must be REL; that is, all the sub-boms to be included in the ip bom 
            must have already been released (using dmx release command).
            
            The milestone, thread, and label (optional) are used to build the final REL boms 
            using the standard naming convention (spaces inserted for readability):
                REL milestone thread [--label] __ timestamp

            The description is used to help locate this release request in the release queue 
            or results.
            The system will also remember the user initiating the release for these reasons.

            The release behaviour is to send the release request to the gated release system,
            wait for the result, report it, and then exit.

            As of dmx/8.1, IP release now needs to be cross-checked against a syncpoint. 
            Release will be aborted if the BOM to be released has conflicts with the given syncpoint.

            Example
            =======
            $ dmx release -p i10socfm -i cw_lib -b dev -m 1.0 -t FM8revA0 --label sample --desc "Clean RTL for 7/7 model spec" --syncpoint RTL1.0FM8revA0
            Checks i10socfm/cw_lib@dev agaisnt syncpoint RTL1.0FM8revA0. If there are no conflicts, release IP cw_lib provided all deliverables within cw_lib have already been released

            -------------------------------------------------
            Release an IP bottom-up (With --hierarchy option)
            -------------------------------------------------
            If --hierarchy is given, command will release the IP from bottom-up. 
            The command always waits for the Test and Release system to finish
            processing a release request before submitting the next release request. 
            If a release fails for any reason, command will stop immediately.

            The default behaviour is to release all unreleased content within the BOM.
            Command will not re-release a released content in the BOM.
            If there is a need to re-release content in the BOM, provide --force together
            with --hierarchy.
            
            The milestone, thread, and label (optional) are used to build the final REL boms 
            using the standard naming convention (spaces inserted for readability):
                REL milestone thread [--label] __ timestamp

            The description is used to help locate this release request in the release queue 
            or results.
            The system will also remember the user initiating the release for these reasons.

            The release behaviour is to send the release request to the gated release system,
            wait for the result, report it, and then exit.

            As of dmx/8.1, IP release now needs to be cross-checked against a syncpoint. 
            Release will be aborted if the BOM to be released has conflicts with the given syncpoint.

            Example
            =======
            $ dmx release -p i10socfm -i cw_lib -b dev -m 1.0 -t FM8revA0 --label sample --desc "Clean RTL for 7/7 model spec" --hierarchy --syncpoint RTL1.0FM8revA0
            Checks i10socfm/cw_lib@dev agaisnt syncpoint RTL1.0FM8revA0. If there are no conflicts, release IP cw_lib bottom-up hierarchically.


            --------------------------------------------------------------------------------
            Release deliverables hierarchically (With --hierarchy and --deliverable options)
            --------------------------------------------------------------------------------
            If --hierarchy and --deliverable <deliverable> are given, command will release all the <deliverable>s it could find in the given BOM
            The command always waits for the Test and Release system to finish
            processing a release request before submitting the next release request. 
            If a release fails for any reason, command will stop immediately.

            The default behaviour is to release all unreleased specified deliverable within the BOM.
            Command will not re-release a released content in the BOM.
            If there is a need to re-release content in the BOM, provide --force together
            with --hierarchy.
            
            The milestone, thread, and label (optional) are used to build the final REL boms 
            using the standard naming convention (spaces inserted for readability):
                REL milestone thread [--label] __ timestamp

            The description is used to help locate this release request in the release queue 
            or results.
            The system will also remember the user initiating the release for these reasons.

            The release behaviour is to send the release request to the gated release system,
            wait for the result, report it, and then exit.

            Example
            =======
            $ dmx release -p i10socfm -i cw_lib -b dev -d rtl oa -m 1.0 -t FM8revA0 --label sample --desc "Clean RTL for 7/7 model spec" --hierarchy
            Release every rtl and oa deliverables that can be found in i10socfm/cw_lib@dev BOM including the sub-IPs

            -----------------
            Applying Waivers.
            -----------------
            For deliverable release, it will automatically read the tnrwaivers.csv file 
            if the waiver file exist (is checked in) inside its deliverable.
                * dmx release -p i10socfm -i cw_lib -d rtl ...
                  workspaceroot/cw_lib/rtl/tnrwaivers.csv will be used as the waiver file
            For  IP release, it will automatically read the tnrwaivers.csv waiver files
            from all deliverables of its IP.
                * dmx release -p i10socfm -i cw_lib ...
                  workspaceroot/cw_lib/*/tnrwaivers.csv will be used as the waiver file
            
                        '''

        if is_admin():
            extra_help += '''
            #####################
            ~~~ ADMIN OPTIONS ~~~
            #####################
            For admins only. 
            If at times, admins need to run 'dmx release' by forcing it to read from a certain dmx/dmxdata version, 
            they can play around with this 2 environment variables:
            - DMXREL_DMXPATH        (fullpath to release_runner.py)
            - DMXREL_DMXDATAPATH    (fullpath to DMXDATA_ROOT)

            By setting these 2 environment variables, 'dmx release' will honor and use the paths set in the environment variables.

            Example:-
                >setenv DMXREL_DMXPATH      /p/psg/data/lionelta/dmx/main/lib/python/dmx/tnrlib/release_runner.py
                >setenv DMXREL_DMXDATAPATH  /p/psg/data/lionelta/dmxdata/main/data
            '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''execute the subcommand'''
        # generic arugments
        project = args.project
        ip = args.ip
        bom = args.bom
        milestone = args.milestone
        thread = args.thread
        label = args.label
        desc = args.desc
        preview = args.preview
        wait = True
        force = args.force
       
        # releaselibrary arguments
        deliverables = [y for x in args.deliverable for y in x]

        # releasetree arguments
        hierarchy = args.hierarchy
        intermediate = False

        # http://pg-rdjira:8080/browse/DI-653 
        # required_only flag is always True
        required_only = True

        # for legacy compatibility        
        waiver_files = None

        # https://jira.devtools.intel.com/browse/PSGDMX-1882
        # support for PREREL
        is_prel = False
        for deliverable in deliverables:
            if deliverable.startswith('prel_'):
                is_prel = True
        ### Start checking for disallowed cases for PREL mode
        if is_prel:
            if hierarchy:
                raise ReleaseError('Hierarchical release of prel are not supported. Please refer to the help description of dmx release: \'dmx help release\'')
            if len(deliverables) > 1:
                if [x for x in deliverables if ':' not in x]:
                    raise ReleaseError("PREL release mode of multiple deliverables only allow multiple [prel:deliverable prel:deliverable ...]. Please refer to 'dmx help release' for detail help.")

        # http://pg-rdjira:8080/browse/DI-685
        # if the deliverable starts with view, it is a view release
        # must be submitted to releaseview
        is_view = False
        for deliverable in deliverables:
            if deliverable.startswith('view'):
                is_view = True      
        if is_view and hierarchy:
            #raise ReleaseError('Hierarchical release of views are not supported. Please refer to the help description of dmx release: \'dmx help release\'')
            print('Hierarchical release of views were not supported. Now they are !!!')
       
        ### Disable --skipsyncpoint for REL
        if not is_prel and args.skipsyncpoint:
            raise ReleaseError("(DEPRECATED) --skipsyncpoint is no longer allowed!")

        if is_view or not deliverables or (is_prel and ':' not in deliverables[0]):
            # http://pg-rdjira:8080/browse/DI-1060
            # New syncpoint argument for IP release
            syncpoint = args.syncpoint
            skipsyncpoint = args.skipsyncpoint
            if skipsyncpoint:
                if len(str(skipsyncpoint)) < 10:
                    raise ReleaseError('Justification reason to skip syncpoint must be >= 10 characters')            
            if not syncpoint and not skipsyncpoint:
                raise ReleaseError('Release of view/IP needs to be provided with --syncpoint or --skipsyncpoint.')                    

            # http://pg-rdjira:8080/browse/DI-1179
            # Argument to skip milestone checking
            skipmscheck = args.skipmscheck
            if skipmscheck:
                if len(str(skipmscheck)) < 10:
                    raise ReleaseError('Justification reason to skip milestone checking must be >= 10 characters')

        # deprecated option
        ipspec = args.ipspec
        if ipspec:
            raise ReleaseError('--ipspec option is already deprecated. Please refer to the help description of dmx release: \'dmx help release\'')

        # temporary option
        wait = not args.nowait

        ret = 1

        if deliverables:
            '''
            The decision making process for this command is detailed below:
            If the input bom is mutable:
                If there is an outstanding change:
                    An IC Manage library release is created
                    A snap- simple bom is created that points to the library release
                    The snap- bom is submitted to the gated release queue
                Else
                    Re-submit the last snap that references this content

            If the input bom is immutable:
                If the bom is a REL bom:
                    If the milestone or thread are different:
                        The corresponding snap- bom is submitted to the gated release system
                If the bom is snap-
                    The snap- bom is re-submitted to the gated release system
            '''
            if hierarchy and not is_view:
                release = ReleaseDeliverables(project, ip , bom, deliverables, 
                                      milestone, thread, desc, 
                                      label=label, force=force,
                                      preview=preview, regmode=args.regmode)
                ret = release.run()

            elif is_prel:
                if ':' in deliverables[0]:
                    for deliverable in deliverables:
                        ret = 1
                        release = ReleaseDeliverable(project, ip, deliverable, bom, milestone, thread,
                                                 desc, label=label,  
                                                 wait=wait, force=force,
                                                 preview=preview, regmode=args.regmode)
                        ret = release.run()
                        if ret != 0:
                            break
                else:
                    release = ReleasePrel(project, ip, deliverables[0], 
                                          bom, milestone, thread, desc, 
                                          label=label, syncpoint=syncpoint,
                                          skipsyncpoint=skipsyncpoint, 
                                          skipmscheck=skipmscheck,
                                          preview=preview, regmode=args.regmode)
                    ret = release.run()

            else:
                if is_view:
                    if hierarchy:
                        release = ReleaseTree(project, ip, bom, milestone, thread, desc, 
                                              label=label, required_only=required_only, 
                                              intermediate=intermediate,
                                              waiver_files=waiver_files, force=force,
                                              syncpoint=syncpoint, skipsyncpoint=skipsyncpoint,
                                              skipmscheck=skipmscheck,
                                              preview=preview, views=deliverables, regmode=args.regmode)
                    else:
                        release = ReleaseView(project, ip, deliverables, 
                                              bom, milestone, thread, desc, 
                                              label=label, syncpoint=syncpoint,
                                              skipsyncpoint=skipsyncpoint, 
                                              skipmscheck=skipmscheck,
                                              preview=preview, regmode=args.regmode)
                    ret = release.run()
                else:
                    for deliverable in deliverables:
                        ret = 1
                        release = ReleaseDeliverable(project, ip, deliverable, bom, milestone, thread,
                                                 desc, label=label,  
                                                 wait=wait, force=force,
                                                 preview=preview, regmode=args.regmode)
                        ret = release.run()
                        if ret != 0:
                            break
        else:
            '''
            A snapshot of the given bom is made and then VP context and audit checks are performed against all deliverables in the given ip bom as well as those required by the development roadmap (based on the ip type, milestone, and thread). 
            If all tests pass (or failures are waived), the snap bom will be converted to a REL bom.
            Snap boms will be cleaned up every 60 days. 
            Please note that the given bom must include references to all related ips and deliverables required for audit validation.
            '''
            if hierarchy:
                release = ReleaseTree(project, ip , bom, milestone, thread, desc, 
                                      label=label, required_only=required_only, 
                                      intermediate=intermediate,
                                      waiver_files=waiver_files, force=force,
                                      syncpoint=syncpoint, skipsyncpoint=skipsyncpoint,
                                      skipmscheck=skipmscheck,
                                      preview=preview, regmode=args.regmode)
            else:
                release = ReleaseVariant(project, ip , bom, milestone, thread, desc, 
                                     label=label, wait=wait,
                                     waiver_files=waiver_files, force=force,
                                     syncpoint=syncpoint, skipsyncpoint=skipsyncpoint,
                                     skipmscheck=skipmscheck,
                                     preview=preview, regmode=args.regmode)                     
            ret = release.run()
        return ret

