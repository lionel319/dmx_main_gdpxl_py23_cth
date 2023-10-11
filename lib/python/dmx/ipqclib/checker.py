#!/usr/bin/env python
"""Checker object"""
from __future__ import print_function
import os
import json
import re
import uuid
import tabulate
from dmx.python_common.uiConfigParser import ConfigObj
from dmx.ipqclib.audit import Audit
from dmx.ipqclib.settings import _FATAL, _IPQC_WRAPPER, _DB_DEVICE
from dmx.ipqclib.utils import memoized, file_accessible, memoize
from dmx.ipqclib.waiver import get_waivers
from dmx.tnrlib.waiver_file import WaiverFile
from dmx.ipqclib.log import uiDebug

@memoize
def get_ipqc_waivers(workspace_path, ip_name, deliverable_name, subflow):
    """get_ipqc_waivers"""
    waivers = []
    waivers_file = os.path.join(workspace_path, ip_name, deliverable_name, "tnrwaivers.csv")
    if file_accessible(waivers_file, os.R_OK):
        for waiver in get_waivers(waivers_file):
            if (waiver[2].match(subflow)) or (waiver[2].match('*')):
                waivers.append(waiver)

    return waivers


#########################################################################
#   All information related to checker
#########################################################################
#class Checker(dmx.ecolib.checker.Checker):
class Checker(object):
    """IPQC Checker object"""
    def __init__(self, workspace_path, workdir, milestone, ip_name, deliverable_name, checker, \
            bom_is_immutable, ipobj=None):
        self._checker = checker
        self._milestones = self._checker.milestones[_DB_DEVICE]
        self._workspace_path = workspace_path
        self._workdir = workdir
        self._milestone = milestone
        self._ip_name = ip_name
        self._deliverable_name = deliverable_name
        self._bom_is_immutable = bom_is_immutable
        self._status = _FATAL
        self._errors_waived = []
        self._errors_unwaived = []
        self._errors_unwaivable = []
        self._nb_subflow = 0
        self._needs_execution = False
        self._name = self._checker.checkname
        self._longname = self._checker.name
        self._errors_waived_file = None
        self._errors_unwaived_file = None
        self._logfile = ''
        self._waived = False
        self._skipped = False
        self._waiver = WaiverFile()
        self._uid = uuid.uuid4()
        self._ipobj = ipobj
        if self._checker.subflow == '':
            self._checker_id = self._checker.flow
        else:
            self._checker_id = self._checker.flow+'_'+self._checker.subflow


        if self._workspace_path != None:
            if self._checker.subflow != "":
                self._waivers_file = os.path.join(workdir, deliverable_name, 'waivers_' + \
                        self._checker.subflow)
            else:
                self._waivers_file = os.path.join(workdir, deliverable_name, 'waivers')

        self._audit = self._get_audit()


        ### Handling: Wrapper Name Override
        filename = os.path.join(os.getenv("DMXDATA_ROOT"), os.getenv("DB_FAMILY"), 'ipqc', 'wrapper_name_override.json')
        try:
            uiDebug("Loading {}".format(filename))
            with open(filename) as f:
                data = json.load(f)
            uiDebug("data:{}".format(data))
            for newname in data[self._checker.wrapper_name]:
                if self._ipobj.iptype in data[self._checker.wrapper_name][newname]['Iptypes']:
                    oldname = self._checker._wrapper_name
                    self._checker._wrapper_name = newname
                    uiDebug("Wrapper name overriden from {} to {}".format(oldname, newname))
        except Exception as e:
            uiDebug("Fail loading override file: {}".format(str(e)))

    def get_cth_setup_cmd(self, envvar):
        '''
        Get cth_setup_cmd without the -x
        '''
        cth_setup_cmd = os.environ.get(envvar)
        match = re.search('(.+) -x .+', cth_setup_cmd)
        if match:
            setup_cmd = match.group(1)
            match_ward = re.search('.*-ward (\S+)?.* ', setup_cmd)
            ward = match_ward.group(1)
            sub_cmd = re.sub(ward, '$PWD', setup_cmd)
            return sub_cmd
        else:
            LOGGER.error('Cannot get cth setup command. Make sure you are inside a CTH environement')

    def __repr__(self):
        return str(self._name)

    def is_waived(self, cellname, config):
        """checker is waived for the given cell"""
        try:
            if bool(config.options[self._checker.wrapper_name][cellname]['Waive']) is True:
                self._waived = True
                return True
        except KeyError:
            return False

        return False

    def is_skipped(self, cellname, config):
        """checker is skipped for the given cell"""
        try:
            if bool(config.options[self._checker.wrapper_name][cellname]['Skip']) is True:
                self._skippeD = True
                return True
        except KeyError:
            return False

        return False


    @property
    def name(self):
        """checker name"""
        return self._name

    @property
    def checker_id(self):
        """checker_id"""
        return self._checker_id

    @property
    def audit(self):
        """audit"""
        return self._audit

    @property
    def nb_subflow(self):
        """nb_subflow"""
        return self._nb_subflow

    @nb_subflow.setter
    def nb_subflow(self, value):
        self._nb_subflow = value

    @property
    def needs_execution(self):
        """needs_execution"""
        return self._checker.needs_execution

    @needs_execution.setter
    def needs_execution(self, value):
        self._checker.needs_execution = value

    @property
    def dependencies(self):
        """dependencies"""
        return self._checker.dependencies

    @property
    def waivers_file(self):
        """waivers_file"""
        return self._waivers_file

    @property
    def status(self):
        """status"""
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def workdir(self):
        """workdir"""
        return self._workdir

    @property
    def ip_name(self):
        """ip_name"""
        return self._ip_name

    @property
    def deliverable_name(self):
        """deliverable_name"""
        return self._deliverable_name

    @property
    def logfile(self):
        """logfile"""
        return self._logfile

    @memoized
    def get_arcparam(self, cellname, config):
        
        options = config.options

        ### Set the options from .ini file
        if self._checker.wrapper_name in options.keys():

            for option, val in options[self._checker.wrapper_name][cellname].items():
                # get Options key from .ini file
                if option == 'Arcparams':
                    return val
        return ''
        

    @memoized
    def get_command(self, cellname, config):
        """wrapper is a wrapper checker name follwing the
            recommandations to this URL:
            https://securewiki.ith.intel.com/display/PSGDMX/Wrapper+checker+naming+convention
        """
        self._logfile = os.path.join(os.path.realpath(self._workdir), self._deliverable_name, \
                'ipqc_' + cellname + '_' + self._checker.wrapper_name)
        if config is None:
            return None

        command = ''

        options = config.options

        if self.has_checker_execution():

            wrapper = {}

            wrapper_file = _IPQC_WRAPPER
            wrapper_dict = ConfigObj(wrapper_file)

            for key, val in wrapper_dict.items():
                val = re.sub('_IPNAME', self._ip_name, val)
                val = re.sub('_CELLNAME', cellname, val)
                val = re.sub('_MILESTONE', self._milestone, val)
                val = re.sub('_WORKDIR', self._workdir, val)
                val = re.sub('_LOGFILE', self._logfile, val)
                val = re.sub('_CHEETAH_PSETUP_PSG', self.get_cth_setup_cmd('CTH_PSETUP_PSG'), val)
                val = re.sub('_CHEETAH_RTL_ROOT', os.environ.get('CHEETAH_RTL_ROOT'), val)
                val = re.sub('_DMXDATA_ROOT', os.environ.get('DMXDATA_ROOT'), val)
                val = re.sub('_DB_FAMILY', os.environ.get('DB_FAMILY'), val)
                wrapper[key] = val

            if self._checker.wrapper_name != None:
                command = wrapper[self._checker.wrapper_name]
            else:
                command = ' '

            ### Set the options from .ini file
            if self._checker.wrapper_name in options.keys():

                for option, val in options[self._checker.wrapper_name][cellname].items():
                    # get Options key from .ini file
                    if option == 'Options':
                        command = command + ' ' + val

            command = command + ' |& tee -a ' + self._logfile

        return command


    # unit test - TO DO
    def has_dependencies(self):
        """has_dependencies"""
        if self.dependencies != '':
            return True
        return False

    def is_run_perip(self):
        if self._checker.checkerlevel == 'ip':
            return True
        return False

    def has_audit_verification(self):
        """has_audit_verification"""
        return self._checker.audit_verification

    def _get_audit(self):
        return Audit(self._workspace_path, self._ip_name, self._deliverable_name, self.checker_id, \
                self._workdir, self._bom_is_immutable)

    def has_checker_execution(self):
        """has_checker_execution"""
        return self._checker.checker_execution

    # unit test - TO DO
    def has_waivers(self):
        """has_waivers"""
        if self.get_waivers() != []:
            return True
        return False


    def get_waivers(self):
        """get_waivers"""
        waivers = get_ipqc_waivers(self._workspace_path, self._ip_name, self._deliverable_name, \
                self._checker.subflow)
        return waivers


    # store waivers for checker
    def record_waivers(self):
        """record waivers in workdir"""
        if self.has_waivers():
            waivers = self.get_waivers()
            lines = []
            with open(self._waivers_file, 'w') as fid:
                for waiver in waivers:
                    lines.append([waiver.reason, self._waiver.from_regex(waiver.error.pattern)])

                print(tabulate.tabulate(lines, headers=['reason', 'error']), file=fid)
        return

    # store the list of errors waived into file
    def record_errors_waived(self, cellname):
        """record errors waived in workdir"""
        if self._errors_waived != []:
            self._errors_waived_file = os.path.join(self._workdir, self._deliverable_name, \
                    'errors_waived_' + cellname + '_' +self.checker_id)
            with open(self._errors_waived_file, 'w') as fid:
                for error_waived in self.errors_waived:
                    print(error_waived.error, file=fid)
        return

    # store the list of remaining errors into file
    def record_errors_unwaived(self, cellname):
        """record errors unwaived in workdir"""
        if (self._errors_unwaived != []) or (self._errors_unwaivable != []):
            self._errors_unwaived_file = os.path.join(self._workdir, self._deliverable_name, \
                    'errors_unwaived_' + cellname + '_' +self.checker_id)

            with open(self._errors_unwaived_file, 'w') as fid:
                for unwaived_error in self._errors_unwaived:
                    print(unwaived_error.error, file=fid, end='\n')
        return

    @property
    def errors_waived(self):
        """errors_waived"""
        return self._errors_waived

    @errors_waived.setter
    def errors_waived(self, value):
        self._errors_waived = value

    @property
    def errors_unwaived(self):
        """errors_unwaived"""
        return self._errors_unwaived

    @errors_unwaived.setter
    def errors_unwaived(self, value):
        self._errors_unwaived = value

    @property
    def errors_unwaivable(self):
        """errors_unwaivable"""
        return self._errors_unwaivable

    @errors_unwaivable.setter
    def errors_unwaivable(self, value):
        self._errors_unwaivable = value

    @property
    def errors_waived_file(self):
        """errors_waived_file"""
        return self._errors_waived_file

    @property
    def errors_unwaived_file(self):
        """errors_unwaived_file"""
        return self._errors_unwaived_file

    @property
    def nb_errors(self):
        """nb_errors"""
        nb_errors = len(self._errors_waived) + len(self._errors_unwaived)
        return nb_errors

    @property
    def wrapper_name(self):
        """wrapper_name"""
        return self._checker.wrapper_name

    @property
    def subflow(self):
        """subflow"""
        return self._checker.subflow

    @property
    def flow(self):
        """flow"""
        return self._checker.flow

    @property
    def milestones(self):
        """milestones"""
        return self._milestones

    @property
    def audit_verification(self):
        """audit_verification"""
        return self._checker.audit_verification

    @property
    def waived(self):
        """waived"""
        return self._waived

    @property
    def skipped(self):
        """skipped"""
        return self._skipped


    @property
    def longname(self):
        """longname"""
        return self._longname

    @property
    def uid(self):
        return str(self._uid)
