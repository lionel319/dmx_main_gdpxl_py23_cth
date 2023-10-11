#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/list.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr "list" subcommand plugin
Author: Lee Cartwright
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
from __future__ import print_function
from builtins import object
import sys
import logging
import textwrap
import re

from dmx.abnrlib.icm import ICManageCLI, run_read_command
from dmx.abnrlib.config_factory import ConfigFactory

TNR_SNAP_PATTERNS = ['^snap-\d+-*\w*']

class ListError(Exception): pass

class List(object):
    '''
    Runner subclass for the abnr report icm subcommand
    '''
    def __init__(self, project, variant, libtype, library, config_or_library_or_release,
                 switches, props, regex, debug=False):
        '''
        Initialiser for the ListRunner class

        :param project:  The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param libtype: The IC Manage libtype
        :type libtype: str
        :param library: The IC Manage library
        :type library: str
        :param config: The IC Manage config
        :type config: str
        :param switches: Displays results in a format that can be accepted by another abnr command
        :type switches: bool
        :param props: Displays configuration properties
        :type props: bool
        :param regex: Use perl style regex rather than glob style 
        :type regex: bool
        '''
        self.logger = logging.getLogger(__name__)
        self.cli = ICManageCLI()
        self.SITE = 'intel'

        self.logger.debug("param: project:{} variant:{} libtype:{} library:{} clr:{}".format(
            project, variant, libtype, library, config_or_library_or_release))
        self.project = project
        self.variant = variant
        self.libtype = libtype

        self.clr = config_or_library_or_release
        self.switches = switches
        self.props = props
        self.regex = regex
        self.debug = debug

        self._RETKEYS = ['path', 'type', 'name', 'created-by', 'created']

        self._getobjproject = self._getobjpattern(self.project)            
        self._getobjvariant = self._getobjpattern(self.variant)   
        self._getobjlibtype = self._getobjpattern(self.libtype)   
        self._getobjclr     = self._getobjpattern(self.clr)

        self._pyproject = self._pypattern(self.project)            
        self._pyvariant = self._pypattern(self.variant)   
        self._pylibtype = self._pypattern(self.libtype)   
        self._pyclr = self._pypattern(self.clr)
                
    def run(self):
        '''
        Runs the report icm abnr subcommand
        '''
        ret = 0

        self.print_output()

        return ret

    def _filter_out_unsupported(self, data):
        '''
        As we are still in a very early stage of GDPXL migration, there are still
        a lot of wierd/illegal data structure lying around in the db.
        In order to move forward, we have to have this hardcoded function to remove
        all those illegal stuff in order to move forward. Once everything has settled
        down, this function will no longer be needed, and will/should go.

        data = return list from self.cli._get_objects(retkeys=['name', 'path', 'type'])
        '''
        newlist = []
        for d in data:
            if not d['path'].startswith(("/intel/RegressionTest", "/intel/a")):
                newlist.append(d)
        return newlist

    def _get_projects(self):
        ret = self.cli._get_objects('/{}/**/:project'.format(self.SITE), retkeys=self._RETKEYS)
        return self._filter_out_unsupported(ret)

    def _get_variants(self):
        ret = self.cli._get_objects('/{}/**/:variant'.format(self.SITE), retkeys=self._RETKEYS)
        return self._filter_out_unsupported(ret)

    def _get_libtypes(self):
        ret = self.cli._get_objects('/{}/{}/{}/{}:libtype'.format(self.SITE, self._getobjproject, self._getobjvariant, self._getobjlibtype), retkeys=self._RETKEYS)
        return self._filter_out_unsupported(ret)

    def _get_variant_boms(self):
        ret = self.cli._get_objects('/{}/{}/{}/{}:config'.format(self.SITE, self._getobjproject, self._getobjvariant, self._getobjclr), retkeys=self._RETKEYS)
        return self._filter_out_unsupported(ret)

    def _get_libtype_boms(self):
        ret = self.cli._get_objects('/{}/{}/{}/{}/**/:library,release'.format(self.SITE, self._getobjproject, self._getobjvariant, self._getobjlibtype), retkeys=self._RETKEYS)
        newlist = []
        for d in self._filter_out_unsupported(ret):
            if d['type'] == 'release':
                d['path'] = re.sub('[^/]+/([^/]+)$', '\\1', d['path'])
            newlist.append(d)
        return newlist

    def print_output(self):
        '''
        There are 5 levels of different scenarios that are supported.
        Print out the list of:-
        1. projects
        2. variants
        3. libtypes
        4. variant-boms
        5. libtype-boms
        '''
        matched = []  
        found = []     
        props = dict()

        scenario = ''
        if self.project and not (self.variant or self.libtype or self.clr):
            scenario = 'projects'
            pypattern = "/{}/({})$".format(self.SITE, self._pyproject)
            header = "Project"      
            if self.switches:
                searchpattern = "(.+)"
                replacepattern = "-p \\1"
            else:      
                searchpattern = "(.+)"
                replacepattern = "\\1"
            results = self._get_projects()
        elif self.project and self.variant and not (self.libtype or self.clr):
            scenario = 'variants'
            pypattern = "/{}/({}/{})$".format(self.SITE, self._pyproject, self._pyvariant)
            header = "Project/IP"
            if self.switches:
                searchpattern = "(.+)/(.+)"
                replacepattern = "-p \\1 -i \\2"
            else:
                searchpattern = "(.+/.+)"
                replacepattern = "\\1"
            results = self._get_variants()
        elif self.project and self.variant and self.libtype and not self.clr:
            scenario = 'libtypes'
            pypattern = "/{}/({}/{}/{})$".format(self.SITE, self._pyproject, self._pyvariant, self._pylibtype)
            header = "Project/IP:Deliverable"
            if self.switches:
                searchpattern = "(.+)/(.+)/(.+)"
                replacepattern = "-p \\1 -i \\2 -d \\3"
            else:
                searchpattern = "(.+/.+)/(.+)"
                replacepattern = "\\1:\\2"
            results = self._get_libtypes()
        elif self.project and self.variant and not self.libtype and self.clr:
            scenario = 'variant-boms'
            pypattern = "/{}/({}/{}/{})$".format(self.SITE, self._pyproject, self._pyvariant, self._pyclr)
            header = "Project/IP@BOM"
            if self.switches:
                searchpattern = "(.+)/(.+)/(.+)"
                replacepattern = "-p \\1 -i \\2 -b \\3"
            else:
                searchpattern = "(.+/.+)/(.+)"
                replacepattern = "\\1@\\2"
            results = self._get_variant_boms()
        elif self.project and self.variant and self.libtype and self.clr:
            scenario = 'libtype-boms'
            pypattern = "/{}/({}/{}/{}/{})$".format(self.SITE, self._pyproject, self._pyvariant, self._pylibtype, self._pyclr)
            header = "Project/IP:Deliverable@BOM"
            if self.switches:
                searchpattern = "(.+)/(.+)/(.+)/(.+)"
                replacepattern = "-p \\1 -i \\2 -d \\3 -b \\4"
            else:
                searchpattern = "(.+/.+)/(.+)/(.+)"
                replacepattern = "\\1:\\2@\\3"
            results = self._get_libtype_boms()
       

        self.logger.debug("pypattern = {}".format(pypattern))
        self.logger.debug("searchpattern = {}".format(searchpattern))

        for result in results:
            self.logger.debug("pypattern: -{}-, result: -{}-".format(pypattern, result))
            m = re.search(pypattern, result['path'])
            self.logger.debug("MMM: {}".format(m))
            if m:
                value = re.sub(searchpattern, replacepattern, m.group(1))
                result['dmx_list_format'] = value
                matched.append(result)

        matched = sorted(matched, key=lambda d: d['dmx_list_format'])
        self.logger.debug("matched: {}".format(matched))

        if scenario == 'projects':
            # http://pg-rdjira.altera.com:8080/browse/DI-619                
            # We need to print the categories and sort the projects according to 
            # their categories
            # That's why printing of project gets special treatment
            categories = {'/{}'.format(self.SITE):[]}
            for m in matched:
                match = m['dmx_list_format']
                categories['/{}'.format(self.SITE)].append(match) 
            for category in sorted(categories.keys()):                
                print('Category: {}'.format(category))
                for project in sorted(categories[category]):
                    print(project)
                print()                    
        else:    
            print("{}:".format(header))        
            for m in matched:
                match = m['dmx_list_format']
                print(match)
                if self.props:
                    for prefix, key in [['Owner:', 'created-by'], ['Created At:', 'created']]:
                        value = m[key] if key in m else 'None'
                        print('\t{} {}'.format(prefix, value))
        print("Found {} match".format(len(matched)))                


    def _getobjpattern(self, string):
        ''' 
        Format string pattern to be used in self.cli._get_objects(),
        which calls "gdp list " 
        '''
        if not string:
            pattern = '*'
        elif re.search(r'[^a-zA-Z0-9_ -]', string):
            pattern = '*'
        else:
            pattern = string
        return pattern


    def _pypattern(self, string):
        '''
        Format string pattern to follow python pattern template
        '''
        pattern = None
        # if string is None return [^/]+ otherwise try to compile the pattern
        if string:                                          
            if '\\' in string:
                raise ListError("Names {} cannot contain '\\'".format(string))
            if '/' in string:
                raise ListError("Names {} cannot contain '/'".format(string))
    
            if self.regex:
                pattern = string
            else:
                pattern = string.replace('.', '\\.').replace('?', '.').replace('^', '').replace('*', '[^/]*')
    
            # try to compile it as a python regular expression
            try:
                re.compile(pattern)
            except:
                raise ListError("Bad python name/pattern: '{}'".format(pattern))
        else:
            pattern = '[^/]+'  

        return pattern                                  
    
