#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/icmlibrary.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

GDP Library/Release object.

We are merging both the library and release object into one class because both of them have exactly the same properties.
The only difference is the "type" and the "change" property.
See below for details:-
    > gdp list /site/project/variant/libtype/library/release
    {
        "uri": "p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/i10socfm/liotest1/ipspec/dev/...@2482",
        "created-by": "lionelta",
        "id": "R2245321",
        "type": "release",
        "name": "snap-4",
        "path": "/intel/i10socfm/liotest1/ipspec/dev/snap-4",
        "created": "2020-10-13T09:41:52.384Z",
        "modified": "2020-10-13T09:41:52.384Z",
        "change": "@2482",
        "libtype": "ipspec"
    }
    > gdp list /site/project/variant/libtype/library
    {
        "location": "liotest1/ipspec",
        "uri": "p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/i10socfm/liotest1/ipspec/dev/...",
        "created-by": "lionelta",
        "id": "L1247063",
        "type": "library",
        "name": "dev",
        "path": "/intel/i10socfm/liotest1/ipspec/dev",
        "created": "2020-09-23T10:06:31.322Z",
        "modified": "2020-09-23T10:06:31.322Z",
        "change": "@now",
        "libtype": "ipspec"
    } 


There are things that are allowed to be changed, and things that are not allowed.

Allowed (during save())
- create a new empty library (libtype must pre-exist)
- create a new branched library (libtype must pre-exist)
- create a new release (library must pre-exist)
- add/modify user defined properties

Disallowed(during save())
- modify anything else in existing library/release

'''

## @addtogroup dmxlib
## @{

from builtins import str
from builtins import object
import os
import logging
from datetime import datetime
import re

from dmx.abnrlib.icm import ICManageCLI, ICManageError
from dmx.abnrlib.namevalidator import ICMName
import dmx.abnrlib.config_naming_scheme

class IcmLibraryError(Exception):
    pass

class IcmLibrary(object):
    ''' GDP Library/Release object '''

    ### These are the default properties created by icm (no user created)
    DEFAULT_PROP_KEYS = ['location', 'uri', 'created-by', 'id', 'type', 'name', 'path', 'created', 'modified', 'change', 'libtype']

    def __init__(self, project='', variant='', libtype='', library='', lib_release='', description='', preview=False, use_db=True, parents=None, changenum=None, defprop_from_icm=None,
            srclibrary='', srcrelease=''):
        '''
        defprop_from_icm:   This is used to create the library/release object by providing the json output from 'gdp list'
                            At times, we already have the details, and thus, we do not want to incur additional cost by hitting the server for queries.
                            This is the purpose of introducing this param.

        When defprop_from_icm is provided, no other input params is required.
        Else, project, variant, libtype, library are compulsory inputs.

        During clone, project/variant/libtype/library will be created, based from the following source:
        if srclibrary and srcrelease is given:
            --from project/variant/libtype/srclibrary/srcrelease
        if srclibrary:
            --from project/variant/libtype/srclibrary
        '''

        self.__logger = logging.getLogger(__name__)
        self._preview = preview
        self._icm = ICManageCLI(preview=preview)

        if defprop_from_icm:
            self._type = defprop_from_icm['type']
            data = self._icm.decompose_gdp_path(defprop_from_icm['path'], self._type)
            self._project = data['project']
            self._variant = data['variant']
            self._libtype = data['libtype']
            self._library = data['library']
            self._lib_release = ''
            if self._type == 'release':
                self._lib_release = data['release']
            self._changenum = defprop_from_icm['change'][1:]  # removed @ from '@1234'
            self._description = ''
            self._defprops = defprop_from_icm
            ### Since this info is coming from 'gdp list', we assume(and expect) that 
            ### this object data is already saved, and already in icm db
            self._in_db = True
            self._saved = True
        else:
            self._project = project
            self._variant = variant
            self._libtype = libtype
            self._library = library
            self._lib_release = lib_release
            self._changenum = changenum
            self._description = description
            self._defprops = {} # These are all the default properties return my icm (system + user created properties)
            if lib_release:
                self._type = 'release'
            else:
                self._type = 'library'

            # In order to determine if we're really 'in the database' or not we
            # have to consider not just the project/variant:libtype@config but
            # also the library and release. Otherwise it could all get very
            # confusing for the consumer of this class
            # If the project/variant:libtype@config is detected in the db
            # but with a different libtype or release we should throw an
            # error and point the user to create_from_icm
            self._in_db = False
            self._saved = False

            # Only extract data from the database if we've been told to
            # In many situations other scripts have got the details from IC Manage
            # and they're now building the class. Therefore there's no need to
            # hit the database again
            if use_db:
                if self._lib_release:
                    func = self._icm.get_release_details
                    params = [project, variant, libtype, library, lib_release]

                else:
                    func = self._icm.get_library_details
                    params = [project, variant, libtype, library]

                try:
                    self._defprops = func(*params)
                except:
                    self._defprops = {}
                if self._defprops:
                    # Meaning object already exists in database
                    self._in_db = True
                    self._saved = True
                    
                    self._changenum = self._defprops['change'][1:]
            else:
                # Assume it's in the database
                self._in_db = True
                self._saved = True

        # These are the properties created by users (not created automatically by icm)
        # - There is a difference between setting self._properties to None and {}:
        #   > None == the library/release does exist in db, it's just that we haven't loaded them
        #   > {}   == the library/release does NOT exist in db. Loading them will raise error.
        if self._in_db:
            # Set properties to None as we lazy load them
            self._properties = None
            if self._defprops:
                self._properties = self.get_user_properties()
        else:
            # Set it to blank because we have no properties
            self._properties = {}

        # Store the library we have now in original library so we can format
        # update commands accordingly - they need to remove the original
        self._original_library = self._library

        # Flag to show if the properties have been updated at all
        # Using this means we only hit the IC Manage database for
        # properties when we have to, which is good for performance
        self._properties_changed = False

        if 'uri' in self._defprops:
            self._filespec = re.sub('^p4://[^\/]+\/depot', '//depot', self._defprops['uri'])

        if parents is None:
            self._parents = set()
        else:
            self._parents = set(parents)

        self._srclibrary = srclibrary
        self._srcrelease = srcrelease

    @property
    def name(self):
        if self.is_library():
            return self._library
        else:
            return self._lib_release

    @property
    def project(self):
        '''
        The configuration's project
        '''
        return self._project

    @project.setter
    def project(self, new_project):
        '''
        Sets the project name
        '''
        self._project = new_project
        self._saved = False
        if not self._icm.config_exists(self.project, self.variant, self.config, libtype=self.libtype):
            self._in_db = False

    @property
    def variant(self):
        '''
        The configuration's variant
        '''
        return self._variant

    @variant.setter
    def variant(self, new_variant):
        '''
        Sets the variant name
        '''
        self._variant = new_variant
        self._saved = False
        if not self._icm.config_exists(self.project, self.variant, self.config, libtype=self.libtype):
            self._in_db = False


    @property
    def properties(self):
        '''
        The configuration's properties
        '''
        if self._properties is None:
            if self.is_library():
                self._properties = self._icm.get_library_properties(self.project, self.variant, self.libtype, self.library)
            else:   # is_release
                self._properties = self._icm.get_release_properties(self.project, self.variant, self.libtype, self.library, self.lib_release)
            #self._properties = self._icm.get_config_properties(self.project, self.variant, self.config, libtype=self.libtype)
        return self._properties

    @properties.setter
    def properties(self, new_properties):
        '''
        Sets the properties
        '''
        self._properties = new_properties
        self._saved = False
        self._properties_changed = True

    def add_property(self, key, value):
        '''
        Adds the key=value pair to properties.

        :param key: The property key
        :type key: str
        :param value: The value of the property
        :type value: str
        '''
        if key in self.DEFAULT_PROP_KEYS:
            raise Exception("add/modify system default properties is prohibited: {}={}".format(key, value))
        self.properties[key] = value
        self._saved = False
        self._properties_changed = True

    def remove_property(self, key):
        '''
        Removes the property key from properties

        :param key: The key to remove from this config's properties
        :type key: str
        '''
        if key in self.properties:
            del self.properties[key]
            self._saved = False
            self._properties_changed = True

    @property
    def libtype(self):
        '''
        The configuration's libtype
        '''
        return self._libtype

    @libtype.setter
    def libtype(self, new_libtype):
        '''
        Sets the libtype
        '''
        self._libtype = new_libtype
        self._saved = False
        if not self._icm.config_exists(self.project, self.variant, self.config, libtype=self.libtype):
            self._in_db = False

    @property
    def library(self):
        '''
        The configuration's library
        '''
        return self._library

    @library.setter
    def library(self, new_library):
        '''
        Sets the library
        '''
        self._library = new_library
        self._saved = False

    @property
    def lib_release(self):
        '''
        The configuration's release
        '''
        return self._lib_release

    @lib_release.setter
    def lib_release(self, new_lib_release):
        '''
        Sets the lib_release
        '''
        self._lib_release = new_lib_release
        self._saved = False
        self._type = 'release'

    @property
    def changenum(self):
        return self._changenum

    @changenum.setter
    def changenum(self, new_changenum):
        self._changenum = new_changenum
        self._saved = False
        self._type = 'release'

    @property
    def changenumdigit(self):
        ''' 
        the real changenum, instead of '@now'
        '''
        if hasattr(self, '_changenumdigit') and self._changenumdigit:
            return self._changenumdigit
        
        change = self.changenum
        if change != 'now':
            self._changenumdigit = change
            return self._changenumdigit

        self._changenumdigit = self._icm.get_activedev_changenum(self.project, self.variant, self.libtype, self.library)
        return self._changenumdigit

    @property
    def description(self):
        '''
        The configuration's description
        '''
        return self._description

    @description.setter
    def description(self, new_description):
        '''
        Sets the description
        '''
        self._description = new_description
        self._saved = False

    @property
    def preview(self):
        '''
        Return the preview flag
        :return: The preview flag
        :type return: bool
        '''
        return self._preview

    @preview.setter
    def preview(self, new_preview):
        '''
        Sets the preview mode and reflects that change
        to the ICManageCLI object
        :param new_preview: New preview setting
        :type preview: bool
        '''
        self._preview = new_preview
        self._icm.preview = new_preview

    @property
    def parents(self):
        return self._parents


    def add_parent(self, new_parent):
        '''
        Adds new_parent to the list of parents

        :param new_parent: The new parent IC Manage configuration
        :type new_parent: Config
        :raises: SimpleConfigError
        '''
        # Validate the parent before adding it
        # It needs to be config, in the same project/variant
        # and have self in its configurations
        if new_parent._type != 'config':
            raise Exception('Tried to add {}:{} as a parent of {}:{}'.format(new_parent._type, new_parent.get_full_name(), self._type, self.get_full_name()))

        if new_parent.project != self.project or new_parent.variant != self.variant:
            error_msg = 'Problem adding {0} as parent of {1}'.format(new_parent.get_full_name(), self.get_full_name())
            error_msg += '\n{0} is in a different project and/or variant'.format(new_parent.get_full_name())
            raise Exception(error_msg)

        if self not in new_parent.configurations:
            error_msg = 'Problem adding {}:{} as parent of {}:{}'.format(new_parent._type, new_parent.get_full_name(), self._type, self.get_full_name())
            error_msg += '\n{0} is not a child of {1}'.format(self.get_full_name(), new_parent.get_full_name())
            raise Exception(error_msg)

        self._parents.add(new_parent)

    def remove_parent(self, parent):
        '''
        Removes parent from the set of parents

        :param parent: The parent IC Manage configuration to remove
        :type parent: CompositeConfig
        '''
        try:
            self._parents.remove(parent)
        except KeyError:
            self.__logger.warn("Tried to remove {0} from list of parents for {1} but it wasn't in the list".format(parent.get_full_name(), self.get_full_name()))

    def clone(self, name, skip_existence_check=False):
        '''
        Create a clone of the library/release called name

        if name.startswith(immutable):
            clone it to a new release object
            name is the new release name
        else:
            clone it to a new library object
            name is the new library name

        you can clone 
        - a library to a new library
        - a library to a new release
        - a release to a new release
        - a release to a new library


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
        ### All IcmLibrary() object creation uses use_db=False because we already know that the object
        ### does not exists in the db. Thus, we do not want it to hit the server for self.get_library/release_details() 
        ### (see __init_ for details)
        ### Also, we need to set _in_db and _saved to false so that when save() is called, the object will be created.
        ######################################

        # Cloning to Release
        if self._icm.is_name_immutable(name):
            if not skip_existence_check and self._icm.release_exists(self.project, self.variant, self.libtype, self.library, name):
                raise Exception("Cannot clone to release:{}/{}/{}/{}/{} - it already exists".format(self.project, self.variant, self.libtype, self.library,  name))
            self.__logger.info("Cloning {} into {}/{}/{}/{}/{}".format(self.get_full_name(), self.project, self.variant, self.libtype, self.library, name))
          
            # Cloning library to release
            if self.is_library():
                ret = IcmLibrary(self.project, self.variant, self.libtype, self.library, name, preview=self.preview, use_db=False)
            # Cloning release to release
            else:
                ret = IcmLibrary(self.project, self.variant, self.libtype, self.library, name, preview=self.preview, changenum=self.changenum, use_db=False)
        
        # Cloning to library 
        else:
            if not skip_existence_check and self._icm.library_exists(self.project, self.variant, self.libtype, name):
                raise Exception("Cannot clone to library:{}/{}/{}/{} - it already exists".format(self.project, self.variant, self.libtype, name))
            self.__logger.info("Cloning {} into {}/{}/{}/{}".format(self.get_full_name(), self.project, self.variant, self.libtype, name))
            # Cloning library to library 
            if self.is_library():
                ret = IcmLibrary(self.project, self.variant, self.libtype, name, preview=self.preview, srclibrary=self.library, use_db=False)
            # Cloning release to library
            else:
                ret = IcmLibrary(self.project, self.variant, self.libtype, name, preview=self.preview, srclibrary=self.library, srcrelease=self.lib_release, use_db=False)
        
        ### Set properties in correct state, otherwise a lot of things will break. >.<
        ret._in_db = False
        ret._saved = False
        ret._properties = {}
        return ret


    def get_user_properties(self):
        ret = {}
        for key in self._defprops:
            if key not in self.DEFAULT_PROP_KEYS:
                ret[key] = self._defprops[key]
        return ret
    
    def delete(self, shallow=False):
        ''' DEPRECATED: We do not allow deletion of library/release. '''
        raise Exception("Deletion of library/release is prohibited.") 

    def get_full_name(self, legacy_format=False):
        if legacy_format:
            path = '{}/{}:{}'.format(self.project, self.variant, self.libtype)
            if self.lib_release:
                path += '@{}'.format(self.lib_release)
            else:
                path += '@{}'.format(self.library)
        else:
            path = '{}/{}/{}/{}'.format(self.project, self.variant, self.libtype, self.library)
            if self.lib_release:
                path += '/{}'.format(self.lib_release)
        return path
    get_path = get_full_name

    def get_dict_of_files(self, ignore_project_variant=False):
        return self._icm.get_dict_of_files(self.project, self.variant, self.libtype, self.lib_release, self.library, ignore_project_variant=ignore_project_variant)

    def in_db(self, shallow='this param is meant for not breaking IcmConfig() calls.'):
        return self._in_db

    def is_mutable(self, shallow='this param is meant for not breaking IcmConfig() calls.'):
        if self.is_release():
            return False
        else:
            return True

    def is_released(self, shallow='this param is meant for not breaking IcmConfig() calls.'):
        if self.is_release() and self.lib_release.startswith("REL"):
            return True
        else:
            return False

    def is_preleased(self, shallow='this param is meant for not breaking IcmConfig() calls.', strict=False):
        '''
        Returns True if the configuration is a PREL configuration

        This is a very unique case. PREL is a subset of REL, and thus, a REL should be treated as PREL too.
        By right, I believe that when is_preleased() is called, it should be returning `true` if it is either REL/PREL.
        I could not think of any use case where it needs to return `false`.
        However, in order to have that option, the `strict` parameter is introduced here.
        If there is any possibility that a user strictly would only want this method to return `true` if only the entire tree is PREL,
        then this param needs to be set to strict=true.

        :param shallow: Ignored as we're a simple config
        :type shallow: None
        :return: Boolean indicating if this config is a PREL config
        :rtype: bool
        '''
        if strict:
            rel = ("PREL")
        else:
            rel = ("REL", "PREL")
        if self.is_release() and self.lib_release.startswith(rel):
            return True
        else:
            return False

    def is_active_dev(self):
        if self.is_library():
            return True
        else:
            return False

    def is_active_rel(self):
        ''' DEPRECATED: There is no active_rel concenpt in GDPXL '''
        raise Exception("There is no longer active_rel concept in GDPXL.")

    def is_saved(self, shallow='this param is meant for not breaking IcmConfig() calls' ):
        '''
        Returns True if there are no outstanding changes that have not been committed to the IC Manage database
        Otherwise returns False

        :param shallow: Ignored as we're a simple config
        :type shallow: None
        :return: Boolean indicating whether or not this config needs to be saved
        :rtype: bool
        '''
        return self._saved

    def save(self, shallow=None):
        '''
        Saves the current state of the instance to the IC Manage database

        There are only 2 things that can be(allowed tobe) saved.
        1. if it is a non-existing library, create it
        2. if it is a non-existing release, create it
        (Note: We do not support branch_library here. If you need it, then user icm.py's branch_library() to branch it first)

        :param shallow: Ignored as we're a simple config
        :type shallow: None
        :return: Boolean indicating success or failure
        :rtype: bool
        '''
        self._FOR_REGTEST = []   # This property is meant for regression tests
        if self.is_saved():
            self.__logger.debug("{0} already saved - nothing to do here.".format(self.get_full_name()))
            self._FOR_REGTEST = "already saved"
            return True
        else:
            self.__logger.debug("Validating before saving {} ...".format(self))
            validate_errors = self.validate()
            self._FOR_REGTEST = validate_errors
            if validate_errors:
                self.__logger.error("Problems detected when validating {0}".format(self.get_full_name()))
                for error in validate_errors:
                    self.__logger.error(error)
                return False

        ### Start Saving ###
        ret = True
        # Creating new library/release if they don't exist
        if self._type == 'library':
            self._icm.add_library(self.project, self.variant, self.libtype, self.library, self.description, self._srclibrary, self._srcrelease)
        if self._type == 'release':
            if not self._icm.library_exists(self.project, self.variant, self.libtype, self.library):
                err = 'Cannot create a release on a non-existing library:{}'.format(self.get_full_name())
                self._FOR_REGTEST = err
                self.__logger.error(err)
                return False
            self._icm.add_library_release(self.project, self.variant, self.libtype, self.lib_release, self.changenum, self.description, self.library)

        # Now update the properties if everything is ok
        if ret:
            ret = self.save_properties()

        # Finally, if ret is still good update the flags
        if ret:
            self._saved = True
            self._in_db = True
            # Reset original to reflect what's now in the database
            self._original_library = self.library

        return ret

    def save_properties(self):
        '''
        Save the configuration properties

        :return: Boolean indicating success or failure
        :rtype: bool
        '''
        ret = True 
        if self._properties_changed:
            if self._type == 'library':
                ret = self._icm.add_library_properties(self.project, self.variant, self.libtype, self.library, self.properties)
            else:
                ret = self._icm.add_release_properties(self.project, self.variant, self.libtype, self.library, self.lib_release, self.properties)
            if ret:
                self._properties_changed = False
            else:
                self.__logger.error("Problem saving properties to {}".format(self.get_full_name()))
        return ret

    def validate(self, shallow=True):
        '''
        Validates the configuration - i.e. do we think it can be saved
        Returns the number of issues detected

        shallow is ignored as it's only used for composites

        :param shallow: Ignored as we're a simple config
        :type shallow: None
        :return: List of problems found
        :rtype: list
        '''
        problems = []

        # Is the configuration name valid?
        if not ICMName.is_config_name_valid(self.library):
            problems.append('{0} is not a valid library name'.format(self.library))

        if self.lib_release:
            relnames = ("REL", "PREL", "snap-")
            if not self.lib_release.startswith(relnames):
                problems.append("{} is not a valid release name. It must start with (REL, PREL, snap-).".format(self.lib_release))

                if self.lib_release.startswith("REL"):
                    if not dmx.abnrlib.config_naming_scheme.ConfigNamingScheme().get_data_for_release_config(self.lib_release):
                        problems.append("{} is not a valid REL tag name.".format(self.lib_release))

        if not self.preview and not self._icm.libtype_exists(self.project, self.variant, self.libtype):
            problems.append("Libtype:{} does not exist.".format(self.libtype))

        return problems

    def report(self, show_simple=True, show_libraries=False, depth=0, legacy_format=False):
        '''
        Returns a report on the configuration.

        :param show_simple: Ignored as we are a simple config
        :type show_simple: True
        :param show_libraries: Flag indicating whether or not to include library/release information
        :type show_libraries: bool
        :param depth: Indicates how far down the tree we are
        :type depth: int
        :return: String representation of this config
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
        report = "{0}{1}".format(indentation, self.get_full_name(legacy_format=legacy_format))
        if show_libraries:
            report += ' {}@{}[@{}]'.format(self.library, self.lib_release, self.changenum if self.changenum else 'now')
        return '{0}\n'.format(report)

    def location_key(self):
        '''
        Returns a tuple key for this configuration based upon its location in the
        IC Manage tree, ignoring the config name.

        For composite configs: (project, variant)

        For simple configs: (project, variant, libtype)

        :return: The config location key (project, variant, libtype)
        :rtype: tuple
        '''
        return (self.project, self.variant, self.libtype)

    def key(self):
        '''
        Returns a key representing this object

        :return: Tuple containing project, variant, libtype and config name
        :rtype: tuple
        '''
        return (self.project, self.variant, self.libtype, self.name)

    #TODO:
    def get_bom(self, libtypes=[], p4=False, relchange=False):
        '''
        Returns the depot path for this configuration.

        :param libtypes: Optional libtypes filter
        :type libtypes: list
        :param p4: Boolean indicating whether to print Perforce depot paths or IC Manage/Altera depot paths
        :type p4: bool
        :param relchange: Boolean indicating whether to use dev or icmrel depot paths when printing Perforce paths.
        :type relchange: bool
        :return: The depot path for this configuration within a list
        :rtype: list
        '''
        bom = []
        if not libtypes or self.libtype in libtypes:
            if p4:
                bom.append(self.get_depot_path(relchange=relchange))
            else:
                bom.append(self.__get_altera_path(relchange=relchange))

        return bom

    def get_immutable_parents(self):
        '''
        Walks from this point up the configuration tree
        building a list of immutable parent configurations
        '''
        immutable_parents = []
        for parent in self.parents:
            if not parent.is_mutable():
                immutable_parents += parent.get_immutable_parents()
                immutable_parents.append(parent)
        return immutable_parents
        
    def search(self, project='', variant='', libtype=None): 
        '''
        A generic method used to search for and return all configurations that match
        the specified search criteria. Search criteria are Python regex
        expressions.

        :param project: Regex to match project
        :type project: str
        :param variant: Regex to match variant
        :type variant: str
        :param libtype: Regex to match libtype or None to only match composite configs
        :type libtype: str or None
        :param name: Regex to match config name
        :rtype: list
        '''
        retlist = []
        if not project and not variant and not libtype:
            self.__logger.warn('IcmLibrary search method called with no search criteria')
        else:
            if re.search(project, self.project) and re.search(variant, self.variant) and re.search(libtype, self.libtype):
                retlist.append(self)
      #      elif re.search(project, self.project) and re.search(variant, self.variant) and re.search(libtype, self.libtype):
      #          retlist.append(self)
                         
        return retlist

    def is_library(self):
        return self._type == 'library'

    def is_release(self):
        return self._type == 'release'

    def is_config(self):
        return False

    def flatten_tree(self):
        return [self]

    def get_dot(self):
        '''
        Returns a list of strings, each representing one line
        of dot output representing the configuration.

        :return: Empty list as simple configs aren't included in dot output
        :rtype: list
        '''
        return []

    def is_content_equal(self, other):
        '''
        Performs a comparison of the two configs to see if they're pointing
        at the same IC Manage objects.

        Does not check at the file level

        :param other: The IC Manage configuration we're checking against
        :type other: ICMConfig
        :return: Boolean indicating whether or not the content of the two configs is equal
        :rtype: bool
        '''
        content_equal = False
        if self == other:
            content_equal = True
        else:
            # For readability I'm splitting this if up
            if self.project == other.project and self.variant == other.variant:
                if self.libtype == other.libtype and self.library == other.library:
                    content_equal = self.lib_release == other.lib_release
        return content_equal

    def get_depot_path(self, relchange=False):
        '''
        Returns the depot path to this library/release
        '''
        if self.is_release():
            path = '//depot/gdpxl{}/...{}'.format(os.path.dirname(self._defprops['path']), self._defprops['change'])
        else:
            changenum = '@' + str(self._icm.get_activedev_changenum(self.project, self.variant, self.libtype, self.library))
            path = '//depot/gdpxl{}/...{}'.format(self._defprops['path'], changenum)

        return path

    def __get_altera_path(self, relchange=False):
        '''
        Returns the Altera path to this configuration
        The Altera path takes the format:
        project/variant:libtype/library@release (@changenumber)
        '''
        changenum = self._icm.get_changenum(self.project, self.variant, self.libtype,
                                            self.library, self.lib_release, relchange=relchange)
        path = '{0}/{1}:{2}/{3}@{4} (@{5})'.format(self.project, self.variant, self.libtype,
                                                   self.library, self.lib_release, changenum)
        return path

    def __repr__(self):
        if self.is_release():
            return "{0}/{1}/{2}/{3}/{4}".format(self._project, self._variant, self._libtype, self._library, self._lib_release)
        else:
            return "{0}/{1}/{2}/{3}".format(self._project, self._variant, self._libtype, self._library)

    def __cmp__(self, other):
        return self.key() == other.key()

    def __eq__(self, other):
        return self.key() == other.key()

    def __ne__(self, other):
        return not self.key() == other.key()

    def __hash__(self):
        return hash(self.key())

## @}
