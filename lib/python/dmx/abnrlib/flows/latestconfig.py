#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/latestconfig.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr bomlatest subcommand
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
from __future__ import print_function

from builtins import object
import sys
import logging
import textwrap
import re
import os

from dmx.utillib.utils import add_common_args, _pypattern
from dmx.abnrlib.icm import ICManageCLI
from pprint import pprint
from dmx.abnrlib.config_naming_scheme import ConfigNamingScheme
from dmx.utillib.arcenv import ARCEnv

class LatestConfigError(Exception): pass

class LatestConfig(object):
    '''
    Runs the bomlatest command
    '''
    def __init__(self, project, variant, config, libtype=None, pedantic=False, limit=-1):
        self.logger = logging.getLogger(__name__)
        self.project = project
        self.variant = variant
        self.config = config
        self.libtype = libtype
        self.pedantic = pedantic
        self.limit = limit

        self.re_config = _pypattern(self.config, False)
        self.logger.debug("re_config:{}".format(self.re_config))

        self.cli = ICManageCLI(preview=True)
        self.latest_config = None

        # If project not given, get project from IP
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise LatestConfigError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
            if not self.cli.variant_exists(self.project, self.variant):
                if not self.cli.project_exists(self.project):
                    raise LatestConfigError('Project {0} does not exist'.format(self.project))
                else:
                    raise LatestConfigError('Variant {0} does not exist in project {1}'.format(self.variant,
                                                                                     self.project))


    def run(self):
        ret = 1

        rel_configs, snap_configs, nonrel_configs = self.get_regex_matching_configs(self.project, self.variant, self.libtype, self.re_config)

        rel_configs_by_toi = self.separate_rel_configlist_by_thread_of_integration(rel_configs)
        snap_configs_by_label = self.separate_snap_configlist_by_label(snap_configs)


        retlist = []
        for toi in rel_configs_by_toi:
            retlist.append(self.sort_rel_configs(rel_configs_by_toi[toi])[-1])
        for label in snap_configs_by_label:
            retlist.append(self.sort_snap_configs(snap_configs_by_label[label])[-1])
        
        if not self.pedantic:
            retlist.extend(nonrel_configs)
        else:
            retlist.extend(self.get_pedantic_configs_from_configlist(nonrel_configs))

        sorted_retlist = sorted(retlist)
        sorted_retlist.reverse()

        final_retlist = []
        if self.limit > len(sorted_retlist) or self.limit == -1:
            final_retlist = sorted_retlist
        else:
            final_retlist = self.sort_configlist_based_on_timestamp(sorted_retlist)[0:self.limit]

        for config in final_retlist:
            print(config) 

        self.final_retlist = final_retlist

        ret = 0

        return ret

    
    def sort_configlist_based_on_timestamp(self, configlist):
        '''
        Sort a given list of configurations based on their timestamp.
        Only officially REL* and snap- config will be sorted, the rest will stay unchanged.
        Sorted REL* and snap-* configs will be in the front of the list, followed by the rest.
        '''
        retlist = []
        relsnaplist = []
        for config in configlist:
            data = None
            if config.startswith('REL'):
                data = ConfigNamingScheme.get_data_for_release_config(config)
            elif config.startswith('snap-'):
                data = ConfigNamingScheme.get_data_for_snap_config(config)          
            if data:
                relsnaplist.append(config)
            else:
                retlist.append(config)

        if relsnaplist:
            sorted_relsnaplist = self.sort_rel_and_snap_configs(relsnaplist)
            sorted_relsnaplist.reverse()
            retlist = sorted_relsnaplist + retlist

        return retlist
    

    def get_pedantic_configs_from_configlist(self, configlist):
        '''
        Given a list of configs, return only the configurations that meet the 
        Altera Officially defined Config Naming Scheme.
        '''
        retlist = []
        for config in configlist:
            ret = ConfigNamingScheme.get_data_for_config(config)
            if ret:
                retlist.append(config)
        return retlist


    def separate_rel_configlist_by_thread_of_integration(self, rel_configlist):
        '''
        given a list of REL* configs, separated them into lists of thread-of-integrations.
        Example:-
        configlist = [
            'REL1.5ND5revA--SECTOR__14ww334a',
            'REL1.5ND5revA--SECTOR-USAGE-ONLY__14ww363a',
            'REL1.5ND5revA--SECTOR-USAGE-ONLY__14ww392a',
            'REL2.0ND5revA__14ww414a',
            'REL2.0ND5revA__14ww431a',
            'REL2.0ND5revA__14ww434a',
            'REL2.0ND5revA__14ww435a',
            'REL2.0ND5revA__14ww462a',
            'REL2.0ND5revA__14ww462b',
            'REL3.0ND5revA__15ww047a',
            'REL3.0ND5revA__15ww064a',
            'REL3.0ND5revA__15ww32a',
            'REL3.5ND5revA__15ww144a', ]

        ret = {
            'REL1.5ND5revA--SECTOR': [
                'REL1.5ND5revA--SECTOR__14ww334a'],
            'REL1.5ND5revA--SECTOR-USAGE-ONLY': [
                'REL1.5ND5revA--SECTOR-USAGE-ONLY__14ww363a',
                'REL1.5ND5revA--SECTOR-USAGE-ONLY__14ww392a' ],
            'REL2.0ND5revA': [
                'REL2.0ND5revA__14ww414a',
                'REL2.0ND5revA__14ww431a',
                'REL2.0ND5revA__14ww434a',
                'REL2.0ND5revA__14ww435a',
                'REL2.0ND5revA__14ww462a',
                'REL2.0ND5revA__14ww462b',],
            'REL3.0ND5revA': [
                'REL3.0ND5revA__15ww047a',
                'REL3.0ND5revA__15ww064a',
                'REL3.0ND5revA__15ww32a',],
            'REL3.5ND5revA': [
                'REL3.5ND5revA__15ww144a', ]
        }
        '''
        ret = {}
        for config in rel_configlist:
            toi = self.get_thread_of_integration_from_rel_config(config)
            if toi in ret:
                ret[toi].append(config)
            else:
                ret[toi] = [config]
        return ret

    def separate_snap_configlist_by_label(self, snap_configlist):
        '''
        given a list of snap* configs, separated them into lists of label.
        Example:-
        configlist = [
            'snap-lay__17ww454a',
            'snap-lay__17ww493a',
            'snap-RC_phys_3.0__17ww473a',
            'snap-RC_phys_3.0__18ww015a']

        ret = {
            'snap-lay': [
                'snap-lay__17ww454a',
                'snap-lay__17ww493a'],
            'snap-RC_phys_3.0': [
                'snap-RC_phys_3.0__17ww473a',
                'snap-RC_phys_3.0__18ww015a' ],
        }
        '''
        ret = {}
        for config in snap_configlist:
            label = self.get_label_from_snap_config(config)
            if label in ret:
                ret[label].append(config)
            else:
                ret[label] = [config]
        return ret

            
    def sort_rel_and_snap_configs(self, configlist):
        ''' 
        | sort the REL* and snap-* configurations by date stated in the config name, whereby the bomlatest created one is the last one 
        | Any configurations which is not a well-defined released or snap configuration will be dropped.

        | The configs look like this:

        ::
          
            REL<milestone><thread>[--<labelname>]__<yy>ww<ww><d><a-z>
            snap-<labelname>__<yy>ww<ww><d><a-z>

        Example:

        ::

            REL3.0FM8revA0__17ww345c
            snap-lay__17ww493a
            snap-RC_phys_3.0__18ww035a

        The algorithm goes like this:
        1. Given:

        ::

            configlist = ["REL3.0FM8revA0__17ww345c", "snap-lay__17ww493a", "snap-RC_phys_3.0__18ww035a"] 
        
        2. Create a new list which has it's <yy><wwd><suffix> as the first element:

        ::

            to_be_sorted = [
                ["REL3.0FM8revA0__17ww345c", "17345c"],
                ["snap-lay__17ww493a", "17493a"],
                ["snap-RC_phys_3.0__18ww035a", "18035a"] 
            ]
        
        3. sort the to_be_sorted list based on the [1] element.
        
        4. return all the [0] elements of the newly sorted list.

        '''
        to_be_sorted = []
        for config in configlist:
            if config.startswith('REL'):
                info = self.get_rel_config_info(config)
            elif config.startswith('snap-'):
                info = self.get_snap_config_info(config)

            if 'wwd' in info:
                if 'milestone' in info:
                    milestone = info['milestone']
                else:
                    milestone = '0.0'
                to_be_sorted.append([config, '{}{}{}'.format(info['yy'], info['wwd'], info['suffix']), milestone])

        sorted_list = sorted(to_be_sorted, key=lambda config_index: (config_index[1], config_index[2]))
        return [x[0] for x in sorted_list]


    def sort_rel_configs(self, configlist):
        ''' 
        | sort the REL* configurations by date stated in the config name, whereby the bomlatest created one is the last one 
        | Any configurations which is not a well-defined released configuration will be dropped.

        | The REL configs look like this:

        ::
          
            REL<milestone><thread>[--<labelname>]__<yy>ww<ww><d><a-z>

        Example:

        ::

            REL3.0ND5revA--TESTING__15ww123b
            REL3.0ND5revA__15ww243c

        The algorithm goes like this:
        1. Given:

        ::

            configlist = ["REL3.0ND5revA__15ww243c", "REL3.0ND5revA__15ww011a", "REL3.0ND5revA__15ww444f"] 
        
        2. Create a new list which has it's <yy><wwd><suffix> as the first element:

        ::

            to_be_sorted = [
                ["REL3.0ND5revA__15ww243c", "15243c"],
                ["REL3.0ND5revA__15ww011a", "15011a"],
                ["REL3.0ND5revA__15ww44f",  "15044f"] 
            ]
        
        3. sort the to_be_sorted list based on the [1] element.
        
        4. return all the [0] elements of the newly sorted list.

        '''
        to_be_sorted = []
        for config in configlist:
            info = self.get_rel_config_info(config)
            if 'wwd' in info:
                to_be_sorted.append([config, '{}{}{}'.format(info['yy'], info['wwd'], info['suffix'])])

        sorted_list = sorted(to_be_sorted, key=lambda config_index: config_index[1])
        return [x[0] for x in sorted_list]

    def sort_snap_configs(self, configlist):
        ''' 
        | sort the snap-* configurations by date stated in the config name, whereby the bomlatest created one is the last one 
        | Any configurations which is not a well-defined snap configuration will be dropped.

        | The snap configs look like this:

        ::
            snap-<labelname>__<yy>ww<ww><d><a-z>

        Example:

        ::
            snap-lay__17ww454a
            snap-lay__17ww493a

        The algorithm goes like this:
        1. Given:

        ::

            configlist = ["snap-lay__17ww454a", "snap-lay__17ww493a"] 
        
        2. Create a new list which has it's <yy><wwd><suffix> as the first element:

        ::

            to_be_sorted = [
                ["snap-lay__17ww454a", "17454a"],
                ["snap-lay__17ww493a", "17493a"],
            ]
        
        3. sort the to_be_sorted list based on the [1] element.
        
        4. return all the [0] elements of the newly sorted list.

        '''
        to_be_sorted = []
        for config in configlist:
            info = self.get_snap_config_info(config)
            if 'wwd' in info:
                to_be_sorted.append([config, '{}{}{}'.format(info['yy'], info['wwd'], info['suffix'])])

        sorted_list = sorted(to_be_sorted, key=lambda config_index: config_index[1])
        return [x[0] for x in sorted_list]

    def get_regex_matching_configs(self, project, variant, libtype, config_regex):
        ''' Get all the configs that matches the regex 
        return in 2 lists:

        ::

            retlist = [
                [all_REL*_configs],
                [all_non-REL*_configs],
            ]

        '''
        rel_configs = []
        snap_configs = []
        nonrel_configs = []
        if not libtype:
            all_configs = self.cli.get_configs(project, variant)
        else:
            libraries = self.cli.get_libraries(project, variant, libtype)
            releases = self.cli.get_library_releases(project, variant, libtype, library='*')
            all_configs = libraries + releases

        for config in all_configs:
            if re.search(config_regex, config):
                if self.get_rel_config_info(config):
                    rel_configs.append(config)
                elif self.get_snap_config_info(config):
                    snap_configs.append(config)
                else:
                    nonrel_configs.append(config)
        return [rel_configs, snap_configs, nonrel_configs]

    def get_thread_of_integration_from_rel_config(self, relconfig):
        ''' Return the thread-of-integration from a given REL* config

        ::

            relconfig = "REL3.0ND5revA__15ww123x"
            thread_of_integration = "REL3.0ND5revA"
            
            relconfig = "REL3.0ND5revA--KIT__15ww123x"
            thread_of_integration = "REL3.0ND5revA--KIT"

            relconfig = "some-non-rel-config"
            thread_of_integration = ""

        '''
        info = self.get_rel_config_info(relconfig)
        
        if not info:
            return ''

        thread_of_integration = 'REL{}{}'.format(info['milestone'], info['thread'])
        if 'label' in info and info['label']:
            thread_of_integration += '--{}'.format(info['label']) 
        return thread_of_integration

    def get_label_from_snap_config(self, snapconfig):
        ''' Return the snap from a given snap-* config

        ::

            snapconfig = "snap-lay__17ww454a"
            label = "snap-lay"
            
            snapconfig = "snap-RC_phys_3.0__17ww473a"
            label = "snap-RC_phys_3.0"

        '''
        info = self.get_snap_config_info(snapconfig)
        
        if not info:
            return ''

        label = 'snap-{}'.format(info['label'])
        return label
   

    def get_rel_config_info(self, config):
        ''' Get the info from the REL config name.

        The REL config looks like this:

        ::

            REL<milestone><thread>[--<labelname>]__<yy>ww<ww><d><a-z>
        
        Example 
        
        ::
        
            REL3.0ND5revA--TESTING__15ww123b

        Return dict

        ::

            {
                milestone   : '3.0'
                thread      : "ND5revA'
                label       : "TESTING"
                yy          : "15"
                wwd         : '123'
                suffix      : 'a'
            }

        (*note:- if the ``wwd`` is only 2 digits, added a '0' prefix to it)

        '''

        ret = {}
        data = ConfigNamingScheme.get_data_for_release_config(config)
        if data:
            ret = {
                "milestone" : data['milestone'],
                "thread"    : '{}rev{}'.format(data['thread'], data['rev']),
                "label"     : data['label'],
                "yy"        : data['year'],
                "wwd"       : data['ww'] + data['day'],
                "suffix"    : data['index'],
            }
        self.logger.debug("{}:{}".format(config, ret))
        return ret

    def get_snap_config_info(self, config):
        ''' Get the info from the snap config name.

        The snap config looks like this:

        ::

            snap-<labelname>__<yy>ww<ww><d><a-z>
        
        Example 
        
        ::
        
            snap-RC_phys_3.0__17ww473a

        Return dict

        ::

            {
                label       : "RC_phys_3.0"
                yy          : "17"
                wwd         : '473'
                suffix      : 'a'
            }

        (*note:- if the ``wwd`` is only 2 digits, added a '0' prefix to it)

        '''

        ret = {}
        data = ConfigNamingScheme.get_data_for_snap_config(config)
        if data:
            ret = {
                "label"     : data['norm_ic'],
                "yy"        : data['year'],
                "wwd"       : data['ww'] + data['day'],
                "suffix"    : data['index'],
            }
        self.logger.debug("{}:{}".format(config, ret))
        return ret



