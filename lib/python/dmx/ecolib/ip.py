#!/usr/bin/env python
## @addtogroup ecolib
## @{

''' axc
This is documentation

@author Lionel Tan, Kevin Lim
@image html dmx.ecolib.png 

-the end-
'''

import inspect
import sys, os
import re
import logging
import datetime
import dmx.ecolib.family
import dmx.ecolib.cell
import dmx.ecolib.iptype 
from dmx.utillib.multiproc import run_mp
from dmx.utillib.utils import suppress_stdout, user_exists, split_lc, is_pice_env
from dmx.utillib.arcenv import ARCEnv
import dmx.abnrlib.config_naming_scheme

import dmx.abnrlib.workspace
import dmx.abnrlib.icm 
import dmx.abnrlib.config_factory

LOGGER = logging.getLogger(__name__)

class IPError(Exception): pass

class IP(dmx.ecolib.iptype.IPType):  
    def __init__(self, family, ip, workspaceroot=None, workspace=None, preview=True, icmproject=None, roadmap=None):
        self._family = family
        self._ip = ip
        if workspaceroot:
            self._workspaceroot = workspaceroot        
        else:
            self._workspaceroot = os.getcwd()
        self._workspace = workspace
        self._preview = preview
                
        self._icmvariant = ip    
        self._deliverables = {}
        
        # This switch determines whether the expensive self._preload() method has been called.
        # If it has been called, then there is no need to call it again. Just return the properties will do.
        self._preloaded = False 
        # Why another variable that is so similar with _preloaded???
        # _preload command loads get_all_deliverables. Sometimes, we only want to load the properties, hence another variable to control that
        self._properties_loaded = False

        # Why don't we get the properties when the object is created?
        # Because the pm calls are expensive and slow
        # To get the properties, self.preload needs to be run
        self._icmproject = icmproject                
        self._owner = None
        self._iptype = None
        self._created = None
        self._last_updated = None
        self._products = None
        self._roadmap = roadmap

    @property
    def name(self):
        return self._ip        
        
    @property
    def family(self):
        return self._family

    @property
    def products(self):
        False if self._properties_loaded else self._load_ip_properties()
        return self._products

    @property
    def ip(self):
        return self._ip        

    @property
    def owner(self):
        False if self._properties_loaded else self._load_ip_properties()
        return self._owner
    
    @property
    def iptype(self):
        False if self._properties_loaded else self._load_ip_properties()
        return self._iptype

    @property
    def created(self):
        False if self._properties_loaded else self._load_ip_properties()
        return self._created
        
    @property
    def last_updated(self):
        False if self._properties_loaded else self._load_ip_properties()
        return self._last_updated

    @property
    def icmproject(self):
        False if self._properties_loaded else self._load_ip_properties()
        return self._icmproject        

    @property
    def icmvariant(self):
        return self._icmvariant        

    @property
    def roadmap(self):
        False if self._properties_loaded else self._load_ip_properties()
        return self._roadmap
    
    # Preloads local variables
    ## self._deliverables
    ##
    ## @param self The object pointer. 
    def _preload(self):
        self._load_ip_properties()           
        # Some IPs doesn't have iptype (mainly in pm propval), no choice but to skip over it
        if self._iptype:            
            self._deliverables = self._get_deliverables(roadmap=self._roadmap)
        # Indicate the preload has been run
        self._preloaded = True            

    ## Returns a list of Deliverable objects that are registered as unneeded for the Product/IP
    ## By default, this API attempts to read from lcoal workspace
    ## To read from depot, set local to False and set the BOM to read from
    ## To read from the local workspace's BOM (but not from local workspace files),
    ## set local to True and BOM to None
    ##
    ## @param self The object pointer. 
    ## @param product Product
    ## @param bom BOM to search ipspec for in the depot
    ## @param local If True, look for ipspec in the local workspace
    ## @return list of Deliverable objects
    def get_unneeded_deliverables(self, product=None, bom=None, local=True, roadmap=''):
        results = set()
        roadmap = roadmap if roadmap else self.roadmap
        if not roadmap:
            raise IPError('{}.{} requires roadmap option to be specified'.format(self.__class__.__name__, inspect.stack()[0][3]))
        for num, cell in enumerate(self.get_cells_names(product_filter = product, bom=bom, local=local)):
            cell = self.get_cell(cell, bom=bom, local=local)
            unneeded_deliverables = [x for x in cell.get_unneeded_deliverables(bom=bom, local=local, roadmap=roadmap)]
            if not num:
                results = set(unneeded_deliverables)
            else:
                results = results.intersection(set(unneeded_deliverables))

        return sorted(list(results))

    ## Returns a list of invalid deliverables in *.unneeded_deliverables.txt in string
    ## By default, this API attempts to read from lcoal workspace
    ## To read from depot, set local to False and set the BOM to read from
    ## To read from the local workspace's BOM (but not from local workspace files),
    ## set local to True and BOM to None
    ##
    ## @param self The object pointer. 
    ## @param product Product
    ## @param bom BOM to search ipspec for in the depot
    ## @param local If True, look for ipspec in the local workspace
    ## @return list of deliverables in string
    def get_invalid_unneeded_deliverables(self, product=None, bom=None, local=True, roadmap=''):
        results = set()
        roadmap = roadmap if roadmap else self.roadmap
        if not roadmap:
            raise IPError('{}.{} requires roadmap option to be specified'.format(self.__class__.__name__, inspect.stack()[0][3]))
        results = []            
        for cell in self.get_cells(product_filter = product, bom=bom, local=local):
            results = results + [x for x in cell.get_invalid_unneeded_deliverables(bom=bom, local=local, roadmap=roadmap)]

        return sorted(list(set(results)))

    ## Returns a list of Deliverable objects that are needed
    ## By default, this API attempts to read from lcoal workspace
    ## To read from depot, set local to False and set the BOM to read from
    ## To read from the local workspace's BOM (but not from local workspace files),
    ## set local to True and BOM to None
    ##
    ## @param self The object pointer. 
    ## @param product Product
    ## @param bom BOM to search ipspec for in the depot
    ## @param local If True, look for ipspec in the local workspace
    ## @param deliverable_filter Filter by deliverable
    ## @param milestone Defaults to 99, 99 means All
    ## @param views Filter by view, view must be a list
    ## @return list of Deliverable objects
    def get_deliverables(self, bom=None, local=True, deliverable_filter='', milestone=None, views=None, roadmap='', delta=False, prels=None):
        results = set()
        roadmap = roadmap if roadmap else self.roadmap
        if not roadmap:
            raise IPError('{}.{} requires roadmap option to be specified'.format(self.__class__.__name__, inspect.stack()[0][3]))  
        bom_deliverables = []
        bom_milestone = ''
        if bom:
            if '@' in bom:
                d, b = split_lc(bom)
                if delta:
                    raise IPError('Delta option does not work with deliverable BOM.')
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
        all_deliverables = self.get_all_deliverables(deliverable_filter=deliverable_filter, milestone=milestone, views=views, roadmap=roadmap, prels=prels)
        unneeded_deliverables = self.get_unneeded_deliverables(bom=bom, local=local, roadmap=roadmap)
        needed_deliverables = list(set([x.deliverable for x in all_deliverables]) - set([x.deliverable for x in unneeded_deliverables]))
        results = [x for x in all_deliverables if x.deliverable in needed_deliverables]
        
        if delta:
            # If delta is true, return a tuple of (deliverabls, removed_deliverables, added_deliverables)
            # deliverables are expected deliverables objects for this cell
            # added_deliverables are deliverables objects that are added to roadmap but not present in config
            # removed_deliverables are deliverables in string that are removed from roadmap and not marked as unneeded but present in config
            added_deliverables = [x for x in results if x.deliverable not in bom_deliverables] if bom_deliverables else []
            removed_deliverables = [x for x in bom_deliverables if x not in [y.deliverable for y in results] and x not in unneeded_deliverables] if bom_deliverables else []
            ret = (sorted(results, key=lambda deliverable: deliverable.deliverable),
                   sorted(removed_deliverables),
                   sorted(added_deliverables))
        else:            
            ret = sorted(list(results))

        return ret

    ## Returns a list of cells strings (useful if get_cells takes too long)
    ## get_cells initializes the objects and all its properties and takes a long time if run from SJ 
    ## since server is in PG. To remedy, use get_cells_name instead and instantiate the needed object via get_cell
    ## By default, this API attempts to read from lcoal workspace
    ## To read from depot, set local to False and set the BOM to read from
    ## To read from the local workspace's BOM (but not from local workspace files),
    ## set local to True and BOM to None
    ##
    ## @param self The object pointer. 
    ## @param cell_filter Filter by cellname
    ## @param product_filter Filter by product
    ## @param bom library name to search ipspec for in the depot
    ## @param local If True, look for ipspec in the local workspace
    ## @return list of Cell strings
    def get_cells_names(self, cell_filter = None, product_filter = None, bom = None, local = True):   
        results = []
        if bom and local:
            raise IPError('local and bom options cannot be provided together.')
                
        cli = dmx.abnrlib.icm.ICManageCLI()
        # local means getting cell names from local workspace
        # otherwise cell names are queried from depot 
        # if bom is given, cell names are queried from the bom
        # else, cell names are queried from the bom used to create the workspace in current working directory
        if local:
            LOGGER.debug('{}.{}: Querying IP {} cells from ICManageWorkspace'.format(self.__class__.__name__, inspect.stack()[0][3], self._ip))
            if self._workspace:
                ws = self._workspace
            else:
                with suppress_stdout():
                    ws = dmx.abnrlib.workspace.Workspace(self._workspaceroot)
                    self._workspace = ws
            cells = ws.get_cells_for_ip(self._ip)
            if not cells:
                cellnames_filespec = '{}/{}/ipspec/cell_names.txt'.format(self._workspace._workspaceroot, self._ip)
                raise IPError('{} is empty'.format(cellnames_filespec))
        else:                
            ipspec_bom_info = {}
            if bom:
                LOGGER.debug('{}.{}: Querying IP {} cells from BOM {}'.format(self.__class__.__name__, inspect.stack()[0][3], self._ip, bom))
                deliverable = None
                try:
                    deliverable, bom = split_lc(bom)
                except:
                    pass
                if deliverable and deliverable != 'ipspec':
                    raise IPError('Expecting ipspec, got {} instead'.format(deliverable))
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
                LOGGER.debug('{}.{}: Querying IP {} cells from ICManageWorkspace\'s BOM'.format(self.__class__.__name__, inspect.stack()[0][3], self._ip))
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
            cellname_filepath = '{}/{}/{}:{}'.format(self.icmproject, self.icmvariant, 'ipspec', 'cell_names.txt')

            if cellname_filepath in files:
                cellnames_file = files[cellname_filepath]
                cellnames_filespec = '{}/{}#{}'.format(cellnames_file['directory'], cellnames_file['filename'], cellnames_file['version'])
                cells = [x.strip() for x in cli.p4_print(cellnames_filespec).splitlines() if not x.startswith('//') and not x.startswith('#') and x]
                if not cells:
                    raise IPError('{} is empty'.format(cellnames_filespec))
            else:
                raise IPError('{} does not exist'.format(cellname_filepath))
       
        for cell in cells:
            m = re.match(cell_filter if cell_filter else '.*', cell)
            if m:
                results.append(cell)

        # http://pg-rdjira:8080/browse/DI-1069
        # Cells not allowed to have upper case
        invalid_cells = []
        for result in results:
            has_upper = True if [x for x in result if x.isupper()] else False
            if has_upper:
                invalid_cells.append(result)
        if invalid_cells:
            LOGGER.error('Cells with upper cases found in ipspec for {}/{}:'.format(self.icmproject, self.icmvariant))
            for cell in invalid_cells:
                LOGGER.error('* {}'.format(cell))
            raise IPError('Cells are not allowed with upper cases.')  

        return sorted(list(set(results)))

    ## Returns a list of Cell objects that matches the filters
    ## By default, this API attempts to read from lcoal workspace
    ## To read from depot, set local to False and set the BOM to read from
    ## To read from the local workspace's BOM (but not from local workspace files),
    ## set local to True and BOM to None
    ##
    ## @param self The object pointer. 
    ## @param cell_filter Filter by cellname
    ## @param product_filter Filter by product
    ## @param bom BOM to search ipspec for in the depot
    ## @param local If True, look for ipspec in the local workspace
    ## @return list of Cell objects    
    def get_cells(self, cell_filter = None, product_filter = None, bom = None, local = True):
        results = []

        cells = self.get_cells_names(cell_filter = cell_filter, product_filter = product_filter, bom = bom, local = local)
        unique_cells = []
        for cell in cells:
            m = re.match(cell_filter if cell_filter else '.*', cell)
            if m:
                unique_cells.append(cell)

        for cell in unique_cells:
            results.append(dmx.ecolib.cell.Cell(self.family, self._ip, cell, 
                            self._workspaceroot,
                            self._workspace,
                            self._preview,
                            ipobj=self))
            
        return sorted(list(set(results)), key=lambda cell: cell.cell)
    
    # Returns a Cell object that matches the cellname
    ##
    ## @param self The object pointer. 
    ## @param cell Cell name
    ## @exception dmx::ecolib::ip::IPError Raise if cell name contains illegal characters, cell cannot be found
    ## @return Cell object
    def get_cell(self, cell, bom = None,  local = True):
        if re.search('[^A-Za-z0-9_]', cell):
            raise IPError('Cell can contain only alphabets, numbers and underscores. "{}"'.format(cell))

        # run_mp is causing threads to get stuck and hung
        # for the time being, instantiate the object on our own 
        results = self.get_cells_names('^{}$'.format(cell), bom=bom, local=local)
        if results:
            results = [dmx.ecolib.cell.Cell(
                           self.family, self._ip, cell, 
                           self._workspaceroot,
                           self._workspace,
                           self._preview,
                           ipobj=self)]

        if results:
            return results[0]
        else:
            LOGGER.error('Cell {} does not exist'.format(cell))
            raise IPError('Valid cells for IP {}/{} are: {}'.format(self.family, self._ip, self.get_cells_names(bom=bom, local=local))) 
       
    def get_iptype(self, properties):
        '''
        properties == output from ICManageCLI().get_variant_properties()

        if "iptype_override" property contains matching "$family:$type", 
            return $type
        else:
            if "iptype" exist:
                return value from "iptype"
            else:
                return None
        '''
        okey = 'iptype_override'
        defkey = 'iptype'
        if okey in properties:
            for e in properties[okey].split():
                family, iptype = e.split(":")
                if family.lower() == self._family.lower():
                    return iptype
        if defkey in properties:
            return properties[defkey]
        else:
            return None

    def set_iptype(self, iptype):
        '''
        if family==None, 
            family == DB_FAMILY from environment variable

        if "iptype_override" in property:
            if property['iptype_override'] contains matching "$family:<*>", 
                if $iptype == <*>:
                    skip
                else:
                    replace $family:<*> with $family:$iptype
            else:
                add $family:$iptype to property['iptype_override']
        else:
            if property['iptype'] == $iptype:
                skip
            else:
                set 'iptype' = $iptype
        '''
        okey = 'iptype_override'
        defkey = 'iptype'
        family_found_and_fixed = False
        newlist = []
        cli = dmx.abnrlib.icm.ICManageCLI()
        properties = cli.get_variant_properties(self._icmproject, self._icmvariant)
        if okey in properties:
            for e in properties[okey].split():
                family, oritype = e.split(":")
                if family.lower() == self._family.lower():
                    if oritype == iptype:
                        self._FOR_REGTEST = {}
                        LOGGER.debug("Iptype({}) already set for IP({}) in ({}). Skipping ...".format(iptype, [self._icmproject, self._icmvariant], okey))
                        return 0
                    else:
                        newlist.append('{}:{}'.format(family, iptype))
                        family_found_and_fixed = True
                else:
                    newlist.append('{}:{}'.format(family, oritype))

            if not family_found_and_fixed:
                newlist.append('{}:{}'.format(self._family, iptype))

            props = {okey: ' '.join(newlist)}
            self._FOR_REGTEST = props
            LOGGER.debug("Setting Iptype({}) for IP({}) in ({}) ...".format(iptype, [self._icmproject, self._icmvariant], okey))
            return cli.add_variant_properties(self._icmproject, self._icmvariant, props)

        else:
            ''' iptype_override not defined in variant property '''
            if defkey not in properties:
                props = {defkey: iptype}
                self._FOR_REGTEST = props
                LOGGER.debug("Setting Iptype({}) for IP({}) in ({}) ...".format(iptype, [self._icmproject, self._icmvariant], defkey))
                return cli.add_variant_properties(self._icmproject, self._icmvariant, props)
            elif properties[defkey] != iptype:
                # iptype property defined, but value is not iptype
                # DO NOT MODIFY iptype value. Set it at iptype_override instead!
                props = {okey: '{}:{}'.format(self._family, iptype)}
                self._FOR_REGTEST = props
                LOGGER.debug("Setting Iptype({}) for IP({}) in ({}) ...".format(iptype, [self._icmproject, self._icmvariant], okey))
                return cli.add_variant_properties(self._icmproject, self._icmvariant, props)
            else:
                self._FOR_REGTEST = {}
                LOGGER.debug("Iptype({}) already set for IP({}) in ({}). Skipping ...".format(iptype, [self._icmproject, self._icmvariant], defkey))
                return 0
            

    ## Loads IP properties
    ##
    ## @param self The object pointer. 
    def _load_ip_properties(self):
        if not self._properties_loaded:
            LOGGER.debug('{}.{}: Querying IP {} properties from ICManage'.format(self.__class__.__name__, inspect.stack()[0][3], self._ip))
            cli = dmx.abnrlib.icm.ICManageCLI(True)
            if self._icmproject:
                if cli.variant_exists(self._icmproject, self._ip):
                    project = self._icmproject  
            else:                        
                icmprojects = [x.project for x in dmx.ecolib.family.Family(self.family).get_icmprojects()]
                project = ''
                for icmproject in icmprojects:
                    if cli.variant_exists(icmproject, self._ip):
                        project = icmproject                    
                if not project:
                    raise IPError('ICManage project for {} cannot be found'.format(self.name))
            properties = cli.get_variant_properties(project, self._ip)
            icmproject = project
            owner = properties['Owner'] if 'Owner' in properties else None
            type = properties['iptype'] if 'iptype' in properties else None
            created = properties['created'] if 'created' in properties else None

            ### Will No longer get Roadmap from ICM's Roadmap property.
            ### From now on, Roadmap property is referred from $DB_DEVICE env var.
            ### https://jira.devtools.intel.com/browse/PSGDMX-1636
            #roadmap = properties['Roadmap'] if 'Roadmap' in properties else None
            roadmap = os.getenv("DB_DEVICE")
            if not roadmap and self._roadmap:
                roadmap = self._roadmap

            # These properties are only defined in django
            last_updated = None
            products = None
            if not type:
                raise IPError('{} does not have IPType registered in DMX'.format(self.name))      
            if not roadmap:
                # http://pg-rdjira:8080/browse/DI-800
                if is_pice_env():
                    # Roadmap property is expected in PICE, errors out if roadmap isn't found
                    raise IPError('{} does not have Roadmap registered in DMX'.format(self.name))
                else:
                    # Roadmap property is not expected in legacy, returns warning if roadmap isn't found
                    # Users are expected to provide roadmap argument to ecolib APIs
                    LOGGER.warning('{} does not have Roadmap registered in DMX'.format(self.name))
            
            self._icmproject = icmproject                
            self._owner = owner
            self._created = created
            self._last_updated = last_updated
            self._products = products
            self._roadmap = roadmap
            #self._iptype = type                
            self._iptype = self.get_iptype(properties)
            # Indicate the properties have been loaded
            self._properties_loaded = True


    ## Returns a list of strings of iptypes for the Family
    ##
    ## @param self The object pointer. 
    ## @return a list of strings of iptypes
    def _get_iptypes(self):
        iptypes = dmx.ecolib.loader.load_deliverables_by_ip_type(self.family)
        return sorted(list(set([str(x) for x in iptypes])))
     

    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{}".format(self._ip)

## @}
