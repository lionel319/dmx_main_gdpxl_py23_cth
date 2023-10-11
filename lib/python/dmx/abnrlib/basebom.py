#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/basebom.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Abstract base class used for representing IC Manage boms. 
See: http://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/ICMConfigurationClass for more details

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''

## @addtogroup dmxlib
## @{

import logging
import getpass
from datetime import datetime
import re

class BaseBOMError(Exception):
    pass

class BaseBOM(object):
    '''
    Concrete implementation of the ICMConfig base class.

    Represents a simple IC Manage bom
    '''
    # Properties
    #
    @property
    def name(self):
        '''
        The name of the bom
        '''
        return self.__repr__()

    @property
    def bom(self):
        '''
        The name of the bom
        '''
        return self.bom

    @bom.setter
    def bom(self, new_bom):
        '''
        Sets the bom name
        '''
        return

    @property
    def project(self):
        '''
        The bom's project
        '''
        return self.project

    @project.setter
    def project(self, new_project):
        '''
        Sets the project name
        '''
        return

    @property
    def ip(self):
        '''
        The bom's ip
        '''
        return self.ip

    @ip.setter
    def ip(self, new_ip):
        '''
        Sets the ip name
        '''
        return
          
    @property
    def preview(self):
        '''
        Return the preview flag
        :return: The preview flag
        :type return: bool
        '''
        return self.preview

    @preview.setter
    def preview(self, new_preview):
        '''
        Sets the preview mode and reflects that change
        to the ICManageCLI object
        :param new_preview: New preview setting
        :type preview: bool
        '''
        return

    #
    # Methods
    #

    def clone(self, name):
        return
        
    def delete(self):
        return
        
    def create(self):
        return           

    def check(self):        
        return

    def snap(self):
        return
        
    def diff(self):
        return
        
    def release(self):
        return                              

    def report(self):
        return            

    
## @}
