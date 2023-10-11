#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/abnrlib/flows/scmco.py#3 $
$Change: 7798167 $
$DateTime: 2023/09/27 01:24:54 $
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

### Import DMX API
dmxlibdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, dmxlibdir)
import dmx.abnrlib.workspace
import dmx.abnrlib.icm
from dmx.abnrlib.config_factory import ConfigFactory

class ScmCoError(Exception): pass

class ScmCo(object):

    def __init__(self, cell, stage, deliverable, preview, precheck=True):
        self.preview = preview
        self.cells = cell
        self.stages = stage
        self.logger = logging.getLogger(__name__)
        self.deliverable = deliverable
        self.ward = get_ward()
        if precheck:
            self.precheck()
        self.wsinfo = get_ws_info(self.ward)
        self.project = self.wsinfo['project']
        self.ip = self.wsinfo['ip']
        self.bom = self.wsinfo['bom']
        
        self.cthenv = self.wsinfo['cthenv']
        self.icm = dmx.abnrlib.icm.ICManageCLI()

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
 
           
    def run_arc_population(self):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        dm_bom = self.icm.get_deliverable_bom(self.project, self.ip, self.bom, self.deliverable, hier=False)[0].name
        arc_dm = DMFactory().create_dm('arc', f'{self.deliverable}bomcfg')
        arc_dm.sync(self.project, self.ip, dm_bom)
        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))

        
    def run_dm_population(self, dmtype):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        dutdata = cmx.tnrlib.utils.get_duts_data()
        cells = dutdata
        dm = DMFactory().create_dm(dmtype)
        co_sections = []

        for cell in dutdata.keys():
            if self.cells:
                if cell not in self.cells: continue

            if not dutdata[cell].get('cico') and not dutdata[cell].get('co'): 
                self.logger.info(f'\'[cico]/[co]\' does not found in {cell}.design.cfg. Skip.')
                continue

            if dutdata[cell].get('cico'):
                co_sections.append('cico')
            if dutdata[cell].get('co'):
                co_sections.append('co')

            for section in co_sections:
                for bundle, tag in dutdata[cell][section].items():
                    if self.stages:
                        if bundle not in self.stages: continue
                    dm.stages = [bundle]
                    ret = dm.sync(self.project, self.ip, tag, [cell])
        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))


    def run(self):
        '''
        if --r2gbomcfg/--ipdebomcfg:
            sync only the bomcfg
        else if no option or --cell/--bundle:
            sync the option
        '''
        if self.deliverable == 'r2g' or self.deliverable == 'ipde':
            self.run_arc_population()
        else:
            self.run_dm_population(self.cthenv)
        return 0


