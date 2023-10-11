#!/usr/bin/env python

import os
import sys
from pprint import pprint

rootdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, rootdir)
import dmx.ecolib.ecosphere
import dmx.abnrlib.config_factory

project = 'Falcon_Mesa'
variant = 'z1557a'
config = 'REL3.0FM8revA0__18ww156a'


cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(
    project, variant, config)

donelist = []
with open('fullchiptree.txt', 'w') as f:
    for c in cf.flatten_tree():
        if c.is_composite and [c.project, c.variant] not in donelist:
            f.write("{} {}\n".format(c.project, c.variant))
            donelist.append([c.project, c.variant])

