#!/usr/bin/env python

'''
https://jira.devtools.intel.com/browse/PSGDMX-1971
$Author: lionelta $
$Revision: #1 $
$DateTime: 2022/12/13 18:19:49 $
'''

import os
import sys
import re

from dmx.utillib.utils import run_command
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.config_naming_scheme import ConfigNamingScheme

def main():

    if '-h' in ' '.join(sys.argv):
        print """
        Usage:-
        -------
        {} <project> <variant> <config> <cfgfile> <cutoff>

            cfgfile format
            --------------
            rnr/rnr_aib_cmn:bcmrbc@REL1.0RNRrevA0__20ww163a
            rnr/rnr_aib_cmn:cdc@REL1.0RNRrevA0__20ww164a
            rnr/rnr_aib_cmn:complib@REL1.0RNRrevA0__20ww093a
            rnr/rnr_aib_cmn:cvrtl@REL1.0RNRrevA0__20ww164a
            rnr/rnr_aib_cmn:dftdsm@REL1.0RNRrevA0__20ww133a
            rnr/rnr_aib_cmn:ippwrmod@REL1.0RNRrevA0__20ww140a
            rnr/rnr_aib_cmn:ipspec@REL1.0RNRrevA0__20ww030a

            cutoff format
            -------------
            20ww203

        """.format(sys.argv[0])
        return

    project, variant, config, cfgfile, cutoff = sys.argv[1:6]
    print "{}/{}@{}".format(project, variant, config)
    cutoffnum = cutoff[0:2] + cutoff[4:7]
    print "cutoffnum: {}".format(cutoffnum)
    
    req_varlib = get_required_varlib(cfgfile)
    print "req_varlib: {}".format(req_varlib)
    print "----------------------------------------------"
    cns = ConfigNamingScheme()
    for cf in ConfigFactory.create_from_icm(project, variant, config).flatten_tree():
        if cf.is_composite():
            continue

        p = cf.project
        v = cf.variant
        c = cf.config
        l = cf.libtype
        library = cf.library

        if [v, l] in req_varlib:
            data = cns.get_data_for_release_config(c)
            if not data:
                continue    # Not a REL
            confignum = data['year'] + data['ww'] + data['day']
            if int(confignum) < int(cutoffnum):
                print "SKIP: {} (cutoff)".format(cf)
                continue
            
            if library == 'dev':
                print "FAIL: {} (library: {})".format(cf, library)
            else:
                print "PASS: {} (library: dev)".format(cf)

        else:
            print "SKIP: {} (libtype)".format(cf)
            continue



def get_required_varlib(cfgfile):
    retlist = []
    with open(cfgfile) as f:
        for line in f:
            if line.isspace() or not line:
                continue
            sline = re.findall('[\w]+', line)
            if len(sline) >  4:
                retlist.append([sline[1], sline[2]])
    return retlist


if __name__ == '__main__':
    sys.exit(main())
