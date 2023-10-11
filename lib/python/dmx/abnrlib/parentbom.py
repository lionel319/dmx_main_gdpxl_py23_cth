#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/parentbom.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Concrete implementation of the abstract base class ICMConfig for use with composite boms
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
import json

from dmx.dmxlib.basebom import BaseBOM
from dmx.dmxlib.leafbom import LeafBOM
from dmx.abnrlib.icm import ICManageCLI, ICManageError
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.flows.snaptree import SnapTree
from dmx.abnrlib.flows.branchlibraries import BranchLibraries
from dmx.abnrlib.flows.releasevariant import ReleaseVariant
from dmx.abnrlib.flows.releasetree import ReleaseTree
#from dmx.abnrlib.flows.releaselibraries import ReleaseLibraries
from dmx.abnrlib.flows.checkconfigs import CheckConfigs

class ParentBOMError(Exception):
    pass

class ParentBOM(BaseBOM):
    '''
    Concrete implementation of the ICMConfig base class
    Represents a composite IC Manage bom
    '''
        
    def __init__(self, project, ip, bom, boms=[], description='',
                 preview=False):
        '''
        Initialiser
        '''
        if boms:
            raise ParentBOMError("boms: param no longer supported.")
            #self._config = CompositeConfig(bom, project, ip, boms, description, preview) 
        else:           
            self._config = ConfigFactory.create_from_icm(project, ip, bom, preview = preview)
        self.cli = ICManageCLI(preview=preview)
        self.logger = logging.getLogger(__name__)        
        self.boms = []
        
        if not boms:
            for config in self._config.configurations:
                if not config.is_config():
                    self.boms.append(LeafBOM(config.project, config.variant, config.libtype, config.name, preview=preview))
                else:
                    self.boms.append(ParentBOM(config.project, config.variant, config.config, preview=preview))                
 
    #
    # Properties
    #
    @property
    def bom(self):
        '''
        The name of the bom
        '''
        return self._config.config

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

    def clone(self, name, tree=False, simple=False, immutable=False):
        '''
        Create a clone of the bom called name.

        Does not save it to IC Manage.

        :param name: The name of the new bom.
        :type name: str
        :return: The cloned bom
        :rtype: ParentBOM
        :raises: ParentBOMError
        '''
        ret = 1  
        # Why don't we check? CompositeConfig.clone already handles the check..
        if tree:
            cloned_config = self._config.clone_tree(name, simple, immutable)
        else:            
            cloned_config = self._config.clone(name)
        if cloned_config.save():
            bom = ParentBOM(cloned_config.project, cloned_config.variant, cloned_config.config)
            self.logger.info('{0}/{1}@{2} successfully cloned to {0}/{1}@{3}'.format(
                self.project, self.ip, self.bom, name))
            ret = bom
        return ret

    def delete(self):
        '''
        Removes this bom from the IC Manage database

        If shallow=False removes all boms in the tree from
        the IC Manage database too.

        :param shallow: Boolean indicating whether or not the delete is shallow.
        :type shallow: bool
        :return: Boolean indicating success or failure
        :rtype: bool
        :raises: ParentBOMError
        '''
        return self._config.delete()

    def create():
        '''
        Saves every bom in the bom tree that needs it.

        Must be performed depth first.

        Validates the bom tree before saving.

        :param shallow: Boolean indicating whether to save just this bom or the entire tree
        :type shallow: bool
        :return: Boolean indicating success or failure
        :rtype: bool
        :raises: ParentBOMError
        '''
        if self._config.configurations:
            return self._config.save()
        else:
            raise ParentBOMError('{}/{}@{} already exists.'.format(self.project, self.ip,
                self.bom))

    def update(self):
        return self._config.save()

    def format_contents_to_file(self, jsonfile=''):
        if jsonfile:
            data = {}
            def build_json(data, bom):
                if str(bom) not in data:
                    data[str(bom)] = {}
                    data[str(bom)]['deliverable'] = []
                    data[str(bom)]['ip'] = []
                for b in bom.boms:
                    if type(b) == LeafBOM:
                        data[str(bom)]['deliverable'].append(str(b))
                    else:
                        data[str(bom)]['ip'].append(str(b))                    
                        build_json(data, b)
                data[str(bom)]['deliverable'] = sorted(list(set(data[str(bom)]['deliverable'])))
                data[str(bom)]['ip'] = sorted(list(set(data[str(bom)]['ip'])))
            build_json(data, self) 
                       
            with open(jsonfile, 'w') as f:
                json.dump(data, f, indent=4, sort_keys=True)

    def contents(self, flatten=False, include_leaf=False):
        results = []
        if not flatten:
            results = self.boms
        else:   
            def parse_bom(self, include_leaf, bom, results):
                for bom in bom.boms:
                    if type(bom) == LeafBOM:
                        if bom.project == self.project and bom.ip == self.ip:
                            results.append(bom)
                        else:
                            if include_leaf:
                                results.append(bom)                            
                    elif type(bom) == ParentBOM:
                        results.append(bom)
                        parse_bom(self, include_leaf, bom, results)
            parse_bom(self, include_leaf, self, results)
        
        return results

    def check(self, syncpoints=[]):
        ret = 1
        check = CheckConfigs(self.project, self.ip, self.bom, syncpoints, self.preview)
        ret = check.run()
        return ret        

    def branch(self, branch_name, libtypes=[], description='', reuse=False, exact=False):
        ret = 1
        branch_config = BranchLibraries(self.project, self.ip, self.bom, branch_name, libtypes=libtypes, description=description, reuse=reuse, exact=exact, preview=self.preview).run()
        if isinstance(branch_config, IcmConfig):
            ret = ParentBOM(branch_config.project, branch_config.variant, branch_config.config)    

        return ret            

    def snap(self, snap_name, description='', reuse=False, variants=[], libtypes=[], changelist=0):
        ret = 1
        snap_config = SnapTree(self.project, self.ip, self.bom, snap_name, libtypes=libtypes, variants=variants, description=description, reuse=reuse, changelist=changelist, preview=self.preview).run()
        if isinstance(snap_config, IcmConfig):
            ret = ParentBOM(snap_config.project, snap_config.variant, snap_config.config)    
        
        return ret

    def release(self, milestone, thread, description, label=None,    
                wait=False, waiver_files=None,
                force=False, required_only=False, intermediate=False,
                tree=False, variant_filter=[], libtype_filter=[], inplace=True,
                new_config=None, release_snap=False, libsonly=False):
        '''
        Runs the release flow - entry point for the class
        '''        
        ret = 1
        if tree:
            releasetree = ReleaseTree(self.project, self.ip, self.bom, milestone, thread, 
                                      description, label=label, required_only=required_only,
                                      intermediate=intermediate,
                                      waiver_files=waiver_files,
                                      force=force, preview=self.preview)
            ret = releasetree.run()
            if not ret:
                ret = ParentBOM(releasetree.rel_config.project, 
                                releasetree.rel_config.variant,
                                releasetree.rel_config.config,
                                preview=self.preview)                        
        elif libsonly:
            raise ParentBOMError("ReleaseLibriaries no longer supported.")
            '''
            releaselibsintree = ReleaseLibraries(self.project, self.ip, self.bom, milestone, 
                                                  thread, description, label=label, 
                                                  variant_filter=variant_filter,
                                                  libtype_filter=libtype_filter,
                                                  inplace=inplace, new_config=new_config,
                                                  waiver_files=waiver_files,
                                                  force=force, release_snap=release_snap,
                                                  preview=self.preview)
            ret = releaselibsintree.run()
            if not ret:
                ret = ParentBOM(ret.project, 
                                ret.variant,
                                ret.config,
                                preview=self.preview)           
            '''
        else:
            releasevar = ReleaseVariant(self.project, self.ip, self.bom, milestone, thread, 
                                    description, label=label,  
                                    wait=wait, waiver_files=waiver_files,
                                    force=force, preview=self.preview)
            ret = releasevar.run()
            if wait and not ret:
                ret = ParentBOM(releasevar.rel_config.project, 
                                releasevar.rel_config.variant,
                                releasevar.rel_config.config,
                                preview=self.preview)

        return ret

    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{0}/{1}@{2}".format(self.project, self.ip, self.bom)

    def __hash__(self):
        '''
        Returns a hash of this object
        '''
        return hash(self.key())

## @}
