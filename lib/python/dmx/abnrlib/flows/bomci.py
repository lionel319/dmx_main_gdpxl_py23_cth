#!/usr/bin/env python

'''
SPEC
====
    https://wiki.ith.intel.com/display/tdmaInfra/dmx+bom+ci+-+Phase+1

'''
import re
import logging
import os
import urllib, urllib2
import sys
from argparse import ArgumentParser
from getpass import getpass
import csv

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)

from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.icm import ICManageCLI
from dmx.utillib.utils import run_command
import dmx.abnrlib.workspace
import dmx.ecolib.ecosphere

class BomCheckin(object):

    def __init__(self, ip, milestone, description, deliverables=None, hook=None, hierarchy=False, dryrun=False):
        
        self.logger = logging.getLogger(__name__)
        self.ip_name = ip
        self.milestone = milestone
        self.description = description
        self.deliverables = deliverables
        self.hook = hook
        self.hierarchy = hierarchy
        self.dryrun = dryrun

        eco = dmx.ecolib.ecosphere.EcoSphere()
        family = eco.get_family()
        self.ip = family.get_ip(self.ip_name)

    def run(self): 
        ##########################################
        ### Running IPQC 
        self.logger.info("Running ipqc command ...")
        ipqccmd = 'ipqc run-all -i {} -m {} --no-revert '.format(self.ip_name, self.milestone)
        if not self.hierarchy:
            ipqccmd += ' --no-hierarchy '
        if self.deliverables:
            ipqccmd += ' -d {} '.format( ' '.join([x for x in self.deliverables]) )
        self.logger.info(">>> {}".format(ipqccmd))
        if not self.dryrun:
            exitcode = os.system(ipqccmd)
        if exitcode != 0:
            self.logger.error("ipqc has error and exited with exitcode({}). Program terminated.".format(exitcode))
            return exitcode

        ##########################################
        ### Running HOOK
        if self.hook:
            self.logger.info("Running hook command ...")
            if not self.dryrun:
                exitcode = os.system(self.hook)
        else:
            self.logger.info("No hook provided. Skipping this step.")
            exitcode = 0
        if exitcode != 0:
            self.logger.error("hook command has error and exited with exitcode({}). Program terminated.".format(exitcode))
            return exitcode

        ##########################################
        ### Check-IN
        cmds = []
        cmdprefix = "icmp4 submit -d '{}' ".format(self.desc)

        if self.hierarchy:
            variantspec = '*'
        else:
            variantspec = self.ip_name

        if not self.deliverables:
            ### Check-in with NO --deliverables
            cmds.append("{} '{}/...'".format(cmdprefix, variantspec))

        elif self.deliverables[0].startswith("view_"):
            ### check-in with --deliverables of view_*
            dobjs = self.ip.get_deliverables(milestone=self.milestone, views=self.deliverables)
            for dobj in dobjs:
                cmds.append("{} '{}/{}/...'".format(cmdprefix, variantspec, dobj.name))
        else:
            ### check-in with --deliverables of pure icm-libtypes
            for d in self.deliverables:
                cmds.append("{} '{}/{}/...'".format(cmdprefix, variantspec, d))


        self.logger.info("Checking-in files ...")
        for cmd in cmds:
            self.logger.info(">>> {}".format(cmd))
            if not self.dryrun:
                os.system(cmd)

        return 0


