#!/usr/bin/env python

## @addtogroup ecolib
## @{

from builtins import object
import inspect
import sys, os
import logging
import datetime
import dmx.ecolib.deliverable
import dmx.ecolib.loader
import dmx.ecolib.ip
import functools

# For backward compatibility
from dmx.ecolib.__init__ import LEGACY
if not LEGACY:
    from dmx.djangolib.models import *
    from django.db import connection
import dmx.abnrlib.workspace
import dmx.abnrlib.icm
from dmx.utillib.utils import suppress_stdout, split_lc
import dmx.abnrlib.config_factory

LOGGER = logging.getLogger(__name__)

class CellError(Exception): pass

@functools.total_ordering
class Cell(object):  
    def __init__(self, family, ip, cell, workspaceroot=None, workspace=None, preview=True, ipobj=None):
        self._family = family
        self._ip = ip
        self._cell = cell        
        if workspaceroot:
            self._workspaceroot = workspaceroot        
        else:
            self._workspaceroot = os.getcwd()
        self._workspace = workspace
        self._deliverables = []
        self._products = []
        # Internal IP object to speed up operation
        self._ipobj = ipobj

        # This switch determines whether the expensive self._preload() method has been called.
        # If it has been called, then there is no need to call it again. Just return the properties will do.
        self._preloaded = False 
        # Why another variable that is so similar with _preloaded???
        # _preload command loads get_all_deliverables. Sometimes, we only want to load the properties, hence another variable to control that
        self._properties_loaded = False
        
        self._icmproject = None
        self._creator = None
        self._created = None
        self._roadmap = None

        self._icmvariant = ip
        self._preview = preview

    @property
    def name(self):
        return self._cell        

    @property
    def family(self):
        return self._family

    @property
    def ip(self):
        return self._ip      

    @property
    def cell(self):
        return self._cell 

    @property
    def icmproject(self):
        False if self._properties_loaded else self._load_cell_properties()
        return self._icmproject

    @property
    def icmvariant(self):
        return self._icmvariant 
        
    @property
    def creator(self):
        False if self._properties_loaded else self._load_cell_properties()
        return self._creator
        
    @property
    def created(self):
        False if self._properties_loaded else self._load_cell_properties()
        return self._created 
        
    @property
    def roadmap(self):
        False if self._properties_loaded else self._load_cell_properties()
        return self._roadmap                            
           
    ## Preloads local variables
    ## self._deliverables
    ##
    ## @param self The object pointer. 
    def _preload(self, bom=None):
        self._load_cell_properties()
        # Indicate the preload has been run
        # For every other class, self._preloaded is only set at the end of _preload API
        # But for this object, it HAS to be set before calling for self.deliverables
        # Otherwise, the API runs into an infinite loop - to be figured out in the future
        self._preloaded = True
        # If bom is provided to preload API, we read from the bom to return the deliverables
        self._deliverables = self.get_deliverables(bom=bom if bom else None, local=False)

    ## Load cell's properties (icmproject, creator, created, roadmap)
    ##
    ## @param self The object pointer. 
    def _load_cell_properties(self):
        if not self._properties_loaded:
            LOGGER.debug('{}.{}: Querying cell {} properties from ICManage'.format(self.__class__.__name__, inspect.stack()[0][3], self.cell))
            if self._ipobj:
                icmproject = self._ipobj.icmproject
                roadmap = self._ipobj.roadmap
            else:                
                ip = dmx.ecolib.ip.IP(self.family, self.ip)
                icmproject = ip.icmproject
                roadmap = ip.roadmap
                self._ipobj = ip
            # These attributes are defined only in django
            creator = None
            created = None

            self._icmproject = icmproject        
            self._creator = creator
            self._created = created
            self._roadmap = roadmap
            # Indicate properties have been loaded
            self._properties_loaded = True

    ## Returns a list of all Deliverable objects
    ##
    ## @param self The object pointer. 
    ## @param milestone Defaults to 99, 99 means All
    ## @param views Filter by view, view must be a list
    ## @return a list of Deliverable objects
    def get_all_deliverables(self, milestone = '99', views = [], roadmap = ''):
        roadmap = roadmap if roadmap else self.roadmap
        if not roadmap:
            raise CellError('{}.{} requires roadmap option to be specified'.format(self.__class__.__name__, inspect.stack()[0][3]))
        if self._ipobj:
            deliverables = self._ipobj.get_all_deliverables(milestone = milestone, views = views, roadmap=roadmap)
        else:                
            ip = dmx.ecolib.ip.IP(self.family, self.ip)
            ip._preload()
            deliverables = ip.get_all_deliverables(milestone = milestone, views = views, roadmap=roadmap)

        return sorted(list(set(deliverables)))

    ## Returns list of Deliverable objects needed by the cell
    ## By default, this API attempts to read from lcoal workspace
    ## To read from depot, set local to False and set the BOM to read from
    ## To read from the local workspace's BOM (but not from local workspace files),
    ## set local to True and BOM to None
    ##
    ## @param self The object pointer. 
    ## @param bom BOM to search ipspec for in the depot
    ## @param local If True, look for ipspec in the local workspace
    ## @param milestone Defaults to 99, 99 means All
    ## @param views Filter by view, view must be a list
    ## @return a list of Deliverable objects
    def get_deliverables(self, bom=None, local=True, milestone = None, views = [], roadmap = '', delta=False):
        roadmap = roadmap if roadmap else self.roadmap
        if not roadmap:
            raise CellError('{}.{} requires roadmap option to be specified'.format(self.__class__.__name__, inspect.stack()[0][3]))
        bom_deliverables = []
        bom_milestone = ''
        if bom:
            if '@' in bom:
                d, b = split_lc(bom)
                if delta:
                    raise CellError('Delta option does not work with deliverable BOM.')
            else:
                b = bom
                # if delta is true and BOM is an IP BOM
                if delta:
                    cfgobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.icmproject, self.ip, b)
                    bom_deliverables = [x.libtype for x in cfgobj.flatten_tree() if x.is_simple() and x.variant == self.icmvariant]

            reldata = dmx.abnrlib.config_naming_scheme.ConfigNamingScheme().get_data_for_release_config(b)
            # If bom is REL, get the milestone from BOM
            if reldata:
                bom_milestone = reldata['milestone']
        if milestone:
            milestone = milestone
        elif bom_milestone:
            milestone = bom_milestone
        else:
            milestone = '99'
        unneeded_deliverables = [x.deliverable for x in self.get_unneeded_deliverables(bom=bom, local=local, roadmap=roadmap)]
        
        deliverables = [x for x in self.get_all_deliverables(milestone=milestone, views=views, roadmap=roadmap) if x.deliverable not in unneeded_deliverables]

        if delta:
            # If delta is true, return a tuple of (deliverabls, removed_deliverables, added_deliverables)
            # deliverables are expected deliverables objects for this cell
            # added_deliverables are deliverables in string that are added to roadmap but not present in config
            # removed_deliverables are deliverables in string that are removed from roadmap and not marked as unneeded but present in config
            added_deliverables = [x for x in deliverables if x.deliverable not in bom_deliverables] if bom_deliverables else []
            removed_deliverables = [x for x in bom_deliverables if x not in [y.deliverable for y in deliverables] and x not in unneeded_deliverables] if bom_deliverables else []
            ret = (sorted(deliverables, key=lambda deliverable: deliverable.deliverable),
                   sorted(removed_deliverables),
                   sorted(added_deliverables))
        else:            
            ret = sorted(deliverables, key=lambda deliverable: deliverable.deliverable)

        return ret

    ## Returns list of Deliverable objects unneeded by the cell
    ## By default, this API attempts to read from lcoal workspace
    ## To read from depot, set local to False and set the BOM to read from
    ## To read from the local workspace's BOM (but not from local workspace files),
    ## set local to True and BOM to None
    ##
    ## @param self The object pointer. 
    ## @return a list of Deliverable objects
    def get_unneeded_deliverables(self, bom=None, local=True, roadmap=''):
        # As mentioned previously, for legacy method, we are getting cell's info from ICManage workspace
        # For non-legacy, we are getting info from django
        results = []
        if bom and local:
            raise CellError('local and bom options cannot be provided together.')
        roadmap = roadmap if roadmap else self.roadmap        
        if not roadmap:
            raise CellError('{}.{} requires roadmap option to be specified'.format(self.__class__.__name__, inspect.stack()[0][3]))

        cli = dmx.abnrlib.icm.ICManageCLI()
        # local means getting cell names from local workspace
        # otherwise cell names are queried from depot 
        # if bom is given, cell names are queried from the bom
        # else, cell names are queried from the bom used to create the workspace in current working directory
        if local:
            LOGGER.debug('{}.{}: Querying cell {} unneeded deliverables from ICManage workspace'.format(self.__class__.__name__, inspect.stack()[0][3], self.cell))
            if self._workspace:
                ws = self._workspace
            else:                
                with suppress_stdout():
                    ws = dmx.abnrlib.workspace.Workspace(self._workspaceroot)
                    self._workspace = ws
            unneeded_deliverables = ws.get_unneeded_deliverables_for_cell(self.ip, self.cell)
        else:
            ipspec_bom_info = {}
            if bom:
                LOGGER.debug('{}.{}: Querying cell {} unneeded deliverables from BOM {}'.format(self.__class__.__name__, inspect.stack()[0][3], self.cell, bom))
                deliverable = None
                try:
                    deliverable, bom = split_lc(bom)
                except:
                    pass
                if deliverable and deliverable != 'ipspec':
                    raise CellError('Expecting ipspec, got {} instead'.format(deliverable))
                if not deliverable:
                    ipspec_bom_info = cli.get_libtype_library_and_release(self.icmproject, self.icmvariant, bom, libtype='ipspec')                        
                else:
                    if cli.is_name_immutable(bom):
                        ipspec_bom_info['release'] = bom
                        ipspec_bom_info['library'] = cli.get_library_from_release(self.icmproject, self.icmvariant, 'ipspec', bom, retkeys=['name'])
                    else:
                        ipspec_bom_info['release'] = None
                        ipspec_bom_info['library'] = bom

            else:
                LOGGER.debug('{}.{}: Querying cell {} unneeded deliverables from ICManageWorkspace\'s BOM'.format(self.__class__.__name__, inspect.stack()[0][3], self.cell))
                if self._workspace:
                    ws = self._workspace
                else:
                    with suppress_stdout():
                        ws = dmx.abnrlib.workspace.Workspace(self._workspaceroot)
                        self._workspace = ws
                # Get icmanage workspace's config and look for ipspec
                bom = ws.get_workspace_attributes()['config']

                ipspec_bom_info = cli.get_libtype_library_and_release(self.icmproject, self.icmvariant, bom, 'ipspec')
                        
            files = cli.get_dict_of_files(self.icmproject, self.icmvariant, 'ipspec', ipspec_bom_info['release'], ipspec_bom_info['library'])
            unneeded_deliverables_filepath = '{}/{}/{}:{}.{}'.format(self.icmproject, self.icmvariant, 'ipspec', self.cell, 'unneeded_deliverables.txt')
            if unneeded_deliverables_filepath in files:
                unneeded_deliverables_file = files[unneeded_deliverables_filepath]                            
                unneeded_deliverables_filespec = '{}/{}#{}'.format(unneeded_deliverables_file['directory'], unneeded_deliverables_file['filename'], unneeded_deliverables_file['version'])
                unneeded_deliverables = [x.lower() for x in cli.p4_print(unneeded_deliverables_filespec).splitlines() if not x.startswith('//') and not x.startswith('#') and x]
                if not unneeded_deliverables:
                    LOGGER.debug('{} is empty'.format(unneeded_deliverables_filespec))
            else:
                LOGGER.debug('{} does not exist'.format(unneeded_deliverables_filepath))
                unneeded_deliverables = []                

        # http://pg-rdjira:8080/browse/DI-1196
        # Strip empty space
        unneeded_deliverables = [x.strip() for x in unneeded_deliverables]
        for deliverable in self.get_all_deliverables(roadmap=roadmap):
            if deliverable.deliverable in unneeded_deliverables:
                results.append(deliverable)
        
        return sorted(list(set(results)), key=lambda deliverable: deliverable.deliverable)

    ## Returns list of invalid deliverables in unneeded_deliverables.txt in string
    ## By default, this API attempts to read from lcoal workspace
    ## To read from depot, set local to False and set the BOM to read from
    ## To read from the local workspace's BOM (but not from local workspace files),
    ## set local to True and BOM to None
    ##
    ## @param self The object pointer. 
    ## @return a list of deliverables in string
    def get_invalid_unneeded_deliverables(self, bom=None, local=True, roadmap=''):
        # As mentioned previously, for legacy method, we are getting cell's info from ICManage workspace
        # For non-legacy, we are getting info from django
        results = []
        if bom and local:
            raise CellError('local and bom options cannot be provided together.')
        roadmap = roadmap if roadmap else self.roadmap        
        if not roadmap:
            raise CellError('{}.{} requires roadmap option to be specified'.format(self.__class__.__name__, inspect.stack()[0][3]))

        cli = dmx.abnrlib.icm.ICManageCLI()
        # local means getting cell names from local workspace
        # otherwise cell names are queried from depot 
        # if bom is given, cell names are queried from the bom
        # else, cell names are queried from the bom used to create the workspace in current working directory
        if local:
            LOGGER.debug('{}.{}: Querying cell {} unneeded deliverables from ICManage workspace'.format(self.__class__.__name__, inspect.stack()[0][3], self.cell))
            if self._workspace:
                ws = self._workspace
            else:                
                with suppress_stdout():
                    ws = dmx.abnrlib.workspace.Workspace(self._workspaceroot)
                    self._workspace = ws
            unneeded_deliverables = ws.get_unneeded_deliverables_for_cell(self.ip, self.cell)
        else:
            if bom:
                LOGGER.debug('{}.{}: Querying cell {} unneeded deliverables from BOM {}'.format(self.__class__.__name__, inspect.stack()[0][3], self.cell, bom))
                deliverable = None
                try:
                    deliverable, bom = split_lc(bom)
                except:
                    pass
                if deliverable and deliverable != 'ipspec':
                    raise CellError('Expecting ipspec, got {} instead'.format(deliverable))
                if not deliverable:
                    ipspec_bom_info = cli.get_libtype_library_and_release(self.icmproject, self.icmvariant, bom, libtype='ipspec')                        
                else:

                    ipspec_bom_info['release'] = bom
                    ipspec_bom_info['library'] = cli.get_library_from_release(self.icmproject, self.icmvariant, 'ipspec', bom, retkeys=['name'])

            else:
                LOGGER.debug('{}.{}: Querying cell {} unneeded deliverables from ICManageWorkspace\'s BOM'.format(self.__class__.__name__, inspect.stack()[0][3], self.cell))
                if self._workspace:
                    ws = self._workspace
                else:
                    with suppress_stdout():
                        ws = dmx.abnrlib.workspace.Workspace(self._workspaceroot)
                        self._workspace = ws
                ipspec_bom_info = {}
                # Get icmanage workspace's config and look for ipspec
                bom = ws.get_workspace_attributes()['config']

                ipspec_bom_info = cli.get_libtype_library_and_release(self.icmproject, self.icmvariant, bom, 'ipspec')
                        
            files = cli.get_dict_of_files(self.icmproject, self.icmvariant, 'ipspec', ipspec_bom_info['release'], ipspec_bom_info['library'])
            unneeded_deliverables_filepath = '{}/{}/{}:{}.{}'.format(self.icmproject, self.icmvariant, 'ipspec', self.cell, 'unneeded_deliverables.txt')
            if unneeded_deliverables_filepath in files:
                unneeded_deliverables_file = files[unneeded_deliverables_filepath]                            
                unneeded_deliverables_filespec = '{}/{}#{}'.format(unneeded_deliverables_file['directory'], unneeded_deliverables_file['filename'], unneeded_deliverables_file['version'])
                unneeded_deliverables = [x.lower() for x in cli.p4_print(unneeded_deliverables_filespec).splitlines() if not x.startswith('//') and not x.startswith('#') and x]
                if not unneeded_deliverables:
                    LOGGER.debug('{} is empty'.format(unneeded_deliverables_filespec))
            else:
                LOGGER.debug('{} does not exist'.format(unneeded_deliverables_filepath))
                unneeded_deliverables = []                

        valid_deliverables = [x.deliverable for x in self.get_all_deliverables(roadmap=roadmap)]
        for deliverable in unneeded_deliverables:
            if deliverable not in valid_deliverables:
                results.append(deliverable)

        return sorted(list(set(results)))

    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{}".format(self.cell)

    ### needed for python 3
    def __lt__(self, other):
        return self.name < other.name



## @}
