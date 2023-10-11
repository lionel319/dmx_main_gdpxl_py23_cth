#!/usr/bin/env python
# coding: utf-8
import os
import sys, getopt
from subprocess import Popen, PIPE, check_output
import subprocess
import re
import random
import getpass
import time
import argparse
import glob
import dmx.abnrlib.icm
import dmx.utillib.utils
from dmx.abnrlib.flows.updatevariant import UpdateVariant
import logging


class CICQ_Regression():

    def __init__(self, proj, ip, thread, bom=None):
        self.dst_res =""
        self.proj = proj
        self.thread = thread
        self.bom = bom
        self.ip = ip
        self.preview = True
        self.icm_client = dmx.abnrlib.icm.ICManageCLI()
        self.source_ip_with_libtype_details = ""
        self.logger = logging.getLogger(__name__)


    def check_before_running(self):

        if self.bom: 
            if not self.icm_client.config_exists(self.proj, self.ip, self.bom):
                self.logger.error("\nThe Bom: " + self.proj + "/" + self.ip + "@" + self.bom + " does not exist!!")
                sys.exit(1)


        if not self.icm_client.project_exists(self.proj):
            self.logger.error("\nThe project " + self.proj + " does not exist!!Can not continue")
            sys.exit(1)

        if not self.icm_client.variant_exists(self.proj, self.ip):
            self.logger.error("\nThe IP: " + self.proj + "/" + self.ip + " does not exist!!")
            sys.exit(1)

        thread_landing_zone_config = "landing_zone_" + self.thread

        if not self.icm_client.config_exists(self.proj, self.ip, thread_landing_zone_config):
            self.logger.error("\nThe thread: " + self.proj + "/" + self.ip + "@" + thread_landing_zone_config + " does not exist!!")
            sys.exit(1)


    def cicq_update_optional(self, config_file = None):
        self.check_before_running()
        if not self.icm_client.config_exists(self.proj, self.ip, self.bom):
            self.logger.error("\nThe Bom: " + self.proj + "/" + self.ip + "@" + self.bom + " does not exist!!")
            sys.exit(1)
        if config_file and self.icm_client.config_exists(self.proj, self.ip, self.bom):
            cicq_update_command = "arc submit -- 'dmx cicq update -p " + self.proj + " -b " + self.bom + " -i " + self.ip + " -t " + self.thread + " -c " + config_file + "'"
            print(cicq_update_command)
            #arc_output_cicq = check_output(cicq_update_command)
            arc_output_cicq  = subprocess.Popen(cicq_update_command.split(" "), stdout = subprocess.PIPE)
            wait_for_cicq_update_command = "arc wait " + str(arc_output_cicq.stdout.read())
            self.logger.info(wait_for_cicq_update_command)
            os.system(wait_for_cicq_update_command)


    def regress(self):
        self.check_before_running()
        cicq_run_command = "arc submit -- 'dmx cicq run -p " + self.proj + " -i " + self.ip + " -t " + self.thread + " --force '"
        #cicq_run_output = check_output(cicq_run_command)
        print(cicq_run_command)
        #os.system(cicq_run_command)
        #return cicq_run_output


    def run(self):
        self.regress()
        #return ret


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='Command to migrate IP')
    parser.add_argument('-p', '--proj', metavar='project', action='store')
    parser.add_argument('-ip', '--ip', metavar='ip', action='store')
    parser.add_argument('-b', '--bom', metavar='bom', action='store')
    parser.add_argument('-t', '--thread', metavar='thread', action='store')
    parser.add_argument('-c', '--config', metavar='config_file', action='store')
    args=parser.parse_args()
    logging.info("CICQ Regress ...")

    a = CICQ_Regression(args.proj, args.ip, args.thread, args.bom)

    if args.bom and args.config:
        a.cicq_update_optional(args.config)

    a.run()
    print("\n\nCICQ Regress script finished successfully\n\n")

