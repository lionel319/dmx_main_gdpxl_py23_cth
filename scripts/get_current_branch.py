#!/usr/bin/env python

import os
import sys
import datetime

rootdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, rootdir)
import dmx.utillib.intel_dates as intel_dates

(yyyy, ww, d) = intel_dates.intel_calendar(datetime.datetime.today().date())
print "main_{}ww{}".format(str(yyyy)[2:], ww)

