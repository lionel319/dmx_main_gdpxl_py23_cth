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
from cmx.tnrlib.test_runner_view import TestRunnerView

class TestRunnerVariant(TestRunnerView):

    def __init__(self, thread=None, milestone=None, deliverable=None, workspace_root=None, ipname=None, stepname='a0'):
        self.logger = logging.getLogger(__name__)
        super().__init__(thread=thread, milestone=milestone, deliverable=deliverable, workspace_root=workspace_root, ipname=ipname, stepname=stepname)
        print(locals())

    def get_required_deliverables(self):
        if not self.required_deliverables:
            roadmapobj = self.get_roadmap_obj()
            self.required_deliverables = roadmapobj.get_deliverables(milestone=self.milestone)
        return self.required_deliverables 



