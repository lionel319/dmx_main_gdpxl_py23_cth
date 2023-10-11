#!/usr/bin/env python

import os
from dmx.utillib.arcenv import ARCEnv

############################################################################
# IPQC disk area for post-trigger release
# It is needed for Workspace creatio
# https://fogbugz.altera.com/default.asp?604578
############################################################################
arc = ARCEnv()
_DB_FAMILY  = arc.get_family()

if _DB_FAMILY.lower() == "falcon":
    ipqc_release_area = '/nfs/site/disks/fln_tnr_1/ipqc'
elif _DB_FAMILY.lower() == 'wharfrock':
    ipqc_release_area = '/nfs/site/disks/whr_tnr_1/ipqc'
elif (_DB_FAMILY.lower() == 'gundersonrock') or (_DB_FAMILY.lower() == 'reynoldsrock'):
    ipqc_release_area = '/nfs/site/disks/psg_tnr_1/ipqc'
else:
    ipqc_release_area = '/nfs/site/disks/psg_tnr_1/ipqc'
