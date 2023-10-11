#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/config_factory.py#3 $
$Change: 7639121 $
$DateTime: 2023/06/01 01:42:39 $
$Author: lionelta $

Description: Factory class for creating SimpleConfig and CompositeConfig objects
in a generic way.

Author: Lee Cartwright
Copyright (c) Altera Corporation 2015
All rights reserved.
'''

## @addtogroup dmxlib
## @{

from builtins import object
import dmx.abnrlib.icmconfig
import dmx.abnrlib.icmlibrary
from dmx.abnrlib.icm import ICManageCLI, convert_gdpxl_config_name_to_icm, convert_config_name_to_icm
import logging


class ConfigFactoryError(Exception): pass

class ConfigFactory(object):
    '''
    Factory class for creating IC Manage config objects
    '''

    LOGGER = logging.getLogger(__name__)

    ### static lookup table for every instance of the class
    ### Purpose of this table is so that, every time an IcmLibrary/IcmConfig object has been created, 
    ### we can just make use of the ConfigFactory.add_configuration() method to add that object into this
    ### lookupt table, and then if we need them, we can call ConfigFactory.get_configuration() to retrieve it.
    ### By doing so, we save a lot of overhead cost from the need to always use create_from_icm(), which will 
    ### hit the server load.
    obj_table = dict()

    @classmethod
    def create_config_from_full_name(cls, full_name, preview=False):
        '''
        Creates a configuration object from the full IC Manage name

        :param full_name: Configuration name in the conventional gdp format:- 
                                project/variant[:libtype]@config format
                          or gdpxl format
                                project/variant/config
                                project/variant/libtype/library
                                project/variant/libtype/library/release
        :type full_Name: str
        :param preview: Flag indicating how to set the preview flag in the config objects
        :type preview: bool
        :return: Corresponding IC Manage configuration object
        :type return: ICMConfig
        '''
        config_object = None
       
        ### We support both gdp format and gdpxl format
        ### - gdp format: project/variant[:libtype]@config
        ### - gdpxl format: project/variant/config -or- project/variant/libtype/library -or- project/variant/libtype/library/release
        if '@' in full_name:
            config_details = convert_config_name_to_icm(full_name)
        else:
            config_details = convert_gdpxl_config_name_to_icm(full_name)

        if not config_details:
            raise ConfigFactoryError('Problem converting {0} into IC Manage components'.format(full_name))

        if 'libtype' in config_details:
            config_object = ConfigFactory.create_from_icm(config_details['project'],
                                                          config_details['variant'],
                                                          config_details['config'],
                                                          libtype=config_details['libtype'],
                                                          preview=preview)
        else:
            config_object = ConfigFactory.create_from_icm(config_details['project'],
                                                          config_details['variant'],
                                                          config_details['config'],
                                                          preview=preview)

        return config_object

    @classmethod
    def create_from_icm(cls, project, variant, config_or_library_or_release='', libtype='', preview=False):
        '''
        Creates an IC Manage configuration based upon the data within IC Manage

        config_or_library_or_release 
        ----------------------------
        This input param needs some explanation.
        For a detail explanation of the input of config_or_library_or_release:-
            https://wiki.ith.intel.com/display/tdmaInfra/ICM+-+GDPXL+object+mappings#ICMGDPXLobjectmappings-#1.config/library/release

        Basically, in order to retain backward compatibility to most of the 'dmx commands' which uses 
            -p PRO -i IP -d DEL -b BOM
        we need to map that into GDPXL.
    
        So, if
        - (project, variant, config_or_library_or_release) is provided
        - (libtype) is not provided
        config_or_library_or_release == GDPXL config

        if 
        - (project, variant, config_or_library_or_release, libtype) is provided
          > if config_or_library_or_release == immutable (ie:- starts with REL/PREL/snap-)
              config_or_library_or_release == release
              library == will be gotten thru API, no need to be provided as a release is unique across the entire libtype's libraries.
          > if config_or_library_or_release == mutable
              config_or_library_or_release == library

        '''
        obj = None

        if libtype:
            icm = ICManageCLI()
            library = ''
            release = ''
            if icm.is_name_immutable(config_or_library_or_release):
                release = config_or_library_or_release
                library = icm.get_library_from_release(project, variant, libtype, release)
            else:
                library = config_or_library_or_release
            obj = dmx.abnrlib.icmlibrary.IcmLibrary(project, variant, libtype, library, release, preview=preview)
        else:
            config = config_or_library_or_release
            obj = cls.__build_hierarchical_icmconfig(project, variant, config, preview=preview)

        if not obj:
            raise ConfigFactoryError("Failed creating config_factory object for {}/{}/{}/{}. Make sure that object exists in gdpxl.".format(project, variant, libtype, config_or_library_or_release))
        obj.preview = preview
        return obj

    @classmethod
    def __build_hierarchical_icmconfig(cls, project, variant, config, preview=False):
        '''
        metadata ==
        ... ... ...
        {                                                                                                                                                                                                                                                                   
            "location": "liotestfc1/reldoc",
            "uri": "p4://scyapp37.sc.intel.com:1666/depot/gdpxl/intel/i10socfm/liotestfc1/reldoc/dev/...",
            "created-by": "lionelta",
            "id": "L1247121",
            "type": "library",
            "name": "dev",
            "path": "/intel/i10socfm/liotestfc1/reldoc/dev",
            "created": "2020-09-23T10:06:57.013Z",
            "modified": "2020-09-23T10:06:57.013Z",
            "change": "@now",
            "libtype": "reldoc"
        },
        ... ... ...


        linkdata ==
        ... ... ...
        {
            "path": "/intel/i10socfm/liotestfc1/sta/dev",
            "content:link:path": []
        },
        {
            "path": "/intel/i10socfm/liotest1/dev",
            "content:link:path": [
                "/intel/i10socfm/liotest1/ipspec/dev",
                "/intel/i10socfm/liotest1/reldoc/dev",
                "/intel/i10socfm/liotest1/rdf/dev",
                "/intel/i10socfm/liotest1/sta/dev",
                "/intel/i10socfm/liotest3/dev"
            ]
        },
        ... ... ...
        '''
        cli = dmx.abnrlib.icm.ICManageCLI(site='intel', preview=preview)
        metadata = cli.get_config_content_details(project, variant, config, hierarchy=True)  # details of each self+children config 
        linkdata = cli.get_parent_child_relationship(project, variant, config, hierarchy=True) # children info of each self+children config 
        
        ### Create all IcmLibrary and IcmConfig objects (without child/parent data)
        objtable = {}
        rootobj = ''
        for defprop in metadata:
            if defprop['type'] == 'config':
                obj = dmx.abnrlib.icmconfig.IcmConfig(defprop_from_icm=defprop, preview=preview)
                objtable[obj._defprops['path']] = obj
                if '/{}/{}/'.format(project, variant) in defprop['path']:
                    rootobj = obj
            else:
                obj = dmx.abnrlib.icmlibrary.IcmLibrary(defprop_from_icm=defprop, preview=preview)
                objtable[obj._defprops['path']] = obj

        ### Now, add children/parent for each of the IcmConfig
        for parent in linkdata:
            parentobj = objtable[parent['path']]
            for childpath in parent['content:link:path']:
                childobj = objtable[childpath]
                parentobj.add_object(childobj)

        ### Now, set all the objects to their correct state.
        for path, obj in objtable.items():
            obj._saved = True
            obj._in_db = True
            if obj.is_config():
                obj._saved_configurations = list(obj.configurations)

        return rootobj


    @classmethod
    def remove_all_objs(cls):
        ConfigFactory.obj_table = {}
        if ConfigFactory.obj_table:
            return False
        else:
            return True

    @classmethod
    def add_obj(cls, obj):
        '''
        Adds an IcmLibrary/IcmConfig object to the configuration lookup table
        If there is already a matched object, raise an error.
        '''
        if obj.key() in ConfigFactory.obj_table:
            raise ConfigFactoryError('An entry for {} already exists in the factory lookup table.'.format(obj.get_full_name()))
        else:
            ConfigFactory.obj_table[obj.key()] = obj

    @classmethod
    def remove_obj(cls, obj):
        if obj.key() in ConfigFactory.obj_table:
            del ConfigFactory.obj_table[obj.key()]

    @classmethod
    def get_obj(cls, project, variant, config_or_library_or_release, libtype=None):
        '''
        Retrieve the IcmLibrary/IcmConfig obj from the look up table.
        If it doesn't exist, 
        - create_from_icm() it, 
        - add it into the lookup table
        - return the obj
        '''
        if libtype:
            key = (project, variant, libtype, config_or_library_or_release)
        else:
            key = (project, variant, config_or_library_or_release)
        if key in ConfigFactory.obj_table:
            return ConfigFactory.obj_table[key]
        else:
            obj = ConfigFactory.create_from_icm(project, variant, config_or_library_or_release, libtype)
            ConfigFactory.add_obj(obj)
            return obj

    @classmethod
    def get_deliverable_type_from_config_factory_object(self, cf, config_type):
        '''
        Get mutable/immutable devlierable from workspace
        '''
        #os.chdir(self.wsroot)
        #ws = dmx.abnrlib.workspace.Workspace()
        #cf = ws.get_config_factory_object()

        mutable_path = []
        immutable_path = []
        variant_info = {}

        for conf in cf.flatten_tree():
            if not conf.is_config(): 
                if (config_type == 'mutable' and conf.is_mutable()) or (config_type == 'immutable' and not conf.is_mutable()):
                    if variant_info.get(conf._variant):
                        variant_info[conf._variant].append(conf._libtype)
                    else:
                        variant_info[conf._variant] = [conf._libtype]

        return variant_info

## @}
