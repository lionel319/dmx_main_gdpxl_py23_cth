#!/usr/bin/env python

from abnrlib.icm import ICManageCLI
from altera_icm.abnr_utils import run_command
import json
import re


def get_cellname_from_filepath(filepath):
    m = re.search('(^.+/([^/]+).unneeded_deliverables.txt)', filepath)
    if not m:
        return []
    return [m.group(1), m.group(2)] # (filepath, cellname)


icm = ICManageCLI()

filename = '//depot/icm/proj/{}/{}/ipspec/dev/*.unneeded_deliverables.txt'
cmd = "icmp4 files '" + filename + "' | grep -v 'delete change'"

data = []
projects = ['i14socnd', 'Crete3', 'i10socfm']
for project in projects:
    for variant in icm.get_variants(project):
        exitcode, stdout, stderr = run_command(cmd.format(project, variant))
        print "Variant:{}".format(variant)
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        for line in lines:
            ret = get_cellname_from_filepath(line)
            if ret:
                filepath, cellname = ret
                printcmd = 'icmp4 print -q {}'.format(filepath)
                exitcode, stdout, stderr = run_command(printcmd)
                libtypes = [line.strip() for line in stdout.splitlines() if line.strip() and not line.startswith("#") and not line.startswith("//")]
                data.append( [project, variant, cellname, libtypes] )

with open('unneeded.json', 'w') as f:
    json.dump(data, f, indent=2)


