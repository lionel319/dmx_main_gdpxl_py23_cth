#!/usr/bin/env python

from __future__ import print_function
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..'))
import argparse
import logging
from dmx.abnrlib.flows.workspace import Workspace


LOGGER = logging.getLogger(__name__)


def workspacecheck(project, variant, configuration, milestone, thread, libtype=None, logfile=None, dashboard=None, celllist_file=None, nowarnings=False, waiver_file=[], preview=False):
    ws = Workspace()
    ws.check_action(project, variant, configuration, milestone, thread, libtype, logfile, dashboard, celllist_file, nowarnings, waiver_file, preview)
    return [ws.exit_code, ws.errors, ws.report_message]



if __name__ == '__main__':
    ### For debugging purpose
    p = argparse.ArgumentParser()
    p.add_argument('--project',     '-p', required=True)
    p.add_argument('--variant',     '-v', required=True)
    p.add_argument('--config',      '-c', required=True)
    p.add_argument('--milestone',   '-m', required=True)
    p.add_argument('--thread',      '-t', required=True)
    p.add_argument('--libtype',     '-l', required=False, default=None)
    args = p.parse_args()
    ret = workspacecheck(args.project, args.variant, args.config, args.milestone, args.thread, args.libtype)

    print("exit_code: <<<{}>>>".format(ret[0]))
    print("errors: <<<{}>>>".format(ret[1]))
    print("report: <<<{}>>>".format(ret[2]))

        
        


