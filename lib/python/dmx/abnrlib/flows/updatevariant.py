#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/updatevariant.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: updatevariant abnr subcommand
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''

import os
import sys
import logging
import textwrap
import time

import dmx.abnrlib.icm
import dmx.abnrlib.icmconfig 
import dmx.abnrlib.icmlibrary 
import dmx.utillib.utils
import dmx.abnrlib.config_factory

import dmx.ecolib.ecosphere
import dmx.ecolib.__init__       
import dmx.utillib.arcenv
import dmx.utillib.admin
import dmx.utillib.naa
import dmx.utillib.admin


# http://pg-rdjira:8080/browse/DI-1319
ILLEGAL_VARIANT_TYPES = ['asicustom']

class UpdateVariantError(Exception): pass

class UpdateVariant(object):
    '''
    Class to handle running updatevariant
    '''

    def __init__(self, project, variant, variant_type, preview):
        self.project = project
        self.variant = variant
        self.variant_type = variant_type
        self.preview = preview
        self.cli = dmx.abnrlib.icm.ICManageCLI(preview=self.preview)
        self.logger = logging.getLogger(__name__)
        self.naa = dmx.utillib.naa.NAA(preview=preview)



        # If project not given, get project from IP
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise UpdateVariantError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
            # Make sure the project and variant exist
            if not self.cli.project_exists(self.project):
                raise UpdateVariantError("{0} is not a valid project".format(self.project))
            if not self.cli.variant_exists(self.project, self.variant):
                raise UpdateVariantError("{0} does not exist within project {1}".format(self.variant, self.project))

        self.family = dmx.ecolib.ecosphere.EcoSphere().get_family(os.getenv("DB_FAMILY"))
        self.logger.debug("FAMILY: {}".format(self.family))
        thread = os.getenv("DB_THREAD")
        ### Setting default library/config naming. https://jira.devtools.intel.com/browse/PSGDMX-2329
        self.defconfig = dmx.utillib.utils.get_default_dev_config(family=self.family.name, icmproject=self.project, thread=thread)
        self.logger.debug("DEFAULT CONFIG: {}".format(self.defconfig))


        try:
            self.ip = self.family.get_ip(self.variant, project_filter=self.project)
        except Exception as e:
            '''
            The reason why the self.family.get_ip() failed inside the try: statement is due to the fact that the variant
            is missing iptype, and thus, we are only fixing that problem now.
            '''
            self.logger.debug(str(e))
            self.logger.info("Seems like IP wasn't created using the official 'dmx ip create' and is missing some properties ...")
            self.logger.info("Trying to fix IP now ...")
            
            properties = {
                'Owner' : os.getenv("USER"),
                'iptype' : self.variant_type,
            }
            self.cli.add_variant_properties(self.project, self.variant, properties)
            self.ip = self.family.get_ip(self.variant, project_filter=self.project)


        if self.variant_type:
            # http://pg-rdjira:8080/browse/DI-1319
            # Do not allow users to create variant with variant type registered in ILLEGAL_VARIANT_TYPES 
            # Only allow admin to do so
            if self.variant_type in ILLEGAL_VARIANT_TYPES and not dmx.utillib.admin.is_admin():
                if not is_admin(os.getenv('USER')):
                    raise UpdateVariantError('Variant type {} is not allowed. Please refer to psgicmsupport@intel.com.'.format(variant_type))

            self.iptype = self.family.get_iptype(self.variant_type)       
        else:
            self.iptype = self.family.get_iptype(self.ip.iptype)
        
    def get_variant_type(self):
        '''
        Gets the variant type from the variant
        '''
        variant_type = self.ip.iptype                        

        return variant_type

          
    def get_variant_type_libtypes(self, variant_type, variant_roadmap):
        '''
        Returns a list of libtypes for the variant type
        '''
        iptype = self.family.get_iptype(variant_type)
        # http://pg-rdconfluence:8090/pages/viewpage.action?pageId=4523862
        # Now we need to get the deliverables for the roadmap intersected with iptype
        libtypes = [x.deliverable for x in iptype.get_all_deliverables(roadmap=variant_roadmap)]

        return libtypes

    def get_missing_libtypes(self, variant_type_libtypes):
        '''
        Compares the current libtypes for project/variant against the
        variant_type_libtypes. Anthing that is missing is returned
        '''
        current_libtypes = self.cli.get_libtypes(self.project, self.variant)
        return [x for x in variant_type_libtypes if x not in current_libtypes]

    def add_libtypes_to_composite_config(self, libtypes):
        '''
        Updates the dev config at project/variant and ensures it is referencing
        all of the correct simple configs
        '''
        ret = False
        config_added = False

        ### Creating/Getting the variant-config
        if self.cli.config_exists(self.project, self.variant, self.defconfig):
            dev_cfg = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, self.defconfig, preview=self.preview)
        else:
            dev_cfg = dmx.abnrlib.icmconfig.IcmConfig(self.defconfig, self.project, self.variant, [], preview=self.preview)

        ### creating/getting the libtype-library
        for libtype in libtypes:
            if self.cli.library_exists(self.project, self.variant, libtype, self.defconfig):
                simple_cfg = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, self.defconfig, libtype, preview=self.preview)
                simple_cfg.save()
            else:
                simple_cfg = dmx.abnrlib.icmlibrary.IcmLibrary(self.project, self.variant, libtype, self.defconfig, preview=self.preview)

            if not simple_cfg in dev_cfg.configurations:
                self.logger.info('Adding {0} to {1}'.format(simple_cfg.get_full_name(), dev_cfg.get_full_name()))
                dev_cfg.add_configuration(simple_cfg)
                config_added = True

        if not config_added:
            self.logger.info('All configurations already present')
            ret = True
        else:
            ret = dev_cfg.save(shallow=True)

        return ret

    def remove_non_roadmap_libtypes_from_composite_configs(self, libtypes_to_remove):
        '''
        Removes all references libtypes not on the roadmap from all mutable
        composite configs
        '''
        failed_to_remove_config = False
        save_failed = False

        self.logger.info('Removing non-roadmap libtypes from mutable composite configurations')
        for config_name in self.cli.get_configs(self.project, self.variant):
            self.logger.debug('Checking {0} for simple configs to remove'.format(config_name))
            if not config_name.startswith(('REL', 'snap-', 'PREL', 'tnr-placeholder')):
                config = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, config_name, preview=self.preview)

                # Build the list of simple configs to remove
                simple_configs_to_remove = []
                for sub_config in config.configurations:
                    if not sub_config.is_config() and sub_config.libtype in libtypes_to_remove:
                        simple_configs_to_remove.append(sub_config)

                # Remove the simple configs
                for simple_config in simple_configs_to_remove:
                    self.logger.debug('Removing {0} from {1}'.format(simple_config.get_full_name(),
                                                                     config.get_full_name()))
                    if not config.remove_configuration(simple_config):
                        failed_to_remove_config = True

                # If there were any simple configs to remove we need to save
                if simple_configs_to_remove and not failed_to_remove_config:
                    if not config.save(shallow=True):
                        save_failed = True

        return not failed_to_remove_config and not save_failed

    def remove_non_roadmap_libtype_simple_configs(self, libtypes_to_remove):
        '''
        Attempts to remove all simple configurations associated with the libtypes
        in libtypes_to_remove
        Failure to delete is not fatal, as they could have been included in
        immutable configs and those it's not possible to remove them
        '''
        delete_error = False
        for libtype in libtypes_to_remove:
            self.logger.info('Removing simple config {0}/{1}:{2}'.format(self.project,
                                                                               self.variant,
                                                                               libtype))

            for config_name in self.cli.get_configs(self.project, self.variant, libtype=libtype):
                if not config_name.startswith(('REL', 'snap-')):
                    try:
                        self.cli.del_config(self.project, self.variant, config_name,
                                            libtype=libtype)
                    except dmx.abnrlib.icm.ICManageError:
                        self.logger.warn('Unable to remove {0}'.format(
                            format_configuration_name_for_printing(self.project, self.variant,
                                                                   config_name,
                                                                   libtype=libtype)))
                        delete_error = True
                        pass

        return not delete_error

    def add_missing_libtypes(self, libtypes):
        '''
        Adds the missing libtypes to the variant
        '''
        ret = False

        if self.cli.add_libtypes_to_variant(self.project, self.variant, libtypes):
            self.logger.warn("Duplicates detected when adding libtypes to the variant")
        else:
            ret = True
        return ret

    def get_missing_libraries(self, libtypes):
        '''
        Gets the list of libtypes that do not have a dev library
        '''
        libtypes_missing_dev = []

        for libtype in libtypes:
            if not self.cli.library_exists(self.project, self.variant, libtype, self.defconfig):
                libtypes_missing_dev.append(libtype)

        return libtypes_missing_dev

    def add_missing_libraries(self, libtypes):
        '''
        Adds the dev library to libtypes and creates the corresponding simple config
        '''
        ret = False

        if libtypes:
            if self.cli.add_libraries(self.project, self.variant, libtypes, library=self.defconfig):
                self.logger.warn("Duplicates detected when adding {} libraries to the new libtypes".format(self.defconfig))

            # http://pg-rdjira:8080/browse/DI-1287
            # For large data deliverable and IP is not excluded, create a dev NAA label that will be aligned to ICManage dev library
            for libtype in libtypes:
                delobj = self.iptype.get_deliverable(libtype)
                is_large = delobj.large
                large_excluded_ip = delobj.large_excluded_ip

                if is_large and self.variant not in large_excluded_ip:
                    self.naa.create_label(self.family.family, self.project, self.variant, libtype, self.defconfig)
        else:
            ret = True

        return ret

    def add_libtypes_if_needed(self, required_libtypes):
        '''
        Updates the libtypes in the variant if any are missing
        '''
        missing_libtypes = self.get_missing_libtypes(required_libtypes)
        if missing_libtypes:
            self.add_missing_libtypes(missing_libtypes)
        else:
            self.logger.info('All required libtypes already present')

    def add_dev_libraries_if_needed(self, required_libtypes):
        '''
        Adds a dev library and simple config for any libtypes that don't have them
        '''
        libtypes_missing_dev = self.get_missing_libraries(required_libtypes)
        if libtypes_missing_dev:
            self.add_missing_libraries(libtypes_missing_dev)
        else:
            self.logger.info('All dev libraries already present')

    def update_the_variant(self):
        '''
        Controls the process of updating the variant
        '''
        ret = False

        # Get current variant-type
        variant_type = self.get_variant_type()

        self.logger.debug("iptype: {}".format(variant_type))

        # Modify the variant-type if variant-type argument is specified and is different than the current variant-type
        if self.variant_type and (self.variant_type != variant_type):
            # Overwrite the variant type with the new variant-type
            variant_type = self.variant_type
            self.ip.set_iptype(variant_type)

        roadmap = os.getenv("DB_DEVICE", "")
        self.logger.debug("roadmap: {}".format(roadmap))

        roadmap_libtypes = self.get_variant_type_libtypes(variant_type, roadmap)
        self.logger.debug("Roadmap libtypes: {}".format(roadmap_libtypes))

        self.add_libtypes_if_needed(roadmap_libtypes)
        self.add_dev_libraries_if_needed(roadmap_libtypes)

        ret = self.add_libtypes_to_composite_config(roadmap_libtypes)

        libtypes_in_variant = self.cli.get_libtypes(self.project, self.variant)
        libtypes_to_remove = set(libtypes_in_variant) - set(roadmap_libtypes)
        if libtypes_to_remove:
            ret = self.remove_non_roadmap_libtypes_from_composite_configs(libtypes_to_remove)
            # Don't check the return here as there are legitimate reasons why
            # we may not be able to remove some simple configs
            # self.remove_non_roadmap_libtype_simple_configs(libtypes_to_remove)

        return ret

    def run(self):
        '''
        Entry point for running updatevariant
        '''
        ret = 1

        if self.update_the_variant():
            ret = 0
        else:
            ret = 1

        return ret
