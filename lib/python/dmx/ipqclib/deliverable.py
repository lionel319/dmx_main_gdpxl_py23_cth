#!/usr/bin/python env
# pylint: disable-msg=R0904
# pylint: disable-msg=R0911
# -*- coding: utf-8 -*-
"""
Deliverable object
"""
import os
import shutil
from operator import attrgetter
from dmx.ipqclib.checker import Checker
from dmx.ipqclib.utils import file_accessible, is_non_zero_file, get_bom, memoize, memoized, \
        process_filepath
from dmx.ipqclib.settings import _FAILED, _CHECKER_SKIPPED, _FATAL, _NA, _WARNING, _PASSED, _ALL_WAIVED, \
        _CHECKER_WAIVED, _UNNEEDED, _NA_MILESTONE, _DB_DEVICE, _IMMUTABLE_BOM
from dmx.ipqclib.log import uiInfo, uiDebug

@memoize
def get_deliverable(ipobj, name):
    """get_deliverable"""
    return ipobj.get_deliverable(name, roadmap=_DB_DEVICE)


#########################################################################
#   All information related to deliverable
#########################################################################
class Deliverable(object):
    """
    Deliverable class
    """
    def __init__(self, workspace_path, workdir, name, ip, milestone, bom, project, requalify, checkers_to_run='*'):
        self._status = _FATAL
        self._workspace_path = workspace_path
        self._workdir = workdir
        self._name = name
        self._ip = ip
        self._ip_name = self._ip.name
        self._milestone = milestone
        self._ip_bom = bom
        self._project = project
        self._requalify = requalify
        self._is_waived = False
        self._report = None
        self._owner = ''
        self._view = ''
        self._err = ''
        self._errors_waived = []
        self._errors_unwaived = []
        self._errors_unwaivable = []
        self._deliverable_existence = {'waived': [], 'unwaived': []}
        self._is_unneeded = False
        self._bom = None
        self._waivers = None
        self._checkers_to_run = checkers_to_run

        if self._workspace_path != None:
            self._waivers_file = os.path.join(self._workspace_path, self._ip_name, self._name, \
                    "tnrwaivers.csv")
        else:
            self._waivers_file = None

        self._bom = get_bom(self._project, self._ip_name, self._ip_bom, self._name)
        if self._bom == '':
            self._err = '{} is required by the roadmap, but not included in the IP configuration.' \
                    .format(self._name)


        self._is_immutable = self._bom.startswith(_IMMUTABLE_BOM)

        self._deliverable = get_deliverable(self._ip, self._name)
        self._checkers = self.ipqc_get_checkers(self._deliverable)

        if self._checkers == []:
            self._status = _NA


        self._nb_fail = 0
        self._nb_pass = 0
        self._nb_fatal = 0
        self._nb_warning = 0
        self._nb_unneeded = 0
        self._nb_na = 0

        list_name = [checker.name for checker in self._checkers]
        for checker in self._checkers:
            i = list_name.count(checker.name)
            checker.nb_subflow = i
        self._needs_checkers_execution = False

        for checker in self._checkers:
            i = list_name.count(checker.name)
            checker.nb_subflow = i
            if checker.has_checker_execution() is True:
                self._needs_checkers_execution = True


    def __repr__(self):
        return str(self._name)


    def get_check_info(self):
        """get_check_info"""
        nb_passed = 0
        nb_failed = 0
        nb_fatal = 0
        nb_waived = 0
        nb_unneeded = 0
        nb_na = 0


        if (self.status == _NA_MILESTONE) or self.is_waived:
            return (nb_passed, nb_failed, nb_fatal, nb_waived, nb_unneeded, nb_na)

        for checker in self._checkers:

            if self.is_unneeded:
                nb_unneeded = nb_unneeded + 1
                continue

            if checker.status == _FAILED or checker.status == _CHECKER_SKIPPED:
                nb_failed = nb_failed + 1
                continue

            if checker.status == _PASSED:
                nb_passed = nb_passed + 1
                continue

            if checker.status == _FATAL:
                nb_fatal = nb_fatal + 1
                continue

            if (checker.status == _WARNING) or (checker.status == _CHECKER_WAIVED):
                nb_waived = nb_waived + 1
                continue

            if checker.status == _NA:
                nb_na = nb_na + 1
                continue

        return (nb_passed, nb_failed, nb_fatal, nb_waived, nb_unneeded, nb_na)


    def ipqc_get_checkers(self, deliverable):
        """
        get the list of checkers contained into the deliverable
        """
        checkers_list = []
        checkers = deliverable.get_checkers(iptype_filter="^" + str(self._ip.iptype) + "$")
        for checker in checkers:
            c = Checker(self._workspace_path, self._workdir, self._milestone, \
                    self._ip_name, self.name, checker, self._is_immutable, ipobj=self._ip)

            ## if '*', run all, else compare with self._checkers_to_run
            if self._checkers_to_run != '*':
                if c.wrapper_name not in self._checkers_to_run:
                    c._skipped = True

            checkers_list.append(c)

        return sorted(checkers_list, key=attrgetter('wrapper_name'))


    def _set_checkers_errors(self, cellname):

        for checker in self._checkers:
            for err in  self.errors_waived:
                if (err.topcell == cellname) and (err.libtype == self._name) and \
                        (err.flow == checker.flow) and ((err.subflow == checker.subflow) or \
                        (err.subflow == 'type')):
                    checker.errors_waived.append(err)

            for err in  self.errors_unwaived:
                if (err.topcell == cellname) and (err.libtype == self._name) and \
                        (err.flow == checker.flow) and ((err.subflow == checker.subflow) or \
                        (err.subflow == 'type')):
                    checker.errors_unwaived.append(err)

            for err in  self.errors_unwaivable:
                if (err.topcell == cellname) and (err.libtype == self._name) and \
                        (err.flow == checker.flow) and ((err.subflow == checker.subflow) or \
                        (err.subflow == 'type')):
                    checker.errors_unwaivable.append(err)

            checker.record_errors_waived(cellname)
            checker.record_errors_unwaived(cellname)

        return

    def get_status(self, cellname):
        """
        iterate on checkers. If one of the checkers is
            failed/fatal, return failed/fatal. If they all passed
            return passed.
        If deliverable has neither checker execution nor audit
            verification, return NA.
        """
        status_checkers = []

        if self._status == _NA_MILESTONE:
            for checker in self._checkers:
                checker.status = _NA_MILESTONE
            return _NA_MILESTONE

        # if deliverable is waived return _ALL_WAIVED status
        if self.is_waived is True:
            self._status = _ALL_WAIVED

            for checker in self._checkers:
                checker.status = _ALL_WAIVED

            return _ALL_WAIVED


        if self._status == _NA:
            for checker in self._checkers:
                checker.status = _NA
            (self._nb_pass, self._nb_fail, self._nb_fatal, self._nb_warning, self._nb_unneeded, \
                    self._nb_na) = self.get_check_info()
            return self._status

        if self.is_unneeded is True:
            for checker in self._checkers:
                checker.status = _UNNEEDED
            self._status = _UNNEEDED
            (self._nb_pass, self._nb_fail, self._nb_fatal, self._nb_warning, self._nb_unneeded, \
                    self._nb_na) = self.get_check_info()
            return self._status


        # if deliverable existence is not waived return fatal
        if self.deliverable_existence['unwaived'] != []:
            self._status = _FATAL
            (self._nb_pass, self._nb_fail, self._nb_fatal, self._nb_warning, self._nb_unneeded, \
                    self._nb_na) = self.get_check_info()
            return _FATAL

        if self._err != '':
            self._status = _FATAL
            (self._nb_pass, self._nb_fail, self._nb_fatal, self._nb_warning, self._nb_unneeded, \
                    self._nb_na) = self.get_check_info()
            return _FATAL


        # if deliverable has no checkers return _NA status
        if self._checkers == []:
            self._status = _NA
            (self._nb_pass, self._nb_fail, self._nb_fatal, self._nb_warning, self._nb_unneeded, \
                    self._nb_na) = self.get_check_info()
            return _NA

        # set the status for checkers in deliverable
        self._set_checkers_errors(cellname)

        for checker in self._checkers:
            if not self._milestone in checker.milestones:
                status_checkers.append(_NA)
                checker.status = _NA
            elif not checker.has_checker_execution() and not checker.has_audit_verification():
                status_checkers.append(_NA)
                checker.status = _NA
            elif (checker.skipped is True):
                status_checkers.append(_CHECKER_SKIPPED)
                checker.status = _CHECKER_SKIPPED
            elif checker.errors_unwaivable != []:
                status_checkers.append(_FATAL)
                checker.status = _FATAL
            elif (checker.waived is True) or (checker.audit.has_file(cellname) and \
                    checker.audit.is_filelist(checker.audit.get_file(cellname)) and \
                    not is_non_zero_file(checker.audit.get_file(cellname))):
                status_checkers.append(_WARNING)
                checker.status = _WARNING
            elif checker.errors_unwaived != []:
                status_checkers.append(_FAILED)
                checker.status = _FAILED
            elif checker.errors_waived != []:
                status_checkers.append(_WARNING)
                checker.status = _WARNING
            elif checker.errors_waived == []:
                status_checkers.append(_PASSED)
                checker.status = _PASSED
            else:
                status_checkers.append(_FATAL)
                checker.status = _FATAL

        (self._nb_pass, self._nb_fail, self._nb_fatal, self._nb_warning, self._nb_unneeded, \
                self._nb_na) = self.get_check_info()

        if _FATAL in status_checkers:
            self._status = _FATAL
            return _FATAL

        if _FAILED in status_checkers:
            self._status = _FAILED
            return _FAILED

        if _CHECKER_SKIPPED in status_checkers:
            self._status = _FAILED
            return _FAILED

        if _WARNING in status_checkers:
            self._status = _WARNING
            return _WARNING

        if _PASSED in status_checkers:
            self._status = _PASSED
            return _PASSED

        if _NA in status_checkers:
            self._status = _NA
            return _NA

        return self._status


    def get_audit_files(self, cellname):
        """
        return list of audit files if checker has audit
        else return empty list
        """
        list_of_audit_file = []

        if cellname == 'all':
            if (self._is_immutable) or (self._requalify is True):
                filepath = '{}/{}/audit/*' .format(self._ip_name, self._name)
            else:
                filepath = '{}/{}/audit/...' .format(self._ip_name, self._name)
            return [filepath]

        for checker in self._checkers:
            if checker.has_audit_verification() and checker.has_checker_execution() and \
                    checker.audit.has_file(cellname):
                for filepath in checker.audit.get_files(cellname):
                    list_of_audit_file.append(os.path.relpath(filepath))
        return list_of_audit_file

    @memoized
    def get_manifest(self, cellname):
        """get_manifest"""
        file_list = []
        design_files_list = []

        patterns = self._deliverable.get_patterns(ip=self._ip_name)

        for filepath, attributes in patterns.items():
            ##################################################################################
            # http://pg-rdjira:8080/browse/DI-1262 - support "generated" attribute in manifest
            # Wharfrock project supported "generated" attribute in manifest
            # Other projects do not support "generated"
            # This is why it needs exception
            ##################################################################################
            try:
                if attributes['generated'] is True:
                    file_list = process_filepath(filepath, cellname, file_list)
                else:
                    design_files_list = process_filepath(filepath, cellname, design_files_list)
            except KeyError:
                file_list = process_filepath(filepath, cellname, file_list)

        return (file_list, design_files_list)

    def get_patterns(self):
        """Get patterns from manifest.json in dmxdata for the given family.
        """
        file_list = []

        patterns = self._deliverable.get_patterns(ip=self._ip_name)

        for filepath in patterns.keys():
            file_list = process_filepath(filepath, "all", file_list)

        return file_list


    def has_waivers(self):
        """
        return True if deliverable has waivers
        """
        if file_accessible(self._waivers_file, os.R_OK):
            return True
        return False

    def record_waivers(self):
        """record_waivers"""
        if self.has_waivers():
            shutil.copyfile(os.path.join(self._waivers_file), os.path.join(self._workdir, \
                    self._name, 'tnrwaivers.csv'))
        return


    def remove_checker(self, checker):
        """remove_checker"""
        for chk in self._checkers:
            if chk.wrapper_name == checker.wrapper_name:
                i = self._checkers.index(chk)
        chk = self._checkers.pop(i)
        uiInfo("removing {}" .format(chk.wrapper_name))


    def get_checker(self, dependency=None):
        """ return checker
        """
        for checker in self._checkers:
            var = checker.flow + '_' + checker.subflow
            if not checker.subflow:
                var = checker.flow
            if var == dependency:
                return checker

        return None

    @property
    def checkers(self):
        """checkers"""
        return self._checkers

    # returns number of checkers contained into the deliverable
    @property
    def nb_checkers(self):
        """nb_checkers"""
        return len(self._checkers)

    @property
    def bom(self):
        """bom"""
        return self._bom

    @bom.setter
    def bom(self, value):
        self._bom = value

    @property
    def is_immutable(self):
        """is_immutable"""
        return self._is_immutable

    @property
    def status(self):
        """status"""
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def needs_checkers_execution(self):
        """needs_checkers_execution"""
        return self._needs_checkers_execution

    @needs_checkers_execution.setter
    def needs_checkers_execution(self, value):
        self._needs_checkers_execution = value


    # waivers file at deliverable level
    @property
    def waivers_file(self):
        """waivers_file"""
        if self.has_waivers() is True:
            return self._waivers_file

        return _NA

    @property
    def nb_fail(self):
        """nb_fail"""
        return self._nb_fail

    @nb_fail.setter
    def nb_fail(self, value):
        self._nb_fail = value

    @property
    def nb_pass(self):
        """nb_pass"""
        return self._nb_pass

    @nb_pass.setter
    def nb_pass(self, value):
        self._nb_pass = value

    @property
    def nb_fatal(self):
        """nb_fatal"""
        return self._nb_fatal

    @nb_fatal.setter
    def nb_fatal(self, value):
        self._nb_fatal = value


    @property
    def nb_warning(self):
        """nb_warning"""
        return self._nb_warning

    @nb_warning.setter
    def nb_warning(self, value):
        self._nb_warning = value

    @property
    def nb_unneeded(self):
        """nb_unneeded"""
        return self._nb_unneeded

    @nb_unneeded.setter
    def nb_unneeded(self, value):
        self._nb_unneeded = value

    @property
    def nb_na(self):
        """nb_na"""
        return self._nb_na

    @nb_na.setter
    def nb_na(self, value):
        self._nb_na = value

    @property
    def is_waived(self):
        """is_waived"""
        return self._is_waived

    @is_waived.setter
    def is_waived(self, value):
        self._is_waived = value

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
    def deliverable_existence(self):
        """deliverable_existence"""
        return self._deliverable_existence

    @deliverable_existence.setter
    def deliverable_existence(self, value):
        self._deliverable_existence = value

    @property
    def is_unneeded(self):
        """is _unneeded"""
        return self._is_unneeded

    @is_unneeded.setter
    def is_unneeded(self, value):
        self._is_unneeded = value

    @property
    def err(self):
        """err"""
        return self._err

    @err.setter
    def err(self, value):
        self._err = value

    @property
    def waivers(self):
        """waivers"""
        return self._waivers

    @waivers.setter
    def waivers(self, value):
        self._waivers = value

    @property
    def name(self):
        """name"""
        return self._name

    @property
    def owner(self):
        """owner"""
        return self._owner

    @owner.setter
    def owner(self, value):
        self._owner = value

    # return the status of the checker
    @property
    def report(self):
        """report"""
        return self._report

    @report.setter
    def report(self, value):
        self._report = value

    @property
    def view(self):
        """view"""
        return self._view

    @view.setter
    def view(self, value):
        self._view = value
