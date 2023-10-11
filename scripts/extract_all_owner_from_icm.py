#!/usr/bin/env python

from abnrlib.icm import ICManageCLI
from altera_icm.abnr_utils import run_command
import json


icm = ICManageCLI()

data = []
projects = ['i14socnd', 'i10socfm', 'Crete3']
for project in projects:
    for variant in icm.get_variants(project):
        prop = icm.get_variant_properties(project, variant)
        if 'Owner' in prop:
            data.append([project, variant, prop['Owner']])

with open('owner.json', 'w') as f:
    json.dump(data, f, indent=2)

