#!/usr/bin/env python
import os

_FAMILY_MAP = '/nfs/site/disks/da_infra_1/users/dmxweb/ipqc_catalog/ipqc_catalog/webapp/settings/family_map.json'
_INFRA_PATH = '/p/psg/da/infra/dmx/ipqc'
_RELEASES_DB = os.path.join(_INFRA_PATH, 'releases.db')
_SNAPS_DB = os.path.join(_INFRA_PATH, 'snaps.db')
_IPCATEGORY_DB = os.path.join(_INFRA_PATH, 'ipcategory.db')
_IPCATEGORY_SNAP_DB = os.path.join(_INFRA_PATH, 'ipcategory_snap.db')
_TABLE_IP_TYPE = 'category'
_TABLE_IP_RELEASES = 'releases'

