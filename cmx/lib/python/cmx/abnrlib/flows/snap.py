#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/abnrlib/flows/snap.py#6 $
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
from cmx.utillib.utils import get_ws_from_ward, is_belongs_to_arcpl_related_deliverables, get_ward
### Import DMX API
dmxlibdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, dmxlibdir)
import dmx.abnrlib.workspace
import dmx.abnrlib.icm
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.utillib.utils import normalize_config_name, get_ww_details

class SnapError(Exception): pass

class Snap(object):

    def __init__(self, project, ip, bom, deliverable, snapshot):
        self.project = project
        self.ip = ip
        self.deliverable = deliverable
        self.icm = dmx.abnrlib.icm.ICManageCLI()
        self.bom = bom
        self.snapshot = snapshot
        self.logger = logging.getLogger(__name__)
        self.ward = get_ward()
        self.icm = dmx.abnrlib.icm.ICManageCLI()
        self.IS_DELIVERABLE_SNAP = False
        if self.deliverable:
            self.IS_DELIVERABLE_SNAP = True

    def get_snapname(self, project, ip, deliverable, bom, snapshot):
        snapname = ''
        if snapshot:
            snapname = snapshot
        else:
            normalized_config = normalize_config_name(bom)
            (year, ww, day) = get_ww_details()
            snapshot = 'snap-{0}__{1}ww{2}{3}'.format(normalized_config, year, ww, day)
            snapname = self.icm.get_next_snap(project, ip, snapshot, libtype=deliverable, num=-1)
        self.logger.debug("self.snapshot: {}".format(snapname))
        return snapname



    def run(self):
        if self.IS_DELIVERABLE_SNAP:
            self.logger.info('Deliverable snap')
            wspath = get_ws_from_ward(self.ward)
            project, ip, bom = self.icm.get_pvc_from_workspace(wspath)
            cells = self.icm.get_cells_from_project_ip_bom(project, ip, bom)

            dm = DMFactory().create_dm(self.deliverable)
            snapname = self.get_snapname(self.project, self.ip, self.deliverable, self.bom, self.snapshot)
            ret = dm.snap(self.project, self.ip, self.bom, snapname, cells[self.project, self.ip], lock_latest_tag=True)
            return ret

        cells = self.icm.get_cells_from_ipspec_bom(self.project, self.ip, self.bom)
        flatten_srcbom = [x for x in ConfigFactory().create_config_from_full_name(
            f"{self.project}/{self.ip}/{self.bom}").flatten_tree() if isinstance(x, dmx.abnrlib.icmlibrary.IcmLibrary) if is_belongs_to_arcpl_related_deliverables(x.libtype) ]

        for srccfg in flatten_srcbom:
            if(is_belongs_to_arcpl_related_deliverables(srccfg.libtype)):
                dm = DMFactory().create_dm(srccfg.libtype)
                
            cell_to_snap =  cells[srccfg.project, srccfg.variant]

            snapname = self.get_snapname(srccfg.project, srccfg.variant, srccfg.libtype, srccfg.library, self.snapshot)
            ret = dm.snap(srccfg.project, srccfg.variant, srccfg.library, snapname, cell_to_snap, lock_latest_tag=True)

        return ret

        
