#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/printsize.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $
'''
from __future__ import print_function
from builtins import object
import sys
import logging
import textwrap
import csv
import json
import re 
import os
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.flows.printconfig import PrintConfig
from dmx.utillib.utils import run_command

class PrintSize(object):
    '''
    Runner subclass for the abnr printconfig subcommand
    '''
    def __init__(self, project, variant, deliverable, bom):
        '''
        '''
        self.project = project
        self.variant = variant
        self.deliverable = deliverable
        self.bom = bom

    def calc_size(self,result):
        '''
        Return the size from icmp4 sizes command
        '''
        if result == '': return 0
        size_in_bytes = result.split(' ')[-3] 
        return int(size_in_bytes)

    def run(self):
        '''
        Get the total number of file and size with given bom only 
        '''

        total_size = 0
        composite_size = 0
        file_num = 0
        total_file_num = 0

        if self.deliverable:
            config_fac = ConfigFactory.create_from_icm(self.project, self.variant, self.bom, self.deliverable)
        else:
            config_fac = ConfigFactory.create_from_icm(self.project, self.variant, self.bom)

        for c in sorted(config_fac.flatten_tree(), key=lambda cfobj: cfobj.name):
            if not c.is_config():
                cmd = '_xlp4 sizes {}'.format(c._filespec) 
                exitcode, stdout, stderr = run_command(cmd)
                files_size = stdout.split('\n')
                
                for ea_file_size in files_size:
                    size = self.calc_size(ea_file_size)
                    composite_size += size
                    total_size += size
                    file_num += 1
                    total_file_num += 1
                    
                print("{}/{}:{}@{}[{}] - Size : {} File : {}".format(c.project, c.variant, c.libtype, c.library, c.lib_release, composite_size, file_num))

            composite_size = 0
            file_num = 0 

        print("Total size : {}, total file : {}".format(total_size,total_file_num))
        return total_size,total_file_num 
