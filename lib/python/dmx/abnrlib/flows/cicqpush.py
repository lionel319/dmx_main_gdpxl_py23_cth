#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/cicqpush.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "abnr clonconfigs"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import sys
import os
import logging
import textwrap
from pprint import pprint

import dmx.abnrlib.config_factory
import dmx.abnrlib.icm
import dmx.abnrlib.flows.overlaydeliverables
import dmx.abnrlib.flows.overlayvariant


class CicqPushError(Exception): pass

class CicqPush(object):
    '''
    Runner class for abnr cloneconfigs
    '''
    def __init__(self, project, variant, config, deliverables=None, hier=False, thread='', preview=True, wait=False, dstconfig=None, filespec=None):
        self.filespec = filespec 
        self.project = project
        self.variant = variant
        self.config = config
        self.deliverables = deliverables
        self.suffix = thread
        self.hier = hier
        self.preview = preview
        self.wait = wait
        self.dstconfig = dstconfig
        self.logger = logging.getLogger(__name__)
        self.icm = dmx.abnrlib.icm.ICManageCLI()
        self.desc = 'dmx cicq pushed from {}/{}@{}. '.format(self.project, self.variant, self.config)

        ### Cicq Backend Boms
        self.lz = 'landing_zone'    ### Default dstconfig.
        if self.dstconfig:
            self.lz = self.dstconfig
        if self.suffix:
            self.lz = self.lz + '_' + self.suffix
        self.logger.debug("self.lz: {}".format(self.lz))


    def run(self):
        '''
        Executes the abnr cloneconfigs command
        :return: 0 == success, non-zero == failure
        :type return: int
        '''
        ret = 1

        ### Todolist in the input for overlaydeliverables.py, and formatted like this
        ### [ [project, variant, libtype, lib-src-config, lib-dst-config], ... ]
        todolist = []
        
        self.cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, self.config)

        if not self.deliverables:

            if not self.hier:
                ### Overlay all deliverables in this variant
                for c in self.cf.configurations:
                    if not c.is_config():
                        todolist = self._add_to_todolist_if_mutable(c, todolist, self.lz)
            else:
                ### Overlay all deliverables throughout the entire tree
                for c in self.cf.flatten_tree():
                    if not c.is_config():
                        todolist = self._add_to_todolist_if_mutable(c, todolist, self.lz)

        else:   

            for libtype in self.deliverables:

                if not self.hier:
                    ### Overlay specified deliverables of top IP
                    for c in self.cf.search('^{}$'.format(self.project), "^{}$".format(self.variant),
                        "^{}$".format(libtype)):
                        todolist = self._add_to_todolist_if_mutable(c, todolist, self.lz)
                else:
                    ### overlay specified deliverables throughout the entire tree
                    for c in self.cf.search(".*", ".*", "^{}$".format(libtype)):
                        todolist = self._add_to_todolist_if_mutable(c, todolist, self.lz)

        ### make sure ipspec + reldoc are not in ipspec/*.unneeded_deliverables.txt
        ### https://jira.devtools.intel.com/browse/PSGDMX-3030
        for project, variant, libtype, srclibrary, destlibrary in todolist:
            if libtype == 'ipspec':
                unneeded = self.icm.get_unneeded_deliverables(project, variant, library=srclibrary)
                
                ### Remove commented unneeded deliverables, and lowercase it
                real_unneeded = [x.lower() for x in unneeded if not x.startswith(("#", "//"))]

                ### Compulsory deliverables
                errcount = 0
                needed = ['ipspec', 'reldoc']
                for n in needed:
                    if n in real_unneeded:
                        errmsg = """
                        {} found in one of the ipspec/*.unneeded_deliverables.txt in {}. 
                        {} is a compulsory deliverables and can not be defined in any ipspec/*.unnneded_deliverables.txt
                        """.format(n, [project, variant, libtype, srclibrary], n)
                        self.logger.error(errmsg)
                        errcount += 1
        if errcount:
            return 1


        ### if filespec, only need to overlay those delvierable that the filespec is in
        if self.filespec:
            todolist = dmx.abnrlib.flows.overlayvariant.OverlayVariant.get_filespec_todolist_only(todolist, self.filespec)

        od = dmx.abnrlib.flows.overlaydeliverables.OverlayDeliverables(todolist, self.project, self.variant, self.lz, preview=self.preview, wait=self.wait, forcerevert=True, filespec=self.filespec) 
        ret = od.run()
        if self.preview:
            return 0

        ### If fail, try 3 times before conceding failure.
        ### https://jira.devtools.intel.com/browse/PSGDMX-1719
        if ret != 0:
            trycount = 5
            for i in range(2, trycount+1):
                self.logger.info("Previous cicqpush job did not complete successfully. Trying again {}-th time ...".format(i))
                od = dmx.abnrlib.flows.overlaydeliverables.OverlayDeliverables(todolist, self.project, self.variant, self.lz, preview=False, wait=self.wait, forcerevert=True, filespec=self.filespec) 
                ret = od.run()
                if ret == 0:
                    break

        return ret


    def _add_to_todolist_if_mutable(self, simple_config_obj, todolist, dstbom):
        if simple_config_obj.is_mutable():
            todolist.append( [simple_config_obj.project, simple_config_obj.variant, simple_config_obj.libtype, simple_config_obj.library, dstbom] )
        else:
            self.logger.debug("Skipped cicqpush immutable source: {}/{}:{}@{}".format(
                simple_config_obj.project, simple_config_obj.variant, simple_config_obj.libtype, simple_config_obj.release))
        return todolist


