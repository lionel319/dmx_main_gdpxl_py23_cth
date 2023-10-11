#!/usr/bin/env python
from __future__ import print_function
import re
import os
import json
import sqlite3
from collections import OrderedDict
from dmx.ipqclib.utils import run_command, dir_accessible
from dmx.utillib.settings import _FAMILY_MAP, _TABLE_IP_RELEASES, _RELEASES_DB, _SNAPS_DB


def get_list_of_z_ip(projects):
    list_of_ips = []
    for project in projects:
        (code, out) = run_command("dmx report list -p {} -i 'z*'" .format(project.name))
        out = out.strip()
        out = out.split('\n')

        pattern = project.name + r"/(\S+)"

        for element in out:
            match = re.search(pattern, element)
            if match:
                if re.search('^z[0-9][0-9][0-9][0-9]\w$', match.group(1)):
                    list_of_ips.append(match.group(1))
    return list_of_ips

def get_fullchip_names(family):
    projects = family.get_icmprojects()
    zdevices = get_list_of_z_ip(family.get_icmprojects())

    return zdevices

# Get IPQC catalog path for release
def get_ipqc_path(family):
    with open(_FAMILY_MAP, 'r') as f:
        data = json.load(f)
        relpath = data[family.name]['rel']
        relpath = os.path.join(relpath, 'dashboard')
        return relpath

# Get IPQC catalog path for snap
def get_ipqc_snap_path(family):
    with open(_FAMILY_MAP, 'r') as f:
        data = json.load(f)
        relpath = data[family.name]['snap']
        relpath = os.path.join(relpath, 'dashboard')
        return relpath


# Get REL Full Chip
def get_released_fullchips(family, rel_type='REL'):

    list_of_released_fullchip = []
    fullchips = get_fullchip_names(family)

    if rel_type == 'REL':
        relpath = get_ipqc_path(family)
        conn = sqlite3.connect(_RELEASES_DB)
    elif rel_type == 'snap':
        relpath = get_ipqc_snap_path(family)
        conn = sqlite3.connect(_SNAPS_DB)
        
    print(fullchips)
   
    
    c= conn.cursor()

    for chip in fullchips:
        t = (chip, )
        c.execute('SELECT * FROM releases WHERE ipname=?', t)
        for row in c:
            list_of_released_fullchip.append({k[0]: v for k, v in list(zip(c.description, row))})

    conn.close()
    print(list_of_released_fullchip)
    return list_of_released_fullchip

def get_milestones(family):
    l = []
    for m in family.get_valid_milestones_threads():
        if not m[0] in l:
            l.append(m[0])
    return l


def get_ip_releases(ipname, family, rel_type='REL'):
#    list_of_release = OrderedDict()
    list_of_releases = []
    milestones = get_milestones(family)

    if rel_type == 'snap':
        conn = sqlite3.connect(_SNAPS_DB)
    else:
        conn = sqlite3.connect(_RELEASES_DB)

    c= conn.cursor()

    t = (ipname, )
    c.execute('SELECT * FROM releases WHERE ipname=?', t)
    for row in c:
        list_of_releases.append({k[0]: v for k, v in list(zip(c.description, row))})

    conn.close()

    return list_of_releases
