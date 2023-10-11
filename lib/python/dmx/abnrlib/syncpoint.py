#!/usr/bin/env python

## @addtogroup dmxlib
## @{

'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/syncpoint.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Contains standard libraries for interacting with the syncpoint system

Author: Lee Cartwright

Copyright (c) Altera Corporation 2015
All rights reserved.
'''
import logging

from dmx.syncpointlib.syncpoint_webapi import SyncpointWebAPI
from dmx.utillib.utils import format_configuration_name_for_printing

class SyncPoint(object):
    '''
    Wraps interactions between ABNR and the syncpoint system
    '''
    def __init__(self, server='sw-web.altera.com'):
        self.server = server
        self.syncpoint = SyncpointWebAPI(web_server=self.server)
        self.logger = logging.getLogger(__name__)

    def get_all_configs_for_syncpoint(self, syncpoint_name):
        '''
        Returns a list of (project, variant, config) tuples for all
        configurations associated with syncpoint_name
        :param syncpoint_name: The name of the syncpoint
        :type syncpoint_name: str
        :return: List of (project, variant, config) tuples
        :type return: list
        '''
        syncpoint_configs = []

        for syncpoint_config in self.syncpoint.get_releases_from_syncpoint(syncpoint_name):
            # get_releases_from_syncpoint returns a list of lists
            # Each inner list is as follows:
            # [<project>, <variant>, <config>]
            # It's possible for config to be blank so ignore those
            if syncpoint_config[2]:
                syncpoint_configs.append((syncpoint_config[0], syncpoint_config[1],
                                          syncpoint_config[2]))
            else:
                self.logger.warn('Syncpoint {0} has no configuration for {1}/{2}'.format(
                    syncpoint_name, syncpoint_config[0], syncpoint_config[1]
                ))

        return syncpoint_configs

    def convert_syncpoint_to_full_config_name(self, project, variant, syncpoint):
        '''
        Converts the syncpoint into a full configuration name in Altera format
        i.e. project/variant@config
        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param syncpoint: The name of the syncpoint
        :type syncpoint: str
        :return: The full config name or an empty string if no config found
        :type return: str
        '''
        full_config_name = ''
        self.logger.debug('Obtaining configuration for syncpoint {0}/{1}@{2}'.format(
            project, variant, syncpoint
        ))
        config = self.syncpoint.get_syncpoint_configuration(syncpoint, project, variant)

        if config:
            full_config_name = format_configuration_name_for_printing(project, variant,
                                                                      config)

        return full_config_name

    def split_syncpoint_name(self, full_syncpoint_name):
        '''
        Takes a full syncpoint name and converts it into its three parts:
        project, variant, syncpoint
        :param full_syncpoint_name: The full syncpoint name in project/variant@syncpoint format
        :type full_syncpoint_name: str
        :return: Tuple of (project, variant, syncpoint)
        :type return: tuple
        '''
        (pv, syncpoint) = full_syncpoint_name.split('@')
        (project, variant) = pv.split('/')

        return (project, variant, syncpoint)

## @}
