#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/createvariant.py#3 $
$Change: 7808991 $
$DateTime: 2023/10/04 23:53:43 $
$Author: lionelta $

Description: branch abnr subcommand
Author: Lee Cartwright
Copyright (c) Altera Corporation 2013
All rights reserved.
'''

import sys
import os
import logging
import textwrap
import getpass
import time
import re
import datetime

from dmx.abnrlib.icm import ICManageCLI
#from dmx.abnrlib.icmcompositeconfig import CompositeConfig
#from dmx.abnrlib.icmsimpleconfig import SimpleConfig
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.namevalidator import ICMName
from dmx.utillib.multiproc import run_mp
from dmx.utillib.admin import is_admin
from dmx.utillib.utils import user_exists, get_default_dev_config
from dmx.utillib.arcenv import ARCEnv
from dmx.utillib.naa import NAA
import dmx.utillib.admin

# Import ecolib
import dmx.ecolib.ecosphere 
import dmx.ecolib.__init__

if not dmx.ecolib.__init__.LEGACY:
    from dmx.djangolib.models import *

# In legacy, each sub-list of projects needs to be handled as a group regarding naming conflicts.
# For PICE, all projects are handled as one group.
LEGACY_PROJECTS = ('Crete', 't20socand', 'Nadder', 'i14socnd', 'process_t20socanf', 
                   'process_nadder_14nm', 'Crete3', 'CretextIP')

PROJECT_LISTS = [
    ('Crete', 't20socand', 'Nadder', 'i14socnd', 'process_t20socanf', 
        'process_nadder_14nm', 'Crete3', 'CretextIP'), 
    ('Crete', 't20socand', 'process_t20socanf', 'i10socfm', 'Falcon_Mesa', 
        'Crete3', 'CretextIP'),
    ]

# http://pg-rdjira:8080/browse/DI-561
ILLEGAL_NAMES = [
    'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3',
    'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1',
    'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8',
    'LPT9'
]

# http://pg-rdjira:8080/browse/DI-1319
ILLEGAL_VARIANT_TYPES = ['asicustom']

# http://pg-rdjira:8080/browse/DI-1429
ILLEGAL_VARIANT_PREFIXES = ['REL', 'RC', 'snap-']

# https://jira01.devtools.intel.com/browse/PSGDMX-1443
ILLEGAL_VARIANT_PREFIXES += ['fc0', 'f0', 'f8', 'e8', 'fdk', 'ip7', 'x74', 'rng_es1_gen4']

class CreateVariantError(Exception): pass

class CreateVariant(object):
    '''
    Handles running the createvariantiant command
    '''
    def __init__(self, project, variant, variant_type, description='', 
                 preview=True, nocheck=False, owner=os.getenv('USER'),
                 roadmap=''):
        self.project = project
        self.variant = variant
        self.variant_type = variant_type
        self.description = description
        self.preview = preview
        self.nocheck = nocheck
        self.owner = owner       
        self.exclude_prefix_name_list = ['soc', 'proxy']     # prefix name which should be exlucded from conflict check (Fogbugz 345524), (Fogbugz 373756)       
        
        # http://pg-rdjira:8080/browse/DI-561
        if variant.upper() in ILLEGAL_NAMES:
            raise CreateVariantError("IP(Variant) name is illegal. These names are illegal IP name: {}".format(ILLEGAL_NAMES))

        # http://pg-rdjira:8080/browse/DI-1429
        for illegal_prefix in ILLEGAL_VARIANT_PREFIXES:
            if variant.startswith(illegal_prefix):
                raise CreateVariantError("IP(Variant) name cannot begin with {}".format(illegal_prefix))

        # http://pg-rdjira:8080/browse/DI-1319
        # Do not allow users to create variant with variant type registered in ILLEGAL_VARIANT_TYPES 
        # Only allow admin to do so
        if variant_type in ILLEGAL_VARIANT_TYPES and not dmx.utillib.admin.is_admin():
            if not is_admin(os.getenv('USER')):
                raise CreateVariantError('Variant type {} is not allowed. Please refer to psgicmsupport@intel.com.'.format(variant_type))

        # Pattern that is exempt from prefix checking as they have no sub-cells.
        # This is for the multidie <channel>_virtual_<product> IPs.
        self.exclude_pattern_from_prefix_check = '.*[a-zA-Z0-9].*_virtual_.*[a-zA-Z0-9].*'
        
        self.cli = ICManageCLI(preview=self.preview)
        self.logger = logging.getLogger(__name__)

        # Make sure the variant name is valid
        if not ICMName.is_variant_name_valid(variant):
            raise CreateVariantError('{0} is not a valid variant name'.format(variant))

        # Make sure the project exists
        if not self.cli.project_exists(self.project):
            raise CreateVariantError("{0} is not a valid project".format(self.project))

        # Make sure the variant doesn't exist
        if self.cli.variant_exists(self.project, self.variant):
            raise CreateVariantError("Variant {0} already exists in project {1}".format(self.variant, self.project))

        # http://pg-rdjira.altera.com:8080/browse/DI-621
        # Make sure that the owner name cannot be an admin
        '''
        if is_admin(self.owner):
            raise CreateVariantError("{} is not allowed to be an owner of an IP as he/she is a DMX admin".format(self.owner))
        '''
        # Make sure the owner name exists            
        if not user_exists(self.owner):  
            raise CreateVariantError("{} is not a valid username".format(self.owner)) 

        # http://pg-rdjira.altera.com:8080/browse/DI-621
        # If nocheck is specified, skip prefix name checking
        if not self.nocheck:
            # TODO Should be its own method with its own tests...
            # Make sure variant does not have prefix name conflict - unless we are allowing the pattern.
            if not re.match(self.exclude_pattern_from_prefix_check, self.variant):
                if self.cli.get_variant_name_prefix(self.variant) not in self.exclude_prefix_name_list:
                    conflict_variants = None
                    if self.project in LEGACY_PROJECTS:
                        for project_list in PROJECT_LISTS:                        
                            if self.project in project_list:
                                existing_projects = [x for x in project_list if self.cli.project_exists(x)]
                                conflict_variants = self.cli.get_conflicting_variant_prefix(self.variant, existing_projects)
                    else:
                        # All non-legacy projects are in the same group of disallowed conflicts.
                        # Originally this was WHR and onward but per http://pg-rdjira:8080/browse/DI-871
                        # It's now all of PICE.
                        # Get the list of existing projects and strip out LabProjects
                        #all_projects = [x for x in self.cli.get_projects() if 'LabProject' not in x]
                       
                        # Previously conflict check checks across all icm-projects. Now, 
                        # only do conflict check on same icm-projects. https://jira.devtools.intel.com/browse/PSGDMX-2129
                        all_projects = [self.project]
                        if self.project in all_projects:
                            conflict_variants = self.cli.get_conflicting_variant_prefix_for_whr_onwards(self.variant, all_projects)
                    if conflict_variants:
                        raise CreateVariantError("Variant {} has conflict prefix names with: {}".format(self.variant, conflict_variants))

        # Get the variant type definitions
        self.family = dmx.ecolib.ecosphere.EcoSphere(preview=self.preview).get_family(os.getenv("DB_FAMILY"))

        # http://pg-rdjira:8080/browse/DI-1159
        # Ensure that IP is unique across all projects in the same family
        if not self.nocheck:
            if os.getenv("DMX_FAMILY_LOADER", "") != 'family_test.json':
                if self.variant in self.family.get_ips_names():
                    existing_ip = self.family.get_ip(self.variant)
                    raise CreateVariantError("Variant {} already exists in project {}".format(existing_ip.icmvariant, existing_ip.icmproject)) 

        if roadmap:
            # Ensure that roadmap is valid
            self.roadmapobj = self.family.get_roadmap(roadmap)
            self.roadmap = roadmap
        else:
            device = ARCEnv().get_device()
            if device:
                self.roadmap = self.family.get_product(device).roadmap
            else:
                raise CreateVariantError('--roadmap needs to be provided')            

        variant_type = self.family.get_iptype(self.variant_type, roadmap=self.roadmap)            
        libtypes = variant_type.get_all_deliverables(roadmap=self.roadmap)

        # Make sure all libtypes are defined in the system
        bad_libtypes = []
        for libtype in [x.deliverable for x in libtypes]:
            if not self.cli.libtype_defined(libtype):
                bad_libtypes.append(libtype)

        if bad_libtypes:
            error_msg = "This variant type contains library types that have not been defined.\n"
            error_msg += "Non-defined library types are: {}\n".format(' '.join(bad_libtypes))
            error_msg += "Please contact psgicmsupport@intel.com\n"
            raise CreateVariantError(error_msg)
        else:
            self.libtypes = [x.deliverable for x in libtypes]

        ### Setting default library/config naming. https://jira.devtools.intel.com/browse/PSGDMX-1661
        ### Setting default library/config naming. https://jira.devtools.intel.com/browse/PSGDMX-2329
        thread = os.getenv("DB_THREAD")
        self.default_config_name = get_default_dev_config(family=self.family.name, icmproject=self.project, thread=thread)
        self.default_library_name = self.default_config_name
        self.logger.debug("Family:{}, default_config:{}, default_library:{}".format(self.family.name, self.default_config_name, self.default_library_name))



    def create_dev_configs(self):
        '''
        Creates the simple and composite configs for the libtypes
        '''
        ret = False

        default_cfg_name = self.default_config_name
        default_library_name = self.default_library_name

        # First build all the simple configs
        simple_configs = []
        for libtype in self.libtypes:
            '''
            simple_config = IcmLibrary(default_cfg_name, self.project, self.variant, libtype,
                                         default_library_name, '#ActiveDev', cli=self.cli,
                                         preview=self.preview)
            # http://pg-rdjira:8080/browse/DI-1055
            # Config should be created with owner's name
            simple_config.add_property('Owner', self.owner)
            '''
            simple_config = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, default_cfg_name, libtype, preview=self.preview)
            simple_configs.append(simple_config)

        # Now the composite
        composite_config = IcmConfig(default_cfg_name, self.project, self.variant, simple_configs, preview=self.preview)
        # http://pg-rdjira:8080/browse/DI-1055
        # Config should be created with owner's name
        composite_config.add_property('Owner', self.owner)
        ret = composite_config.save(shallow=False)

        return ret

    def build_variant_properties(self, owner=os.getenv('USER')):
        '''
        Returns a dictionary representing the variant's properties
        '''
        return {
            'Owner' : owner,
            'iptype' : self.variant_type,
        }

    def create_variant(self):
        '''
        Creates variant within project and adds meta data defining
        who created the variant, when they created it and what
        type it is
        '''
        ret = False

        self.logger.info("Start creating variant ...")
        ret = self.cli.add_variant(self.project, self.variant, description=self.description)
        self.logger.info("Done creating variant ...")
        if ret:
            self.logger.info("Start adding variant properties ...")
            properties = self.build_variant_properties(self.owner)
            ret = self.cli.add_variant_properties(self.project, self.variant, properties)
            self.logger.info("Done adding variant properties ...")
        return ret

    def add_libtype_structure_to_variant(self):
        '''
        Adds the libtypes, libraries and simple configs to the variant.

        Uses the abnr multiprocessing library to do so.

        :raises: CreateVariantError
        '''
        mp_args = []
        for libtype in self.libtypes:
            iptypeobj = self.family.get_iptype(self.variant_type).get_deliverable(libtype)
            large_excluded_ip = iptypeobj.large_excluded_ip
            is_large = iptypeobj.large and self.variant not in large_excluded_ip

            mp_args.append([self.project, self.variant, libtype, self.preview, self.owner, is_large, self.family.family, 
                self.default_config_name, self.default_library_name])

        ''' TODO: Do we need to parallelize in gdpxl, since the speed is already so fast?
        results = run_mp(add_libtype_to_variant, mp_args, num_processes=3)
        for result in results:
            if not result['success']:
                raise CreateVariantError('Problem creating libtype {0}'.format(result['libtype']))
        '''

        ### This section of the code is left here in purpose for debugging.
        ### It runs the above code in series instead of parallel
        for project, variant, libtype, preview, owner, is_large, family, _, _ in mp_args:
            self.logger.debug("Working on {}".format([project, variant, libtype, preview, owner, is_large, family, self.default_config_name, self.default_library_name]))
            ret = add_libtype_to_variant(project, variant, libtype, preview, owner, is_large, family, self.default_config_name, self.default_library_name)
            self.logger.debug("- {}".format(ret))


    def create_the_variant(self):
        '''
        Creates the variant and it's libtypes
        '''
        ret = 1
        # Make sure there are some libtypes associated with the variant
        if not self.libtypes:
            self.logger.error("No libtypes defined for variant type '{}'".format(self.variant_type))
            ret = 1
        else:
            # Create the variant and it's meta data
            if self.create_variant():
                # Create the structure (libtype/library/simple config)
                self.add_libtype_structure_to_variant()
                # Now create the configuration tree
                if self.create_dev_configs():
                    ret = 0
                else:
                    ret = 1
            else:
                ret = 1

        return ret

    def run(self):
        '''
        Runs the createvariantiant command
        '''
        ret = 1
        ret = self.create_the_variant()

        return ret

def add_libtype_to_variant(project, variant, libtype, preview, owner=os.getenv('USER'), is_large=False, family=None, default_config='dev', default_library='dev'):
    '''
    Adds the new libtype, the default dev library and the default dev
    configuration to the variant.

    :param project: The IC Manage project
    :type project: str
    :param variant: The IC Manage variant we're adding libtype/library/simple config to
    :type variant: str
    :param libtype: The name of the libtype to add.
    :type libtype: str
    :param preview: Boolean indicating whether or not we're in preview mode
    :type preview: bool
    :return: Dictionary containing name of libtype and success status
    :rtype: dict
    :raises: CreateVariantError
    '''
    ret = {
        'libtype' : libtype
    }
    cli = ICManageCLI(preview=preview)
    default_config = default_config
    default_library = default_library

    cli.add_libtypes_to_variant(project, variant, [libtype])
    if not preview and not cli.libtype_exists(project, variant, libtype):
        raise CreateVariantError('Failed to add libtype {} to {}/{}'.format(
            libtype, project, variant
        ))

    cli.add_libraries(project, variant, [libtype], library=default_library)
    if not preview and not cli.library_exists(project, variant, libtype, default_library):
        raise CreateVariantError('Failed to add {} library to {}/{}:{}'.format(
            default_library, project, variant, libtype
        ))

    # http://pg-rdjira:8080/browse/DI-1287
    # For large data deliverable, create a dev NAA label that will be aligned to ICManage dev library
    if is_large:
        family = family if family else dmx.eoclib.ecosphere.EcoSphere(preview=preview).get_family(os.getenv("DB_FAMILY")).family
        naa = NAA(preview=preview)
        naa.create_label(family, project, variant, libtype, default_library)

    dev_cfg = IcmLibrary(project, variant, libtype, default_library, preview=preview)
    # http://pg-rdjira:8080/browse/DI-1055
    # Config should be created with owner's name
    dev_cfg.add_property('Owner', owner)

    if not dev_cfg.save():
        raise CreateVariantError('Failed to create simple config {0}/{1}:{2}@{3}'.format(
            project, variant, libtype, default_config
        ))

    ret['success'] = True

    return ret

