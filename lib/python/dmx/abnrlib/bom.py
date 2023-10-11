#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/bom.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Abstract base class used for representing IC Manage boms. 
See: http://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/ICMConfigurationClass for more details

Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2016
All rights reserved.
'''

## @addtogroup dmxlib
## @{

from dmx.dmxlib.leafbom import LeafBOM
from dmx.dmxlib.parentbom import ParentBOM

class BOMError(Exception):
    pass

class BOM(object):
    '''
    Concrete implementation of the ICMConfig base class.

    Represents a simple IC Manage bom
    '''

    @classmethod    
    def get_bom(self, project, ip, bom, deliverable=None, preview=True):
        '''
        Used to create a new IC Manage simple bom.

        Use ConfigFactory to load a bom from the IC Manage database.
        '''
        if deliverable:
            return LeafBOM(project, ip, deliverable, bom, preview=preview)
        else:
            return ParentBOM(project, ip, bom, preview=preview)            

## @}
