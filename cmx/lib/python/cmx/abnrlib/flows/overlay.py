#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/abnrlib/flows/overlay.py#14 $
$Change: 7733831 $
$DateTime: 2023/08/09 03:35:58 $
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

lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, lib)

from cmx.dmlib.dmfactory import DMFactory
import cmx.utillib.utils
from cmx.utillib.utils import is_belongs_to_arcpl_related_deliverables, filtered_cell_not_in_cells, get_ward

### Import DMX API
dmxlibdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, dmxlibdir)
import dmx.abnrlib.workspace
import dmx.abnrlib.icm
from dmx.abnrlib.config_factory import ConfigFactory

class OverlayError(Exception): pass

class Overlay(object):

    def __init__(self, project, ip, deliverables, source_bom, dest_bom, cells, preview=True, hier=False):
        self.preview = preview
        self.project = project
        self.ip = ip
        self.deliverables = deliverables
        self.IS_DELIVERABLE_OVERLAY = False
        if ':' in ip:
            self.default_ip = ip
            self.ip = ip.split(':')[0]
            self.deliverables = ip.split(':')[1]
            self.IS_DELIVERABLE_OVERLAY = True

        self.cells = cells
        self.source_bom = source_bom
        self.dest_bom = dest_bom
        self.hier = hier
        self.logger = logging.getLogger(__name__)
        self.ward = get_ward()
        self.icm = dmx.abnrlib.icm.ICManageCLI()
        self.IS_WORKSPACE_OVERLAY = False


    def run(self):

        wspath = cmx.utillib.utils.get_ws_from_ward(self.ward)
        project, ip, bom = self.icm.get_pvc_from_workspace(wspath)
        if self.IS_DELIVERABLE_OVERLAY:
            if not (is_belongs_to_arcpl_related_deliverables(self.deliverables)):
                return 0

            self.logger.info('Deliverable overlay')
            dm = DMFactory().create_dm(self.deliverables)
            cells =  self.icm.get_cells_from_ipspec_bom(project, ip, bom)
            filtered_cells = filtered_cell_not_in_cells(cells, self.cells)

            # Workspace overlay. Overlay own project/ip:libitype bom only
            if not self.source_bom:
                self.logger.info('Workspace overlay')
                cthfe_bom = [x for x in self.icm.get_deliverable_bom(project, ip, bom, self.deliverables) if x.project == self.project and x.variant == self.ip]
                for srccfg in cthfe_bom:
                    ret = dm.checkin(srccfg.project, srccfg.variant, srccfg.library, filtered_cells[srccfg.project, srccfg.variant])
                return ret

            ret = dm.overlay(self.project, self.ip, self.source_bom, self.dest_bom, filtered_cells[self.project, self.ip])
            return ret


        # Workspace overlay. Overlay all thing in current workspace to bom of ICM workspace = dmx scm ci
        if not self.source_bom:
            self.logger.info('Workspace overlay to bom in ICM workspace')
            ## since we do not have source_bom, we will use workspace bom
            flatten_wsbom = [x for x in ConfigFactory().create_config_from_full_name(
            f"{project}/{ip}/{bom}").flatten_tree() if isinstance(x, dmx.abnrlib.icmlibrary.IcmLibrary)  if is_belongs_to_arcpl_related_deliverables(x.libtype)]

            cells =  self.icm.get_cells_from_project_ip_bom(project, ip, bom)
            filtered_cells = filtered_cell_not_in_cells(cells, self.cells)
            for srccfg in flatten_wsbom: 
                dm = DMFactory().create_dm(self.deliverables)
                if not self.hier:
                    if srccfg.project != self.project or srccfg.variant != self.ip:
                        continue

                if self.dest_bom:
                    dm.checkin(srccfg.project, srccfg.variant, self.dest_bom, filtered_cells[srccfg.project, srccfg.variant])
                else:
                    dm.checkin(srccfg.project, srccfg.variant, srccfg.library, filtered_cells[srccfg.project, srccfg.variant])
            return 0



        cells =  self.icm.get_cells_from_project_ip_bom(self.project, self.ip, self.source_bom)
        ## Filtered cell if user specified cell
        filtered_cells = filtered_cell_not_in_cells(cells, self.cells)

        flatten_srcbom = [x for x in ConfigFactory().create_config_from_full_name(
            f"{self.project}/{self.ip}/{self.source_bom}").flatten_tree() if isinstance(x, dmx.abnrlib.icmlibrary.IcmLibrary)  if is_belongs_to_arcpl_related_deliverables(x.libtype)]
        flatten_dstbom = [x for x in ConfigFactory().create_config_from_full_name(
            f"{self.project}/{self.ip}/{self.dest_bom}").flatten_tree() if isinstance(x, dmx.abnrlib.icmlibrary.IcmLibrary) if is_belongs_to_arcpl_related_deliverables(x.libtype)]

        
        for srccfg in flatten_srcbom:
            ### if not hier, only overlay top ip cell
            if not self.hier:
                if srccfg.project != self.project or srccfg.variant != self.ip:
                    continue

            ### If user specified -d and th elibtype is not part of -d, skip
            if self.deliverables and srccfg.libtype != self.deliverables:
                continue
    
            print(srccfg)
            if(is_belongs_to_arcpl_related_deliverables(srccfg.libtype) ):
                dm = DMFactory().create_dm(srccfg.libtype)

                for dstcfg in flatten_dstbom:
                    print(dstcfg)
                    if dstcfg.libtype == srccfg.libtype and dstcfg.project == srccfg.project and dstcfg.variant == srccfg.variant and filtered_cells.get(srccfg.project, srccfg.variant):
                       dm.overlay(srccfg.project, srccfg.variant, srccfg.library, dstcfg.library, filtered_cells[srccfg.project, srccfg.variant])

        return 0

        
