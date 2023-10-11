#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/owner.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr "owner" subcommand plugin
Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2016
All rights reserved.
'''
from __future__ import print_function
from builtins import object
import sys
import os
import logging
import textwrap
import pwd
import re
import csv
from pprint import pprint

from dmx.abnrlib.command import Command, Runner
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.icm import ICManageCLI
import dmx.ecolib.ecosphere
import dmx.ecolib.__init__
from dmx.utillib.arcenv import ARCEnv
IMMUTABLE_ACCOUNT = ['immutable', 'icetnr']

class OwnerError(Exception): pass

class Owner(object):
    '''
    Runner subclass for the abnr owner subcommand
    '''
    def __init__(self, project, variant, config_or_library_or_release=None, libtype=None, all=False, format=None,
                 owner=None, creator=None, designer=None, setowner=None, preview=True):
        '''
        Initialiser for the OwnerRunner class

        :param project:  The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param config: The IC Manage config
        :type config: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param all: Flag to display updaters for configuration
        :type all: bool
        :param format: Format to output the results into
        :type format: str
        '''
        self.project = project
        self.variant = variant
        self.config_or_library_or_release = config_or_library_or_release
        self.libtype = libtype
        self.all = all
        self.format = format
        self.owner = owner
        self.creator = creator
        self.designer = designer
        self.setowner = setowner
        self.preview = preview
        self.cli = ICManageCLI(preview=self.preview)
        self.logger = logging.getLogger(__name__)

        if self.setowner and not self.user_exist(self.setowner):
            raise OwnerError("User {} doesn't exist.".format(self.setowner))

        # If project not given, get project from IP
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise OwnerError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
            if not self.cli.project_exists(self.project):
                raise OwnerError("Project {0} does not exist".format(self.project))
            if not self.cli.variant_exists(self.project, self.variant):
                raise OwnerError("Variant {0} does not exist in project {1}".format(
                                  self.variant, self.project))

        self.cfobj = None
        if self.config_or_library_or_release:
            self.cfobj = ConfigFactory.create_from_icm(self.project, self.variant, self.config_or_library_or_release, libtype=self.libtype)
                    
        if not dmx.ecolib.__init__.LEGACY:
            self.family = dmx.ecolib.ecosphere.EcoSphere().get_family(os.getenv("DB_FAMILY"))

    def run(self):
        '''
        Runs the owner abnr subcommand
        '''
        ret = 0

        if self.setowner:      
            if self.cfobj:
                # If config is given, set the configuration owner property
                properties = self.cfobj.properties
                properties['Owner'] = self.setowner
                self.cfobj.properties = properties
                self.cfobj.save_properties()

                if self.libtype:
                    self.logger.info("{} has been successfully set as Owner for {}/{}:{}@{}".format(self.setowner,
                                     self.project, self.variant, self.libtype, self.config_or_library_or_release))
                else:                
                    self.logger.info("{} has been successfully set as Owner for {}/{}@{}".format(self.setowner, 
                                     self.project, self.variant, self.cfobj.config))
            else:
                ### set the variant owner property
                properties = {}
                properties['Owner'] = self.setowner
                if self.cli.add_variant_properties(self.project, self.variant, properties):
                    self.logger.info("{} has been successfully set as Owner for {}/{}".format(self.setowner, 
                                     self.project, self.variant))
        else:
            # Print output to terminal
            self.print_output()
        return ret

    def print_output(self):        
        
        if self.config_or_library_or_release:
            data = self.get_configuration_designers(self.project, self.variant, self.config_or_library_or_release, self.libtype)
            creator = data[0][1]
            creator_fullname = self.get_full_name(creator)
            owner = data[-1][1]
            owner_fullname = self.get_full_name(owner)
            createdat = data[-1][2]
            if self.format == 'csv':
                w = csv.writer(sys.stdout)
                w.writerow(['owner', 'owner_fullname', 'creator', 'creator_fullname', 'time'])
                w.writerow([owner, owner_fullname, creator, creator_fullname, createdat])
            else:
                if self.owner:
                    print(owner)
                elif self.creator:
                    print(creator)
                else:                        
                    print("Owner: {} ({})".format(owner, owner_fullname))
                    print("Creator: {} ({})".format(creator, creator_fullname))
                    print("Time: {}".format(createdat))

        else:
            owner, createdat = self.get_variant_owner_properties(self.project, self.variant)
            owner_fullname = self.get_full_name(owner)

            if self.format == 'csv':
                w = csv.writer(sys.stdout)
                w.writerow(['owner', 'owner_fullname', 'time'])
                w.writerow([owner, owner_fullname, createdat])
            else:
                if owner:
                    print("Owner: {} ({})".format(owner, owner_fullname))
                else:
                    print("Owner information not found.")                    
                if createdat:                    
                    print("Time: {}".format(createdat))
                else:
                    print("Creation date not found.")                    


    def has_property(self, config, property):
        '''
        Returns True if given property exists for the config object
        '''
        try:
            if config.properties[property]:
                return True                                
        except:
            return False   
        return False                         

    def user_exist(self, user):
        '''
        Returns true if user id exists in UNIX else False
        '''
        try:
            pwd.getpwnam(user)
        except KeyError:
            return False
        return True                        

    def get_configuration_created_time(self, project, variant, config_or_library_or_release, libtype=None):
        '''
        Returns list of revisions, updaters and the date for a configuration
        '''
        ret = self.get_configuration_designers(project, variant, config_or_library_or_release, libtype)
        return ret[0][2]

        if libtype:
            configfile = "//depot/icm/configs/{}/{}/{}/{}.icmCfg".format(project, variant,
                                                                         libtype, config.config)
        else:
            configfile = "//depot/icm/configs/{}/{}/{}.icmCfg".format(project, variant, config.config)

        filelogs = self.cli.get_filelog(configfile)
        for filelog in filelogs:
            m = re.match(r'... #(.*?) change (\d*?) .* \(.*\) \'(.*?) .*', filelog)            
            if m:
                rev = int(m.group(1))
                changelist = m.group(2)
                updater = m.group(3)                
                # Interested only in rev==1, since that is when the config is created
                if rev == 1:
                    return self.get_configuration_updated_time(changelist)
        return None            

    def get_configuration_designers(self, project, variant, config_or_library_or_release, libtype=None):
        '''
        return = [[revision, designer, date], [revision, designer, date], ...]
        example:-
            return = [
                [1, 'lionelta', '2020-09-24T10:26:08.417Z'],
                [2, 'wplim', '2020-09-24T10:26:08.417Z'],
                ... ... ...
            ]
        Note:
            return[0]   is the creator of the object
            return[-1]  is the last modifier of the object
        '''
        if libtype:
            if self.cli.is_name_immutable(config_or_library_or_release):
                release = config_or_library_or_release
                library = self.cli.get_library_from_release(project, variant, libtype, release)
                details = self.cli.get_release_details(project, variant, libtype, library, release)
            else:
                release = ''
                library = config_or_library_or_release
                details = self.cli.get_library_details(project, variant, libtype, library)
        else:
            config = config_or_library_or_release
            details = self.cli.get_config_details(project, variant, config)

        designers = []
        ### Initial creator
        designers.append([1, details['created-by'], details['created']])
        ### Last modifier
        if 'modified' in details and details['modified'] != details['created']:
            owner = details['created-by']
            if 'Owner' in details:
                owner = details['Owner']
            designers.append([2, owner, details['modified']])
        self.logger.debug("get_configuration_designers: {}".format(designers)) 
        return designers

    def get_configuration_updated_time(self, changelist):
        '''
        Return the changelist submitted date and time
        '''
        describe = self.cli.get_change_info(changelist)
        for line in describe:
            m = re.match(r'.* on (.*?)$', line)
            if m:
                time = m.group(1)
                return time
        return None                
   
    def get_configuration_latest_designer(self, project, variant, config, libtype=None):
        '''
        Return the latest designer for a configuration
        '''
        designers = self.get_configuration_designers(project, variant, config, libtype)
        designers.sort()
        rev, designer, time = designers[-1]

        return designer
 
    def get_configuration_creator(self, project, variant, config, libtype=None):
        '''
        Return the configuration's creator
        '''
        designers = self.get_configuration_designers(project, variant, config, libtype)
        creator = None

        for rev, designer, time in designers:            
            if rev == 1:
                creator = designer
        return creator

    def get_variant_owner_properties(self, project, variant):
        '''     
        Returns variant's Owner and Created At property value
        '''
        properties = self.cli.get_variant_properties(project, variant)
        try:
            owner = properties['Owner']
        except:
            owner = ''
        try:                        
            createdat = properties['created']
        except:
            createdat = ''            
        return owner, createdat

    def get_full_name(self, user):
        '''
        Returns user's fullname as registered in UNIX
        '''
        fullname = ''
        if self.user_exist(user):
            unixname = pwd.getpwnam(user).pw_gecos
            if '(' in unixname:
                m = re.match('(.*?)\(', unixname)
                if m:
                    fullname = m.group(1)
            elif ',' in unixname:
                m = re.match('(.*?),', unixname)
                if m:
                    fullname = m.group(1)
            else:
                fullname = unixname                                                        
        return fullname            
