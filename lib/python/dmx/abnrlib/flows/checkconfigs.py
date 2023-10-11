#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/checkconfigs.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "abnr clonehier"

Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.
'''
import logging
import textwrap
import sys
import itertools
from pprint import pprint

from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.syncpoint import SyncPoint
from dmx.abnrlib.icm import ICManageCLI
from dmx.utillib.arcenv import ARCEnv

class CheckConfigsError(Exception): pass

class CheckConfigs(object):
    '''
    Runs the abnr checkconfigs command
    '''
    def __init__(self, project='', variant='', config='', syncpoints=[], preview=True, ignore_top=True):
        '''
        if ignore_top == True
            the given project/variant@config will not be checked for conflicts
            only the children of project/variant@config will be checked
        '''
        self.logger = logging.getLogger(__name__)
        self.project = project
        self.variant = variant
        self.config = config
        self.syncpoints = syncpoints
        self.ignore_top = ignore_top
        self.allconfigs = {}
        self.conflicts = {}
        self.cli = ICManageCLI(preview)

        if project and variant and config:
            if not self.cli.project_exists(project):
                raise CheckConfigsError("{0} does not exist".format(project))
            if not self.cli.variant_exists(project, variant):
                raise CheckConfigsError("{0}/{1} does not exist".format(project, variant))    

    def run(self):
        self.get_all_configs()
        self.report_conflicts()
        return self.conflicts

    def report_conflicts(self):
        '''
        self.conflicts = {
            (project, variant) = [(config, source), (config, source)]
        }
        '''
        for p in self.allconfigs:
            for v in self.allconfigs[p]:
                count = len(self.allconfigs[p][v].keys())
                if count > 1:
                    self.conflicts[(p,v)] = []
                    for c in self.allconfigs[p][v]:
                        source = self.allconfigs[p][v][c]
                        err  = [c, 'syncpoint/pvc: {}/{}'.format(source['syncpoint'], source['parent'])]
                        self.conflicts[(p, v)].append(err)
        return self.conflicts

    def get_all_configs(self):
        '''
        self.allconfigs = {
            project: {
                variant: {
                    config: {
                        syncpoint: <syncpointname>,
                        parent: <project/variant@config>,
                    }
                }
            }
        }
        '''
        if self.project and self.variant and self.config:
            configs = self.get_hierarchical_configs_from_pvc(self.project, self.variant, self.config)
            for p, v, c in configs:
                if not self.ignore_top or (p != self.project or v != self.variant or c != self.config):
                    self.add_pvc_to_allconfigs(p, v, c, {'syncpoint': None, 'parent': [self.project, self.variant, self.config]})

        sp_server = SyncPoint()
        for syncpoint in self.syncpoints:
            all_syncpoint_pvc = sp_server.get_all_configs_for_syncpoint(syncpoint)
            for (project, variant, config) in all_syncpoint_pvc:
                configs = self.get_hierarchical_configs_from_pvc(project, variant, config)
                for p, v, c in configs:
                    self.add_pvc_to_allconfigs(p, v, c, {'syncpoint': syncpoint, 'parent': [project, variant, config]})
        
        return self.allconfigs


    def add_pvc_to_allconfigs(self, project, variant, config, data={}):
        if project not in self.allconfigs:
            self.allconfigs[project] = {}
        if variant not in self.allconfigs[project]:
            self.allconfigs[project][variant] = {}
        if config not in self.allconfigs[project][variant]:
            self.allconfigs[project][variant][config] = data


    def get_hierarchical_configs_from_pvc(self, project, variant, config):
        ''' Given project/variant/config, return all the children configs found in it, like this;

        return = [
            [project, variant, config],
            [project, variant, config],
            ... ... ...
        ]
        '''
        cf = ConfigFactory.create_from_icm(project, variant, config)
        configs = [x for x in cf.flatten_tree() if x.is_config()]
        ret = []
        for c in configs:
            ret.append([c.project, c.variant, c.config])
        return ret

    def run_old(self):
        ret = 1

        if self.syncpoints:
            self.convert_syncpoints_to_configs()
            self.check_syncpoint_configs_for_clashes()

        problems = self.get_list_of_problems()
        if problems:
            for problem in problems:
                self.logger.error(problem)
            ret = problems
        else:
            ret = []
            self.logger.info('No issues found')

        return ret

    def get_list_of_problems(self):
        '''
        Performs all checks required against the configuration and returns
        any problems found
        :return: List of proble/error messages
        :type return: list
        '''
        problems = self.config.validate()
        self.logger.debug('Detected {0} config validation problems'.format(len(problems)))
        if self.syncpoints:
            problems += self.get_config_syncpoint_violations()

        return problems

    def get_config_syncpoint_violations(self):
        '''
        Checks self.config for any syncpoint violations - configurations
        for a given project/variant that are different from the config
        registered as the syncpoint
        :return: List of error messages
        :type return: list
        '''
        violations = []

        for syncpoint_config in self.syncpoint_configs:
            pv_configs = self.config.search(project=syncpoint_config.project,
                                            variant='^{}$'.format(syncpoint_config.variant),
                                            libtype=None)

            for pv_config in pv_configs:
                self.logger.debug('Checking tree config {0} against syncpoint config {1}'.format(
                    pv_config.get_full_name(), syncpoint_config.get_full_name()
                ))
                if syncpoint_config != pv_config:
                    violations.append('{0} does not match the current syncpoint configuration for {1}/{2}. Should be {3}'.format(
                        pv_config.get_full_name(), syncpoint_config.project, syncpoint_config.variant,
                        syncpoint_config.get_full_name()
                    ))

        return violations

    def convert_syncpoints_to_configs(self):
        '''
        Converts the syncpoint specified on the command line into
        it's corresponding IC Manage configurations
        The list of configurations are stored in self.syncpoint_configs
        '''
        sp_server = SyncPoint()

        for syncpoint in self.syncpoints:
            all_syncpoint_pvc = sp_server.get_all_configs_for_syncpoint(syncpoint)

            if not all_syncpoint_pvc:
                self.logger.warning('No configurations associated with syncpoint {0}'.format(syncpoint))

            for (project, variant, config) in all_syncpoint_pvc:
                self.syncpoint_configs.append(ConfigFactory.create_from_icm(project, variant, config))

    def check_syncpoint_configs_for_clashes(self):
        '''
        Checks the list of configurations obtained from the syncpoints to see if there
        are clashes.
        Raises an exception if clashes are detected.
        '''
        configs_by_pv = {}
        clash_detected = False

        for config in self.syncpoint_configs:
            if config.location_key() in configs_by_pv:
                configs_by_pv[config.location_key()].append(config)
            else:
                configs_by_pv[config.location_key()] = [config]

        for key in configs_by_pv:
            if len(configs_by_pv[key]) > 1:
                self.logger.error('Configuration clashes detected from syncpoints: {}'.format(
                    ' '.join([x.get_full_name() for x in configs_by_pv[key]])
                ))
                clash_detected = True

        if clash_detected:
            raise CheckConfigsError('Clashes detected in the configurations obtained from syncpoints')
