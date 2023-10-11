#!/usr/bin/env python

from abnrlib.icm import ICManageCLI
from altera_icm.abnr_utils import run_command
import json

icm = ICManageCLI()

filename = '//depot/icm/proj/{}/{}/ipspec/dev/cell_names.txt'
cmd = 'icmp4 print -q ' + filename

data = []
projects = ['i14socnd', 'Crete3', 'i10socfm']
for project in projects:
    for variant in icm.get_variants(project):
        exitcode, stdout, stderr = run_command(cmd.format(project, variant))
        cellnames = [line.strip() for line in stdout.splitlines() if not line.startswith('//') and not line.startswith("#") and line.strip()]
        for cellname in cellnames:
            data.append( [project, variant, cellname] ) 

with open('cellnames.json', 'w') as f:
    json.dump(data, f, indent=2)
