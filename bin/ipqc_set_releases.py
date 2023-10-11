#!/usr/bin/env python
import os
import sys
import re
import json
import argparse
import sqlite3

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)

from dmx.ecolib.ecosphere import EcoSphere
from dmx.utillib.ipcategory import get_released_fullchips, get_ipqc_path

from dmx.ipqclib.utils import dir_accessible, file_accessible, run_command
from dmx.utillib.settings import _RELEASES_DB
_TABLE = 'releases'

def is_valid_family(arg):
    e = EcoSphere()
    families = [f.name.lower() for f in e.get_families()]
    if not(arg.lower() in families):
        print("Error: invalid family name. List of families: {}" .format(families))
        return
    return arg

class Release():

    def __init__(self, milestone, ip_name, ipqc_path, release_name, family):
        self._milestone = milestone
        self._ip_name = ip_name
        self._ipqc_path = ipqc_path
        self._name = release_name
        self._family = family
        self._device = None
        self._report_path = os.path.join(self._ipqc_path, 'ipqc.html')

        for device in self._family.get_products():
            if device.name in self._name:
                self._device = device.name

    @property
    def device(self):
        return self._device

    @property
    def name(self):
        return self._name

    @property
    def milestone(self):
        return self._milestone

    @property
    def report_path(self):
        return self._report_path



class IP():

    def __init__(self, name, milestones, family, ipqc_path):
        self._name = name
        self._milestones = milestones
        self._family = family
        self._ipqc_path = ipqc_path
        self._releases = self._get_releases()

    def _get_releases(self):
        releases = []
        for milestone in self._milestones:
            path = os.path.join(self._ipqc_path, milestone, 'rel')
            tmp_releases = os.listdir(path)
            for release in tmp_releases:
                releases.append(Release(milestone, self._name, os.path.join(path, release), release, self._family))
        return releases

    @property
    def releases(self):
        return self._releases

    @property
    def name(self):
        return self._name



def create_table(filepath):
    print("Creating category table")
    # Create a connection object that represents the database.
    # Data are stored in /p/psg/falcon/ipqc_rel/settings/ip_category.db
    conn = sqlite3.connect(filepath)

    # Once you have a connection, you can create a Cursor object and call its execute() method to perform SQL commands
    c= conn.cursor()

    # Create table
    c.execute('''CREATE TABLE {} (ip_id INTEGER PRIMARY KEY AUTOINCREMENT, ipname, project, device, release_name, milestone, report_path)''' .format(_TABLE))
    
    # Save (commit) the changes
    conn.commit()

    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()

def release_is_in_db(ip, release, filepath):
    conn = sqlite3.connect(filepath)
    c= conn.cursor()

    t = (ip, release,)
    c.execute('SELECT * FROM releases WHERE ipname=? and release_name=?', t)
    
    if c.fetchone() != None:
        return True
    return False


def main():
    e = EcoSphere()
    family = e.get_family(args.family)

    path = get_ipqc_path(family)
    ips = os.listdir(path)
    ip_list = []

    for ip in ips:
        
        milestones = os.listdir(os.path.join(path, ip))
        ip_list.append(IP(ip, milestones, family, os.path.join(path, ip)))


    if not(file_accessible(_RELEASES_DB, os.F_OK)):
        create_table(_RELEASES_DB)

    l = []

    for ip in ip_list:
        for release in ip.releases:
            if not(release_is_in_db(ip.name, release.name, _RELEASES_DB)):
                print("Updating {} {}" .format(ip.name, release.name))
                l.append((ip.name, family.name, release.device, release.name, release.milestone, release.report_path))

    conn = sqlite3.connect(_RELEASES_DB)
    c= conn.cursor()

    c.executemany('''INSERT INTO releases(ipname, project, device, release_name, milestone, report_path) VALUES (?, ?, ?, ?, ?, ?)''' , l)
    conn.commit()

    c.execute('SELECT * FROM releases')
    for row in c:
       print(row)

    conn.close()



if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        add_help=True
    )
    parser.add_argument('-f', '--family', dest='family', action='store', metavar='<family>', required=True, type=is_valid_family, help='family name')
    args = parser.parse_args()

    result = main()
    sys.exit(result)
