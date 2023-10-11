#!/usr/intel/pkgs/python3/3.9.6/bin/python3

# $Header: //depot/icd_cad/qa/audit_tcl.py#39 $
# $DateTime: 2015/11/02 18:49:47 $
# $Author: yltan $
#-------------------------------------------------------------------------------
"""
Links Tcl-generated audit info to the Python AuditFile API.
Tcl-based test flows should use audit_file.tcl to generate audit logs.

This script should not be used directly.
"""
from __future__ import print_function
import UsrIntel.R1
import sys
import os
from argparse import ArgumentParser
from xml.etree import ElementTree as ET

# current file: main/bin/audit_tcl 
# rootdir = main/
# insert = main/lib/python
rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(rootdir, 'lib', 'python'))
from dmx.tnrlib.audit_check import AuditFile

class AuditFileTcl(AuditFile):
  """
  Interface between AuditFile.tcl and AuditFile.py.
  Reads a skeleton audit file and uses the Python API to complete
  missing information.
  """

  def __init__(self):
    """
    Creates and AuditFileTcl object
    """

    pass

  def _transfer_flow_info(self, audit):
    """
    Extract all info from audit_tcl.xml required for AuditFile.set_test_info().
    Need to call that method since it does some auto-completion of audit info.
    """

    flow_node = audit.find('flow')
    flow = flow_node.get('name')
    subflow = flow_node.get('subflow')
    run_dir = flow_node.get('run_dir')
    cmdline = flow_node.get('cmdline')
    libtype = flow_node.get('libtype')
    topcell = flow_node.get('topcell')
    variant = flow_node.get('variant')
    arc_job_id = flow_node.get('arc_job_id')
    lsf_job_id = flow_node.get('lsf_job_id')
    subtest = flow_node.get('subtest')
    super(AuditFileTcl, self).set_test_info(flow, subflow, run_dir, cmdline, libtype, topcell, variant, arc_job_id, lsf_job_id, subtest)

  def _transfer_requirements(self, audit):
    """
    Transfer all file requirement data from audit_tcl.xml to the AuditFile API.
    """

    for file_node in audit.findall('files/file'):
      file_path = file_node.get('file_path')
      actual_filepath = file_node.get('actual_filepath', '')
      future_filepath = file_node.get('future_filepath', '')
      checksum = file_node.get('checksum')
      run_dir = file_node.get('run_dir')
      icm_dir = file_node.get('icm_dir')
      inputfile = file_node.get('type', None)
      if inputfile == 'input':
        inputfile = True
      elif inputfile == 'output':
        inputfile = False
      if checksum == "":
        checksum = False
      filter = file_node.get('filter')
      rcs_disable = file_node.get('rcs_disable', False)
      if filter == "":
        filter = None
      if actual_filepath and future_filepath:
          self.add_requirement_helper(actual_filepath, future_filepath, checksum, filter, rcs_disable, inputfile=inputfile)
      elif run_dir == "":
          self.add_requirement(file_path, checksum, filter, disable_rcs_filtering=rcs_disable, inputfile=inputfile)
      else:
          self.add_relocated_requirement(file_path, run_dir, icm_dir, checksum, filter, rcs_disable, inputfile=inputfile)

  def _transfer_results(self, audit):
    """
    Transfer all result data from audit_tcl.xml to the AuditFile API.
    """

    for result_node in audit.findall('results/result'):
      name = result_node.get('text')
      passed = result_node.get('failure')
      severity = result_node.get('severity')
      if passed == 'pass':
        passed = True
      else:
        passed = False
      self.add_result(name, passed, severity)

  def _transfer_records(self, audit):
    """
    Transfer all data from audit_tcl.xml to the AuditFile API.
    """

    for data_node in audit.findall('data/record'):
      name = data_node.get('tag')
      value = data_node.get('text')
      self.add_data(name, value)

  def from_xml(self, xml):
    """
    Builds an AuditFile object from xml string.
    Calls the appropriate methods of AuditFile to build the in-memory object.
    """

    try:
        audit = ET.fromstring(xml)
    except:
        print("Error Parsing xml string:")
        print(xml)
        raise

    # Extract the workspace_rootdir from the audit_tcl.xml
    # since that is required to construct a AuditFile object.
    environment_node = audit.find('environment')
    workspace_rootdir = environment_node.get('workspace_rootdir')

    # Construct a AuditFile object
    super(AuditFileTcl, self).__init__(workspace_rootdir=workspace_rootdir)

    # Overwrite the run_date from now() to the date provided by Tcl
    self.run_date = environment_node.get('run_date')

    # Transfer all flow information from audit_tcl.tcl to the AuditFile API.
    self._transfer_flow_info(audit)

    # Transfer all file requirement data from audit_tcl.xml to the AuditFile API.
    self._transfer_requirements(audit)
    
    # Transfer all result data from audit_tcl.xml to the AuditFile API.
    self._transfer_results(audit)

    # Transfer all data from audit_tcl.xml to the AuditFile API.
    self._transfer_records(audit)

  def load(self, fid):
    """
    Builds an AuditFile object from data read from a file handle.
    """

    xml = fid.read()
    self.from_xml(xml)

  def xfer_file_path(self, output_filepath):
    """
    Creates a file for audit_file.tcl to pick up.
    The location of the file is provided via
    the cmdline so the client can remove it after
    reading it.
    """
    the_path = audit_file_tcl.get_audit_file_path()
    with open(output_filepath,'w') as f:
        f.write(the_path)

#############################################
# Main
#############################################

if __name__ == "__main__":
  # If this file is called as a script, then the use model is
  #   audit.tcl | audit_tcl.py
  # that is, the Tcl audit API will pipe the skeleton audit.xml to this script
  # which will complete the audit file and save it, or just return the path 
  # if the -p option is provided.
  parser = ArgumentParser(description='Audit file Tcl-Python bridge.')
  parser.add_argument('-p', '--path', help='return the path to the audit file instead of saving it')
  parser.add_argument('-d', '--dir', default=None, help='save audit file to this directory instead of the normal location')
  args = parser.parse_args()

  audit_file_tcl = AuditFileTcl()
  audit_file_tcl.load(sys.stdin)
  if args.path:
      audit_file_tcl.xfer_file_path(args.path)
  else:
      audit_file_tcl.save(custom_dir=args.dir)

