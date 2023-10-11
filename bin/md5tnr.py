#!/usr/bin/env python

import sys
import os
rootdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'lib', 'python')
#rootdir = '/p/psg/flows/common/dmx/12.3/lib/python/'
sys.path.insert(0, rootdir)
import dmx.tnrlib.audit_check


def main():

    if '-h' in sys.argv or len(sys.argv) < 2:
        print '''
        Usage:
        ------
            $md5tnr.py <filename> [filter_regex|None] [(rcs_disable)True|False]
        '''
        return 1

    a = dmx.tnrlib.audit_check.AuditFile(workspace_rootdir = '.')
    try:
        a.set_test_info('flow', 'subflow', 'rundir', 'cmdline', 'libtype', 'topcell')
    except Exception as e:
        print str(e)

    filename = sys.argv[1]

    filter_regex = ''
    if len(sys.argv) > 2 and sys.argv[2] != 'None':
        filter_regex = sys.argv[2]

    rcs_disable = False
    if len(sys.argv) > 3 and sys.argv[3] == 'True':
        rcs_disable = True


    print "get_checksum('{}', filter='{}', rcs_disable={})".format(filename, filter_regex, rcs_disable)
    print a.get_checksum(filename, filter=filter_regex, rcs_disable=rcs_disable)


if __name__ == '__main__':
    main()

