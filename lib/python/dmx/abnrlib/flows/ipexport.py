#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/ipexport.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: dmx "ip import" subcommand plugin

Author: Mitchell Conkin
Copyright (c) Intel Corporation 2019
All rights reserved.
'''
import os
import subprocess
import dmx.abnrlib.flows.workspacepopulate
import dmx.utillib.eximport_utils 
import dmx.abnrlib.workspace
import dmx.abnrlib.icm
import logging

class IPExportError(Exception): pass

class IPExport(object):
    '''
    Runner class for dmx ip export 
    '''

    def __init__(self, project, ip, bom, deliverables, format):
        self.project = project
        self.ip = ip
        self.bom = bom 
        self.deliverables = deliverables
        self.format = format 
        self.stagingws = '/nfs/site/disks/psg_dmx_1/ws/'
        dmx.utillib.utils.set_dmx_workspace(self.stagingws)
        self.wsname = ':icm:' 
        self.logger = logging.getLogger(__name__)
        self.service = 'export'

        #self.expand_str = {"${IP}": self.ip, "${PROJECT}": self.project, "${BOM}": self.bom, "${DEST}":os.environ.get('WARD')} 
        self.expand_str = {"${IP}": self.ip, "${PROJECT}": self.project, "${BOM}": self.bom, "${DEST}":os.environ.get('WARD')} 
        self.icm = dmx.abnrlib.icm.ICManageCLI()

    def get_all_format_name(self):
        result = dmx.utillib.eximport_utils.get_format_name('export')
        self.logger.info('Available format name for export: {}'.format(result))

    def populate_icm_workspace(self):
        '''
        ws = dmx.abnrlib.flows.workspacepopulate.WorkspacePopulate(self.project, self.ip, self.bom, self.wsname, cfgfile=None, deliverables=self.deliverables, preview=None, debug=True, force_cache=False)
        ws.run()
        clientname = ws.wsclient
        wsroot = ws._get_wsroot()
        '''
    
        ws = self.icm.add_workspace(self.project, self.ip, self.bom, username=os.environ['USER'], dirname=self.stagingws, ignore_clientname=False, libtype=None)
        clientname = ws
        wsroot = self.stagingws + '/' + ws 
        self.icm.sync_workspace(clientname, skeleton=False, variants=['all'], libtypes=['all'], specs=[], force=True, verbose=False, skip_update=False, only_update_server=False)


        return wsroot

    def run(self):
        # populate staging icm workspace
        self.wsroot = self.populate_icm_workspace()
        #self.wsroot = '/nfs/site/disks/psg_dmx_1/ws/wplim.i10socfm.liotest1.4210'
        self.logger.info('Workspace root: {}'.format(self.wsroot))
        self.expand_str['${SOURCE}'] = self.wsroot

       
        dmx.utillib.eximport_utils.run_mapper_and_generator_file(self.service, self.format, self.deliverables, self.expand_str)
        ws = dmx.abnrlib.workspace.Workspace(workspacepath=self.wsroot)
        ws.delete(preserve=False, force=True)    
 

        self.logger.debug('deleted {}'.format(self.wsroot))
        self.logger.info('Export succesfully.')
