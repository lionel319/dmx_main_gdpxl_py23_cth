"""
Filename:      $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/py23comlib/tdma_hsdes_py23/__init__.py#1 $

Description:   Utility Class to interact with HSD-ES
               Use this class to access hsdes and execute on commands
               to list objects, get specific objects or create new objects
               It is similar to fogbugz module.
               
Author:        Jim Zhao

               Copyright (c) Intel Corporation 2018
               All rights reserved.

This is based off of PSWE's REST API that was written by Jim Zhao (jim.x.zhao@intel.com) and updated to support PHE (support subject) in TDMA. All credits go to Jim Zhao
Original source depot: //depot/devenv/python_modules/main/altera/hsdes          
"""
from __future__ import absolute_import


from builtins import str
from builtins import object
__author__ ="Jim Zhao (jim.x.zhao@intel.com)"
__copyright__ = "Copyright 2018 Intel Corporation."

import json
import os
import re
import types
import sys
sys.path.append('/p/psg/ctools/python/altera_modules/1.0/')
from altera import Error
from .hsdes import *

#-----------------------------------------------------------------------------------------------------------------
HSDES_FPGA_BUG_KEY_DICT = {}
HSDES_FPGA_BUG_REVERSE_KEY_DICT = {}
HSDES_FPGA_AR_KEY_DICT = {}
HSDES_FPGA_AR_REVERSE_KEY_DICT = {}
HSDES_FPGA_SUPPORT_KEY_DICT = {}
HSDES_FPGA_SUPPORT_REVERSE_KEY_DICT = {}
HSDES_FPGA_WORK_ITEM_KEY_DICT = {}
HSDES_FPGA_WORK_ITEM_REVERSE_KEY_DICT = {}
    
#===============================================================================================================
class HsdesConnection(object):
    """
    Uses HSDES REST API to interact with HSDES server.
    """    
    HSDES_TEST_ENVIRONMENT = 'PREPRODUCTION'
    HSDES_PROD_ENVIRONMENT = 'PRODUCTION'
    HSDES_TENANT = 'fpga'
    HSDES_BUG_SUBJECT = 'bug'
    HSDES_AR_SUBJECT = 'ar'    
    HSDES_SUPPORT_SUBJECT = 'support'    
    HSDES_APPROVAL_SUBJECT = 'approval'    
    HSDES_WORK_ITEM_SUBJECT = 'work_item'    

    #---------------------------------------------------------------------------------------
    def __init__(self, username=None, password=None, env=None, debug=False, proxy=None):
#    def __init__(self, env=None, debug=False, proxy=None):
        global HSDES_FPGA_BUG_KEY_DICT
        global HSDES_FPGA_BUG_REVERSE_KEY_DICT
        global HSDES_FPGA_AR_KEY_DICT
        global HSDES_FPGA_AR_REVERSE_KEY_DICT
        global HSDES_FPGA_SUPPORT_KEY_DICT
        global HSDES_FPGA_SUPPORT_REVERSE_KEY_DICT
        global HSDES_FPGA_WORK_ITEM_KEY_DICT
        global HSDES_FPGA_WORK_ITEM_REVERSE_KEY_DICT        
        global HSDES_FPGA_COMPONENT_KEY_DICT
        data_file = os.path.join(os.path.dirname(__file__), 'hsdes_data.json')
        with open(data_file) as json_file:  
            data = json.load(json_file)
            HSDES_FPGA_BUG_KEY_DICT = data['bug'] 
            HSDES_FPGA_BUG_REVERSE_KEY_DICT = {}
            for hsdes_ui_key, hsdes_db_key in HSDES_FPGA_BUG_KEY_DICT.items():
                HSDES_FPGA_BUG_REVERSE_KEY_DICT[hsdes_db_key] = hsdes_ui_key
            HSDES_FPGA_AR_KEY_DICT = data['ar'] 
            HSDES_FPGA_AR_REVERSE_KEY_DICT = {}
            for hsdes_ui_key, hsdes_db_key in HSDES_FPGA_AR_KEY_DICT.items():
                HSDES_FPGA_AR_REVERSE_KEY_DICT[hsdes_db_key] = hsdes_ui_key
            HSDES_FPGA_SUPPORT_KEY_DICT = data['support']
            HSDES_FPGA_SUPPORT_REVERSE_KEY_DICT = {}
            for hsdes_ui_key, hsdes_db_key in HSDES_FPGA_SUPPORT_KEY_DICT.items():
                HSDES_FPGA_SUPPORT_REVERSE_KEY_DICT[hsdes_db_key] = hsdes_ui_key                
            HSDES_FPGA_WORK_ITEM_KEY_DICT = data['work_item']
            HSDES_FPGA_WORK_ITEM_REVERSE_KEY_DICT = {}
            for hsdes_ui_key, hsdes_db_key in HSDES_FPGA_WORK_ITEM_KEY_DICT.items():
                HSDES_FPGA_WORK_ITEM_REVERSE_KEY_DICT[hsdes_db_key] = hsdes_ui_key                
            HSDES_FPGA_COMPONENT_KEY_DICT = data['component']

        if env is None:
            if debug:
                env = self.HSDES_TEST_ENVIRONMENT
            else:
                env = self.HSDES_PROD_ENVIRONMENT
        self.api = EsApi(env, username, password)
        self.base_url = self.api.base_url
        self.support_dict = HSDES_FPGA_SUPPORT_REVERSE_KEY_DICT

    #---------------------------------------------------------------------------------------
    def da_list_families(self):
        """ 
        Get all hsdes families. 
        """
        try:            
            qry = self.api.Query()            
            #components = qry.get_records('select support.filing_project where tenant = "fpga" and subject = "support"',count=1000)
            components = qry.get_records('select fpga.dyn_lookup.filing_project where fpga.dyn_lookup.value = "Undecided"')
            families = []        
            if components != None:
                for component in components:
                    family = component['fpga.dyn_lookup.filing_project']
                    if family not in families:
                        families.append(family)                
            return families
        except Exception as exc:
            raise
    #---------------------------------------------------------------------------------------
    def da_list_releases(self):
        """ 
        Get all hsdes families. 
        """
        try:            
            qry = self.api.Query()            
            components = qry.get_records("select component.unique_release where tenant = 'fpga' and subject = 'component' and component.subjects_used CONTAINS 'support' and status='shadow' and family IS_NOT_EMPTY and component.unique_release IS_NOT_EMPTY")
            releases = []
            if releases != None:
                for component in components:
                    release = component['component.unique_release']
                    if release not in releases:
                        releases.append(release)                
            return releases
        except Exception as exc:
            raise
    #---------------------------------------------------------------------------------------
    def da_list_components(self):
        """ 
        Get all hsdes families. 
        """
        try:            
            qry = self.api.Query()            
            components = qry.get_records("select component.name where tenant = 'fpga' and subject = 'component' and component.subjects_used CONTAINS 'support'")
            component_names = []
            if components != None:
                for component in components:
                    name = component['component.name']
                    if name not in component_names:
                        component_names.append(name)                
            return component_names
        except Exception as exc:
            raise


    #---------------------------------------------------------------------------------------
    def list_families(self):
        """ 
        Get all hsdes families. 
        """
        try:            
            qry = self.api.Query()            
            components = qry.get_records('select family.name where tenant = "release_central" and subject = "family" and family.hsdes_tenant = "fpga" and family.name STARTS_WITH "sw."')
            families = []        
            if components != None:
                for component in components:
                    family = component['family.name']
                    if family not in families:
                        families.append(family)                
            return families
        except Exception as exc:
            raise
            
    #---------------------------------------------------------------------------------------
    def list_releases(self):
        """ 
        Get hsdes releases. 
        """
        try:            
            qry = self.api.Query()            
            components = qry.get_records("select component.unique_release where tenant = 'fpga' and subject = 'component' and status= 'shadow' and family IS_NOT_EMPTY and component.unique_release IS_NOT_EMPTY")
            releases = []
            if releases != None:
                for component in components:
                    release = component['component.unique_release']
                    if release not in releases:
                        releases.append(release)                
            return releases
        except Exception as exc:
            raise
            
    #---------------------------------------------------------------------------------------
    def list_releases_by_family(self, family):
        """ 
        Get hsdes releases for a given family. 
        """
        try:            
            qry = self.api.Query()            
            components = qry.get_records("select component.name where tenant = 'fpga' and subject = 'component' and status= 'shadow' and family = '%s' and component.unique_release IS_NOT_EMPTY" % (family))
            releases = []
            if releases != None:
                for component in components:
                    release = component['component.name']
                    if release not in releases:
                        releases.append(release)                
            return releases
        except Exception:
            raise
        
    #---------------------------------------------------------------------------------------
    def list_components(self):
        """ 
        Get all hsdes components. 
        """
        try:            
            qry = self.api.Query()            
            components = qry.get_records("select component.name where tenant = 'fpga' and subject = 'component' and status= 'tree_local' and component.release_affected IS_NOT_EMPTY and component.name IS_NOT_EMPTY")        
            component_names = []
            if components != None:
                for component in components:
                    name = component['component.name']
                    if name not in component_names:
                        component_names.append(name)                
            return component_names
        except Exception as exc:
            raise
            
    #---------------------------------------------------------------------------------------
    def list_components_by_release(self, release):
        """ 
        Get hsdes components for a given release. 
        """
        try:            
            qry = self.api.Query()            
            components = qry.get_records("select component.name where tenant = 'fpga' and subject = 'component' and status= 'tree_local' and component.name IS_NOT_EMPTY and component.release_affected = '%s' " % (release))        
            component_names = []        
            if components != None:
                for component in components:
                    name = component['component.name']
                    if name not in component_names:
                        component_names.append(name)                
            return component_names
        except Exception:
            raise
    
    #---------------------------------------------------------------------------------------
    def list_areas(self):
        """
        Get All areas defined in HsdEs
        """
        try:            
            qry = self.api.Query()  
            components = qry.get_records("select fpga.component.area where tenant = 'fpga' and subject = 'component' and fpga.component.area IS_NOT_EMPTY and status= 'tree_local'")

            areas = []        
            if components != None:
                for component in components:
                    area = component['fpga.component.area']

                    if area not in areas:
                        areas.append(area)                
            return areas
        except Exception:
            raise
        
    #---------------------------------------------------------------------------------------
    def list_areas_by_release(self, release):
        """ 
        Get hsdes areas for a given release. 
        """
        try:            
            qry = self.api.Query()            
            components = qry.get_records("select fpga.component.area where tenant = 'fpga' and subject = 'component' and fpga.component.area IS_NOT_EMPTY and status= 'tree_local' and component.release_affected = '%s' " % (release))        
            areas = []        
            if components != None:
                for component in components:
                    area = component['fpga.component.area']

                    if area not in areas:
                        areas.append(area)                
            return areas
        except Exception:
            raise

    #---------------------------------------------------------------------------------------
    def get_field_lookup(self, field):        
        """
        Get All lookup values for a given field HsdEs. 
        """
        try:            
            lookup = self.api.Lookup()
            lookups = lookup.get_lookup_data(field)
            result = []        
            if lookups != None:
                for lookup in lookups:
                    name = lookup['sys_lookup.value']
                    result.append(name)                
            return result
        except Exception as exc:
            raise

    #---------------------------------------------------------------------------------------
    def list_exposures(self):        
        """
        Get All Exposures defined in HsdEs fpga_sw.bug.exposure. It is similar to the FB list_priorities.
          fb.priority == bug.exposure
        """
        try:        
            result = self.get_field_lookup('bug.exposure')
            return result
        except Exception as exc:
            raise
    
    #---------------------------------------------------------------------------------------
    def list_report_types(self):
        """
        Get All report_type defined in HsdEs fpga_sw.bug. It replaces the list_categories
          FB Category ==> bug.report_type                
        """
        try:                    
            result = self.get_field_lookup('bug.report_type')
            return result
        except Exception as exc:
            raise    
        
    #---------------------------------------------------------------------------------------
    def search(self, q, cols=None, subject=None):
        """
        Search for a list of columns based on the "q" string 
        cols is a string with comma delimiter to seperate column names
        The column name are the field name in HSD-ES UI
        """  
        try:            
            search_string = ""
            col_names = []
            hsdes_subject = self.HSDES_BUG_SUBJECT
            if subject:
                hsdes_subject = subject
            if cols:
                for col in cols.split(','):
                    if hsdes_subject == self.HSDES_BUG_SUBJECT:
                        if col in HSDES_FPGA_BUG_KEY_DICT:
                            col_names.append(HSDES_FPGA_BUG_KEY_DICT.get(col))
                    elif hsdes_subject == self.HSDES_AR_SUBJECT:
                        if col in HSDES_FPGA_AR_KEY_DICT:
                            col_names.append(HSDES_FPGA_AR_KEY_DICT.get(col))                        
                    else:
                        if col in HSDES_FPGA_SUPPORT_KEY_DICT:
                            col_names.append(HSDES_FPGA_SUPPORT_KEY_DICT.get(col))                                
            else:                
                if hsdes_subject == self.HSDES_BUG_SUBJECT:
                    col_names = list(HSDES_FPGA_BUG_KEY_DICT.values())
                elif hsdes_subject == self.HSDES_AR_SUBJECT:
                    col_names = list(HSDES_FPGA_AR_KEY_DICT.values())
                else:
                    col_names = list(HSDES_FPGA_SUPPORT_KEY_DICT.values())                                        

            artcl = self.api.Article()
            data = artcl.get_data(q, col_names)            
            attributes = {}
            if data:
                for key in list(data.keys()):
                    if hsdes_subject == self.HSDES_BUG_SUBJECT:
                        if key in HSDES_FPGA_BUG_REVERSE_KEY_DICT:
                            attributes[HSDES_FPGA_BUG_REVERSE_KEY_DICT.get(key, key)] = data[key]
                    elif hsdes_subject == self.HSDES_AR_SUBJECT:
                        if key in HSDES_FPGA_AR_REVERSE_KEY_DICT:
                            attributes[HSDES_FPGA_AR_REVERSE_KEY_DICT.get(key, key)] = data[key]                            
                    else:
                        if key in HSDES_FPGA_SUPPORT_REVERSE_KEY_DICT:
                            attributes[HSDES_FPGA_SUPPORT_REVERSE_KEY_DICT.get(key, key)] = data[key]                                                    
            if 'comments' in attributes:
                attributes['comments'] = artcl.get_comments()
            return attributes        
        except Exception as exc:
            raise        
    
    #---------------------------------------------------------------------------------------
    def query_search(self,eql,start_at=0,count=1000):
        """ Using EQL https://wiki.ith.intel.com/display/HSDESWIKI/EQL+-+ES+Query+Language to search. It will be very flexible to control your query.
        Example:
        bugs = hsdes.search("select id,title where tenant='fpga' AND subject='bug' AND updated_date GREATER_THAN MinutesAgo(15)")
        """
        
        try:            
            result = []
            qry = self.api.Query()
            result = qry.get_records(eql, start_at, count)            
            return result
        except Exception as exc:
            raise            

    #---------------------------------------------------------------------------------------
    def queryid_search(self,query_id,start_at=0):
        """ Searches and returns an output of an existing built query 
        """
        
        try:            
            result = []
            qry = self.api.Query()
            result = qry.get_query(query_id, start_at)            
            return result
        except Exception as exc:
            raise            
                        

    #---------------------------------------------------------------------------------------
    def new_bug(self, title, description, family, release, component, found_in, exposure='3-medium', 
                    owner=None, report_type=None, send_mail=None):
        """
        Create a New HsdEs BUG.
        The corresponding function is new_case in fogbugz.py
        To create a new bug, the following fileds are mandatory: title,description,family,bug.found_in,bug.exposure,component,release
        owner value has to be an Intel idsid
        """        
        try:
            artcl = self.api.Article()
            new_artcl = artcl.newArticle(self.HSDES_TENANT, self.HSDES_BUG_SUBJECT)        

            new_artcl.set('title', title)
            new_artcl.set('description', description)
            new_artcl.set('family', family)
            new_artcl.set('release', release)
            new_artcl.set('component', component)
            new_artcl.set('bug.found_in', found_in)
            new_artcl.set('bug.exposure', exposure)
            if report_type: new_artcl.set('bug.report_type', report_type)
            if owner:       new_artcl.set('owner', owner)
            if send_mail:   new_artcl.set('send_mail', send_mail)
            new_id = artcl.insert(new_artcl)
            return new_id
        except Exception as exc:
            raise exc
            #return None
                
    #---------------------------------------------------------------------------------------
    def new_ar(self, owner, bug_id, planned_in, description=None, ar_type=None, title=None, send_mail=None):
        """
        Create a New HsdEs ar   
        To create a new ar, the following fileds are mandatory: title,owner
        owner value has to be an Intel idsid
        """        
        try:
            artcl = self.api.Article()
            new_artcl = artcl.newArticle(self.HSDES_TENANT, self.HSDES_AR_SUBJECT)        

            if ar_type is None:
                ar_type = 'put request'
            if description is None:
                description = 'Please approve the put request'
            new_artcl.set('owner', owner)            
            new_artcl.set('parent_id', bug_id)        
            new_artcl.set('priority', '2-high')            
            new_artcl.set('description', description)
            new_artcl.set('fpga.ar.ar_type', ar_type)
            new_artcl.set('fpga.ar.planned_in', planned_in)

            bug = self.search(q=bug_id, cols="title,family,release,component,area")
            if bug:
                new_artcl.set('family', bug['family'])
                new_artcl.set('release',  bug['release'])
                new_artcl.set('component',  bug['component'])
                new_artcl.set('fpga.ar.area',  bug['area'])            
                
            if title is None:
                title = bug['title']
            new_artcl.set('title', title)
            if send_mail:   new_artcl.set('send_mail', send_mail)
            new_id = artcl.insert(new_artcl)
            return new_id 
        except Exception as exc:
            raise
            #return None
   

    #---------------------------------------------------------------------------------------
    def new_support(self, title, description, family, release, component, issue_type, exposure='3-medium', filing_project=None, 
                    owner=None, submitted_by=None, fpga_device=None, milestone=None, fpga_resource=None, fpga_milestone=None, fpga_release_note=None,  fpga_year=None, fpga_ww=None,  fpga_sub_ww=None, ext_case_id=None, customer_facing_comments=None, cth_tool=None, cth_tool_version=None, cth_domain=None, cth_milestone=None, tag=None, send_mail=None ):
        """
        Create a New HsdEs SUPPORT.
        The corresponding function is new_case in fogbugz.py
        To create a new bug, the following fileds are mandatory: title,description,family,release,component,issue_type, ###filing_project,fpga_device,fpga_milestone
        owner value has to be an Intel idsid
        """        
        try:
            artcl = self.api.Article()
            new_artcl = artcl.newArticle(self.HSDES_TENANT, self.HSDES_SUPPORT_SUBJECT)        

            new_artcl.set('title', title)
            new_artcl.set('description', description)
            new_artcl.set('family', family)
            new_artcl.set('release', release)
            new_artcl.set('component', component)           
            new_artcl.set('support.issue_type', issue_type)           

            if filing_project:      new_artcl.set('support.filing_project', filing_project)
            if owner:               new_artcl.set('owner', owner)
            if submitted_by:        new_artcl.set('submitted_by', submitted_by)
            if send_mail:           new_artcl.set('send_mail', send_mail)
            if fpga_device:         new_artcl.set('fpga.support.fpga_device', fpga_device)
            if milestone:           new_artcl.set('fpga.support.milestone', milestone)
            if fpga_resource:       new_artcl.set('fpga.support.fpga_resource', fpga_resource)
            if fpga_milestone:      new_artcl.set('fpga.support.fpga_milestone', fpga_milestone)
            if fpga_release_note:   new_artcl.set('fpga.support.fpga_release_note', fpga_release_note)
            if fpga_year:           new_artcl.set('fpga.support.fpga_year', fpga_year)
            if fpga_ww:             new_artcl.set('fpga.support.fpga_ww', fpga_ww)
            if fpga_sub_ww:         new_artcl.set('fpga.support.fpga_sub_ww', fpga_sub_ww)
            if cth_tool:            new_artcl.set('fpga.support.cth_tool', cth_tool)
            if cth_tool_version:    new_artcl.set('fpga.support.cth_tool_version', cth_tool_version)
            if cth_domain:          new_artcl.set('fpga.support.cth_domain', cth_domain)
            if cth_milestone:       new_artcl.set('fpga.support.cth_milestone', cth_milestone)
            if ext_case_id:         new_artcl.set('fpga.support.ext_case_id', ext_case_id)
            if customer_facing_comments: new_artcl.set('fpga.support.customer_facing_comments', customer_facing_comments)
            if tag:                 new_artcl.set('tag', tag)
          
            new_id = artcl.insert(new_artcl)
            return new_id
        except Exception as exc:
            raise exc
            #return None
    #---------------------------------------------------------------------------------------
    def new_approval(self,owner,support_id, title=None, description=None, deliverable=None, notify=None, send_mail=None):
            """
            Create a New HsdES APPROVAL
            To create a new approval, the following fields are mandatory: title. owner
            If support_id is provided, the approval will be created as a dependent approval to the support_id provided.
            Owner value has to be a valid Intel idsid
            """
            try:
                artcl = self.api.Article()
                new_artcl = artcl.newArticle(self.HSDES_TENANT, self.HSDES_APPROVAL_SUBJECT)
                
                new_artcl.set('title', title)
                new_artcl.set('owner', owner)
                new_artcl.set('parent_id', support_id)
                                                                            
                if send_mail:       new_artcl.set('send_mail', send_mail)
                if description:     new_artcl.set('description', description)
                if notify:          new_artcl.set('notify', notify)
                if deliverable:     new_artcl.set('fpga.approval.dmx_deliverable', deliverable)

                new_id = artcl.insert(new_artcl)
 
                return new_id
            except Exception as exc:
                raise exc

    #---------------------------------------------------------------------------------------
    def new_work_item(self, title, description, family, release, work_item_type, stepping=None, deliverable=None, found_in=None ,owner=None, send_mail=None, tag=None):
        """
        Create a New HsdEs SUPPORT.
        The corresponding function is new_case in fogbugz.py
        To create a new bug, the following fileds are mandatory: title,description,family,release,component,issue_type, ###filing_project,fpga_device,fpga_milestone
        owner value has to be an Intel idsid
        """        
        try:
            artcl = self.api.Article()
            new_artcl = artcl.newArticle(self.HSDES_TENANT, self.HSDES_WORK_ITEM_SUBJECT)        

            new_artcl.set('title', title)
            new_artcl.set('description', description)
            new_artcl.set('family', family)
            new_artcl.set('release', release)
            new_artcl.set('work_item.type', work_item_type)

            if owner:               new_artcl.set('owner', owner)
            if send_mail:           new_artcl.set('send_mail', send_mail)
            if stepping:            new_artcl.set('fpga.work_item.stepping', stepping)
            if found_in:            new_artcl.set('fpga.work_item.found_in', found_in)
            if deliverable:         new_artcl.set('fpga.work_item.dmx_deliverable', deliverable)
            if tag:                 new_artcl.set('tag', tag)

            new_id = artcl.insert(new_artcl)
            return new_id
        except Exception as exc:
            raise exc

    #---------------------------------------------------------------------------------------
    def query_bugs(self,*args, **kwargs):
        """ Get hsdes bug id list by query the criteria such as status, family and report_type
            The returns list of bug id. It is corresponding query_cases in fogbugz.py.
        Example:
        bugs = hsdes.query_bugs(status="open", family="sw.Quartus Suite")
        """
        search_string = ""        
        for criteria in list(HSDES_FPGA_BUG_KEY_DICT.keys()) :    
            if kwargs.get(criteria):
                search_string += " AND %s='%s'" % (criteria, kwargs.get(criteria))
        try:            
            result = []
            qry = self.api.Query()
            bugs = qry.get_records('select id where tenant = "fpga" and subject = "bug" ' + search_string)
            if bugs != None:
                for bug in bugs:
                    bug_id = bug['id']
                    result.append(bug_id)                
            return result
        except Exception as exc:
            raise   
        
    #---------------------------------------------------------------------------------------
    def query_ars(self,*args, **kwargs):
        """ Get hsdes ar id list by query the criteria such as status, family and report_type
            The returns list of bug id. It is corresponding query_cases in fogbugz.py.
        Example:
        ars = hsdes.query_ars(status="not done", family="sw.Quartus Suite")
        """
        search_string = ""        
        for criteria in list(HSDES_FPGA_AR_KEY_DICT.keys()) :    
            if kwargs.get(criteria):
                search_string += " AND %s='%s'" % (criteria, kwargs.get(criteria))
        try:            
            result = []
            qry = self.api.Query()
            ars = qry.get_records('select id where tenant = "fpga" and subject = "ar" ' + search_string)
            if ars != None:
                for ar in ars:
                    ar_id = ar['id']
                    result.append(ar_id)                
            return result
        except Exception as exc:
            raise        

    #---------------------------------------------------------------------------------------
    def query_supports(self,*args, **kwargs):
        """ Get hsdes support id list by query the criteria such as status, family and report_type
            The returns list of support id. It is corresponding query_cases in fogbugz.py.
        Example:
        supports = hsdes.query_supports(status="open", component="tool.hsd")
        """
        search_string = ""        
        for criteria in list(HSDES_FPGA_SUPPORT_KEY_DICT.keys()) :    
            if kwargs.get(criteria):
                search_string += " AND %s='%s'" % (criteria.replace('__','.'), kwargs.get(criteria))
        try:            
            result = []
            qry = self.api.Query()
            supports = qry.get_records('select id where tenant = "fpga" and subject = "support" ' + search_string)
            if supports != None:
                for support in supports:
                    support_id = support['id']
                    result.append(support_id)                
            return result
        except Exception as exc:
            raise   

    #---------------------------------------------------------------------------------------
    def set_bug_status(self, bug_id, status, reason, comment=None, send_mail=True): 
        """ set given status for specific hsdes bug
            return True or Exception
            It is co set_case_status in HSDES
        Example:
        self.hsdes.set_bug_status(bug_id=123456789, status="rejected",reason="wont_fix", comment="unittest test_set_bug_status to set the status via API", send_mail=True)
        """    
        if not bug_id:
            raise Error("must specify hsdes bug id")
         
        if status:            
            if not reason:
                raise Error("must specify hsdes reason for the new status " + status)

        if not status and not comment:
            return
        
        try:
            artcl = self.api.Article()
            artcl.load(str(bug_id))
            if status:
                artcl.set('status',status)
                artcl.set('reason',reason)
                if send_mail:
                    artcl.set('send_mail',send_mail)
                artcl.update()
            if comment:                
                artcl.insert_comment(comment)                    
            return True
        except Exception as exc:
            raise


    #---------------------------------------------------------------------------------------
    def upload_support(self, support_id, upload_file, title=None, file_name=None): 
        """ uploads attachment to support article
            return True or Exception
        Example:
        self.hsdes.upload_support(support_id=1306794825, upload_file='/p/psg/data/jwquah/karen_mask.csv') 
        """    
        if not support_id:
            raise Error("must specify hsdes support id")
  
        try:
            artcl = self.api.Article()
            artcl.load(str(support_id))
            if not upload_file:
                raise Error("must specify a file for upload")
            if not title:       title = re.split('\/',upload_file)[-1]
            if not file_name:   file_name = re.split('\/',upload_file)[-1]
                             
            artcl.upload(upload_file, title, file_name)
                      
            return True
        except Exception as exc:
            raise     


    #---------------------------------------------------------------------------------------
    def set_support_status(self, support_id, status, reason, comment=None, send_mail=True, fpga_release_status=None): 
        """ set given status for specific hsdes support
            return True or Exception
            It is co set_case_status in HSDES
        Example:
        self.hsdes.set_support_status(support_id=1404982803, status='complete', reason='user_verified', comment='Verified version', send_mail=True)
        """    
        if not support_id:
            raise Error("must specify hsdes support id")
         
        if status:            
            if not reason:
                raise Error("must specify hsdes reason for the new status " + status)

        if not status and not comment:
            return
        
        try:
            artcl = self.api.Article()
            artcl.load(str(support_id))
            if status:
                artcl.set('status',status)
                artcl.set('reason',reason)               
                if send_mail:
                    artcl.set('send_mail',send_mail)
                if fpga_release_status:
                    artcl.set('fpga.support.fpga_release_status',fpga_release_status)                    
                artcl.update()
            if comment:                
                artcl.insert_comment(comment)                    
            return True
        except Exception as exc:
            raise            
    
    #---------------------------------------------------------------------------------------
    def set_bug_attributes(self, *args, **kwargs):
        """ set given attributs for a specific hsdes case
            return True or False
            see the keys of HSDES_FPGA_BUG_KEY_DICT for supported arguments
        Example:
            resp = hsdes.set_bug_attributes(bug_id=1306107802, status="rejected",reason="wont_fix", exposure="2-high", comment="unittest test_set_bug_status to set the status")
        """         
        bug = kwargs.get("bug_id", None)
        if not bug:
            raise Error("must specify hsdes bug_id")
        
        comment = kwargs.get("comment", None)
        try:
            artcl = self.api.Article()
            artcl.load(bug)
            for key in list(kwargs.keys()):
                if key in HSDES_FPGA_BUG_KEY_DICT:                

                    artcl.set(HSDES_FPGA_BUG_KEY_DICT.get(key,key),kwargs[key]) 

            artcl.update()
            if comment: 
                artcl.insert_comment(comment)  
            return True
        except Exception as exc:
            raise

    #---------------------------------------------------------------------------------------
    def set_ar_attributes(self, *args, **kwargs):
        """ set given attributs for a specific hsdes case
            return True or False
            see the keys of HSDES_FPGA_AR_KEY_DICT for supported arguments
        Example:
            resp = hsdes.set_ar_attributes(ar_id=1306512772, status="wont_do",priority="2-high", comment="unittest set_ar_attributes to set the status to wont_do")
        """         
        ar = kwargs.get("ar_id", None)
        if not ar:
            raise Error("must specify hsdes ar_id")
        
        comment = kwargs.get("comment", None)
        try:
            artcl = self.api.Article()
            artcl.load(ar)
            for key in list(kwargs.keys()):
                if key in HSDES_FPGA_AR_KEY_DICT:
                    artcl.set(HSDES_FPGA_AR_KEY_DICT.get(key,key),kwargs[key]) 

            artcl.update()
            if comment: 
                artcl.insert_comment(comment)  
            return True
        except Exception as exc:
            raise

    #---------------------------------------------------------------------------------------
    def set_support_attributes(self, *args, **kwargs):
        """ set given attributs for a specific hsdes case
            return True or False
            see the keys of HSDES_FPGA_SUPPORT_KEY_DICT for supported arguments
        Example:
            resp = hsdes.set_support_attributes(support_id=1404982803, customer_vendor='Mentor Graphics', filing_project='nightfury', fpga_device='nf', fpga_year='2018', comment='foobar')
        """         
        support = kwargs.get("support_id", None)
        if not support:
            raise Error("must specify hsdes support_id")
        
        comment = kwargs.get("comment", None)
        try:
            artcl = self.api.Article()
            artcl.load(support)
            for key in list(kwargs.keys()):
                if key in HSDES_FPGA_SUPPORT_KEY_DICT:                

                    artcl.set(HSDES_FPGA_SUPPORT_KEY_DICT.get(key,key),kwargs[key]) 

            artcl.update()
            if comment: 
                artcl.insert_comment(comment)  
            return True
        except Exception as exc:
            raise

    #---------------------------------------------------------------------------------------
    def set_work_item_attributes(self, *args, **kwargs):
        """ set given attributss for a specific hsdes case
            return True or False
            see the keys of HSDES_FPGA_WORK_ITEM_KEY_DICT for supported arguments
        Example:
            resp = hsdes.set_work_item_attributes(work_item_id=1404982803, comment='foobar')
        """         
        support = kwargs.get("work_item_id", None)
        if not support:
            raise Error("must specify hsdes work_item_id")
        
        comment = kwargs.get("comment", None)
        try:
            artcl = self.api.Article()
            b = artcl.load(support)
            
            for key in list(kwargs.keys()):
                if key in HSDES_FPGA_WORK_ITEM_KEY_DICT:                
                    artcl.set(HSDES_FPGA_WORK_ITEM_KEY_DICT.get(key,key),kwargs[key]) 

            artcl.update()
            if comment: 
                artcl.insert_comment(comment)  
            return True
        except Exception as exc:
            raise
    #---------------------------------------------------------------------------------------
    def set_component_attributes(self, *args, **kwargs):
        """ set given attributs for a specific hsdes case
            return True or False
            see the keys of HSDES_FPGA_COMPONENT_KEY_DICT for supported arguments
        Example:
            resp = hsdes.set_component_attributes(support_id=1404982803, customer_vendor='Mentor Graphics', filing_project='nightfury', fpga_device='nf', fpga_year='2018', comment='foobar')
        """         
        component = kwargs.get("component_id", None)
        if not component:
            raise Error("must specify hsdes component_id")
        
        try:
            artcl = self.api.Article()
            artcl.load(component)
            for key in list(kwargs.keys()):
                if key in HSDES_FPGA_COMPONENT_KEY_DICT:                
                    artcl.set('send_mail',False)
                    artcl.set(HSDES_FPGA_COMPONENT_KEY_DICT.get(key,key),kwargs[key]) 

            artcl.update()
            return True
        except Exception as exc:
            raise

    #---------------------------------------------------------------------------------------
    def get_bug_attributes(self, bug_id, cols=None):
        """
            Get all attributs in HSDES_FPGA_BUG_KEY_DICT for a specific hsdes bug
            Returns a dict containing attributes
        Example:
            attributes = hsdes.get_bug_attributs(1306329150)
        """
        attributes = None

        if not bug_id:
            raise Error("must specify hsdes bug number")

        hsdes_cols = {}
        if cols:
            hsdes_cols = [HSDES_FPGA_BUG_KEY_DICT.get(col,col) for col in cols]
        else:
            hsdes_cols = list(HSDES_FPGA_BUG_KEY_DICT.values())                

        try:
            artcl = self.api.Article()            
            artcl.get_data(str(bug_id), hsdes_cols)            
            attributes = {}
            if artcl.data:
                bug = artcl.data
                for key in list(bug.keys()):
                    if key in HSDES_FPGA_BUG_REVERSE_KEY_DICT:
                        attributes[HSDES_FPGA_BUG_REVERSE_KEY_DICT.get(key, key)] = bug[key] 
            if 'comments' in attributes:
                attributes['comments'] = artcl.get_comments()
            return attributes
        except Exception as exc:
            raise        

    #---------------------------------------------------------------------------------------
    def get_ar_attributes(self, ar_id, cols=None):
        """
            Get all attributs in HSDES_FPGA_AR_KEY_DICT for a specific hsdes ar
            Returns a dict containing attributes
        Example:
            attributes = hsdes.get_ar_attributs(1306329150)
        """
        attributes = None

        if not ar_id:
            raise Error("must specify hsdes ar number")

        hsdes_cols = {}
        if cols:
            hsdes_cols = [HSDES_FPGA_AR_KEY_DICT.get(col,col) for col in cols]
        else:
            hsdes_cols = list(HSDES_FPGA_AR_KEY_DICT.values())                

        try:
            artcl = self.api.Article()            
            artcl.get_data(str(ar_id), hsdes_cols)            
            attributes = {}
            if artcl.data:
                ar = artcl.data
                for key in list(ar.keys()):
                    if key in HSDES_FPGA_AR_REVERSE_KEY_DICT:
                        attributes[HSDES_FPGA_AR_REVERSE_KEY_DICT.get(key, key)] = ar[key] 
            if 'comments' in attributes:
                attributes['comments'] = artcl.get_comments()
            return attributes
        except Exception as exc:
            raise        
                
    #---------------------------------------------------------------------------------------
    def get_ar_status(self, ar_id):
        status = None

        if not ar_id:
            raise Error("must specify hsdes ar number")

        try:
            artcl = self.api.Article()            
            ar = artcl.get_data(str(ar_id), ['status'])                        
            if ar: status = ar['status']                
            return status
        except Exception as exc:
            #return None
            raise

    #---------------------------------------------------------------------------------------
    def get_hsdes_id(self,fb_id):
        """ Using EQL to search by fb_id and returns the first one.
        Example:
        fb_id = 450913
        hsdes_id = self.hsdes.get_hsdes_id(fb_id)
        """        
        try:            
            result = []
            search = "select id,title where tenant='fpga' AND (fpga.bug.fb_id='{0}' OR fpga.ar.fb_id='{0}' OR fpga.support.fb_id='{0}')".format(fb_id) 
            qry = self.api.Query()
            result = qry.get_records(search)
            if not result:
                return None
            else:
                return result[0]["id"]                
        except Exception as exc:
            raise            
        
    #---------------------------------------------------------------------------------------
    def get_history(self, id, cols=None):
        """
            Get all history for a given article
            Returns a list with asked cols 
        Example:
            historys = hsdes.get_history(1306329150, "id,title,owner,updated_by,updated_date")
        """
        historys = None
        if not cols:
            cols = "id,title,owner,updated_by,updated_date"
        if not id:
            raise Error("must specify hsdes id number")

        try:
            artcl = self.api.Article() 
            artcl.load(id)            
            historys = artcl.get_history(cols) 
            return historys
        except Exception as exc:
            raise        

    #-------------------------------------------------------------------------------------
    def get_attachment_metadata(self, id):
        """
        Gets the JSON metadata from the attachment in an existing article
        """
        if not id:
            raise Error("must specify hsdes id number")
        try:
            artcl = self.api.Article()
            artcl.load(id)
            attachments_metadata = artcl.get_attachments_metadata()
            return attachments_metadata
        except Exception:
            raise

    #-------------------------------------------------------------------------------------
    def get_attachment(self, attachment_id):
        """
        Gets the raw binary content from the attachment in an existing article
        """
        if not id:
            raise Error("must specify hsdes id number")
        try:
            artcl = self.api.Article()
            attachment_binary = artcl.download_attachment(attachment_id)

            return attachment_binary
        except Exception:
            raise

####################################################################
