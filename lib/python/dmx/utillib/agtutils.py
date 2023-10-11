#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/agtutils.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: useful utils for Automated Generated Tag script
For more details, refer to
- https://jira.devtools.intel.com/browse/PSGDMX-1588
- https://wiki.ith.intel.com/pages/viewpage.action?pageId=1259093795

Author: yoke.liang.tan@intel.com, wei.pin.lim@intel.com

Copyright (c) Intel-PSG Corporation 2019
All rights reserved.
'''

import os
import logging
import sys
import re
from pprint import pprint

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(0, LIB)

import dmx.abnrlib.config_naming_scheme
import dmx.abnrlib.config_factory


LOGGER = logging.getLogger(__name__)

class AgtUtils(object):

    def __init__(self, cache=True):
        pass

    def get_latest_tagname(self, relconfig, with_milestone=True):
        '''
        relconfig = REL1.0FM4revA0__16ww192a

        if with_milestone == True:
            return agt_latest_FM4revA0_1.0
        if with_milestone == False:
            return agt_latest_FM4revA0
        '''
        cns = dmx.abnrlib.config_naming_scheme.ConfigNamingScheme()
        data = cns.get_data_for_release_config(relconfig)
        
        tagname = 'agt_latest_{}'.format(data['thread']+'rev'+data['rev'])
        if with_milestone:
            tagname = tagname + '_{}'.format(data['milestone'])

        return tagname


    def force_clone_libtype_config(self, project, variant, libtype, src_config, dst_config):
        '''
        Given a pvlc,
            force clone the src_config to dst_config, even if the dst_config already exists.
        '''
        libc = dmx.abnrlib.config_factory.ConfigFactory().create_from_icm(project, variant, src_config, libtype)
        LOGGER.debug("Cloning {} to config:{} ...".format(libc, dst_config))
        try:
            ### If dst_config does not exist, clone it
            latest_libc = libc.clone(dst_config)
            LOGGER.debug("cloning {} to {} ...".format(libc, latest_libc))
        except:
            ### if dst_config already exist, then modify it
            latest_libc = dmx.abnrlib.config_factory.ConfigFactory().create_from_icm(project, variant, dst_config, libtype)
            latest_libc.library = libc.library
            latest_libc.lib_release = libc.lib_release
            LOGGER.debug("updating {} with content of {} ...".format(latest_libc, libc))

        latest_libc.description = src_config
        latest_libc.save()
        LOGGER.debug("Successfully force cloned {} to {}".format(libc, latest_libc))


    
    def force_update_variant_config(self, project, variant, libtype, libconfig, varconfig): 
        ''' 
        Given a project/variant:libtype@libconfig
            - create project/variant@varconfig if it does not exist
            - insert project/variant:libtype@libconfig ==> project/variant@varconfig
        '''

        LOGGER.debug("Updating variant for {}/{}:{}@{} ...".format(project, variant, libtype, libconfig))
        latest_libc = dmx.abnrlib.config_factory.ConfigFactory().create_from_icm(project, variant, libconfig, libtype)

        ###############################################################
        ### create variant-latest-config if does not exist
        ###############################################################
        try:
            latest_wrapc = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(project, variant, varconfig)
            LOGGER.debug("variant-config exists: {}".format(latest_wrapc))
        except:
            latest_wrapc = dmx.abnrlib.icmcompositeconfig.CompositeConfig(varconfig, project, variant, [latest_libc])
            LOGGER.debug("variant-config does not exist. Creating {} ...".format(latest_wrapc))

        ### add libconfig to varconfig
        found = latest_wrapc.search(project, variant, libtype)
        if not found:
            latest_wrapc.add_configuration(latest_libc)
            LOGGER.debug("adding {} into {} ...".format(latest_libc, latest_wrapc))
        else:
            old_libc = found[0]
            if old_libc == latest_libc:
                LOGGER.debug("{} already in {}. Nothing needs to be done.".format(latest_libc, latest_wrapc))
            else:
                LOGGER.debug("replacing {} to {} in {} ...".format(old_libc, latest_libc, latest_wrapc))
                latest_wrapc.replace_config_in_tree(old_libc, latest_libc)

        latest_wrapc.save()
        LOGGER.debug("Successfully force update {} in {}".format(latest_libc, latest_wrapc))


    def force_update_wrapper_config(self, wrapproject, wrapvariant, varproject, variant, config): 
        ''' 
        Given a wrapproject/wrapvariant@config
            - create wrapproject/wrapvariant@config if it does not exist
            - insert varproject/variant@config ==> wrapproject/wrapvariant@config
        '''

        LOGGER.debug("Updating variant for {}/{}@{} ...".format(wrapproject, wrapvariant, config))
        latest_libc = dmx.abnrlib.config_factory.ConfigFactory().create_from_icm(varproject, variant, config)

        ###############################################################
        ### create wrapper-latest-config if does not exist
        ###############################################################
        try:
            latest_wrapc = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(wrapproject, wrapvariant, config)
            LOGGER.debug("variant-config exists: {}".format(latest_wrapc))
        except:
            latest_wrapc = dmx.abnrlib.icmcompositeconfig.CompositeConfig(config, wrapproject, wrapvariant, [latest_libc])
            LOGGER.debug("variant-config does not exist. Creating {} ...".format(latest_wrapc))

        ### add libconfig to wrapconfig
        found = latest_wrapc.search(varproject, variant)
        if not found:
            latest_wrapc.add_configuration(latest_libc)
            LOGGER.debug("adding {} into {} ...".format(latest_libc, latest_wrapc))
        else:
            old_libc = found[0]
            if old_libc == latest_libc:
                LOGGER.debug("{} already in {}. Nothing needs to be done.".format(latest_libc, latest_wrapc))
            else:
                LOGGER.debug("replacing {} to {} in {} ...".format(old_libc, latest_libc, latest_wrapc))
                latest_wrapc.replace_config_in_tree(old_libc, latest_libc)

        latest_wrapc.save()
        LOGGER.debug("Successfully force update {} in {}".format(latest_libc, latest_wrapc))



if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)

