#!/usr/bin/env python
"""backup.py"""
# -*- coding: utf-8 -*-
from __future__ import print_function
import os as os
from operator import attrgetter
from joblib import Parallel, delayed
from dmx.ipqclib.utils import file_accessible, dir_accessible, run, replace, get_catalog_paths, \
        run_command, get_functionality_file_data
from dmx.ipqclib.settings import _DATA_PATH, _ARC_URL, _VIEW, _FUNCTIONALITY, _SIMPLE
from dmx.ipqclib.log import uiInfo, uiError, uiDebug
from dmx.ipqclib.ipqcException import NotADirectoryError


def trace(ipqc, report_format, report_template=_VIEW):
    """trace"""
    if ipqc.sendmail:
        report_path = backup(ipqc, report_format, report_template)
        return report_path

    if ipqc.ip.report_url != None:
        return ipqc.ip.report_url

    ipqc.ip.report_url = _ARC_URL + ipqc.ip.report_nfs
    return ipqc.ip.report_nfs

def replace_string(ipobj, nfs_path, url_path, commands, cell, requalify):
    """replace_string"""
    cell_filename = 'ipqc_'+cell.name+'.html'
    cell_html = os.path.join(nfs_path, cell_filename)

    if not file_accessible(cell_html, os.R_OK):
        return

    run("{} -a {} {}" .format(commands["rsync"], os.path.join(ipobj.workdir, cell_filename), \
            cell_html))

    with open(os.path.join(nfs_path, cell_filename), 'r') as f_cell:
        html_cell = f_cell.read()

        for deliverable in ipobj.deliverables:
            if (deliverable.report != None) and file_accessible(deliverable.report, os.F_OK):
                html_cell = replace(os.path.join(ipobj.workdir, deliverable.name+'/'), \
                        os.path.dirname(deliverable.report)+'/', html_cell)
            else:
                deliverable_cell_level = cell.get_deliverable(deliverable.name)
                if deliverable_cell_level.is_immutable and not requalify:
                    deliverable_report_path = get_catalog_paths(ipobj.name, ipobj.bom, \
                            ipobj.milestone, \
                            deliverable)
                    html_cell = replace(os.path.join(ipobj.workdir, deliverable.name+'/'), \
                            deliverable_report_path[0]+'/', html_cell)
                else:
                    html_cell = replace(os.path.join(ipobj.workdir, deliverable.name+'/'), \
                            os.path.join(url_path, deliverable.name+'/'), html_cell)

        html_cell = replace(os.path.dirname(ipobj.workdir), os.path.dirname(url_path), html_cell)

    run('{} {}' .format(commands["chmod_write"], cell_html))
    with open(cell_html, 'w') as f_cell:
        print(html_cell, file=f_cell)

    run('{} {}' .format(commands["chmod"], cell_html))
    return


def easy_parallelize_replace(ipobj, nfs_path, url_path, commands, requalify):
    """easy_parallelize_replace"""
    results = []
    results = Parallel(n_jobs=len(ipobj.topcells), \
            backend="threading")(delayed(replace_string)(ipobj, nfs_path, url_path, commands, \
            cell, requalify) for cell in ipobj.topcells)
    return results

def replace_functionality(ipobj, url_path, nfs_path, rsync_cmd, chmod_cmd):
    """replace_functionality"""
    data = get_functionality_file_data()
    for functionality in data.keys():
        filename = 'ipqc_'+ipobj.name+'_'+functionality+'.html'
        filepath = os.path.join(ipobj.workdir, filename)
        if not file_accessible(filepath, os.F_OK):
            continue

        with open(filepath, 'r') as fid:
            html = fid.read()
            html = replace(ipobj.workdir, url_path, html)
            html = replace(os.path.dirname(ipobj.workdir), os.path.dirname(url_path), html)

        new_html = os.path.join(ipobj.workdir, 'tmp')
        with open(new_html, 'w') as fid:
            print(html, file=fid)
        new_file = os.path.join(nfs_path, filename)
        run("{} -a {} {}" .format(rsync_cmd, new_html, new_file))
        run("{} {}" .format(chmod_cmd, new_file))

    return

def get_info(ipqc, sub_ipqc):
    """get_info"""
    # REL/snap and not in requalification mode
    # If dashboard already exists, continue
    if sub_ipqc.ip.is_immutable and not sub_ipqc.requalify and not sub_ipqc.cache:

        (url_path, nfs_path) = get_catalog_paths(sub_ipqc.ip.name, sub_ipqc.ip.bom, \
                sub_ipqc.ip.milestone)

        rsync_cmd = "/p/psg/da/infra/admin/setuid/ipqc_rsync"
        chmod_cmd = "/p/psg/da/infra/admin/setuid/ipqc_chmod -R a+rX"
        chmod_write_cmd = "/p/psg/da/infra/admin/setuid/ipqc_chmod -R g+wX"
        mkdir_cmd = "/p/psg/da/infra/admin/setuid/ipqc_mkdir"

        dst_path = nfs_path

    else:
        ### Create destination path
        if dir_accessible(os.path.join(_DATA_PATH, os.getenv('USER')), os.W_OK):
            dst_path = os.path.join(_DATA_PATH, os.getenv('USER'), 'ipqc')
        else:
            dst_path = os.path.join("/tmp")

        dst_path = os.path.join(dst_path, os.getenv('USER') + '_' + ipqc.ip.name + '_' + \
                ipqc.ip.bom + '_' + ipqc.date)

        if not dir_accessible(dst_path, os.F_OK):
            os.makedirs(dst_path)
            os.chmod(dst_path, 0o775)

        if not os.path.exists(dst_path):
            raise NotADirectoryError("Directory not found")
        ### End create destination path if not existing

        (url_path, nfs_path) = (_ARC_URL + os.path.join(dst_path, sub_ipqc.ip.name), \
                os.path.join(dst_path, sub_ipqc.ip.name))

        rsync_cmd = "rsync"
        chmod_cmd = "chmod -R 0775"
        chmod_write_cmd = chmod_cmd
        mkdir_cmd = "mkdir"

    commands = {"rsync": rsync_cmd, "chmod": chmod_cmd, "chmod_write": chmod_write_cmd, \
            "mkdir": mkdir_cmd}

    return (url_path, nfs_path, commands, dst_path)

def handle_ip_error_during_creation(sub_ipqc, url_path, nfs_path, commands, report_format):
    """handle_ip_error_during_creation"""
    ### If error during IP creation
    if sub_ipqc.ip.err != '':
        filename = 'ipqc.' + report_format
        filepath = os.path.join(nfs_path, filename)
        sub_ipqc.ip.report_nfs = filepath
        sub_ipqc.ip.report_url = os.path.join(url_path, filename)

        if not file_accessible(os.path.join(nfs_path, filename), os.F_OK):
            run("{} -p {}" .format(commands["mkdir"], nfs_path))
            run("{} -av --exclude '*.f' {}/ {}/" .format(commands["rsync"], \
                    sub_ipqc.ip.workdir, nfs_path))

        if not file_accessible(os.path.join(nfs_path, filename), os.F_OK):
            return 1

        with open(filepath, 'r') as fid:
            html = fid.read()
            html = replace(os.path.join(sub_ipqc.ip.workdir, 'ip_graph.pdf'), \
                    os.path.join(url_path, 'ip_graph.pdf'), html)

        ip_html = os.path.join(sub_ipqc.ip.workdir, 'tmp')
        with open(ip_html, 'w') as fid:
            print(html, file=fid)

        run("{} -a {} {}" .format(commands["rsync"], os.path.join(sub_ipqc.ip.workdir, \
                'tmp'), filepath))
        run('{} {}' .format(commands["chmod"], nfs_path))
        sub_ipqc.ip.report_url = _ARC_URL + filepath
        sub_ipqc.ip.report_nfs = filepath
        return 1

    return 0


def html_replace_deliverable(html, ipqc, sub_ipqc, deliverable, dst_path):
    """html_replace_deliverable"""
    for i in sorted(sub_ipqc.ip.flat_hierarchy):
        s_ipqc = sub_ipqc.get_ipqc(i)
        if (s_ipqc is None) or (s_ipqc.ip.err != ""):
            continue

        deliverable_subipqc = s_ipqc.ip.get_deliverable_ipqc(deliverable.name)
        if (deliverable_subipqc is None) or (deliverable_subipqc.bom == ''):
            continue

        if (ipqc.ip.is_immutable) and (ipqc.requalify is False):
            sub_ipqc_report_path = get_catalog_paths(s_ipqc.ip.name, s_ipqc.ip.bom, \
                    s_ipqc.ip.milestone, deliverable_subipqc)
        else:
            sub_ipqc_report_path = (_ARC_URL + os.path.join(dst_path, s_ipqc.ip.name, \
                    deliverable.name), os.path.join(dst_path, s_ipqc.ip.name, deliverable.name))

        html = replace(os.path.join(s_ipqc.ip.workdir, deliverable.name), sub_ipqc_report_path[0], \
                html)

    return html


#################################################################################
#  FB483425 - https://fogbugz.altera.com/default.asp?483425                     #
#  For immutable confguration dashboard is centralized on http server           #
#                                                                               #
#  See in $DMXDATA_ROOT/<family>/ipqc/settings.ini for location.                #
#  Example for Falcon:                                                          #
#  In $DMXDATA_ROOT/Falcon/ipqc/settings.ini                                    #
#       REL config:                                                             #
#       [rel]                                                                   #
#       nfs = /nfs/site/disks/fln_ipqrellog_1/dashboard                         #
#       url = http://sjdmxweb01.sc.intel.com:8890/ipqc/results/Falcon           #
#                                                                               #
#       snap config:                                                            #
#       [snap]                                                                  #
#       nfs = /nfs/site/disks/fln_ipqsnaplog_1/snap                             #
#       url = NA (On development)                                               #
#################################################################################
def backup(ipqc, report_format, report_template):
    """backup"""
    hierarchy = [ipqc] + ipqc.hierarchy

    for sub_ipqc in sorted(hierarchy, key=attrgetter('depth')):
        uiDebug(">>> backup.py - sub_ipqc: {} cache: {} requalify: {} is_immutable: {}" \
                .format(sub_ipqc, sub_ipqc.cache, sub_ipqc.requalify, sub_ipqc.ip.is_immutable))
        if sub_ipqc.cache and not sub_ipqc.requalify:
            continue

        if sub_ipqc.ip.is_immutable and not sub_ipqc.requalify and sub_ipqc.cache:
            continue

        (url_path, nfs_path, commands, dst_path) = get_info(ipqc, sub_ipqc)
        ret = handle_ip_error_during_creation(sub_ipqc, url_path, nfs_path, commands, report_format)

        if ret != 0:
            continue

        ################################################################################
        # First generate the report of the atomic level of an IP aka deliverable level
        ################################################################################
        for deliverable in sub_ipqc.ip.deliverables:
            uiDebug(">>> backup.py {} {}" .format(sub_ipqc.ip.name, deliverable.name))
            if not file_accessible(os.path.join(sub_ipqc.ip.workdir, deliverable.name, \
                    'ipqc.html'), os.F_OK):
                continue

            uiDebug(">>> backup.py: {}" .format(dst_path))
            if deliverable.bom == '':
                continue

            if ipqc.ip.is_immutable and not ipqc.requalify:
                (deliverable_url_path, deliverable_nfs_path) = get_catalog_paths(sub_ipqc.ip.name, \
                        sub_ipqc.ip.bom, sub_ipqc.ip.milestone, deliverable)
            else:
                (deliverable_url_path, deliverable_nfs_path) = ( \
                        _ARC_URL + os.path.join(dst_path, sub_ipqc.ip.name, deliverable.name), \
                        os.path.join(dst_path, sub_ipqc.ip.name, deliverable.name) \
                    )

            filepath = os.path.realpath(os.path.join(deliverable_nfs_path, 'ipqc.' + report_format))
            filename = os.path.basename(filepath)

            if file_accessible(filepath, os.F_OK):
                deliverable.report = os.path.join(deliverable_url_path, filename)
            else:
                run("{} -p {}" .format(commands["mkdir"], deliverable_nfs_path))
                cmd = "{} -a --exclude '*.f' {}/ {}" .format(commands["rsync"], \
                        os.path.join(sub_ipqc.ip.workdir, deliverable.name), deliverable_nfs_path)
                uiInfo("Running {}" .format(cmd))
                (code, out) = run_command(cmd)

                if code != 0:
                    uiError(out)

                if not file_accessible(filepath, os.F_OK):
                    deliverable.report = ''
                else:
                    with open(filepath, 'r') as fid:
                        html = fid.read()
                    html = replace(os.path.join(sub_ipqc.ip.workdir, deliverable.name), \
                            deliverable_url_path, html)
                    html = html_replace_deliverable(html, ipqc, sub_ipqc, deliverable, dst_path)
                    html = replace(sub_ipqc.ip.workdir, url_path, html)

                    with open(os.path.join(sub_ipqc.ip.workdir, deliverable.name, 'tmp'), 'w') as \
                            fid:
                        print(html, file=fid)

                    run("{} -a {} {}" .format(commands["rsync"], \
                            os.path.join(sub_ipqc.ip.workdir, deliverable.name, 'tmp'), \
                            os.path.join(deliverable_nfs_path, filename)))

                    deliverable.report = os.path.join(deliverable_url_path, filename)
                    run('{} {}' .format(commands["chmod"], deliverable_nfs_path))


        ################################################################################
        # Then generates root level report aka IP level
        ################################################################################
        filename = os.path.basename(sub_ipqc.ip.report_nfs)
        filepath = os.path.join(nfs_path, filename)
        list_files = [filepath]

        if not file_accessible(filepath, os.F_OK):
            run("{} -p {}" .format(commands["mkdir"], nfs_path))
            with open(os.path.join(sub_ipqc.ip.workdir, 'all.configs'), 'w') as fid:
                print(sub_ipqc.ip.boms, file=fid)

            run("{} -a {} {}/" .format(commands["rsync"], os.path.join(sub_ipqc.ip.workdir, \
                    'all.configs'), nfs_path))
            run("{} -a {} {}/" .format(commands["rsync"], os.path.join(sub_ipqc.ip.workdir, \
                    'ipqc*.html'), nfs_path))

            run("{} -a {} {}/" .format(commands["rsync"], os.path.join(sub_ipqc.ip.workdir, \
                    'ip_graph.pdf'), nfs_path))
            run("{} -a {} {}/" .format(commands["rsync"], \
                    os.path.join(sub_ipqc.ip.record_file), nfs_path))
            run('{} {}' .format(commands["chmod"], nfs_path))

            if _SIMPLE in report_template:
                list_files.append(os.path.join(nfs_path, 'ipqc.html'))

            for report_file in list_files:

                with open(report_file, 'r') as fid:

                    html = fid.read()
                    html = replace(os.path.join(sub_ipqc.ip.workdir, 'ip_graph.pdf'), \
                            os.path.join(url_path, 'ip_graph.pdf'), html)
                    html = replace(os.path.join(sub_ipqc.ip.workdir, 'ipqc.html'), \
                            os.path.join(url_path, 'ipqc.html'), html)

                    if report_template == _FUNCTIONALITY:
                        replace_functionality(sub_ipqc.ip, url_path, nfs_path, commands["rsync"], \
                                commands["chmod"])


                for deliverable in sub_ipqc.ip.deliverables:
                    if deliverable.report != None:
                        html = replace(os.path.join(sub_ipqc.ip.workdir, deliverable.name, \
                                'ipqc.html'), deliverable.report, html)

                for s_ipqc in sub_ipqc.top_hierarchy:
                    if (ipqc.ip.is_immutable) and (ipqc.requalify is False):
                        sub_ipqc_report_path = get_catalog_paths(s_ipqc.ip.name, s_ipqc.ip.bom, \
                                s_ipqc.ip.milestone)
                    else:
                        sub_ipqc_report_path = (_ARC_URL + os.path.join(dst_path, s_ipqc.ip.name), \
                                os.path.join(dst_path, s_ipqc.ip.name))
                    if report_template == _VIEW:
                        html = replace(os.path.join(s_ipqc.ip.workdir, 'ipqc.html'), \
                                os.path.join(sub_ipqc_report_path[0], 'ipqc.html'), html)
                    else:
                        html = replace(s_ipqc.ip.workdir, sub_ipqc_report_path[0], html)
                        replace_functionality(s_ipqc.ip, sub_ipqc_report_path[0], nfs_path, \
                                commands["rsync"], commands["chmod"])


                for cell in sub_ipqc.ip.topcells:
                    cell_filename = 'ipqc_'+cell.name+'.html'
                    html = replace(os.path.join(sub_ipqc.ip.workdir, cell_filename), \
                            os.path.join(url_path, cell_filename), html)

                if len(sub_ipqc.ip.topcells) != 0:
                    easy_parallelize_replace(sub_ipqc.ip, nfs_path, url_path, commands, \
                            sub_ipqc.requalify)

                if (report_template == _FUNCTIONALITY) and (sub_ipqc == ipqc):
                    hierarchy = ipqc.hierarchy + [ipqc]
                    for deliverable in ipqc.deliverables:
                        d_filepath = os.path.join(nfs_path, 'ipqc_' + deliverable + '.html')

                        if not file_accessible(d_filepath, os.F_OK):
                            continue

                        with open(d_filepath, 'r') as f_d:
                            html_deliverable = f_d.read()
                        for s_ipqc in hierarchy:
                            sub_ipqc_report_path = (_ARC_URL + os.path.join(dst_path, \
                                    s_ipqc.ip.name), os.path.join(dst_path, s_ipqc.ip.name))
                            html_deliverable = replace(s_ipqc.ip.workdir, sub_ipqc_report_path[0], \
                                    html_deliverable)
                        with open(d_filepath, 'w') as f_d:
                            print(html_deliverable, file=f_d)

                html = replace(sub_ipqc.ip.workdir, url_path, html)

                ip_html = os.path.join(sub_ipqc.ip.workdir, 'tmp')
                with open(ip_html, 'w') as fid:
                    print(html, file=fid)
                run("{} -a {} {}" .format(commands["rsync"], \
                        os.path.join(sub_ipqc.ip.workdir, 'tmp'), report_file))
                run('{} {}' .format(commands["chmod"], report_file))

            sub_ipqc.ip.report_nfs = filepath
            sub_ipqc.ip.report_url = os.path.join(url_path, filename)

        else:
            sub_ipqc.ip.report_nfs = filepath
            sub_ipqc.ip.report_url = os.path.join(url_path, filename)

    return ipqc.ip.report_nfs
