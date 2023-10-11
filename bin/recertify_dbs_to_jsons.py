#!/usr/bin/env python

'''
This script reads in all the data from database table of 
- certificate 
- goldenarc

... and generate a bunch of json files in the current working directory.

The generated files will have the following naming convention:-
    <tablename>___<milestone>___<thread>.json

Example:-
    certificate___3.0___FM8revA0.json
    certificate___4.0___FM8revA0.json
    certificate___5.0___FM8revA0.json
    certificate___3.0___WHRrevA0.json
    certificate___4.0___WHRrevA0.json
    certificate___5.0___WHRrevA0.json
    certificate___distinct.json

    goldenarc___3.0___FM8revA0.json
    goldenarc___4.0___FM8revA0.json
    goldenarc___5.0___FM8revA0.json
    goldenarc___3.0___WHRrevA0.json
    goldenarc___4.0___WHRrevA0.json
    goldenarc___5.0___WHRrevA0.json
    goldenarc___distinct.json

'''

import os
import sys
from pprint import pprint
import json

rootdir = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'lib', 'python'))
sys.path.insert(0, rootdir)

import dmx.abnrlib.certificate_db
import dmx.abnrlib.goldenarc_db


def main():
    generate_certificate_jsons()
    generate_goldenarc_jsons()


def generate_certificate_jsons():
    ''' '''
    dbname = 'certificate'

    ### certificate___distinct.json
    c = dmx.abnrlib.certificate_db.CertificateDb(usejson=False)
    mt = c.get_distinct_milestone_thread()
    write_to_json_file(mt, get_filepath(dbname))

    ### certificate___<milestone>___<thread>.json
    for m,t in mt:
        ret = c.get_certified_list(t, m)
        write_to_json_file(ret, get_filepath(dbname, m, t))


def generate_goldenarc_jsons():
    ''' '''
    dbname = 'goldenarc'

    ### goldenarc___distinct.json
    a = dmx.abnrlib.goldenarc_db.GoldenarcDb(usejson=False)
    mt = a.get_distinct_milestone_thread()
    write_to_json_file(mt, get_filepath(dbname))

    ### goldenarc___<milestone>___<thread>.json
    for m,t in mt:
        ret = a.get_goldenarc_list(t, m)
        write_to_json_file(ret, get_filepath(dbname, m, t))


def get_filepath(dbname, milestone='distinct', thread=''):
    ''' '''
    if milestone == 'distinct':
        return './{}___{}.json'.format(dbname, milestone)
    else:
        return './{}___{}___{}.json'.format(dbname, milestone, thread)


def write_to_json_file(obj, filename):
    print "Generating {} ...".format(filename)
    with open(filename, 'w') as f:
        json.dump(obj, f, indent=4, sort_keys=True)





if __name__ == '__main__':
    sys.exit(main())

