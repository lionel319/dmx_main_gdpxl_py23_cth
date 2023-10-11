#!/usr/bin/env python

## @addtogroup ecolib
## @{

''' axc
This is documentation

@author Lionel Tan, Kevin Lim
@image html dmx.ecolib.png 

-the end-
'''
import os, sys
import re
import logging

_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, _LIB)
from dmx.errorlib.exceptions import *
import dmx.ecolib.family
import dmx.ecolib.loader
import dmx.abnrlib.workspace
import dmx.dmxlib.workspace
from dmx.utillib.utils import suppress_stdout
from dmx.utillib.arcenv import ARCEnv

LOGGER = logging.getLogger(__name__)

class EcoSphereError(Exception): pass
      
class EcoSphere(object):
    def __init__(self, workspaceroot=None, workspace=None, production=False, preview=True):
        self._families = []        
        # Question, why do we need workspaceroot and workspace?
        # If workspace instance is passed, it will speed up ecolib operation as it doesn't need to create an ICmanageWorkspace instance every time it needs to query info from ICManage
        # If workspaceroot is passed, it will create ICManageWorkspace instance at the beginning and pass it down the hierachies
        # If workspace instance is passed, workspaceroot will be ignored
        if workspaceroot:
            self._workspaceroot = workspaceroot        
        else:
            try:
                self._workspaceroot = os.getcwd()     
            except:
                raise DmxErrorCFDR01('Failed to get CWD. CWD might no longer exist.')
        self._production = production
        self._preview = preview
        self.logger = logging.getLogger(__name__)

        self._workspace = workspace
        self._errors = ''

        # Loading ARC environment's variable for consumption
        self._arc_project, self._arc_family, self._arc_thread, self._arc_device, self._arc_process = ARCEnv().get_arc_vars()
        
        if not self._workspace:
            with suppress_stdout():
                try:        
                    self._workspace = dmx.abnrlib.workspace.Workspace(self._workspaceroot)
                except Exception as e:
                    self._errors = e      
        else:
            if isinstance(self._workspace, dmx.abnrlib.workspace.Workspace) or isinstance(self._workspace, dmx.dmxlib.workspace.Workspace):
                self._workspaceroot = self._workspace._workspaceroot
            else:
                raise DmxErrorICWS03('{} is not a Workspace instance'.format(self._workspace))                

    @property
    def workspace(self):  
        if self._errors:
            raise DmxErrorICWS03(self._errors)            
        return self._workspace

    ## Return all available dmx::ecolib::family::Family objects.
    def _get_families(self):
        '''
        Return list of Family objects
        '''
        if not self._families:
            familydict = dmx.ecolib.loader.load_family()
            families = list(set([str(x) for x in familydict.keys()]))
            for family in families:
                if self._production and family.startswith('_'):
                    continue                    
                self._families.append(dmx.ecolib.family.Family(str(family), 
                    workspaceroot=self._workspaceroot, 
                    workspace=self._workspace,
                    production=self._production,
                    preview=self._preview))

        return self._families

    ## Returns a @c list of @c string of family name.
    ##
    ## @param self The object pointer
    ## @param family_filter a @c string . If given, only family that regex-match with the given @c family_filter will be returned.
    ## @return a @c list of @c string , which are the family names.
    def get_families(self, family_filter = ''):    
        try:
            re.compile(family_filter)
        except:
            raise DmxErrorRMRX01('{} cannot be compiled'.format(family_filter))        
        results = []
        for family in self._get_families():
            if re.match(family_filter.lower(), family.family.lower()):
                results.append(family)

        return sorted(list(set(results)), key=lambda family: family.family)            

    ## Check if family exist.
    ##
    ## @param self The object pointer. 
    ## @param family a @c string . 
    ## @exception dmx::ecolib::family::FamilyError Raised if nothing found.
    ## @return @c True if exist, else @c False .
    def has_family(self, family):
        try: 
            self.get_family(family)
        except:
            return False
        return True                        

    ## Returns a @c string of the family name.
    ##
    ## @param self The object pointer. 
    ## @param family a @c string . 
    ## @exception dmx::ecolib::ecosphere::EcoSphereError Raise if @c family not found.
    ## @return a @c string . The family name.
    def get_family(self, family=None):
        # Default when family not given, should take it from DB_FAMILY env var.
        # http://pg-rdjira:8080/browse/DI-1205
        if not family:
            family = self._arc_family

        if re.search('[^a-zA-Z0-9_]', family):
            raise DmxErrorRMFM01('Family can contain only alphabets, numbers and underscores.')

        results = self.get_families('^{}$'.format(family))
        if results:
            return results[0]
        else:
            LOGGER.error('Family {} does not exist'.format(family))
            raise DmxErrorRMFM01('Valid families are: {}'.format(self.get_families()))            

    ## Returns the Family object for the ICM project
    ## Since most flows/tools are still referring to project rather than by family,
    ## this command essential in returning the family for a particular project as ecolib
    ## refers to family, rather than project.
    ##
    ## @param self The object pointer. 
    ## @param icmproject string
    ## @exception dmx::ecolib::ecosphere::EcoSphereError Raise if family not found.
    ## @return family object.
    def get_family_for_icmproject(self, icmproject):
        families = self.get_families()
        for family in families:            
            if icmproject in [x.project for x in family.get_icmprojects()]:
                return family
        icmprojects = sorted(list(set([y for x in families for y in x.get_icmprojects()]))) 
        LOGGER.error('ICM Project {} does not exist'.format(icmproject))
        raise DmxErrorICPR01('Valid ICM projects are: {}'.format(icmprojects))                

    ## Returns the Family object for the thread
    ##
    ## @param self The object pointer. 
    ## @param thread string
    ## @exception dmx::ecolib::ecosphere::EcoSphereError Raise if family not found.
    ## @return family object.
    def get_family_for_thread(self, thread):
        all_threads = []
        families = self.get_families()
        for family in families:
            try:
                threads = [x[1] for x in family.get_valid_milestones_threads()]
                if thread in [x[1] for x in family.get_valid_milestones_threads()]:
                    return family
                all_threads += threads
            except:
                pass

        LOGGER.error('Thread {} does not exist'.format(thread))
        raise DmxErrorRMTH01('Valid threads are: {}'.format(set(all_threads)))

    ## Returns the roadmap object for the thread
    ##
    ## @param self The object pointer. 
    ## @param thread string
    ## @exception dmx::ecolib::ecosphere::EcoSphereError Raise if family not found.
    ## @return roadmap string.
    def get_roadmap_for_thread(self, thread):
        family = self.get_family_for_thread(thread)
        productname, revision = thread.split('rev')
        product = family.get_product(productname)
        return product.roadmap

    ## Returns the Family object for the roadmap
    ##
    ## @param self The object pointer. 
    ## @param roadmap string
    ## @exception dmx::ecolib::ecosphere::EcoSphereError Raise if family not found.
    ## @return family object.

    def get_family_for_roadmap(self, roadmap):
        all_roadmaps = []
        families = self.get_families()
        for family in families:
            roadmaps = family.get_roadmaps()
            if roadmap in [x.roadmap for x in roadmaps]:
                return family
            else:
                all_roadmaps += roadmaps
        LOGGER.warning('Roadmap {} does not exist'.format(roadmap))
        raise DmxErrorRMRM01('Valid roadmaps are: {}'.format(all_roadmaps))                

    ## Returns the valid thread and milestone in roadmap 
    ##
    ## @param self The object pointer. 
    ## @exception dmx::ecolib::ecosphere::EcoSphereError Raise if family not found.
    ## @return dict with thread: [milestone] 
    def get_valid_thread_and_milestone(self):
        families = self.get_families()
        valid_thread = {}
        valid_ms = []

        for f in families:
            for ms,thread in f.get_valid_milestones_threads():
                if ms != '99':
                    if thread in valid_thread:
                        valid_thread[thread].append(ms)
                    else:
                        valid_thread[thread] = [ms]
        return valid_thread


    def get_icmprojects(self):
        '''
        return all icmproject avaialble
        '''
        families = self.get_families()
        allicmproj = []
        for family in families:
            icmproj = [x.project for x in family.get_icmprojects() if x.project not in allicmproj]
            allicmproj += icmproj
        return allicmproj
        #icmprojects = sorted(list(set([y for x in families for y in x.get_icmprojects()])))
        #LOGGER.error('ICM Project {} does not exist'.format(icmproject))
        #raise DmxErrorICPR01('Valid ICM projects are: {}'.format(icmprojects))

        
        ## @}
