#!/usr/bin/env python

## @addtogroup ecolib
## @{

''' axc
This is documentation

@author Lionel Tan, Kevin Lim
@image html dmx.ecolib.png 

-the end-
'''

import sys, os
import re
import logging
import dmx.ecolib.loader

LOGGER = logging.getLogger(__name__)

class ManifestError(Exception): pass

class Manifest(object):  
    def __init__(self, family, deliverable,
                 preview=True):
        self._family = family
        self._deliverable = deliverable.lower()
        self._manifest = self._deliverable
        self._preview = preview

        (successor, predecessor, producer, consumer, description, owner, additional_owners, pattern, filelist, milkyway, slice, dm, dm_meta, large, large_excluded_ip) = self.get_manifest() 
        self._producer = producer
        self._consumer = consumer
        self._predecessor = predecessor
        self._successor = successor 
        self._description = description
        self._owner = owner
        self._additional_owners = additional_owners
        self._pattern = pattern
        self._filelist = filelist
        self._milkyway = milkyway
        self._slice = slice
        self._dm = dm
        self._dm_meta = dm_meta

        # For backwards compatibility
        if large:
            self._large = large
        elif self._dm == 'naa':
            self._large = True
        else:
            self._large = False
        if large_excluded_ip:
            self._large_excluded_ip = large_excluded_ip
        elif 'large_excluded_ip' in self._dm_meta:
            self._large_excluded_ip = self._dm_meta['large_excluded_ip']
        else:
            self._large_excluded_ip = []

    @property
    def name(self):
        return self._manifest        
                
    @property
    def family(self):
        return self._family

    @property
    def deliverable(self):
        return self._deliverable        

    @property
    def manifest(self):
        return self._manifest
        
    @property
    def producer(self):
        return self._producer

    @property
    def consumer(self):
        return self._consumer
    
    @property
    def predecessor(self):
        return self._predecessor
    
    @property
    def successor(self):
        return self._successor

    @property
    def description(self):
        return self._description

    @property
    def owner(self):
        return self._owner

    @property
    def additional_owners(self):
        return self._additional_owners

    @property
    def pattern(self):
        return self._pattern  
        
    @property
    def slice(self):
        return self._slice   
        
    @property
    def dm(self):
        return self._dm

    @property
    def dm_meta(self):
        return self._dm_meta

    @property
    def large(self):
        return self._large

    @property
    def large_excluded_ip(self):
        return self._large_excluded_ip

    ## Preloads local variables
    ## self._checkers
    ##
    ## @param self The object pointer. 
    def _preload(self):
        pass

    ## Return short description if found short description, else return nothing 
    def get_short_description(self):
        match = re.search('.*\(ShortDescription:\s?(.+)\).*',self._description)
        if match:
            short_description = match.group(1) 
            return short_description
        else:
            return ""

    ## Returns a list of file patterns for the ip/manifest/cell
    ##
    ## @param self The object pointer. 
    ## @param ip IP
    ## @param cell Cellname
    ## @return list of strings of file patterns
    def get_patterns(self, ip = None, cell = None, iptype_filter='', prel_filter=''):
        try:
            re.compile(iptype_filter)
        except:
            raise ManifestError("Regex {} cannot be compiled.".format(iptype_filter))
        try:
            re.compile(prel_filter)
        except:
            raise ManifestError("Regex {} cannot be compiled.".format(prel_filter))

        patterns = {}
        for pattern in self._pattern:
            newpattern = pattern
            if ip:
                newpattern = pattern.replace('ip_name', ip)
            if 'cell_names' not in newpattern:                      
                if cell:
                    newpattern = newpattern.replace('cell_name', cell)

            ### iptype aware https://jira.devtools.intel.com/browse/PSGDMX-1600
            if 'iptypes' in self._pattern[pattern] and self._pattern[pattern]['iptypes'] and not [iptype for iptype in self._pattern[pattern]['iptypes'] if re.match(iptype_filter, iptype)]:
                pass
            else:
                ### prel aware https://jira.devtools.intel.com/browse/PSGDMX-1884
                if not prel_filter or 'prels' not in self._pattern[pattern] or [prel for prel in self._pattern[pattern]['prels'] if re.match(prel_filter, prel)]:
                    patterns[newpattern] = self._pattern[pattern]


        return patterns

    ## Returns a list of file lists for the ip/manifest/cell
    ##
    ## @param self The object pointer. 
    ## @param ip IP
    ## @param cell Cellname
    ## @return list of strings of file lists
    def get_filelists(self, ip = None, cell = None, iptype_filter=''):
        filelists = {}
        for filelist in self._filelist:
            newfilelist = filelist
            if ip:
                newfilelist = filelist.replace('ip_name', ip)
            if 'cell_names' not in newfilelist:                                            
                if cell:
                    newfilelist = newfilelist.replace('cell_name', cell)

            ### iptype aware https://jira.devtools.intel.com/browse/PSGDMX-1600
            if 'iptypes' in self._filelist[filelist] and self._filelist[filelist]['iptypes'] and not [iptype for iptype in self._filelist[filelist]['iptypes'] if re.match(iptype_filter, iptype)]:
                pass
            else:
                filelists[newfilelist] = self._filelist[filelist]
        return filelists

    ## Returns a dict of milkyway lib
    ##
    ## @param self The object pointer. 
    ## @param ip IP
    ## @param cell Cellname
    ## @return dict of strings
    def get_milkyway(self, ip = None, cell = None):
        milkyway = {}
        for lib in self._milkyway:
            newlib = lib
            if ip:
                newlib = lib.replace('ip_name', ip)
            if 'cell_names' not in newlib:                      
                if cell:
                    newlib = newlib.replace('cell_name', cell)                
            milkyway[newlib] = self._milkyway[lib]
        return milkyway        
                    
    ## Returns Manifest's manifest
    ##
    ## @param self The object pointer. 
    ## @return tuple of (successor, predecessor, producer, consumer, description, pattern)
    def get_manifest(self):
        manifest = dmx.ecolib.loader.load_manifest(self._family)
        deliverable = self._deliverable.lower()
        successor = predecessor = producer = consumer = description = pattern = owner = additional_owners = None
        patterns = {}
        filelists = {}
        milkyway = {}
        slice = []
        dm = ''
        dm_meta = {}
        large = False
        large_excluded_ip = []
        if deliverable in manifest:
            successor = [str(x) for x in manifest[deliverable]['successor']]
            predecessor = [str(x) for x in manifest[deliverable]['predecessor']]
            producer = [str(x) for x in manifest[deliverable]['producer']]
            consumer = [str(x) for x in manifest[deliverable]['consumer']]
            description = manifest[deliverable]['description'].encode('utf-8')            
            owner = str(manifest[deliverable]['owner'])
            additional_owners = [str(x) for x in manifest[deliverable]['additional owners']]
            for pattern in manifest[deliverable]['pattern']:
                if pattern not in patterns:
                    patterns[str(pattern)] = {}
                for key in manifest[deliverable]['pattern'][pattern].keys():
                    value = manifest[deliverable]['pattern'][pattern][key]
                    if type(value) is bool:
                        patterns[pattern][str(key)] = bool(manifest[deliverable]['pattern'][pattern][key])
                    elif type(value) is list:
                        patterns[pattern][str(key)] = list(manifest[deliverable]['pattern'][pattern][key])
                    else:
                        patterns[pattern][str(key)] = str(manifest[deliverable]['pattern'][pattern][key])
            for filelist in manifest[deliverable]['filelist']:
                if filelist not in filelists:
                    filelists[str(filelist)] = {}
                for key in manifest[deliverable]['filelist'][filelist].keys():
                    value = manifest[deliverable]['filelist'][filelist][key]
                    if type(value) is bool:
                        filelists[filelist][str(key)] = bool(manifest[deliverable]['filelist'][filelist][key])
                    elif type(value) is list:
                        filelists[filelist][str(key)] = list(manifest[deliverable]['filelist'][filelist][key])
                    else:
                        filelists[filelist][str(key)] = str(manifest[deliverable]['filelist'][filelist][key])
            if 'milkyway' in manifest[deliverable]:
                for lib in manifest[deliverable]['milkyway']:
                    milkyway[str(lib)] = str(manifest[deliverable]['milkyway'][lib])
            if 'slice' in manifest[deliverable]:
                slice = [str(x) for x in manifest[deliverable]['slice']]            
            # Default to icmanage if field does not exist
            dm = str(manifest[deliverable]['dm']) if 'dm' in manifest[deliverable] else 'icmanage'
            if 'dm_meta' in manifest[deliverable]:
                for key in manifest[deliverable]['dm_meta'].keys():
                    value = manifest[deliverable]['dm_meta'][key]
                    if type(value) is list:
                        dm_meta[str(key)] = [str(x) for x in value]
                    else:
                        dm_meta[str(key)] = str(value)

            # For backwards compatibility
            large = manifest[deliverable]['large'] if 'large' in manifest[deliverable] else False
            if 'large_excluded_ip' in manifest[deliverable]:
                for ip in manifest[deliverable]['large_excluded_ip']:
                    large_excluded_ip.append(str(ip))
                                                        
        return (successor, predecessor, producer, consumer, description, owner, additional_owners, patterns, filelists, milkyway, slice, dm, dm_meta, large, large_excluded_ip) 

    def __repr__(self):
        '''
        Returns a slightly more complete/unique view of the class
        '''
        return "{}".format(self._manifest)
        
## @}        
