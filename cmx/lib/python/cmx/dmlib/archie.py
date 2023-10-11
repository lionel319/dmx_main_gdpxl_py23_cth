#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/dmlib/archie.py#1 $
$Change: 7733831 $
$DateTime: 2023/08/09 03:35:58 $
$Author: wplim $

Description: Abstract base class used for representing IC Manage configurations. See: http://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/ICMConfigurationClass for more details

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import os
import sys
import logging
from configparser import ConfigParser
from cmx.dmlib.dmbase import DMBase

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(0, LIB)

LOGGER = logging.getLogger(__name__)


class ARCHIEError(Exception): pass


class ARCHIE(DMBase):

    def __init__(self, stages=None):
        scm_name = 'archie'
        main_cmd = 'cmd'
        cell_option = 'cell'
        stage_option = 'stage'
        tag_option = 'tag'
        sync_option = 'sync'
        ci_option = 'ci'
        force_option = 'force'
        config_parser = ConfigParser()
        cp_dict = config_parser.read(f'{LIB}/cmx/constants/arcplwrapper.ini')
        if len(cp_dict) == 0:
            raise Exception("Could not find the arcpl wrapper configuration file.")
        else:
            if config_parser.has_option(scm_name, main_cmd) and config_parser.has_option(scm_name, cell_option) and \
                    config_parser.has_option(scm_name, stage_option) and config_parser.has_option(scm_name, tag_option):
                cmd_options = {
                    'cmd': config_parser.get(scm_name, main_cmd),
                    'cell': config_parser.get(scm_name, cell_option),
                    'stage': config_parser.get(scm_name, stage_option),
                    'tag': config_parser.get(scm_name, tag_option),
                    'sync': config_parser.get(scm_name, sync_option),
                    'ci': config_parser.get(scm_name, ci_option),
                    'force': config_parser.get(scm_name, force_option)
                }
            else:
                raise Exception(f"Could not find the {scm_name} configuration from the wrapper configuration file.")
        stages = stages if stages else os.environ.get('DMX_ARCHIE_BUNDLES', 'all').split(',')
        super().__init__(stages, 'ipde', cmd_options)
        self.logger = LOGGER


if __name__ == "__main__":
    sys.exit(main())
