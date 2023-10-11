#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/cloneconfigsemptybranch.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "abnr clonconfigs"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import sys
import logging
import textwrap

import dmx.abnrlib.config_factory
from dmx.abnrlib.icm import ICManageCLI


class CloneConfigsEmptyBranchError(Exception): pass

class CloneConfigsEmptyBranch(object):
    '''
    Runner class for abnr cloneconfigs
    '''
    def __init__(self, project, variant, srcconfig, dstconfig, libtype=None, preview=False):
        
        self.project = project
        self.variant = variant
        self.libtype = libtype
        self.preview = preview
        self.dstconfig = dstconfig
        self.srcconfig = srcconfig
        self.logger = logging.getLogger(__name__)
        self.icm = ICManageCLI(preview=self.preview)
        self.desc = 'branched thru (dmx bom clone)'
        


    def run(self):
        '''
        Executes the abnr cloneconfigs command
        :return: 0 == success, non-zero == failure
        :type return: int
        '''
        ret = 1
        self.logger.debug("libtype:{}".format(self.libtype))
        
        ### LIBTYPE level 
        if self.libtype:
            dup_add_libraries = self.icm.add_libraries(self.project, self.variant, [self.libtype], self.dstconfig, self.desc)
            #dup_add_configs = self.icm.add_libtype_configs(self.project, self.variant, [self.libtype], self.dstconfig, '#dev', self.dstconfig)

        ### VARIANT level
        else:
            cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, self.srcconfig, None, preview=self.preview)
            self.logger.debug("ConfigFactory of srcconfig: {}".format(cf))
            
            ### This part make all the preparation
            ### - create all the new libtypes library
            ### - create all the new libtypes config
            for x in cf.flatten_tree():
                if not x.is_config():
                    dup_add_libraries = self.icm.add_libraries(x.project, x.variant, [x.libtype], self.dstconfig, self.desc)
                    #dup_add_configs = self.icm.add_libtype_configs(x.project, x.variant, [x.libtype], self.dstconfig, '#dev', self.dstconfig)
            
            self.newcf = cf.clone_tree(self.dstconfig, clone_simple=True, clone_immutable=True, reuse_existing_config=True)

            if not self.preview:
                self.logger.info("Saving Cloned Tree Configuration ...")
                self.newcf.save()
            else:
                self.logger.info("Cloned Tree Configuration Not Saved in preview-mode.")

        ret = 0

        return ret
