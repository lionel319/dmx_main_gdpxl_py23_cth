#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/washgroup.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: 
    Class that provides API to get information regarding linux groups for different projects.

    By default, it uses cls.DBFILE as the default dbfile.
    This can be overriden by setting the environment variable in cls.ENVVAR_OVERRIDE

'''
from __future__ import print_function

from builtins import object
import os
import logging
import sys
import json
import grp
import pwd
''' (12 Nov 2021)
### We do not have any sort of postsynctrigger for gdpxl yet right now.
### so we have to fall back to still using the old method above, for now.
import imp
postsynctrigger = imp.load_source('pst', '/p/psg/flows/common/icmadmin/prod/icm_home/triggers/icmpm/enforce_icm_protection.py')
'''
LOGGER = logging.getLogger(__name__)


sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
import dmx.ecolib.ecosphere
from dmx.utillib.utils import run_command
import dmx.abnrlib.config_factory



class WashGroupError(Exception): pass

class WashGroup(object):

    # Default database file that keeps the linux groups information
    DBFILE = '/p/psg/flows/common/dmx/dmx_setting_files/washgroups.json'
    ENVVAR_OVERRIDE = 'WASHGROUP_DBFILE'

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.clear_db_cache()
        self.load_db() 
        self.eco = dmx.ecolib.ecosphere.EcoSphere()

        ### This property stores the config factory object that has been ran before.
        ### creating a config_factory object is very time-expensive, and thus, should 
        ### be cached at every possible chance.
        ### self.cf_cache = {
        ###    (project, variant, config) = config_factory_object,
        ###    ...   ...   ...
        ### }
        self.cf_cache = {}

    def get_dbfile(self):
        '''
        If ENVVAR is defined, used the defined dbfile, 
        else, use the default one.

        This provides a way for user do testings.
        '''
        envvar_val = os.getenv(self.ENVVAR_OVERRIDE, False)
        if envvar_val:
            return envvar_val
        return self.DBFILE
   
    def load_db(self, use_cache=True):
        '''
        {u'base': [u'psgeng'],
         u'eip': [u'psgsynopsys', u'psgintel', u'psgship'],
         u'projects': {
            u'avoncrest': [u'psgavc', u'psgt16ff'],
            u'diamondmesa': [u'psgdmd', u'psgt16arm', u'psgt16ff'],
            u'falcon': [u'psgfln', u'psgi10', u'psgi10arm'],
            u'gundersonrock': [u'psggdr', u'psgi10'],
            u'kinneloamesa': [u'psgknl', u'psgi7'],
            u'reynoldsrock': [u'psgrnr', u'psgi10'],
            u'stanislausriver': [u'psgslr'],
            u'valleycrest': [u'psgvlc', u'psgi7'],
            u'wharfrock': [u'psgwhr', u'psgt16ff']}
        "eips": {
            "diamondmesa": ["psgt16arm"],
            "diamondmesa2": ["psgipxsmx_arm", "psgart", "psgcadence", "psgsynopsys"],
            "falcon": ["psgi10arm", "psgrambus"]}
        }
            
        '''
        if not use_cache:
            self.clear_db_cache()
        with open(self.get_dbfile()) as f:
            self._db = json.load(f)
        return self._db

    def clear_db_cache(self):
        self._db = {}

    def get_groups_by_families(self, families, include_eip_groups=False, include_base_groups=False):
        retval = []
        for family in families:
            retval += self.get_groups_by_family(family)
        if include_eip_groups:
            retval += self.get_eip_groups(families=families)
        if include_base_groups:
            retval += self.get_base_groups()
        return sorted(list(set(retval)))


    def get_groups_by_family(self, family):
        if family in self._db['projects']:
            return self._db['projects'][family]
        else:
            return []

    def get_eip_groups(self, families=[], icmprojects=[]):
        retlist = []
        for pro in icmprojects:
            familyname = self.eco.get_family_for_icmproject(pro).name.lower()
            families.append(familyname)
        for familyname in families:
            if familyname and familyname in self._db['eips']:
                retlist.extend(self._db['eips'][familyname])
        return retlist

    def get_base_groups(self):
        return self._db['base']
                  

    def get_groups_by_pvc(self, project, variant, config, include_eip_groups=False, include_base_groups=False):
        cf = self.get_config_factory_by_pvc(project, variant, config)
        icmprojects = cf.get_all_projects()
        return self.get_groups_by_icmprojects(cf.get_all_projects(), include_eip_groups=include_eip_groups, include_base_groups=include_base_groups)

    
    def get_groups_by_icmprojects(self, icmprojects, include_eip_groups=False, include_base_groups=False):
        retval = []
        
        for project in icmprojects:
            ### Special Case for icmproject:SoftIP
            if project == 'SoftIP':
                retval += self.get_groups_for_icmproject_softip()
            else:
                retval += self.get_groups_by_icmproject(project)
        if include_eip_groups:
            retval += self.get_eip_groups(icmprojects=icmprojects)
        if include_base_groups:
            retval += self.get_base_groups()
        return sorted(list(set(retval)))


    def get_groups_by_icmproject(self, icmproject):
        ''' (11 Mar 2021)
        This was an old method. 
        Not accurate. 
        We now getting the group directly from postsynctrigger
        ------------------------------------------------------- 
        '''
        familyname = self.eco.get_family_for_icmproject(icmproject).name.lower()
        if familyname in self._db['projects']:
            return self._db['projects'][familyname]
        else:
            return []

        ''' (12 Nov 2021)
        ### We do not have any sort of postsynctrigger for gdpxl yet right now.
        ### so we have to fall back to still using the old method above, for now.
        return [self.get_groups_by_icmproject_from_protect_table(icmproject)]
        '''

    """ (12 Nov 2021)
    ### We do not have any sort of postsynctrigger for gdpxl yet right now.
    ### so we have to fall back to still using the old method above, for now.
    def get_groups_by_icmproject_from_protect_table(self, icmproject):
        '''
        Calls the postsynctrigger to get the correct linux group
        '''
        return postsynctrigger.get_proj_prot_group(icmproject)
    """

    def get_groups_for_icmproject_softip(self):
        ''' This is a special case. For icmproject:SoftIP 
        - is not a dedicated project 
        - its IPs are used/shared across multiple projects
        - however, in many cases (eg:- sion, when caching the files), we need a place to store the files under a dedicated project disks
        - thus, we forced this special icmproject to be under rnr.
        '''
        return ['psgrnr', 'psgship']


    def get_user_groups(self, userid=None, current_process=False):
        if not userid:
            userid = os.getenv("USER")
        if not current_process:
            ''' 
            ### Strage. grp module seems to be giving inconsistent return values !!!!
            ### no choice. Need to use linux `groups` command
            groups = [g.gr_name for g in grp.getgrall() if userid in g.gr_mem]
            gid = pwd.getpwnam(userid).pw_gid
            groups.append(grp.getgrgid(gid).gr_name)
            '''
            exitcode, stdout, stderr = run_command('groups ' + userid)
            groups = stdout.split()[2:]
        else:
            ### Strage. grp module seems to be giving inconsistent return values !!!!
            ### no choice. Need to use linux `groups` command
            #groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]
            exitcode, stdout, stderr = run_command('groups')
            groups = stdout.split()
        return sorted(groups)


    def get_user_missing_groups_from_accessing_icmprojects(self, userid, icmprojects):
        usergroups = self.get_user_groups(userid)
        projectgroups = self.get_groups_by_icmprojects(icmprojects)
        print("usergroup: {}".format(usergroups))
        print("projgroups:{}".format(projectgroups))
        return sorted(list(set(projectgroups) - set(usergroups)))


    def get_user_missing_groups_from_accessing_pvc(self, userid, project, variant, config):
        cf = self.get_config_factory_by_pvc(project, variant, config)
        icmprojects = cf.get_all_projects()
        return self.get_user_missing_groups_from_accessing_icmprojects(userid, icmprojects)


    def get_config_factory_by_pvc(self, project, variant, config):
        key = (project, variant, config)
        if key not in self.cf_cache:
            cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(project, variant, config)
            self.cf_cache[key] = cf
        return self.cf_cache[key]


