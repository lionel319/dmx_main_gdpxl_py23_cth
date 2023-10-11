#!/usr/bin/env python

''' 
Do a diff and show the changes between 2 dmx released version 

Usage:-
    diff_dmx_version main 1.1 [p4cmd]

Note:-
    set p4cmd to your own settings so that it works.
    For me, i need to set it to this in order for it to work, (which is the default setting)
        /p/psg/ctools/perforce/2015.1/linux64/p4 -u yltan -c pice-yltan-pg -p sj-perforce:1666 

How it works:-
    - find the changelist from 
        - /p/psg/flows/common/dmx/main/.version
        - /p/psg/flows/common/dmx/1.1/.version
    - run 'p4 diff2 -Od ...@changelist1 @changelist2'


'''

import os
import sys

def main():
    root = '/p/psg/flows/common/dmx'

    v1 = sys.argv[1]
    v2 = sys.argv[2]
    if len(sys.argv) > 3:
        p4cmd = sys.argv[3]
    else:
        p4cmd = "/p/psg/ctools/perforce/2015.1/linux64/p4 -u yltan -c pice-yltan-pg -p sj-perforce:1666 "

    
    f1 = os.path.join(root, v1, '.version')
    f2 = os.path.join(root, v2, '.version')

    c1 = get_changelist_from_file(f1)
    c2 = get_changelist_from_file(f2)

    depot = '//depot/da/infra/dmx/main/...'
   
    #print_diff_2(p4cmd, depot, c1, c2)
    print_changes(p4cmd, depot, c1, c2)


def print_changes(p4cmd, depot, c1, c2):
    sorted_changelist = sorted([c1, c2])
    os.system("{} changes -l {}@{},{}".format(p4cmd, depot, sorted_changelist[0], sorted_changelist[1]))

def print_diff_2(p4cmd, depot, c1, c2):
    os.system(""" echo '
=======================================
=============== SUMMARY ===============
=======================================
    ' """)
    os.system("{} diff2 -q -Od -ds {}@{} {}@{}".format(p4cmd, depot, c1, depot, c2))

    os.system(""" echo '
=======================================
=============== DETAILS ===============
=======================================
    ' """)
    os.system("{} diff2 -Od {}@{} {}@{}".format(p4cmd, depot, c1, depot, c2))


def get_changelist_from_file(filename):
    with open(filename) as f:
        changelist = f.readline().split()[0]
    return changelist




if __name__ == '__main__':
    main()

