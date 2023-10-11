#!/usr/bin/env python

## @addtogroup ecolib
## @{

''' axc
This is documentation

@author Lionel Tan, Kevin Lim
@image html dmx.ecolib.png 

-the end-
'''

from builtins import str
from builtins import object
import sys, os
import re
import logging
import datetime
import dmx.ecolib.loader
import dmx.ecolib.product
import dmx.ecolib.project
import dmx.ecolib.iptype
import dmx.ecolib.ip 
import dmx.ecolib.view
import dmx.ecolib.prel
from dmx.utillib.multiproc import run_mp
from dmx.utillib.arcenv import ARCEnv

# For backward compatibility
from dmx.ecolib.__init__ import LEGACY
if not LEGACY:
    from dmx.djangolib.models import *
import dmx.abnrlib.icm 

LOGGER = logging.getLogger(__name__)

class FamilyError(Exception): pass

class Family(object):  
    def __init__(self, family, workspaceroot=None, workspace=None, production=False, preview=True):
        self._family = family
        if workspaceroot:
            self._workspaceroot = workspaceroot        
        else:
            self._workspaceroot = os.getcwd()
        self._workspace = workspace
        self._production = production
        self._preview = preview
        self.cli = dmx.abnrlib.icm.ICManageCLI(preview=self._preview)

        properties = self._get_family_properties()
        self._nisgroup = str(properties['NIS'])
        self._icmgroup = str(properties['ICM'])
        self._scratchpath = str(properties['scratch'])

        self._products = []
        self._icmprojects = []
        self._iptypes = []
        self._ips = []
        self._disks = []
        self._views = []
        self._prels = []
        self._roadmaps = []
        self._deliverables = {}

    @property
    def name(self):
        return self._family        

    @property
    def family(self):
        return self._family

    @property
    def nisgroup(self):
        return self._nisgroup

    @property
    def icmgroup(self):
        return self._icmgroup

    @property
    def scratchpath(self):
        return self._scratchpath

    ## Preloads local variables
    ## self._products
    ## self._icmprojects
    ## self._iptypes
    ## self._ips
    ## self._disks
    ## self._views
    ##
    ## @param self The object pointer. 
    def _preload(self):
        self._products = self.get_products()
        self._icmprojects = self.get_icmprojects()
        self._iptypes = self.get_iptypes()
        self._ips = self.get_ips_names()
        self._disks = self.get_approved_disks()
        self._views = self.get_views()
        self._deliverables = self.get_all_deliverables()
       
    ## Returns a dictionary of Family's properties
    ##
    ## @param self The object pointer. 
    ## @return dictionary of Family's properties
    def _get_family_properties(self):
        familydict = dmx.ecolib.loader.load_family()
        return familydict[self._family]        

    ## Returns a list of Product objects associated with the Family
    ##
    ## @param self The object pointer. 
    ## @return list of Product objects
    def _get_products(self):
        if not self._products:
            products = dmx.ecolib.loader.load_roadmap_and_revisions_by_product(self._family)
            for product in products:
                self._products.append(dmx.ecolib.product.Product(self._family, str(product),
                    preview=self._preview))
        return self._products
        
    ## Returns a list of Product objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param product_filter Filter by product
    ## @exception dmx::ecolib::family::FamilyError Raise if filter cannot be compiled
    ## @return list of Product objects
    def get_products(self, product_filter = ''):
        try:
            re.compile(product_filter)
        except:
            raise FamilyError('{} cannot be compiled'.format(product_filter))            

        results = []
        seen = []   # To make sure finaly `results` does not have duplicated entries
        for product in self._get_products():
            if product.name not in seen:
                seen.append(product.name)
                if re.match(product_filter, product.product):
                    results.append(product)
       
        return sorted(results, key=lambda product: product.product)
          
    ## Returns True if product exists, otherwise False
    ##
    ## @param self The object pointer. 
    ## @param product Product
    ## @return True if product exists, otherwise False
    def has_product(self, product):
        try:
            self.get_product(product)
        except:
            return False
        return True                        

    ## Returns a Product object that matches the product name
    ##
    ## @param self The object pointer. 
    ## @param product Product
    ## @exception dmx::ecolib::family::FamilyError Raise if product name contains illegal characters or product cannot be found
    ## @return Product object
    def get_product(self, product):
        if re.search('[^A-Za-z0-9]', product):
            raise FamilyError('ICM Project can contain only alphabets and numbers.')

        results = self.get_products('^{}$'.format(product))
        if results:
            return results[0]
        else:
            LOGGER.error('Product {} does not exist'.format(product))
            raise FamilyError('Valid products for Family {} are: {}'.format(self._family, self.get_products()))
 
    ## Returns a list of Project objects associated with the Family
    ##
    ## @param self The object pointer.
    ## @return list of Project objects
    def _get_icmprojects(self):
        if not self._icmprojects:
            icmprojects = self._get_family_properties()['icmprojects']
            exclude_icmprojects = []
            if 'exclude_icmprojects' in self._get_family_properties():
                exclude_icmprojects = [str(x) for x in self._get_family_properties()['exclude_icmprojects']]

            for icmproject in icmprojects:
                # http://pg-rdjira:8080/browse/DI-1393
                # exclude  the project is if it's marked as so
                if icmproject in exclude_icmprojects:
                    continue

                # DI474: Recognize LabProject projects in dmx
                # If wildcard is found, match the regex with all the projects in the system to determine if they should be categorized under _TestData
                if '*' in icmproject:
                    for project in self.cli.get_projects():
                        # http://pg-rdjira:8080/browse/DI-1393
                        # exclude  the project is if it's marked as so
                        if project in exclude_icmprojects:
                            continue
                        m = re.search(icmproject.replace('*', '.*'), project)
                        if m:
                            self._icmprojects.append(dmx.ecolib.project.Project(
                                self._family,
                                str(project),
                                preview=self._preview))
                elif self.cli.project_exists(icmproject):
                    self._icmprojects.append(dmx.ecolib.project.Project(
                        self._family, 
                        str(icmproject),
                        preview=self._preview))
        return self._icmprojects

    ## Returns a list of Project objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param icmproject_filter Filter by ICM projects
    ## @exception dmx::ecolib::ecosphere::EcoSphereError Raise if filter cannot be compiled
    ## @return list of Project objects
    def get_icmprojects(self, icmproject_filter = ''):
        try:
            re.compile(icmproject_filter)
        except:
            raise FamilyError('{} cannot be compiled'.format(icmproject_filter))            

        results = []
        for icmproject in self._get_icmprojects():
            if re.match(icmproject_filter, icmproject.project):                        
                results.append(icmproject)
       
        return sorted(list(set(results)), key=lambda project: project.project)
                  
    ## Returns True if ICM project exists, otherwise False
    ##
    ## @param self The object pointer. 
    ## @param icmproject ICM project
    ## @return True if ICM project exists, otherwise False                         
    def has_icmproject(self, icmproject):
        try:
            self.get_icmproject(icmproject)
        except:
            return False
        return True                        

    ## Returns a Project object that matches the ICM project name
    ##
    ## @param self The object pointer. 
    ## @param icmproject ICM project
    ## @exception dmx::ecolib::family::FamilyError Raise if ICM project name contains illegal characters or ICM project cannot be found
    ## @return Project object
    def get_icmproject(self, icmproject):
        if re.search('[^A-Za-z0-9_]', icmproject):
            raise FamilyError('ICM Project can contain only alphabets, numbers and underscores.')

        results = self.get_icmprojects('^{}$'.format(icmproject))
        if results:
            return results[0]
        else:
            LOGGER.error('ICM Project {} does not exist'.format(icmproject))
            raise FamilyError('Valid ICM projects for Family {} are: {}'.format(self._family, self.get_icmprojects()))

    ## Returns a list of IPType objects associated with the Family
    ##
    ## @param self The object pointer. 
    ## @return list of IPType objects
    def _get_iptypes(self, roadmap=''):
        if not self._iptypes:
            iptypes = dmx.ecolib.loader.load_deliverables_by_ip_type(self._family)
            for iptype in iptypes:
                self._iptypes.append(dmx.ecolib.iptype.IPType(self._family, 
                                                              str(iptype),
                                                              roadmap = roadmap,
                                                              preview = self._preview))
        return self._iptypes
       
    ## Returns a list of IPType objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param iptype_filter Filter by iptype
    ## @exception dmx::ecolib::family::FamilyError Raise if filter cannot be compiled
    ## @return list of IPType objects                        
    def get_iptypes(self, iptype_filter = '', roadmap=''): 
        try:
            re.compile(iptype_filter)
        except:
            raise FamilyError('{} cannot be compiled'.format(iptype_filter))   

        iptypes = []
        for iptype in self._get_iptypes(roadmap=roadmap):
            if re.match(iptype_filter, iptype.iptype):
                iptypes.append(iptype)
       
        return sorted(list(set(iptypes)), key=lambda iptype: iptype.iptype)

    ## Returns True if iptype exists, otherwise False
    ##
    ## @param self The object pointer. 
    ## @param iptype IPType
    ## @return True if iptype exists, otherwise False         
    def has_iptype(self, iptype):                    
        try:
            self.get_iptype(iptype)
        except:
            return False
        return True                        

    ## Returns a IPType object that matches the iptype
    ##
    ## @param self The object pointer. 
    ## @param iptype IPType
    ## @exception dmx::ecolib::family::FamilyError Raise if iptype contains illegal characters or iptype cannot be found
    ## @return IPType object
    def get_iptype(self, iptype, roadmap=''):
        if re.search('[^A-Za-z0-9_]', iptype):
            raise FamilyError('IPType can contain only alphabets or underscores.')

        results = self.get_iptypes('^{}$'.format(iptype), roadmap=roadmap)       
        if results:
            return results[0]
        else:
            LOGGER.error('IPType {} does not exist'.format(iptype))
            raise FamilyError('Valid iptypes for Family {} are: {}'.format(self._family, self.get_iptypes()))        

    ## Returns a list of IP strings (useful if get_ips takes too long)
    ## get_ips initializes the objects and all its properties and takes a long time if run from SJ 
    ## since server is in PG. To remedy, use get_ips_names instead and instantiate the needed object via get_ip
    ##
    ## @param self The object pointer. 
    ## @param ip_filter Filter by ip
    ## @param product_filter Filter by product
    ## @param project_filter Filter by ICM project
    ## @return list of IP strings
    def get_ips_names(self, ip_filter = None, product_filter = None, project_filter = None):  
        if project_filter:
            icmprojects = [project_filter]
        else:            
            icmprojects = [x.project for x in self.get_icmprojects()]
        ips = []
        results = []
        # Why? For legacy, we are getting IP info from ICManage
        # For non-legacy, we are getting info from django
        if LEGACY:
            LOGGER.debug('DMX_LEGACY: Querying family {} IPs from ICManage'.format(self._family))
            for icmproject in icmprojects:
                results = results + list(self.cli.get_variants(icmproject))
            for result in results:
                m = re.match(ip_filter if ip_filter else '.*', result)
                if m:
                    ips.append(result)
        else:     
            LOGGER.debug('Querying family {} IPs from django Cellname/Owner'.format(self._family))       
            if product_filter and ip_filter:
                for icmproject in icmprojects:
                    for owner in Owner.objects.filter(variant__regex=ip_filter, project__regex=icmproject):
                        results = results + [x for x in Cellname.objects.filter(variant__regex=owner.variant, product__regex=product_filter, project__regex=icmproject)]
            elif product_filter:
                for icmproject in icmprojects:
                    results = results + [x for x in Cellname.objects.filter(product__regex=product_filter, project__regex=icmproject)]
            elif ip_filter:
                for icmproject in icmprojects:
                    results = results + [x for x in Owner.objects.filter(variant__regex=ip_filter, project__regex=icmproject)]
            else:
                for icmproject in icmprojects:
                    results = results + [x for x in Owner.objects.filter(project__regex=icmproject)]

            ips  = list(set([str(x.variant) for x in results]))        
        
        return sorted(list(set(ips)))
            
    ## Returns a list of IP objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param ip_filter Filter by ip
    ## @param product_filter Filter by product
    ## @param project_filter Filter by project
    ## @return list of IP objects
    def get_ips(self, ip_filter = None, product_filter = None, project_filter = None):     
        if project_filter:
            icmprojects = [project_filter]
        else:            
            icmprojects = [x.project for x in self.get_icmprojects()]
        ips = []
        results = []
        unique_ips = []
        
        LOGGER.debug('DMX_LEGACY: Querying family {} IPs from ICManage'.format(self._family))
        for icmproject in icmprojects:
            tmp = [[icmproject, x] for x in list(self.cli.get_variants(icmproject))]
            results = results + tmp
        for project,variant in results:
            m = re.match(ip_filter if ip_filter else '.*', variant)
            if m:
                unique_ips.append([project, variant])
            
        for unique_project, unique_ip in unique_ips:
            ips.append(dmx.ecolib.ip.IP(self._family, unique_ip, self._workspaceroot,
                            self._workspace, self._preview, icmproject=unique_project))

        return sorted(list(set(ips)), key=lambda ip: ip.ip)
    
    ## Returns True if ip exists, otherwise False
    ##
    ## @param self The object pointer. 
    ## @param ip IP
    ## @return True if ip exists, otherwise False         
    def has_ip(self, ip, project_filter = ''):
        try:
            self.get_ip(ip, project_filter=project_filter)
        except:
            return False
        return True                        
         
    ## Returns a IP object that matches the ip name
    ##
    ## @param self The object pointer. 
    ## @param ip IP 
    ## @exception dmx::ecolib::family::FamilyError Raise if IP name contains illegal characters or IP cannot be found
    ## @return IP object                
    def get_ip(self, ip, project_filter = ''):
        if re.search('[^a-zA-Z0-9_]', ip):
            raise FamilyError('IP can contain only alphabets, numbers and underscores.')

        results = []
        if LEGACY:
            # Why don't we just call get_ips? This is because cli.get_variants() takes abysmally long for i14socnd as it returns all combinations of variants/libtypes.
            # As such, we write our own codes to check the IP existence.
            LOGGER.debug('DMX_LEGACY: Querying IP {}/{} from ICManage'.format(self._family, ip))
            if project_filter:
                if project_filter in [x.project for x in self.get_icmprojects()] and self.cli.project_exists(project_filter):
                    icmprojects = [project_filter]
                else:
                    raise FamilyError('Unrecognized project: {} ! \nValid projects for {} are:\n{}'.format(project_filter, self._family, self.get_icmprojects()))
            else:                
                icmprojects = [x.project for x in self.get_icmprojects()]

            for icmproject in icmprojects:
                if self.cli.project_exists(icmproject) and self.cli.variant_exists(icmproject, ip):
                    result = dmx.ecolib.ip.IP(
                        self._family, ip, 
                        workspaceroot=self._workspaceroot,
                        workspace=self._workspace,
                        icmproject=icmproject,
                        preview=self._preview)    
                    result._preload()
                    results.append(result)                                       
        else:
            results = self.get_ips(ip_filter='^{}$'.format(ip))

        if results:
            if len(results) == 1:
                # Preload the IP object before returning
                results[0]._preload()
                return results[0]
            else:
                raise FamilyError('More than one IP found for {}: {}'.format(self._family, ['{}/{}'.format(x.icmproject, x.ip) for x in results]))
        else:
            raise FamilyError('Unrecognized ip: {} !\nValid ips for {} are:\n{}'.format(ip, self._family, "\n".join(self.get_ips_names())))

    ## Registers a new IP to the Family
    ##
    ## @param self The object pointer. 
    ## @param icmproject ICM project
    ## @param ip IP 
    ## @param iptype IP Type
    ## @exception dmx::ecolib::family::FamilyError Raise if IP already exists in the Family. IP is unique across all ICM projects in the same Family
    ## @return True if successful, else False
    def add_ip(self, icmproject, ip, iptype, description=''):
        # Why? For legacy, we don't need this since we are getting IP list from ICM
        # For non-legacy, this will add the IP into django
        if LEGACY:
            raise FamilyError('This function is not supported')
        ret = False
        if not self.has_iptype(iptype):
            LOGGER.error('IPType {} does not exist'.format(iptype))
            raise FamilyError('Valid iptypes for Family {} are: {}'.format(self._family, self.get_ips()))
        if not self.has_icmproject(icmproject):
            LOGGER.error('ICM Project {} does not exist'.format(icmproject))
            raise FamilyError('Valid ICM projects for Family {} are: {}'.format(self._family, self.get_products()))
        if self.has_ip(ip):
            LOGGER.error('IP {} does not exist'.format(ip))
            raise FamilyError('IP {} already exists for {}/{}'.format(ip, self._family, icmproject))

        owner = Owner(project=icmproject,
                      variant=ip,
                      type=iptype,
                      owner=os.environ['USER'],
                      datetime=datetime.datetime.today())

        if not self._preview:
            owner.save()
        LOGGER.info('{}IP {} added to {}/{}'.format('PREVIEW: ' if self._preview else '', ip, self._family, icmproject))
        ret = True

        return ret
       
    ## Removes an existing IP from the Family
    ##
    ## @param self The object pointer. 
    ## @param ip IP 
    ## @exception dmx::ecolib::family::FamilyError Raise if IP does not exist in the Family
    ## @return True if successful, else False
    def delete_ip(self, ip):
        # Why? For legacy, we don't need this since we are getting IP list from ICM
        # For non-legacy, this will delete the IP from django
        if LEGACY:
            raise FamilyError('This function is not supported')
        ret = False        
        if not self.has_ip(ip):
            raise FamilyError('IP {} does not exist for {}'.format(ip, self._family))
        
        # Delete from cellnames/unneededs table
        ipobj = self.get_ip(ip)
        cells_to_delete = ipobj.get_cells()
        for cell in cells_to_delete:
            unneededs = cell.get_unneeded_deliverables()
            for unneeded in unneededs:
                if not self._preview:
                    cell.delete_unneeded_deliverable(unneeded)    
            ipobj.delete_cell(cell.cell, cell.product)                    
                                                
        # Delete from owners table
        ip_to_delete = Owner.objects.get(variant=ip)
        if not self._preview:            
            ip_to_delete.delete()
        LOGGER.info('{}IP {} deleted from {}'.format('PREVIEW: ' if self._preview else '', ip, self._family))
        ret = True

        return ret        

    ## Returns a list of strings of approved disks that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param owner_filter Disk's owner name
    ## @param site_filter Disk's site
    ## @return list of strings of approved disks
    def get_approved_disks(self, owner_filter = None, site_filter = None):
        # This is disabled for legacy as we try not to depend on django yet.
        if LEGACY:
            LOGGER.debug('This function is not supported for legacy.')
            return
        results = []
        icmprojects = self.get_icmprojects() 
        for icmproject in icmprojects:
            if owner_filter and site_filter:
                results = results + [(str(x.disk), int(x.size)) for x in Disk.objects.filter(project__regex=icmproject.project, ownerid__regex=owner_filter, site__regex=site_filter)]
            elif owner_filter:
                results = results + [(str(x.disk), int(x.size)) for x in Disk.objects.filter(project__regex=icmproject.project, ownerid__regex=owner_filter)]
            elif site_filter:
                results = results + [(str(x.disk), int(x.size)) for x in Disk.objects.filter(project__regex=icmproject.project, site__regex=site_filter)]
            else:
                results = results + [(str(x.disk), int(x.size)) for x in Disk.objects.filter(project__regex=icmproject.project)]

        return sorted(list(set([disk for disk, size in results if size>0])))

    ## Returns a list of View objects associated with the Family
    ##
    ## @param self The object pointer. 
    ## @return list of View objects
    def _get_views(self):
        if not self._views:
            views = dmx.ecolib.loader.load_views(self._family)
            for view in views:
                self._views.append(dmx.ecolib.view.View(self._family, 
                                                        str(view),
                                                        preview = self._preview))
        return self._views        

    ## Returns a list of View objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param view_filter Filter by view
    ## @exception dmx::ecolib::family::FamilyError Raise if filter cannot be compiled
    ## @return list of View objects                        
    def get_views(self, view_filter = ''): 
        try:
            re.compile(view_filter)
        except:
            raise FamilyError('{} cannot be compiled'.format(view_filter))   

        views = []
        for view in self._get_views():
            if re.match(view_filter, view.view):
                views.append(view)
       
        return sorted(list(set(views)), key=lambda view: view.view)

    ## Returns True if view exists, otherwise False
    ##
    ## @param self The object pointer. 
    ## @param view View
    ## @return True if view exists, otherwise False         
    def has_view(self, view):                    
        try:
            self.get_view(view)
        except:
            return False
        return True                        

    ## Returns a View object that matches the view
    ##
    ## @param self The object pointer. 
    ## @param view View
    ## @exception dmx::ecolib::family::FamilyError Raise if view contains illegal characters or view cannot be found
    ## @return View object
    def get_view(self, view):
        if re.search('[^view_A-Za-z0-9]', view):
            raise FamilyError('View must begin with \'view_\' and can contain only alphabets or numbers.')

        results = self.get_views('^{}$'.format(view))       
        if results:
            return results[0]
        else:
            LOGGER.error('View {} does not exist'.format(view))
            raise FamilyError('Valid views for Family {} are: {}'.format(self._family, self.get_views()))          

    ## Returns a list of View objects associated with the Family
    ##
    ## @param self The object pointer. 
    ## @return list of View objects
    def _get_prels(self):
        if not self._prels:
            prels = dmx.ecolib.loader.load_prels(self._family)
            for prel in prels:
                self._prels.append(dmx.ecolib.prel.Prel(self._family, 
                                                        str(prel),
                                                        preview = self._preview))
        return self._prels

    ## Returns a list of View objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param prel_filter Filter by prel
    ## @exception dmx::ecolib::family::FamilyError Raise if filter cannot be compiled
    ## @return list of View objects                        
    def get_prels(self, prel_filter = ''): 
        try:
            re.compile(prel_filter)
        except:
            raise FamilyError('{} cannot be compiled'.format(prel_filter))   

        prels = []
        for prel in self._get_prels():
            if re.match(prel_filter, prel.prel):
                prels.append(prel)
       
        return sorted(list(set(prels)), key=lambda prel: prel.prel)

    ## Returns True if prel exists, otherwise False
    ##
    ## @param self The object pointer. 
    ## @param prel Prel
    ## @return True if prel exists, otherwise False         
    def has_prel(self, prel):                    
        try:
            self.get_prel(prel)
        except:
            return False
        return True                        

    ## Returns a View object that matches the prel
    ##
    ## @param self The object pointer. 
    ## @param prel Prel
    ## @exception dmx::ecolib::family::FamilyError Raise if prel contains illegal characters or prel cannot be found
    ## @return View object
    def get_prel(self, prel):
        if re.search('[^prel_A-Za-z0-9]', prel):
            raise FamilyError('Prel must begin with \'prel_\' and can contain only alphabets or numbers.')

        results = self.get_prels('^{}$'.format(prel))       
        if results:
            return results[0]
        else:
            LOGGER.error('Prel {} does not exist'.format(prel))
            raise FamilyError('Valid prels for Family {} are: {}'.format(self._family, self.get_prels()))          

    ## Returns a list of Roadmap objects associated with the Family
    ##
    ## @param self The object pointer. 
    ## @return list of Roadmap objects
    def _get_roadmaps(self):
        if not self._roadmaps:
            roadmaps = dmx.ecolib.loader.load_roadmaps(self._family)
            for roadmap in roadmaps:
                self._roadmaps.append(dmx.ecolib.roadmap.Roadmap(self._family, str(roadmap),
                    preview=self._preview))
        return self._roadmaps
        
    ## Returns a list of Roadmap objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param product_filter Filter by roadmap
    ## @exception dmx::ecolib::family::FamilyError Raise if filter cannot be compiled
    ## @return list of Roadmap objects
    def get_roadmaps(self, roadmap_filter = ''):
        try:
            re.compile(roadmap_filter)
        except:
            raise FamilyError('{} cannot be compiled'.format(roadmap_filter))            

        results = []
        seen = []   # variable that keep tracks of roadmap that has been appended, to avoid duplicated entries
        for roadmap in self._get_roadmaps():
            if re.match(roadmap_filter, roadmap.roadmap):
                if roadmap.roadmap not in seen:
                    results.append(roadmap)
                    seen.append(roadmap.roadmap)
      
        return sorted(results, key=lambda r: r.roadmap)
          
    ## Returns True if roadmap exists, otherwise False
    ##
    ## @param self The object pointer. 
    ## @param roadmap Roadmap
    ## @return True if roadmap exists, otherwise False
    def has_roadmap(self, roadmap):
        try:
            self.get_roadmap(roadmap)
        except:
            return False
        return True                        

    ## Returns a Roadmap object that matches the roadmap name
    ##
    ## @param self The object pointer. 
    ## @param roadmap Roadmap
    ## @exception dmx::ecolib::family::FamilyError Raise if roadmap name contains illegal characters or roadmap cannot be found
    ## @return Roadmap object
    def get_roadmap(self, roadmap):
        if re.search('[^A-Za-z0-9]', roadmap):
            raise FamilyError('ICM Project can contain only alphabets and numbers.')

        results = self.get_roadmaps('^{}$'.format(roadmap))
        if results:
            return results[0]
        else:
            LOGGER.warning('Roadmap {} does not exist'.format(roadmap))
            raise FamilyError('Valid roadmaps for Family {} are: {}'.format(self._family, self.get_roadmaps()))                       
    ## Returns a list of tuples of available (milestone, thread)
    ## 
    ## http://pg-rdjira:8080/browse/DI-718
    ## Ported from abnrlib/roadmap.py
    ##
    ## @param self The object pointer.
    ## @return [('1.0', 'FM8revA0'), ('2.0', 'FM8revA0'), ... ('5.0', 'FM4revB3') ... ]
    def get_valid_milestones_threads(self):
        #family = self.ecosphere.get_family_for_icmproject(project)
        products = self.get_products()
        supported_combos = []
        for product in products:
            revisions = product.get_revisions()
            milestones = product.get_milestones()
            for revision in revisions:
                for milestone in milestones:
                    supported_combos.append((milestone.milestone, '{}{}'.format(product.product, revision.revision)))
        return supported_combos


    ## Returns True if given (milestone, thread) exists for this Family, else False
    ## 
    ## http://pg-rdjira:8080/browse/DI-718
    ## Ported from abnrlib/roadmap.py
    ##
    ## @param self The object pointer.
    ## @param milestone String
    ## @param thread String
    ## @return Boolean
    def verify_roadmap(self, milestone, thread):
        ret = False

        combos = self.get_valid_milestones_threads()
        
        if not combos:
            LOGGER.error("Could not get roadmap data from EcoSphere")
            ret = False
        elif (milestone, thread) not in combos:
            LOGGER.error("The milestone and thread combination of {0} {1} are not valid for family {2}".format(
                milestone, thread, self._family))
            LOGGER.error("Valid milestone/thread combinations are:")
            for combo in combos:
                LOGGER.error("Milestone:'{0}' Thread:'{1}'".format(combo[0], combo[1]))
            ret = False
        else:
            ret = True            
        return ret

    ## Returns a string of the Project name for the IP
    ## A family contains multiple projects. This API helps to return the corresponding ICM project
    ## for a given IP
    ##
    ## @param self The object pointer. 
    ## @param icmproject string
    ## @exception dmx::ecolib::ecosphere::EcoSphereError Raise if family not found.
    ## @return a string. The project name.
    def get_icmproject_for_ip(self, ip):
        icmprojects = self.get_icmprojects()
        for icmproject in icmprojects:
            ips = self.get_ips_names(project_filter=icmproject.project)
            if ip in ips:
                return icmproject.project
        LOGGER.error('IP {} does not exist'.format(ip))
        raise FamilyError('Valid IPs for Family {} are: {}'.format(self._family, self.get_ips_names()))

    ## Returns a list of Deliverable objects defined for the family
    ##
    ## @param self The object pointer. 
    ## @return list of Deliverable objects
    def _get_deliverables(self):        
        if not self._deliverables:
            roadmaps = dmx.ecolib.loader.load_roadmaps(self.family)
            for roadmap in roadmaps:
                if roadmap not in self._deliverables:
                    self._deliverables[str(roadmap)] = []
                deliverables = dmx.ecolib.loader.load_manifest(self.family)
                for deliverable in deliverables:
                    self._deliverables[roadmap].append(dmx.ecolib.deliverable.Deliverable(
                        family = self.family,
                        deliverable = str(deliverable),
                        roadmap = str(roadmap),
                        preview = self._preview))
        return self._deliverables                                

    ## Returns a list of Deliverable objects that matches the filters
    ##
    ## @param self The object pointer. 
    ## @param deliverable_filter Filter by deliverable
    ## @param roadmap Filter by roadmap
    ## @exception dmx::ecolib::family::FamilyError Raise if filter cannot be compiled
    ## @return list of Deliverable objects
    def get_all_deliverables(self, deliverable_filter = '', roadmap = ''):
        try:
            re.compile(deliverable_filter)
        except:
            raise IPTypeError('{} cannot be compiled'.format(deliverable_filter))        

        deliverables = self._get_deliverables()
        if not roadmap:
            # If roadmap is not given, simply choose a roadmap from the dictionary
            # It doesn't matter as deliverables are the same in all roadmaps (except for the checker info)
            roadmap = list(deliverables.keys())[0]
        if roadmap not in deliverables:
            LOGGER.warning('Roadmap {} does not exist'.format(roadmap))
            raise FamilyError('Valid roadmaps for Family {} are: {}'.format(self.family, sorted(deliverables)))

        results = []
        for deliverable in deliverables[roadmap]:
            if re.match(deliverable_filter, deliverable.deliverable):
                results.append(deliverable)   

        return sorted(list(set(results)), key=lambda deliverable: deliverable.deliverable)

    ## Returns True if deliverable exists, otherwise False
    ##
    ## @param self The object pointer. 
    ## @param deliverable Deliverable
    ## @return True if deliverable exists, otherwise False    
    def has_deliverable(self, deliverable, roadmap = ''):
        try:
            self.get_deliverable(deliverable, roadmap=roadmap)
        except:
            return False
        return True                        

    ## Returns a Deliverable object that matches the deliverable and milestone
    ##
    ## @param self The object pointer. 
    ## @param deliverable Deliverable
    ## @exception dmx::ecolib::family::FamilyError Raise if deliverable contains illegal characters
    ## @return Deliverable object
    def get_deliverable(self, deliverable, roadmap = ''):  
        if re.search('[^A-Za-z0-9_]', deliverable):
            raise IPTypeError('Deliverable can contain only alphabets, numbers and underscores.')

        results = self.get_all_deliverables('^{}$'.format(deliverable), roadmap=roadmap)
        if results:
            return results[0]
        else:
            LOGGER.error('Deliverable {} does not exist'.format(deliverable))
            raise FamilyError('Valid deliverables for Family {} are: {}'.format(self.family, self.get_all_deliverables(roadmap=roadmap)))

    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{}".format(self._family)


## @}
