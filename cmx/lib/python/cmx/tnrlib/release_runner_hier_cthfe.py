#!/usr/bin/env python

import os
import sys
import json
from pprint import pprint, pformat
import textwrap
import logging
import inspect
import json
import time
import re
import tempfile

CMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, os.getenv("DMXLIB"))
sys.path.insert(0, os.getenv("CMXLIB"))

import cmx.utillib.utils
from cmx.tnrlib.test_runner_view import TestRunnerView
import cmx.tnrlib.test_runner_factory
import dmx.abnrlib.config_factory
import dmx.abnrlib.icm
from cmx.tnrlib.release_runner_base import ReleaseRunnerBase
from cmx.tnrlib.release_runner_cthfe import ReleaseRunnerCthfe
import dmx.abnrlib.icmconfig
import dmx.abnrlib.config_factory

class ReleaseRunnerHierCthfe(ReleaseRunnerBase):
    
    def __init__(self, thread, milestone, deliverable, project, ip, bom, label=None, views=None, skipmscheck=None, prel=None, syncpoint=None, skipsyncpoint=None, workarea=None, dryrun=False):
        super().__init__(thread, milestone, deliverable, project, ip, bom, label=label, views=views, skipmscheck=skipmscheck, prel=prel, syncpoint=syncpoint, skipsyncpoint=skipsyncpoint, workarea=workarea, dryrun=dryrun)
        self.logger = logging.getLogger(__name__)
        self.workarea = workarea
        if not self.workarea:
            self.workarea = self.get_workarea()
        self.thread = thread
        self.milestone = milestone
        self.deliverable = deliverable
        self.project = project
        self.ip = ip
        self.bom = bom  # This is the ip-bom
        self.staging_bomname = None     # this is the bom that is used to create the workspace, which is cloned from self.bom, and had its cthfe bom replaced
        self.label = label
        self.views = views
        self.skipmscheck = skipmscheck
        self.prel = prel
        self.syncpoint = syncpoint
        self.skipsyncpoint = skipsyncpoint
        self.dryrun = dryrun
        self.staging_workarea = self.get_staging_workarea()
        self.cfobj = None
        self.required_deliverables = None

        self.release_model_path = None


    def find_pvlc_from_release_model(self, release_model):
        retkeys = ['project:parent:name', 'variant:parent:name', 'libtype:parent:name', 'name']
        retlist = ReleaseRunnerCthfe(None, None, None, None, None, None).find_mapping_reltag(release_model, retkeys=retkeys)
        return retlist

    def get_release_model_path(self):
        if not self.release_model_path:
            key = 'IP_MODEL'
            ret = dmx.abnrlib.icm.ICManageCLI().get_release_details(self.project, self.ip, 'cthfe', '*', self.bom)
            if ret and key in ret:
                self.release_model_path = ret[key]
            else:
                self.release_model_path = None
        self.logger.debug("release_model_path: {}".format(self.release_model_path))
        return self.release_model_path


    def run(self):
        ''' Here's the flow of releasing CTHFE.

        User runs
        > dmx release -p i18asockm -i liotest1 -d hier_cthfe -b REL1.0KM2revA0__23ww332a -t KM2revA0 -m 1.0

        1. Precheck (refer to the method's docs for detail)

        2. Create hierarchical REL, by ...
            create toplevel@REL
            for subip in all_subips:
                create subip@REL
                --add subip:cthfe@REL into subip@REL
                --add subip@REL into toplevel@REL  

        '''

        self.precheck()

        self.generate_rel_configs()
        
        error = self.run_posthooks()
        if error:
            return error

        
        self.logger.info("=THE END=")
        return 0

 
    def precheck(self):
        '''
        - $WORKAREA env var is defined
        - i18asockm/liotest1:cthfe@REL1.0KM2revA0__23ww332a exist
        - $WORKAREA/subip/sip and hip are all symlinked to $IP_MODEL area, 
            > symlinks are statis release (not *-latest)
            > all symlinked gk-release must have corresponding icm-RELTAG
        '''
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))
        errlist = []
        if not os.getenv("WORKAREA"):
            errlist.append("$WORKAREA env var not defined.")
     
        if not self.bom.startswith("REL"):
            raise Exception("-b has to be a released(REL*) cthfe bom for {}/{}".format(self.project, self.ip))

        if not dmx.abnrlib.icm.ICManageCLI().config_exists(self.project, self.ip, self.bom, 'cthfe'):
            raise Exception("Can not find existing object from database: {}/{}:{}@{}".format(self.project, self.ip, 'cthfe', self.bom))

        if not self.get_release_model_path():
            errlist.append("Can't find gk-release-model for {}/{}:cthfe@{}".format(self.project, self.ip, self.bom))

        errors = self.is_release_model_subip_all_symlinked_to_official_area()
        if errors:
            errlist.append("These subip from {} contains symlink from non-official path.\n {}".format(self.release_model_path, errors))

        errors = self.is_all_subip_having_mapping_icm_reltag()
        if errors:
            errlist.append("These subip from {} has no corresponding icm-reltag.\n {}".format(self.release_model_path, errors))
        self.logger.info("mapping_reltags: {}".format(self.mapping_reltags))

        if errlist:
            msg = "  - FAIL: precheck. Please check the errors below."
            for e in errlist:
                msg += e + "\n"
            self.logger.error(msg)
            raise Exception("FAIL: precheck")

        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))

    def is_all_subip_having_mapping_icm_reltag(self):
        ret = {}
        errors = []

        ### XXX: This is meant for negative testing
        #self.subip_files['sip'].append('/nfs/site/disks/psg.mod.001/GK4/release/spc_top/spc_top-a0-23ww27a')

        for key in self.subip_files:
            for symlink in self.subip_files[key]:
                data = self.find_pvlc_from_release_model(os.path.basename(symlink))
                if not data:
                    errors.append(symlink)
                else:
                    ret[symlink] = data
        self.mapping_reltags = ret
        return errors


    def is_release_model_subip_all_symlinked_to_official_area(self):
        ''' Check if all subip/* files are symlinked from official IP_MODEL path.
        if yes (pass):
            return []
        else: (fail)
            return [list_of_errors]
        '''
        goldenpath = 'nfs/site/disks/psg.mod.00'
        data = self.get_all_subip_symlinks_from_release_model()
        pprint(data)
        errors = [] 
        for key in data.keys():
            for symlink in data[key]:
                if symlink.startswith(goldenpath):
                    errors.append(data[key])
        return errors


    def get_all_subip_symlinks_from_release_model(self):
        '''
        self.subip_files = {
            'hip': ['/nfs/site/disks/psg.mod.001/GK4/release/bypass_reg/bypass_reg-a0-23ww27b'],
            'sip': ['/nfs/site/disks/psg.mod.001/GK4/release/bypass_pnr_reg/bypass_pnr_reg-a0-23ww27a']
        }
        '''
        ret = {'hip': [], 'sip':[]}
        relmodpath = self.get_release_model_path()
        subipdir = os.path.join(relmodpath, 'subip')
        for key in ret.keys():
            outdir = os.path.join(subipdir, key)

            ### Convert them to fullpath
            for filename in os.listdir(outdir):
                ret[key].append(os.path.realpath(os.path.join(outdir, filename)))
        self.subip_files = ret
        return self.subip_files


    def create_staging_bom(self):
        '''
        staging_bomname = _for_tnr_variant_<user>_<atime>
        1. clone project/ip@bom -> project/ip@staging_Bom
        2. replace project/ip:cthfe@bom -> project/ip:cthfe@release_model_icm_bom
        '''
        self.staging_bomname = '_for_tnr_variant_{}_{}'.format(os.getenv("USER"), int(time.time()))
        cf = self.get_config_factory_obj()
        newcf = cf.clone(self.staging_bomname)
        
        ### Removed all libtypes which are not required
        required_deliverable_names = [x.name for x in self.get_required_deliverables()]
        tobe_removed = []
        for c in newcf.configurations:
            if not c.is_config():
                if c.libtype not in required_deliverable_names:
                    tobe_removed.append(c)

        for c in tobe_removed:
            newcf.remove_object(c)

        self.logger.debug(newcf.report())

        newcf.save()
        self.staging_bom_obj = newcf

        return self.staging_bomname



    def generate_rel_configs(self):
        self.logger.info("-Running-: {}".format(inspect.currentframe().f_code.co_name))

        ### list of sub-ips that are created, which eventually needs to be inserted into top-ip bom
        ### subips = [ IcmConfig_obj1, IcmConfig_obj2, ... ... ... ]
        subip_objs = [] 


        ### generate sub-ip variant REL
        for rel_model_path in self.mapping_reltags:


            for data in self.mapping_reltags[rel_model_path]:
                project = data['project:parent:name']
                variant = data['variant:parent:name']
                libtype = data['libtype:parent:name']
                config  = data['name']
            
                ### Lionel Noticed that at certain situation, the subip/ contains symlink to it's own cthfe
                ### (ie: avmm_lib/subip/sip contains a symlink to it's own avmm_lib)
                ### (Example: refer to /nfs/site/disks/psg.mod.001/GK4/release/avmm_lib/avmm_lib-a0-23ww35h/subip)
                ### Thus, we workaround it by skipping this.
                if variant == self.ip:
                    continue


                ### The cthfe libtype REL should already exist. Thus, we get it from ICM
                cthfe_bom = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(project, variant, config, libtype)

                ### This is the subip Variant-bom(REL) that needs to be created
                relname = ReleaseRunnerBase(self.thread, self.milestone, None, project, variant, 'dev').get_rel_name()
                self.logger.info("-- {}/{}@{}".format(project, variant, relname))
                subipobj = dmx.abnrlib.icmconfig.IcmConfig(relname, project, variant, [cthfe_bom])
                subip_objs.append(subipobj)

        ### generate top-ip variant REL
        # the self.deliverable was 'hier_cthfe'. When it tries to get_rel_name(), it couldn't find the correct REL name.
        # thus, we need to temporary hack/change the self.deliverable to None, to get the correct abc... suffix of the REL name.
        ori_deliverable = self.deliverable
        self.deliverable = None
        relname = self.get_rel_name()
        self.deliverable = ori_deliverable

        top_cthfe_obj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.ip, self.bom, 'cthfe')
        subip_and_top_cthfe_objs = subip_objs + [top_cthfe_obj]

        self.logger.info("-- {}/{}@{}".format(self.project, self.ip, relname))
        top_ip_bom_obj = dmx.abnrlib.icmconfig.IcmConfig(relname, self.project, self.ip, subip_and_top_cthfe_objs)

        self.logger.info("This will be the hierarchy that will be generated:\n{}".format(top_ip_bom_obj.report()))
       
        if self.dryrun:
            self.logger.info("DRYRUN: {}. Skipping saving the final configuration. Hierarchy not generated.".format(self.dryrun))
            return 0
        else:
            self.logger.info("Saving hierarchy configuration ...")
            top_ip_bom_obj.save()
            self.logger.info("Successfully saved: {}".format(top_ip_bom_obj))


        self.logger.info("-Complete-: {}".format(inspect.currentframe().f_code.co_name))
