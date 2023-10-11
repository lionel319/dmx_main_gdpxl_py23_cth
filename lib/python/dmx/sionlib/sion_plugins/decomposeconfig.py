#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/sionlib/sion_plugins/decomposeconfig.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr "printconfig" subcommand plugin
Author: Lee Cartwright
Copyright (c) Altera Corporation 2015
All rights reserved.
'''
import sys
import logging
import textwrap
import csv
from datetime import datetime
import re

from dmx.abnrlib.icmconfig import ICMConfig
from dmx.abnrlib.icmsimpleconfig import SimpleConfig, SimpleConfigError
from dmx.utillib.utils import format_configuration_name_for_printing
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.icm import ICManageCLI

class DecomposeConfigError(Exception): pass

class DecomposeConfig(object):
    '''
    Runner subclass for the abnr printconfig subcommand
    '''
    def __init__(self, project, variant, config, show_simple=False, show_libraries=False,
                 nohier=False, csv=None, libtype=None, variant_filter=[], libtype_filter=[], show_composite=False):
        '''
        Initialiser for the DecomposeConfigRunner class

        :param project:  The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param config: The IC Manage config
        :type config: str
        :param show_simple: Flag indicating whether or not to include simple configs in the output
        :type show_simple: bool
        :param show_libraries: Flag indicating whether or not to show library/release information in output
        :type show_libraries: bool
        :param csv: Specifies a filename to write  the report to in CSV format
        :type csv: str or None
        '''
        self.project = project
        self.variant = variant
        self.libtype = libtype
        self.cli = ICManageCLI(preview=True)
        if not self.cli.project_exists(self.project):
            raise DecomposeConfigError("{0} does not exist".format(self.project))
        if not self.cli.variant_exists(self.project, self.variant):
            raise DecomposeConfigError("{0}/{1} does not exist".format(self.project, self.variant))       
        self.config = ConfigFactory.create_from_icm(project, variant, config, libtype=libtype, preview=True)
        self.show_simple = show_simple
        self.show_composite = show_composite
        self.show_libraries = show_libraries
        self.nohier = nohier
        self.csv = csv
        self.variant_filter = variant_filter
        self.libtype_filter = libtype_filter

        # If show_libraries is set then show_simple must also be True, even if not
        # explicitly requested
        if self.show_libraries:
            self.show_simple = True
        # If libtype_filter is applied, we are showing simple configs. Set show_simple to true
        if self.libtype_filter:
            self.show_simple = True            

        self.logger = logging.getLogger(__name__)

    def __eq__(self, other):
        return self.get_full_name==other.get_full_name

    def run(self):
        '''
        Runs the printconfig abnr subcommand
        '''
        ret = 0
        simple_configs = []
        composite_configs = []
        last_modified_date = self.get_config_last_modified_date()
        if self.config.is_simple():
            simple_configs.append(self.config)
        else:
            simple_configs = self.decompose_simple(config = self.config)
            composite_configs.append(self.config)
            composite_configs+=self.decompose_composite(config = self.config)
        if self.show_composite :
            return composite_configs
        elif self.show_simple :
            return simple_configs

    def decompose_simple(self, config=None, depth=0, all_simple_configs=[]):
      if(config != None) :
        for x in config.configurations :
            if (x.is_simple() and (x not in all_simple_configs)) :
                all_simple_configs.append(x)
        for x in config.configurations :
            if x.is_composite() :
              all_simple_configs = self.decompose_simple(config = x, all_simple_configs = all_simple_configs)
        return all_simple_configs

    def decompose_composite(self, config=None, depth=0, all_composite_configs=[]):
      if(config != None) :
        for x in config.configurations :
            if x.is_composite() and not (x in all_composite_configs) :
                all_composite_configs.append(x)
		all_composite_configs = self.decompose_composite(config = x, all_composite_configs = all_composite_configs)
        return all_composite_configs

    def return_config(self) :
        config_string = ''
        last_modified_date = self.get_config_last_modified_date()
        if not last_modified_date:
            raise PrintConfigError('Problem getting configuration last modified date for {0}'.format(
                self.config.get_full_name()
            ))

        if self.config.is_simple():
            config_string+=self.return_header(last_modified_date) + '\n'
            config_string+=self.format_simple_config() + '\n'

            #print self.format_simple_config()
        else:
            # Filter only works for composite configuration
            if self.variant_filter and not self.libtype_filter:
                results = []
                for variant in self.variant_filter:
                    results = results + [str(x) for x in self.config.search(
                                                        variant='^{}$'.format(variant),
                                                        libtype=None)]
                for result in sorted(list(set(results))):
                    config_string+=result + '\n'
                    #print result
            elif not self.variant_filter and self.libtype_filter:
                results = []
                for libtype in self.libtype_filter:
                    results = results + [str(x) for x in self.config.search(
                                                        libtype='^{}$'.format(libtype))]
                for result in sorted(list(set(results))):
                    config_string+=result + '\n'
                    #print result
            elif self.variant_filter and self.libtype_filter:
                results = []
                for variant in self.variant_filter:
                    for libtype in self.libtype_filter:
                        results = results + [str(x) for x in self.config.search(
                                                        variant='^{}$'.format(variant),
                                                        libtype='^{}$'.format(libtype))]
                for result in sorted(list(set(results))):
                    config_string+=result + '\n'
                    #print result
            else:
                config_string+=self.return_header(last_modified_date) + '\n'
                config_string+= self.config.report(show_simple=self.show_simple,
                                         show_libraries=self.show_libraries,
                                         nohier=self.nohier) + '\n'
        return config_string

    def format_simple_config(self):
        '''
        Formats a top-level simple configuration for printing to stdout
        :param config_details: The configuration details
        :type config_details: dict
        :return: Formatted string representing the config
        :type return: str
        '''
        formatted_output = '\tLibtype: {0}, Library: {1}, Release: {2}'.format(
                    self.config.libtype, self.config.library,
                    self.config.lib_release
                )

        return formatted_output

    def return_header(self, last_modified_date):
        '''
        Decomposes the standard header for the configuration
        :param last_modified_date: The configuration details
        :type last_modified_date: str
        '''
        header = ''
        if self.config.is_simple():
            header += 'Project: {0}, IP: {1}, Deliverable: {2}, BOM: {3}'.format(
                self.project, self.variant, self.libtype,
                self.config.config
            ) + '\n'
        else:
            header += 'Project: {0}, IP: {1}, BOM: {2}'.format(
                self.project, self.variant, self.config.config
            ) + '\n'

        header += '\tLast modified: {0} (in server timezone)'.format(last_modified_date) + '\n'
        return header

    def get_config_last_modified_date(self):
        '''
        Gets the configuration last modified date from IC Manage depot
        :return: String of the date
        :type return: str
        '''
        # Get the last modified date from Perforce
        last_modified_data = self.cli.get_configs_last_modified_data(self.project,
                                                                     self.variant,
                                                                     self.config.config,
                                                                     libtype=self.libtype)

        date = '{0}/{1}/{2} {3}:{4}:{5}'.format(
            last_modified_data['year'], last_modified_data['month'],
            last_modified_data['day'], last_modified_data['hours'],
            last_modified_data['minutes'], last_modified_data['seconds']
        )

        return date

    def write_csv(self):
        '''
        Writes the configuration report in CSV format to self.csv
        '''
        with open(self.csv, 'w') as csvfile:
            fieldnames = ['project', 'variant', 'config', 'libtype', 'library', 'release', 'sub_configs']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            self.csv_report(writer, self.config)

    def csv_report(self, writer, config):
        '''
        Writes config to the writer csv object. Recurses through the configuration tree.

        :param writer: The CSV DictWriter object used for writing
        :type writer: DictWriter
        :param config: The configuration being written to csv
        :type config: ICMConfig
        '''
        row_data = {
            'project' : config.project,
            'variant' : config.variant,
            'config' : config.config,
        }

        # Only sort the sub_configs once
        sorted_configs = []
        if config.is_composite():
            all_configs = config.configurations
            if not self.show_simple:
                all_configs = [x for x in all_configs if x.is_composite()]

            sorted_configs = sorted(all_configs, key=lambda x: x.get_full_name())

        if config.is_simple():
            row_data['libtype'] = config.libtype
            if self.show_libraries:
                row_data['library'] = config.library
                row_data['release'] = config.lib_release
        else:
            row_data['sub_configs'] = ' '.join([x.get_full_name() for x in sorted_configs])

        if self.variant_filter and not self.libtype_filter:
            if row_data['variant'] in self.variant_filter:
                writer.writerow(row_data)
        elif not self.variant_filter and self.libtype_filter:
            if 'libtype' in row_data:
                if row_data['libtype'] in self.libtype_filter:
                    writer.writerow(row_data)
        elif self.variant_filter and self.libtype_filter:
            if 'libtype' in row_data:
                if row_data['variant'] in self.variant_filter and row_data['libtype'] in self.libtype_filter:
                    writer.writerow(row_data)
        else:
             writer.writerow(row_data)
        for sub_config in sorted_configs:
            if sub_config.is_simple() and not self.show_simple:
                continue

            self.csv_report(writer, sub_config)

