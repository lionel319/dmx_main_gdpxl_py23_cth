#!/usr/bin/env python
""" IPQC object
"""
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import json
import datetime
import copy
from operator import attrgetter
from dmx.ipqclib.ip import IP
from dmx.ipqclib.utils import file_accessible, run_command, get_catalog_paths, memoized, \
         RedirectStdStreams
from dmx.ipqclib.log import uiInfo, uiError, uiDebug, uiInfoStars
from dmx.ipqclib.settings import _PASSED, _FAILED, _FATAL, _NA, _WARNING, \
        _ALL_WAIVED, _UNNEEDED, _NA_MILESTONE, _IMMUTABLE_BOM, _DB_FAMILY, _REL, _SION, _VIEW
from dmx.ipqclib.workspace import Workspace
from dmx.ipqclib.pre_dry_run import pre_dry_run
from dmx.ecolib.ecosphere import EcoSphere
from dmx.ipqclib.ipqc_utils import get_ip_changelist,  \
        ipqc_close_cell_files, ipqc_close_cell_files_checkin, ipqc_print_files, ipqc_close_file, \
        ipqc_scripts_dm_deliverable, ipqc_open_file, ipqc_open_cell_files, \
        ipqc_add_files_not_in_depot, easy_parallelize_ipqc, easy_parallelize_data_prep, \
        easy_parallelize, get_results
from dmx.ipqclib.options import INITFILE, WORKSPACE_TYPE, SENDMAIL
from dmx.ipqclib.ipqcException import IPQCDryRunException


########################################################################################
# IPQC Documentation Object
########################################################################################
class IPQC(object):
    '''
    The IPQC object contains all top IP information (cells, deliverables, checkers, hierarchy).

    Args:
        milestone (str):
        ip (str):
        cellname (list):
        deliverables (list):
        initfile (path):
        mode (str):
        output_dir (path):
        sendmail (bool):


    Attributes:
    '''
    def __init__(self, milestone, ip, project=None, cellname=[], deliverables=[], \
                mode=None, output_dir=None, no_clientname=False, workspace=None, \
                requalify=False, depth=0, no_hierarchy=False, top=True, checkin=False, \
                no_revert=False, exclude_ip=[], ciw=False, report_template=_VIEW, ip_filter=[], \
                options={}, checkers_to_run='*'):
        self.date = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        self._cellname = cellname
        self._deliverables = deliverables
        self._milestone = milestone
        self._project = project
        self._mode = mode
        self._output_dir = output_dir
        self.sendmail = options[SENDMAIL] if SENDMAIL in options.keys() else False
        self._no_clientname = no_clientname
        self._requalify = requalify
        self._revert_file = None
        self._depth = depth
        self._hierarchy = []
        self._top_hierarchy = []
        self._top = top
        self._checkin = checkin
        self._no_revert = no_revert
        self._exclude_ip = exclude_ip
        self._ciw = ciw
        self._workspace_type = options[WORKSPACE_TYPE] if WORKSPACE_TYPE in options.keys() \
                               else 'icmanage'
        self._initial_exclude_ip = exclude_ip
        self._workspace = workspace
        self._environment = None
        self._scripts_revert = []
        self._scripts_checkin = []
        self._scripts_checkout = []
        self._all_checkin_scripts = []
        self._all_checkout_scripts = []
        self._all_revert_scripts = []
        self._cache = False
        self._ipenv = ip
        self._include_ip = []
        self._parents = []
        self._record_file = None
        self._report_template = report_template
        self._ip_filter = ip_filter
        self._options = options
        self._checkers_to_run = checkers_to_run

        if self._workspace_type == _SION:
            self._sync_cache = True
        else:
            self._sync_cache = False


        if (INITFILE in options.keys()) and (options[INITFILE] != None):
            self._initfile = os.path.realpath(options[INITFILE])
        else:
            self._initfile = None

        self._no_hierarchy = no_hierarchy
        self._ip = None
        self.lsf_job_list = []

        if len(ip.split('@')) > 1:
            self.ipname = ip.split('@')[0]
            self._bom = ip.split('@')[1]
        else:
            self.ipname = ip
            self._bom = None

        if self._no_hierarchy is True:
            self._all = False
        else:
            self._all = True

        ####################
        # Checkers Execution
        ####################
        if (self._mode == "run-all") or (self._mode == "setup") or (self._mode is None):
            if self._top is True:
                self._workspace = self._get_workspace()
            self._bom = self._workspace.get_project_bom(self.ipname)[1]

            if self._bom.startswith(_IMMUTABLE_BOM) and (self._top is True) and \
                (self._requalify is False):

                nfs_path = get_catalog_paths(self.ipname, self._bom, self._milestone)[1]
                if file_accessible(os.path.realpath(os.path.join(nfs_path, 'ipqc.html')), os.F_OK):
                    self._cache = True
                    self._record_file = os.path.realpath(os.path.join(nfs_path, 'ipqc.json'))
                    return


        #####################################################################
        # FB488992
        # For immutable config, populate only the snapped files (if found)
        # and pull checker status from them
        # For mutable config, populate all files as checksum may need files
        # located in other IPs, topcells, deliverables.
        #####################################################################
        elif self._mode == "dry-run":

            # user specified a bom
            if self._bom is not None:
                if self._bom.startswith(_IMMUTABLE_BOM):
                    if self._requalify is False:
                        nfs_path = get_catalog_paths(self.ipname, self._bom, self._milestone)[1]

                        if not file_accessible(os.path.realpath(os.path.join(nfs_path, \
                                        'ipqc.html')), os.F_OK):
                            self._workspace = self._get_workspace()

                            if self._top is True:
                                if self._bom.startswith(_REL):
                                    deliverable = 'ipspec'
                                    uiDebug("IPQC - Sync IPSPEC")
                                    self._workspace.sync(variants='*', libtypes=[deliverable], \
                                            force=True, sync_cache=self._sync_cache)

                                    ### Check in audit files if deliverable BOM is immutable

                                    pattern = '*/*/audit/...'
                                    uiDebug("IPQC - Sync audit")
                                    self._workspace.sync(variants='*', libtypes='*', \
                                    specs=[pattern], sync_cache=self._sync_cache)

                                    pattern = '*/*/tnrwaivers.csv'
                                    uiDebug("IPQC - Sync TNR waivers")
                                    self._workspace.sync(variants='*', libtypes='*', \
                                    specs=[pattern], sync_cache=self._sync_cache)
                                else:
                                    if self._top is True:
                                        uiDebug("IPQC - Sync snap")
                                        self._workspace.sync(skeleton=False, \
                                        sync_cache=self._sync_cache)
                                        uiDebug("IPQC - End Sync snap")
                                os.chdir(self._workspace.path)

                    # requalification mode
                    else:
                        self._workspace = self._get_workspace()

                        if self._top is True:
                            os.chdir(self._workspace.path)
                            self._workspace.sync(skeleton=False, sync_cache=self._sync_cache)
                else:
                    if self._top is True:
                        self._workspace = self._get_workspace()
                        self._workspace.sync(variants='*', libtypes='*', force=True, \
                        sync_cache=self._sync_cache)
                        os.chdir(self._workspace.path)

            # in workspace
            else:
                self._workspace = self._get_workspace()
                self._bom = self._workspace.get_project_bom(self.ipname)[1]

            if self._bom.startswith(_IMMUTABLE_BOM) and (self._top is True) and \
                (self._requalify is False):

                nfs_path = get_catalog_paths(self.ipname, self._bom, self._milestone)[1]
                if file_accessible(os.path.realpath(os.path.join(nfs_path, 'ipqc.html')), os.F_OK):
                    self._cache = True
                    self._record_file = os.path.realpath(os.path.join(nfs_path, 'ipqc.json'))
                    return

            if self._bom.startswith(_IMMUTABLE_BOM) and (self._requalify is False):
                nfs_path = get_catalog_paths(self.ipname, self._bom, self._milestone)[1]
                if file_accessible(os.path.realpath(os.path.join(nfs_path, 'ipqc.html')), os.F_OK):
                    uiInfo(">>> Dashboard already computed for IP {}: {}" \
                    .format(self.ipname, nfs_path))
                    self._cache = True



    def __repr__(self):
        return 'ipqc_'+str(self.ipname)


    #############################
    ### Workspace initialization
    #############################
    def _get_workspace(self):
        if self._bom is not None:
            workspace = Workspace(self.ipname, bom=self._bom, project=self._project, ignore_clientname=self._no_clientname)
            os.chdir(workspace.path)
        else:
            workspace = Workspace(self.ipname)
            os.chdir(workspace.path)

        return workspace

    #############################
    ### IP initialization
    #############################
    def init_ip(self):
        """ init_ip method to create IP object. IP object creates also a ocllection of objects:
                cell(s), deliverable(s), checker(s), ...
            init_ip is consuming time because of the object creations. This method is called only
            if the dashboard generation is necessary.
        """
        # Do not remove this line otherwise it does not recognize workspace path and fail
        os.chdir(self._workspace.path)
        #### WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
        #### BIG BIG DISCLAIMER - do not never ever move the lines between WARNING comments.
        #### EcoSphere is very sensitive to where it is instanciate and can break IPQC !!!
        ecosphere = EcoSphere()
        self._family = ecosphere.get_family(_DB_FAMILY)
        #### WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING

        self._ip = IP(self._workspace, self.ipname, self._milestone, self._family, project=self._project, bom=self._bom, \
                initfile=self._initfile, output_dir=self._output_dir, cell_list=self._cellname, \
                deliverable_list=self._deliverables, top=self._top, cache=self._cache, \
                requalify=self._requalify, ciw=self._ciw, report_template=self._report_template, checkers_to_run=self._checkers_to_run)


        # Get hierarchy for top IP
        if (self._top is True) and (self._no_hierarchy is False):
            self._hierarchy = self.get_hierarchy(self._ip_filter)

            if (self._mode == "run-all") or (self._mode == "setup"):

                self.set_needs_checkers_execution()

                # make all IP dont_touch per default
                # then compute IPs that really need to be excluded.
                dont_touch = [self._ip.name] + list(self._ip.flat_hierarchy)

                for i in self._initial_exclude_ip:

                    if i in dont_touch:
                        index = dont_touch.index(i)
                        dont_touch.pop(index)

                exclude_all = copy.deepcopy(self._initial_exclude_ip)

                for ipname in self._initial_exclude_ip:

                    sub_ipqc = self.get_ipqc(ipname)

                    if sub_ipqc is None:
                        continue

                    exclude_all = exclude_all + sub_ipqc.ip.flat_hierarchy

                tmp_exclude = copy.deepcopy(self._initial_exclude_ip)
                to_not_exclude = []

                for s_ipqc in sorted(self._hierarchy, key=attrgetter('depth')):
                    ipname = s_ipqc.ip.name
                    hier = self._ip.hierarchy[ipname]

                    for i in exclude_all:

                        if i in self._initial_exclude_ip:
                            continue

                        if (ipname not in self._initial_exclude_ip) and not(ipname in tmp_exclude) \
                            and (i in hier):
                            to_not_exclude.append(i)

                        if (ipname not in self._initial_exclude_ip) and (ipname in to_not_exclude) \
                            and (i in hier):
                            to_not_exclude.append(i)

                        if (ipname in self._initial_exclude_ip) and (i in hier) and (i != ipname):
                            tmp_exclude.append(i)

                        if (ipname in tmp_exclude) and (i in hier) and (i != ipname):
                            tmp_exclude.append(i)

                for ip in to_not_exclude: #pylint: disable=invalid-name
                    if ip in exclude_all:
                        index = exclude_all.index(ip)
                        exclude_all.pop(index)


                to_keep = list(set(dont_touch) - set(exclude_all))
                self._exclude_ip = list(set(exclude_all))

                for ipname in self._exclude_ip:
                    if not ipname in to_keep:
                        continue

                    index = self._exclude_ip.index(ipname)
                    self._exclude_ip.pop(index)


            for sub_ipqc in [self] + self._hierarchy:
                for ip in sub_ipqc.ip.flat_hierarchy: #pylint: disable=invalid-name
                    if self.get_ipqc(ip) is None:
                        continue
                    sub_ipqc.top_hierarchy = sub_ipqc.top_hierarchy + [self.get_ipqc(ip)]


        # Data preparation
        if (self._mode is not None) and (self._workspace is not None) and (self._top is True):
            if (self._mode == "run-all") or (self._mode == "setup"):
                hier = [self] + self.hierarchy
                for sub_ipqc in hier:
                    if sub_ipqc.ip.config_err is not None:


                        if sub_ipqc.ip.name in self.exclude_ip:
                            uiError(sub_ipqc.ip.config_err)
                            continue


            uiInfo("")
            uiInfo("-----------------------------------------------------------------")
            uiInfo("Data preparation for {}" .format(self._ip.name))
            uiInfo("-----------------------------------------------------------------")
            uiInfo("")
            easy_parallelize_data_prep([self] + self._hierarchy)
        return

    def set_needs_checkers_execution(self):
        """If the IP dashboard is already computed, it is not necessary to re-run the checkers.
        """
        if self._ip.bom.startswith(_IMMUTABLE_BOM) and (self._requalify is False):
            self._ip.needs_execution = False
            return

        for cell in self._ip.topcells:
            for deliverable in cell.deliverables:
                if deliverable.bom.startswith(_IMMUTABLE_BOM) and (self._requalify is False):
                    deliverable.needs_checkers_execution = False
        return

    def _get_deliverables_waived(self):

        try:
            uiDebug("dry_run >>> get deliverable waivers for {}" .format(self._ip.name))
            self._ip.workspace.check(self._ip.name, self._milestone, os.getenv("DB_THREAD"), \
                    deliverable=None, nowarnings=True, validate_deliverable_existence_check=True, \
                    validate_type_check=False, validate_checksum_check=False, \
                    validate_result_check=False, validate_goldenarc_check=False, \
                    familyobj=self._ip.family)
        except Exception as err:
            self._ip.err = err
            raise IPQCDryRunException(err)

        # for each topcell in IP, set the deliverables that are waived
        for cell in self._ip.topcells:

            for deliverable in cell.deliverables:

                if (self._deliverables != []) and (not deliverable.name in self._deliverables):
                    continue

                deliverable.deliverable_existence = \
                self._ip.workspace.get_deliverable_existence_errors(deliverable=deliverable.name)
                if deliverable.deliverable_existence['waived'] != []:
                    deliverable.is_waived = True
                    deliverable.status = _ALL_WAIVED
                    deliverable_ip = self._ip.get_deliverable_ipqc(deliverable.name)
                    deliverable_ip.is_waived = True
                    deliverable_ip.status = _ALL_WAIVED

    def _run_wokspace_check(self):
        for deliverable_ip in self._ip.deliverables:

            if (self._deliverables != []) and not deliverable_ip.name in self._deliverables:
                continue

            if (deliverable_ip.err != '') or (deliverable_ip.bom == '') or \
                        (deliverable_ip.status == _NA_MILESTONE) or (deliverable_ip.is_unneeded):
                continue

            validate_checksum_check = True
            validate_type_check = True

            if deliverable_ip.bom.startswith(_REL) and (self._requalify is False):
                validate_checksum_check = False
                validate_type_check = False

            uiDebug("dry_run >>>  run workspace check for  {} - {}" \
                    .format(self._ip.name, deliverable_ip.name))
            self._ip.workspace.check(self._ip.name, self._milestone, os.getenv("DB_THREAD"), \
                    deliverable=deliverable_ip.name, nowarnings=True, \
                    validate_deliverable_existence_check=False, \
                    validate_type_check=validate_type_check, \
                    validate_checksum_check=validate_checksum_check, \
                    validate_result_check=True, \
                    validate_goldenarc_check=False, familyobj=self._ip.family)

            for cell in self._ip.topcells:

                for deliverable in cell.deliverables:

                    if deliverable.name != deliverable_ip.name:
                        continue

                    # if BOM is REL, run result check only
                    if (deliverable.is_immutable) and (deliverable_ip.bom.startswith(_REL)) and \
                        (self._requalify is False):
                        deliverable.errors_waived = deliverable.errors_waived + \
                                                    self._ip.workspace.get_result_errors()['waived']
                        deliverable.errors_unwaived = deliverable.errors_unwaived + \
                                                self._ip.workspace.get_result_errors()['unwaived']
                    # if BOM is mutable or snap, run type check, result check and checksum
                    #    verification
                    else:
                        deliverable.errors_waived = deliverable.errors_waived + \
                                                    self._ip.workspace.errors['waived']
                        deliverable.errors_unwaived = deliverable.errors_unwaived + \
                                                      self._ip.workspace.errors['unwaived']

                    # Get unwaivable errors
                    deliverable.errors_unwaivable = deliverable.errors_unwaivable + \
                                            self._ip.workspace.get_unwaivable_errors()['unwaived']



    @pre_dry_run
    def dry_run(self):
        """ dry-run API
            Run workspace check.
            1/ check if deliverable are waived
            2/ run workspace check on each deliverable to compute deliverable status
            3/ set the status at IP, cell/deliverable, checker level
            Workspace check API is very limited, slow, doing mutiple times the same task,
                cannot run deliverables in parallel and needs to be run into 2 steps:
                    to get deliverables waived
                    to run workspace check on the deliverable that are not waived
        """
        # if ip contains error return because won't be able to run workspace.check for that IP
        if self._ip.err != '':
            return

        #####################################################################
        # FB522867
        # cd into workspace root
        # needs to be at workspace root to run:
        #   --> workspace.check to get deliverables waived
        #   --> workspace.check on each deliverable (type/data/context checks)
        #####################################################################
        os.chdir(self._workspace.path)

        # Check at IP level - get deliverable waived information
        # Set ip.err if an error occurs
        try:
            self._get_deliverables_waived()
        except IPQCDryRunException as err:
            uiError(err)

        # Check at deliverable level - data check and context check
        self._run_wokspace_check()

        # Set the status
        results = get_results(self._ip)
        self._ip.set_status(status_list=[])
        self._record_status()

        return results


    def get_hierarchy(self, ip_filter):
        """Get IPQC objects hierarchy for the top.
        """
        hierarchy_ip = []

        if self._no_hierarchy is True:
            return hierarchy_ip

        uiInfo(">> IPQC OBJECT {} {}" .format(self._ip.name, self._ip.boms))
        if self._ip.boms:
            devnull = open(os.devnull, 'w')
            with RedirectStdStreams(stdout=devnull, stderr=devnull):
                hierarchy_ip = easy_parallelize_ipqc(self, self._ip.boms, ip_filter, self._checkers_to_run)

        return hierarchy_ip


    def set_status_from_record(self, record_file):
        """Set status from ipqc.record to keep trace of the
            process run. Updates when new run.
        """
        from dmx.ipqclib.ipqc_utils import set_deliverable_status_from_record
        checkers_status = []

        with open(record_file, 'r') as fid:
            ip_data = json.load(fid)

        for cell, cell_values in ip_data.items():

            if cell == 'summary':
                #pylint: disable=invalid-name,line-too-long
                results = {\
                    "passed": [_PASSED] * int(ip_data[cell]["number_of_tests"]["passed"]), \
                    "failed": [_FAILED] * int(ip_data[cell]["number_of_tests"]["failed"]), \
                    "fatal": [_FATAL] * int(ip_data[cell]["number_of_tests"]["fatal"]), \
                    "na": [_NA] * int(ip_data[cell]["number_of_tests"]["na"]), \
                    "waived": [_WARNING] * int(ip_data[cell]["number_of_tests"]["warning"]), \
                    "unneeded": [_UNNEEDED] * int(ip_data[cell]["number_of_tests"]["unneeded"]) \
                }
                checkers_status = results["passed"] + results["failed"] + results["fatal"] + \
                    results["na"] + results["waived"] + results["unneeded"]
                #pylint: enable=invalid-name,line-too-long
                continue

            if isinstance(cell_values, dict):
                for deliverable, deliverable_values in cell_values.items():
                    set_deliverable_status_from_record(self.ip, deliverable, deliverable_values)


        self._ip.set_status(status_list=checkers_status)

        return ip_data

    def _record_status(self):
        """Generates ipqc.json to record checkers status
        """
        ip_data = {}
        ip_data['summary'] = {}
        ip_data['summary']['url'] = self._ip.report_url
        ip_data['summary']['command'] = self.environment.cmd
        ip_data['summary']['ip'] = self._ip.name
        ip_data['summary']['workspace'] = self._ip.workspace.path
        ip_data['summary']['project'] = '{} ({})' .format(self._ip.project, self._ip.family.name)
        ip_data['summary']['release'] = self._ip.bom
        ip_data['summary']['milestone'] = self._ip.milestone
        ip_data['summary']['number_of_topcells'] = len(self._ip.topcells)
        ip_data['summary']['number_of_deliverables'] = len(self._ip.deliverables)
        ip_data['summary']['number_of_tests'] = {}
        ip_data['summary']['number_of_tests']['total'] = self._ip.nb_pass + self._ip.nb_fail + \
            self._ip.nb_fatal + self._ip.nb_warning + self._ip.nb_unneeded+ self._ip.nb_na
        ip_data['summary']['number_of_tests']['passed'] = self._ip.nb_pass
        ip_data['summary']['number_of_tests']['failed'] = self._ip.nb_fail
        ip_data['summary']['number_of_tests']['fatal'] = self._ip.nb_fatal
        ip_data['summary']['number_of_tests']['warning'] = self._ip.nb_warning
        ip_data['summary']['number_of_tests']['unneeded'] = self._ip.nb_unneeded
        ip_data['summary']['number_of_tests']['na'] = self._ip.nb_na


        for cell in self._ip.topcells:

            uiInfo("")
            uiInfo("Storing {} data into {}" .format(cell.name, cell.record_file))

            data = {}
            data[cell.name] = {'status': cell.status}

            for deliverable in cell.deliverables:
                data[cell.name][deliverable.name] = {'status': deliverable.status}
                for checker in deliverable.checkers:
                    data[cell.name][deliverable.name][checker.wrapper_name] = \
                        {'status': checker.status}

            if not file_accessible(cell.record_file, os.F_OK):
                if not os.path.exists(os.path.dirname(cell.record_file)):
                    os.makedirs(os.path.dirname(cell.record_file))
                with open(cell.record_file, 'w') as fid:
                    json.dump(data, fid, indent=4)

            ip_data[cell.name] = data[cell.name]


        with open(self._ip.record_file, 'w') as f_ip:
            json.dump(ip_data, f_ip, indent=4)


    def add_files_not_in_depot(self):
        """ If files defined in the manifest is not in the ICM depot, submit files in the depot.
        """
        uiDebug("DEBUG RUNTIME ADD FILE NOT IN DEPOT --> Begin {}" \
                .format(datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S'))) # pylint: disable=C0301
        for sub_ipqc in [self] + self._hierarchy:
            if (sub_ipqc.ip.is_immutable and self._requalify is False) or \
                    (sub_ipqc.ip.name in self.exclude_ip):
                continue

            for deliverable in sub_ipqc.ip.deliverables:

                if deliverable.is_immutable or not deliverable.needs_checkers_execution:
                    continue

                patterns = deliverable.get_patterns()

                if patterns != []:
                    ipqc_add_files_not_in_depot(patterns, sub_ipqc.ip.name)

        uiDebug("DEBUG RUNTIME ADD FILE NOT IN DEPOT --> End {}" \
                .format(datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S'))) # pylint: disable=C0301

    #########################################################
    # Checkout action for files based on deliverable manifest
    #########################################################
    def checkout(self, checkin_only_pass=False):
        """Check out data when non requlify mode.
        """
        uiInfo("")
        uiInfoStars(msg="Checkout files:")
        uiInfo("DEBUG RUNTIME CHECKOUT --> Begin {}" \
                .format(datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S'))) # pylint: disable=C0301
        # create revert file script if user wants to revert check-outed files
        (f_revert, self._revert_file) = ipqc_open_file(self._workspace.path, self._ip.workdir, \
                'ipqc_revert')
        (f_checkin, _checkin_file) = ipqc_open_file(self._workspace.path, self._ip.workdir, \
                'ipqc_checkin')
        (f_checkout, _checkout_file) = ipqc_open_file(self._workspace.path, self._ip.workdir, \
                'ipqc_checkout')

        flag = {"ip": None, "cell": None, "global": None, "revert": None}
        
        ### Added by Lionel. CICQ needs this because some files are not checked-in.
        self._all_checkin_scripts.append(_checkin_file)

        for sub_ipqc in [self] + self._hierarchy:

            flag["ip"] = 0

            if (sub_ipqc.ip.is_immutable and self._requalify is False) or \
                    (sub_ipqc.ip.name in self.exclude_ip):
                continue

            if not(sub_ipqc.ip.is_immutable) and (self._requalify is False):
                sub_ipqc.ip.changelist = get_ip_changelist(sub_ipqc)

            # begin for cell loop
            flag["cell"] = 0
            flag["global"] = 0

            for cell in sub_ipqc.ip.topcells:

                flag["revert"] = False

                if (self._cellname == []) and (checkin_only_pass is False):
                    cellname = 'all'
                else:
                    cellname = cell.name
                    flag["cell"] = 0

                if flag["cell"] != 0:
                    continue

                if flag["cell"] == 0:
                    # checkout per topcell
                    cell_checkout = ipqc_print_files(sub_ipqc.ip.name, cellname, self._ip.workdir, \
                            "checkout")
                    # revert per topcell
                    cell_revert = ipqc_print_files(sub_ipqc.ip.name, cellname, self._ip.workdir, \
                            "revert")
                    # checkin per topcell
                    cell_checkin = ipqc_print_files(sub_ipqc.ip.name, cellname, self._ip.workdir, \
                            "checkin")
                else:
                    cell_checkout = ipqc_open_cell_files(sub_ipqc.ip.name, cellname, \
                            self._ip.workdir, "checkout")
                    # revert per topcell
                    cell_revert = ipqc_open_cell_files(sub_ipqc.ip.name, cellname, \
                            self._ip.workdir, "revert")
                    # checkin per topcell
                    cell_checkin = ipqc_open_cell_files(sub_ipqc.ip.name, cellname, \
                            self._ip.workdir, "checkin")

                for deliverable in cell.deliverables:

                    if not deliverable.needs_checkers_execution:
                        continue

                    flag["revert"] = ipqc_scripts_dm_deliverable(sub_ipqc, cellname, deliverable, \
                            self._requalify, cell_checkout[1], cell_checkin[1], cell_revert[1], \
                            flag["revert"])

                self._scripts_checkout = ipqc_close_cell_files(cell_checkout[1], cell_checkout[0], \
                        self._scripts_checkout)
                self._scripts_revert = ipqc_close_cell_files(cell_revert[1], cell_revert[0], \
                        self._scripts_revert)
                flag["ip"] = ipqc_close_cell_files_checkin(sub_ipqc, cell_checkin[1], \
                        cell_checkin[0], self._ip.workdir, flag["ip"], self._ip.is_immutable)
                flag["cell"] = 1

                ### Added by Lionel. CICQ needs this because some files are not checked-in.
                self._all_checkin_scripts.append(cell_checkin[0])

        # end for cell loop
        ipqc_close_file(f_revert, self._revert_file)
        ipqc_close_file(f_checkin, _checkin_file)
        self._scripts_checkin.append(_checkin_file)
        ipqc_close_file(f_checkout, _checkout_file)
                
        os.chdir(self._workspace.path)
        easy_parallelize(self._scripts_checkout)
        uiDebug("DEBUG RUNTIME CHECKOUT --> End {}" .format(datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S'))) # pylint: disable=C0301

        uiDebug("self._scripts_checkout: {}".format(self._scripts_checkout))
        uiDebug("self._scripts_revert: {}".format(self._scripts_revert))
        uiDebug("self._scripts_checkin: {}".format(self._scripts_checkin))
        uiDebug("self._all_checkin_scripts: {}".format(self._all_checkin_scripts))

        return

    #######################################################
    # Revert files that were previously checked-out by ipqc
    #######################################################
    def revert(self):
        """Revert files at the end of the run except if --no-revert is invoked.
        """
        uiInfo("DEBUG RUNTIME REVERT FILES --> Begin {}" .format(datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S'))) # pylint: disable=C0301
        uiInfo("-------------")
        uiInfo("Revert files:")
        uiInfo("-------------")
        os.chdir(self._workspace.path)
        easy_parallelize(self._scripts_revert)

        if not(self._ip.is_immutable) and (self._requalify is False):

            for sub_ipqc in [self] + self._hierarchy:

                if sub_ipqc.ip.changelist is None:
                    continue

                uiInfo("Deleting changelist {} for IP {}" .format(sub_ipqc.ip.changelist, \
                            sub_ipqc.ip.name))
                (code, out) = run_command('xlp4 change -d {}' .format(sub_ipqc.ip.changelist))
                if code != 0:
                    uiError(out)
                else:
                    uiInfo(out)
        uiInfo("DEBUG RUNTIME REVERT FILES --> End {}" .format(datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S'))) # pylint: disable=C0301


    def check_in(self):
        """Check-in checker files when non requalify mode, BOM is mutable and --check-in option
            is invoked.
        """
        from dmx.ipqclib.ipqc_utils import revert_files_failed_deliverable
        uiInfo("--------------")
        uiInfo("Checkin files:")
        uiInfo("--------------")
        os.chdir(self._workspace.path)

        if not(self._ip.is_immutable) and (self._requalify is False):

            for sub_ipqc in [self] + self._hierarchy:

                for cell in sub_ipqc.ip.topcells:

                    for deliverable in cell.deliverables:

                        if deliverable.status != _FATAL:
                            continue

                        uiInfo("Checkers failed for {} {} {}. Reverting files." \
                                .format(sub_ipqc.ip.name, cell.name, deliverable.name))
                        revert_files_failed_deliverable(sub_ipqc.ip.changelist, cell, \
                                deliverable)


        easy_parallelize(self._scripts_checkin)

    def check_in_only_pass(self):
        """ If option --check-in-only-pass is invoked for run-all sub-command, check-in files for
            deliverables which passed the checks.
        """
        from dmx.ipqclib.ipqc_utils import revert_audit_files
        #pylint: disable=line-too-long
        uiInfo("----------------------------------------------------------------------------------------")
        uiInfo("Checkin files only for cells that have passed or passed with waivers status for checkers")
        uiInfo("----------------------------------------------------------------------------------------")
        #pylint: enable=line-too-long

        for sub_ipqc in [self] + self._hierarchy:

            if (sub_ipqc.ip.is_immutable and self._requalify is False) or \
                (sub_ipqc.ip.name in self.exclude_ip):
                continue

            for deliverable in sub_ipqc.ip.deliverables:

                if deliverable.bom.startswith(_IMMUTABLE_BOM) or (deliverable.status == _PASSED) \
                    or (deliverable.status == _WARNING):
                    continue

                flag_d = 0
                files_to_check_out = []

                for cell in sub_ipqc.ip.topcells:
                    for deliverable_cell in cell.deliverables:

                        if deliverable_cell.name != deliverable.name:
                            continue

                        files_to_check_out = files_to_check_out + \
                                             deliverable_cell.get_manifest(cell.name)[0]

                    if flag_d == 0:
                        revert_audit_files(sub_ipqc, deliverable)
                        flag_d = 1

                for filename in sorted(files_to_check_out, key=lambda file: \
                        (os.path.dirname(file), os.path.basename(file))):
                    uiInfo("Reverting {}" .format(filename))
                    (code, out) = run_command('xlp4 revert {}' .format(filename))
                    if code != 0:
                        uiError(out)
                    else:
                        uiInfo(out)



    @memoized
    def get_ipqc(self, ipname):
        """ Get IPQC object for the given IP.
        """
        if self.hierarchy != []:
            for sub_ipqc in self.hierarchy:
                if sub_ipqc.ip.name == ipname:
                    return sub_ipqc
        else:
            for sub_ipqc in self.top_hierarchy:
                if sub_ipqc.ip.name == ipname:
                    return sub_ipqc

        return None


    @property
    def family(self):
        '''Get the family name.'''
        return self._family

    @property
    def ip(self): # pylint: disable=C0103
        '''Get the IP object.'''
        return self._ip

    @property
    def milestone(self):
        '''Get the milestone.'''
        return self._milestone

    @property
    def deliverables(self):
        '''Get the list of deliverables.'''
        return self._deliverables

    @property
    def cells(self):
        '''Get the list of cells name.'''
        return self._cellname

    @property
    def requalify(self):
        '''Requalify mode is True or False.'''
        return self._requalify

    @property
    def bom(self):
        '''BOM version of the IP under qualification.'''
        return self._bom

    @property
    def exclude_ip(self):
        '''List of IP exclude from --exclude-ip options.'''
        return list(set(self._exclude_ip))

    @exclude_ip.setter
    def exclude_ip(self, value):
        self._exclude_ip = value

    @property
    def exclude(self):
        """List if exclude IPs"""
        return list(set(self._exclude))

    @exclude.setter
    def exclude(self, value):
        self._exclude = value

    @property
    def include_ip(self):
        """List of IPs to remain"""
        return list(set(self._include_ip))

    @include_ip.setter
    def include_ip(self, value):
        self._include_ip = value

    @property
    def hierarchy(self):
        '''List of IPQC objects for all levels of the top IP.'''
        return self._hierarchy

    @hierarchy.setter
    def hierarchy(self, value):
        self._hierarchy = value

    @property
    def top_hierarchy(self):
        '''List of IPQC object for 1st level of the top IP.'''
        return self._top_hierarchy

    @top_hierarchy.setter
    def top_hierarchy(self, value):
        self._top_hierarchy = value

    @property
    def depth(self):
        '''Hierarchy level of the IP.'''
        return self._depth

    @property
    def no_hierarchy(self):
        '''Consider only top level if --no-hierarchy.'''
        return self._no_hierarchy

    @property
    def output_dir(self):
        '''Output directory to store all information related to IPQC execution.'''
        return self._output_dir

    @property
    def mode(self):
        '''IPQc mode - dry-run, run-all, ...'''
        return self._mode

    @property
    def top(self):
        '''Return True IP is top else return False.'''
        return self._top

    @property
    def environment(self):
        '''Environment information - OS, hostname, ...'''
        return self._environment

    @environment.setter
    def environment(self, value):
        self._environment = value

    @property
    def workspace(self):
        '''Workspace object.'''
        return self._workspace

    @property
    def parents(self):
        '''List of parents IP'''
        return self._parents

    @parents.setter
    def parents(self, value):
        self._parents = value

    @property
    def initfile(self):
        '''IPQC init file.'''
        return self._initfile

    @property
    def checkin(self):
        '''If --check-in option is invoked, check-in checkers files (audt, log, ...).'''
        return self._checkin

    @property
    def no_revert(self):
        '''If --no-revert option is invoked, do not revert the files.'''
        return self._no_revert

    @property
    def cache(self):
        """Set to True if dashboard is already cached"""
        return self._cache

    @property
    def ipenv(self):
        """IP information for Environment object"""
        return self._ipenv

    @property
    def initial_exclude_ip(self):
        """Initial of IPs that are excluded"""
        return self._initial_exclude_ip

    @property
    def ciw(self):
        '''If --ciw is invoked, parse the IPQC init file and remove all blocking options in \
                checker options.
                For more info see - https://wiki.ith.intel.com/display/tdmaInfra/--ciw+option
        '''
        return self._ciw

    @property
    def report_template(self):
        """Report template value - --report-template switch."""
        return self._report_template

    @property
    def sync_cache(self):
        """If user invoked --workspace-type set to sion, use sync_cache population method."""
        return self._sync_cache

    @property
    def options(self):
        """IPQC options"""
        return self._options
