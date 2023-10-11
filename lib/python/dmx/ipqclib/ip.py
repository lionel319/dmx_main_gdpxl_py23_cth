#!/usr/bin/env python
# pylint: disable-msg=C0301
"""ip.py"""
# -*- coding: utf-8 -*-

# $Id: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/ipqclib/ip.py#1 $
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/ipqclib/ip.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Change: 7411538 $
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/ipqclib/ip.py $
# $Revision: #1 $
# $Author: lionelta $


import re
import os
import datetime
import json
import traceback
from pprint import pprint
from joblib import Parallel, delayed
from dmx.ecolib.ecosphere import EcoSphere
from dmx.ipqclib.log import uiWarning, uiError, uiCritical, uiDebug
from dmx.ipqclib.cell import Cell
from dmx.ipqclib.utils import dir_accessible, file_accessible, remove_dir, run_command, get_bom, \
        get_deliverable_owner
from dmx.ipqclib.settings import _FAILED, _FATAL, _PASSED, _WARNING, _CHECKER_SKIPPED, _CHECKER_WAIVED, _ALL_WAIVED, \
        _NA, _UNNEEDED, _NA_MILESTONE, _DB_DEVICE, _IMMUTABLE_BOM, _DB_FAMILY, _IPQC_INIT, \
        _VIEW_RTL, _VIEW_PHYS, _VIEW_TIMING, _VIEW_OTHER, _VIEW, _FUNCTIONALITY, _FUNC_FILE, \
        _DEFAULT_FUNC
from dmx.ipqclib.configuration import Configuration
from dmx.python_common.uiConfigParser import ConfigObj
from dmx.ipqclib.workspace import Workspace
from dmx.ipqclib.ipqcException import MissingDeliverable, IniConfigCorrupted, WaiverError
from dmx.dmlib.dmError import dmError
from dmx.ecolib.family import FamilyError
from dmx.ipqclib.ecosystem import get_ip_graph
from dmx.ecolib.ip import IPError
from dmx.ipqclib.waiver import get_waivers
from dmx.ipqclib.deliverable import Deliverable


def create_cell_object(family, workspace_path, workdir, cellname, ip_name, milestone, bom, \
        project, deliverable_list, requalify, cells_functionality, checkers_to_run=None):
    """create_cell_object"""
    os.chdir(workspace_path)
    if (cells_functionality != {}) and (cellname in cells_functionality.keys()):
        functionality = cells_functionality[cellname]
    else:
        functionality = _DEFAULT_FUNC

    uiDebug(">>> start creating object for cell {}" .format(cellname))
    cell = Cell(family, workspace_path, workdir, cellname, ip_name, milestone, bom, project, \
            deliverable_list, requalify, functionality=functionality, checkers_to_run=checkers_to_run)
    uiDebug(">>> end creating object for cell {}" .format(cellname))
    return cell

def easy_parallelize_cell(family, workspace_path, workdir, ip_name, milestone, bom, project, \
        deliverable_list, requalify, my_list, cells_functionality, checkers_to_run=None):
    """easy_parallelize_cell"""
    results = []
    if len(my_list) > 100:
        n_jobs = 4
    else:
        n_jobs = len(my_list)
#    n_jobs = len(my_list)
    results = Parallel(n_jobs=n_jobs, backend="threading")(delayed(create_cell_object)(family, \
            workspace_path, workdir, cellname, ip_name, milestone, bom, project, deliverable_list, \
            requalify, cells_functionality, checkers_to_run) for cellname in my_list)
    return results


def post_process_deliverable(unneeded_deliverables, ipname, ipbom, project, deliverable, \
        workspace_path, view_rtl_deliverables, view_phys_deliverables, view_timing_deliverables):
    """post_process_deliverable"""
    os.chdir(workspace_path)
    try:
        deliverable.bom = get_bom(project, ipname, ipbom, deliverable.name)

        # get owner's email
        deliverable.owner = get_deliverable_owner(project, ipname, deliverable.name, \
                deliverable.bom)
        results = run_command("finger {} | head -n 1 | awk -F'Name: ' '{{print $2}}'" \
                .format(deliverable.owner))
        out = results[1]
        if 'no such user' in out:
            pass
        else:
            deliverable.owner = out.strip()

        # set waiver
        waivers_file = os.path.join(workspace_path, ipname, deliverable.name, "tnrwaivers.csv")
        if file_accessible(waivers_file, os.F_OK):
            deliverable.waivers = get_waivers(waivers_file)

        if deliverable.bom == '':
            raise MissingDeliverable('{} is required by the roadmap, but not included in {} IP \
                    configuration.' .format(deliverable.name, ipname))
    except MissingDeliverable as err:
        deliverable.err = err
        deliverable.bom = ''
    except WaiverError as err:
        raise WaiverError(err)

    # get deliverable view
    if deliverable.name in view_rtl_deliverables:
        deliverable.view = _VIEW_RTL
    elif deliverable.name in view_phys_deliverables:
        deliverable.view = _VIEW_PHYS
    elif deliverable.name in view_timing_deliverables:
        deliverable.view = _VIEW_TIMING
    else:
        deliverable.view = _VIEW_OTHER

    if deliverable.name in unneeded_deliverables:
        deliverable.is_unneeded = True

    return deliverable


def easy_parallelize_post_process_deliverable(unneeded_deliverables, ipname, ipbom, project, \
        workspace_path, view_rtl_deliverables, view_phys_deliverables, view_timing_deliverables, \
        deliverables_list):
    """easy_parallelize_post_process_deliverable"""
    results = []
    results = Parallel(n_jobs=1, backend="multiprocessing")(delayed(post_process_deliverable)(unneeded_deliverables, ipname, ipbom, project, deliverable, workspace_path, view_rtl_deliverables, view_phys_deliverables, view_timing_deliverables) for \
            deliverable in deliverables_list)
    return results


class IP(object):
    """
    IP object
    """

    def __init__(self, ws, name, milestone, family, project=None, bom=None, initfile=None, output_dir=None, \
            cell_list=[], deliverable_list=[], top=False, cache=True, requalify=False, ciw=False, \
            report_template=_VIEW, checkers_to_run='*'):
        uiDebug(">>> ip.py - start IP object creation {}" .format(name))
        self._ws = ws
        self._milestone = milestone
        self._family = family
        self._project = project
        self._bom = bom
        self._name = name
        self._initfile = initfile
        self._topcells = []
        self._workdir = None
        self._flow = None
        self._report_url = None
        self._report_nfs = None
        self._date = datetime.datetime.now().strftime('%Y-%m-%d-%H_%M_%S')
        self._output_dir = output_dir
        self._status = _FATAL
        self._needs_execution = True
        self._leaf_ips = []
        self._cell_list = cell_list
        self._deliverable_list = deliverable_list
        self._top = top
        self._cache = cache
        self._requalify = requalify
        self._ciw = ciw
        self._report_template = report_template
        self.err = ''
        self._nb_checkers = 0
        self._nb_pass = 0
        self._nb_fail = 0
        self._nb_fatal = 0
        self._nb_unneeded = 0
        self._nb_warning = 0
        self._nb_na = 0
        self._nb_pass_global = 0
        self._nb_fail_global = 0
        self._nb_fatal_global = 0
        self._nb_unneeded_global = 0
        self._nb_warning_global = 0
        self._nb_na_global = 0
        self._graph = ''
        self._owner = ''
        self._iptype = ''
        self._config = None
        self._config_err = None
        self._changelist = None
        self._functionality = []
        self._checkers_to_run = checkers_to_run

        ##############################################################################################################
        # Use init file defined by user invoking --init-file <path_to_init_file>
        # else use .ini if file is in <workspace>/<ip>/reldoc/ipqc.ini (https://fogbugz.altera.com/default.asp?522484)
        # else use default $DMXDATA_ROOT/<project>/ipqc.ini
        ##############################################################################################################
        if initfile != None:
            self._initfile = initfile
        elif file_accessible(os.path.join(ws.path, self._name, 'reldoc', 'ipqc.ini'), os.F_OK):
            self._initfile = os.path.join(ws.path, self._name, 'reldoc', 'ipqc.ini')
        else:
            self._initfile = _IPQC_INIT

        if (self._ws is None) and (self._bom is None):
            self._ws = Workspace(self._name)

        #################################################################################################
        # Setting the working directory
        #
        # If user invoked --ouput-dir <output>, workdir=<output>
        # Else:
        #   If in workspace and reldoc exists, workdir=<workspace_path>/<ip>/reldoc/ipqc/<milestone>/<ip>
        #   Else workdir=/p/psg/logs/ipqc/ipqc_<ip>_<date>/<ip>
        #################################################################################################
        if self._output_dir is None:
            if (self._ws != None) and (dir_accessible(os.path.join(self._ws.path, self._name, \
                    'reldoc'), os.W_OK)):
                self._workdir = os.path.join(os.path.realpath(os.path.join(self._ws.path, \
                        self._name, 'reldoc')), 'ipqc', self._milestone, self._name)
            else:
                self._output_dir = os.path.realpath('/p/psg/logs/ipqc')

                if not dir_accessible(self._output_dir, os.W_OK):
                    os.makedirs(self._output_dir)
                    os.chmod(self._output_dir, 0o777)
                self._workdir = os.path.join(self._output_dir, 'ipqc_' + self._name + '_' + \
                        self._date, self._name)
        else:
            if not dir_accessible(os.path.join(self._output_dir, self._name), os.F_OK):
                os.makedirs(os.path.join(self._output_dir, self._name))
            self._workdir = os.path.realpath(os.path.join(self._output_dir, self._name))

        self._output_dir = self._workdir

        if not dir_accessible(self._workdir, os.F_OK):
            os.makedirs(self._workdir)
        else:
            remove_dir(self._workdir)
            os.makedirs(self._workdir)

        (self._project, self._bom) = self._get_info()

        self._is_immutable = self._bom.startswith(_IMMUTABLE_BOM)

        if not self._ws is None:
            try:
                self._config = Configuration(self._name, self._ws, self._initfile, ciw=self._ciw)
            except IniConfigCorrupted as err:
                raise IniConfigCorrupted(err)
            except dmError as err:
                self._config_err = err


        try:
#            ip = EcoSphere(workspaceroot=os.getcwd()).get_family(_DB_FAMILY).get_ip(self._name)
            ip = self._family.get_ip(self._name, project_filter=self._project)
            self._owner = ip.owner
            self._iptype = ip.iptype

            if self._report_template == _FUNCTIONALITY:
                # set ip functionality
                self._get_ip_functionality(ip.name)


            # User provided a list of deliverables
#            uiDebug(">>> ip.py - start get list of deliverables")
            if self._deliverable_list != []:

                self._deliverables_ipqc = []
                view_list = [view.name for view in family.get_views()]
                deliverable_list = [deliverable.name for deliverable in ip.get_deliverables()]
                all_ip_deliverables = [i.name for i in ip.get_all_deliverables()]
                all_family_deliverables = [d.name for d in family.get_all_deliverables()]

                for deliverable in self._deliverable_list:

                    # if this a view aka a collection of deliverables
                    if deliverable in view_list:
                        view = family.get_view(deliverable)
                        for deliverable_view in view.get_deliverables():
                            if deliverable_view.name in all_ip_deliverables:
                                self._deliverables_ipqc = self._deliverables_ipqc + \
                                        [deliverable_view]
                        continue

                    if deliverable in all_ip_deliverables:
#                        self._deliverables_ipqc.append(ip.get_deliverable(deliverable, roadmap=_DB_DEVICE))
                        self._deliverables_ipqc.append(Deliverable(self._ws.path, self._workdir, \
                                deliverable, ip, self._milestone, self._bom, self._project, \
                                self._requalify, self._checkers_to_run))
                        continue

                    # if this is a single deliverable
                    try:
                        self._family.get_deliverable(deliverable, roadmap=_DB_DEVICE)
                    except FamilyError as err:
                        uiCritical("{} is not a valid deliverable. {}" .format(deliverable, err))

                    if not deliverable in all_family_deliverables:
                        uiError("{} is not a valid deliverable. Ignoring it.".format(deliverable))


            # Use all deliverables for the given milestone
            else:
#                self._deliverables_ipqc = ip.get_all_deliverables(roadmap=_DB_DEVICE)
#                uiDebug(">>> ip.py - start get all deliverables list")
                self._deliverables_ipqc = [Deliverable(self._ws.path, self._workdir, d.name, ip, \
                        self._milestone, self._bom, self._project, self._requalify, self._checkers_to_run) for d in \
                        ip.get_all_deliverables(roadmap=_DB_DEVICE)]
#                uiDebug(">>> ip.py - end get all deliverables list")

#            uiDebug(">>> ip.py - start get IPQC deliverables list")
            self._deliverable_list = [d.name for d in self._deliverables_ipqc]
#            uiDebug(">>> ip.py - end get IPQC deliverables list {}" .format(self._ws.path))
            unneeded_deliverables = [i.name for i in ip.get_unneeded_deliverables()]
#            uiDebug(">>> ip.py - end get list of deliverables")

            # Explanation of condition self._cache == False
            # A dashboard is cached if it is availalbe in IPQC catalog: http://sjdmxweb01.sc.intel.com:8891/
            # If user invoked --requalify, cache option does not take precedence is condered as False. IPQC creates Ecolib object and
            # recomputes everything.
            #
            # Explanation of condition self._deliverables_ipqc != []
            # Example: FM6@z1574a is a Full Chip and does not have IPPWRMOD collateral. However, user is interested in seeing
            #   IPPWRMOD status for z1574a hierarchy. Command called would be: ipqc -i z1574a -m 4.0 -d ippwrmod
            #   It results that self._deliverables_ipqc would be equal to [] and would create topcells. We do not want to
            #   create topcells object as it does not make sense since it does not have IPPWRMOD. So adding condition
            #   self._deliverables_ipqc != []
            if (self._cache is False) and (self._deliverables_ipqc != []):
                view_rtl_deliverables = [e.name for e in family.get_view(_VIEW_RTL).get_deliverables()]
                view_phys_deliverables = [e.name for e in family.get_view(_VIEW_PHYS).get_deliverables()]
                view_timing_deliverables = [e.name for e in family.get_view(_VIEW_TIMING).get_deliverables()]

                try:
                    tmp = []

                    tmp = easy_parallelize_post_process_deliverable(unneeded_deliverables, \
                            self._name, self._bom, self._project, self._ws.path, \
                            view_rtl_deliverables, view_phys_deliverables, \
                            view_timing_deliverables, self._deliverables_ipqc)
                    self._deliverables_ipqc = tmp
                except ValueError as err:
                    uiWarning("ipqclib/ip.py deliverable post-processing {}" .format(err))
                    tmp = []
                    for deliverable_ipqc in self._deliverables_ipqc:
                        tmp.append(post_process_deliverable(unneeded_deliverables, self._name, \
                                self._bom, self._project, deliverable_ipqc, self._ws.path, \
                                view_rtl_deliverables, view_phys_deliverables, \
                                view_timing_deliverables))
                    self._deliverables_ipqc = tmp
                except WaiverError as err:
                    trace = traceback.format_exc().splitlines()
                    for i, content in enumerate(trace):
                        if content.startswith('WaiverError'):
                            lines = trace[i:]
                    self.err = '\n'.join(lines)
                    uiError(self.err)

                # If deliverable is not defined on one of the view in $DMXDATA/<family>/views.json remove this deliverable
                for deliverable in self._deliverables_ipqc:
                    if deliverable.view == '':
                        self._deliverables_ipqc.remove(deliverable)

                # Get topcells
                uiDebug(">>> ip.py - start get topcells")
                self._topcells = self._get_topcells(ip)
                uiDebug(">>> ip.py - end get topcells")

                # Initialize number of checkers at IP level
                for cell in self._topcells:
                    self._nb_checkers = self._nb_checkers + cell.nb_checkers
            else:
                for deliverable in self._deliverables_ipqc:
                    if deliverable.name in unneeded_deliverables:
                        deliverable.is_unneeded = True
                    deliverable.bom = get_bom(self._project, self._name, self._bom, \
                            deliverable.name)

        except IPError as err:
            uiError(err)
            self.err = err
        except dmError as err:
            uiError(err)
            self.err = err
        except FamilyError as err:
            uiError(err)
            self.err = err


        if self._workdir != None:
            self.record_file = os.path.join(self._workdir, 'ipqc.json')

        (flat_info, top_info, hierarchy_info) = self.get_hierarchy_info()

        self._flat_hierarchy = flat_info.keys()
        self._boms = flat_info
        self._top_hierarchy = top_info.keys()
        self._top_boms = top_info.values()
        self._hierarchy = hierarchy_info

#        (self._boms, self._hierarchy, self._top_boms, self._top_hierarchy, self._flat_hierarchy) = \
#                self.get_hierarchy_info()

        uiDebug(">>> ip.py - end IP object creation")


    def __repr__(self):
        return str(self.name)

    def get_graph(self):
        """get_graph"""
        self._graph = get_ip_graph(self._name, self._bom, output_dir=self._workdir, \
                project=self._project)


    def get_deliverable_ipqc(self, name):
        """get_deliverable_ipqc"""
        for deliverable in self.deliverables:
            if deliverable.name == name:
                return deliverable
        return None


    def get_hierarchy_info(self):
        """get_hierarchy_info"""
        from dmx.dmxlib.flows.printconfig import PrintConfig
        output = os.path.join(self._workdir, 'hierarchy.json')
        printconfig = PrintConfig(self._project, self._name, self._bom, json=output)
        code = printconfig.run()

        if code != 0:
            uiCritical("Error in running dmx report content for IP: {}" .format(self._name))

        with open(output, 'r') as fid:
            data = json.load(fid)

        flat_boms = {}
        top_boms = {}
        hierarchy = {}

        for i in data:
            #ipname = (i.split('/')[1]).split('@')[0]
            #bom = (i.split('/')[1]).split('@')[1]
            [project, ipname, bom] = i.split('/')
            list_of_ips = []

            if ipname != self._name:
                flat_boms[ipname] = bom

            if data[i]['ip'] == []:
                self._leaf_ips.append(ipname)
                hierarchy[ipname] = list_of_ips
                continue

            if ipname == self._name:

                list_of_ips.append(ipname)

                for sub_ip in data[i]['ip']:
                    #sname = (sub_ip.split('/')[1]).split('@')[0]
                    #sbom = (sub_ip.split('/')[1]).split('@')[1]
                    [sproject, sname, sbom] = i.split('/')
                    list_of_ips.append(sname)
                    top_boms[sname] = sbom

            else:

                for sub_ip in data[i]['ip']:
                    #sname = (sub_ip.split('/')[1]).split('@')[0]
                    [sproject, sname, sbom] = i.split('/')
                    list_of_ips.append(sname)

            hierarchy[ipname] = list_of_ips

        return(flat_boms, top_boms, hierarchy)


    ### Get information
    # project name
    # bom name
    ###################
    def _get_info(self):

        if self._ws != None:
            (project, bom) = self._ws.get_project_bom(self._name)
            return (project, bom)

        # TODO: surgical change here, should init at constructor lvl
        project = EcoSphere().get_family(_DB_FAMILY).get_ip(self._name, project_filter=self._project).icmproject
        return (project, self._bom)


    # Get the top cells of the IP
    def _get_topcells(self, ip):

        cells = []
        cells_functionality = {}

        if self._report_template != _FUNCTIONALITY:

            if self._cell_list == []:
                if self._is_immutable and (self._requalify is False):
                    cell_list = ip.get_cells_names(bom=self._bom, local=False)
                else:
                    cell_list = ip.get_cells_names()
            else:
                cell_list = self._cell_list

        elif self._report_template == _FUNCTIONALITY:

            # set ip functionality
            tmp_cell_list = ip.get_cells_names()
            cell_list = []

            data = ConfigObj(_FUNC_FILE)

            for cell in tmp_cell_list:

                if cell in cell_list:
                    continue

                for functionality, ips in data.items():

                    if cell in cell_list:
                        break

                    if not ip.name in ips.keys():
                        continue

                    for cellname in data[functionality][ip.name].split():

                        pattern = re.escape(cellname)
                        pattern = pattern.replace(r'\*', r'.*')
                        pattern = '^'+pattern+'$'

                        if re.search(pattern, cell):
                            cells_functionality[cell] = functionality
                            cell_list.append(cell)
                            break

                if not cell in cell_list:
                    cells_functionality[cell] = _DEFAULT_FUNC
                    cell_list.append(cell)

                    if _DEFAULT_FUNC not in self._functionality:
                        self._functionality.append(_DEFAULT_FUNC)


        # cell object creation
        try:
            cells = easy_parallelize_cell(self._family, self._ws.path, self._workdir, ip.name, \
                    self._milestone, self._bom, self._project, tuple(self._deliverable_list), \
                    self._requalify, cell_list, cells_functionality, self._checkers_to_run)
        except ValueError as err:
            uiWarning("{} ipqclib/ip/py cell object creation {}" .format(ip.name, err))
            for cellname in cell_list:
                if (cells_functionality != {}) and (cellname in cells_functionality.keys()):
                    functionality = cells_functionality[cellname]
                else:
                    functionality = _DEFAULT_FUNC
                cells.append(Cell(self._family, self._ws.path, self._workdir, cellname, ip.name, \
                        self._milestone, self._bom, self._project, tuple(self._deliverable_list), \
                        self._requalify, functionality=functionality, checkers_to_run=self._checkers_to_run))

        return cells

    # in case user use --report-template = functionality, provide functionality of the IP
    def _get_ip_functionality(self, ip_name):
        data = ConfigObj(_FUNC_FILE)
        for functionality, ips in data.items():
            if ip_name in ips.keys():
                self._functionality = self._functionality + [functionality]

        if self._functionality == []:
            self._functionality.append(_DEFAULT_FUNC)

    # Setting IP status
    def set_status(self, status_list=[]):
        """set_status"""
        if status_list != []:
            self._nb_checkers = len(status_list)

        else:
            if self.err != '':
                return _FATAL

            status_deliverables = {}

            for deliverable_ipqc in self._deliverables_ipqc:
                status_deliverables[deliverable_ipqc.name] = []

            for cell in self._topcells:
                for deliverable in cell.deliverables:
                    deliverable_ipqc = self.get_deliverable_ipqc(deliverable.name)

                    if deliverable_ipqc is None:
                        continue

                    if deliverable_ipqc.is_waived is True:
                        deliverable_ipqc.status = _ALL_WAIVED
                        deliverable.status = _ALL_WAIVED
                        status_deliverables[deliverable_ipqc.name].append(deliverable.status)
                        continue

                    if deliverable.status == _NA_MILESTONE:
                        deliverable.status = _NA_MILESTONE
                        status_deliverables[deliverable_ipqc.name].append(deliverable.status)
                        continue

                    deliverable_ipqc.nb_pass = deliverable_ipqc.nb_pass + deliverable.nb_pass
                    deliverable_ipqc.nb_fail = deliverable_ipqc.nb_fail + deliverable.nb_fail
                    deliverable_ipqc.nb_fatal = deliverable_ipqc.nb_fatal + deliverable.nb_fatal
                    deliverable_ipqc.nb_warning = deliverable_ipqc.nb_warning + \
                            deliverable.nb_warning
                    deliverable_ipqc.nb_unneeded = deliverable_ipqc.nb_unneeded + \
                            deliverable.nb_unneeded
                    deliverable_ipqc.nb_na = deliverable_ipqc.nb_na + deliverable.nb_na

                    status_deliverables[deliverable_ipqc.name].append(deliverable.status)

                    for checker in deliverable.checkers:
                        status = checker.status
                        status_list.append(status)

            for deliverable, values in status_deliverables.items():

                deliverable_ipqc = self.get_deliverable_ipqc(deliverable)

                if _NA_MILESTONE in values:
                    deliverable_ipqc.status = _NA_MILESTONE
                elif _ALL_WAIVED in values:
                    deliverable_ipqc.status = _ALL_WAIVED
                elif _FATAL in values:
                    deliverable_ipqc.status = _FATAL
                elif _FAILED in values or _CHECKER_SKIPPED in values:
                    deliverable_ipqc.status = _FAILED
                elif _WARNING in values:
                    deliverable_ipqc.status = _WARNING
                elif _PASSED in values:
                    deliverable_ipqc.status = _PASSED
                elif  _NA in values:
                    deliverable_ipqc.status = _NA
                elif _UNNEEDED in values:
                    deliverable_ipqc.status = _UNNEEDED


        self._nb_pass = status_list.count(_PASSED)
        self._nb_fail = status_list.count(_FAILED) + status_list.count(_CHECKER_SKIPPED)
        self._nb_fatal = status_list.count(_FATAL)
        self._nb_warning = status_list.count(_WARNING) + status_list.count(_CHECKER_WAIVED)
        self._nb_na = status_list.count(_NA)
        self._nb_unneeded = status_list.count(_UNNEEDED)

        if _FATAL in status_list:
            self._status = _FATAL
            return

        if _FAILED in status_list or _CHECKER_SKIPPED in status_list:
            self._status = _FAILED
            return

        if _WARNING in status_list:
            self._status = _WARNING
            return _WARNING

        if _UNNEEDED in status_list:
            self._status = _UNNEEDED
            return _UNNEEDED

        if _PASSED in status_list:
            self._status = _PASSED
            return _PASSED

        if _NA_MILESTONE in status_list:
            self._status = _NA_MILESTONE
            return _NA_MILESTONE

        if (self._nb_pass == 0) and (self._nb_fail == 0) and (self._nb_fatal == 0) and \
                (self._nb_warning == 0) and (self._nb_na == 0):
            self._status = _NA
            return _NA

        return



    @property
    def topcells(self):
        """topcells"""
        return self._topcells

    @property
    def nb_topcells(self):
        """nb_topcells"""
        return len(self._topcells)

    @property
    def nb_checkers(self):
        """nb_checkers"""
        return self._nb_checkers

    @property
    def flow(self):
        """flow"""
        return self._flow

    @flow.setter
    def flow(self, value):
        self._flow = value

    @property
    def status(self):
        """status"""
        return self._status

    @property
    def nb_pass(self):
        """nb_pass"""
        return self._nb_pass

    @nb_pass.setter
    def nb_pass(self, value):
        self._nb_pass = value

    @property
    def nb_pass_global(self):
        """nb_pass_global"""
        return self._nb_pass_global

    @nb_pass_global.setter
    def nb_pass_global(self, value):
        self._nb_pass_global = value

    @property
    def nb_fail(self):
        """nb_fail"""
        return self._nb_fail

    @nb_fail.setter
    def nb_fail(self, value):
        self._nb_fail = value

    @property
    def nb_fail_global(self):
        """nb_fail_global"""
        return self._nb_fail_global

    @nb_fail_global.setter
    def nb_fail_global(self, value):
        self._nb_fail_global = value

    @property
    def nb_unneeded(self):
        """nb_unneeded"""
        return self._nb_unneeded

    @nb_unneeded.setter
    def nb_unneeded(self, value):
        self._nb_unneeded = value

    @property
    def nb_unneeded_global(self):
        """nb_unneeded_global"""
        return self._nb_unneeded_global

    @nb_unneeded_global.setter
    def nb_unneeded_global(self, value):
        self._nb_unneeded_global = value

    @property
    def nb_fatal(self):
        """nb_fatal"""
        return self._nb_fatal

    @nb_fatal.setter
    def nb_fatal(self, value):
        self._nb_fatal = value

    @property
    def nb_fatal_global(self):
        """nb_fatal_global"""
        return self._nb_fatal_global

    @nb_fatal_global.setter
    def nb_fatal_global(self, value):
        self._nb_fatal_global = value

    @property
    def nb_warning(self):
        """nb_warning"""
        return self._nb_warning

    @nb_warning.setter
    def nb_warning(self, value):
        self._nb_warning = value

    @property
    def nb_warning_global(self):
        """nb_warning_global"""
        return self._nb_warning_global

    @nb_warning_global.setter
    def nb_warning_global(self, value):
        self._nb_warning_global = value

    @property
    def nb_na(self):
        """nb_na"""
        return self._nb_na

    @nb_na.setter
    def nb_na(self, value):
        self._nb_na = value

    @property
    def nb_na_global(self):
        """mb_na_global"""
        return self._nb_na_global

    @nb_na_global.setter
    def nb_na_global(self, value):
        self._nb_na_global = value


    @property
    def report_url(self):
        """report_url"""
        return self._report_url

    @report_url.setter
    def report_url(self, value):
        self._report_url = value

    @property
    def report_nfs(self):
        """report_nfs"""
        return self._report_nfs

    @report_nfs.setter
    def report_nfs(self, value):
        self._report_nfs = value

    @property
    def milestone(self):
        """milestone"""
        return self._milestone

    @property
    def workspace(self):
        """workspace"""
        return self._ws

    @property
    def config(self):
        """config"""
        return self._config

    @property
    def workdir(self):
        """workdir"""
        return self._workdir

    @property
    def deliverables(self):
        """deliverables"""
        return self._deliverables_ipqc

    @property
    def bom(self):
        """bom"""
        return self._bom

    @property
    def is_immutable(self):
        """is_immutable"""
        return self._is_immutable

    @property
    def project(self):
        """project"""
        return self._project

    @property
    def boms(self):
        """boms"""
        return self._boms

    @property
    def output_dir(self):
        """output_dir"""
        return self._output_dir

    @property
    def needs_execution(self):
        """needs_execution"""
        return self._needs_execution

    @needs_execution.setter
    def needs_execution(self, value):
        self._needs_execution = value

    @property
    def leaf_ips(self):
        """leaf_ips"""
        return self._leaf_ips

    @property
    def hierarchy(self):
        """hierarchy"""
        return self._hierarchy

    @property
    def top_hierarchy(self):
        """top_hierarchy"""
        return self._top_hierarchy

    @property
    def flat_hierarchy(self):
        """flat_hierarchy"""
        return self._flat_hierarchy

    @property
    def top_boms(self):
        """top_boms"""
        return self._top_boms

    @property
    def graph(self):
        """graph"""
        return self._graph

    @property
    def name(self):
        """name"""
        return self._name

    @property
    def family(self):
        """family"""
        return self._family

    @property
    def owner(self):
        """owner"""
        return self._owner

    @property
    def iptype(self):
        """iptype"""
        return self._iptype

    @property
    def cache(self):
        """cache"""
        return self._cache

    @cache.setter
    def cache(self, value):
        self._cache = value

    @property
    def config_err(self):
        """config_err"""
        return self._config_err

    @property
    def changelist(self):
        """changelist"""
        return self._changelist

    @changelist.setter
    def changelist(self, value):
        self._changelist = value

    @property
    def functionality(self):
        """functionality"""
        return self._functionality
