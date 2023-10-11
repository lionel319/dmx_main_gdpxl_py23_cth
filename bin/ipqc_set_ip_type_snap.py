#!/usr/bin/env python
import os
import sys
import re
import json
import sqlite3
import argparse


LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)

from dmx.ecolib.ecosphere import EcoSphere
from dmx.utillib.ipcategory import get_released_fullchips, get_ip_releases
from dmx.utillib.settings import _INFRA_PATH, _IPCATEGORY_SNAP_DB, _TABLE_IP_TYPE
from dmx.ipqclib.utils import dir_accessible, file_accessible, run_command, remove_file

_FULLCHIP = 'Fullchip'
_SUBSYSTEM = 'Subsystem'
_IP = 'IP'

def is_valid_family(arg):
    e = EcoSphere()
    families = [f.name.lower() for f in e.get_families()]
    if not(arg.lower() in families):
        print("Error: invalid family name. List of families: {}" .format(families))
        return
    return arg



def create_table(filepath):
    print("Creating category table")
    # Create a connection object that represents the database.
    # Data are stored in /p/psg/falcon/ipqc_rel/settings/ip_category.db
    conn = sqlite3.connect(filepath)

    # Once you have a connection, you can create a Cursor object and call its execute() method to perform SQL commands
    c= conn.cursor()

    # Create table
    c.execute('''CREATE TABLE {} (ipname, project, type, release_name)''' .format(_TABLE_IP_TYPE))
    
    # Save (commit) the changes
    conn.commit()

    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()

def update_table(filepath, chip, project, iptype):
    conn = sqlite3.connect(filepath)
    c = conn.cursor()

    params = (chip, project, iptype)
    # Insert a raw of data
    c.execute("INSERT INTO category VALUES (NULL, ?, ?, ?)" , params)
    conn.commit()

    conn.close()

def delete_entry(filepath, project):
    conn = sqlite3.connect(filepath)
    c = conn.cursor()

    params = (project,)
    # Insert a raw of data
    c.execute("DELETE FROM category WHERE project=?" , params)
    conn.commit()

    conn.close()



def needs_update(ipname, release, filepath):
    conn = sqlite3.connect(filepath)
    c= conn.cursor()

    t = (ipname, release,)
    c.execute('SELECT * FROM category WHERE ipname=? and release_name=?', t)

    if c.fetchone() == None:
        conn.close()
        return True

    conn.close()
    return False


class FullChip():

    def __init__(self, name, family):
        self._name = name
        self._family = family
        self._releases = get_ip_releases(self._name, family, rel_type='snap')
        self._last_release = self._get_last_release()
        self._hierarchy_file = self._get_hierarchy_file()
        (self._integration_ips, self._ips) = self._get_ips_by_category()

    def _get_last_release(self):

        last = 0
        result = None

        for release in self.releases:
            if release['ip_id'] > last:
                result = release['release_name']

        return result

    def _get_hierarchy_file(self):
        if not(dir_accessible(os.path.join(_INFRA_PATH, self._family.name), os.F_OK)):
            os.makedirs(os.path.join(_INFRA_PATH, self._family.name))

        json_file = os.path.join(_INFRA_PATH, self._family.name) + '/{}_{}_hierarchy.json' .format(self._name, self._last_release)

        if not(file_accessible(json_file, os.F_OK)):
            project = self._family.get_icmproject_for_ip(self._name)
            (code, out) = run_command('dmx report content -p {} -i {} -b {} --json {}' .format(project, self._name, self._last_release, json_file))
            print(out)

        return json_file


    def _get_ips_by_category(self):

        integration_ips = []
        all_ips = []

        with open(self._hierarchy_file, 'r') as f:
            data = json.load(f)

            for ip in data:

                pattern = '\S+/{}@\S+' .format(self._name)
                if re.search(pattern, ip):
                    pattern = '\S+/(\S+)@\S+'
                    for subsystem in data[ip]['ip']:
                        match = re.search(pattern, subsystem)
                        if match:
                            integration_ips.append(match.group(1))


                pattern = '\S+/(\S+)@\S+'
                match = re.search(pattern, ip)
                if match:
                    if (match.group(1) in integration_ips) or (match.group(1) == self._name):
                        continue

                    all_ips.append(match.group(1))

        return (integration_ips, all_ips)



    @property
    def name(self):
        return self._name

    @property
    def releases(self):
        return self._releases

    @property
    def last_release(self):
        return self._last_release

    @property
    def integration_ips(self):
        return self._integration_ips

    @property
    def ips(self):
        return self._ips


def main():
    e = EcoSphere()
    family = e.get_family(args.family)
    fullchips = get_released_fullchips(family, rel_type='snap')
    print(fullchips)
    list_of_fullchips = []

    for chip in fullchips:
        list_of_fullchips.append(FullChip(chip['ipname'], family))

    print(list_of_fullchips)


    if not(file_accessible(_IPCATEGORY_SNAP_DB, os.F_OK)):
        create_table(_IPCATEGORY_SNAP_DB)

    for chip in list_of_fullchips:

        if not(needs_update(chip.name, chip.last_release, _IPCATEGORY_SNAP_DB)):
            print("No update needed for {}" .format(chip.name))
            continue

        delete_entry(_IPCATEGORY_SNAP_DB, family.name)

        conn = sqlite3.connect(_IPCATEGORY_SNAP_DB)
        c = conn.cursor()
        t = (chip.name,)
        c.execute('SELECT * FROM category WHERE ipname=?', t)
    
        if c.fetchone() != None:
            continue
    
        print("Updating table for {} {}" .format(family.name, chip.name))
        l = [(chip.name, family.name, _FULLCHIP, chip.last_release)]

        for ip in chip.integration_ips:
            l.append((ip, family.name, _SUBSYSTEM, chip.last_release))

        for ip in chip.ips:
            l.append((ip, family.name, _IP, chip.last_release))

        c.executemany('''INSERT INTO category VALUES (?, ?, ?, ?)''' , l)
        conn.commit()

        c.execute('SELECT * FROM category')
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

