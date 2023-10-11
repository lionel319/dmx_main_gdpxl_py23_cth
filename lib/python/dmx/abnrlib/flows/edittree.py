#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/edittree.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "abnr edittree"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''

import sys
import logging
import textwrap

from dmx.abnrlib.icm import ICManageCLI
#from dmx.abnrlib.icmsimpleconfig import SimpleConfig
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.command import Command, Runner
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.utillib.utils import split_pv, split_pvc, split_pvl, split_pvlc, split_pvll, add_common_args, get_all_default_dev_configs
from dmx.utillib.arcenv import ARCEnv

class EditTreeError(Exception): pass

class EditTree(object):
    '''
    Actually runs abnr edittree
    Operate on libraries code is removed due to no longer being allowed
    '''

    def __init__(self, project, variant, config, inplace=False, new_config='',
                 show_tree=False, add_configs=None, del_configs=None, rep_configs=None,
                 add_libtype=None, del_libtype=None, rep_libtype=None,
                 include_libtypes=None, exclude_libtypes=None, preview=False):
        self.project = project
        self.variant = variant
        self.config = config
        self.inplace = inplace
        self.new_config = new_config
        self.show_tree = show_tree
        self.add_configs = add_configs
        self.del_configs = del_configs
        self.rep_configs = rep_configs
        self.add_libtype = add_libtype
        self.del_libtype = del_libtype
        self.rep_libtype = rep_libtype
        self.include_libtypes = include_libtypes
        self.exclude_libtypes = exclude_libtypes
        self.default_dev_config_list = get_all_default_dev_configs()

        self.preview = preview
        self.logger = logging.getLogger(__name__)
        self.cli = ICManageCLI(preview=True)

        if not self.inplace and not self.new_config:
            raise EditTreeError('You must specify one of --inplace or --newbom')

        if self.new_config and self.new_config.startswith(('snap-', 'REL', 'PREL')):
            raise EditTreeError('--newbom cannot be an immutable config name (RELxxx or snap-xxx or PRELxxx)')

        if self.config.startswith(('snap-', 'REL', 'PREL')) and not self.new_config:
            raise EditTreeError('You cannot modify an immutable configuration inplace. Please use the --newbom option')

        # https://jira.devtools.intel.com/browse/PSGDMX-2962
        if (self.inplace and self.config in self.default_dev_config_list) or self.new_config in self.default_dev_config_list:
            raise EditTreeError("You are not allowed to modify any default dev configs: {}".format(self.default_dev_config_list))

        if (not self.add_configs and not self.del_configs and not self.rep_configs 
                and not self.add_libtype and not self.del_libtype and not self.rep_libtype 
                and not self.include_libtypes and not self.exclude_libtypes):
            raise EditTreeError('You must specify an action to perform')

        # Check for command arguments consistency
        if self.add_configs:
            for pvc, parent in self.add_configs:
                try:
                    p, v, c = split_pvc(pvc)
                except:
                    raise EditTreeError('{} is not in a valid project/variant@config format.'.format(pvc))
                if not self.cli.config_exists(p, v, c):
                    raise EditTreeError('{}/{}@{} doesn\'t exist. Did you give the correct project/variant@config?'.format(p, v, c))
                try:
                    p, v = split_pv(parent)                     
                except:
                    raise EditTreeError('{} is not in a valid project/variant format.'.format(parent)) 
                if not self.cli.variant_exists(p, v):
                    raise EditTreeError('{}/{} doesn\'t exist. Did you give the correct project/variant?'.format(p, v))

        if self.del_configs:
            for pv_pair in self.del_configs:
                if len(pv_pair) == 2:
                    child, parent = pv_pair
                    try:
                        p, v = split_pv(parent)
                    except:
                        raise EditTreeError('{} is not in a valid project/variant format.'.format(parent))  
                    if not self.cli.variant_exists(p, v):
                        raise EditTreeError('{}/{} doesn\'t exist. Did you give the correct project/variant?'.format(p, v))                        
                    try:
                        p, v = split_pv(child)
                    except:
                        raise EditTreeError('{} is not in a valid project/variant format.'.format(child))
                    if not self.cli.variant_exists(p, v):
                        raise EditTreeError('{}/{} doesn\'t exist. Did you give the correct project/variant?'.format(p, v))                        
                else: 
                    child = pv_pair[0]                    
                    try:
                        p, v = split_pv(child)
                    except:
                        raise EditTreeError('{} is not in a valid project/variant format.'.format(child))
                    if not self.cli.variant_exists(p, v):
                        raise EditTreeError('{}/{} doesn\'t exist. Did you give the correct project/variant?'.format(p, v))    
                                                                    
        if self.rep_configs:
            for pv, c in self.rep_configs:
                try:
                    p, v = split_pv(pv)
                except:
                    raise EditTreeError('{} is not in a valid project/variant format.'.format(pv)) 
                if not self.cli.config_exists(p, v, c):
                    raise EditTreeError('{}/{}@{} doesn\'t exist. Did you give the correct project/variant config?'.format(p, v, c))
                    
        if self.add_libtype:
            for (pvlc,) in self.add_libtype:
                try:
                    p, v, l, c = split_pvlc(pvlc)
                except:
                    raise EditTreeError('{} is not in a valid project/variant:libtype@config format.'.format(pvlc))
                if not self.cli.config_exists(p, v, c, libtype=l):
                    raise EditTreeError('{}/{}:{}@{} doesn\'t exist. Did you give the correct project/variant:libtype@config?'.format(p, v, l, c))
                     
        if self.del_libtype:                            
            for pvl in self.del_libtype:
                try:
                    p, v, l = split_pvl(pvl[0])
                except:
                    raise EditTreeError('{} is not in a valid project/variant:libtype format.'.format(pvl[0]))
                if not self.cli.libtype_exists(p, v, libtype=l):
                    raise EditTreeError('{}/{}:{} doesn\'t exist. Did you give the correct project/variant:libtype?'.format(p, v, l))
                    
        if self.rep_libtype:                            
            for (pvl,c) in self.rep_libtype:
                try:
                    p, v, l = split_pvl(pvl)
                except:
                    raise EditTreeError('{} is not in a valid project/variant:libtype format.'.format(pvl)) 
                if not self.cli.config_exists(p, v, c, libtype=l):
                    raise EditTreeError('{}/{}:{}@{} doesn\'t exist. Did you give the correct project/variant:libtype config?'.format(p, v, l, c))

                        
        self.logger.info('Building input configuration tree')
        # If project not given, get project from IP
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise EditTreeError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
            if not self.cli.project_exists(self.project):
                raise EditTreeError("{0} does not exist".format(self.project))
            if not self.cli.variant_exists(self.project, self.variant):
                raise EditTreeError("{0}/{1} does not exist".format(self.project, self.variant))
        self.source_config = ConfigFactory.create_from_icm(self.project, self.variant,
                                                           self.config, preview=self.preview)

        # Keep track of which configs have been modified in some way,
        # either through replacing sub-configs, adding sub-configs or
        # deleting sub-configs
        self.modified_configs = []

    def delete_icm_configs(self):
        '''
        Deletes all icm configurations in self.del_configs
        :return: True on success, False on failure
        :type return: bool
        '''
        ret = True
        self.logger.info('Processing configurations to remove')

        for del_details in self.del_configs:
            # Each argument can be in one of two formats
            # It's either project/variant where all icm configs within
            # project/variant are deleted
            # Or:
            # project/variant parent_project/parent_variant
            # Where the icm configs for project/variant are only
            # deleted from within parent_project/parent_variant
            parent_pv_pairs = [x.split('/') for x in del_details[1:]]
            project, variant = split_pv(del_details[0])

            msg = 'Removing {0}/{1} configurations'.format(project, variant)
            if parent_pv_pairs:
                msg += ' from {0}'.format(' '.join([z for x in parent_pv_pairs for z in x]))

            self.logger.info(msg)

            if parent_pv_pairs:
                ret = self.delete_project_variant_from_parent(parent_pv_pairs, project, variant)
            else:
                ret = self.delete_project_variant(project, variant)

        return ret

    def delete_project_variant_from_parent(self, parent_pv_pairs, del_project, del_variant):
        '''
        Deletes all instances of del_project/del_variant@any_config from
        the parents specified in parent_pv_pairs
        :param parent_pv_pairs: List of parent project/variant pairs
        :type parent_project: list
        :param del_project: The config to be deleted IC Manage project
        :type del_project: str
        :param del_variant: The config to be deleted IC Manage variant
        :type del_variant: str
        :return: True on success, False on failure
        :type return: bool
        '''
        ret = True
        potential_configs_to_remove = set(self.source_config.search(project=del_project,
                                                                    variant='^{}$'.format(del_variant),
                                                                    libtype=None))
        
        if not potential_configs_to_remove:
            raise EditTreeError('{}/{} doesn\'t exist in {}.'.format(del_project, del_variant, self.source_config))

        for del_config in potential_configs_to_remove:
            for parent_project, parent_variant in parent_pv_pairs:
                parents_to_remove_del_config_from = [x for x in del_config.parents if x.project == parent_project and x.variant == parent_variant]
                for parent in parents_to_remove_del_config_from:
                    self.logger.info('Removing {0} from {1}'.format(
                        del_config.get_full_name(), parent.get_full_name()
                    ))
                    if not parent.remove_configuration(del_config):
                        ret = False
                        self.logger.error('Problem removing {0} from {1}'.format(
                            del_config.get_full_name(), parent.get_full_name()
                        ))
                        break

                    if self.new_config and not self.inplace:
                        self.modified_configs.append(parent)
                        self.modified_configs += parent.get_configs_to_clone_if_self_changes_including_mutable()
                    else:                        
                        if not parent.is_mutable():
                            self.modified_configs.append(parent)
                            self.modified_configs += parent.get_configs_to_clone_if_self_changes()

        return ret

    def delete_project_variant(self, del_project, del_variant):
        '''
        Deletes all instances of del_project/del_variant@any_config
        from the tree, regardless of the instance's parent
        :param del_project: The config(s) to be deleted IC Manage project
        :type del_project: str
        :param del_variant: The config(s) to be deleted IC Manage variant
        :type del_variant: str
        :return: True on success, False on failure
        :type return: bool
        '''
        ret = True

        configs_to_remove = [x for x in self.source_config.flatten_tree() if x.is_config()
            and x.variant == del_variant and x.project == del_project]

        if not configs_to_remove:
            raise EditTreeError('{}/{} doesn\'t exist in {}.'.format(del_project, del_variant, self.source_config))

        for del_config in configs_to_remove:
            for parent in del_config.parents:
                if self.new_config and not self.inplace:
                    self.modified_configs.append(parent)
                    self.modified_configs += parent.get_configs_to_clone_if_self_changes_including_mutable()
                else:                        
                    if not parent.is_mutable():
                        self.modified_configs.append(parent)
                        self.modified_configs += parent.get_configs_to_clone_if_self_changes()

            self.logger.info('Removing {0} from {1}'.format(
                del_config.get_full_name(), ' '.join([x.get_full_name() for x in del_config.parents])
            ))
            self.source_config.remove_object_from_tree(del_config)

        return ret

    def delete_libtype_configs(self):
        '''
        Deletes all libtype configs in self.del_libtype
        :return: True on success, False on failure
        :type return: bool
        '''
        ret = True
        self.logger.info('Processing libtype configurations to remove')

        for (name,) in self.del_libtype:
            (del_project, del_variant, del_libtype) = split_pvl(name)
            configs_to_delete = [x for x in self.source_config.flatten_tree() if x.is_library()
                and x.project == del_project and x.variant == del_variant and x.libtype == del_libtype]
            if not configs_to_delete:
                raise EditTreeError('{} not found in {} configuration tree.'.format(name, self.source_config))
            for config_to_delete in configs_to_delete:
                for parent in config_to_delete.parents:
                    if self.new_config and not self.inplace:
                        self.modified_configs.append(parent)
                        self.modified_configs += parent.get_configs_to_clone_if_self_changes_including_mutable()
                    else:                        
                        if not parent.is_mutable():
                            self.modified_configs.append(parent)
                            self.modified_configs += parent.get_configs_to_clone_if_self_changes()

                self.logger.info('Removing {0} from {1}'.format(
                    config_to_delete.get_full_name(), ' '.join([x.get_full_name() for x in config_to_delete.parents])))
                self.source_config.remove_object_from_tree(config_to_delete)

        return ret

    def delete_excluded_libtypes(self):
        '''
        Deletes all libtypes in exclude_libtypes (simple configuration) from configuration tree
        :return: True on success, False on failure
        :type return: bool
        '''
        ret = True
        self.logger.info('Processing simple configurations (exclude-libtypes) to remove')
        libtypes = self.exclude_libtypes[0]

        for libtype in libtypes:
            configs_to_delete = [x for x in self.source_config.flatten_tree() if x.is_library()
                and x.libtype == libtype]
            if not configs_to_delete:
                raise EditTreeError('{} not found in {} configuration tree.'.format(libtype, self.source_config))
            for config_to_delete in configs_to_delete:
                for parent in config_to_delete.parents:
                    if self.new_config and not self.inplace:
                        self.modified_configs.append(parent)
                        self.modified_configs += parent.get_configs_to_clone_if_self_changes_including_mutable()
                    else:                        
                        if not parent.is_mutable():
                            self.modified_configs.append(parent)
                            self.modified_configs += parent.get_configs_to_clone_if_self_changes()
                
                self.logger.info('Removing {0} from {1}'.format(
                    config_to_delete.get_full_name(), ' '.join([x.get_full_name() for x in config_to_delete.parents])))
                self.source_config.remove_object_from_tree(config_to_delete)
 
        return ret

    def delete_all_except_included_libtypes(self):
        '''
        Opposite of exclude_libtypes, edittree removes all libtypes from configuration ttee not 
        listed in include_libtypes
        :return: True on success, False on failure
        :type return: bool
        '''
        ret = True
        self.logger.info('Processing simple configurations (include-libtypes) to remove')
        libtypes = self.include_libtypes[0]
        configs_to_delete = [x for x in self.source_config.flatten_tree() if x.is_library()
            and x.libtype not in libtypes]

        if not configs_to_delete:
            raise EditTreeError('{} not found in {} configuration tree.'.format(libtypes, self.source_config))
        for config_to_delete in configs_to_delete:
            for parent in config_to_delete.parents:
                if self.new_config and not self.inplace:
                    self.modified_configs.append(parent)
                    self.modified_configs += parent.get_configs_to_clone_if_self_changes_including_mutable()
                else:                        
                    if not parent.is_mutable():
                        self.modified_configs.append(parent)
                        self.modified_configs += parent.get_configs_to_clone_if_self_changes()

            self.logger.info('Removing {0} from {1}'.format(
                config_to_delete.get_full_name(), ' '.join([x.get_full_name() for x in config_to_delete.parents])))
            self.source_config.remove_object_from_tree(config_to_delete)
 
        return ret


    def add_icm_configs(self):
        '''
        Adds all icm configurations in self.add_configs
        :return: True on success, False on failure
        :type return: bool
        '''
        ret = True
        self.logger.info('Processing new icm configurations')
        self.logger.debug('self.add_configs: {}'.format(self.add_configs))

        for full_config_name, target_tree_location in self.add_configs:
            target_project, target_variant = split_pv(target_tree_location)
            config = ConfigFactory.create_config_from_full_name(full_config_name)

            # Make sure it's icm config 
            if not config.is_config():
                raise EditTreeError('Tried to add {0} but it is not an icm config'.format(
                    config.get_full_name()
                ))

            # Keep track of which configs we're adding to
            configs_added_to = self.source_config.search(project=target_project,
                                                         variant='^{}$'.format(target_variant),
                                                         libtype=None)
            
            if not configs_added_to:
                raise EditTreeError('{} doesn\'t exist in {} configuration tree.'.format(
                    target_tree_location,
                    self.source_config))
           
            ### configs_added_to might have multiple similar obj if the variant-config appears more than once in the entire tree.
            ### thus, we need to uniqify it.
            configs_added_to = list(set(configs_added_to))

            for target_config in configs_added_to:
                self.logger.info('Adding {0} to {1}'.format(config.get_full_name(),
                                                            target_config.get_full_name()))
                target_config.add_configuration(config)
                if self.new_config and not self.inplace:
                    self.modified_configs.append(target_config)
                    self.modified_configs += target_config.get_configs_to_clone_if_self_changes_including_mutable()
                else:                        
                    if not target_config.is_mutable():
                        self.modified_configs.append(target_config)
                        self.modified_configs += target_config.get_configs_to_clone_if_self_changes()
        return ret                    

    def add_libtype_configs(self):
        '''
        Adds libtype configs to all appropriate icm configurations
        in the tree
        :return: True on success, False on failure
        :type return: bool
        '''
        ret = True
        self.logger.info('Processing new libtype configurations')

        for (name,) in self.add_libtype:
            (project, variant, libtype, config) = split_pvlc(name)
            new_simple = ConfigFactory.create_from_icm(project, variant, config,
                                                       libtype=libtype)

            configs_added_to = set(self.source_config.search(project=project, 
                                                              variant='^{}$'.format(variant),
                                                              libtype=None))

            if not configs_added_to:
                raise EditTreeError('{}/{} doesn\'t exist in {} configuration tree.'.format(
                    project,
                    variant,
                    self.source_config))

            for comp_config in configs_added_to:
                # Capture the modified configs if they're immutable
                if self.new_config and not self.inplace:
                    self.modified_configs.append(comp_config)
                    self.modified_configs += comp_config.get_configs_to_clone_if_self_changes_including_mutable()
                else:                        
                    if not comp_config.is_mutable():
                        self.modified_configs.append(comp_config)
                        self.modified_configs += comp_config.get_configs_to_clone_if_self_changes()

                # Add the simple config
                self.logger.debug('Adding {0} to {1}'.format(new_simple.get_full_name(),
                                                             comp_config.get_full_name()))
                comp_config.add_configuration(new_simple)

        return ret

    def replace_icm_configs(self):
        '''
        Replaces all icm configurations in self.rep_configs
        :return: True on success, False on failure
        :type return: bool
        '''
        ret = True

        self.logger.info('Processing icm configuration replacements')

        # Build a dict of the new configurations coming in
        new_configs = dict()
        for pv, new_config in self.rep_configs:
            (project, variant) = split_pv(pv)
            new_configs[(project, variant)] = ConfigFactory.create_from_icm(
                project, variant, new_config, preview=self.preview)

        # Now we need to figure out which configurations to replace
        # We need this information at the start as it might start changing
        # as we start replacing configs
        to_be_replaced = dict()
        for key in new_configs.keys():
            project, variant = key
            configs_to_replace = set(self.source_config.search(project=project, 
                                                               variant='^{}$'.format(variant),
                                                               libtype=None))
            if configs_to_replace:
                to_be_replaced[key] = configs_to_replace

        if not to_be_replaced:
            raise EditTreeError('No configuration to be replaced found.')

        configs_to_be_replaced = []
        for key in to_be_replaced.keys():
            for config in to_be_replaced[key]:                
                depths = self.get_config_depth_in_source_config_tree(config)
                max_depth = max(depths)
                if [max_depth, config] not in configs_to_be_replaced:
                    configs_to_be_replaced.append([max_depth, key, config])                                                    
        # Now replace the configurations
        for depth, key, rep_config in sorted(configs_to_be_replaced):            
            current_configs = list(set(self.source_config.search(project=rep_config.project, 

                                                            variant='^{}$'.format(rep_config.variant),
                                                            libtype=None)))
            # Add all configs that would need to be updated by swapping out original
            for current_config in current_configs:
                # If configs are the same, there is no need to perform replacement
                if current_config.get_full_name() == new_configs[key].get_full_name():
                    continue
                for parent in current_config.parents:
                    # Check if parent is in source config
                    if self.source_config.search(project=parent.project, 
                                                 variant='^{}$'.format(parent.variant),
                                                 libtype=None):
                        if self.new_config and not self.inplace:
                            self.modified_configs.append(parent)                        
                            self.modified_configs += parent.get_configs_to_clone_if_self_changes_including_mutable()                        
                        else:                        
                            if not parent.is_mutable():
                                self.modified_configs.append(parent)
                                self.modified_configs += parent.get_configs_to_clone_if_self_changes()
                self.logger.info('Replacing {0} with {1} from {2}'.format(current_config.get_full_name(),
                                                                 new_configs[key].get_full_name(),
                                                                 [x.get_full_name() for x in current_config.parents]))
                self.logger.debug('List of modified_configs: {}'.format(self.modified_configs))

                project, variant = key
                self.source_config.replace_object_in_tree(current_config, new_configs[key])

        return ret
        
    def replace_libtype_configs(self):
        '''
        Replaces all libtype configs in self.rep_libtype
        :return: True on success, False on failure
        :type: bool
        '''
        ret = True

        self.logger.info('Processing libtype configuration replacements')

        # Build a dict of the new configurations coming in
        new_configs = dict()
        for pvl, new_config in self.rep_libtype:
            (project, variant, libtype) = split_pvl(pvl)
            new_configs[(project, variant, libtype)] = ConfigFactory.create_from_icm(
                project, variant, new_config, libtype=libtype,
                preview=self.preview)

        # Now we need to figure out which configurations to replace
        # We need this information at the start as it might start changing
        # as we start replacing configs
        to_be_replaced = dict()
        for key in new_configs.keys():
            project, variant, libtype = key
            configs_to_replace = set(self.source_config.search(project=project, 
                                                               variant='^{0}$'.format(variant),
                                                               libtype='^{0}$'.format(libtype)))
            if configs_to_replace:
                to_be_replaced[key] = configs_to_replace
        
        if not to_be_replaced:
            raise EditTreeError('No configuration to be replaced found.')

        # Now replace the configurations
        for key in to_be_replaced.keys():
            for original_config in to_be_replaced[key]:
                for parent in original_config.parents:
                    if self.new_config and not self.inplace:
                        self.modified_configs.append(parent)
                        self.modified_configs += parent.get_configs_to_clone_if_self_changes_including_mutable()
                    else:                        
                        if not parent.is_mutable():
                            # Add all configs that would need to be updated by swapping out original
                            self.modified_configs.append(parent)
                            self.modified_configs += parent.get_configs_to_clone_if_self_changes()

                self.logger.info('Replacing {0} with {1} from {2}'.format(original_config.get_full_name(),
                    new_configs[key].get_full_name(),
                    [x.get_full_name() for x in original_config.parents]))
                if not self.source_config.replace_object_in_tree(original_config, new_configs[key]):
                    ret = False
                    self.logger.warn('Nothing replaced!')

        return ret

    def get_config_depth_in_source_config_tree(self, config_to_look):
        configurations = [x for x in self.source_config.configurations if x.is_config()]
        depths = []

        def find_depth(config_to_look, configurations, depths, depth=1):
            for config in configurations:
                if config_to_look in configurations:
                    depths.append(depth)
                else:
                    next_configurations = [x for x in config.configurations if x.is_config()]
                    depths = find_depth(config_to_look, next_configurations, depths, depth=depth+1)
            return depths                    
        depths = find_depth(config_to_look, configurations, depths)

        return depths

    def update_modified_config_tree(self):
        '''
        Clones all immutable configs that have been modified in some way, or
        will have to be modified in some way, into self.new_config
        '''
        ret = 0
        if self.new_config:
            for config_to_clone in list(set(self.modified_configs)):
                clone = config_to_clone.clone(self.new_config)
                self.source_config.replace_object_in_tree(config_to_clone, clone)
        else:
            error_msg = 'Attempting to replace the child of an immutable configuration in place.'
            error_msg += '\nYou must use the --newbom option to do this.'
            raise EditTreeError(error_msg)
        return ret

    def operate_on_icm_configs(self):
        '''
        Performs operations on icm configs:
        Add, delete and replace
        :return: Zero on success, non-zero on failure
        :type return: int
        '''
        ret = 0

        if self.del_configs:
            if not self.delete_icm_configs():
                ret = 1

        if self.add_configs:
            if not self.add_icm_configs():
                ret = 1

        if self.rep_configs:
            if not self.replace_icm_configs():
                ret = 1

        return ret

    def operate_on_simple_configs(self):
        '''
        Performs operations on simple configs:
        Add, delete, replace, include filter and exclude filter
        :return: Zero on success, non-zero on failure
        :type return: int
        '''
        ret = 0

        if self.del_libtype:
            if not self.delete_libtype_configs():
                ret = 1

        if self.add_libtype:
            if not self.add_libtype_configs():
                ret = 1

        if self.rep_libtype:
            if not self.replace_libtype_configs():
                ret = 1
        
        if self.exclude_libtypes:
            if not self.delete_excluded_libtypes():
                ret = 1
              
        if self.include_libtypes:
            if not self.delete_all_except_included_libtypes():
                ret = 1
                           
        return ret
    
    def run(self):
        '''
        Runs edittree
        :return: Zero on success, non-zero on failure
        :type return: int
        '''
        ret = 1

        ret = self.operate_on_icm_configs()

        if ret == 0:
            ret = self.operate_on_simple_configs()
       
        if ret == 0 and self.modified_configs:
            ret = self.update_modified_config_tree()

        if ret == 0:
            self.source_config.remove_empty_configs()

        errors = []
        if self.new_config and not self.inplace:
            new_tree = self.source_config.clone(self.new_config)
        elif not self.new_config and self.inplace:
            new_tree = self.source_config
        elif self.new_config and self.inplace:
            if not self.source_config.is_mutable():
                new_tree = self.source_config.clone(self.new_config)
            else:
                new_tree = self.source_config
        errors = new_tree.validate()

        if self.show_tree:
            print(new_tree.report(show_simple=False))
            
        if errors:
            for error in errors:
                self.logger.error(error)
            raise EditTreeError('Problems detected when validating new configuration tree')
        else:                                
            if not self.preview:
                new_tree.save()

        return ret
