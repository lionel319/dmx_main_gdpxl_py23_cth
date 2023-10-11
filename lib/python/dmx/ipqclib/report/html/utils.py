from __future__ import print_function
import os
import re
import json
from operator import attrgetter
from dmx.ipqclib.utils import run_command, get_catalog_paths, file_accessible
from dmx.ipqclib.log import uiInfo
from dmx.ipqclib.settings import _FATAL, _FAILED, _PASSED, _WARNING, _CHECKER_SKIPPED, _UNNEEDED, _NA_MILESTONE, _NOT_POR, _ALL_WAIVED, _NA, status_data, _DB_DEVICE, _DELIVERABLES_DESCRIPTION
from dmx.utillib.configobj import ConfigObj
from dmx.ipqclib.report.html.legend import legend
from dmx.ipqclib.report.html.log import set_log

###########################################
# Header common to every hTML IPQC template
###########################################
def header(filepath, url):
    f = open(filepath, 'w')
    print("<!DOCTYPE html>", file=f)
    print("<html>", file=f)
    print("<head>", file=f)
    print("<title>IPQC Dashboard</title>", file=f)
    print("</head>", file=f)
    print("<body>", file=f)
    print("<div>", file=f)


    ##########################################################################
    # IPQC - Header Section
    ##########################################################################
    print('<div style="width: 100%; display:table;  border-top: 1px solid #ccc; border-left: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc; margin-left: 0%">', file=f)
    print('<table border="0" width="100%" style="text-align:center; font-family: arial, helvetica, sans-serif;"> \
            <tr style="background-color: #E0E0E0"><th style="width: 10%; text-align: center; font-weight: bold; font-size: 15px; background-color: #E0E0E0;"><a style="color: blue;" href={}>HOME</a> | <a style="color: blue;" href={} target="_blank">IPQC CATALOG</a></th> \
            <th style="width: 80%; text-align: center; font-family: arial, helvetica, sans-serif; font-size:25px; background-color: #E0E0E0;">IPQC Dashboard</th> \
            <th style="width: 10%; text-align: center; font-size:15px; background-color: #E0E0E0;">Intel - PSG</th></tr> \
            </table></div>' .format(os.path.join(url, os.path.basename(filepath)), "http://scypsgdmxweb01.sc.intel.com:8891/"), file=f)

    f.close()
    return

def executive_summary(filepath, ipqc):

    # get IP owner email
    (code, out) = run_command("finger {} | head -n 1 | awk -F'Name: ' '{{print $2}}'" .format(ipqc.ip.owner))
    if 'no such user' in out:
        owner = ipqc.ip.owner
    else:
        owner = out.strip()


    f = open(filepath,'a')
    ##########################################################################
    # IPQC - IP Summary Section
    ##########################################################################
    print('<div style="width: 100%; display:table; border-top: 1px solid #ccc; border-left: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc; margin-left: 0%">', file=f)
    print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 10%; background-color: #B4D8E7">Executive summary for IP {}</h2> \
            <table width="90%" style="margin-left:10%; text-align:left; font-family: arial, helvetica, sans-serif;"> \
            <tr><td style=\"width: 15%; font-weight: bold;\">Project:</td><td>{} ({})</td></tr> \
            <tr><td style=\"width: 15%; font-weight: bold;\">IP release:</td><td><a href={} ; type=\"application/pdf\">{}@{}</a> ({} type)</td></tr> \
            <tr><td style=\"width: 15%; font-weight: bold;\">sub-IP(s):</td><td>{}</td></tr> \
            <tr><td style=\"width: 15%; font-weight: bold;\">IP owner:</td><td><a href=\"mailto:{}@intel.com?subject=ipqc dashboard\">{}@intel.com</a></td></tr> \
            <tr><td style=\"width: 15%; font-weight: bold;\">Milestone:</td><td>{}</td></tr> \
            <tr><td style=\"width: 15%; font-weight: bold;\">Number of tests (Top IP + Sub IPs):</td><td>{} ({} passed / {} waived / {} failed / {} fatal / {} unneeded / {} NA)</td></tr> \
    </table>' .format(ipqc.ip.name, ipqc.ip.project, ipqc.ip.family, ipqc.ip.graph, ipqc.ip.name, ipqc.ip.bom, ipqc.ip.iptype, len(ipqc.top_hierarchy), owner, owner, ipqc.ip.milestone, (ipqc.ip.nb_pass_global + ipqc.ip.nb_fail_global + ipqc.ip.nb_fatal_global + ipqc.ip.nb_warning_global + ipqc.ip.nb_unneeded_global + ipqc.ip.nb_na_global), ipqc.ip.nb_pass_global, ipqc.ip.nb_warning_global, ipqc.ip.nb_fail_global, ipqc.ip.nb_fatal_global, ipqc.ip.nb_unneeded_global, ipqc.ip.nb_na_global), file=f)

    print("<br>", file=f)
    legend(f)
    print("<br>", file=f)
    print("<br>", file=f)
    f.close()
    return

##########################################################################
# IPQC - Environment Information
#   --> ARC Bundle
#   --> System Information (OS, Release, Host, ...)
##########################################################################
def set_environment_info(filepath, ipqc):
    f = open(filepath,'a')
    print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 10%; background-color: #B4D8E7">Environment Information</h2>', file=f)
    print('<table width="90%" style="margin-left:10%; text-align:left; font-family: arial, helvetica, sans-serif;"> \
            <tr><td style="width: 15%; font-weight: bold;">Command:</td><td>{}</td></tr> \
            <tr><td style="width: 15%; font-weight: bold;">ARC bundle:</td><td>{}</td></tr> \
            <tr><td style="width: 15%; font-weight: bold;">Operating System:</td><td>{}</td></tr> \
            <tr><td style="width: 15%; font-weight: bold;">Hostname:</td><td>{}</td></tr> \
            <tr><td style="width: 15%; font-weight: bold;">Kernel Release:</td><td>{}</td></tr> \
            <tr><td style="width: 15%; font-weight: bold;">Machine:</td><td>{}</td></tr> \
        </table>' .format(ipqc.environment.cmd, ipqc.environment.arc_resources, ipqc.environment.os_name, ipqc.environment.hostname, ipqc.environment.release, ipqc.environment.machine), file=f)

    print("<br>", file=f)
    print("<br>", file=f)
    f.close()
    return

def get_general_info(ipqc):
    roadmap_url = ''
    tests_url   = ''
    ipqc_info   = ConfigObj(os.path.join(os.getenv('DMXDATA_ROOT'), ipqc.family.name, 'ipqc', 'settings.ini'))
    roadmap_url = re.sub('&device;', _DB_DEVICE, ipqc_info['RoadmapURL'])
    tests_url   = re.sub('&device;', _DB_DEVICE, ipqc_info['TestsURL'])
    return (roadmap_url, tests_url)

##########################################################################
# IPQC - General Information Section
##########################################################################
def set_general_info(filepath, ipqc):
    (roadmap_url, tests_url) = get_general_info(ipqc)
    f = open(filepath,'a')
    print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 10%; background-color: #B4D8E7">General Information</h2>', file=f)
    print('<table width="90%" style="margin-left:10%; text-align:left; font-family: arial, helvetica, sans-serif;"> \
            <tr><td style="width: 20%; font-weight: bold;"><a href="{}">{} Roadmap</a></td></tr> \
            <tr><td style="width: 20%; font-weight: bold;"><a href="{}">{} Tests</a></td></tr> \
            <tr><td style="width: 20%; font-weight: bold;"></td></tr> \
            <tr><td style="width: 20%; font-weight: bold;">Process: {}</td></tr> \
            <tr><td style="width: 20%; font-weight: bold;">Product: {}</td></tr> \
            <tr><td style="width: 20%; font-weight: bold;">Device: {}</td></tr> \
            </table>' .format(roadmap_url, ipqc.family.name, tests_url, ipqc.family.name, os.getenv("DB_PROCESS"), ipqc.ip.workspace.project, os.getenv("DB_DEVICE")), file=f)
    print("<br>", file=f)
    f.close()
    return

def get_status_for_deliverable(status):

    if _FATAL in status:
        return _FATAL
    elif _FAILED in status:
        return _FAILED
    elif _WARNING in status:
        return _WARNING
    elif _PASSED in status:
        return _PASSED
    elif _NA_MILESTONE in status:
        return _NA_MILESTONE
    elif _ALL_WAIVED in status:
        return _ALL_WAIVED
    elif _NA in status:
        return _NA
    elif _UNNEEDED in status:
        return _UNNEEDED
    elif _CHECKER_SKIPPED in status:
        return _CHECKER_SKIPPED
    else:
        return _NA

def get_deliverable_score(ipqc, deliverable):

    total = 0
    ipqcs = [ipqc] + ipqc.top_hierarchy

    for s_ipqc in ipqcs:

        for cell in s_ipqc.ip.topcells:
            for d in cell.deliverables:

                if d.name != deliverable:
                    continue

                total = total + d.nb_pass + d.nb_fail + d.nb_fatal + d.nb_warning + d.nb_unneeded + d.nb_na
                break

    return total

def compute_deliverable_status_for_ip(top_ipqc, ipqc, deliverable):

    status = []
    list_of_ips = ipqc.ip.flat_hierarchy + [ipqc.ip.name]
    ipqcs = [top_ipqc] + top_ipqc.top_hierarchy


    for s_ipqc in ipqcs:

        if not s_ipqc.ip.name in list_of_ips:
            continue

        for deliverable_of_s_ipqc in s_ipqc.ip.deliverables:

            if deliverable_of_s_ipqc.name != deliverable:
                continue

            status.append(deliverable_of_s_ipqc.status)
            break

    return get_status_for_deliverable(status)


def get_deliverable_dashboard(top_ipqc, ipqc, deliverable):

    if ipqc.ip.get_deliverable_ipqc(deliverable) != None:
        d = ipqc.ip.get_deliverable_ipqc(deliverable)
    else:
        for sub_ipqc in sorted(top_ipqc.top_hierarchy, key=attrgetter('depth')):

            if sub_ipqc.ip.name != ipqc.ip.name:
                continue

            if sub_ipqc.ip.name in ipqc.ip.flat_hierarchy:
                d = sub_ipqc.ip.get_deliverable_ipqc(deliverable)
                if d != None:
                    ipqc = sub_ipqc
                    break

    try:
        if (ipqc.ip.cache == True) and (ipqc.requalify == False):
            (deliverable_url_path, deliverable_nfs_path) = get_catalog_paths(ipqc.ip.name, ipqc.ip.bom, ipqc.ip.milestone, d)
            d.report = os.path.join(deliverable_url_path, 'ipqc.html')
            return d.report
        else:
            (deliverable_url_path, deliverable_nfs_path) = (os.path.join(ipqc.ip.workdir, d.name), os.path.join(ipqc.ip.workdir, d.name))

        return os.path.join(deliverable_nfs_path, 'ipqc.html')
    except NameError:
        return ''

def score_table(filepath, ipqc, depth='all'):
    f = open(filepath,'a')
    if ipqc.deliverables == []:
        deliverables = [d.name for d in ipqc.ip.family.get_all_deliverables()]

    deliverables_dict = {}
    total = 0

    ipqcs = [ipqc] + ipqc.top_hierarchy

    for s_ipqc in ipqcs:
        for deliverable in s_ipqc.ip.deliverables:
            if not deliverable.name in deliverables_dict.keys():
                deliverables_dict[deliverable.name] = 0

    deliverables_list = sorted(deliverables_dict.keys())

    print('<table border="1" style="text-align: center; margin-left:10%; border: 1px solid; border-color:black; border-collapse: collapse;">', file=f)
    print('<tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD; font-weight: bold; font-family: arial, helvetica, sans-serif;">', file=f)
    print('<th style="background:linear-gradient(to top right, #66CCAA 0%,#66CCAA 50%, #1874CD 50.5%,#1874CD 100%);line-height:1;"> \
            <div style="margin-left:2em;text-align:right;"><span style="color:#FFFFFF">Deliverables</span></div> \
            <div style="margin-right:2em;text-align:left;"><span style="color:#000000">IPs</span></div> \
        </th>', file=f)
    # First line list deliverables
    for deliverable in deliverables_list:
        print('<th style="width=7%">{}</th>' .format(deliverable), file=f)
#    print('<th style="color:#000000; border: 1px solid; border-color:black; font-family: arial, helvetica, sans-serif; background-color: #AAD4FF">Total</th>', file=f)
    print("</tr>", file=f)

    for sub_ipqc in sorted(ipqcs, key=attrgetter('depth')):

        if (depth != 'all') and (sub_ipqc.depth > int(depth)):
            continue

        print('<tr border="1" style="border: 1px solid; border-color:black; font-family: arial, helvetica, sans-serif;">', file=f)
        print('<th style="background-color: #66CCAA">{}#{}</th>' .format(sub_ipqc.ip.name, sub_ipqc.depth), file=f)

        for deliverable in deliverables_list:

            status = compute_deliverable_status_for_ip(ipqc, sub_ipqc, deliverable)

            report = get_deliverable_dashboard(ipqc, sub_ipqc, deliverable)
#            uiInfo("TOTO {} {} {} {}" .format(sub_ipqc.ip.name, deliverable, status, report))
            if report != '':
                if status == _FATAL:
                    print('<td style="color: #FFFFFF; background-color: {};"><a href={} target="_blank" style="color: #FFFFFF">{}</a></td>' .format(status_data[status]['color'], report, status), file=f)
                else:
                    print('<td style="background-color: {};"><a href={} target="_blank">{}</a></td>' .format(status_data[status]['color'], report, status), file=f)
            else:
                if status == _FATAL:
                    print('<td style="color: #FFFFFF; background-color: {};">{}</td>' .format(status_data[status]['color'], status), file=f)
                else:
                    print('<td style="background-color: {};">{}</td>' .format(status_data[status]['color'], status), file=f)

#        print('<td style="background-color: #AAD4FF">{}</td>' .format(sub_ipqc.ip.nb_pass + sub_ipqc.ip.nb_fail + sub_ipqc.ip.nb_fatal + sub_ipqc.ip.nb_warning + sub_ipqc.ip.nb_unneeded + sub_ipqc.ip.nb_na), file=f)

        print("</tr>", file=f)

    print('<tr border="1" style="border: 1px solid; border-color:black; font-family: arial, helvetica, sans-serif;">', file=f)
    for deliverable in deliverables_list:
        score = get_deliverable_score(ipqc, deliverable)
        total = total + score
    print('<th style="background-color: #AAD4FF">Total = {}</th>' .format(total), file=f)
    for deliverable in deliverables_list:
        score = get_deliverable_score(ipqc, deliverable)
#        total = total + score
        print('<td style="background-color: #AAD4FF">{}</td>' .format(score), file=f)
#    print('<td style="background-color: #AAD4FF">{}</td>' .format(total), file=f)
    print("</tr>", file=f)

    print("</table>", file=f)
    print("<br>", file=f)
    f.close()
    return

def get_deliverables_description():
    with open(_DELIVERABLES_DESCRIPTION, 'r') as f_description:
        return json.load(f_description)


def set_array_ip_table(f, filter_status=[]):

    keyorder_deliverable = [_PASSED, _WARNING, _FAILED, _FATAL, _NA, _ALL_WAIVED, _UNNEEDED, _NA_MILESTONE]


    nb_column = len([_PASSED, _WARNING, _FAILED, _FATAL, _UNNEEDED, _NA]) - len(filter_status)

    # https://hsdes.intel.com/resource/1409433556
    #IPQC report for power - remove unneeded count from final
    filter_unneeded =  False
    if status_data[_UNNEEDED]['option'] in filter_status:
        filter_unneeded = True

    print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 10%; background-color: #B4D8E7">Report Summary by deliverables</h2>', file=f)
    print("<br>", file=f)
    legend(f)
    print("<br>", file=f)

    ### Array of deliverables for Top IP
    print('<table border="1" width="89%" style="margin-left:10%; border: 1px solid; border-color:black; border-collapse: collapse;">', file=f)
    print('<tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD; font-weight: bold; font-family: arial, helvetica, sans-serif;">', file=f)
    print('<th border="1" rowspan=2 width="10%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Deliverables</th>', file=f)
    print('<th border="1" rowspan=2 width="27%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Description</th>', file=f)
    print('<th border="1" colspan={} width="36%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Test Result</th>' .format(nb_column), file=f)
    print('<th border="1" rowspan=2 width="16%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Total Test</th>', file=f)
    print("</tr>", file=f)

    print('<tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD; font-weight: bold; font-family: arial, helvetica, sans-serif;">', file=f)
    print('<th border="1" width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Pass</th>', file=f)
    print('<th border="1" width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Waived</th>', file=f)
    print('<th border="1" width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Fail</th>', file=f)
    print('<th border="1" width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Fatal</th>', file=f)

    if not(filter_unneeded):
        print('<th border="1" width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Unneeded</th>', file=f)

    print('<th border="1" width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">NA</th>', file=f)
    print("</tr>", file=f)

    return


# fatal
def set_checker_fatal_status(checker, f, date, status_data, logfile=None):
    if len(checker.errors_unwaived) != 0:
        print("<td style=\"color: #FFFFFF; background-color: {};\">{}</td>"  .format(status_data[_FATAL]['color'], "Unwaivable error(s)"), file=f)
        if len(checker.errors_waived) != 0:
            print("<td><a href={} ; type=\"text/plain\">{}/{}</a></td>" .format(checker.errors_waived_file, len(checker.errors_waived), checker.nb_errors), file=f)
        else:
            print("<td>0/{}</td>" .format(checker.nb_errors), file=f)
        print("<td><a href={} ; type=\"text/plain\">{}/{}</a></td>" .format(checker.errors_unwaived_file, len(checker.errors_unwaived), checker.nb_errors), file=f)
    else:
        print("<td style=\"color: #FFFFFF; background-color: {};\">{}</td>"  .format(status_data[_FATAL]['color'], "Audit not found"), file=f)
        print("<td>{}</td>" .format(_NA), file=f)
        print("<td>{}</td>" .format(_NA), file=f)


    if file_accessible(logfile, os.R_OK):
        if logfile.endswith('.html'):
            format_log = 'text/html'
        else:
            format_log = 'text/plain'

        print('<td><a href={} ; type={}>log</a></td>'  .format(logfile, format_log), file=f)
    else:
        print("<td>{}</td>"  .format(_NA), file=f)

    print('<td style="font-size:12px; background-color: #FFFFFF;">{}</td>' .format(date), file=f)

    return

# failed and skipp 
def set_checker_failed_skip_status(cellname, checker, f, date, status_data, logfile=None):
    print('<td style="background-color:{}">{}</td>' .format(status_data[checker.status]['color'], checker.status), file=f)
    print("<td>0/{}</td>" .format(checker.nb_errors), file=f)
    print("<td><a href={} ; type=\"text/plain\">{}/{}</a></td>" .format(checker.errors_unwaived_file, len(checker.errors_unwaived), checker.nb_errors), file=f)
    print('<td>{}</td>' .format(_NA), file=f)
    print('<td style="font-size:12px; background-color: #FFFFFF;">{}</td>' .format(date), file=f)
    return

# warning /failed
def set_checker_failed_warning_status(cellname, checker, f, date, status_data, logfile=None):
    if checker.has_audit_verification():
        if checker.audit.is_filelist(checker.audit.get_file(cellname)):
            print("<td style=\"background-color: {};\"><a href={} ; type=\"text/html\">{}</a></td>"  .format(status_data[checker.status]['color'], checker.audit.set_audit(cellname), checker.status), file=f)
        else:
            print("<td style=\"background-color: {};\"><a href={} ; type=\"text/xml\">{}</a></td>"  .format(status_data[checker.status]['color'], checker.audit.set_audit(cellname), checker.status), file=f)
    else:
        print('<td style="background-color:{}">{}</td>' .format(status_data[checker.status]['color'], checker.status), file=f)

    if len(checker.errors_waived) != 0:
        print("<td><a href={} ; type=\"text/plain\">{}/{}</a></td>" .format(checker.errors_waived_file, len(checker.errors_waived), checker.nb_errors), file=f)
    else:
        print("<td>0/{}</td>" .format(checker.nb_errors), file=f)

    if len(checker.errors_unwaived) != 0:
        print("<td><a href={} ; type=\"text/plain\">{}/{}</a></td>" .format(checker.errors_unwaived_file, len(checker.errors_unwaived), checker.nb_errors), file=f)
    else:
        print("<td>0/{}</td>" .format(checker.nb_errors), file=f)

    if file_accessible(logfile, os.F_OK):
        if logfile.endswith('.html'):
            format_log = 'text/html'
        else:
            format_log = 'text/plain'
        print('<td><a href={} ; type={}>log</a></td>'  .format(logfile, format_log), file=f)
    else:
        print('<td>{}</td>' .format(_NA), file=f)
    print('<td style="font-size:12px; background-color: #FFFFFF;">{}</td>' .format(date), file=f)

    return

# passed
def set_checker_passed_status(cellname, checker, f, date, status_data, logfile=None):
    if checker.has_audit_verification():
        if checker.audit.is_filelist(checker.audit.get_file(cellname)):
            print("<td style=\"background-color: {};\"><a href={} ; type=\"text/html\">{}</a></td>"  .format(status_data[_PASSED]['color'], checker.audit.set_audit(cellname), _PASSED), file=f)
        else:
            print("<td style=\"background-color: {};\"><a href={} ; type=\"text/xml\">{}</a></td>"  .format(status_data[_PASSED]['color'], checker.audit.set_audit(cellname), _PASSED), file=f)
    else:
        print('<td style="background-color:{}">{}</td>' .format(status_data[_PASSED]['color'], _PASSED), file=f)

    print("<td>{}/{}</td>" .format(len(checker.errors_waived), checker.nb_errors), file=f)
    print("<td>{}/{}</td>" .format(len(checker.errors_unwaived), checker.nb_errors), file=f)

    if file_accessible(logfile, os.F_OK):
        if logfile.endswith('.html'):
            format_log = 'text/html'
        else:
            format_log = 'text/plain'
        print('<td><a href={} ; type="{}">log</a></td>'  .format(logfile, format_log), file=f)
    else:
        print('<td>{}</td>' .format(_NA), file=f)
    print('<td style="font-size:12px; background-color: #FFFFFF;">{}</td>' .format(date), file=f)
    return

# N/A
def set_checker_na_status(f, status_data):
    print("<td style=\"background-color: {};\">{}</td>" .format(status_data[_NA]['color'], _NA), file=f)
    print("<td>{}</td>" .format(_NA), file=f)
    print("<td>{}</td>" .format(_NA), file=f)
    print("<td>{}</td>" .format(_NA), file=f)
    print('<td>{}</td>' .format(_NA), file=f)
    return


def set_check_report_by_deliverable(ipqc, waivers, deliverable_name, f, date):
    for cell in sorted(ipqc.ip.topcells, key=attrgetter('name')):

        for deliverable in cell.deliverables:
            if deliverable.name != deliverable_name:
                continue

            j = 0
            flag = []

            if (deliverable.status == _NA) or (deliverable.status == _NA_MILESTONE) or (deliverable.is_unneeded):

                if deliverable.nb_checkers != 0:
                    for checker in deliverable.checkers:
                        print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)
                        if j == 0:
                            print("<td rowspan={} style=\"background-color: {};\">{}</td>" .format(deliverable.nb_checkers, status_data[deliverable.status]['color'], cell.name), file=f)
                            j = j + 1

                        if checker.subflow:
                            print('<td style=\"background-color: #FFFFFF\">{} ({})</td>'  .format(checker.name, checker.subflow), file=f)
                        else:
                            print('<td style=\"background-color: #FFFFFF\">{}</td>'  .format(checker.name), file=f)

                        if checker.has_waivers():
                            print("<td><a href={} ; type=\"text/plain\">{}</a></td>" .format(checker.waivers_file, waivers), file=f)
                        else:
                            print("<td>{}</td>" .format(_NA), file=f)

                        if (deliverable.status == _NA_MILESTONE):
                            print('<td colspan=5 style="background-color: {}">{}</td>' .format(status_data[deliverable.status]['color'], deliverable.status), file=f)
                        elif deliverable.is_unneeded:
                            print('<td colspan=5 style="background-color: {}">{}</td>' .format(status_data[deliverable.status]['color'], _NOT_POR), file=f)
                        else:
                            print('<td style="background-color: {}">{}</td>' .format(status_data[deliverable.status]['color'], deliverable.status), file=f)
                            print("<td>{}</td>" .format(_NA), file=f)
                            print("<td>{}</td>" .format(_NA), file=f)
                            print("<td>{}</td>" .format(_NA), file=f)
                            print("<td>{}</td>" .format(_NA), file=f)
                        print("</tr>", file=f)
                else:
                    print('<tr style="text-align:center; font-family: arial, helvetica, sans-serif; ">', file=f)
                    print("<td>{}</td>" .format(cell.name), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("</tr>", file=f)
                continue

            if (deliverable.status == _ALL_WAIVED):
                if deliverable.nb_checkers != 0:
                    for checker in deliverable.checkers:
                        print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)
                        if j == 0:
                            print("<td rowspan={} style=\"background-color: {};\">{}</td>" .format(deliverable.nb_checkers, status_data[deliverable.status]['color'], cell.name), file=f)
                            j = j + 1

                        if checker.subflow:
                            print('<td style=\"background-color: #FFFFFF\">{} ({})</td>'  .format(checker.name, checker.subflow), file=f)
                        else:
                            print('<td style=\"background-color: #FFFFFF\">{}</td>'  .format(checker.name), file=f)

                        if checker.has_waivers():
                            print("<td><a href={} ; type=\"text/plain\">{}</a></td>" .format(checker.waivers_file, waivers), file=f)
                        else:
                            print("<td>{}</td>" .format(_NA), file=f)

                        print("<td style=\"background-color: {};\">{}</td>" .format(status_data[deliverable.status]['color'], _ALL_WAIVED), file=f)
                        print("<td>{}</td>" .format(_NA), file=f)
                        print("<td>{}</td>" .format(_NA), file=f)
                        print("<td>{}</td>" .format(_NA), file=f)
                        print("<td>{}</td>" .format(_NA), file=f)
                        print("</tr>", file=f)
                else:
                    print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)
                    print("<td style=\"background-color: {};\">{}</td>" .format(status_data[deliverable.status]['color'], cell.name), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("</tr>", file=f)

                continue

            if deliverable.deliverable_existence['unwaived'] != []:
                if deliverable.nb_checkers != 0:
                    for checker in deliverable.checkers:
                        print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)
                        if j == 0:
                            print("<td rowspan={} style=\"color: #FFFFFF; background-color: {};\">{}</td>" .format(deliverable.nb_checkers, status_data[deliverable.status]['color'], deliverable.name.upper()), file=f)
                            j = j + 1

                            if checker.subflow:
                                print('<td style=\"background-color: #FFFFFF\">{} ({})</td>'  .format(checker.name, checker.subflow), file=f)
                            else:
                                print('<td style=\"background-color: #FFFFFF\">{}</td>'  .format(checker.name), file=f)

                            print("<td>{}</td>" .format(_NA), file=f)
                            print("<td colspan=5 style=\"color: #FFFFFF; background-color: {};\">{}</td>" .format(status_data[_FATAL]['color'], deliverable.deliverable_existence['unwaived'][0].error), file=f)
                else:
                    print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)
                    print("<td style=\"color: #FFFFFF; background-color: {};\">{}</td>" .format(status_data[_FATAL]['color'], cell.name), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td colspan=5 style=\"color: #FFFFFF; background-color: {};\">{}</td>" .format(status_data[_FATAL]['color'], deliverable.deliverable_existence['unwaived'][0].error), file=f)
                    print("</tr>", file=f)

                continue


            for checker in sorted(deliverable.checkers, key=attrgetter('name')):
                logfile = set_log(ipqc.ip, cell, deliverable, checker)
                print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)

                if j == 0:
                    if deliverable.status == _FATAL:
                        print("<td rowspan={} style=\"color: #FFFFFF; background-color: {}; border-top: white;\">{}</td>" .format(deliverable.nb_checkers, status_data[deliverable.status]['color'], cell.name), file=f)
                    else:
                        print("<td rowspan={} style=\"background-color: {};\">{}</td>" .format(deliverable.nb_checkers, status_data[deliverable.status]['color'], cell.name), file=f)

                    j = j + 1

                if checker.subflow:
                    print("<td style=\"background-color: #FFFFFF;\">{} ({})</td>"  .format(checker.name, checker.subflow), file=f)
                else:
                    print("<td style=\"background-color: #FFFFFF;\">{}</td>"  .format(checker.name), file=f)

                if checker.has_waivers():
                    print("<td><a href={} ; type=\"text/plain\">{}</a></td>" .format(checker.waivers_file, waivers), file=f)
                else:
                    print("<td>{}</td>" .format(_NA), file=f)

                ###############################################
                # no checker execution - has audit verification
                ###############################################
                if (not checker.has_checker_execution()) and (checker.has_audit_verification()):
                    flag.append(checker.name)

                    ###########
                    # PASSED
                    ###########
                    if checker.status == _PASSED:
                        set_checker_passed_status(cell.name, checker, f, date, status_data, logfile)
                        continue

                    ########################
                    # ERROR_WAIVED OR FAILED
                    ########################
                    if (checker.status == _WARNING) or (checker.status == _FAILED):
                        set_checker_failed_warning_status(cell.name, checker, f, date, status_data, logfile)
                        continue


#                    ################
#                    # CHECKER_WAIVED
#                    ################
#                    if checker.status == _CHECKER_WAIVED :
#                        print("<td style=\"background-color: {};\">{}</td>"  .format(status_data[_CHECKER_WAIVED]['color'], _CHECKER_WAIVED), file=f)
#                        print("<td>{}</td>" .format(_NA), file=f)
#                        print("<td>{}</td>" .format(_NA), file=f)
#                        print('<td>{}</td>' .format(_NA), file=f)
#                        print('<td style="font-size:12px; background-color: #FFFFFF;">{}</td>' .format(date), file=f)
#                        continue


                    ###########
                    # FATAL
                    ###########
                    if checker.status == _FATAL:
                        set_checker_fatal_status(checker, f, date, status_data, logfile)
                        continue


                    ###############
                    # NA
                    ###############
                    if checker.status == _NA:
                        set_checker_na_status(f, status_data)
                        continue



                ################################################
                # has checker execution
                ################################################
                if checker.has_checker_execution():
                    flag.append(checker.name)

                    ###########
                    # PASSED
                    ###########
                    if checker.status == _PASSED :
                        set_checker_passed_status(cell.name, checker, f, date, status_data, logfile)
                        continue

                    ########################
                    # ERROR_WAIVED OR FAILED
                    ########################
                    if (checker.status == _WARNING) or  (checker.status == _FAILED):
                        set_checker_failed_warning_status(cell.name, checker, f, date, status_data, logfile)
                        continue

                    if (checker.status == _CHECKER_SKIPPED):
                        set_checker_failed_skip_status(cell.name, checker, f, date, status_data, logfile)
                        continue

#                    ################
#                    # CHECKER_WAIVED
#                    ################
#                    if checker.status == _CHECKER_WAIVED :
#                        print("<td style=\"background-color: {};\">{}</td>"  .format(status_data[_CHECKER_WAIVED]['color'], _CHECKER_WAIVED), file=f)
#                        print("<td>{}</td>" .format(_NA), file=f)
#                        print("<td>{}</td>" .format(_NA), file=f)
#                        print('<td>{}</td>' .format(_NA), file=f)
#                        print('<td style="font-size:12px; background-color: #FFFFFF;">{}</td>' .format(date), file=f)
#
#                        continue

                    ###########
                    # FATAL
                    ###########
                    if checker.status == _FATAL:
                        set_checker_fatal_status(checker, f, date, status_data, logfile)
                        continue

                    ###############
                    # NA
                    ###############
                    if checker.status == _NA:
                        set_checker_na_status(f, status_data)
                        continue



                ################################################
                # no checker execution - no audit verification
                ################################################
                if not(checker.has_checker_execution()) and not(checker.has_audit_verification()):
                    flag.append(checker.name)
                    ###############
                    # NA
                    ###############
                    if checker.status == _NA:
                        set_checker_na_status(f, status_data)
                        continue

            print("</tr>", file=f)

    return

