#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/plugins/bomedit.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "dmx bom edit"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''

import os
import sys
import logging
import textwrap

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.edittree import EditTree

class BomEditError(Exception): pass

class BomEdit(Command):
    '''plugin for "dmx bom edit"'''

    @classmethod
    def get_help(cls):
        '''one-line description for "dmx help"'''
        myhelp = '''\
            A swiss-knife tool to edit a BOM hierarchically
            '''
        return textwrap.dedent(myhelp)

    @classmethod
    def add_args(cls, parser):
        '''set up argument parser this subcommand'''
        add_common_args(parser)
        parser.add_argument('-p', '--project', metavar='project', required=False, default=None,
                            help='source project')
        parser.add_argument('-i', '--ip', metavar='ip', required=True, help='source ip')
        parser.add_argument('-b', '--bom',  metavar='src_bom', required=True, help='source bom')
        parser.add_argument('--inplace',  action='store_true', help='edit all mutable boms in-place.  --newbom may still be required if any immutable boms require editing.')
        parser.add_argument('--newbom',  metavar='newbomname', required=False, help='''
            name to use for newly created boms - existing boms by this name are edited in place''')
        parser.add_argument('--showtree',  action='store_true', help='For debugging: show the raw tree data structure after all edits have been internally processed and before executing any icManage edit commands.')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--includedeliverables', nargs='+', metavar='deliverable', help='remove all deliverables except the deliverables in this list')
        group.add_argument('--excludedeliverables', nargs='+', metavar='deliverable', help='remove all deliverables in this list')
        group.add_argument('--addbom', nargs='*', action='append',
                           help='add a new bom. Refer to argument format below')
        group.add_argument('--delbom', nargs='*', action='append',
                           help='remove given bom. Refer to argument format below')
        group.add_argument('--repbom', nargs=2, action='append',
                           help='replace existing bom with given bom. Refer to argument format below')
        parser.add_argument('-f', '--file',
                            metavar='file', required=False,
                            help='A file that lists the operations to perform on the source BOM')

    @classmethod
    def extra_help(cls):
        '''extra narrative for dmx help bom edit'''
        extra_help = '''\
            This command is a "swiss army knife" for editing a bom hierarchically.
            Basic usage is to specify a top bom, whether to edit mutable
            boms inplace, a name for any newly created boms, and the edit
            commands desired.  
            All error checking is done prior to any bom editing.
            Only 1 type of operation may be specified for each edittree command.
            For multiple additions, deletions or replacements, please split them up
            into multiple bom edit calls. 
            
            Note:
            * Mutable boms are any bom that doesn't start with "REL" or "snap-"
            * Immutable boms are any bom that start with "REL" or "snap-"

            One or both of "--newbom" and/or "--inplace" must be specified.
            * If both "--inplace" and "--newbom" are specified, mutable boms are
              edited in place and immutable boms are cloned to the "--newbom" name.
            * If "--inplace" is specified and "--newbom" is not specified, it is
              an error if any immutable bom needs to be edited.
            * If a bom needs to be copied to the "--newbom" name, it is an
              error if the "--newbom" name already exists (unless it is already in
              the original tree, in which case it is edited in-place)
            * The "--newbom" option must provide a mutable bom name (not "RELxxx"
              or "snap-xxx")

            Edit commands are effectively processed in the following order:
            1) addip/delip/repip/adddel/deldel/repdel: modify the bom hierarchically
            3) "uniquification":  all new boms require editing of the parent to
               reference the new child.  If editing the parent requires creating a
               new bom, this process ripples up the hierarchy.

            Arguments format for addbom:
            1. --addbom project/childip@bom project/parentip
                * add a child ip bom reference to a parent bom
                * it is an error to attempt to add a childip if the parent already
                  refers to that bom
                * it is an error if the new bom creates a recursive cycle of
                  boms 
            2. --addbom project/ip:deliverable@bom 
                * add project/ip:deliverable@bom to project/ip@bom
                * it is an error if ip@bom already has an entry for the
                  specified deliverable (use "--repbom" instead) 

            Example
            =======
            $dmx bom edit -p i10socfm -i cw_lib -b dev --addbom i10socfm/ce_lib@dev i10socfm/cw_lib
            Add i10socfm/ce_lib@dev BOM to i10socfm/cw_lib@dev BOM

            $dmx bom edit -p i10socfm -i cw_lib -b dev --addbom i10socfm/ce_lib@dev i10socfm/cs_lib
            Look for i10socfm@cs_lib BOM in i10socfm/cw_lib@dev and add i10socfm/ce_lib@dev BOM to i10socfm/cs_lib BOM

            $dmx bom edit -p i10socfm -i cw_lib -b dev --addbom i10socfm/cw_lib:rtl@dev
            Add i10socfm/cw_lib:rtl@dev BOM to i10socfm/cw_lib@dev BOM        

            Arguments format for delbom:
            1. --delbom project/childip [project/parentip...]
                * if no parentips are specified:
                    - the childip is deleted everywhere it appears in the
                      source bom
                    - it is an error if the childip is not found in the source tree
                * if one or more parentips are specified:
                    - the childip is only deleted from the specified parentips
                    - it is an error if a listed parent doesn't reference the
                      childip
            2. --delbom project/ip:deliverable
                * the deliverable is removed from source bom
                * it is an error if the source bom doesn't have a an
                  entry for the specified deliverable                  

            Example
            =======
            $dmx bom edit -p i10socfm -i cw_lib -b dev --delbom i10socfm/ce_lib
            Remove every i10socfm/ce_lib BOM found in i10socfm/cw_lib@dev BOM

            $dmx bom edit -p i10socfm -i cw_lib -b dev --delbom i10socfm/ce_lib i10socfm/cw_lib
            Remove only i10socfm/ce_lib BOM from i10socfm/cw_lib BOM

            $dmx bom edit -p i10socfm -i cw_lib -b dev --delbom i10socfm/ce_lib i10socfm/cw_lib i10socfm/cs_lib
            Remove only i10socfm/ce_lib BOM from i10socfm/cw_lib BOM and i10socfm/cw_lib BOM (i10socfm/cs_lib BOM must be found in i10socfm/cw_lib)

            $dmx bom edit -p i10socfm -i cw_lib -b dev --delbom i10socfm/cw_lib:rtl
            Remove i10socfm/cw_lib:rtl BOM from i10socfm/cw_lib BOM

            Arguments format for repbom:
            1. --repbom project/ip newbom
                * all occurrences of ip are replaced with references to the
                  newbom of ip
                * it is an error if the ip is not found in the source bom
            2. --repbom project/ip:deliverable newbom
                * the project/ip:deliverable is replaced with new bom
                * it is an error if there is not already an entry for the deliverable
                  (use "--addbom" instead)              

            Example
            =======
            $dmx bom edit -p i10socfm -i cw_lib -b dev --repbom i10socfm/ce_lib testing
            Replace i10socfm/ce_lib BOM found in i10socfm/cw_lib@dev BOM to i10socfm/ce_lib@testing BOM

            $dmx bom edit -p i10socfm -i cw_lib -b dev --repbom i10socfm/cw_lib:rtl testing
            Replace i10socfm/cw_lib:rtl BOM found in i10socfm/cw_lib@dev BOM to i10socfm/cw_lib:rtl@testing BOM

            Arguments format for includedeliverables/excludedeliverables:
            --includedeliverables deliverable...
            --excludedeliverables deliverable...
                * Only one of includedeliverables or excludedeliverables can be 
                  specified
                * These options are functionally equivalent to a corresponding 
                  set of delbom commands
                * includedeliverables specifies the set of deliverables to include,
                  any others are deleted
                * excludedeliverables specifies the set of deliverables to exclude, 
                  any others will remain

            Example
            =======
            $dmx bom edit -p i10socfm -i cw_lib -b dev --includedeliverables rtl
            Removes every other deliverables from i10socfm/cw_lib@dev except rtl

            $dmx bom edit -p i10socfm -i cw_lib -b dev --excludedeliverables rtl
            Removes every rtl BOM found in i10socfm/cw_lib@dev

            For ease of usage, addbom/delbom/repbom/includedeliverables/excludedeliverables 
            arguments can be listed in a file and be provided
            to --file option. 

            Example
            =======
            option.txt:
            --repbom i10socfm/ce_lib testing
            --delbom i10socfm/cs_lib

            $dmx bom edit -p i10socfm -i cw_lib -b dev --file option.txt
            Replace i10socfm/ce_lib BOM found in i10socfm/cw_lib@dev BOM to i10socfm/ce_lib@testing BOM
            Remove every i10socfm/cs_lib BOM found in i10socfm/cw_lib@dev BOM

        '''
        return textwrap.dedent(extra_help)

    @classmethod
    def command(cls, args):
        '''the "bom edit" subcommand'''
        project = args.project
        ip = args.ip
        bom = args.bom
        newbom = args.newbom
        inplace = args.inplace
        showtree = args.showtree
        bom_file = args.file
        preview = args.preview

        if bom_file:
            cls.addbom, cls.delbom, cls.repbom, cls.includedeliverables, cls.excludedeliverables = cls.validate_bom_file(bom_file)
        else:
            cls.addbom = args.addbom
            cls.delbom = args.delbom
            cls.repbom = args.repbom
            cls.includedeliverables = args.includedeliverables
            cls.excludedeliverables = args.excludedeliverables

        includedeliverables = [cls.includedeliverables] if cls.includedeliverables else cls.includedeliverables
        excludedeliverables = [cls.excludedeliverables] if cls.excludedeliverables else cls.excludedeliverables
        
        # Force all options to None first
        addboms = []
        delboms = []
        repboms = []
        # We are consolidating all *_simple options with *_bom options
        # This variable is automatically filled if users provide bom for deliverable
        addlibtype = []
        dellibtype = []
        replibtype = []

        if cls.addbom:                
            for addbom in cls.addbom:
                if len(addbom) == 2:
                    # if 2 values are given,  
                    # --addbom project/childip@bom project/parentip
                    addboms.append(addbom)
                elif len(addbom) == 1:
                    # if only single value is given, 
                    # --addbom project/ip:deliverable@bom 
                    addlibtype.append(addbom)
                else:
                    raise Exception('Values provided to --addbom does not follow the format required. Please refer to \'dmx help bom edit\'')    
                
        if cls.delbom:
            for delbom in cls.delbom:
                if len(delbom) == 1:
                    if ':' in delbom[0]:
                        # if only single value is given and doublecolon is found,
                        # --delbom project/ip:deliverable
                        dellibtype.append(delbom)
                    else:
                        # if only single value is given and doublecolon is not found,
                        # --delbom project/childip 
                        delboms.append(delbom)
                else:
                    # if 2 or more values are given,
                    # --delbom project/childip [project/parentip...]
                    delboms.append(delbom)

        if cls.repbom:
            for repbom in cls.repbom:
                if ':' in repbom[0]:
                    # if doublecolon is found,
                    # --repbom project/ip:deliverable newbom
                    replibtype.append(repbom)
                else:
                    # if doublecolon is not found
                    # --repbom project/ip newbom
                    repboms.append(repbom)

        edittree = EditTree(project, ip, bom, inplace=inplace,
                            new_config=newbom, show_tree=showtree,
                            add_configs=addboms, del_configs=delboms,
                            rep_configs=repboms, add_libtype=addlibtype,
                            del_libtype=dellibtype, rep_libtype=replibtype,
                            include_libtypes=includedeliverables,
                            exclude_libtypes=excludedeliverables,
                            preview=preview)

        return (edittree.run())

    @classmethod
    def validate_bom_file(cls, bom_file):
        '''
        Read in arguments provided in a file to respective options 
        '''
        addbom = []
        delbom = []
        repbom = []
        includedeliverables = []
        excludedeliverables = []

        if not os.path.exists(bom_file):
            raise Exception('File {} does not exist'.format(bom_file))

        with open(bom_file, 'r') as f:
            for line in f.readlines():
                # Skip comments and empty lines
                if line.startswith('#'):
                    continue
                if not line.rstrip():
                    continue

                items = line.split()
                if line.startswith('--addbom'):
                    addbom.append(items[1:])
                elif line.startswith('--delbom'):
                    delbom.append(items[1:])
                elif line.startswith('--repbom'):
                    repbom.append(items[1:])
                elif line.startswith('--includedeliverables'):
                    for item in items[1:]:
                        includedeliverables.append(item)
                elif line.startswith('--excludedeliverables'):
                    for item in items[1:]:
                        excludedeliverables.append(item)

        return addbom, delbom, repbom, includedeliverables, excludedeliverables                    
