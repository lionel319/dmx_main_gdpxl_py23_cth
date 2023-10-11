#!/usr/bin/env python
# pylint: disable-msg=C0103
# pylint: disable-msg=R0911
# pylint: disable-msg=R0913
# pylint: disable-msg=W0102
# pylint: disable-msg=R0902
"""cell.py"""
import os
from joblib import Parallel, delayed
from dmx.ipqclib.deliverable import Deliverable
from dmx.ipqclib.settings import _FAILED, _FATAL, _NA, _WARNING, _CHECKER_SKIPPED, _PASSED, _ALL_WAIVED, _UNNEEDED, \
        _NA_MILESTONE
from dmx.ipqclib.log import uiDebug


def get_deliverable_object(workspace_path, workdir, deliverable_name, ip, milestone, bom, project, \
        requalify, all_deliverables, unneeded_deliverables, checkers_to_run=None):
    """get_deliverable_object"""
    deliverable = Deliverable(workspace_path, workdir, deliverable_name, ip, milestone, bom, \
            project, requalify, checkers_to_run)
    if not deliverable.name in all_deliverables:
        deliverable.status = _NA_MILESTONE
        # deliverable is unneeded - marked as unneeded
    elif deliverable.name in unneeded_deliverables:
        deliverable.is_unneeded = True

    return deliverable


def easy_parallelize_deliverables(workspace_path, workdir, ip, milestone, bom, \
        project, requalify, all_deliverables, unneeded_deliverables, my_list, checkers_to_run=None):
    """easy_parallelize_deliverables"""
    results = []
    results = Parallel(n_jobs=len(my_list), \
            backend="threading")(delayed(get_deliverable_object)(workspace_path, workdir, \
            deliverable_name, ip, milestone, bom, project, requalify, all_deliverables, \
            unneeded_deliverables, checkers_to_run) for deliverable_name in my_list)
    return results


class Cell(object):
    """Cell"""
    def __init__(self, family, workspace_path, workdir, name, ip_name, milestone, bom, project, \
            deliverable_list=[], requalify=False, functionality=None, checkers_to_run=None):
        self._workspace_path = workspace_path
        self._workdir = workdir
        self._ip = family.get_ip(ip_name, project_filter=project)
        self._ipname = self._ip.name
        self._name = name
        self._ip_type = self._ip.iptype
        self._status = _FATAL
        self._nb_fail = 0
        self._nb_pass = 0
        self._nb_fatal = 0
        self._nb_warning = 0
        self._nb_unneeded = 0
        self._nb_nc = 0
        self._flow = None
        self._milestone = milestone
        self._needs_execution = False
        self._bom = bom
        self._project = project
        self._cell = self._ip.get_cell(self._name)
        self._deliverable_list = list(deliverable_list)
        self._requalify = requalify
        self._functionality = functionality
        self._checkers_to_run = checkers_to_run
        self._deliverables = self._get_ipqc_deliverables()
        if self._workdir != None:
            self.record_file = os.path.join(self._workdir, 'ipqc_'+self._name+'.record')

        self._nb_checkers = 0
        for deliverable in self._deliverables:
            self._nb_checkers = self._nb_checkers + deliverable.nb_checkers

    def __repr__(self):
        return str(self._name)

    @property
    def workdir(self):
        """workdir"""
        return self._workdir
    @property
    def milestone(self):
        """milestone"""
        return self._milestone

    @property
    def deliverables(self):
        """deliverable"""
        return self._deliverables

    def _get_ipqc_deliverables(self):

        deliverables_list = []

        if self._workspace_path != None:
            bom = None
            local = True
        else:
            bom = self._bom
            local = False

        # Unneeded deliverable for topcell
        if local is False:
            unneeded_deliverables = [deliverable.name for deliverable in \
                    self._cell.get_unneeded_deliverables(bom=bom, local=local)]
        else:
            unneeded_deliverables = [deliverable.name for deliverable in \
                    self._cell.get_unneeded_deliverables()]

        # Deliverable for topcell for the given milestone
        all_deliverables = [deliverable.name for deliverable in \
                self._cell.get_all_deliverables(milestone=self._milestone)]

        if self._deliverable_list == []:
            deliverables = [deliverable.name for deliverable in self._cell.get_all_deliverables()]
        else:
            deliverables = []
            for deliverable_name in self._deliverable_list:
                deliverables.append(deliverable_name)



        if len(self._ip.get_cells_names()) > 100:
            deliverables_list = easy_parallelize_deliverables(self._workspace_path, self._workdir, \
                    self._ip, self._milestone, self._bom, self._project, \
                    self._requalify, all_deliverables, unneeded_deliverables, deliverables, self._checkers_to_run)
        else:
            for deliverable in deliverables:
                uiDebug(">>> Cell object {} - deliverable {}" .format(self.name, deliverable))
                deliverable_obj = get_deliverable_object(self._workspace_path, self._workdir, \
                        deliverable, self._ip, self._milestone, self._bom, self._project, \
                        self._requalify, all_deliverables, unneeded_deliverables, self._checkers_to_run)
                deliverables_list.append(deliverable_obj)

        return deliverables_list

    @property
    def nb_checkers(self):
        """nb_checkers"""
        return self._nb_checkers

    @property
    def status(self):
        """status"""
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    def set_status(self):
        """set_status"""
        self._status = self.get_status()

    # if cell is in the list provided by the user, run the checkers associated
    @property
    def needs_execution(self):
        """needs_execution"""
        return self._needs_execution

    @needs_execution.setter
    def needs_execution(self, value):
        self._needs_execution = value

    def get_status(self):
        """get_status"""
        status_list = []

        for deliverable in self._deliverables:
            status_list.append(deliverable.status)

        if _FATAL in status_list:
            return _FATAL

        if _FAILED in status_list  or (_CHECKER_SKIPPED in status_list):
            return _FAILED

        if (_WARNING in status_list) or (_ALL_WAIVED in status_list):
            return _WARNING

        if _PASSED in status_list:
            return _PASSED

        if _UNNEEDED in status_list:
            return _UNNEEDED

        if _NA in status_list:
            return _NA

        if _NA_MILESTONE in status_list:
            return _NA_MILESTONE

        return self._status

    @property
    def nb_fail(self):
        """nb_fail"""
        return self._nb_fail

    @nb_fail.setter
    def nb_fail(self, value):
        self._nb_fail = value

    @property
    def nb_unneeded(self):
        """nb_unneeded"""
        return self._nb_unneeded

    @nb_unneeded.setter
    def nb_unneeded(self, value):
        self._nb_unneeded = value

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
    def nb_nc(self):
        """b_nc"""
        return self._nb_nc

    @nb_nc.setter
    def nb_nc(self, value):
        self._nb_nc = value

    @property
    def flow(self):
        """flow"""
        return self._flow

    @flow.setter
    def flow(self, value):
        self._flow = value

    @property
    def name(self):
        """name"""
        return self._name

    # get deliverable object per name
    def get_deliverable(self, deliverable_name):
        """get_deliverable"""
        for deliverable in self._deliverables:
            if deliverable.name == deliverable_name:
                return deliverable

        return None

    @property
    def functionality(self):
        """functionality"""
        return self._functionality
