#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/bomupdate.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "abnr bom"

Author: Rudy Albachten
Copyright (c) Altera Corporation 2013
All rights reserved.
'''
from __future__ import print_function
from builtins import object
import sys
import os
import logging
import textwrap
import multiprocessing
import re
import tempfile

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(0, LIB)

import dmx.abnrlib.icmconfig
import dmx.abnrlib.config_factory
import dmx.abnrlib.icm
import dmx.syncpointlib.syncpoint_webapi
import dmx.abnrlib.flows.checkconfigs
import dmx.utillib.utils

class BomUpdateError(Exception): pass

class BomUpdate(object):
    '''
    Runs the abnr bom command
    '''
    def __init__(self, project, variant, config, syncpoint, newbom=False, preview=False, cfgfile=None):
        self.project = project
        self.variant = variant
        self.config = config
        self.syncpoint = syncpoint
        self.preview = preview
        self.newbom = newbom
        self.logger = logging.getLogger(__name__)
        self.cfgfile = cfgfile

    def read_cfgfile(self):
        result = []
        for line in open(self.cfgfile):
            line = line.rstrip()
            match = re.search('(\S+)\/(\S+):(\S+)@(remove|delete|\S+)', line)
            if not match:
                raise BomUpdateError('\'{}\' does not match expected format, make sure you follow this format $PROJECT/$IP:$DELIVERABLE@<$BOM|remove|delete>'.format(line))
            result.append(line)
        return result

    def get_flatten_configfile_dict(self, cfgfile_info):
        datadict = {} 
        line_num = {}
        for i, ea_cfg in enumerate(cfgfile_info):
            i = i + 1
            project, ip, deliverable, bom = self.split_pvc_in_config(ea_cfg)
            if not datadict.get((project, ip)):
                datadict[project, ip] = {}
                datadict[project, ip][deliverable] = bom 
            else:
                if datadict[project, ip].get(deliverable):
                    raise BomUpdateError('{7}: {0}/{1}:{2}@{3} (line {5}) conflicts with {0}/{1}:{2}@{4} (line {6}). A unique entry for {0}/{1}:{2} is expected.'.format(project, ip, deliverable, datadict[project, ip].get(deliverable), bom, line_num.get((project, ip, deliverable, bom), 1), i, self.cfgfile))
                datadict[project, ip][deliverable] = bom 
                line_num[project, ip, deliverable, bom] = i

        return datadict 


    def split_pvc_in_config(self, cfg):
        match = re.search('(\S+)\/(\S+):(\S+)@(remove|delete|\S+)', cfg)
        project = match.group(1)
        ip = match.group(2)
        deliverable = match.group(3)
        bom = match.group(4)
        return project, ip, deliverable, bom



    def get_flatten_root_dict(self):
        datadict = {}
        flatten_root = dmx.abnrlib.icm.ICManageCLI().get_flattened_config_details(self.project, self.variant, self.config, retkeys=['path'])
        for ea_flatten_cfg in flatten_root:
            match = re.search('/intel/(\S+)/(\S+)/(\S+)/(\S+)', ea_flatten_cfg)
            if not match: continue
            project = match.group(1)
            ip = match.group(2)
            deliverable = match.group(3)
            config = match.group(1)
            #project = ea_flatten_cfg['project']
            #ip = ea_flatten_cfg['variant']
            #deliverable = ea_flatten_cfg['libtype']
            #config = ea_flatten_cfg['config']
            if not datadict.get((project, ip)):
                datadict[project, ip] = {}
                datadict[project, ip][deliverable] = config
            else:
                datadict[project, ip][deliverable] = config

        return datadict
    
       # flatten_root_config = [x.get_full_name() for x in root_config.flatten_tree() if x.is_simple()]
       ## need_update_cfgs = set(cfg_obj) - set(flatten_root_config) 
       # print need_update_cfgs

    def get_bom_edit_file(self, cfgfile_dict, rootcfg_dict):
        fd, path = tempfile.mkstemp(prefix='dmx_bom_update')
        fo = open(path, 'w+')
        for cfgfile_key, cfcgfiledeliverable_dict in list(cfgfile_dict.items()):
            for cfgfiledeliverable, cfgfilebom in list(cfcgfiledeliverable_dict.items()):

                # Do nothing as it is same pvc
                if rootcfg_dict.get(cfgfile_key) and rootcfg_dict.get(cfgfile_key).get(cfgfiledeliverable) == cfgfilebom: continue
                # if contain remove/delete, check the bom exists in rootconfig, if no, prompt error
                elif cfgfilebom == 'remove' or  cfgfilebom == 'delete':
                    if rootcfg_dict.get(cfgfile_key).get(cfgfiledeliverable):
                        fo.write('--delbom {}/{}:{}\n'.format(cfgfile_key[0], cfgfile_key[1], cfgfiledeliverable))
                    else:
                        raise BomUpdateError('Cannot remove bom {}/{}:{}. Bom does not exists in {}/{}@{}.'.format(cfgfile_key[0], cfgfile_key[1], cfgfiledeliverable, self.project, self.variant, self.config))

                elif dmx.abnrlib.icm.ICManageCLI().config_exists(cfgfile_key[0], cfgfile_key[1], libtype=cfgfiledeliverable, config=cfgfilebom):
                    # if contain bom exist and is not equal with root boom, replace the bom
                    if rootcfg_dict.get(cfgfile_key) and rootcfg_dict.get(cfgfile_key).get(cfgfiledeliverable) != None and rootcfg_dict.get(cfgfile_key).get(cfgfiledeliverable) != cfgfilebom:
                        fo.write('--repbom {}/{}:{} {}\n'.format(cfgfile_key[0], cfgfile_key[1], cfgfiledeliverable, cfgfilebom))
                    elif rootcfg_dict.get(cfgfile_key) and rootcfg_dict.get(cfgfile_key).get(cfgfiledeliverable) is None:
                            fo.write('--addbom {}/{}:{}@{}\n'.format(cfgfile_key[0], cfgfile_key[1], cfgfiledeliverable, cfgfilebom))
                    elif rootcfg_dict.get(cfgfile_key) is None:
                        raise BomUpdateError('{}/{}:{}@{} does not exists in {}/{}@{}. Please check your config file.'.format(cfgfile_key[0], cfgfile_key[1], cfgfiledeliverable, cfgfilebom, self.project, self.variant, self.config))
                else:
                    raise BomUpdateError('{}/{}:{}@{} does not exists. Please check your config file.'.format(cfgfile_key[0], cfgfile_key[1], cfgfiledeliverable, cfgfilebom))
        fo.close()
        return path
 
    def get_bom_edit_file_2(self, root_config, cfg_obj):
        fd, path = tempfile.mkstemp(prefix='dmx_bom_update')
        fo = open(path, 'w+')

        flatten_root_config = [x for x in root_config.flatten_tree() if x.is_library()]
        need_update_cfgs = set(cfg_obj) - set(flatten_root_config) 
        for ea_need_update_cfg in need_update_cfgs:
            if isinstance(ea_need_update_cfg, dmx.abnrlib.icmconfig.IcmConfig): continue
            for ea_flatten_root_config in flatten_root_config:
                if ea_flatten_root_config.project == ea_need_update_cfg.project and ea_flatten_root_config.variant == ea_need_update_cfg.variant and ea_flatten_root_config.libtype == ea_need_update_cfg.libtype:
                    fo.write('--repbom {}/{}:{} {}'.format(ea_need_update_cfg.project, ea_flatten_root_config.variant, ea_flatten_root_config.libtype, ea_flatten_root_config.config))

            if 'delete' in ea_need_update_cfg or 'remove' in ea_need_update_cfg:
                project, ip, deliverable, bom = self.split_pvc_in_config(ea_need_update_cfg)
                fo.write('--delbom {}/{}:{}'.format(project, ip, deliverable))
        print(path)


    def update(self):
        cfgfile_info = self.read_cfgfile()
        root_config = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, self.config)
        cfgfile_dict = self.get_flatten_configfile_dict(cfgfile_info)
        rootcfg_dict = self.get_flatten_root_dict()
        
        dmx_bom_edit_file = self.get_bom_edit_file(cfgfile_dict, rootcfg_dict)
        self.logger.info('DMX bom edit file: {}'.format(os.path.abspath(dmx_bom_edit_file)))
        command = 'dmx bom edit -p {} -i {} -b {} --inplace --file {}'.format(self.project, self.variant, self.config, dmx_bom_edit_file)
        self.logger.info('Running: {}'.format(command))
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(command)
        print(stderr.rstrip())
            #self.logger.info('Bom {}/{}:{} updated. '.format(self.project, self,variant, self.config)) 
        #cfgobj = self.get_configuration_object(cfgfile_info)
        #root_config = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, self.config)
        #self.get_bom_edit_file(root_config, cfgobj)

    def run(self):
        if self.preview:
            self.logger.info("Dryrun mode. Nothing to be done!")
            return 0
        
        self.check_conflicts_in_pvc()
        self.check_conflicts_in_syncpoint()

        self.replace_bom()


    def replace_bom(self):
        repboms = self.find_tobe_replaced_boms() 
        self.logger.debug("Boms that need to be replaced: {}".format(repboms))
        if not repboms:
            self.logger.info("There is nothing that needs to be replaced. Aborting.")
            return 0
        et = dmx.abnrlib.flows.edittree.EditTree(self.project, self.variant, self.config, inplace=True, new_config=self.newbom, rep_configs=repboms)
        return et.run()


    def find_tobe_replaced_boms(self):
        retval = []
        cfobj = self.get_config_factory_obj()
        for cf in cfobj.flatten_tree():
            if not cf.is_library() and cf.variant != self.variant:
                syncpointconfig = self.get_rel_config_from_syncpoint(cf.project, cf.variant)
                if syncpointconfig and syncpointconfig != cf.config:
                    retval.append(['{}/{}'.format(cf.project, cf.variant), syncpointconfig])
        return retval


    def get_rel_config_from_syncpoint(self, project, variant):
        spconfigs = self.get_syncpoint_configs()
        for p,v,c in spconfigs:
            if project == p and variant == v:
                return c
        return False


    def check_conflicts_in_pvc(self):
        self.logger.info("Checking for any conflicts in {}/{}@{} ...".format(self.project, self.variant, self.config))
        cfobj = self.get_config_factory_obj()
        problems = cfobj.validate()
        if problems:
            raise BomUpdateError("Conflict found in bom. Please fix it before proceeding.\n{}".format(problems))
        return 0


    def check_conflicts_in_syncpoint(self):
        self.logger.info("Checking for any conflicts in syncpoint:{} ...".format(self.syncpoint))
        cfobj_list = []
        spconfigs = self.get_syncpoint_configs()
        for p,v,c in spconfigs:
            if c:
                cfobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(p, v, c)
                cfobj_list.append(cfobj)
        spccobj = dmx.abnrlib.icmconfig.IcmConfig('dummyconfig', self.project, self.variant, cfobj_list)
        problems = spccobj.validate()
        if problems:
            raise BomUpdateError("Conflict found in syncpoint. Please fix it before proceeding.\n{}".format(problems))
        return 0

    def get_config_factory_obj(self):
        retval = getattr(self, 'cfobj', False)
        if not retval or not self.cfobj:
            retval = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, self.config)
            self.cfobj = retval
        return self.cfobj


    def get_syncpoint_configs(self):
        retval = getattr(self, 'spconfigs', False)
        if not retval or not self.spconfigs:
            spapi = dmx.syncpointlib.syncpoint_webapi.SyncpointWebAPI()
            retval = spapi.get_releases_from_syncpoint(self.syncpoint)
            self.spconfigs = retval
        return self.spconfigs


