#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/Manifest_testDAG.py#1 $

"""
Test the deliverables for presence of loops in the predecessor/successor graph
"""

import sys
import os

dmRoot = os.path.dirname (os.path.dirname (__file__))
sys.path.insert(0, os.path.abspath(dmRoot))

import Manifest


deliverables = Manifest.Manifest.getAllDefaultDeliverables() # will return str on errors
if type (deliverables) is str:
    print deliverables
    sys.exit (1)

print deliverables
print "OK"