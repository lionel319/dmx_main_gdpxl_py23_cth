#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/superuser.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Class to return list of DMX superusers

Author: Kevin Lim Khai - Wern

Copyright (c) Altera Corporation 2016
All rights reserved.
'''

import os
import logging
import sys
from dmx.utillib.utils import is_pice_env, get_altera_userid

PICE_DMX_SUPERUSERS = ['limtecky', 'bblanc', 'khow', 'fysu', 'jytseng', 'arunjang']
PSG_DMX_SUPERUSERS = ['tylim', 'bblanc', 'kbhow', 'fysu', 'jtseng', 'ajangity']

def get_dmx_superusers():
    superusers = []
    if is_pice_env():
        superusers = PICE_DMX_SUPERUSERS
    else:
        superusers = PSG_DMX_SUPERUSERS

    return superusers        
                
def is_superuser(user=os.getenv('USER')):                
    return user in get_dmx_superusers()
