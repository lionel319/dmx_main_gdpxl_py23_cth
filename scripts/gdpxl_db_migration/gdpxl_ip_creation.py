#!/usr/bin/env python

import sys
import os
import logging
import dmx.abnrlib.config_factory
import dmx.abnrlib.icm
from pprint import pprint

LOGGER = logging.getLogger()

def main():
    infile = 'gdp.data'

    with open(infile) as f:
        a = {}
        for line in f:
            if line.startswith('='):
                variant = ''
            elif line.startswith('variant'):
                sline = line.split()
                variant = sline[1]
                a[variant] = {}
            elif line.startswith('iptype'):
                sline = line.split()
                a[variant]['iptype'] = sline[1]
            elif line.startswith('project'):
                sline = line.split()
                a[variant]['project'] = sline[1]
            elif line.startswith('subips'):
                sline = line.split()
                a[variant]['subips'] = sline[1:]
               
    for variant in a:
        cmd = 'dmx ip create -p {} -i {} --type {} --debug'.format(a[variant]['project'], variant, a[variant]['iptype'])
        print cmd
        #os.system(cmd)

if __name__ == '__main__':
    if '--debug' in sys.argv:
        logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.INFO)
    main()
