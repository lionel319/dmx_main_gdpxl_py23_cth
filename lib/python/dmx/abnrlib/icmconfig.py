#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/icmconfig.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Concrete implementation of the abstract base class ICMConfig for use with composite configs
See: http://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/ICMConfigurationClass for more details

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''

## @addtogroup dmxlib
## @{

from builtins import object
import logging
import getpass
from datetime import datetime
import re
from pprint import pprint, pformat

from dmx.abnrlib.icm import ICManageCLI, ICManageError
from dmx.abnrlib.icmlibrary import IcmLibrary, IcmLibraryError
from dmx.utillib.utils import format_configuration_name_for_printing
from dmx.abnrlib.namevalidator import ICMName
import dmx.abnrlib.config_factory

class IcmConfigError(Exception):
    pass

class IcmConfig(object):
       
    ### These are the default properties created by icm (no user created)
    DEFAULT_PROP_KEYS = ['location', 'uri', 'created-by', 'id', 'type', 'name', 'path', 'created', 'modified', 'change', 'libtype']
    
    def __init__(self, config='', project='', variant='', objects='', description='', preview=False, parents=None, use_db=True, defprop_from_icm=None):
        '''
        objects: can be either IcmLibrary()/IcmConfig() objects
        defprop_from_icm:   This is used to create the library/release object by providing the json output from 'gdp list'
                            At times, we already have the details, and thus, we do not want to incur additional cost by hitting the server for queries.
                            This is the purpose of introducing this param.
        When defprop_from_icm is provided, no other input params is required, except objects.
        Else, project, variant, config are compulsory inputs.

        '''
        self.__logger = logging.getLogger(__name__)
        self._preview = preview
        self._icm = ICManageCLI(preview=preview)
      
        self._type = 'config'

        if defprop_from_icm:
            data = self._icm.decompose_gdp_path(defprop_from_icm['path'], 'config')
            self._project = data['project']
            self._variant = data['variant']
            self._config = data['config']
            self._description = ''
            self._defprops = defprop_from_icm
            ### Since this info is coming from 'gdp list', we assume(and expect) that 
            ### this object data is already saved, and already in icm db
            self._in_db = True
            self._saved = True
        else:
            self._config = config
            self._project = project
            self._variant = variant
            self._description = description
            self._defprops = {} # These are all the default properties returned by icm (system + user created properties)

            self._in_db = False 
            self._saved = False

            if use_db:
                try:
                    self._defprops = self._icm.get_config_details(project, variant, config)
                except:
                    self._defprops = {}
                if self._defprops:
                    # Meaning object already exists in database
                    self._in_db = True
                    self._saved = True
            else:
                # Assume it is in the database
                self._in_db = False
                self._saved = False
            
        self._configurations = set(objects)

        # Set properties to None as we lazy load them
        self._properties = None

        # Set properties dependent on whether we're in the db or not
        if self._in_db:
            # Keep a copy of the saved configuration list to help us construct
            # the pm command for saving
            # This list should be blank if we're not in the db so that all changes are
            # made to the database
            self._saved_configurations = list(self.configurations)
            
            # Set the properties to None as we lazy load them
            self._properties = None
            if self._defprops:
                self._properties = self.get_user_properties()
        else:
            self._saved_configurations = []
            # Not in db = no properties
            self._properties = {}

        # Flag to show if the properties have been updated at all
        # Using this means we only hit the IC Manage database for
        # properties when we have to, which is good for performance
        self._properties_changed = False

        if parents is None:
            self._parents = set()
        else:
            self._parents = set(parents)
        
        # Make sure all sub configurations have this instance as a parent
        for obj in self.configurations:
            obj.add_parent(self)

    @property
    def name(self):
        return self._config

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, new_config):
        self._config = new_config
        self._saved = False
        self._in_db = self._icm.config_exists(self.project, self.variant, self.config)

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, new_project):
        self._project = new_project
        self._saved = False
        self._in_db = self._icm.config_exists(self.project, self.variant, self.config)

    @property
    def variant(self):
        return self._variant

    @variant.setter
    def variant(self, new_variant):
        self._variant = new_variant
        self._saved = False
        self._in_db = self._icm.config_exists(self.project, self.variant, self.config)

    @property
    def properties(self):
        if self._properties is None:
            self._properties = self._icm.get_config_properties(self.project, self.variant, self.config)
        return self._properties

    @properties.setter
    def properties(self, new_properties):
        self._properties = new_properties
        self._saved = False
        self._properties_changed = True

    def add_property(self, key, value):
        self.properties[key] = value
        self._saved = False
        self._properties_changed = True

    def remove_property(self, key):
        if key in self.properties:
            del self.properties[key]
            self._saved = False
            self._properties_changed = True

    @property
    def configurations(self):
        return self._configurations

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, new_description):
        self._description = new_description
        self._saved = False

    @property
    def preview(self):
        return self._preview

    @preview.setter
    def preview(self, new_preview):
        self._preview = new_preview
        self._icm.preview = new_preview
        for sub_config in self.configurations:
            sub_config.preview = new_preview

    @property
    def parents(self):
        return self._parents

    def is_library(self):
        return False
    
    def is_release(self):
        return False

    def is_config(self):
        return True

    def get_user_properties(self):
        ret = {}
        for key in self._defprops:
            if key not in self.DEFAULT_PROP_KEYS:
                ret[key] = self._defprops[key]
        return ret

    def add_configuration(self, obj):
        ''' obj: either a IcmLibrary()/IcmConfig() object '''
        if not isinstance(obj, IcmConfig) and not isinstance(obj, IcmLibrary):
            raise IcmConfigError("Tried to add a config of incorrect type")
        elif obj in self.configurations:
            self.__logger.warning('IcmConfig.add_configuration: {0} is already in {1}'.format(obj.get_full_name(), self.get_full_name()))

        # We need to make sure there aren't clashes with other
        # configs using that location
        new_location = obj.location_key()
        for config in self.configurations:
            if config.location_key() == new_location:
                raise IcmConfigError('IcmConfig.add_configuration:{0} clashes with an existing config in {1}'.format(obj.get_full_name(), self.get_full_name()))

        # Make sure that library/release are local to this composite
        if (obj.is_library() or obj.is_release()) and self.is_foreign(obj):
            raise IcmConfigError("Tried to add IcmLibrary() object that is an external reference:{0}".format(obj.get_full_name()))

        self.configurations.add(obj)
        # Update the new child's parents too
        obj.add_parent(self)
        self._saved = False
    # The correct name should be add_object() instead of add_configuration(),
    # but we keep the old naming due to backward compatibility
    add_object = add_configuration

    def remove_configuration(self, obj):
        ret = False
        try:
            self.configurations.remove(obj)
            obj.remove_parent(self)
            ret = True
        except KeyError:
            # This means obj wasn't in configurations
            ret = False
        if ret:
            self._saved = False
        return ret
    # The correct name should be remove_object() instead of remove_configuration(),
    # but we keep the old naming due to backward compatibility
    remove_object = remove_configuration

    def add_parent(self, new_parent):
        if not new_parent.is_config():
            raise CompositeConfigError('Tried to add non-config object:{0} as a parent of {1}'.format(new_parent.get_full_name(), self.get_full_name()))
        if self not in new_parent.configurations:
            error_msg = 'Problem adding {0} as parent of {1}'.format(new_parent.get_full_name(), self.get_full_name())
            error_msg += '\n{0} is not a child of {1}'.format(self.get_full_name(), new_parent.get_full_name())
            raise CompositeConfigError(error_msg)
        self._parents.add(new_parent)

    def remove_parent(self, parent):
        try:
            self._parents.remove(parent)
        except KeyError:
            self.__logger.debug("Tried to remove {0} from list of parents for {1} but it wasn't in the list".format(parent.get_full_name(), self.get_full_name()))

    def clone(self, name, skip_existence_check=False):
        '''
        Create a clone of the configuration called name.
        Does not save it to IC Manage.

        skip_existence_check
        --------------------
        Before cloning, we need to make sure the destination object does not exist in icm.
        However, doing this for a clone_tree() which needs to clone 1000+ of objects means that it needs to hit
        the server for this query. So, we does that existence_check at clone_tree() level, with just a single 
        command call (check out the code in clone_tree() for details), and thus, we can set 'skip_existence_check=True'
        here.
        '''
        ######################################
        ### === Note: ===
        ### All IcmConfig() object creation uses use_db=False because we already know that the object
        ### does not exists in the db. Thus, we do not want it to hit the server for self.get_library/release_details() 
        ### (see __init_ for details)
        ### Also, we need to set _in_db and _saved to false so that when save() is called, the object will be created.
        ######################################

        if not skip_existence_check and self._icm.config_exists(self.project, self.variant, name):
            raise IcmConfigError("Cannot clone to {0}/{1}@{2} - it already exists".format(self.project, self.variant, name))
        self.__logger.info("Cloning {0} into {1}/{2}@{3}".format(self.get_full_name(), self.project, self.variant, name))
        ret = IcmConfig(name, self.project, self.variant, self.configurations, preview=self.preview, use_db=False)
        ### Set properties in correct state
        ret._in_db = False
        ret._saved = False
        return ret

    def delete(self, shallow=True):
        ''' DEPRECATED: We do not allow deletion of config. '''
        raise IcmConfigError("Deletiong of config is prohibited.")

    def get_full_name(self, legacy_format=False):
        path = '{}/{}/{}'.format(self.project, self.variant, self.config)
        if legacy_format:
            path = '{}/{}@{}'.format(self.project, self.variant, self.config)
        return path
    get_path = get_full_name

    def in_db(self, shallow=True):
        '''
        Returns True if the configuration exists in the IC Manage database in some form
        Otherwise returns False
        If shallow=True will run in_db against entire tree

        :param shallow: Boolean indicating whether or not the check should be performed only at this level or the entire tree
        :type shallow: bool
        :return: Boolean indicating whether or not the config(s) are in the IC Manage database
        :rtype: bool
        '''
        ret = self._in_db
        if ret and not shallow:
            ret = self.__apply_to_tree('in_db', shallow=shallow)
        return ret

    def is_mutable(self, shallow=True):
        '''
        Returns True if the configuration is mutable.
        Otherwise returns False
        If shallow=True will test the entire tree

        :param shallow: Boolean indicating whether to check just this config or the entire tree
        :type shallow: bool
        :return: Boolean indicating whether or not the config(s) are mutable
        :rtype: bool
        '''
        ret = not self.config.startswith(('REL', 'snap-', 'PREL'))
        if ret and not shallow:
            ret = self.__apply_to_tree('is_mutable', shallow=shallow)

        return ret

    def is_released(self, shallow=False):
        '''
        Returns True if the configuration is a REL configuration
        If shallow=False will descend the entire tree and return
        True only if all configs are released

        :param shallow: Boolean indicating whether to check just this config or the entire tree
        :type shallow: bool
        :return: Boolean indicating if the config(s) are REL configs
        :rtype: bool
        '''
        ret = self.config.startswith('REL')
        if ret and not shallow:
            ret = self.__apply_to_tree('is_released', shallow=shallow)

        return ret

    def is_preleased(self, shallow=False, strict=False):
        '''
        Returns True if the configuration is a PREL configuration
        If shallow=False will descend the entire tree and return
        True only if all configs are released.

        This is a very unique case. PREL is a subset of REL, and thus, a REL should be treated as PREL too.
        By right, I believe that when is_preleased() is called, it should be returning `true` if it is either REL/PREL.
        I could not think of any use case where it needs to return `false`.
        However, in order to have that option, the `strict` parameter is introduced here.
        If there is any possibility that a user strictly would only want this method to return `true` if only the entire tree is PREL,
        then this param needs to be set to strict=true.

        :param shallow: Boolean indicating whether to check just this config or the entire tree
        :type shallow: bool
        :return: Boolean indicating if the config(s) are PREL configs
        :rtype: bool
        '''
        if strict:
            rel = ("PREL")
        else:
            rel = ("REL", "PREL")
        ret = self.config.startswith(rel)
        if ret and not shallow:
            ret = self.__apply_to_tree('is_preleased', shallow=shallow, strict=strict)

        return ret

    def is_saved(self, shallow=True):
        '''
        Returns True if there are no outstanding changes to commit to the IC Manage database
        Otherwise returns False 
        If shallow=True calles is+saved on the entire tree

        :param shallow: Boolean indicating whether to check just this config or the entire tree
        :type shallow: bool
        :return: Boolean indicating if the config(s) have outstanding changes
        :rtype: bool
        '''
        ret = self._saved
        if ret and not shallow:
            ret = self.__apply_to_tree('is_saved', shallow=shallow)

        return ret

    def save(self, shallow=False):
        '''
        Saves every config in the config tree that needs it.

        Must be performed depth first.

        Validates the configuration tree before saving.

        :param shallow: Boolean indicating whether to save just this config or the entire tree
        :type shallow: bool
        :return: Boolean indicating success or failure
        :rtype: bool
        :raises: CompositeConfigError
        '''
        ret = False
        
        # Do we even need to do anything?
        if self.is_saved(shallow=shallow):
            ret = True
        else:
            problems = self.validate()
            if problems:
                self.__logger.error("Problems detected when validating the config tree")
                for problem in problems:
                    self.__logger.error(problem)
                ret = False
            else:
                if not shallow:
                    # All of our configs need to be saved first
                    # Walk through our list of configs and save them
                    for obj in self.configurations:
                        ret = obj.save(shallow=shallow)
    
                        # If there were any problems stop straight away
                        if not ret:
                            raise IcmConfigError("IcmConfig.save: Problem saving {0}".format(obj.get_full_name()))

                # Finally, save ourself but only if we need to be saved
                # If we're in deep save mode (shallow=False) then it's possible that
                # this config did not need saving but something further down the tree
                # did need to be saved. In that case we don't need to do anything more
                if self.is_saved(shallow=True):
                    ret = True
                else:
                    if self._icm.config_exists(self.project, self.variant, self.config):
                        if self.is_mutable(shallow=True):
                            self.__logger.info("Saving configuration: {}".format(self.get_full_name()))
                            pm_includes = self.__format_objects_for_pm()
                            if pm_includes:
                                ret = self._icm.update_config(self.project, self.variant, self.config, pm_includes)
                                if not ret:
                                    self.__logger.error("Problem updating configuration {0}".format(self.get_full_name()))
                            else:
                                self.__logger.info("Skip saving as there were no differences between previous/current configuration.")
                                ret = True
                        else:
                            ret = False
                            self.__logger.warn("Cannot update immutable configuration {0}".format(self.get_full_name()))
                    else:
                        self.__logger.info("Creating {0}".format(self.get_full_name()))
                        pm_includes = self.__format_objects_for_pm()
                        self.__logger.debug("pm_includes: {}".format(pformat(pm_includes)))
                        if pm_includes:
                            ret = self._icm.add_config(self.project, self.variant, self.config, description=self.description)
                            if not ret:
                                self.__logger.error("Problem creating configuration {0}".format(self.get_full_name()))
                            else:
                                ret = self._icm.update_config(self.project, self.variant, self.config, pm_includes)
                                if not ret:
                                    self.__logger.error("Problem updating configuration {0}".format(self.get_full_name()))
                        else:
                            self.__logger.info("Skip saving as there were no differences between previous/current configuration.")
                            ret = True

                # Now update the properties if everything is ok
                if ret:
                    ret = self.save_properties()

                # Finally, if ret is still good update the flags
                if ret:
                    self._saved = True
                    self._in_db = True
                    # Set the originals to be the new current
                    self._saved_configurations = list(self.configurations)

        return ret

    def save_properties(self):
        '''
        Saves the configuration properties

        :return: Boolean indicating success or failure
        :rtype: bool
        '''
        ret = True
        if self._properties_changed:
            ret = self._icm.add_config_properties(self.project, self.variant, self.config, self.properties)
        if ret:
            self._properties_changed = False
        else:
            self.__logger.error("Problem adding properties to {}".format(self.get_full_name()))
        return ret

    def validate(self):
        '''
        Runs validation checks on this configuration and the entire config tree

        :return: List of issues found
        :rtype: list
        '''
        problems = []

        if not ICMName.is_config_name_valid(self.config):
            problems.append('{0} is not a valid config name.'.format(self.config))

        # Validate ourself first
        # We aren't in the business of building the tree, just the configs
        # so make sure project/variant already exist
        # Don't perform this check if we're in preview mode
        if not self.preview:
            problems += self.__validate_location_in_icm_tree()

        # Make sure configurations are valid in this context
        # For example, are all simple configs local
        # Make sure there are no duplicates with different configs: e.g. foo@1.0 and foo@2.0
        problems += self.__validate_configurations()

        # If we have no parents we're the root config so need to check the entire tree
        if not self.parents:
            problems += self.__check_tree_for_clashes()
    
        return list(set(problems))

    def report(self, show_simple=True, show_libraries=False, nohier=False, depth=0, legacy_format=False):
        '''
        Returns a report on the configuration:

        :param show_simple: Boolean indicating whether or not to include simple configs in the report.
        :type show_simple: bool
        :param show_libraries: Flag indicating whether or not to include library/release information
        :type show_libraries: bool
        :param depth: Value used to indicate how far down the tree the method has progressed when called recursively.
        :type depth: int
        :return: String containing a printable report about the configuration.
        :rtype: str

        legacy_format:
            in gdpxl, these objects are printed like this:
                config:  project/variant/config
                library: project/variant/libtype/library
                release: project/variant/libtype/library/release
            if legacy_format=True, it will be printed like this:
                config:  project/variant@config
                library: project/variant:libtype@library
                release: project/variant/libtype@release
        '''
        indentation = '\t' * depth
        report = "{0}{1}\n".format(indentation, self.get_full_name(legacy_format=legacy_format))

        if show_simple:
            all_simple_objs = [x for x in self.configurations if not x.is_config()]
            for obj in sorted(all_simple_objs, key=lambda x: x.get_full_name(legacy_format=legacy_format)):
                report += obj.report(show_simple=show_simple, show_libraries=show_libraries, depth=depth+1, legacy_format=legacy_format)

        all_configs = [x for x in self.configurations if x.is_config()]
        for obj in sorted(all_configs, key=lambda x: x.get_full_name(legacy_format=legacy_format)):
            if nohier:
                report += "\t{}\n".format(obj.get_full_name(legacy_format=legacy_format))
            else:                
                report += obj.report(show_simple=show_simple, show_libraries=show_libraries, depth=depth+1, legacy_format=legacy_format)

        return report

    def is_object_in_tree(self, obj):
        '''
        Finds and returns the number of times the specified config is in the tree

        :param sought_config: The configuration being sought
        :type sought_config: ICMConfig
        :return: The number of times sought_config appears in the tree
        :rtype: int
        '''
        return self.flatten_tree().count(obj)
    
    def get_foreign_objects(self):
        '''
        Returns a list of all foreign configurations in the tree
        Foreign configurations are those that are outside this configs
        part of the project/variant structure. For example, in a different
        project or same project but different variant.

        :return: List of foreign configurations.
        :rtype: list
        '''
        unique_objs = set(self.flatten_tree())
        return [x for x in unique_objs if self.is_foreign(x)]

    def get_local_objects(self):
        '''
        Returns a list of all local configurations in the tree
        Includes self!

        :return: List of local configurations
        :rtype: list
        '''
        unique_objs = set(self.flatten_tree())
        return [x for x in unique_objs if self.is_local(x)]

    def remove_object_from_tree(self, sought_obj):
        '''
        Removes all instances of the specified config from the config tree

        :param sought_config: The IC Manage configuration to remove
        :type sought_config: ICMConfig
        :return: The number of configurations that were removed from the tree
        :rtype: int
        '''
        num_removed = 0

        # Check the current level
        if self.remove_configuration(sought_obj):
            num_removed += 1

        # Now go through the tree
        for obj in self.configurations:
            if obj.is_config():
                num_removed += obj.remove_object_from_tree(sought_obj)

        return num_removed

    def remove_objects_from_tree(self, objs_to_remove):
        '''
        Removes all instances of each config listed in configs_to_remove
        from the config tree

        :param configs_to_remove: List of ICManageCOnfig objects to remove
        :type configs_to_remove: list
        :return: Total number of configs removed
        :type return: int
        '''
        num_removed = 0
        for obj_to_remove in objs_to_remove:
            num_removed += self.remove_object_from_tree(obj_to_remove)
        return num_removed

    def auto_replace_object_in_tree(self, new_obj):
        '''
        By right, all the following APIs should be able to automatically replace the
        objects without having to provide the tobe-replaced object info:-
        - replace_object_in_tree()
        - replace_all_instances_in_tree()

        The reason is because:-
        - if the new_obj is a variant-config, 
           > then 'obviously' all matching 'project/variant' should be replaced with the new_obj
        - if the new_obj is a IcmLibrary
           > then 'obviously' all matching 'project/variant/libtype' should be replaced with the new_obj
        '''
        project = new_obj.project
        variant = new_obj.variant
        if new_obj.is_config():
            libtype = None
        else:
            libtype = new_obj.libtype
        
        sought_objs = self.search("^{}$".format(project), "^{}$".format(variant), "^{}$".format(libtype))
        for obj in sought_objs:
            num_replaced += self.replace_object_in_tree(obj, new_obj)

        return num_replaced


    def replace_object_in_tree(self, sought_obj, new_obj, allow_same_obj=False):
        '''
        Replaces all instances of the sought config in the config tree
        with the new config
        Both sought and new config must be instances of a concrete implementation of ICMConfig

        :param sought_config: The IC Manage config to be replaced
        :type sought_config: ICMConfig
        :param new_config: The IC Manage config that will replace sought_config
        :type new_config: ICMConfig
        :return: The number of configurations that were replaced
        :rtype: int
        :raises: CompositeConfigError
        '''
        num_replaced = 0

        if not isinstance(sought_obj, IcmLibrary) and not isinstance(sought_obj, IcmConfig):
            raise IcmConfigError("replace_object_in_tree: Sought obj is not of type IcmConfig/IcmLibrary")

        if not isinstance(new_obj, IcmConfig) and not isinstance(new_obj, IcmLibrary):
            raise IcmConfigError("replace_object_in_tree: New obj is not of type IcmConfig/IcmLibrary")

        if not allow_same_obj:
            if sought_obj == new_obj:
                raise IcmConfigError("replace_object_in_tree: Source ({}) and destination ({}) objects are the same".format(sought_obj, new_obj))

        if sought_obj in self.configurations:
            self.remove_configuration(sought_obj)
            self.add_configuration(new_obj)
            num_replaced += 1

        for obj in self.configurations:
            if obj.is_config():
                num_replaced += obj.replace_object_in_tree(sought_obj, new_obj)

        return num_replaced

    def replace_all_instances_in_tree(self, project, variant, new_obj, libtype=None):
        '''
        The below set of inputs are mutually exclusive:-
        - new_config (only replace IcmConfig() objects)
        - new_libtype (only replace IcmLibrary() objects)
        '''
        num_replaced = 0
        if not libtype:
            sought_objs = self.search('^'+project+'$', '^'+variant+'$', libtype=None)
        else:
            sought_objs = self.search('^'+project+'$', '^'+variant+'$', '^'+libtype+'$')
        for obj in sought_objs:
            num_replaced += self.replace_object_in_tree(obj, new_obj, True)

        return num_replaced

    def flatten_tree(self):
        '''
        Returns a flattened list of every configuration in the tree
        including this one

        :return: List of configurations in the tree
        :rtype: list
        '''
        flattened_tree = [self]
        for config in self.configurations:
            flattened_tree += config.flatten_tree()
        return list(set(flattened_tree))

    def is_local(self, obj):
        return self.project == obj.project and self.variant == obj.variant

    def is_foreign(self, obj):
        return not self.is_local(obj)

    def location_key(self):
        '''
        Returns a tuple key for this configuration based upon its location in the
        IC Manage tree, ingoring the config name.
        Only applicable to simple configs
        For composite configs: (project, variant)
        For simple configs: (project, variant, libtype)

        :return: Tuple containing project and variant
        :rtype: tuple
        '''
        return (self.project, self.variant)

    def key(self):
        '''
        Returns a key representation of this config

        :return: A tuple containing project, variant and config
        :rtype: tuple
        '''
        return (self.project, self.variant, self.config)

    def get_bom(self, libtypes=[], p4=False, relchange=False):
        '''
        Returns the depot paths for all sub-configurations

        :param libtypes: Optional libtype filter
        :type libtypes: list
        :param p4: Boolean indicating whether or not to provide configuration information as Perforce depot paths
        :type p4: bool
        :param relchange: Boolean indicating whether to use the dev or icmrel depot path
        :type relchange: bool
        :return: A list of paths for all sub-configs
        :rtype: list
        '''
        paths = []
        for config in self.configurations:
            bom = config.get_bom(libtypes=libtypes, p4=p4, relchange=relchange)
            if bom:
                paths.extend(bom)

        # Pass paths through a set to de-dupe it
        return list(set(paths))

    def search(self, project='', variant='', libtype=None):
        '''
        A generic method used to search for and return all configurations that match
        the specified search criteria. Search criteria are Python regex
        expressions.
        
        If libtype == None:
            returns only IcmConfig() objects
        if libtypes != None:
            returns IcmLibrary() objects

        (Note: libtype=None and libtype='' is different.
        - libtype=None means no matching of IcmLibrary() objects
        - libtype='' means match all

        :param project: Regex to match project
        :type project: str
        :param variant: Regex to match variant
        :type variant: str
        :param libtype: Regex to match libtype or None to only match IcmConfig
        :type libtype: str or None
        :return: List of matching IcmConfig(if libtype=None) or IcmLibrary(if libtype!=None) within the tree
        :rtype: list
        '''
        ret = []
        if not project and not variant and not libtype:
            self.__logger.warn('IcmConfig search method called with no search criteria')
        else:
            # If libtype is specified we can't match!
            if libtype == None:
                if re.search(project, self.project) and re.search(variant, self.variant):
                    ret.append(self)
            
            for obj in self.configurations:
                if libtype == None and not obj.is_config():
                    continue
                ret.extend(obj.search(project=project, variant=variant, libtype=libtype))
        return ret

    #def get_next_mutable_composite_config(self):
    def get_next_mutable_config(self):
        '''
        Searches through the configuration tree to find a composite
        configuration that has at least one mutable sub config or
        has all immutable sub-configs but is itself mutable

        :return: The next composite configuration that is mutable
        :type return: CompositeConfig
        '''
        ret = None

        for obj in self.configurations:
            # Only interested in mutable configurations
            if obj.is_mutable():
                # If the obj is mutable and IcmConfig(), recurse
                if obj.is_config():
                    ret = obj.get_next_mutable_config()
                    break
                else:
                    # If the obj is mutable and IcmLibrary(), we need to release
                    # tree. Don't break though in case there's a mutable composite
                    # we haven't seen yet
                    ret = self

        # If all sub-configs are immutable ret will be None but we still
        # consider self to be mutable
        if ret is None and self.is_mutable():
            ret = self

        return ret

    #def get_mutable_composite_configs_ready_for_snap(self):
    def get_mutable_configs_ready_for_snap(self):
        '''
        Returns a list of mutable composite configurations within the tree that are ready
        to be converted into snap- configurations. That is, composite configs that are
        mutable and all composite sub-configs are immutable.

        :return: List of composite configurations.
        :rtype: list
        '''
        configs_to_snap = []
        include_self = True

        for obj in self.configurations:
            if obj.is_mutable() and obj.is_config():
                include_self = False
                configs_to_snap.extend(obj.get_mutable_configs_ready_for_snap())

        if include_self and self.is_mutable():
            configs_to_snap.append(self)

        # De-dupe what we're returning
        return list(set(configs_to_snap))

    #def get_composite_configs_ready_for_release(self):
    def get_configs_ready_for_release(self):
        '''
        Returns a list of composite configurations within the tree that are ready
        to be converted into REL configurations. That is, composite configs that are
        not already REL and all of their sub-configs are REL configs.

        :return: List of composite configurations.
        :rtype: list
        '''
        configs_to_rel = []
        include_self = True

        for obj in self.configurations:
            if not obj.is_released():
                include_self = False
                if obj.is_config():
                    configs_to_rel.extend(obj.get_configs_ready_for_release())

        if include_self and not self.is_released():
            configs_to_rel.append(self)

        # De-dupe list before returning
        return list(set(configs_to_rel))

    #def get_composite_configs_ready_for_prelease(self):
    def get_configs_ready_for_prelease(self):
        '''
        Returns a list of composite configurations within the tree that are ready
        to be converted into PREL configurations. That is, composite configs that are
        not already REL/PREL and all of their sub-configs are REL/PREL configs.

        :return: List of composite configurations.
        :rtype: list
        '''
        configs_to_rel = []
        include_self = True

        for obj in self.configurations:
            if not obj.is_preleased():
                include_self = False
                if obj.is_config():
                    configs_to_rel.extend(obj.get_configs_ready_for_prelease())

        if include_self and not self.is_preleased():
            configs_to_rel.append(self)

        # De-dupe list before returning
        return list(set(configs_to_rel))

    #def get_all_composite_configs_with_only_simple_sub_configs(self):
    def get_all_configs_with_only_library_or_release(self):
        '''
        Gets a list of all composite configurations in the tree that only contain simple
        sub configurations.

        :return: List of composite configurations
        :rtype: list
        '''
        ret = []
        include_self = True

        # If this is an empty config don't include it in ret
        if not self.configurations:
            include_self = False
        else:
            for obj in self.configurations:
                if obj.is_config():
                    include_self = False
                    ret.extend(obj.get_all_configs_with_only_library_or_release())

        if include_self:
            ret.append(self)

        # De-dupe list before returning
        return list(set(ret))

    def get_empty_configs(self):
        '''
        Returns a list of the empty composite configurations within the tree
        An empty composite configuration is one that has no sub-configs

        :return: List of empty composite configurations
        :type return: list
        '''
        return [x for x in self.flatten_tree() if x.is_config() and len(x.configurations) == 0]

    def remove_empty_configs(self):
        '''
        Removes empty composite configurations from the tree

        :return: The number of empty composite configurations removed
        :type return: int
        '''
        num_removed = 0

        # Get all composite configs
        empty_configs = self.get_empty_configs()
        # Keep spinning until all empties are removed
        # We do this because the process of removing empty composites may produce more empties
        while empty_configs:
            for empty_config in empty_configs:
                self.__logger.debug('Removing empty configuration {0}'.format(empty_config.get_full_name()))
                num_removed += self.remove_object_from_tree(empty_config)
            empty_configs = self.get_empty_configs()
        return num_removed

    def get_dot(self):
        '''
        Returns a list of strings, each representing one line
        of dot output representing the configuration.

        :return: List of dot output strings
        :rtype: list
        '''
        dot_lines = []

        for obj in self.configurations:
            if obj.is_config():
                dot_lines.append('"{0}" -> "{1}";'.format(self.get_full_name(), obj.get_full_name()))
                dot_lines.extend(obj.get_dot())

        # Convert to set before returning to remove duplicates
        return list(set(dot_lines))

    def is_content_equal(self, other):
        '''
        Performs a comparison of the two configs to see if
        they're pointing at the same IC Manage objects.

        Does not check at the file level.

        :param other: The other IC Manage configuration we're comparing against
        :type other: ICMConfig
        :return: Boolan indicating whether or not the content is equal
        :rtype: bool
        '''
        content_equal = False

        if self == other:
            content_equal = True
        else:
            if self.project == other.project and self.variant == other.variant:
                # The sub configurations are sets so an equality comparison should
                # work regardless of order
                content_equal = self.configurations == other.configurations

        return content_equal

    def get_objects_by_location(self):
        '''
        Returns a dict describing the configurations in the tree
        by their location in the IC Manage tree.

        key = object's location
        Value = Set of IcmConfig()/IcmLibrary() objects 

        :return: A dictionary describing the configurations in the tree by their location
        :rtype: dict
        '''
        objs_by_location = {}
        all_objs = self.flatten_tree()
        for obj in all_objs:
            location = obj.location_key()
            if location in objs_by_location:
                objs_by_location[location].add(obj)
            else:
                objs_by_location[location] = set([obj])
        return objs_by_location

    def clone_tree(self, new_name, clone_simple=False, clone_immutable=False, reuse_existing_config=False):
        '''
        Clones every mutable IcmConfig within the tree to new_name.

        If clone_simple=True then clones IcmLibrary objects too.

        If clone_immutable=True then REL/snap- IcmConfig/IcmLibrary are also cloned.

        :param new_name: The new IC Manage configuration name
        :type new_name: str
        :param clone_simple: Boolean indicating whether or not simple configs should be cloned
        :type clone_simple: bool
        :param clone_immutable: Boolean indicating whether or not immutable configs should be cloned
        :type clone_immutable: bool
        :return: The root of the cloned configuration tree
        :rtype: CompositeConfig
        '''
        clone = self.clone(new_name)

        immutables = ('REL', 'PREL', 'snap-')
        exists = False
        if not reuse_existing_config:
            exists = self._icm.config_exists_under_config_hierarchy(new_name, self.project, self.variant, self.config, stop_at_immutables=not clone_immutable)
        if exists:
            raise IcmConfigError("Failed clone_tree because these configs already exist: {}".format(exists))
        if clone_simple:
            if not new_name.startswith(immutables):
                exists = False
                if not reuse_existing_config:
                    exists = self._icm.library_exists_under_config_hierarchy(new_name, self.project, self.variant, self.config, stop_at_immutables=not clone_immutable)
                if exists:
                    raise IcmConfigError("Failed clone_tree because these libraries already exist: {}".format(exists))
            else:
                exists = self._icm.release_exists_under_config_hierarchy(new_name, self.project, self.variant, self.config, stop_at_immutables=not clone_immutable)
                if exists:
                    raise IcmConfigError("Failed clone_tree because these releases already exist: {}".format(exists))

        for obj in clone.flatten_tree():
            if obj == clone:
                continue

            if not obj.is_mutable() and not clone_immutable:
                self.__logger.info('Ignoring {0} as clone_immutable=False'.format(obj.get_full_name()))
                continue

            elif obj.is_config() or clone_simple:
                self.__logger.info("Cloning {}".format(obj.get_full_name()))
                sub_clone = obj.clone(new_name, skip_existence_check=True)
                clone.replace_object_in_tree(obj, sub_clone)
               
        return clone

    def get_immutable_parents(self):
        '''
        Returns a list of parent configurations that are immutable

        :return: List of CompositeConfig objects
        :type return: list
        '''
        return [x for x in self.parents if not x.is_mutable()]

    def get_configs_to_clone_if_self_changes(self):
        '''
        Returns a list of configurations that would need to be cloned
        if this configuration were modified. That is the configs immutable parents,
        their immutable parents, and so on.

        :return: List of CompositeConfig objects that need to be cloned
        :type return: list
        '''
        configs_to_clone = []
        for parent in self.get_immutable_parents():
            configs_to_clone.append(parent)
            configs_to_clone += parent.get_configs_to_clone_if_self_changes()
        return list(set(configs_to_clone))

    def get_configs_to_clone_if_self_changes_including_mutable(self):
        '''
        Returns a list of configurations that would need to be cloned whether its immutable or mutable

        :return: List of CompositeConfig objects that need to be cloned
        :type return: list
        '''
        configs_to_clone = []
        for parent in self.parents:
            configs_to_clone.append(parent)
            configs_to_clone += parent.get_configs_to_clone_if_self_changes_including_mutable()
        return list(set(configs_to_clone))

    def get_modified_immutable_configs(self):
        '''
        Returns a list of immutable configurations within the tree that have been modified
        in some way.

        :return: List of IcmConfig objects referencing modified immutable configs
        :rtype: list
        '''
        modified_immutable_configs = [x for x in self.configurations if x.is_config() and not x.is_mutable() and not x.is_saved(shallow=True)]
        # Add the modified immutables from the rest of the tree
        for obj in self.configurations:
            if obj.is_config():
                modified_immutable_configs.extend(obj.get_modified_immutable_configs())

        return list(set(modified_immutable_configs))

    def get_modified_mutable_configs(self):
        '''
        Returns a list of mutable composite configurations within the tree that have been
        modified in some way.

        :return: List of ZCompositeConfig objects referencing modified mutable configs
        :rtype: list
        '''
        modified_mutable_configs = [x for x in self.configurations if x.is_config() and x.is_mutable() and not x.is_saved(shallow=True)]
        # Add the modified mutable configs from the rest of the tree
        for obj in self.configurations:
            if obj.is_config():
                modified_mutable_configs.extend(obj.get_modified_mutable_configs())

        return list(set(modified_mutable_configs))

    def convert_modified_immutable_configs_into_mutable(self, new_name):
        '''
        Converts all modified immutable configs into mutable configs named new_name.

        :param new_name: The new configuration name.
        :type new_name: str
        :return: Number of configurations converted
        :rtype: int
        :raises: CompositeConfigError
        '''
        num_converted = 0

        # Cannot convert into an immutable config
        if new_name.startswith(('snap-', 'REL', 'PREL')):
            raise IcmConfigError('Cannot convert a modified immutable config into an immutable config')

        # We need to get the list of modified immutable configs, convert them,
        # get the new list, convert, etc. until there are no modified
        # immutable configs left in the system.
        modified_immutables = self.get_modified_immutable_configs()
        while modified_immutables:
            for modified_immutable in modified_immutables:
                new_mutable = modified_immutable.clone(new_name)
                num_converted += self.replace_object_in_tree(modified_immutable, new_mutable)

            modified_immutables = self.get_modified_immutable_configs()

        return num_converted

    def rename_modified_mutable_configs(self, new_config_name):
        '''
        Renames any modified mutable configs to new_config_name.

        Does not rename the root configuration in the tree if it is mutable and modified.

        :param new_config_name: The new configuration name
        :type new_config_name: str
        :return: Number of configurations renamed
        :rtype: int
        :raises: CompositeConfigError
        '''
        num_renamed = 0

        # Cannot rename to an immutable config
        if new_config_name.startswith(('snap-', 'REL', 'PREL')):
            raise IcmConfigError('Cannot rename a modified mutable config into an immutable config')

        # We need to keep processing the modified mutable configs until
        # there are none left as each time we rename a config it modifies
        # that config's parents
        modified_mutables = self.get_modified_mutable_configs()
        # Discard any configs whose name is new_config_name as we've probably just inserted
        # them into the tree
        modified_mutables = [x for x in modified_mutables if x.config != new_config_name]
        while modified_mutables:
            for modified_mutable in modified_mutables:
                new_mutable = modified_mutable.clone(new_config_name)
                num_renamed += self.replace_object_in_tree(modified_mutable, new_mutable)

            modified_mutables = self.get_modified_mutable_configs()
            modified_mutables = [x for x in modified_mutables if x.config != new_config_name]

        return num_renamed
           

    def get_all_projects(self):
        ''' return a list of all icm-projects that were included. '''
        projects = []
        for cf in self.flatten_tree():
            projects.append(cf.project)
        return sorted(list(set(projects)))


    def __repr__(self):
        return "{0}/{1}/{2}".format(self.project, self.variant, self.config)

    def __format_objects_for_pm(self):
        '''
        Returns this configs configuration items as a dictionary formatted for
        use in 'gdp update' call.
        For details on the format, kindly refer to docstring in icm.py's update_config()
        '''
        formatted_objs = {'add':[], 'remove':[]}

        # We need to handle the following:
        # Completely new configurations - those that were not present in any way before
        # Completely deleted configurations - those that have been completely removed from the original list
        # Modified - those that have simple had the configuration name changed (e.g. foo@1.0 has become foo@2.0)
        # These are all determined using the original configuration list stored in self._saved_configurations
        # versus the current configuration list
        # Nicely, if pm spots a remove and a new instance of a config it knows to remove the old and add the new
        # so the modified section takes care of itself. Assuming we get the adds and deletes right of course.
        current = set(self.configurations)
        saved = set(self._saved_configurations)
        self.__logger.debug("-- current: {}".format(current))
        self.__logger.debug("-- saved: {}".format(saved))

        # If there have been no changes just move on
        if current != saved:
            deleted = saved - current
            new = current - saved
             
            # First the new configurations
            for obj in new:
                formatted_objs['add'].append(obj.get_path())

            # Now the removed configurations
            for obj in deleted:
                formatted_objs['remove'].append(obj.get_path())

        return formatted_objs

    def __apply_to_tree(self, method, *args, **kwargs):
        '''
        Iterates over the entire config tree, calling method against each object
        '''
        ret = None
        for obj in self.configurations:
            ret = getattr(obj, method)(*args, **kwargs)
            if not ret:
                break

        # If ret is still None then we had no subconfigs so
        # set it to True    
        if ret is None:
            ret = True

        return ret

    def __validate_location_in_icm_tree(self):
        '''
        Returns a list of issues found. Empty list is good
        '''
        ret = []
        variant_exists = False
        try: 
            if not self._icm.variant_exists(self.project, self.variant):
                ret.append("Variant {} does not exist in project {}".format(self.variant, self.project))
            else:
                variant_exists = True
        except ICManageError:
            ret.append("Variant {0} and/or project {1} does not exist".format(self.variant, self.project))

        if not variant_exists:
            if not self._icm.project_exists(self.project):
                ret.append("Project {} does not exist".format(self.project))

        return ret

    def __validate_configurations(self):
        '''
        Validates the configurations in configurations only
        Returns a list of issues found or empty list if all good
        '''
        ret = []
        for obj in self.configurations:
            if (obj.is_library() or obj.is_release()) and not self.is_local(obj):
                ret.append("IcmLibrary:{0} is not local to {1}".format(obj.get_full_name(), self.get_full_name()))
            if not self.is_mutable() and obj.is_mutable():
                ret.append("{0} is a mutable object within an immutable configuration".format(obj.get_full_name()))
        return ret

    def __check_tree_for_clashes(self):
        '''
        Checks the entire tree for clashes
        Clashes are multiple project/variant[:libtypes] that refer to different
        configs
        '''
        ret = []

        # First get the list of configurations by location
        # If there are multiple configurations for a location
        # that's a clash and must be reported
        objs_by_location = self.get_objects_by_location()
        all_objs = self.flatten_tree()

        for location in list(objs_by_location.keys()):
            if len(objs_by_location[location]) > 1:
                # There's a clash!
                self.__logger.debug('Found clash in location {}'.format(location))
                error_msg = 'Multiple configurations for {0} found:'.format(location)

                for clashing_obj in objs_by_location[location]:
                    error_msg += '\n{0}'.format(clashing_obj.get_full_name())
                    def get_parents(obj, all_objs, depth=0):
                        error_msg = ""
                        parent_config_names = [x for x in obj.parents if x in all_objs and x.is_saved()]
                        # Using spaces instead of \t for better visualization
                        for parent in parent_config_names:
                            format = '    ' * depth
                            error_msg += '\n    {0}-> {1}'.format(format, parent.get_full_name())
                            error_msg += get_parents(parent, all_objs, depth=depth+1)
                        return error_msg
                    error_msg += get_parents(clashing_obj, all_objs, depth=0)   
                ret.append(error_msg)
        return ret

    def __cmp__(self, other):
        return self.key() == other.key()

    def __eq__(self, other):
        return self.key() == other.key()

    def __ne__(self, other):
        if other is None:
            return True

        return not self.key() == other.key()

    def __hash__(self):
        return hash(self.key())

## @}
