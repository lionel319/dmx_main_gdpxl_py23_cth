#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/abnrlib/flows/workspacepopulate.py#25 $
$Change: 7798229 $
$DateTime: 2023/09/27 02:08:04 $
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
import tempfile
import time
import datetime
import json
import inspect
import pprint
import pytz 

lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, lib)

from cmx.dmlib.dmfactory import DMFactory
from cmx.abnrlib.flows.dmxmoab import DmxMoab
from cmx.utillib.utils import is_belongs_to_arcpl_related_deliverables, get_ws_from_ward, get_ward, run_command
import cmx.utillib.precheck
import cmx.tnrlib.utils
import cmx.abnrlib.flows.scmco

### Import DMX API
dmxlibdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, dmxlibdir)
import dmx.abnrlib.workspace
import dmx.abnrlib.icm
from dmx.abnrlib.config_factory import ConfigFactory
import dmx.utillib.loggingutils

class WorkspacePopulateError(Exception): pass

class WorkspacePopulate(object):

    USE_ICM_CLIENT_KEYWORD = ':icm:'

    def __init__(self, project, ip, bom, deliverable=None, preview=False, debug=False, hier=False, force=False):
        self.project = project
        self.ip = ip 
        self.bom = bom
        self.deliverable = deliverable
        self.preview = preview
        self.logger = logging.getLogger(__name__)
        self.debug = debug
        self.hier = hier
        self.force = force
        self.icm = dmx.abnrlib.icm.ICManageCLI()
        self.workarea = os.environ.get("WORKAREA")
        os.environ['GIT_REPOS'] = '/nfs/site/disks/psg.git.001' 
        os.environ['IP_MODELS'] = '/nfs/site/disks/psg.mod.000' 
        self.precheck()
        self.gen_workspace_info()

    def gen_workspace_info(self):
        sc_timezone = pytz.timezone("America/Los_Angeles")
        pg_timezone = pytz.timezone("Asia/Kuala_Lumpur")

        sc_now = datetime.datetime.now(sc_timezone)
        pg_now = datetime.datetime.now(pg_timezone)
        sc_date_time = sc_now.strftime("%m/%d/%Y, %H:%M:%S")
        pg_date_time = pg_now.strftime("%m/%d/%Y, %H:%M:%S")
        command = sys.argv[0]
        dmxlog = dmx.utillib.loggingutils.get_dmx_log_full_path()

        data = {'created_at(SC)': sc_date_time, 'created_at(PNG)': pg_date_time, 'project': self.project, 'ip': self.ip, 'bom': self.bom, \
                'cmd': ' '.join(sys.argv), 'DMX_ROOT': os.environ.get('DMX_ROOT'),  'DMXDATA_ROOT': os.environ.get('DMXDATA_ROOT'), \
                'CTH_SETUP_CMD':  os.environ.get('CTH_SETUP_CMD'), 'log': dmxlog, 'cthenv': self.cthenv } 

        with open(f"{self.workarea}/.dmxwsinfo", "w") as file:
            json.dump(data, file, indent=4)


    def create_git_workspace(self, ip_models, git_bom):
        '''
        Create a git workspace in $WORKAREA
        '''
        self.logger.info(f'Creating {self.deliverable} workspace')
        #cmd = f'rm -rf {os.environ.get("WORKAREA")}/*; rm -rf {os.environ.get("WORKAREA")}/.git*; rm -rf {os.environ.get("WORKAREA")}/.created_at;'
        #self.logger.info(cmd)
        #os.system(cmd) 
        if self.icm.is_name_immutable(git_bom):
            #cmd = f'cp -rLf {ip_models}/* {os.environ.get("WORKAREA")}/.'
            cmd = f'rsync -axzl --exclude=.git --exclude=".icm*" rsync.zsc7.intel.com:{ip_models}/* {os.environ.get("WORKAREA")}/.'
        else:
            cmd = f'git clone {os.environ.get("GIT_REPOS")}/git_repos/{self.ip}-a0 {os.environ.get("WORKAREA")}'
        self.logger.info(cmd)
        ret = os.system(cmd) 
        if ret == 0:
            self.logger.info(f'{self.deliverable} workspace for {self.project}/{self.ip}:{self.bom} created in {os.environ.get("WORKAREA")}. ')

    def get_ip_models(self, project, ip, deliverable, bom):
        repo_name = ''
        if bom.startswith('snap-'):
            repo_name = bom.removeprefix('snap-')
        elif bom.startswith('REL'):
            repo_name = os.path.basename((self.icm.get_release_details(project, ip, deliverable, '*', bom))['IP_MODEL'])

        ip_model = f'{os.environ.get("IP_MODELS")}/release/{ip}/{repo_name}'
        return ip_model

    def get_cthfe_reltag_from_febe_bom(self, project, ip, bom):
        cthfe_reltag = self.icm.get_release_details(project, ip, 'febe', '*', bom)['CTHFE_RELTAG']
        return cthfe_reltag 

    def create_ip_deliverable_directory_and_symlink(self, ip, deliverable, ip_model):
        make_directory_cmd = f'mkdir -p {ip}'
        symlink_cmd = f'ln -s {ip_model} {ip}/{deliverable}'
        full_cmd = f'{make_directory_cmd}; {symlink_cmd}'
        self.logger.debug(f'Run: {full_cmd}')
        os.system(full_cmd)

    def run_hier_population(self):
        # Get all cthfebom
        # for each cthfe bom
        #   create ip directory and cthfe directory
        #   symlink ip_models

        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        hier_git_boms = self.icm.get_deliverable_bom(self.project, self.ip, self.bom, 'cthfe', hier=True)
        for git_bom in hier_git_boms:
            project = git_bom.project
            ip = git_bom.variant
            deliverable = git_bom.libtype
            bom_of_git = git_bom.name
            ip_model = self.get_ip_models(project, ip, deliverable, bom_of_git)
            self.logger.info(f'Linking {ip_model} to {ip}/cthfe')
            self.create_ip_deliverable_directory_and_symlink(ip, 'cthfe', ip_model)

        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))
        

    def run_mapping_file(self):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        default_mapping = f"{os.environ.get('DMXDATA_ROOT', '/p/psg/flows/commond/dmxdata/latestdev')}/{os.environ.get('DB_FAMILY')}/ws_hook/cth_to_psg_mapping.csh"
        mapping_file = os.environ.get('DMX_MAPPING_FILE_FOR_PSAS', f"{default_mapping}") 
        self.logger.info(f"Running: tcsh {mapping_file}")
        ret = os.system(f'tcsh {mapping_file}')
        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))

    def precheck(self):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))

        # common precheck
        pc = cmx.utillib.precheck.Precheck()
        pc.is_workarea_defined()
        pc.is_config_exists(self.project, self.ip, self.bom)
        if not self.force:
            pc.is_workarea_empty()
            if not pc.is_workarea_empty and self.deliverable == 'cthfe':
                pc.errlist.append("$WORKAREA is a git workspace.")

        if self.hier:
            self.cthenv = pc.is_cheetah_env(['FE', 'R2G', 'IPDE'])
            pc.is_bom_immutable(self.bom)
        else:
            # common for cthfe/ipde/r2g
            pc.is_deliverable_exists(self.project, self.ip, self.bom, self.deliverable)

        if self.deliverable == 'cthfe':
            self.cthenv = pc.is_cheetah_env(['FE'])

        if self.deliverable == 'febe':
            pc.is_deliverable_bom_immutable(self.project, self.ip, self.bom, 'febe')
            self.cthenv = pc.is_cheetah_env(['R2G', 'IPDE'])

        if self.deliverable == 'r2g' or self.deliverable == 'ipde':
            #if self.icm.get_deliverable_bom(self.project, self.ip, self.bom, 'febe'):
            #    pc.is_deliverable_bom_immutable(self.project, self.ip, self.bom, 'febe')
            self.cthenv = pc.is_cheetah_env([self.deliverable])

        pc.report()
        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))
        

    def run_git_population(self):
        git_bom = self.icm.get_deliverable_bom(self.project, self.ip, self.bom, self.deliverable, hier=False)[0].name
        ip_model = self.get_ip_models(self.project, self.ip, self.deliverable, git_bom)
        self.create_git_workspace(ip_model, git_bom)


    def run_febe_population(self, env):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        febe_bom = self.icm.get_deliverable_bom(self.project, self.ip, self.bom, 'febe', hier=False)[0].name
        cthfe_reltag = self.get_cthfe_reltag_from_febe_bom(self.project, self.ip, febe_bom)
        ip_model = self.get_ip_models(self.project, self.ip, 'cthfe', cthfe_reltag)

        cfgdir = f"{ip_model}/cfg"
        dutdata = cmx.tnrlib.utils.get_duts_data(cfgdir)
        cells = dutdata.keys()

        dm = DMFactory().create_dm(env, ['fe_collateral'])
        dm.sync(self.project, self.ip, febe_bom, cells)
        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))

        
    def run(self):
        '''
        Here is the flow of workspace population:
    
        Users runs:
        > dmx workspace popoulate -p i18asockm -i avmm_lib -b REL1.0KM2revA0__23ww301a [--hier]

        1. Precheck

        2. if self.hier detected:
                run_hier_population    
                - get all cthfe bom i16asockm/avmm_lib@REL1.0KM2revA0__23ww301a
                - for each project/ip@cthfebom:
                    get IP_MODEL from project/ip:cthfe@bom
                    /create directory $WORKAREA/ip
                    symlink IP_MODEL to cthfe directory in $WORKAREA/ip
      
        3. if -d cthfe: 
            run_git_population()
            if cthfe@immutable bom:
                rsync from IP_MODEL
            elif cthfe@mutable bom:
                git clone from repo
                 
        4. if -d febe
            run_febe_population()
            - get rel_tag from febe bom
                get all duts from ip_model 
                for each dut in all_duts:
                    sync dut/fe_collateral/REL

        5. if -d r2g
            - run_febe_population() if febe@bom exists
            - run_arc_population
                arc populate ip/r2gbomcfg/dev
                get design.cfg from $WORKAREA/<cfgdir>/
                
            - run_dm_population
                read design.cfg 
                for all_duts in design.cfg:
                    sync based on cfg using eouMGR

        Temporary disable moab and r2g/ipde sync
        self.run_moab(self.project, self.ip, self.bom)
        ret = self.run_pop(self.project, self.ip, self.bom)
        '''
        ret = 0

        if self.hier is True:
            self.run_hier_population()
            self.run_mapping_file()
            ret = 0

        elif self.deliverable == 'cthfe':
            self.run_git_population()

        elif self.deliverable == 'febe':
            self.run_febe_population(self.cthenv)

        elif self.deliverable == 'r2g' or self.deliverable == 'ipde':
            #is_febe_bom_exists = self.icm.get_deliverable_bom(self.project, self.ip, self.bom, 'febe', hier=False)
            #if is_febe_bom_exists:
            #    self.logger.info('FEBE bom exists.')
            #    self.run_febe_population(self.deliverable)

            scm = cmx.abnrlib.flows.scmco.ScmCo(None, None, self.deliverable, self.preview, False)
            scm.run_arc_population()
            scm.run_dm_population(self.deliverable)
            


        return ret


