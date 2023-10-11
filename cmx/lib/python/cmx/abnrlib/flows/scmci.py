#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/abnrlib/flows/scmci.py#18 $
$Change: 7798147 $
$DateTime: 2023/09/27 01:09:59 $
$Author: wplim $

Description: plugin for "quick reporttree"

Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.
'''
from builtins import object
import os
import re
import sys
import logging
import glob
import inspect
lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, lib)

from cmx.dmlib.dmfactory import DMFactory
from cmx.utillib.utils import is_belongs_to_arcpl_related_deliverables, get_ws_from_ward, filtered_cell_not_in_cells, get_ward, get_ws_info
import cmx.utillib.precheck
import cmx.tnrlib.utils
from pprint import pprint
### Import DMX API
dmxlibdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, dmxlibdir)
import dmx.abnrlib.workspace
import dmx.abnrlib.icm
from dmx.abnrlib.config_factory import ConfigFactory
import dmx.abnrlib.icm

class ScmCiError(Exception): pass

class ScmCi(object):

    def __init__(self, cell, stage, deliverable, preview, for_release_bomname):
        self.preview = preview
        self.cells = cell
        self.stages = stage
        self.logger = logging.getLogger(__name__)
        self.deliverable = deliverable
        self.ward = get_ward()

        self.precheck()
        self.wsinfo = get_ws_info(self.ward)
        self.project = self.wsinfo['project']
        self.ip = self.wsinfo['ip']
        self.bom = self.wsinfo['bom']
        self.cthenv = self.wsinfo['cthenv']
        self.icm = dmx.abnrlib.icm.ICManageCLI()
        self.for_release_bomname = for_release_bomname

    def precheck(self):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))

        pc = cmx.utillib.precheck.Precheck()
        pc.is_workarea_defined()
        pc.is_dmxwsinfo_exist(self.ward)
        if self.deliverable == 'backend':
            pc.is_cheetah_env(['r2g', 'ipde'])
        else:
            pc.is_cheetah_env([self.deliverable])

        pc.report()
        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))
 
    def run_dm_checkin(self):
        dutdata = cmx.tnrlib.utils.get_duts_data()
        cells = dutdata
        dm = DMFactory().create_dm(self.cthenv)
        for cell in dutdata.keys():
            if self.cells:
                if cell not in self.cells: continue

            if not dutdata[cell].get('cico'):
                 self.logger.info(f'\'[cico]\' does not found in {cell}.design.cfg. Skip.')
                 continue

            for bundle, tag in dutdata[cell]['cico'].items():
                if self.for_release_bomname:
                    tag = self.for_release_bomname

                if self.stages:
                    if bundle not in self.stages: continue

                dm.stages = [bundle]
                ret = dm.checkin(self.ip, tag, [cell])
           

    def run(self):
        if self.deliverable == 'r2g' or self.deliverable == 'ipde':
            dm = DMFactory().create_dm('arc', f'{self.deliverable}bomcfg') 
            if self.for_release_bomname:
                dm.checkin(self.ip, self.for_release_bomname, self.deliverable)
            else:
                dm_bom = self.icm.get_deliverable_bom(self.project, self.ip, self.bom, self.deliverable, hier=False)[0].name
                dm.checkin(self.ip, dm_bom, self.deliverable)
        else:
            self.run_dm_checkin()

        return 0


