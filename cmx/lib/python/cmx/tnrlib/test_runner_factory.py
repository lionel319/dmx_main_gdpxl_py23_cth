#!/usr/bin/env python

import os
import sys
import json
from pprint import pprint
import textwrap
import logging

CMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DMXLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'lib', 'python')
sys.path.insert(0, os.getenv("DMXLIB"))
sys.path.insert(0, os.getenv("CMXLIB"))

from dmx.utillib.utils import add_common_args, run_command
import dmx.tnrlib.audit_check
from dmx.tnrlib.test_result import TestResult, TestFailure
from dmx.tnrlib.waiver_file import WaiverFile
import dmx.ecolib.ecosphere

import cmx.tnrlib.typecheck
import cmx.utillib.utils
import cmx.tnrlib.test_runner
import cmx.tnrlib.test_runner_febe
import cmx.tnrlib.test_runner_view
import cmx.tnrlib.test_runner_variant

class TestRunnerFactory():

    def __init__(self, thread=None, milestone=None, deliverable=None, workspace_root=None, ipname=None, stepname='a0'):

        self.logger = logging.getLogger(__name__)
        self._kwargs = {
            'thread' : thread,
            'milestone' : milestone,
            'deliverable' : deliverable,
            'workspace_root' : workspace_root,
            'ipname' : ipname,
            'stepname' : stepname
        }
        self.logger.debug("kwargs: {}".format(self._kwargs))

    def get_testrunner(self):
        deliverable = self._kwargs['deliverable']
        if not deliverable:
            inst = cmx.tnrlib.test_runner_variant.TestRunnerVariant(**self._kwargs)
        elif deliverable.startswith("view_"):
            inst  = cmx.tnrlib.test_runner_view.TestRunnerView(**self._kwargs)
        elif deliverable == 'febe':
            inst  = cmx.tnrlib.test_runner_febe.TestRunnerFebe(**self._kwargs)
        else:
            inst = cmx.tnrlib.test_runner.TestRunnerPoc(**self._kwargs)
        return inst
