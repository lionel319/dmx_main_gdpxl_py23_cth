#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/overlayvariant.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: plugin for "abnr clonconfigs"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import sys
import re
import os
import logging
import textwrap
from pprint import pprint

import dmx.abnrlib.config_factory
import dmx.abnrlib.icm
import dmx.abnrlib.flows.overlaydeliverables


class OverlayVariantError(Exception): pass

class OverlayVariant(object):
    '''
    Runner class for abnr cloneconfigs
    '''
    def __init__(self, project, variant, srcconfig, dstconfig, deliverables=None, hier=False, cells=None, directory=None, preview=True, desc='', wait=False, forcerevert=False, filespec=None):
        self.filespec = filespec 
        self.project = project
        self.variant = variant
        self.srcconfig = srcconfig
        self.dstconfig = dstconfig
        self.deliverables = deliverables
        self.hier = hier
        self.cells = cells
        self.directory = directory
        self.preview = preview
        self.wait = wait
        self.forcerevert = forcerevert
        self.logger = logging.getLogger(__name__)
        self.icm = dmx.abnrlib.icm.ICManageCLI()
        self.desc = 'dmx overlayvariant from {}/{}@{}. {}'.format(self.project, self.variant, self.srcconfig, desc)

    @classmethod
    def get_filespec_todolist_only(self, todolist, filespec):
        data = {}
        filespec_todolist = []
        for ea_filespec in filespec:
            ea_files = ea_filespec.split('/') 
            match = re.search('(\S+)/(\S+)/(\S+)', ea_filespec)
            if match:
                ip = match.group(1) 
                deliverable = match.group(2) 
                data[ip, deliverable] = 'True' 
            else:
                raise Exception('Filespec \'{}\' does not match format ip/deliverable/files. Skip'.format(ea_filespec))
             
        for project, variant, libtype, source, dest in todolist:
            if data.get((variant, libtype)) == 'True':
                filespec_todolist.append(( project, variant, libtype, source, dest))
        
        return filespec_todolist 

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
        
        self.cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, self.srcconfig)

        if not self.deliverables:

            if not self.hier:
                ### Overlay all deliverables in this variant
                for c in self.cf.configurations:
                    if not c.is_config():
                        if c._type == 'library':
                            todolist.append( [c.project, c.variant, c.libtype, c.library, self.dstconfig] )
                        else:
                            todolist.append( [c.project, c.variant, c.libtype, c.lib_release, self.dstconfig] )

            else:
                ### Overlay all deliverables throughout the entire tree
                for c in self.cf.flatten_tree():
                    if not c.is_config():
                        if c._type == 'library':
                            todolist.append( [c.project, c.variant, c.libtype, c.library, self.dstconfig] )
                        else:
                            todolist.append( [c.project, c.variant, c.libtype, c.lib_release, self.dstconfig] )

        else:   

            for libtype in self.deliverables:

                if not self.hier:
                    ### Overlay specified deliverables of top IP
                    for c in self.cf.search('^{}$'.format(self.project), "^{}$".format(self.variant),
                        "^{}$".format(libtype)):
                        if c._type == 'library':
                            todolist.append( [c.project, c.variant, c.libtype, c.library, self.dstconfig] )
                        else:
                            todolist.append( [c.project, c.variant, c.libtype, c.lib_release, self.dstconfig] )

                else:
                    ### overlay specified deliverables throughout the entire tree
                    for c in self.cf.search(".*", ".*", "^{}$".format(libtype)):
                        if c._type == 'library':
                            todolist.append( [c.project, c.variant, c.libtype, c.library, self.dstconfig] )
                        else:
                            todolist.append( [c.project, c.variant, c.libtype, c.lib_release, self.dstconfig] )

        ### if filespec, only need to overlay those delvierable that the filespec is in
        if self.filespec:
            todolist = self.get_filespec_todolist_only(todolist, self.filespec)

        od = dmx.abnrlib.flows.overlaydeliverables.OverlayDeliverables(todolist, self.project, self.variant, self.dstconfig, cells=self.cells, 
            directory=self.directory, preview=self.preview, desc=self.desc, wait=self.wait, forcerevert=self.forcerevert, filespec=self.filespec) 
        ret = od.run()

        return ret

