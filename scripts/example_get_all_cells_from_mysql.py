#!/usr/bin/env python

import os
import sys
rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)

from djangodata import mysql_db_connector
from djangodata.models import Cell

### Get all available Cell()
print '========================'
print "All Available Cells"
print '========================'
print Cell.objects.all()

### Get all Cell() from variant:ad
print '========================'
print "Cells from variaint:ad"
print '========================'
print Cell.objects.filter(variant='ad')

