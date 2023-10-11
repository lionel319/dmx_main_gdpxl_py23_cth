#!/usr/bin/env python

## @page djangolibgraph A Detail Hierarchical Graph Of the djangolib Architecture
## @image html djangolib.png

import os
import sys
rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)

dmxdb = os.getenv("DMXDB", 0)
if dmxdb == "DMXTEST":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'djangolib.mysql_systemtest_settings'
else:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'djangolib.mysql_settings'
