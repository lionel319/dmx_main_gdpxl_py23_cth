#!/usr/bin/env python
""" Utilities for IPQC object (ipqc.py)
"""
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import re
from dmx.ipqclib.utils import run_command, file_accessible, dir_accessible, is_non_zero_file, \
         remove_file, remove_dir, get_status_for_deliverable, get_milestones
from dmx.ipqclib.log import uiInfo, uiWarning, uiDebug, uiError
from dmx.ipqclib.settings import _IMMUTABLE_BOM, _REL, _DB_DEVICE, _ALL_WAIVED, _UNNEEDED, \
         _NA_MILESTONE, _PASSED, _FAILED, _FATAL, _NA, _WARNING, _CHECKER_WAIVED, _CHECKER_SKIPPED


def get_ip_changelist(sub_ipqc):
    """ Create a changelist number per IP
    """
    #pylint: disable= line-too-long
    command = "xlp4 change -o | grep '^\(Change\|Client\|User\|Description\)' | sed \"s/Description:/Description:IPQC checker execution/\" | xlp4 change -i | cut -d ' ' -f 2" # pylint: disable=W1401
    #pylint: enable= line-too-long

    (code, out) = run_command(command)
    if code != 0:
        uiError(out)
    else:
        uiInfo("Changelist number for IP {}: {}" .format(sub_ipqc.ip.name, out))

    return out.strip()


def ipqc_add_files_not_in_depot(files_to_add, ipname):
    """
        https://fogbugz.altera.com/default.asp?607478
        This is an enhancement request on IPQC to support the xlp4 add command on input \
            files (not flow generated) which are not check-in to depot previously
    """
    cmd = 'xlp4 status {}' .format(' '.join(files_to_add))
    uiDebug("Running {}" .format(cmd))
    (code, out) = run_command(cmd)
    out = out.strip()
    uiDebug(out)

    if re.search('reconcile to add', out):
        #pylint: disable= line-too-long
        command = "xlp4 change -o | grep '^\(Change\|Client\|User\|Description\)' | sed \"s/Description:/Description:$1/\" | xlp4 change -i | cut -d ' ' -f 2" # pylint: disable=W1401
        #pylint: enable= line-too-long
        (code, out) = run_command(command)
        if code != 0:
            uiError(out)
        else:
            uiInfo("Changelist number for IP {} adding files: {}" \
                    .format(ipname, out))
        changelist = out.strip()
        uiInfo("Adding {}" .format(' '.join(files_to_add)))

        cmd = 'xlp4 reconcile -a -c {} {}' .format(changelist, ' '.join(files_to_add))
        uiInfo("Running {}" .format(cmd))
        (code, out) = run_command(cmd)
        if code != 0:
            uiError(out)
        else:
            uiInfo(out)

        cmd = 'xlp4 submit -c {}' .format(changelist)
        uiInfo("Running {}" .format(cmd))
        (code, out) = run_command(cmd)

        if code != 0:
            uiError(out)
        else:
            uiInfo(out)

    return

#pylint: disable=too-many-locals,inconsistent-return-statements
def ipqc_scripts_dm_deliverable(sub_ipqc, cellname, deliverable, requalify, f_checkout_cell, \
        f_checkin_cell, f_revert_cell, flag_revert):
    """ create .csh scripts to checkout data per deliverable
    """

    (edit_command, revert_command, submit_command, add_command, reopen_command) = \
            ipqc_get_commands(sub_ipqc, deliverable, requalify)

    files_to_check_out = deliverable.get_manifest(cellname)[0] + \
                         deliverable.get_audit_files(cellname)

    if files_to_check_out == []:
        return

    # checkout script
    print('%s %s' % (edit_command, ' '.join(files_to_check_out)), file=f_checkout_cell)

    if not reopen_command is None:
        print('%s %s' % (reopen_command, ' '.join(files_to_check_out)), file=f_checkout_cell)

    # files that are marked as generated True in manifest
    for filename in sorted(files_to_check_out, key=lambda \
            file: (os.path.dirname(file), os.path.basename(file))):

        # checkin script
        # If this is the first time the check is executed, need to anticipate file to check-in

        # if in mutable config use ICM command
        if not(add_command is None) and not file_accessible(filename, os.R_OK):
            print('echo "%s %s"; %s %s' % (add_command, filename, add_command, \
                    filename), file=f_checkin_cell)
        else:
        # in immutable config use Unix command
            print('echo "%s %s"; %s %s' % (submit_command, filename, \
                    submit_command, filename), file=f_checkin_cell)

        # revert script
        cmd = '{} {}' .format(revert_command, filename)

        # revert script
        if deliverable.bom.startswith(_IMMUTABLE_BOM) or (requalify is True):
            cmd = '/bin/ls {} && {} || echo "no file {} to revert"' \
                    .format(filename, cmd, filename)
        elif flag_revert is False:
            cmd = '{} ...' .format(revert_command)
            flag_revert = True
        else:
            return flag_revert

        print(cmd, file=f_revert_cell)

    return flag_revert
#pylint: enable=too-many-locals,inconsistent-return-statements


def ipqc_open_file(workspace_path, workdir, step):
    """ create file
    """
    filepath = os.path.join(workdir, step)
    fid = open(filepath, 'w')
    print('#!/bin/csh', file=fid)
    print('cd {}' .format(workspace_path), file=fid)
    return (fid, filepath)

def ipqc_close_file(f_id, filename):
    """ close file
    """
    f_id.close()
    os.chmod(filename, 0o775)


def ipqc_print_files(ipname, cellname, workdir, step):
    """ open file for cell
    """
    filename = 'ipqc_{}_{}_{}' .format(step, ipname, cellname)
    filepath = os.path.join(workdir, filename)
    f_cell = open(filepath, 'w')
    print('#!/bin/csh', file=f_cell)
    return (filepath, f_cell)

def ipqc_open_cell_files(ipname, cellname, workdir, step):
    """ipqc_open_files_checkout"""
    filename = 'ipqc_{}_{}_{}' .format(step, ipname, cellname)
    filepath = os.path.join(workdir, filename)
    f_cell = open(filepath, 'a+')
    return (filepath, f_cell)

def ipqc_close_cell_files(f_checkout, checkout_file, scripts_checkout):
    """ipqc_close_files_checkout"""
#    print(os.path.join(workdir, checkout_file), file=f_checkout)
    f_checkout.close()
    os.chmod(checkout_file, 0o775)

    if checkout_file not in scripts_checkout:
        scripts_checkout.append(checkout_file)

    return scripts_checkout


def ipqc_close_cell_files_checkin(sub_ipqc, f_checkin, checkin_file, workdir, flag, immutable):
    """Close file for cell checkin script
    """
    if not(immutable) and (flag == 0):
        submit_command = 'xlp4 submit -c {}' .format(sub_ipqc.ip.changelist)
        print('echo "%s"; %s' % (submit_command, submit_command), file=f_checkin)
        flag = 1
    elif immutable:
        print(os.path.join(workdir, checkin_file), file=f_checkin)
    f_checkin.close()
    os.chmod(checkin_file, 0o775)

    return flag


def ipqc_get_commands(sub_ipqc, deliverable, requalify):
    """If BOM is immutable use chmod unix else use xlp4
    """
    if deliverable.bom.startswith(_IMMUTABLE_BOM) or (requalify is True):
        edit_command = 'chmod -R +w'
        revert_command = 'chmod -R -w'
        submit_command = 'chmod -R -w'
        add_command = None
        reopen_command = None
    else:
        edit_command = 'xlp4 edit -c {}' .format(sub_ipqc.ip.changelist)
        revert_command = 'xlp4 revert -c {}' .format(sub_ipqc.ip.changelist)
        submit_command = 'xlp4 submit -c {}' .format(sub_ipqc.ip.changelist)
        add_command = 'xlp4 reconcile -a -c {}' .format(sub_ipqc.ip.changelist)
        reopen_command = 'xlp4 reopen -c {}' .format(sub_ipqc.ip.changelist)

    return (edit_command, revert_command, submit_command, add_command, reopen_command)

def remove_audit_file(deliverable, sub_ipqc, audit_file):
    """Delete audit file
    """
    if (deliverable.is_immutable) or (sub_ipqc.requalify is True):
        (code, out) = run_command('chmod +w {}' .format(audit_file))

        if code != 0:
            uiError(out)
        else:
            uiInfo(out)
    else:
        (code, out) = run_command('xlp4 delete {}' .format(audit_file))
        if code != 0:
            uiError(out)
        else:
            uiInfo(out)

        (code, out) = run_command('xlp4 submit -d "waiving check" {}' .format(audit_file))
        if code != 0:
            uiError(out)
        else:
            uiInfo(out)

    remove_file(audit_file)


def process_checker_waived(sub_ipqc, cell, deliverable, checker):
    """ If checker is waived there is a stupid trick with empty audit filelist.
        Methodology does not want to make this trick exposed to users.
        https://wiki.ith.intel.com/pages/viewpage.action?pageId=1024985391#Waivers-Checker-levelWaivers

        Checker-level Waivers
        Methodology has approved two cases in which the checker can be waived, even if the \
            deliverable is required.

        DA flow is not supported for your project (yet)
        When many top cells are present and the check is needed for only certain cells
        Do not use this to waive checkers in any other case!

        To waive the checker, provide an empty .f file.

        touch audit.<cell_name>.<flow>_<subflow>.f
    """
    uiWarning("Waiving checker {} (flow={} subflow={}) for IP {} cell {}" \
            .format(checker.name, checker.flow, checker.subflow, sub_ipqc.ip.name, cell.name))
    audit_filelist = os.path.join(checker.audit.prefix_path, \
            '.'.join(('audit', cell.name, checker.checker_id, 'f')))
    audit_file = os.path.join(checker.audit.prefix_path, \
            '.'.join(('audit', cell.name, checker.checker_id, 'xml')))

    if file_accessible(audit_file, os.F_OK):
        remove_audit_file(deliverable, sub_ipqc, audit_file)

    if file_accessible(audit_filelist, os.F_OK):
        if (deliverable.is_immutable) or (sub_ipqc.requalify is True):
            (code, out) = run_command('chmod +w {}' .format(audit_filelist))
        else:
            (code, out) = run_command('xlp4 edit {}' .format(audit_filelist))

        if code != 0:
            uiError(out)
        else:
            uiInfo(out)
        remove_file(audit_filelist)

    if not dir_accessible(checker.audit.prefix_path, os.F_OK):
        os.makedirs(checker.audit.prefix_path)

    os.mknod(os.path.join(checker.audit.prefix_path, '.'.join(('audit', cell.name, \
                        checker.checker_id, 'f'))))


def set_path(path):
    """ rm, mkdir directory
    """
    if dir_accessible(path, os.F_OK):
        uiInfo("Removing: {}" .format(path))
        remove_dir(path)
    if not dir_accessible(os.path.join(path), os.F_OK):
        uiInfo("Creating: {}" .format(path))
        os.makedirs(os.path.join(path))
    return

def remove_empty_audit_filelist(deliverable, audit_filelist, sub_ipqc):
    """If immutable BOM, use rm unix command else use xlp4 command to remove filelist.
    """
    if file_accessible(audit_filelist, os.F_OK) and not is_non_zero_file(audit_filelist):
        uiDebug("Removing empty filelist {}" .format(audit_filelist))
        if (deliverable.is_immutable) or (sub_ipqc.requalify is True):
            remove_file(audit_filelist)
        else:
            (code, out) = run_command('xlp4 delete {}' .format(audit_filelist))
            if code != 0:
                uiError(out)
            else:
                uiInfo(out)
            (code, out) = run_command('xlp4 submit -d "remove waiving check" {}' \
                    .format(audit_filelist))
            if code != 0:
                uiError(out)
            else:
                uiInfo(out)
            remove_file(audit_filelist)


def data_prep(sub_ipqc):
    """Create folders necessary for IPQC
    """
    from dmx.ipqclib.ipqcException import WaiverError
    from dmx.ipqclib.environment import Environment
    # If data are already cached, it is not necessary to regenerate the dashboard
    if (sub_ipqc.cache is True) and (sub_ipqc.requalify is False):
        return

    # generates IP graph
    sub_ipqc.ip.get_graph()

    for cell in sub_ipqc.ip.topcells:
        set_path(os.path.join(sub_ipqc.ip.workdir, cell.name))

        for deliverable in cell.deliverables:

            if not dir_accessible(os.path.join(sub_ipqc.ip.workdir, deliverable.name), os.F_OK):
                set_path(os.path.join(sub_ipqc.ip.workdir, deliverable.name))
                if deliverable.has_waivers():
                    deliverable.record_waivers()

            for checker in deliverable.checkers:

                try:
                    checker.record_waivers()
                except WaiverError:
                    continue

                if (sub_ipqc.mode != "run-all") and (sub_ipqc.mode != "setup"):
                    continue

                if checker.is_waived(cell.name, sub_ipqc.ip.config) is True:
                    process_checker_waived(sub_ipqc, cell, deliverable, checker)

                else:
                    audit_filelist = os.path.join(checker.audit.prefix_path, '.'.join(('audit', \
                                    cell.name, checker.checker_id, 'f')))

                    remove_empty_audit_filelist(deliverable, audit_filelist, sub_ipqc)

    ### Record ini file for run-all
    if (sub_ipqc.mode == "run-all") or (sub_ipqc.mode == 'setup'):
        if sub_ipqc.ip.config_err != None:
            uiError("Error encountered during config file parsing")
            return
        sub_ipqc.ip.config.save(os.path.join(sub_ipqc.ip.workdir, 'ipqc.ini'))

    sub_ipqc.environment = Environment(sub_ipqc.ip.workdir, sub_ipqc.ipenv)
    uiDebug(">> Saving environment info")
    sub_ipqc.environment.save()
    return


def create_ipqc_object(ipqc, ipname, bom, ip_filter, checkers_to_run=None):
    """Create sub-ipqc object
    """
    from dmx.ipqclib.ipqc import IPQC
    from dmx.ipqclib.pre_dry_run import get_depth, find_all_paths

    if ipname == ipqc.ip.name:
        return

    if ip_filter != [] and not ipname in ip_filter:
        return

    milestone = ipqc.milestone

    if bom.startswith(_IMMUTABLE_BOM) and bom.startswith(_REL):
        pattern = _REL+'([0-9]\\.[0-9])'+_DB_DEVICE
        result = re.search(pattern, bom)

        # if device are different than the one in ARC.
        # Top IP is from FM8. Sub-IP is from FM6.
        if result is None:
            pattern = _REL+r'([0-9]\\.[0-9])\w*'
            result = re.search(pattern, bom)

            if result and (result.group(1) in get_milestones()):
                milestone = result.group(1)

    if ipqc.ip.workspace != None:
        ipdata = ipname
    else:
        ipdata = ipname+'@'+bom

    depth = {}
    paths = []

    for subip in ipqc.ip.leaf_ips:
        paths = paths + find_all_paths(ipqc.ip.hierarchy, ipqc.ip.name, subip)

    for ip in ipqc.ip.hierarchy.keys(): # pylint: disable=invalid-name
        if ip != ipname:
            continue
        depth[ip] = get_depth(ip, paths)
    depths = list(set(depth.values()))

    if depth == {}:
        max_depth = 0
    else:
        max_depth = max(depths)

    sub_ipqc = IPQC(milestone, ipdata, deliverables=ipqc.deliverables, mode=ipqc.mode, \
            requalify=ipqc.requalify, depth=max_depth, workspace=ipqc.workspace, \
            output_dir=os.path.dirname(ipqc.ip.output_dir), checkin=ipqc.checkin, \
            no_revert=ipqc.no_revert, exclude_ip=ipqc.exclude_ip, \
            ciw=ipqc.ciw, report_template=ipqc.report_template, top=False, options=ipqc.options, checkers_to_run=checkers_to_run)

    sub_ipqc.init_ip()

    return sub_ipqc



def easy_parallelize_ipqc(ipqc, my_list, ip_filter, checkers_to_run=None):
    """ Parallelize IPQC object creation
    """
    from joblib import Parallel, delayed
    results = []
    results = Parallel(n_jobs=len(my_list), backend="threading")(delayed(create_ipqc_object)(ipqc, \
                ipname, bom, ip_filter, checkers_to_run) for (ipname, bom) in my_list.items() \
                if ipname != ipqc.ip.name)
    results = list(set(results))
    if None in results:
        results.remove(None)
    return results


def checkin_checkout_command(cmd):
    """Execute checkin/checkout command
    """
    uiDebug("Running {}" .format(cmd))
    (code, out) = run_command(cmd)

    if code != 0:
        uiError(out)
    else:
        uiInfo(out)
    return


def easy_parallelize_data_prep(list_of_ipqc):
    """Parallelize data_prep
    """
    import multiprocessing
    from joblib import Parallel, delayed
    njobs = (multiprocessing.cpu_count() * 2)
    Parallel(n_jobs=njobs, backend="threading")(delayed(data_prep)(ipqc) for ipqc in list_of_ipqc)


def easy_parallelize(my_list):
    """Parallelize checkin/checkout commands.
    """
    import multiprocessing
    from joblib import Parallel, delayed
    results = []
    njobs = (multiprocessing.cpu_count() * 2)
    results = Parallel(n_jobs=njobs, backend="threading")(delayed(checkin_checkout_command)(cmd) \
            for cmd in my_list)
    return results

def revert_files_failed_deliverable(changelist, cell, deliverable):
    """Revert files for deliverables which failed.
    """
    list_of_files = deliverable.get_audit_files('all') + deliverable.get_manifest(cell.name)[0]

    for manifest in list_of_files:

        cmd = "xlp4 revert {} -c {}" .format(manifest, changelist)
        (code, out) = run_command(cmd)

        if code != 0:
            uiError(out)
        else:
            uiInfo(out)

def revert_audit_files(sub_ipqc, deliverable):
    """ Revert audit files
    """
    audit_files = '{}/{}/audit/...' .format(sub_ipqc.ip.name, deliverable.name)
    uiInfo("Reverting {}" .format(audit_files))
    (code, out) = run_command('xlp4 revert {}' .format(audit_files))

    if code != 0:
        uiError(out)
    else:
        uiInfo(out)

def set_deliverable_status_from_record(ip, deliverable, deliverable_values): #pylint: disable=invalid-name,
    """ Set the deliverable status from the record .json file.
    """
    status = []
    deliverable_ip = ip.get_deliverable_ipqc(deliverable)

    if deliverable_ip is None:
        return

    if deliverable_values["status"] == _NA_MILESTONE:
        deliverable_ip.status = _NA_MILESTONE
        return

    if deliverable_values["status"] == _ALL_WAIVED:
        deliverable_ip.status = _ALL_WAIVED
        return

    if isinstance(deliverable_values, dict):
        for checker_values in deliverable_values.values():
            if isinstance(checker_values, dict):

                status.append(checker_values["status"])

                if checker_values["status"] == _PASSED:
                    deliverable_ip.nb_pass = deliverable_ip.nb_pass + 1
                elif checker_values["status"] == _FAILED or (checker_values["status"] == _CHECKER_SKIPPED):
                    deliverable_ip.nb_fail = deliverable_ip.nb_fail + 1
                elif checker_values["status"] == _FATAL:
                    deliverable_ip.nb_fatal = deliverable_ip.nb_fatal + 1
                elif checker_values["status"] == _NA:
                    deliverable_ip.nb_na = deliverable_ip.nb_na + 1
                elif (checker_values["status"] == _WARNING) or \
                    (checker_values["status"] == _CHECKER_WAIVED):
                    deliverable_ip.nb_warning = deliverable_ip.nb_warning + 1
                elif checker_values["status"] == _UNNEEDED:
                    deliverable_ip.nb_unneeded = deliverable_ip.nb_unneeded + 1

    deliverable_ip.status = get_status_for_deliverable(status)


def get_results(ip): # pylint: disable=invalid-name
    """ Get results for the given IP
    """
    from operator import attrgetter

    tests = []

    for cell in sorted(ip.topcells, key=attrgetter('name')):
        for deliverable in sorted(cell.deliverables, key=attrgetter('name')):
            # Get deliverable status: PASSED, FAILED, FATAL, WARNING, NA, UNNEEDED, NA_MILESTONE

            if deliverable.is_waived:
                tests.append([cell.name, deliverable.name, '-', _ALL_WAIVED])
                deliverable.get_status(cell.name)
                continue

            if deliverable.is_unneeded:
                tests.append([cell.name, deliverable.name, '-', _UNNEEDED])
                deliverable.get_status(cell.name)
                for checker in sorted(deliverable.checkers, key=attrgetter('checker_id')):
                    cell.nb_unneeded = cell.nb_unneeded + 1
                continue

            if deliverable.status == _NA_MILESTONE:
                tests.append([cell.name, deliverable.name, '-', _NA_MILESTONE])
                deliverable.get_status(cell.name)
                continue

            if deliverable.err != "":
                for checker in deliverable.checkers:
                    cell.nb_fatal = cell.nb_fatal + 1
                deliverable.get_status(cell.name)
                continue

            deliverable.get_status(cell.name)

            for checker in sorted(deliverable.checkers, key=attrgetter('checker_id')):

                if (checker.status == _WARNING) or (checker.status == _CHECKER_WAIVED):
                    message = 'completed and passed with waivers'
                    cell.nb_warning = cell.nb_warning + 1
                elif checker.status == _PASSED:
                    message = 'completed and passed'
                    cell.nb_pass = cell.nb_pass + 1
                elif checker.status == _FAILED:
                    message = 'completed and failed'
                    cell.nb_fail = cell.nb_fail + 1
                elif checker.status == _CHECKER_SKIPPED:
                    message = 'completed and failed(skip)'
                    cell.nb_fail = cell.nb_fail + 1
                elif checker.status == _FATAL:
                    message = 'needs to be executed'
                    cell.nb_fatal = cell.nb_fatal + 1
                elif checker.status == _NA:
                    message = '-'
                    cell.nb_nc = cell.nb_nc + 1
                elif checker.status == _UNNEEDED:
                    message = 'unneeded'
                    cell.nb_unneeded = cell.nb_unneeded + 1

                tests.append([cell.name, checker.deliverable_name, checker.wrapper_name, message])

        cell.set_status()

    return tests
