#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/leafbom.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Abstract base class used for representing IC Manage boms. 
See: http://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/ICMConfigurationClass for more details

Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2016
All rights reserved.
'''

## @addtogroup dmxlib
## @{

import logging
import getpass
from datetime import datetime
import re

from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.dmxlib.basebom import BaseBOM
from dmx.abnrlib.flows.snaplibrary import SnapLibrary
from dmx.abnrlib.flows.branchlibrary import BranchLibrary
from dmx.abnrlib.flows.releaselibrary import ReleaseLibrary

class LeafBOMError(Exception):
    pass

class LeafBOM(BaseBOM):
    '''
    Concrete implementation of the ICMConfig base class.

    Represents a simple IC Manage bom
    '''

    def __init__(self, project, ip, deliverable, bom, 
                 library=None, lib_release=None, description='', preview=False):
        '''
        Used to create a new IC Manage simple bom.

        Use ConfigFactory to load a bom from the IC Manage database.
        '''
        if library and lib_release:
            raise LeafBOMError("library/lib_release param no longer supported in gdpxl")
            #self._config = SimpleConfig(bom, project, ip, deliverable, library, lib_release, description, preview)
        else:            
            self._config = ConfigFactory.create_from_icm(project, ip, bom, libtype = deliverable, preview = preview)
        self.logger = logging.getLogger(__name__)

    # Properties
    #
    @property
    def bom(self):
        '''
        The name of the bom
        '''
        return self._config.name

    @bom.setter
    def bom(self, new_bom):
        '''
        Sets the bom name
        '''
        self._config.config = new_bom

    @property
    def project(self):
        '''
        The bom's project
        '''
        return self._config.project

    @project.setter
    def project(self, new_project):
        '''
        Sets the project name
        '''
        self._config.project = new_project

    @property
    def ip(self):
        '''
        The bom's ip
        '''
        return self._config.variant

    @ip.setter
    def ip(self, new_ip):
        '''
        Sets the ip name
        '''
        self._config.variant = new_ip

    @property
    def deliverable(self):
        '''
        The bom's deliverable
        '''
        return self._config.libtype

    @deliverable.setter
    def deliverable(self, new_deliverable):
        '''
        Sets the deliverable
        '''
        self._config.deliverable = new_deliverable

    @property
    def properties(self):
        '''
        The bom's properties
        '''
        return self._config.properties

    @properties.setter
    def properties(self, new_properties):
        '''
        Sets the properties
        '''
        self._config.properties = new_properties 

    @property
    def library(self):
        '''
        The configuration's library
        '''
        return self._config.library

    @library.setter
    def library(self, new_library):
        '''
        Sets the library
        '''
        self._config.library = new_library

    @property
    def lib_release(self):
        '''
        The configuration's release
        '''
        return self._config.lib_release

    @lib_release.setter
    def lib_release(self, new_lib_release):
        '''
        Sets the lib_release
        '''
        self._config.lib_release = new_lib_release

    @property
    def description(self):
        '''
        The configuration's description
        '''
        return self._config.description

    @description.setter
    def description(self, new_description):
        '''
        Sets the description
        '''
        self._config.description = new_description

    @property
    def preview(self):
        '''
        Return the preview flag
        :return: The preview flag
        :type return: bool
        '''
        return self._config.preview

    @preview.setter
    def preview(self, new_preview):
        '''
        Sets the preview mode and reflects that change
        to the ICManageCLI object
        :param new_preview: New preview setting
        :type preview: bool
        '''
        self._config.preview = new_preview

    #
    # Methods
    #
    def clone(self, name):
        '''
        Create a clone of the bom called name

        :param name: The name of the clone bom
        :type name: str
        :return: The cloned bom object
        :rtype: LeafBOM
        :raises: LeafBOMError
        '''      
        ret = 1  
        # Why don't we check? SimpleConfig.clone already handles the check..
        cloned_config = self._config.clone(name)
        if cloned_config.save():
            bom = LeafBOM(cloned_config.project, cloned_config.variant, cloned_config.libtype, cloned_config.config)            
            self.logger.info('{0}/{1}:{2}@{3} successfully cloned to {0}/{1}:{2}@{4}'.format(
                self.project, self.ip, self.deliverable, self.bom, name))
            ret = bom
        return ret            

    def branch(self, branch_name, description='', target_project='', target_ip='', 
               target_bom=''):
        ret = 1
        branch_config = BranchLibrary(self.project, self.ip, self.deliverable, self.bom, branch_name,
            target_project=target_project, target_variant=target_ip, target_config=target_bom, 
            description=description, preview=self.preview).run()
        if isinstance(branch_config, IcmLibrary):
            ret = LeafBOM(branch_config.project, branch_config.variant, branch_config.libtype, branch_config.config)    
        return ret            

    def delete(self):
        '''
        Removes this bom from the IC Manage database.

        Ignore shallow as it only applies to composite boms.

        :param shallow: Ignored for simple boms.
        :type shallow: None
        :return: Boolean indicating success or failure of deletion
        :rtype: bool
        '''
        return self._config.delete()

    def create(self):
        if self.library and self.lib_release:
            return self._config.save()
        else:
            raise LeafBOMError('{}/{}:{}@{} already exists.'.format(self.project, self.ip,
                self.deliverable, self.bom))

    def update(self):
        return self._config.save()

    def format_contents_to_file(self):
        '''
        Not supported at the moment
        '''
        pass        

    def contents(self):
        return self

    def check(self):
        ret = 1
        errors = self._config.validate()
        if errors:
            for error in errors:
                print(error)
            raise LeafBomError('There are {} errors found with {}'.format(len(errors, self)))
        ret = 0            
        return ret        

    def snap(self, snap_name):
        ret = 1
        snap_config = SnapLibrary(self.project, self.ip, self.deliverable, self.bom, snap_name, preview=self.preview).run()        
        if isinstance(snap_config, IcmLibrary):
            ret = LeafBOM(snap_config.project, snap_config.variant, 
                          snap_config.libtype, snap_config.config)                
                                        
        return ret                

    def release(self, milestone, thread, description, label='', ipspec=None,
                wait=False, waiver_files=None,
                force=False):
        '''
        Runs the release flow - entry point for the class
        '''        
        ret = 1
        releaselib = ReleaseLibrary(self.project, self.ip, self.deliverable, self.bom, 
                                milestone, thread, description, label=label, 
                                ipspec=ipspec, wait=wait, 
                                waiver_files=waiver_files, force=force, 
                                preview=self.preview)
        ret = releaselib.run()
        if wait and not ret:
            ret = LeafBOM(releaselib.rel_config.project, 
                          releaselib.rel_config.variant,
                          releaselib.rel_config.libtype,
                          releaselib.rel_config.config,
                          preview=self.preview)

        return ret
        
    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{0}/{1}:{2}@{3}".format(self.project, self.ip, self.deliverable, self.bom)

    def __hash__(self):
        '''
        Returns a hash of this object
        '''
        return hash(self.key())

## @}
