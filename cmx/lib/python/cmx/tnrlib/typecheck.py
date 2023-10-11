#!/usr/bin/env python

from __future__ import print_function
from builtins import object
import sys, os
import re
import logging

CMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, os.getenv("DMXLIB"))
sys.path.insert(0, os.getenv("CMXLIB"))

import cmx.dmlib.CheckType
import dmx.utillib.contextmgr

LOGGER = logging.getLogger(__name__)

class TypeCheckError(Exception): pass

class TypeCheck(object):
    def __init__(self, workarea, ipname, cellname, deliverablename, familyobj):
            
        self.workarea = workarea
        self.ipname = ipname
        self.cellname = cellname
        self.deliverablename = deliverablename
        self.familyobj = familyobj
        self.deliverableobj = self.familyobj.get_deliverable(self.deliverablename)


    def runCheck(self):
        LOGGER.debug('Running type-check for {}:{}/{}'.format(self.ipname, self.deliverablename, self.cellname))
        with dmx.utillib.contextmgr.cd(self.workarea):
            checkobj = cmx.dmlib.CheckType.CheckType(self.ipname, self.cellname, workarea=self.workarea, familyobj=self.familyobj)
            checkobj.checkType(self.deliverablename, verbose=True)
            errors = [x.strip() for x in checkobj._errors]
        return errors


