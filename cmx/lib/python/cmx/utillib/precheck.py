#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/utillib/precheck.py#5 $
$Change: 7756464 $
$DateTime: 2023/08/25 01:53:39 $
$Author: wplim $

Description: Class to return list of Precheck 

'''
import os
import sys
import logging
from pprint import pprint, pformat

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, LIB)


import dmx.abnrlib.icm

class Precheck(object):
   
    def __init__(self):
        self.errlist = [] 
        self.icm = dmx.abnrlib.icm.ICManageCLI()
        self.logger = logging.getLogger(__name__)

    def is_workarea_defined(self):
        if not os.getenv("WORKAREA"):
            self.errlist.append("$WORKAREA environment variable not defined.")

    def is_workarea_empty(self):
        all_files = [x for x in os.listdir(os.getenv("WORKAREA")) if not x.startswith('.') and not x.startswith('.git')]
        if all_files:
            self.errlist.append("$WORKAREA is not empty.")
            return False
        return True

    def is_dmxwsinfo_exist(self, workarea):
        if not os.path.exists(f"{workarea}/.dmxwsinfo"):
            self.errlist.append(f"{workarea} does not have .dmxwsinfo. This is not a valid dmx workspace.")


    def is_bom_immutable(self, bom):
        if not bom.startswith('REL') and not bom.startswith('snap-'):
            self.errlist.append(f"\'{bom}\' is not an immutable bom.")
    
    def is_config_exists(self, project, ip, bom):
        if not self.icm.config_exists(project, ip, bom):
            self.errlist.append(f"{project}/{ip}@{bom} does not exists.")

    def is_deliverable_exists(self, project, ip, bom, deliverable):
        if not self.icm.get_deliverable_bom(project, ip, bom, deliverable):
            self.errlist.append(f"{project}/{ip}@{bom} does not contain \'{deliverable}\' deliverable.")

    
    def is_cheetah_env(self, names):
        err = True
        cthenv = ''
        for name in names:
            if f'_{name.upper()}_' in os.environ.get('CTH_SETUP_CMD'):
                cthenv = name
                err = False
        if err is True:
            self.errlist.append(f'You need to be inside {name} environment to run this command.')
        return cthenv.lower() 

    def is_deliverable_bom_immutable(self, project, ip, bom, deliverable):
        deliverable_bom = self.icm.get_deliverable_bom(project, ip, bom, deliverable)
        if deliverable_bom:
            if not deliverable_bom[0].lib_release:
                self.errlist.append(f"{deliverable_bom[0].get_full_name(legacy_format=True)} need to be REL/snap-.")
 
    def report(self):
        if self.errlist:
            self.logger.error("  - FAIL: precheck. Please check the errors below. \n{}".format(pformat(self.errlist)))
            raise Exception("FAIL: precheck")

