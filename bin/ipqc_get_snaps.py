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

from dmx.ipqclib.utils import dir_accessible, file_accessible, run_command
from dmx.utillib.settings import _SNAPS_DB
_TABLE = 'releases'

def is_valid_family(arg):
    e = EcoSphere()
    families = [f.name.lower() for f in e.get_families()]
    if not(arg.lower() in families):
        print("Error: invalid family name. List of families: {}" .format(families))
        return
    return arg



def main():
    
    e = EcoSphere()
    family = e.get_family(args.family)

    conn = sqlite3.connect(_SNAPS_DB)
    c= conn.cursor()

    t = (family.name, )
    c.execute('SELECT * FROM releases WHERE project=?', t)
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
