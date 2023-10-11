#!/usr/bin/env python
"""report_deliverable.py

    Example: http://sjdmxweb01.sc.intel.com:8891/falcon_dashboards/fmesram/4.0/rtlcompchk/rel/REL4.0FM6revB0__19ww304a/ipqc.html
"""
from __future__ import print_function
import os
import datetime
from dmx.ipqclib.utils import dir_accessible
from dmx.ipqclib.settings import _PASSED, _FAILED, _FATAL, _NA, _NA_MILESTONE, _WARNING, \
        _UNNEEDED, _FATAL_SYSTEM, status_data
from dmx.ipqclib.report.html.legend import legend
from dmx.ipqclib.report.html.utils import set_check_report_by_deliverable

def get_deliverable_score(deliverable, deliverable_score):
    """get_deliverable_score"""
    (tmp_nb_pass, tmp_nb_fail, tmp_nb_fatal, tmp_nb_warning, tmp_nb_unneeded, tmp_nb_na) = \
            deliverable.get_check_info()
    deliverable_score["nb_pass"] = tmp_nb_pass + deliverable_score["nb_pass"]
    deliverable_score["nb_warning"] = tmp_nb_warning + deliverable_score["nb_warning"]
    deliverable_score["nb_fail"] = tmp_nb_fail + deliverable_score["nb_fail"]
    deliverable_score["nb_fatal"] = tmp_nb_fatal + deliverable_score["nb_fatal"]
    deliverable_score["nb_unneeded"] = tmp_nb_unneeded + deliverable_score["nb_unneeded"]
    deliverable_score["nb_na"] = tmp_nb_na + deliverable_score["nb_na"]

    return(deliverable_score["nb_pass"], deliverable_score["nb_warning"], \
            deliverable_score["nb_fail"], deliverable_score["nb_fatal"], \
            deliverable_score["nb_unneeded"], deliverable_score["nb_na"])


def set_deliverable_score(ipqc, deliverable_ip_level):
    """set_deliverable_score"""

    deliverable_score = {"nb_pass": 0, "nb_warning": 0, "nb_fail": 0, "nb_fatal": 0, \
                    "nb_unneeded": 0, "nb_na": 0}

    for cell in ipqc.ip.topcells:

        for deliverable in cell.deliverables:

            if deliverable.name == deliverable_ip_level.name:

                (deliverable_score["nb_pass"], \
                    deliverable_score["nb_warning"], \
                    deliverable_score["nb_fail"], \
                    deliverable_score["nb_fatal"], \
                    deliverable_score["nb_unneeded"], \
                    deliverable_score["nb_na"] \
                ) = get_deliverable_score(deliverable, deliverable_score)

    deliverable_ip_level.report = os.path.realpath(os.path.join(ipqc.ip.workdir, \
            deliverable_ip_level.name, 'ipqc.html'))
    deliverable_ip_level.nb_pass = deliverable_score["nb_pass"]
    deliverable_ip_level.nb_warning = deliverable_score["nb_warning"]
    deliverable_ip_level.nb_fail = deliverable_score["nb_fail"]
    deliverable_ip_level.nb_fatal = deliverable_score["nb_fatal"]
    deliverable_ip_level.nb_unneeded = deliverable_score["nb_unneeded"]
    deliverable_ip_level.nb_na = deliverable_score["nb_na"]

    return (deliverable_score["nb_pass"], deliverable_score["nb_warning"], \
            deliverable_score["nb_fail"], deliverable_score["nb_fatal"], \
            deliverable_score["nb_unneeded"], deliverable_score["nb_na"])

def print_owner(fid, deliverable_ip_level):
    """print_owner"""
    if deliverable_ip_level.owner != '':
        print("<td style=\"background-color: #E0E0E0;\">\
            <a href=\"mailto:{}@intel.com?subject=ipqc dashboard\">{}@intel.com</a>\
            </td>" .format(deliverable_ip_level.owner, deliverable_ip_level.owner),\
            file=fid)
    else:
        print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (_NA), file=fid)

def print_bom(fid, deliverable_ip_level):
    """print_bom"""
    if deliverable_ip_level.bom != '':
        print("<td style=\"background-color: #E0E0E0;\">%s@%s</td>" % \
        (deliverable_ip_level.name, deliverable_ip_level.bom),\
        file=fid)
    else:
        print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (_NA), file=fid)

def print_pass_status(fid, deliverable_ip_level, nb_pass):
    """print_pass_status"""
    if nb_pass == 0:
        print("<td>{}</td>"  .format(nb_pass), file=fid)
    else:
        print("<td style=\"background-color: {};\"><a href={}>{}</a></td>"  \
            .format(status_data[_PASSED]['color'], deliverable_ip_level.report, nb_pass), file=fid)

def print_warning_status(fid, deliverable_ip_level, nb_warning):
    """print_warning_status"""
    if nb_warning == 0:
        print("<td>{}</td>"  .format(nb_warning), file=fid)
    else:
        print("<td style=\"background-color: {};\"><a href={}>{}</a></td>"  \
            .format(status_data[_WARNING]['color'], deliverable_ip_level.report, nb_warning), \
            file=fid)

def print_fail_status(fid, deliverable_ip_level, nb_fail):
    """print_fail_status"""
    if nb_fail == 0:
        print("<td>{}</td>"  .format(nb_fail), file=fid)
    else:
        print("<td style=\"background-color: {};\"><a href={}>{}</a></td>"  \
            .format(status_data[_FAILED]['color'], deliverable_ip_level.report, nb_fail), file=fid)

def print_fatal_status(fid, deliverable_ip_level, nb_fatal):
    """print_fatal_status"""
    if nb_fatal == 0:
        print("<td>{}</td>"  .format(nb_fatal), file=fid)
    elif deliverable_ip_level.bom == '':
        print("<td style=\"color: #FFFFFF; background-color: {};\">{}</td>"  \
            .format(status_data[_FATAL]['color'], nb_fatal), file=fid)
    else:
        print("<td style=\"color: #FFFFFF; background-color: {};\"><a href={} \
            style=\"color: #FFFFFF;\">{}</a></td>" .format(status_data[_FATAL]['color'], \
            deliverable_ip_level.report, nb_fatal), file=fid)

def print_unneeded_status(fid, deliverable_ip_level, nb_unneeded, filter_unneeded):
    """print_unneeded_status"""
    if not filter_unneeded:
        if nb_unneeded == 0:
            print("<td>{}</td>"  .format(nb_unneeded), file=fid)
        elif deliverable_ip_level.bom == '':
            print("<td td style=\"background-color: {};\">{}</td>"  \
                .format(status_data[_UNNEEDED]['color'], nb_unneeded), file=fid)
        else:
            print("<td td style=\"background-color: {};\"><a href={}>{}</a></td>"  \
                .format(status_data[_UNNEEDED]['color'], deliverable_ip_level.report, \
                nb_unneeded), file=fid)

def print_na_status(fid, nb_na):
    """print_na_status"""
    if nb_na == 0:
        print("<td>{}</td>"  .format(nb_na), file=fid)
    else:
        print("<td style=\"background-color: {};\">{}</td>" .format(status_data[_NA]['color'], \
                nb_na), file=fid)


def print_na_milestone_status(fid, nb_column):
    """print_na_milestone_status"""
    print("<td colspan={} style=\"background-color: {};\">{}</td>" \
        .format(nb_column, status_data[_NA_MILESTONE]['color'], _NA_MILESTONE), \
        file=fid)

def print_deliverable_score(fid, deliverable_score):
    """print_na_milestone_status"""
    print("<td>{}</td>\n \
        </tr>"  .format(deliverable_score["nb_pass"] + \
        deliverable_score["nb_warning"] + \
        deliverable_score["nb_fail"] + \
        deliverable_score["nb_fatal"] + \
        deliverable_score["nb_unneeded"] + deliverable_score["nb_na"]), file=fid)

def print_hierarchy_score(fid, total_dict, filter_unneeded):
    """print_hierarchy_score"""
    total = total_dict["nb_pass"] + total_dict["nb_warning"] + total_dict["nb_fail"] + \
            total_dict["nb_fatal"] + total_dict["nb_na"]
    print("<tr style=\"background-color: #AAD4FF; font-weight: bold; font-family: arial, \
            helvetica, sans-serif;\">", file=fid)
    print('<th>Total</th>', file=fid)
    print('<th></th>', file=fid)
    print('<th></th>', file=fid)
    print("<th>{}</th>" .format(total_dict["nb_pass"]), file=fid)
    print("<th>{}</th>" .format(total_dict["nb_warning"]), file=fid)
    print("<th>{}</th>" .format(total_dict["nb_fail"]), file=fid)
    print("<th>{}</th>" .format(total_dict["nb_fatal"]), file=fid)

    if not filter_unneeded:
        print("<th>{}</th>" .format(total_dict["nb_unneeded"]), file=fid)
        total = total + total_dict["nb_unneeded"]
    print("<th>{}</th>" .format(total_dict["nb_na"]), file=fid)
    print('<th>{}</th>' .format(total), file=fid)
    print("</tr>", file=fid)



class ReportDeliverable(object):
    """ReportDeliverable"""

    def __init__(self, url, ipqc, deliverable, filter_status=[]):
        self.url = url
        self.ipqc = ipqc
        self.deliverable = deliverable

        # https://hsdes.intel.com/resource/1409433556
        #IPQC report for power - remove unneeded count from final
        self._filter_status = filter_status
        self._filter_unneeded = False
        if status_data[_UNNEEDED]['option'] in self._filter_status:
            self._filter_unneeded = True

        self.date = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        if not dir_accessible(os.path.join(self.ipqc.ip.workdir, self.deliverable), os.F_OK):
            os.makedirs((os.path.join(self.ipqc.ip.workdir, self.deliverable)))
        self.filename = os.path.join(self.ipqc.ip.workdir, self.deliverable, 'ipqc.html')
        self.waivers = 'waivers'

    def generate(self):
        """generate"""
        fid = open(self.filename, 'w')

        ##########################################################################
        # IPQC Results - Deliverable Section
        ##########################################################################
        # header section
        self.header(fid)
        # executive summary for deliverable section
        nb_columns = self.executive_summary_deliverable(fid)
        # top deliverable table
        self.top_deliverable_table(fid)
        # hierarchical deliverable table
        if self.ipqc.top_hierarchy != []:
            self.hierarchical_deliverable_table(fid, nb_columns)

        ##########################################################################
        # Legend
        ##########################################################################
        legend(fid)
        print('<br>', file=fid)

        print("</div>", file=fid)
        print("</div>", file=fid)
        print("</body>", file=fid)
        print("</html>", file=fid)

        fid.close()


    def header(self, fid):
        """header"""
        print("<!DOCTYPE html>", file=fid)
        print("<html>", file=fid)
        print("<head>", file=fid)
        print("<title>IPQC Dashboard - {} {}</title>" .format(self.ipqc.ip.name, \
                self.deliverable), file=fid)
        print("</head>", file=fid)
        print("<body>", file=fid)
        print("<div>", file=fid)

        print('<header style="background-color: #DFE2DB"> \
                <p style="text-align:right; font-family: arial, helvetica, sans-serif;"> \
                    <span style="float: left"><a style=\"color: blue;\" href={}>HOME</a></span> \
                    <span style="float: right">Intel - PSG</span> \
                </p> \
                <br> \
                <h2 style="text-align:center;font-family: arial, helvetica, sans-serif;">Report \
                for deliverable {}</h2> \
                <p style="text-align:center; color: #0000CC; font-size:11px;">Date of execution \
                {} by {}</p> \
                <br> \
                </header>' .format(self.url, self.deliverable, self.date, os.environ["USER"]), \
                file=fid)

        print('<div style="width: 100%; display:table; border-left: 1px solid #ccc; border-bottom:\
                1px solid #ccc; border-right: 1px solid #ccc; margin-left: 0%">', file=fid)


    def executive_summary_deliverable(self, fid):
        """Executive summary for deliverable"""
        (nb_passed, nb_failed, nb_fatal, nb_warning, nb_unneeded, nb_na) = (0, 0, 0, 0, 0, 0)
        nb_columns = len([nb_passed, nb_failed, nb_fatal, nb_warning, nb_unneeded, nb_na]) - \
                len(self._filter_status)
        bom = ''

        for cell in self.ipqc.ip.topcells:
            for deliverable in cell.deliverables:
                if deliverable.name == self.deliverable:
                    if deliverable.bom != '':
                        bom = '{}@{}' .format(deliverable.name, deliverable.bom)
                    else:
                        bom = deliverable.name
                    nb_passed = nb_passed + deliverable.nb_pass
                    nb_failed = nb_failed + deliverable.nb_fail
                    nb_fatal = nb_fatal + deliverable.nb_fatal
                    nb_warning = nb_warning + deliverable.nb_warning
                    nb_unneeded = nb_unneeded + deliverable.nb_unneeded
                    nb_na = nb_na + deliverable.nb_na

        total = nb_passed + nb_failed + nb_fatal + nb_warning + nb_unneeded + nb_na


        ##########################################################################
        # Deliverable Results - Deliverable Summary Section
        ##########################################################################
        print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 5%; \
                background-color: #B4D8E7">Executive summary for deliverable {}</h2> \
                <table width="90%" style="padding-left:10%; text-align:left; font-family: arial, \
                helvetica, sans-serif;"> \
                    <tr><td style=\"width: 30%; font-weight: bold;\">Project:</td><td>{}</td></tr> \
                    <tr><td style=\"width: 30%; font-weight: bold;\">IP:</td><td>{} ({} type)</td>\
                    </tr> \
                    <tr><td style=\"font-weight: bold;\">Deliverable name:</td><td>{}</td></tr> \
                    <tr><td style=\"font-weight: bold;\">Milestone:</td><td>{}</td></tr> \
                    <tr><td style=\"font-weight: bold;\">Number of tests:</td><td>{} ({} passed /\
                    {} waived / {} failed / {} fatal / {} unneeded / {} NA)</td></tr> \
                </table>' .format(self.deliverable, self.ipqc.ip.workspace.project, \
                self.ipqc.ip.name, self.ipqc.ip.iptype, bom, self.ipqc.ip.milestone, total, \
                nb_passed, nb_warning, nb_failed, nb_fatal, nb_unneeded, nb_na), file=fid)

        print("<br>", file=fid)

        return nb_columns


    def top_deliverable_table(self, fid):
        """top_deliverable_table"""
        ##########################################################################
        # Deliverable Results - Deliverable Report
        ##########################################################################
        print("<h2 style=\"font-family: arial, helvetica, sans-serif; padding-left: 5%; \
                background-color: #B4D8E7\">Report summary deliverable {}</h2>" \
                .format(self.deliverable), file=fid)
        print("<br>", file=fid)
        print("<table bgcolor={} align=\"center\" border=\"1\" style=\"width:90%; margin-left:5%; \
                border: 1px solid; border-color:black; border-collapse: collapse;\">" \
                .format(status_data[_NA]['color']), file=fid)
        print('<tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black; \
                border-collapse: collapse; background-color: #1874CD; font-weight: bold; \
                font-family: arial, helvetica, sans-serif;">', file=fid)
        print('<th border="1" style="width=5%; color: #FFFFFF; border: 1px solid; \
                border-color:black; border-collapse: collapse; background-color: #1874CD;">\
                Topcells</th>', file=fid)
        print('<th border="1" style="width=10% color: #FFFFFF; border: 1px solid; \
                border-color:black; border-collapse: collapse; background-color: #1874CD;">\
                Check Name</th>', file=fid)
        print('<th border="1" style="width=10% color: #FFFFFF; border: 1px solid; \
                border-color:black; border-collapse: collapse; background-color: #1874CD;">\
                Waivers</th>', file=fid)
        print('<th border="1" style="width=10% color: #FFFFFF; border: 1px solid; \
                border-color:black; border-collapse: collapse; background-color: #1874CD;">\
                Check Status</th>', file=fid)
        print('<th border="1" style="width=10% color: #FFFFFF; border: 1px solid; \
                border-color:black; border-collapse: collapse; background-color: #1874CD;">\
                Errors Waived</th>', file=fid)
        print('<th border="1" style="width=10% color: #FFFFFF; border: 1px solid; \
                border-color:black; border-collapse: collapse; background-color: #1874CD;">\
                Remaining Errors</th>', file=fid)
        print('<th border="1" style="width=10% color: #FFFFFF; border: 1px solid; \
                border-color:black; border-collapse: collapse; background-color: #1874CD;">\
                LOG</th>', file=fid)
        print('<th border="1" style="width=10% color: #FFFFFF; border: 1px solid; \
                border-color:black; border-collapse: collapse; background-color: #1874CD;">\
                Run Date</th>', file=fid)
        print('</tr>', file=fid)

        set_check_report_by_deliverable(self.ipqc, self.waivers, self.deliverable, fid, self.date)

        print("</table>", file=fid)
        print("<br>", file=fid)


    def hierarchical_deliverable_table(self, fid, nb_columns):
        """hierarchical_deliverable_table"""
        ##########################################################################
        # Deliverable Results - Hierarchy IP Report
        ##########################################################################
        deliverable_ip_level = self.ipqc.ip.get_deliverable_ipqc(self.deliverable)
        set_deliverable_score(self.ipqc, deliverable_ip_level)

        print("<h2 style=\"font-family: arial, helvetica, sans-serif; padding-left: 5%; \
                background-color: #B4D8E7\">Report summary of {} hierarchy</h2>\n<br>" \
                .format(self.ipqc.ip.name), file=fid)

        ### Array of IPs
        print('<table bgcolor={} align="center" border="1" style="width:90%; margin-left:5%; \
                border: 1px solid; border-color:black; border-collapse: collapse;">\n \
                <tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black; \
                border-collapse: collapse; background-color: #1874CD; font-weight: bold; \
                font-family: arial, helvetica, sans-serif;">\n \
                <th border="1" rowspan=2 width="10%" style="border: 1px solid; \
                border-color:black; border-collapse: collapse;">IP(s)</th>\n \
                <th border="1" rowspan=2 width="20%" style="border: 1px solid; \
                border-color:black; border-collapse: collapse;">Version</th>\n \
                <th border="1" rowspan=2 width="17%" style="border: 1px solid; \
                border-color:black; border-collapse: collapse;">Owner</th>\n \
                <th border="1" colspan={} width="36%" style="border: 1px solid; \
                border-color:black; border-collapse: collapse;">Test Result</th>' \
                .format(status_data[_NA]['color'], nb_columns), file=fid)

        print('<th border="1" rowspan=2 width="6%" style="border: 1px solid; \
                border-color:black; border-collapse: collapse;">Total Test</th>\n \
                </tr>\n \
                <tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black; \
                border-collapse: collapse; background-color: #1874CD; font-weight: bold; \
                font-family: arial, helvetica, sans-serif;">\n \
                <th border="1" width="6%" style="border: 1px solid; border-color:black; \
                border-collapse: collapse;">Pass</th>\n \
                <th border="1" width="6%" style="border: 1px solid; border-color:black; \
                border-collapse: collapse;">Waived</th>\n \
                <th border="1" width="6%" style="border: 1px solid; border-color:black; \
                border-collapse: collapse;">Fail</th>\n \
                <th border="1" width="6%" style="border: 1px solid; border-color:black; \
                border-collapse: collapse;">Fatal</th>', file=fid)

        if not self._filter_unneeded:
            print('<th border="1" width="6%" style="border: 1px solid; border-color:black; \
                    border-collapse: collapse;">Unneeded</th>', file=fid)

        print('<th border="1" width="6%" style="border: 1px solid; border-color:black; \
                border-collapse: collapse;">NA</th>\n \
                </tr>', file=fid)

        (total_nb_passed, total_nb_warning, total_nb_failed, total_nb_fatal, total_nb_unneeded, \
                total_nb_na) = (0, 0, 0, 0, 0, 0)

        for i in sorted(self.ipqc.ip.flat_hierarchy):

            if i == self.ipqc.ip.name:
                continue

            sub_ipqc = self.ipqc.get_ipqc(i)

            if sub_ipqc is None:
                continue

            if sub_ipqc.ip.err != '':
                print('<tr style="text-align:center; font-family: arial, helvetica, \
                        sans-serif;">\n \
                    <td style="background-color: #E0E0E0;">{}</td>\n \
                    <td style="background-color: #E0E0E0;">{}</td>\n \
                    <td colspan={} style="background-color: {};">{}</td>\n \
                    </tr>' \
                    .format(sub_ipqc.ip.name, sub_ipqc.ip.bom, nb_columns,\
                    status_data[_FATAL_SYSTEM]['color'], sub_ipqc.ip.err), file=fid)
                continue

            deliverable_ip_level = sub_ipqc.ip.get_deliverable_ipqc(self.deliverable)

            if deliverable_ip_level is None:
                continue

            deliverable_score = {"nb_pass": 0, "nb_warning": 0, "nb_fail": 0, "nb_fatal": 0, \
                    "nb_unneeded": 0, "nb_na": 0}

            if (deliverable_ip_level.report != None) or (sub_ipqc.ip.cache is True):
                (deliverable_score["nb_pass"], \
                        deliverable_score["nb_warning"], \
                        deliverable_score["nb_fail"], \
                        deliverable_score["nb_fatal"], \
                        deliverable_score["nb_unneeded"], \
                        deliverable_score["nb_na"] \
                ) = \
                (deliverable_ip_level.nb_pass, \
                        deliverable_ip_level.nb_warning, \
                        deliverable_ip_level.nb_fail, \
                        deliverable_ip_level.nb_fatal, \
                        deliverable_ip_level.nb_unneeded, \
                        deliverable_ip_level.nb_na \
                )
            else:
                (deliverable_score["nb_pass"], \
                        deliverable_score["nb_warning"], \
                        deliverable_score["nb_fail"], \
                        deliverable_score["nb_fatal"], \
                        deliverable_score["nb_unneeded"], \
                        deliverable_score["nb_na"] \
                ) = set_deliverable_score(sub_ipqc, deliverable_ip_level)

            total_nb_passed = total_nb_passed + deliverable_score["nb_pass"]
            total_nb_warning = total_nb_warning + deliverable_score["nb_warning"]
            total_nb_failed = total_nb_failed + deliverable_score["nb_fail"]
            total_nb_fatal = total_nb_fatal + deliverable_score["nb_fatal"]
            total_nb_unneeded = total_nb_unneeded + deliverable_score["nb_unneeded"]
            total_nb_na = total_nb_na + deliverable_score["nb_na"]

            print("<tr style=\"text-align:center; font-family: arial, helvetica, \
                    sans-serif;\">\n \
                <td style=\"background-color: #E0E0E0;\">%s</td>" % (sub_ipqc.ip.name), \
                    file=fid)
            print_bom(fid, deliverable_ip_level)
            print_owner(fid, deliverable_ip_level)

            if deliverable_ip_level.status == _NA_MILESTONE:
                nb_column = 7 - len(self._filter_status)
                print_na_milestone_status(fid, nb_column)
                continue

            print_pass_status(fid, deliverable_ip_level, deliverable_score["nb_pass"])
            print_warning_status(fid, deliverable_ip_level, deliverable_score["nb_warning"])
            print_fail_status(fid, deliverable_ip_level, deliverable_score["nb_fail"])
            print_fatal_status(fid, deliverable_ip_level, deliverable_score["nb_fatal"])
            print_unneeded_status(fid, deliverable_ip_level, deliverable_score["nb_unneeded"], \
                    self._filter_unneeded)
            print_na_status(fid, deliverable_score["nb_na"])
            print_deliverable_score(fid, deliverable_score)


        # total of passed, waived, failed, fatal, unneeded, na for top IP
        total = {"nb_pass": total_nb_passed, "nb_warning": total_nb_warning, \
                "nb_fail": total_nb_failed, "nb_fatal": total_nb_fatal, \
                "nb_unneeded": total_nb_unneeded, "nb_na": total_nb_na}
        print_hierarchy_score(fid, total, self._filter_unneeded)

        print("</table>\n \
            <br>\n<br>", file=fid)

        return
