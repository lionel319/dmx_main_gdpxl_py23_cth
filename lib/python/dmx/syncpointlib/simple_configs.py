#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/syncpointlib/simple_configs.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Utility classes to read an individual Simple Config

Author: Rudy Albachten
Copyright (c) Altera Corporation 2013
All rights reserved.
'''
from __future__ import print_function
from builtins import str
from builtins import object
import re
import logging

from dmx.utillib.utils import run_command
import dmx.abnrlib.icm

LOGGER = logging.getLogger(__name__)

class Error(Exception): pass 
class ConfigLoadError(Error): pass

class SimpleConfig(object):
    '''A single simple config'''

    def __init__(self, project, variant, libtype, config):
        '''read a single simple config'''
        self.project = project
        self.variant = variant
        self.libtype = libtype
        self.config  = config
        cmd = "pm configuration -l %(project)s %(variant)s -t %(libtype)s -n %(config)s -D +MaGiC+" % vars()
        (status, stdout, stderr) = run_command(cmd)
        if status != 0 or stderr:
            raise ConfigLoadError("Cannot read configuration: %s %s %s %s" % (project, variant, libtype, config))
        lines = [x.split("+MaGiC+") for x in str(stdout).strip().split('\n')]

        # stupid icmanage bug
        if len(lines) >= 3 and lines[2] != ['Project', 'Variant', 'LibType', 'Library', 'Release', 'Configuration', 'Location', 'Description']:
            lines[2:2] = [['Project', 'Variant', 'LibType', 'Library', 'Release', 'Configuration', 'Location', 'Description']]

        assert(len(lines) >= 4)
        assert(lines[0] == ['Configuration', 'ConfType', 'Desc', 'LibDefsPath'])
        assert(lines[2] == ['Project', 'Variant', 'LibType', 'Library', 'Release', 'Configuration', 'Location', 'Description'])
        self.data = lines[3:]

    def get_items(self):
        items = []
        for project, variant, libtype, lib, rel, config, loc, desc in self.data:
            assert(libtype == self.libtype)
            project = re.sub(r'^.*:', '', project)
            if project == self.project and variant == self.variant:
                # local item
                assert(config == self.config)
                item = "%(lib)s@%(rel)s" % vars()
            else:
                # remote item
                item = "%(config)s@%(project)s/%(variant)s" % vars()
            items.append(item)
        return items

    def get_local_libraries(self):
        result = []
        for project, variant, libtype, lib, rel, config, loc, desc in self.data:
            assert(libtype == self.libtype)
            project = re.sub(r'^.*:', '', project)
            if project == self.project and variant == self.variant:
                assert(config == self.config)
                result.append((lib, rel, loc))
        return result

    def get_pvlc(self):
        return self.project, self.variant, self.libtype, self.config 

    def has_remote_entries(self):
        for project, variant, libtype, lib, rel, config, loc, desc in self.data:
            assert(libtype == self.libtype)
            project = re.sub(r'^.*:', '', project)
            if project != self.project or variant != self.variant:
                return True
        return False

    def clone(self, name):        
        #Make sure the target doesn't already exist
        if abnrlib.icm.config_exists(self.project, self.variant, self.libtype, name):
            raise Error("Cannot clone to {0}/{1}:{2}@{3} - it already exists".format(
                self.project, self.variant, self.libtype, name))
        
        [(lib, rel, loc)] = self.get_local_libraries()
        if "ActiveDev" in rel:
            item = "{}@{}".format(lib, "#dev")
        elif "ActiveRel" in rel:
            item = "{}@{}".format(lib, "#rel")
        else:
            item = "{}@{}".format(lib, rel)            
        cmd = "pm configuration {} {} {} {} -t {}".format(self. project, self.variant, 
                                                             name, item, self.libtype)
        (status, stdout, stderr) = run_command(cmd)
        if status != 0 or stderr:
            print(stderr)
            raise Error("Error cloning configuration: %s %s %s %s" % (self.project, self.variant, self.libtype, self.config))


