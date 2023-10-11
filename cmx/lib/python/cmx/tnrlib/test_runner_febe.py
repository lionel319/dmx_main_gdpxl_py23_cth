#!/usr/bin/env python

import os
import sys
import json
from pprint import pprint
import textwrap
import logging

CMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, DMXLIB)
sys.path.insert(0, CMXLIB)

import cmx.tnrlib.test_runner
import cmx.abnrlib.flows.workspacepopulate
import dmx.abnrlib.icm
import cmx.tnrlib.utils

sys.path.insert(0, '/p/cth/rtl/proj_tools/cth_mako_render/23.03.001')
import cth_design_cfg


class TestRunnerFebe(cmx.tnrlib.test_runner.TestRunnerPoc):
    '''
    The reason why we need TestRunnerFebe is because:-
    1. 'dmx workspace populate -d febe' is in r2g environment, which means the WORKAREA is a r2g workarea.
    2. but, during 'dmx workspace check', we can not(should not) get the duts & tnrwaivers.csv files from the WORKAREA
       > we need to get it from the WORKAREA of the CTHFE IP_MODEL.
       > This is because febe is generated from the duts of the CTHFE git.
    3. that is the reason why, we need to override the 'get_cells()' and 'get_tnrwaivers_files()' methods to get those files from IP_MODEL.
    '''

    def __init__(self, thread=None, milestone=None, deliverable=None, workspace_root=None, ipname=None, stepname='a0'):
        super().__init__(thread=thread, milestone=milestone, deliverable=deliverable, workspace_root=workspace_root, ipname=ipname, stepname=stepname)
        self.cthfe_ip_model_path = ''

    def get_pvc_from_workspace(self):
        infile = os.path.join(self.workspace_root, '.dmxwsinfo')
        with open(infile) as f:
            data = json.load(f)
        return [data['project'], data['ip'], data['bom']]

    def get_cells(self):
        ip_model_path = self.get_cthfe_ip_model_path()
        cfgdir = os.path.join(ip_model_path, 'cfg')
        dutdata = cmx.tnrlib.utils.get_duts_data(cfgdir)
        cells = dutdata.keys()
        if not cells:
            raise Exception("There are not duts found in this workarea: {}.".format(cfgdir))
        return cells

    def get_tnrwaivers_files(self):
        if not self._tnrwaivers_files:
            ip_model_path = self.get_cthfe_ip_model_path()
            filepath = os.path.join(ip_model_path, 'psgcheck', 'tnrwaivers.csv')
            if os.path.isfile(filepath):
                self._tnrwaivers_files.append(filepath)
        return self._tnrwaivers_files

    def get_cthfe_ip_model_path(self):
        if not self.cthfe_ip_model_path:
            [project, ip, bom] = self.get_pvc_from_workspace()
            wspop = cmx.abnrlib.flows.workspacepopulate.WorkspacePopulate(project, ip, bom, deliverable='febe', force=True)
            febe_bom = dmx.abnrlib.icm.ICManageCLI().get_deliverable_bom(project, ip, bom, 'febe', hier=False)[0].name
            cthfe_reltag = wspop.get_cthfe_reltag_from_febe_bom(project, ip, febe_bom)
            ip_model_path = wspop.get_ip_models(project, ip, 'cthfe', cthfe_reltag)
            self.cthfe_ip_model_path = ip_model_path
        return self.cthfe_ip_model_path

