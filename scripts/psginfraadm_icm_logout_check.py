#!/usr/bin/env python

import os
import sys
import tempfile
import dmx.utillib.stringifycmd
import dmx.utillib.utils
from pprint import pprint

def main():
    basecmd = '_icmp4 users psginfraadm'
    arcopts = {
        'options': {'--test':'', '--watch':''}, 
        'resources': 'project/falcon/branch/fm6revbmain/rc'
    }
    sshopts = {
        'site': 'sc'
    }
    a = dmx.utillib.stringifycmd.StringifyCmd(basecmd=basecmd, arcopts=arcopts, sshopts=sshopts)
    a.sshexe = '/p/psg/da/infra/admin/setuid/tnr_ssh'
    cmd = a.get_finalcmd_string()

    print cmd

    errstrings = ['Perforce password (P4PASSWD) invalid or unset', 'no such user']

    exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
    print "exitcode: {}".format(exitcode)
    print "stdout: {}".format(stdout)
    print "stderr: {}".format(stderr)

    if exitcode or is_output_match_errstrings(stdout+stderr, errstrings):
        send_telegram(stderr.strip())

def is_output_match_errstrings(output, errstrings):
    return [x for x in errstrings if x in output]

def send_telegram(stderr):
    makefile = locate_makefile()
    cmd = "make -f {} send_message MSG='{}'".format(makefile, stderr)
    os.system(cmd)


def locate_makefile():
    return os.path.join(os.path.dirname(__file__), 'telegram', 'Makefile')


if __name__ == '__main__':
    main()

