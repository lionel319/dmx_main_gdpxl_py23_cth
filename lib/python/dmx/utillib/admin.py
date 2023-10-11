#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/admin.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Class to return list of DMX admins

Author: Kevin Lim Khai - Wern

Copyright (c) Altera Corporation 2016
All rights reserved.
'''

import os
import logging
import sys
import dmx.utillib.utils

PICE_DMX_ADMINS = ['lionelta', 'psginfraadm', 'fysu', 'bblanc', 'wplim', 'cftham', 'limty', 'prevanka', 'mconkin', 'jlonge']
PSG_DMX_ADMINS = ['tclark', 'kwlim', 'yltan', 'nbaklits', 'psginfraadm', 'envadm']

def get_dmx_admins():
    admins = []
    if dmx.utillib.utils.is_pice_env():
        admins = PICE_DMX_ADMINS
    else:
        admins = PSG_DMX_ADMINS

    return admins

def is_admin(user=os.getenv('USER')):
    return user in get_dmx_admins()
