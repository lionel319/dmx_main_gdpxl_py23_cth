#!/usr/bin/env python
"""Utilities commands that can are used in IPQC"""
# -*- coding: utf-8 -*-

# $Id: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/ipqclib/utils.py#1 $
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/ipqclib/utils.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Change: 7411538 $
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/ipqclib/utils.py $
# $Revision: #1 $
# $Author: lionelta $

import os
import sys
import shutil
import functools
import subprocess
import re
import glob
import errno
from collections import defaultdict
from dmx.utillib.configobj import ConfigObj
from dmx.ipqclib.ipqcException import PermissionError
from dmx.ipqclib.log import uiInfo, uiError, uiCritical
from dmx.ipqclib.settings import (_REL, _SNAP, _DB_FAMILY, _DB_DEVICE, _FUNC_FILE, _FATAL, \
        _FAILED, _WARNING, _PASSED, _ALL_WAIVED, _UNNEEDED, _NA, _NA_MILESTONE, _ICMANAGE)
from dmx.ecolib.family import Family
import dmx.abnrlib.icm


def check_icm_ticket(workspace_type):
    """Check if ICM user license has expired"""
    if workspace_type != _ICMANAGE:
        return

    pattern = 'Perforce password (P4PASSWD) invalid or unset.'
    cmd = 'xlp4 -u {} login -s' .format(os.environ['USER'])
    (code, out) = run_command(cmd)
    if (code != 0) or (pattern in out):
        uiError(out)
        uiCritical('You need to run icm_login command to log on ICManage')

# http://code.activestate.com/recipes/578231-probably-the-fastest-memoization-decorator-in-the-/
def memoize(func):
    """ Memoization decorator for a function taking one or more arguments. """
    class Memodict(dict):
        """memo dict object"""
        def __getitem__(self, *key):
            return dict.__getitem__(self, key)

        def __missing__(self, key):
            ret = self[key] = func(*key)
            return ret

    return Memodict().__getitem__


@memoize
def get_bom(project, ip_name, input_bom, deliverable_name):
    """Get BOM function"""
    from dmx.dmxlib.bom import BOM

    boms = BOM.get_bom(project, ip_name, input_bom)

    for bom in boms.contents():
        pattern = r"(\S+)/{}:{}@(\S+)" .format(re.escape(ip_name), re.escape(deliverable_name))
        match = re.search(pattern, str(bom))
        if match != None:
            bom = match.group(2)
            return bom
    return ''

@memoize
def get_projects(family):
    """Get projects from family"""
    return [project.name for project in family.get_icmprojects()]

@memoize
def get_family():
    """Get family"""
    return Family(_DB_FAMILY)

@memoize
def get_roadmap(family):
    """Get roadmap for a given family"""
    return family.get_roadmap(_DB_DEVICE)

@memoize
def get_milestones():
    """Get milestones for a given device"""
    family = get_family()
    return  [m.name for m in family.get_roadmap(_DB_DEVICE).get_milestones()]

@memoize
def get_ip_types():
    """Get IP types"""
    family = get_family()
    return [ip_type.name for ip_type in family.get_iptypes()]


#########################################################
# which command
# A minimal version of the UNIX which utility, in Python.
# Return full-path if found, None if not found.
#########################################################
def which(name):
    """which unix-like function"""
    for path in os.getenv("PATH").split(os.path.pathsep):
        full_path = path + os.sep + name
        if os.path.exists(full_path):
            return full_path

    return None

#########################################################
# file_accessible
# Check if a file exists and is accessible.
#########################################################
def file_accessible(filename, access):
    """Check the filename is accessible with the given access permission"""
    if (filename != None) and (os.path.isfile(filename) and os.access(filename, access)):
        return True

    return False

#########################################################
# is_non_zero_file
# Check if a file exists and is empty.
#########################################################
def is_non_zero_file(filename):
    """Return True if the file is not empty"""
    if file_accessible(filename, os.R_OK) and (os.path.getsize(filename) > 0):
        return True

    return False

#########################################################
# remove_file
# Remove a file if it exists.
#########################################################
def remove_file(filename):
    """Remove the file"""
    if file_accessible(filename, os.W_OK):
        os.remove(filename)

    return

#########################################################
# dir_accessible
# Check if a directory exists and is accessible.
#########################################################
def dir_accessible(path, access):
    """Return True if the path is accessible with the given access permission"""
    if (os.path.isdir(path) and os.access(path, access)):
        return True

    return False

#########################################################
# move
# Move source folder to target folder
#########################################################
def move(root_src_dir, root_target_dir):
    """move unix-like function"""
    for src_dir, dirs, files in os.walk(root_src_dir): # pylint: disable=unused-variable
        dst_dir = src_dir.replace(root_src_dir, root_target_dir)

        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)

        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            shutil.move(src_file, dst_dir)

#########################################################
# copy
# copy source folder to target folder
#########################################################
def copy(src, dest):
    """copy unix-like function"""
    try:
        shutil.copytree(src, dest)
    except OSError as err:
        # If the error was caused because the source wasn't a directory
        if err.errno == errno.ENOTDIR:
            shutil.copy(src, dest)
        else:
            uiError('Directory not copied. Error: %s' % err)


#########################################################
# rm_dir
# Delete a directory
#########################################################
def remove_dir(path):
    """remove directory unix-like function"""
    if not os.path.isdir(path):
        return

    try:
        if not dir_accessible(path, os.W_OK):
            raise PermissionError
    except PermissionError:
        uiCritical("No permission. Can't delete the folder {}." .format(path))

    shutil.rmtree(path)



#########################################################
# Run command
#   -> display in the console
#   -> print in the log file
#########################################################
def run(cmd):
    """Execute command and display output in the console"""
    process = subprocess.Popen(cmd, shell=True, universal_newlines=True, stdout=subprocess.PIPE, \
            stderr=subprocess.STDOUT)

    while process.poll() is None:
        try:
            line = process.stdout.readline().rstrip().encode('utf-8', 'ignore')
            uiInfo(line.decode('utf-8'))
        except UnicodeDecodeError:
            continue

    return process.returncode


def run_command(cmd, input_data=None):
    """Execute command and capture the output in a buffer"""
    process = subprocess.Popen(cmd, bufsize=1, shell=True, universal_newlines=True, \
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    (stdout, stderr) = process.communicate(input_data) # pylint: disable=unused-variable
    exitstatus = process.returncode

    return (exitstatus, stdout)


def cat(filename):
    """cat unix-like command"""
    fid = open(filename, "r")
    text = fid.read()
    uiInfo(text)
    fid.close()
    return

#########################################################
# Get tools path and version
#   -> return a dict containing the name of the tool
#       and the path of the tool
#########################################################
def get_tools(ip): # pylint: disable=invalid-name
    """Get list of tools"""
    tools = {}

    for check in ip.checkers_list:
        tools[check.name] = which(check.name)

    tools['ipqc'] = which('ipqc')

    return tools


class memoized(object): # pylint: disable=invalid-name, too-few-public-methods
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        import collections
        if not isinstance(args, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]

        value = self.func(*args)
        self.cache[args] = value
        return value

    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__

    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)


def replace(pattern, string, html):
    """Replace function for HTML content"""
    # escape slash
    pattern = pattern.replace(r'/', r'\/')

    # put the http prefix to be accessible on windows
    match = re.findall('href=(%s)' % pattern, html)
    if match:
        for i in match:
            html = html.replace(i, string)

    return html

def get_catalog_paths(ipname, ipbom, milestone, deliverable=None):
    """Get IPQC catalog path"""
    data = ConfigObj(os.path.join(os.getenv('DMXDATA_ROOT'), _DB_FAMILY, 'ipqc', 'settings.ini'))

    if deliverable is None:
        if ipbom.startswith(_REL) or ipbom.startswith('PREL'):
            key = 'rel'
        elif ipbom.startswith(_SNAP):
            key = 'snap'

        path = os.path.join(ipname, milestone, key, ipbom)

        url_path = os.path.join(data[key]['url'], path)

        if os.getenv("IPQC_TEST") == 1:
            nfs_path = os.path.join(data[key]['test_nfs'], path)
        else:
            nfs_path = os.path.join(data[key]['nfs'], path)

    else:
        if deliverable.bom.startswith(_REL) or ipbom.startswith('PREL'):
            key = 'rel'
        elif deliverable.bom.startswith(_SNAP):
            key = 'snap'

        path = os.path.join(ipname, milestone, deliverable.name, key, deliverable.bom)
        url_path = os.path.join(data[key]['url'], path)

        if os.getenv("IPQC_TEST") == 1:
            nfs_path = os.path.join(data[key]['test_nfs'], path)
        else:
            nfs_path = os.path.join(data[key]['nfs'], path)


    return(url_path, nfs_path)

#########################################################
# Get percentage of a number
#########################################################
def percentage(part, total):
    """Translate part in percentage"""
    return round(100 * float(part)/float(total), 2)


def dsum(*dicts):
    """Dictionary sum operation"""
    ret = defaultdict(int)
    for dictionary in dicts:
        for k, values in dictionary.items():
            ret[k] += values
    return dict(ret)

@memoized
def get_functionality_file_data():
    """When --template-report is functionality, it needs to get the IP function from a config
        file
    """
    data = ConfigObj(_FUNC_FILE)
    return data

@memoized
def get_ipqc_info(family):
    """Get the IPQC settings from dmxdata for the given family"""
    ipqc_info = ConfigObj(os.path.join(os.getenv('DMXDATA_ROOT'), family.lower().title(), \
                'ipqc', 'settings.ini'))
    return ipqc_info


class RedirectStdStreams(object): # pylint: disable=too-few-public-methods
    """Redirect stdout, stderr"""
    def __init__(self, stdout=None, stderr=None):
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr
        self.old_stdout = None
        self.old_stderr = None

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush()
        self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush()
        self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

def get_dependent_checker(deliverable, dependency):
    """Checker dependency"""
    for checker in deliverable.checkers:
        if dependency == (checker.flow+'_'+checker.subflow):
            return checker
    return None


def get_status_for_deliverable(status): # pylint: disable=too-many-return-statements
    """Get status for the deliverable"""
    if _NA_MILESTONE in status:
        return _NA_MILESTONE
    elif _ALL_WAIVED in status:
        return _ALL_WAIVED
    elif _NA in status:
        return _NA
    elif _UNNEEDED in status:
        return _UNNEEDED
    elif _FATAL in status:
        return _FATAL
    elif _FAILED in status:
        return _FAILED
    elif _WARNING in status:
        return _WARNING
    elif _PASSED in status:
        return _PASSED

    return _NA



def process_filepath(filepath, cellname, file_list):
    """Replace * and cellname from files in manifest"""
    new_filepath = filepath
    cell_pattern = re.compile('cell_name')


    if cellname != 'all':
        new_filepath = re.sub(cell_pattern, cellname, filepath)
    else:
        new_filepath = re.sub(cell_pattern, '*', filepath)


    # File path contains wildcard.
    # Need to expand wildcard and get the list of files
    if bool(new_filepath.count('*')):
        for filename in glob.iglob(new_filepath):
            if file_accessible(filename, os.R_OK) and not os.path.relpath(filename) in file_list:
                file_list.append(os.path.relpath(filename))
        return file_list

    # File path contains ...
    # Need to expand ... and get the list of files
    if bool(new_filepath.count('...')):
        (path, files) = os.path.split(new_filepath)
        extension = files[3:]

        for root, dirs, filenames in os.walk(path): # pylint: disable=unused-variable
            for filename in filenames:
                if filename.endswith(extension):
                    pathname = os.path.join(root, filename)

                    if not os.path.relpath(pathname) in file_list:
                        file_list.append(os.path.relpath(pathname))
        return file_list

    file_list.append(new_filepath)

    return file_list


@memoize
def get_deliverable_owner(project, ipname, deliverable, config):
    """get_deliverable_owner"""
    icm = dmx.abnrlib.icm.ICManageCLI()
    [library, release] = icm.get_library_release_from_libtype_config(project, ipname, deliverable, config)
    data = icm.get_library_details(project, ipname, deliverable, library)
    return data.get('Owner', '')

    '''
    (code, out) = run_command("pm propval -l {} {} {} {} | grep Owner" .format(project, \
            ipname, deliverable, config))
    if code != 0:
        (code, out) = run_command("pm propval -l {} {} {} {} -C | grep Owner" .format(project, \
                ipname, deliverable, config))
        if code != 0:
            uiError(out)
            return ''
        else:
            out = out.strip()
            lines = out.split()
            for line in lines:
                if line.find("Value=") != -1:
                    match = re.search(r'Value="(\S+)"', line)
                    if match:
                        owner = match.group(1)
                        return owner
    else:
        out = out.strip()
        lines = out.split()
        for line in lines:
            if line.find("Value=") != -1:
                match = re.search(r'Value="(\S+)"', line)
                if match:
                    owner = match.group(1)
                    return owner
    return ''
    '''

def get_status_from_record(ipqc):
    """ This function is called if dashboard is already cached. Save runtime.
    """
    import json
    results = []
    variables = {}

    (variables["url_path"], variables["nfs_path"]) = \
        get_catalog_paths(ipqc.ipname, ipqc.bom, ipqc.milestone)
    url_report = os.path.join(variables["url_path"], 'ipqc.html')
    nfs_report = os.path.join(variables["nfs_path"], 'ipqc.html')
    record_file = os.path.realpath(os.path.join(variables["nfs_path"], 'ipqc.json'))

    if not file_accessible(record_file, os.F_OK):
        return (None, url_report, nfs_report)

    with open(record_file, 'r') as fid:
        ip_data = json.load(fid)

    for cell, cell_values in ip_data.items():

        if (cell == 'summary') or not isinstance(cell_values, dict):
            continue

        for deliverable, deliverable_values in cell_values.items():
            if not isinstance(deliverable_values, dict):
                continue

            for checker, checker_values in deliverable_values.items():
                if not isinstance(checker_values, dict):
                    continue

                results.append([cell, deliverable, checker, checker_values["status"]])

    return (results, url_report, nfs_report)

@memoized
def load_logs():
    """get the list of DA checkers logfile"""
    logs_file = os.path.join(os.getenv("DMXDATA_ROOT"), _DB_FAMILY, 'ipqc', 'logs.ini')
    data = {}

    if file_accessible(logs_file, os.R_OK):
        data = ConfigObj(logs_file)

    return data

def check_if_result_clean(results):
    """Take list of list anc check if the list contain any fail message"""
    if results:
        for result in results:
            if result[-1] == 'completed and failed' or result[-1] == 'needs to be executed': 
                return 1
    else:
        return 1
    return 0

