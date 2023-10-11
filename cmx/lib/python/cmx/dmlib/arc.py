#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/dmlib/arc.py#4 $
$Change: 7773972 $
$DateTime: 2023/09/08 02:39:09 $
$Author: lionelta $

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


class ARCError(Exception): pass


class ARC(DMBase):

    def __init__(self, stage=None):
        scm_name = 'arc'
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
        self.stage = stage
        super().__init__([self.stage], 'None', cmd_options)
        self.logger = LOGGER

    def sync(self, project, ip, bom):
        self.logger.info(f"Sync using {self.cmd_options['cmd']}")

        cmd = self._generate_wrapper_command(self.cmd_options['sync'], ip, self.stage, bom)
        self._execute_command(cmd)

        self.logger.info(f"Done sync using {self.cmd_options['cmd']}")
    
    @classmethod
    def get_bom_cfg_file(cls, citype):
        cfgfile = f"{os.environ.get('DB_THREAD')}.{citype}.cfg"
        cfgroot = f"{os.environ.get('DMXDATA_ROOT')}/{os.environ.get('DB_FAMILY')}/bomcfgfiles" 
        bomfile = f"{cfgroot}/{cfgfile}"
        if not os.path.exists(bomfile):
            bomfile = f"{cfgroot}/default.{citype}.cfg" 
        return bomfile

    def checkin(self, ip, bom, citype):
        self.logger.info(f"Check-in using {self.cmd_options['cmd']}")
        bomfile = self.get_bom_cfg_file(citype)
        wrapper_cmd = self._generate_wrapper_command(self.cmd_options['ci'], ip, self.stage, bom, f" -bom {bomfile}")
        if self._execute_command(wrapper_cmd) != 0:
            raise Exception('Exitcode non-zero')
            
        self.logger.info(f"Done check-in using  {self.cmd_options['cmd']}")


if __name__ == "__main__":
    sys.exit(main())
