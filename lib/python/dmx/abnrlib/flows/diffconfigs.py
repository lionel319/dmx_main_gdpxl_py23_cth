#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/diffconfigs.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: "diffconfigs" plugin for abnr
Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.
'''
from __future__ import print_function
from builtins import str
from builtins import object
import os
import logging
import textwrap
from tempfile import NamedTemporaryFile
import subprocess
import filecmp
import re
from pprint import pprint, pformat

from dmx.utillib.decorators import memoized
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.icm import ICManageCLI
from dmx.utillib.utils import get_tools_path, run_once
from dmx.utillib.arcenv import ARCEnv
from dmx.abnrlib.flows.bomdetail import BomDetail
from dmx.utillib.utils import run_command
import dmx.ecolib.ecosphere

LOGGER = logging.getLogger(__name__)
NOT_USER_FILES = ['.icminfo', 'icm_pmlog.txt']

class DiffConfigsError(Exception): pass
class ConfigPairError(Exception): pass

@memoized
def is_file_identical(first_path, second_path):
    '''
    Check if files are identical by comparing the content
    '''
    if first_path == second_path:
        return True
    else:   
        icmcli = ICManageCLI(preview=True)
        first_file_digest = icmcli.get_file_digest(first_path)
        second_file_digest = icmcli.get_file_digest(second_path)
        if first_file_digest == second_file_digest:
            return True
        else:
            # Due to RCS string expansion, files could have different digests, but similar content
            # To be sure, run diff2 to ensure if both files are identical
            if is_file_text(first_path) and is_file_text(second_path) and not icmcli.get_file_diff(first_path, second_path):
                return True
            return False

@memoized
def is_file_text(filespec):
    icmcli = ICManageCLI(preview=True)
    type = icmcli.get_file_type(filespec)
    if 'text' in type:
        return True
    else:
        return False        

@run_once
def print_header(first, second, first_width, second_width):
    '''
    Prints the diff header, but only once thanks to the decorator
    '''
    if first._project == second._project and first._variant == second._variant:
        print('# {0:{1}} {2:{3}} {4}'.format('Project/IP', first_width, 'BOM 1' , second_width, 'BOM 2'))
        pv = "{0}/{1}".format(first._project, first._variant)
        #print '# {0:{1}} {2:{3}} {4}'.format(pv, first_width, first._config , second_width, second._config)
        print('# {0:{1}} {2:{3}} {4}'.format(pv, first_width, first.name, second_width, second.name))
        print('# {0:{1}} {2:{3}} {4}'.format('Project/IP/Deliverable', first_width, 'Lib/Rel/BOM', second_width, 'Lib/Rel/BOM'))
    else:
        print('# {0:{1}} {2:{3}} {4}'.format('Project/IP', first_width, 'BOM 1' , second_width, 'BOM 2'))
        pvpv = "{0}/{1}--{2}/{3}".format(first._project, first._variant, second._project, second._variant)
        #print '# {0:{1}} {2:{3}} {4}'.format(pvpv, first_width, first._config, second_width, second._config)
        print('# {0:{1}} {2:{3}} {4}'.format(pvpv, first_width, first.name, second_width, second.name))
        print('# {0:{1}} {2:{3}} {4}'.format('Project/IP/Deliverable', first_width, 'Lib/Rel/BOM', second_width, 'Lib/Rel/BOM'))
 
class ConfigPair(object):
    '''
    Stores pairs of simple configurations from two different composite configuration trees.

    Both configurations do not have to be populated.
    '''

    @classmethod
    def generate_key(cls, project, variant, libtype):
        return '{0}/{1}:{2}'.format(project, variant, libtype)

    @classmethod
    def generate_key_diff_projects(cls, project, variant, second_project, second_variant, libtype):
        return '{0}/{1}--{2}/{3}:{4}'.format(project, variant, second_project, second_variant, libtype)

    def __init__(self, project, variant, libtype, ignore_config_names=False, include_files=False):
        self.__project = project
        self.__variant = variant
        self.__libtype = libtype
        self.__ignore_config_names = ignore_config_names
        self.__include_files = include_files
        self.__first_config = None
        self.__second_config = None
        self.__parent_first_config = None
        self.__parent_second_config = None
        self.__first_files = dict()
        self.__second_files = dict()
        self.__key = None

        self.__logger = logging.getLogger(__name__)

    @property
    def project(self):
        return self.__project

    @property
    def variant(self):
        return self.__variant

    @property
    def libtype(self):
        return self.__libtype

    @property
    def first_config(self):
        return self.__first_config

    @first_config.setter
    def first_config(self, config):
        self.__first_config = config

    @property
    def second_config(self):
        return self.__second_config

    @second_config.setter
    def second_config(self, config):
        self.__second_config = config

    @property
    def parent_first_config(self):
        return self.__parent_first_config

    @parent_first_config.setter
    def parent_first_config(self, config):
        self.__parent_first_config = config       

    @property
    def parent_second_config(self):
        return self.__parent_second_config

    @parent_second_config.setter
    def parent_second_config(self, config):
        self.__parent_second_config = config       

    @property
    def first_files(self):
        return self.__first_files

    @first_files.setter
    def first_files(self, files):
        self.__first_files = files

    @property
    def second_files(self):
        return self.__second_files

    @second_files.setter
    def second_files(self, files):
        self.__second_files = files

    @property
    def ignore_config_names(self):
        return self.__ignore_config_names

    @ignore_config_names.setter
    def ignore_config_names(self, new_ignore_config_names):
        self.__ignore_config_names = new_ignore_config_names
    
    @property
    def include_files(self):
        return self.__include_files

    @include_files.setter
    def include_files(self, new_include_files):
        self.__include_files = new_include_files

    @property
    def key(self):
        '''
        Returns a key so we can hash these objects
        '''
        if not self.__key:
            self.__key = ConfigPair.generate_key(self.project, self.variant, self.libtype)
        return self.__key

    @key.setter
    def key(self, key):
        self.__key = key

    def first_only(self):
        '''
        Returns True if there is only a configuration in the first_config slot
        '''
        return self.first_config and not self.second_config

    def second_only(self):
        '''
        Returns True if there is only a configuration in the second_config slot
        '''
        return self.second_config and not self.first_config

    def both_configs(self):
        '''
        Returns True if there is a config in both slots
        '''
        return self.first_config and self.second_config

    def differ(self):
        '''
        Returns True if both config slots are populated and they differ
        '''
        if not self.both_configs():
            raise ConfigPairError('Tried to diff a config pair but at least one slot is empty')

        differ = False

        if not self.ignore_config_names:
            differ = self.first_config != self.second_config
        else:
            differ = self.first_config.library != self.second_config.library \
                or self.first_config.lib_release != self.second_config.lib_release

        return differ

    def diff_pv(self):
        '''
        Returns True if project/variant pair is different
        '''
        diff = False
        if '-' in self.key:
            diff = True

        return diff          

    def generate_files_dict(self):
        '''
        Generates the files' dictionary for both the first and/or second configuration
        '''
        if self.diff_pv():
            if self.first_config:   
                self.first_files = self.first_config.get_dict_of_files(ignore_project_variant=True)
            if self.second_config:                  
                self.second_files = self.second_config.get_dict_of_files(ignore_project_variant=True)
        else:            
            if self.first_config:            
                self.first_files = self.first_config.get_dict_of_files()
            if self.second_config:            
                self.second_files = self.second_config.get_dict_of_files()

    def differ_files(self, first_width, second_width):
        '''
        Returns a list of files' differences in string format
        '''
        self.generate_files_dict()

        differences = []
        files = set(list(self.first_files.keys()) + list(self.second_files.keys()))                

        for file in files:
            if file in self.first_files and file in self.second_files:
                if self.first_files[file]['filename'] not in NOT_USER_FILES:
                    first_path = "{}/{}#{}".format(self.first_files[file]['directory'],
                                                   self.first_files[file]['filename'],
                                                   self.first_files[file]['version'])
                    second_path = "{}/{}#{}".format(self.second_files[file]['directory'],
                                                    self.second_files[file]['filename'],
                                                    self.second_files[file]['version'])
                    if not is_file_identical(first_path, second_path):
                        f = "! {}".format(file)
                        differences.append(f)
                        f = "! {0:{1}} {2:{3}} {4}".format("Library", first_width, self.first_files[file]['library'], second_width, self.second_files[file]['library'])
                        differences.append(f)
                        f = "! {0:{1}} {2:{3}} {4}".format("Version", first_width, self.first_files[file]['version'], second_width, self.second_files[file]['version'])
                        differences.append(f)
            elif file in self.first_files and file not in self.second_files:
                if self.first_files[file]['filename'] not in NOT_USER_FILES:
                    f = "- {}".format(file)
                    differences.append(f)
                    f = "- {0:{1}} {2:{3}}".format("Library", first_width, self.first_files[file]['library'], second_width)
                    differences.append(f)
                    f = "- {0:{1}} {2:{3}}".format("Version", first_width, self.first_files[file]['version'], second_width)
                    differences.append(f)
            elif file not in self.first_files and file in self.second_files:
                if self.second_files[file]['filename'] not in NOT_USER_FILES:
                    f = "+ {}".format(file)
                    differences.append(f)
                    f = "+ {0:{1}} {2:{3}} {4}".format("Library", first_width, "", second_width, self.second_files[file]['library'])
                    differences.append(f)
                    f = "+ {0:{1}} {2:{3}} {4}".format("Version", first_width, "", second_width, self.second_files[file]['version'])
                    differences.append(f)

        return differences                
        
    def generate_and_print_diff(self, first_width, second_width):
        '''
        Generates the appropriate diff message and prints it
        '''
        pvl = self.format_with_width('{0}/{1}/{2}'.format(
            self.project, self.variant, self.libtype
        ), first_width)
        
        if self.both_configs() and self.differ():
            lrc = self.format_with_width('{0}/{1}/{2}'.format(
                self.first_config.library, self.first_config.lib_release,
                self.first_config.name
            ), second_width)

            if self.diff_pv():   
                pvpvl = self.format_with_width(self.key, first_width)             
                self.print_diff('! {0} {1} {2}/{3}/{4}'.format(
                    pvpvl, lrc, self.second_config.library, self.second_config.lib_release,
                    self.second_config.name
                ))
            else:                          
                self.print_diff('! {0} {1} {2}/{3}/{4}'.format(
                    pvl, lrc, self.second_config.library, self.second_config.lib_release,
                    self.second_config.name
                ))
            if self.include_files:
                differences = self.differ_files(first_width, second_width)
                for d in differences:
                    self.print_diff(d)

        elif self.first_only():
            lrc = self.format_with_width('{0}/{1}/{2}'.format(
                self.first_config.library, self.first_config.lib_release,
                self.first_config.name
            ), second_width)
            self.print_diff('- {0} {1}'.format(pvl, lrc))
            if self.include_files:
                differences = self.differ_files(first_width, second_width)
                for d in differences:
                    self.print_diff(d)
        elif self.second_only():
            space = self.format_with_width('', second_width)
            lrc = '{0}/{1}/{2}'.format(
                self.second_config.library, self.second_config.lib_release,
                self.second_config.name
            )
            self.print_diff('+ {0} {1} {2}'.format(pvl, space, lrc))
            if self.include_files:
                differences = self.differ_files(first_width, second_width)
                for d in differences:
                    self.print_diff(d)

    def print_diff(self, line):
        '''
        Prints the diff line along with the header, if necessary
        '''
        print(line)

    def format_with_width(self, original, width):
        '''
        Formats original so it is width wide.
        '''
        return '{0:{1}}'.format(original, width)

class HTMLParser(object):
    '''
    HTML class to build html strings for display
    '''
    def __init__(self, project, variant, first_config, second_config, pair_lookup, sort_by_libtypes):
        self.project = project
        self.variant = variant
        self.first_config = first_config
        self.second_config = second_config
        self.pair_lookup = pair_lookup   
        self.sort_by_libtypes = sort_by_libtypes
        self.lookup_dict = dict()
        self.html = ""
       
    def build_lookup_dict(self):
        '''
        Build a dict specifically for HTMLParser
        ConfigPair object alone cannot be used for HTMLParser as it lacks information on parents' project, variant, configuration
        Dict will have a keys in the form of project/variant
        Each project/variant will have first_config, second_config and list of ConfigPair objects
        '''
        for key in sorted(self.pair_lookup.keys()):  
            project = self.pair_lookup[key].project
            variant = self.pair_lookup[key].variant
            parent_first_config = self.pair_lookup[key].parent_first_config
            parent_second_config = self.pair_lookup[key].parent_second_config
            if self.pair_lookup[key].diff_pv():                              
                parent_key = key.split(':')[0]
            else:
                parent_key = "{}/{}".format(project, variant)
            if parent_key in self.lookup_dict:
                if parent_first_config:
                    self.lookup_dict[parent_key]['first_config'] = parent_first_config
                if parent_second_config:
                    self.lookup_dict[parent_key]['second_config'] = parent_second_config
                if ((self.pair_lookup[key].both_configs() and self.pair_lookup[key].differ()) or
                    self.pair_lookup[key].first_only() or
                    self.pair_lookup[key].second_only()): 
                    self.pair_lookup[key].generate_files_dict()
                    self.lookup_dict[parent_key]['ConfigPairs'][key] = self.pair_lookup[key]
            else:                
                if ((self.pair_lookup[key].both_configs() and self.pair_lookup[key].differ()) or
                    self.pair_lookup[key].first_only() or
                    self.pair_lookup[key].second_only()): 
                    self.pair_lookup[key].generate_files_dict()
                    self.lookup_dict[parent_key] = dict()
                    self.lookup_dict[parent_key]['first_config'] = parent_first_config
                    self.lookup_dict[parent_key]['second_config'] = parent_second_config
                    self.lookup_dict[parent_key]['ConfigPairs'] = dict()
                    self.lookup_dict[parent_key]['ConfigPairs'][key] = self.pair_lookup[key]
     
    def build_html(self):
        '''
        Builds the html strings to display differences between configurations
        '''
        self.add_header()

        # First table shows the summary of the configurations being compared
        # Add table header
        table_header = "<table border=\"1\"><tr><th>Project/IP</th><th>BOM 1</th><th>BOM 2</th><th>Summary of File Differences</th></tr>"
        self.html = self.html + table_header
    
        # Add the pvc being compared
        html = "<tr><td>{}/{}</td><td>{}</td><td>{}</td><td></td></tr>".format(
                self.project, self.variant, self.first_config, self.second_config)
        self.html = self.html + html

        if self.sort_by_libtypes:
            libtypes = set([y.libtype for x in list(self.lookup_dict.values()) for y in list(x['ConfigPairs'].values())])
            for libtype in libtypes:
                # Add libtype
                html = "<tr><td><a href=\"#{0}\"><font color=\"red\">-{0}</font></a></td><td></td><td></td><td></td></tr>".format(libtype)
                self.html = self.html + html

                for parent_key in sorted(self.lookup_dict.keys()):             
                    parent_first_config = self.lookup_dict[parent_key]['first_config']
                    parent_second_config = self.lookup_dict[parent_key]['second_config']
                    configpairs = self.lookup_dict[parent_key]['ConfigPairs']
                            
                    for key in sorted(configpairs.keys()): 
                        if libtype == configpairs[key].libtype:
                            if configpairs[key].both_configs() and configpairs[key].differ():
                                # Add parent project/variant@configuration
                                html = "<tr><td><a href=\"#{}\"><font color=\"red\">--{}</font></a></td><td>{}</td><td>{}</td><td></td></tr>".format(
                                          key,
                                          parent_key,
                                          parent_first_config, 
                                          parent_second_config)
                                self.html = self.html + html
    
                                summary = self.get_file_comparison_summary(configpairs[key].first_files, 
                                                                           configpairs[key].second_files)
                                # Add simple project/variant/libtype@configuration comparison
                                html = "<tr><td><a href=\"#{0}\"><font color=\"blue\">---{0}</font></a></td><td>{1}/{2}@{3}</td><td>{4}/{5}@{6}</td><td>{7}</td></tr>".format(
                                        key,
                                        configpairs[key].first_config.library, 
                                        configpairs[key].first_config.lib_release,
                                        configpairs[key].first_config.name,
                                        configpairs[key].second_config.library, 
                                        configpairs[key].second_config.lib_release,
                                        configpairs[key].second_config.name,
                                        summary)
                                self.html= self.html + html  
                            elif configpairs[key].first_only():
                                # Add parent project/variant@configuration
                                html = "<tr><td><a href=\"#{}\"><font color=\"red\">--{}</font></a></td><td>{}</td><td></td><td></td></tr>".format(
                                          key,
                                          parent_key,
                                          parent_first_config)
                                self.html = self.html + html
 
                                summary = self.get_file_comparison_summary(first_files = configpairs[key].first_files)
                                # Add simple project/variant/libtype@configuration comparison
                                html = "<tr><td><a href=\"#{0}\"><font color=\"blue\">---{0}</font></a></td><td>{1}/{2}@{3}</td><td></td><td>{4}</td></tr>".format(
                                        key,
                                        configpairs[key].first_config.library, 
                                        configpairs[key].first_config.lib_release,
                                        configpairs[key].first_config.name,
                                        summary)
                                self.html= self.html + html   
                            elif configpairs[key].second_only(): 
                                # Add parent project/variant@configuration
                                html = "<tr><td><a href=\"#{}\"><font color=\"red\">--{}</font></a></td><td></td><td>{}</td><td></td></tr>".format(
                                          key,
                                          parent_key,
                                          parent_second_config)
                                self.html = self.html + html

                                summary = self.get_file_comparison_summary(second_files = configpairs[key].second_files)
                                # Add simple project/variant/libtype@configuration comparison
                                html = "<tr><td><a href=\"#{0}\"><font color=\"blue\">---{0}</font></a></td><td></td><td>{1}/{2}@{3}</td><td>{4}</td></tr>".format(
                                        key,
                                        configpairs[key].second_config.library, 
                                        configpairs[key].second_config.lib_release,
                                        configpairs[key].second_config.name,
                                        summary)
                                self.html= self.html + html 
        else:            
            for parent_key in sorted(self.lookup_dict.keys()):             
                parent_first_config = self.lookup_dict[parent_key]['first_config']
                parent_second_config = self.lookup_dict[parent_key]['second_config']
                configpairs = self.lookup_dict[parent_key]['ConfigPairs']
    
                # Add parent project/variant@configuration
                html = "<tr><td><a href=\"#{0}\"><font color=\"red\">-{0}</font></a></td><td>{1}</td><td>{2}</td><td></td></tr>".format(
                        parent_key,
                        parent_first_config, 
                        parent_second_config)
                self.html = self.html + html

                for key in sorted(configpairs.keys()):                
                    if configpairs[key].both_configs() and configpairs[key].differ():
                        summary = self.get_file_comparison_summary(configpairs[key].first_files, 
                                                               configpairs[key].second_files)
                        # Add simple project/variant/libtype@configuration comparison
                        html = "<tr><td><a href=\"#{0}\"><font color=\"blue\">--{0}</font></a></td><td>{1}/{2}@{3}</td><td>{4}/{5}@{6}</td><td>{7}</td></tr>".format(
                                key,
                                configpairs[key].first_config.library, 
                                configpairs[key].first_config.lib_release,
                                configpairs[key].first_config.name,
                                configpairs[key].second_config.library, 
                                configpairs[key].second_config.lib_release,
                                configpairs[key].second_config.name,
                                summary)
                        self.html= self.html + html  
                    elif configpairs[key].first_only(): 
                        summary = self.get_file_comparison_summary(first_files = configpairs[key].first_files)
                        # Add simple project/variant/libtype@configuration comparison
                        html = "<tr><td><a href=\"#{0}\"><font color=\"blue\">--{0}</font></a></td><td>{1}/{2}@{3}</td><td></td><td>{4}</td></tr>".format(
                                key,
                                configpairs[key].first_config.library, 
                                configpairs[key].first_config.lib_release,
                                configpairs[key].first_config.name,
                                summary)
                        self.html= self.html + html   
                    elif configpairs[key].second_only(): 
                        summary = self.get_file_comparison_summary(second_files = configpairs[key].second_files)
                        # Add simple project/variant/libtype@configuration comparison
                        html = "<tr><td><a href=\"#{0}\"><font color=\"blue\">--{0}</font></a></td><td></td><td>{1}/{2}@{3}</td><td>{4}</td></tr>".format(
                                key,
                                configpairs[key].second_config.library, 
                                configpairs[key].second_config.lib_release,
                                configpairs[key].second_config.name,
                                summary)
                        self.html= self.html + html 
                         
        # Adds /table tag to end table
        table_footer = "</table>"        
        self.html = self.html + table_footer

        # Some line breaks to separate the tables
        self.html = self.html + "<br>"

        # Second table shows a more detailed differences between the configurations
        # Add table header
        table_header = "<table border=\"1\"><tr><th>Project/IP</th><th>BOM 1</th><th>BOM 2</th><th>File Differences</th></tr>"
        self.html = self.html + table_header
    
        # Add the pvc being compared
        html = "<tr><td>{}/{}</td><td>{}</td><td>{}</td><td></td></tr>".format(
                self.project, self.variant, self.first_config, self.second_config)
        self.html = self.html + html

        if self.sort_by_libtypes:
            libtypes = set([y.libtype for x in list(self.lookup_dict.values()) for y in list(x['ConfigPairs'].values())])
            for libtype in libtypes:
                # Add libtype
                html = "<tr><td><a name=\"{0}\"><font color=\"red\">-{0}</font></a></td><td></td><td></td><td></td></tr>".format(libtype)
                self.html = self.html + html

                for parent_key in sorted(self.lookup_dict.keys()):             
                    parent_first_config = self.lookup_dict[parent_key]['first_config']
                    parent_second_config = self.lookup_dict[parent_key]['second_config']
                    configpairs = self.lookup_dict[parent_key]['ConfigPairs']
                            
                    for key in sorted(configpairs.keys()): 
                        if libtype == configpairs[key].libtype:
                            if configpairs[key].both_configs() and configpairs[key].differ():
                                # Add parent project/variant@configuration
                                html = "<tr><td><a name=\"{}\"><font color=\"red\">--{}</font></a></td><td>{}</td><td>{}</td><td></td></tr>".format(
                                      key,
                                      parent_key,
                                      parent_first_config, 
                                      parent_second_config)
                                self.html = self.html + html
    
                                # Add simple project/variant/libtype@configuration
                                html = "<tr><td><a name=\"{0}\"><font color=\"blue\">---{0}</font></a></td><td>{1}/{2}@{3}</td><td>{4}/{5}@{6}</td><td></td></tr>".format(
                                        key,
                                        configpairs[key].first_config.library, 
                                        configpairs[key].first_config.lib_release,
                                        configpairs[key].first_config.name,
                                        configpairs[key].second_config.library, 
                                        configpairs[key].second_config.lib_release,
                                        configpairs[key].second_config.name)
                                self.html= self.html + html 
                               
                                html = self.get_file_comparison(configpairs[key].first_files, configpairs[key].second_files)
                                self.html = self.html + html 
                            elif configpairs[key].first_only():
                                # Add parent project/variant@configuration
                                html = "<tr><td><a name=\"{}\"><font color=\"red\">--{}</font></a></td><td>{}</td><td></td><td></td></tr>".format(
                                          key,
                                          parent_key,
                                          parent_first_config)
                                self.html = self.html + html
 
                                # Add simple project/variant/libtype@configuration comparison
                                html = "<tr><td><a name=\"{0}\"><font color=\"blue\">---{0}</font></a></td><td>{1}/{2}@{3}</td><td></td><td></td></tr>".format(
                                        key,
                                        configpairs[key].first_config.library, 
                                        configpairs[key].first_config.lib_release,
                                        configpairs[key].first_config.name)
                                self.html= self.html + html 

                                html = self.get_file_comparison(configpairs[key].first_files, configpairs[key].second_files)
                                self.html = self.html + html 
                            elif configpairs[key].second_only(): 
                                # Add parent project/variant@configuration
                                html = "<tr><td><a name=\"{}\"><font color=\"red\">--{}</font></a></td><td></td><td>{}</td><td></td></tr>".format(
                                          key,
                                          parent_key,
                                          parent_second_config)
                                self.html = self.html + html

                                # Add simple project/variant/libtype@configuration comparison
                                html = "<tr><td><a name\"{0}\"><font color=\"blue\">---{0}</font></a></td><td></td><td>{1}/{2}@{3}</td><td></td></tr>".format(
                                        key,
                                        configpairs[key].second_config.library, 
                                        configpairs[key].second_config.lib_release,
                                        configpairs[key].second_config.name)
                                self.html= self.html + html 

                                html = self.get_file_comparison(configpairs[key].first_files, configpairs[key].second_files)
                                self.html = self.html + html 

        else:
            for parent_key in sorted(self.lookup_dict.keys()):  
                parent_first_config = self.lookup_dict[parent_key]['first_config']
                parent_second_config = self.lookup_dict[parent_key]['second_config']
                configpairs = self.lookup_dict[parent_key]['ConfigPairs']

                # Add parent project/variant@configuration
                html = "<tr><td><a name=\"{0}\"><font color=\"red\">-{0}</font></a></td><td>{1}</td><td>{2}</td><td></td></tr>".format(
                        parent_key,
                        parent_first_config, 
                        parent_second_config)
                self.html = self.html + html

                for key in sorted(configpairs.keys()):
                    if configpairs[key].both_configs() and configpairs[key].differ():
                        # Add simple project/variant/libtype@configuration comparison
                        html = "<tr><td><a name=\"{0}\"><font color=\"blue\">--{0}</font></a></td><td>{1}/{2}@{3}</td><td>{4}/{5}@{6}</td><td></td></tr>".format(
                                key,
                                configpairs[key].first_config.library, 
                                configpairs[key].first_config.lib_release,
                                configpairs[key].first_config.name,
                                configpairs[key].second_config.library, 
                                configpairs[key].second_config.lib_release,
                                configpairs[key].second_config.name)
                        self.html= self.html + html  
                        html = self.get_file_comparison(configpairs[key].first_files, configpairs[key].second_files)
                        self.html = self.html + html
                    elif configpairs[key].first_only(): 
                        # Add simple project/variant/libtype@configuration comparison
                        html = "<tr><td><a name=\"{0}\"><font color=\"blue\">--{0}</font></a></td><td>{1}/{2}@{3}</td><td></td><td></td></tr>".format(
                                key,
                                configpairs[key].first_config.library, 
                                configpairs[key].first_config.lib_release,
                                configpairs[key].first_config.name)
                        self.html= self.html + html   
                        html = self.get_file_comparison(first_files = configpairs[key].first_files)
                        self.html = self.html + html
                    elif configpairs[key].second_only(): 
                        # Add simple project/variant/libtype@configuration comparison
                        html = "<tr><td><a name=\"{0}\"><font color=\"blue\">--{0}</font></a></td><td></td><td>{1}/{2}@{3}</td><td></td></tr>".format(
                                key,
                                configpairs[key].second_config.library, 
                                configpairs[key].second_config.lib_release,
                                configpairs[key].second_config.name)
                        self.html= self.html + html  
                        html = self.get_file_comparison(second_files = configpairs[key].second_files)
                        self.html = self.html + html
        # Adds /table tag to end table
        table_footer = "</table>"        
        self.html = self.html + table_footer
        
        # Ends the html with some help messages
        self.add_footer()
    
    def add_header(self):
        # Adds some header messages
        header = "First table shows the summarized differences between the 2 configurations.<br>     \
                  Second table shows a more detailed differences between the 2 configuration.<br>    \
                  Click on the project/variant/libtype link in the first table to jump to the        \
                  respective section in the second table.<br><br>"
    
        self.html = self.html + header
                          
    def add_footer(self):
        # Adds help message
        help_footer = "<br>For any question regarding this html, please email to psgicmsupport@intel.com"

        self.html = self.html + help_footer

    def save_html(self, filename):
        '''
        Saves html into a temporary file

        :param filename: temporary file path to save html
        :type first: string
        '''
        with open(filename, 'w') as w:
            w.write(self.html)         

    def get_file_comparison_summary(self, first_files = dict(), second_files = dict()):
        '''
        Compares between 2 files and returns the summary of file differences

        :param key: HTML row key for collapsing the child row under the parent row
        :type first: string
        :param first_files: Dictionary of files contained in the first configuration
        :type first_files: dict
        :param second_files: Dictionary of files contained in the second configuration
        :type second_files: dict
        :return: Summary of file differences
        :rtype: int
        '''

        files = set(list(first_files.keys()) + list(second_files.keys()))
        num = 0
        for file in sorted(files):
            if file in first_files and file in second_files:
                if first_files[file]['filename'] not in NOT_USER_FILES:
                    first_path = "{}/{}#{}".format(first_files[file]['directory'],
                                                   first_files[file]['filename'],
                                                   first_files[file]['version'])
                    second_path = "{}/{}#{}".format(second_files[file]['directory'],
                                                    second_files[file]['filename'],
                                                    second_files[file]['version'])
                    if not is_file_identical(first_path, second_path):
                        num = num + 1
            elif file in first_files and file not in second_files:
                if first_files[file]['filename'] not in NOT_USER_FILES:
                    num = num + 1
            elif file not in first_files and file in second_files:
                if second_files[file]['filename'] not in NOT_USER_FILES:
                    num = num + 1
        return num                                           

    def get_file_comparison(self, first_files = dict(), second_files = dict()):
        '''
        Compares between 2 files and builds the html strings to display the differences

        :param key: HTML row key for collapsing the child row under the parent row
        :type first: string
        :param first_files: Dictionary of files contained in the first configuration
        :type first_files: dict
        :param second_files: Dictionary of files contained in the second configuration
        :type second_files: dict
        :return: HTML string that displays differences between the 2 files
        :rtype: string
        '''
        htmls = ""
        files = set(list(first_files.keys()) + list(second_files.keys()))
        diffpy = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))))), "bin/difficm.py")
        gvimpy = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))))), "bin/gvimicm.py")

        for file in sorted(files):
            html = ""
            link_html = ""
            if file in first_files and file in second_files:
                if first_files[file]['filename'] not in NOT_USER_FILES:
                    first_path = "{}/{}#{}".format(first_files[file]['directory'],
                                                   first_files[file]['filename'],
                                                   first_files[file]['version'])
                    second_path = "{}/{}#{}".format(second_files[file]['directory'],
                                                    second_files[file]['filename'],
                                                    second_files[file]['version'])
                    if not is_file_identical(first_path, second_path):
                        f = file.split(":")[1]
                        if "text" in first_files[file]['type']:
    
                            first_path = "{}/{}#{}".format(first_files[file]['directory'],
                                                           first_files[file]['filename'],
                                                           first_files[file]['version'])
                            second_path = "{}/{}#{}".format(second_files[file]['directory'],
                                                            second_files[file]['filename'],
                                                            second_files[file]['version'])
                            if self.is_audit(first_files[file]):
                                link_html = "<a href=\"!!{} {} {} &\">Show Diff (WARNING: This might take a long time!)</a>".format(
                                             diffpy, first_path, second_path)
                            else:
                                link_html = "<a href=\"!!{} {} {} &\">Show Diff</a>".format(
                                             diffpy, first_path, second_path)                            
                        html = "<tr><td><font color=\"green\">---{}</font></td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                                f,                             
                                first_files[file]['version'],
                                second_files[file]['version'],
                                link_html)
            elif file in first_files and file not in second_files:
                if first_files[file]['filename'] not in NOT_USER_FILES:
                    f = file.split(":")[1]
                    if "text" in first_files[file]['type']:
                        first_path = "{}/{}#{}".format(first_files[file]['directory'],
                                                           first_files[file]['filename'],
                                                           first_files[file]['version'])
                        link_html = "<a href=\"!!{} {} &\">Show File</a>".format(gvimpy, first_path)
                    html = "<tr><td><font color=\"green\">---{}</font></td><td>{}</td><td></td><td>{}</td></tr>".format(
                            f,
                            first_files[file]['version'],
                            link_html)
            elif file not in first_files and file in second_files:
                if second_files[file]['filename'] not in NOT_USER_FILES:
                    f = file.split(":")[1]
                    if "text" in second_files[file]['type']:
                        second_path = "{}/{}#{}".format(second_files[file]['directory'],
                                                            second_files[file]['filename'],
                                                            second_files[file]['version'])
                        link_html = "<a href=\"!!{} {} &\">Show File</a>".format(gvimpy, second_path)
                    html = "<tr><td><font color=\"green\">---{}</font></td><td></td><td>{}</td><td>{}</td></tr>".format(
                            f,
                            second_files[file]['version'],
                            link_html)
            htmls = htmls + html                    
                                
        return htmls

    def is_audit(self, file):
        '''
        Checks if file is an audit xml file

        :param file: Dictionary of file 
        :type first: dict
        :return: True if file is an audit, False if otherwise
        :rtype: boolean
        '''
        return file['filename'].startswith('audit') and file['filename'].endswith('.xml')

class DiffConfigs(object):
    '''
    Runner subclass that actually executes the diffconfigs logic
    '''

    def __init__(self, project, variant, first_config, second_config,
                 second_project=None, second_variant=None, 
                 use_tkdiff=None, ignore_config_names=None, include_files=None, 
                 html=None, sort_by_libtypes=None, 
                 filter_variants=None, filter_libtypes=None, preview=True, deliverable=None):

        self.user_first_config = first_config
        self.user_second_config = second_config
        self.project = project
        self.variant = variant
        self.preview = preview
        self.second_project = second_project
        self.second_variant = second_variant
        self.cli = ICManageCLI(preview)
        self.deliverable = deliverable
        self.eco = dmx.ecolib.ecosphere.EcoSphere()
        self.family = self.eco.get_family(os.getenv("DB_FAMILY"))

        # If project not given, get project from IP
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise DiffConfigsError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
            if not self.cli.project_exists(self.project):
                raise DiffConfigsError("{0} does not exist".format(self.project))
            if not self.cli.variant_exists(self.project, self.variant):
                raise DiffConfigsError("{0}/{1} does not exist".format(self.project, self.variant))
        self.first_config = ConfigFactory.create_from_icm(self.project, self.variant, first_config, preview=self.preview, libtype=self.deliverable)
        if self.second_project and self.second_variant:
            if not self.cli.project_exists(self.second_project):
                raise DiffConfigsError("{0} does not exist".format(self.second_project))
            if not self.cli.variant_exists(self.second_project, self.second_variant):
                raise DiffConfigsError("{0}/{1} does not exist".format(self.second_project, self.second_variant))
            self.second_config = ConfigFactory.create_from_icm(self.second_project, self.second_variant, second_config, preview=self.preview, libtype=self.deliverable)
        elif not self.second_project and not self.second_variant:
            self.second_config = ConfigFactory.create_from_icm(self.project, self.variant, second_config, preview=self.preview, libtype=self.deliverable)
        else:
            raise DiffConfigsError("Please provide second_project together with second_variant.")                       
        self.use_tkdiff = use_tkdiff
        self.ignore_config_names = ignore_config_names
        self.include_files = include_files
        self.html = html
        self.sort_by_libtypes = sort_by_libtypes
        if filter_variants:
            self.filter_variants = filter_variants
        else:
            self.filter_variants = [x.variant for x in self.first_config.flatten_tree() if x.is_config()] + \
                                   [x.variant for x in self.second_config.flatten_tree() if x.is_config()]
        if filter_libtypes:            
            self.filter_libtypes = filter_libtypes
        else:
            self.filter_libtypes = [x.libtype for x in self.first_config.flatten_tree() if not x.is_config()] + \
                                   [x.libtype for x in self.second_config.flatten_tree() if not x.is_config()]
        if self.html:
            # html switch assumes include-files switch
            self.include_files = True
                                        
        self.logger = logging.getLogger(__name__)
        self.tools_path = os.path.join(get_tools_path('flows'),'hw', 'i10')
        
    def run(self):
        ret = 0

        self.diff_configs()
        return ret

    def build_configs_dict(self, config):
        composite_configs = [x for x in config.flatten_tree() if x.is_config()]
        config_dict = dict()
        for cconfig in composite_configs:
            if cconfig.variant in self.filter_variants:
                config_dict[cconfig] = []
                simple_configs = [x for x in cconfig.get_local_objects() if not x.is_config()]
                for sconfig in simple_configs:
                    if sconfig.libtype in self.filter_libtypes:
                        config_dict[cconfig].append(sconfig)
        return config_dict                        

    def diff_configs(self):
        '''
        Finds the differences between first_config and second_config.

        Prints the differences.
        '''
        first_config_dict = {}
        second_config_dict = {}
        # Get sets of simple configs from both composites
        if self.deliverable:
            first_config_dict[self.first_config] = [self.first_config]
            second_config_dict[self.second_config] = [self.second_config]
        else:
            first_config_dict = self.build_configs_dict(self.first_config)
            second_config_dict = self.build_configs_dict(self.second_config)
        #print first_config_dict
         

        if self.use_tkdiff:
            self.tkdiff_configs(first_config_dict, second_config_dict)
        elif self.html:
            pair_lookup = self.build_pair_lookup(first_config_dict, second_config_dict)
            html = HTMLParser(self.project, self.variant, self.first_config, self.second_config, 
                              pair_lookup, self.sort_by_libtypes) 
            html.build_lookup_dict() 
            html.build_html()
                        
            user_local_html = "{}/diffconfigs_{}_{}_{}_{}.html".format(os.getcwd(), 
                                                                       self.project, self.variant, 
                                                                       self.first_config.name, 
                                                                       self.second_config.name)
            self.launch_html(html, user_local_html)     
            LOGGER.info("A copy of generated html is saved at:{}".format(user_local_html))
            LOGGER.info("You may bring up the html via this command:")
            LOGGER.info("{}/icd_cad/AltHtmlBrowser/main/AltHtmlBrowser.py {}".format(self.tools_path, user_local_html))
        else:
            # Establish the widths for later printing
            first_simple_configs = set([y for x in first_config_dict for y in first_config_dict[x]])
            second_simple_configs = set([y for x in second_config_dict for y in second_config_dict[x]])

            first_width, second_width = self.get_widths(first_simple_configs | second_simple_configs)
            '''
            ### 02 Feb 2021: I have no idea what this is doing.
            ### Temporary comment this section out, until someone screams.
            ---
            # Readjust second width for consistent printing
            if len(self.first_config._config) > second_width:
                second_width = len(self.first_config._config)
            '''
            pair_lookup = self.build_pair_lookup(first_config_dict, second_config_dict)
            self.logger.debug("first_config_dict: {}".format(first_config_dict))
            self.logger.debug("second_condif_dict: {}".format(second_config_dict))
            self.logger.debug("pair_lookup: {}".format(pair_lookup))

            if self.sort_by_libtypes:
                libtypes = set([x.libtype for x in list(pair_lookup.values())])
                for libtype in libtypes:
                    for key in sorted(pair_lookup.keys()):
                        if pair_lookup[key].libtype == libtype:
                            print_header(self.first_config, self.second_config, first_width, second_width)
                            if self.deliverable and not self.include_files:
                                ret = self.get_icmp4_diff()
                                exit(ret)
                            
                            else :
                                pair_lookup[key].generate_and_print_diff(first_width, second_width)
            else:                
                for key in sorted(pair_lookup.keys()):
                    print_header(self.first_config, self.second_config, first_width, second_width)
                    if self.deliverable and not self.include_files:
                        ret = self.get_icmp4_diff()
                        exit(ret)
                    else:
                        pair_lookup[key].generate_and_print_diff(first_width, second_width)

            if self.include_files:
                self.print_diff_help()                               

    def get_icmp4_diff(self):
        '''
        Get icmp4 depot path from BomDetail, diff using icmp4 diff to get file different 
        '''
        ret = 1

        if not self.second_project:
            project = self.project
        if not self.second_variant:
            variant = self.variant

        cfobj1 = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, self.user_first_config, libtype=self.deliverable)
        cfobj2 = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(project, variant, self.user_second_config, libtype=self.deliverable)

        cmd = '_xlp4 diff2 -q {} {}'.format(cfobj1.get_depot_path(), cfobj2.get_depot_path())
        self.logger.debug("Running: {}".format(cmd))
        exitcode, stdout, stderr = run_command(cmd)
        
        if self.is_large_data_deliverable(self.deliverable):
            self.logger.debug("{} is LDD: do something to stdout".format(self.deliverable))
            newstdout = self.massage_large_data_deliverable_stdout(stdout)
        else:
            newstdout = stdout
            self.logger.debug("{} is not LDD: do nothing to stdout".format(self.deliverable))

        if not newstdout :
            print("Both bom are identical") 
            ret = 0
        else:
            print(newstdout.rstrip())
            ret = 1

        return ret 


    def massage_large_data_deliverable_stdout(self, stdout):
        '''
        Example of the stdout (which is the output of running icmp4 diff2):
            
            >_icmp4 diff2 -q //depot/icm/proj/i10socfm/liotest1/ipspec/dev/...@17960502 //depot/icm/proj/i10socfm/liotest1/ipspec/test2_dev/...@17961095
            ==== //depot/icm/proj/i10socfm/liotest1/ipspec/dev/aib_ssm.unneeded_deliverables.txt#9 (text+kl) - //depot/icm/proj/i10socfm/liotest1/ipspec/test2_dev/aib_ssm.unneeded_deliverables.txt#1 (text+kl) ==== content
            ==== //depot/icm/proj/i10socfm/liotest1/ipspec/dev/dummy.txt#1 - <none> ===
            ==== <none> - //depot/icm/proj/i10socfm/liotest1/ipspec/test2_dev/test2_dev.txt#1 ====

        so here is there algorithm:
            - if line contains '==== content'
            - check both the md5sum is the same 
            - if same, remove line, else, retain line.
        '''
        retlist = []
        for line in stdout.split('\n'):
            if line and '==== content' in line:
                m = re.findall("(//depot/.+?#\d+) \(", line)
                if len(m) == 2:
                    checksum1 = self.get_large_data_deliverable_file_md5sum(m[0])
                    self.logger.debug("checksum:{} ==> filespec:{}".format(checksum1, m[0]))
                    checksum2 = self.get_large_data_deliverable_file_md5sum(m[1])
                    self.logger.debug("checksum:{} ==> filespec:{}".format(checksum2, m[1]))
                    if checksum1 != checksum2:
                        self.logger.debug("- file differs!")
                        retlist.append(line)
                    else:
                        self.logger.debug("- file same content!")
                else:
                    self.logger.warning("massage_large_data_deliverable_stdout: Did not get 2 filespecs for line: {}".format(line))
                    self.logger.warning(" -{}".format(pformat(m)))
            else:
                retlist.append(line)

        return "\n".join(retlist)


    def get_large_data_deliverable_file_md5sum(self, filespec):
        ''' '''
        cmd = 'md5sum `_xlp4 print -q {}` | cut -d" " -f1 '.format(filespec)
        exitcode, stdout, stderr = run_command(cmd)
        return stdout.strip()


    def is_large_data_deliverable(self, deliverable):
        ''' 
        if fail to get the info, return false, so that it does not 
        '''
        try:
            d = self.family.get_deliverable(deliverable)
            return d._large
        except Exception as e:
            self.logger.debug("is_large_data_deliverable: {}".format(str(e)))
            return false


    def print_diff_help(self):
        '''
        Prints help messages for user to run icmp4 diff2 command on files
        '''
        print("To see the differences between files, run the following ICM command:")
        print("  > xlp4 diff2 file#ver1 file#ver2")
        print("For example:")
        print("  > xlp4 diff2 //depot/icm/proj/i14socnd/ar_lib/upf/dev/rtl/ar_spine_3_bf.upf#4 //depot/icm/proj/i14socnd/ar_lib/upf/dev/rtl/ar_spine_3_bf.upf#5")

    def build_pair_lookup(self, first, second):
        '''
        Builds the config pair lookup table from the two sets of configs

        :param first: First set of simple configurations
        :type first: set
        :param second: Second set of simple configurations
        :type second: set
        :return: Dictionary where key=<project>/<variant>:<libtype> and value=ConfigPair object
        :rtype: dict
        '''
        pair_lookup = {}
        self.logger.debug("first: {}".format(first))
        self.logger.debug("second: {}".format(second))
        for cconfig in first:
            project = cconfig.project
            variant = cconfig.variant
            config = cconfig.name
            for sconfig in first[cconfig]:
                if self.second_project and self.second_variant and (variant == self.variant or variant == self.second_variant):
                    key = ConfigPair.generate_key_diff_projects(self.project, self.variant, 
                        self.second_project, self.second_variant, sconfig.libtype)
                else:                    
                    key = ConfigPair.generate_key(sconfig.project, sconfig.variant, sconfig.libtype)
                if key in pair_lookup:
                    pair_lookup[key].first_config = sconfig
                else:
                    new_pair = ConfigPair(sconfig.project, sconfig.variant, sconfig.libtype,
                                              ignore_config_names=self.ignore_config_names,
                                              include_files=self.include_files)
                    new_pair.first_config = sconfig
                    new_pair.key = key
                    pair_lookup[key] = new_pair
                pair_lookup[key].parent_first_config = config
                            
        for cconfig in second:
            project = cconfig.project
            variant = cconfig.variant
            config = cconfig.name
            for sconfig in second[cconfig]:
                if self.second_project and self.second_variant and (variant == self.variant or variant == self.second_variant):
                    key = ConfigPair.generate_key_diff_projects(self.project, self.variant, 
                        self.second_project, self.second_variant, sconfig.libtype)
                else:
                    key = ConfigPair.generate_key(sconfig.project, sconfig.variant, sconfig.libtype)
                if key in pair_lookup:
                    pair_lookup[key].second_config = sconfig
                else:
                    new_pair = ConfigPair(sconfig.project, sconfig.variant, sconfig.libtype,
                                          ignore_config_names=self.ignore_config_names,
                                          include_files=self.include_files)
                    new_pair.second_config = sconfig
                    new_pair.key = key
                    pair_lookup[key] = new_pair
                pair_lookup[key].parent_second_config = config                    
        return pair_lookup

    def tkdiff_configs(self, first_config_dict, second_config_dict):
        '''
        Performs a tkdiff of the two configurations. Does this by writing configuration
        content to temporary files and then invoking tkdiff using those files.

        :param first_config_dict: Dict of composite configs that contains a list of its local simple configurations from the first composite config
        :type second_config_dict: similar to first_config_dict but for second composite config
        :param second_simple_configs: List of simple configurations from the second composite config
        :type second_simple_configs: list or set
        '''
        try:
            first_file = NamedTemporaryFile(delete=False, prefix='first_config_file')
            second_file = NamedTemporaryFile(delete=False, prefix='second_config_file')

            self.write_config_file(first_file.name, first_config_dict)
            self.write_config_file(second_file.name, second_config_dict)
            subprocess.call(['tkdiff', first_file.name, second_file.name])
        finally:
            if first_file and os.path.exists(first_file.name):
                os.unlink(first_file.name)
            if second_file and os.path.exists(second_file.name):
                os.unlink(second_file.name)

    def write_config_file(self, file_name, cconfigs):
        '''
        Writes the configuration data from configs into file_name

        :param file_name: Name of the file to write data into.
        :type file_name: str
        :param configs: List of simple configs
        :type configs: list
        '''
        prev_pvl = ''

        with open(file_name, 'w') as fd:
            if self.sort_by_libtypes:
                output = []
                sconfigs = [x for y in list(cconfigs.values()) for x in y]
                libtypes = [x.libtype for x in sconfigs]                                
                for libtype in sorted(libtypes):
                    for sconfig in sorted(sconfigs, key=lambda x: x.variant):
                        if libtype == sconfig.libtype:
                            pvl = '{0}/{1}/{2}'.format(sconfig.project, sconfig.variant, sconfig.libtype)
                            if pvl not in output:
                                output.append(pvl)
                                lrc = '    library={0} release={1} config={2}'.format(sconfig.library, sconfig.lib_release, sconfig.name)
                                output.append(lrc)

                for line in output:                                
                    fd.write('{0}\n'.format(line))
            else:                
                for cconfig in sorted(cconfigs, key=lambda x: x.get_full_name()):
                    for sconfig in sorted(cconfigs[cconfig], key=lambda x: x.get_full_name()):
                        pvl = '{0}/{1}/{2}'.format(sconfig.project, sconfig.variant, sconfig.libtype)
                        if pvl != prev_pvl:
                            fd.write('{0}\n'.format(pvl))
                            prev_pvl = pvl
    
                        fd.write('    library={0} release={1} config={2}\n'.format(sconfig.library, sconfig.lib_release, sconfig.name))

    def get_widths(self, configs):
        '''
        Works through the configurations determining the correct widths to use when
        printing.

        :param configs: List of configuration objects
        :type configs: list
        :return: Two integers representing the widths for the first and second blocks of output
        :rtype: int, int
        '''
        first_width = 1
        second_width = 1

        for config in configs:
            if self.second_project and self.second_variant:
                this_first_width = len(self.project) + len(self.variant) + len(self.second_project) + len(self.second_variant) + len(config.libtype) + 5
            elif not self.second_project and not self.second_variant:
                this_first_width = len(config.project) + len(config.variant) + len(config.libtype) + 4
            this_second_width = len(config.library) + len(config.lib_release) + len(config.name) + 2

            if this_first_width > first_width:
                first_width = this_first_width

            if this_second_width > second_width:
                second_width = this_second_width

        return first_width, second_width

    def launch_html(self, html, user_local_html):
        '''
        Saves html strings into a temporary html file then launches firefox on the saved html

        :param html: HTML strings which contains diff
        :type html: string
        '''
        try:
            html_file = NamedTemporaryFile(delete=False, prefix='html', suffix='.html')

            html.save_html(html_file.name)
            altbrowser = "{}/icd_cad/AltHtmlBrowser/main/AltHtmlBrowser.py".format(self.tools_path)
            subprocess.call(["{}".format(altbrowser), html_file.name])
        finally:
            subprocess.call(['cp', html_file.name, user_local_html])
            if html_file and os.path.exists(html_file.name):
                os.unlink(html_file.name)

