#!/usr/bin/env python

import os
import sys
from dmx.ecolib.ecosphere import EcoSphere
import xml.etree.ElementTree as ET
from pprint import pprint
import xml.dom.minidom
import datetime

import sys
import logging
import textwrap
import itertools

from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.icmsimpleconfig import SimpleConfig
from dmx.utillib.utils import format_configuration_name_for_printing, normalize_config_name, get_ww_details
from dmx.abnrlib.config_factory import ConfigFactory

from dmx.abnrlib.command import Command, Runner
from dmx.utillib.utils import add_common_args
from dmx.abnrlib.flows.snaptree import SnapTree as SnapTreeRunner
from dmx.abnrlib.flows.edittree import EditTree

def main():
  # For sa_lib bom, cw_lib and ipspec will need to be updated
  project = 'i10socfm'
  cw_lib_ip = 'cw_lib'
  cw_lib_bom = 'ciw'
  description='ciw daily pull snapshot'
  
  cw_lib_snap_name = snap_ip(project, cw_lib_ip, cw_lib_bom)
  if (cw_lib_snap_name != '') :
    sa_ip = 'sa_lib'
    sa_bom = 'mxtest'
    update_sub_ip_bom(project, 'sa_lib', 'mxtest', cw_lib_ip, cw_lib_snap_name)


def snap_ip(project, ip, source_bom) :
  normalized_config = normalize_config_name(source_bom)
  (year, ww, day) = get_ww_details()
  now = datetime.datetime.now()

  snap_name = 'snap-mxtest-{0}_{1}ww{2}{3}_t{4}-{5}'.format(normalized_config, year, ww, day, now.hour, now.minute)

  print("Creating snapshot " + snap_name)
  snap = SnapTreeRunner(project, ip, source_bom, snap_name, preview=False)
  snap_creation_error = snap.run()
  print("Snap error: " + str(snap_creation_error))
  if not snap_creation_error :
    return snap_name
  else :
    return ''

def update_sub_ip_bom(project, parent_ip, parent_ip_bom, sub_ip, sub_ip_bom) :
  repbom = []
  repboms = []
  repbom.append(project + '/' + sub_ip)
  repbom.append(sub_ip_bom)
  repboms.append(repbom)
  repsimple = ''
  edittree = EditTree(project, parent_ip, parent_ip_bom,
                      rep_configs=repboms, inplace=True)
  parent_ip_bom_edit_error = edittree.run()
  if not parent_ip_bom_edit_error :
    print "Successfully updated " + project + "/" + parent_ip + "@" + parent_ip_bom + " to include " + project + "/" + sub_ip + "@" + sub_ip_bom
  else:
    print "FAILED to update "  + project + "/" + parent_ip + "@" + parent_ip_bom + " to include " + project + "/" + sub_ip + "@" + sub_ip_bom

if __name__ == '__main__':
    sys.exit(main())
