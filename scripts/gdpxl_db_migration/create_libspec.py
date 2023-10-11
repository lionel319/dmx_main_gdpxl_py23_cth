#!/usr/bin/env python

import os

def main():
    infile = 'all_libtypes.txt'

    with open(infile) as f:
        for line in f:
            sline = line.strip()
            if sline:
                print "={}=".format(sline)
                if sline == 'oa' or sline == 'oa_sim':
                    cmd = 'gdp create libspec {} --set location-template="{{{{variant}}}}/{{{{libtype}}}}/{{{{variant}}}}" --set domain="Cadence_OA"'.format(sline)
                else:
                    cmd = 'gdp create libspec {} --set location-template="{{{{variant}}}}/{{{{libtype}}}}" --set domain="Generic"'.format(sline)
            print 'cmd: {}'.format(cmd)
            os.system(cmd)

if __name__ == '__main__':
    main()
