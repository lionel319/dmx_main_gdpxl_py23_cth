#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python/cmx/utillib/admin.py#1 $
$Change: 7449885 $
$DateTime: 2023/01/19 00:28:35 $
$Author: lionelta $

Description: Class to return list of DMX admins

Author: Kevin Lim Khai - Wern

Copyright (c) Altera Corporation 2016
All rights reserved.
'''

import os
import logging
import sys

PICE_DMX_ADMINS = ['lionelta', 'psginfraadm', 'bblanc', 'wplim', 'cftham', 'limty', 'kenvengn']

def get_dmx_admins():
    admins = PICE_DMX_ADMINS
    return admins

def is_admin(user=os.getenv('USER')):
    return user in get_dmx_admins()
