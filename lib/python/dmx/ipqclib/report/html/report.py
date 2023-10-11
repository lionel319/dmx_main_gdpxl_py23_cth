from __future__ import print_function
import os
import sys
import datetime
import platform
import re
from dmx.ipqclib.utils import get_tools, file_accessible, run, run_command
from operator import attrgetter
from dmx.ipqclib.settings import _PASSED, _FAILED, _FATAL, _NA, _NA_ERROR, _WARNING, _CHECKER_SKIPPED, _CHECKER_WAIVED, _ALL_WAIVED, _UNNEEDED, _NA_MILESTONE, _NOT_POR, status_data
from dmx.ipqclib.log import uiInfo, uiDebug
from dmx.ipqclib.report.html.legend import legend
from dmx.ipqclib.report.html.utils import set_checker_fatal_status, set_checker_failed_warning_status, set_checker_passed_status, set_checker_na_status, set_checker_failed_skip_status
from dmx.ipqclib.report.html.log import set_log


class ReportCell():

    def __init__(self, url, ip, cell, deliverable=None):
        self.url = url
        self.ip = ip
        self.cell = cell
        self.deliverable = deliverable
        self.date = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        self.filename = os.path.join(self.cell.workdir, 'ipqc_'+cell.name+'.html')
        self.waivers = 'waivers'

    def generate(self):

        f = open(self.filename,'w')

        ##########################################################################
        # IPQC Results - Cell Check Section
        ##########################################################################
        print("<!DOCTYPE html>", file=f)
        print("<html>", file=f)
        print("<head>", file=f)
        print("<title>IPQC Dashboard - {} {}</title>" .format(self.ip.name, self.cell.name), file=f)
        print("</head>", file=f)
        print("<body>", file=f)
        print("<div>", file=f)

        print('<header style="background-color: #DFE2DB"> \
                <p style="text-align:right; font-family: arial, helvetica, sans-serif;"> \
                    <span style="float: left"><a style=\"color: blue;\" href={}>HOME</a></span> \
                    <span style="float: right">Intel - PSG</span> \
                </p> \
                <br> \
                <h2 style="text-align:center;font-family: arial, helvetica, sans-serif;">Report for cell {}</h2> \
                <p style="text-align:center; color: #0000CC; font-size:11px;">Date of execution {} by {}</p> \
                <br> \
                </header>' .format(self.url, self.cell.name, self.date, os.environ["USER"]), file=f)

        print('<div style="width: 100%; display:table; border-left: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc; margin-left: 0%">', file=f)
        ##########################################################################
        # Cell Results - Cell Summary Section
        ##########################################################################
        print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 5%; background-color: #B4D8E7">Executive summary for cell {}</h2> \
                <table width="90%" style="padding-left:10%; text-align:left; font-family: arial, helvetica, sans-serif;"> \
                    <tr><td style=\"width: 30%; font-weight: bold;\">Project:</td><td>{}</td></tr> \
                    <tr><td style=\"width: 30%; font-weight: bold;\">IP:</td><td>{}@{} ({} type)</td></tr> \
                    <tr><td style=\"font-weight: bold;\">Topcell name:</td><td>{}</td></tr> \
                    <tr><td style=\"font-weight: bold;\">Milestone:</td><td>{}</td></tr> \
                    <tr><td style=\"font-weight: bold;\">Number of deliverables:</td><td>{}</td></tr> \
                    <tr><td style=\"font-weight: bold;\">Number of tests:</td><td>{} ({} passed / {} waived / {} failed / {} fatal / {} unneeded / {} NA)</td></tr> \
                </table>' .format(self.cell.name, self.ip.workspace.project, self.ip.name, self.ip.bom, self.ip.iptype, self.cell.name, self.ip.milestone, len(self.cell.deliverables), (self.cell.nb_pass + self.cell.nb_warning + self.cell.nb_fail + self.cell.nb_fatal + self.cell.nb_unneeded + self.cell.nb_nc), self.cell.nb_pass, self.cell.nb_warning, self.cell.nb_fail, self.cell.nb_fatal, self.cell.nb_unneeded, self.cell.nb_nc), file=f)

        print("<br>", file=f)

        ##########################################################################
        # Cell Results - Cell Report
        ##########################################################################
        print("<h2 style=\"font-family: arial, helvetica, sans-serif; padding-left: 5%; background-color: #B4D8E7\">Report summary cell {}</h2>" .format(self.cell.name), file=f)
        print("<br>", file=f)
        print("<table bgcolor={} align=\"center\" border=\"1\" style=\"width:90%; margin-left:5%; border: 1px solid; border-color:black; border-collapse: collapse;\">" .format(status_data[_NA]['color']), file=f)
        print('<tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD; font-weight: bold; font-family: arial, helvetica, sans-serif;">', file=f)
        print('<th style="width=5%; color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD;">Deliverables</th>', file=f)
        print('<th style="width=10%; color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD;">Check Name</th>', file=f)
        print('<th style="width=10%; color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD;">Waivers</th>', file=f)
        print('<th style="width=10%; color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD;">Check Status</th>', file=f)
        print('<th style="width=10%; color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD;">Errors Waived</th>', file=f)
        print('<th style="width=10%; color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD;">Remaining Errors</th>', file=f)
        print('<th style="width=10%; color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD;">LOG</th>', file=f)
        print('<th style="width=10%; color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD;">Run Date</th>', file=f)
        print('</tr>', file=f)

        orig = os.getcwd()
        self.set_check_report_by_cell(self.cell, f)

        print("</table>", file=f)
        print("<br>", file=f)

        ##########################################################################
        # Legend
        ##########################################################################
        legend(f)
        print('<br>', file=f)

        print("</div>", file=f)
        print("</div>", file=f)
        print("</body>", file=f)
        print("</html>", file=f)

        f.close


    def set_check_report_by_cell(self, cell, f):

        for deliverable in sorted(cell.deliverables, key=attrgetter('name')):

            j = 0
            flag = []


            if (deliverable.status == _NA) or (deliverable.status == _NA_MILESTONE) or (deliverable.is_unneeded):
                if deliverable.nb_checkers != 0:
                    for checker in deliverable.checkers:
                        print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)
                        if j == 0:
                            print("<td rowspan={} style=\"background-color: {};\">{}</td>" .format(deliverable.nb_checkers, status_data[deliverable.status]['color'], deliverable.name.upper()), file=f)
                            j = j + 1

                        if checker.subflow:
                            print('<td style=\"background-color: #FFFFFF\">{} ({})</td>'  .format(checker.name, checker.subflow), file=f)
                        else:
                            print('<td style=\"background-color: #FFFFFF\">{}</td>'  .format(checker.name), file=f)

                        if checker.has_waivers():
                            print("<td><a href={} ; type=\"text/plain\">{}</td>" .format(checker.waivers_file, self.waivers), file=f)
                        else:
                            print("<td>{}</td>" .format(_NA), file=f)

                        d = self.ip.get_deliverable_ipqc(deliverable.name)

                        if (deliverable.status == _NA_MILESTONE):
                            print('<td colspan=5 style="background-color: {}">{}</td>' .format(status_data[deliverable.status]['color'], deliverable.status), file=f)
                        elif d.is_unneeded:
                            print('<td colspan=5 style="background-color: {}">{}</td>' .format(status_data[deliverable.status]['color'], _NOT_POR), file=f)
                        else:
                            print('<td style="background-color: {}">{}</td>' .format(status_data[deliverable.status]['color'], deliverable.status), file=f)
                            print("<td>{}</td>" .format(_NA), file=f)
                            print("<td>{}</td>" .format(_NA), file=f)
                            print("<td>{}</td>" .format(_NA), file=f)
                            print("<td>{}</td>" .format(_NA), file=f)

                        print("</tr>", file=f)
                else:
                    print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)
                    print('<td style="background-color: {}">{}</td>' .format(status_data[deliverable.status]['color'], deliverable.name.upper()), file=f)
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
                            print("<td rowspan={} style=\"background-color: {};\">{}</td>" .format(deliverable.nb_checkers, status_data[deliverable.status]['color'], deliverable.name.upper()), file=f)
                            j = j + 1

                        if checker.subflow:
                            print('<td style=\"background-color: #FFFFFF\">{} ({})</td>'  .format(checker.name, checker.subflow), file=f)
                        else:
                            print('<td style=\"background-color: #FFFFFF\">{}</td>'  .format(checker.name), file=f)

                        print("<td>{}</td>" .format(_NA), file=f)

                        print("<td style=\"background-color: {};\">{}</td>" .format(status_data[deliverable.status]['color'], _ALL_WAIVED), file=f)
                        print("<td>{}</td>" .format(_NA), file=f)
                        print("<td>{}</td>" .format(_NA), file=f)
                        print("<td>{}</td>" .format(_NA), file=f)
                        print("<td>{}</td>" .format(_NA), file=f)
                        print("</tr>", file=f)
                else:
                    print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)
                    print("<td style=\"background-color: {};\">{}</td>" .format(status_data[deliverable.status]['color'], deliverable.name.upper()), file=f)
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
                        print("</tr>", file=f)

                else:
                    print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)
                    print("<td style=\"color: #FFFFFF; background-color: {};\">{}</td>" .format(status_data[_FATAL]['color'], deliverable.name.upper()), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td>{}</td>" .format(_NA), file=f)
                    print("<td colspan=5 style=\"color: #FFFFFF; background-color: {};\">{}</td>" .format(status_data[_FATAL]['color'], deliverable.deliverable_existence['unwaived'][0].error), file=f)
                    print("</tr>", file=f)
                continue


            date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            for checker in sorted(deliverable.checkers, key=attrgetter('name')):
                logfile = set_log(self.ip, cell, deliverable, checker)
                print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)

                if j == 0:
                    if deliverable.status == _FATAL:
                        print("<td rowspan={} style=\"color: #FFFFFF; background-color: {}; border-top: white;\">{}</td>" .format(deliverable.nb_checkers, status_data[deliverable.status]['color'], deliverable.name.upper()), file=f)
                    else:
                        print("<td rowspan={} style=\"background-color: {};\">{}</td>" .format(deliverable.nb_checkers, status_data[deliverable.status]['color'], deliverable.name.upper()), file=f)

                    j = j + 1

                if checker.subflow:
                    print("<td style=\"background-color: #FFFFFF;\">{} ({})</td>"  .format(checker.name, checker.subflow), file=f)
                else:
                    print("<td style=\"background-color: #FFFFFF;\">{}</td>"  .format(checker.name), file=f)

                if checker.has_waivers():
                    print("<td><a href={} ; type=\"text/plain\">{}</td>" .format(checker.waivers_file, self.waivers), file=f)
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


                    ################
                    # UNNEEDED
                    ################
                    if checker.status == _UNNEEDED:
                        print("<td style=\"background-color: {};\">{}</td>"  .format(status_data[_UNNEEDED]['color'], _UNNEEDED), file=f)
                        print("<td>{}</td>" .format(_NA), file=f)
                        print("<td>{}</td>" .format(_NA), file=f)
                        print('<td>{}</td>' .format(_NA), file=f)
                        print('<td>{}</td>' .format(_NA), file=f)
                        continue


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
                    if (checker.status == _WARNING) or (checker.status == _FAILED):
                        set_checker_failed_warning_status(cell.name, checker, f, date, status_data, logfile)
                        continue

                    if (checker.status == _CHECKER_SKIPPED):
                        set_checker_failed_skip_status(cell.name, checker, f, date, status_data, logfile)
                        continue


#                    ################
#                    # CHECKER_WAIVED
#                    ################
#                    if checker.status == _CHECKER_WAIVED :
#                        print("<td style=\"background-color: {};\">{}</td>"  .format(status_data[checker.status]['color'], checker.status), file=f)
#                        print("<td>{}</td>" .format(_NA), file=f)
#                        print("<td>{}</td>" .format(_NA), file=f)
#                        print('<td>{}</td>' .format(_NA), file=f)
#                        print('<td style="font-size:12px; background-color: #FFFFFF;">{}</td>' .format(date), file=f)
#
#                        continue

                    ################
                    # UNNEEDED
                    ################
                    if checker.status == _UNNEEDED:
                        print("<td style=\"background-color: {};\">{}</td>"  .format(status_data[_UNNEEDED]['color'], _UNNEEDED), file=f)
                        print("<td>{}</td>" .format(_NA), file=f)
                        print("<td>{}</td>" .format(_NA), file=f)
                        print('<td>{}</td>' .format(_NA), file=f)
                        print('<td>{}</td>' .format(_NA), file=f)
                        continue


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

                    ################
                    # UNNEEDED
                    ################
                    if checker.status == _UNNEEDED:
                        print("<td style=\"background-color: {};\">{}</td>"  .format(status_data[_UNNEEDED]['color'], _UNNEEDED), file=f)
                        print("<td>{}</td>" .format(_NA), file=f)
                        print("<td>{}</td>" .format(_NA), file=f)
                        print('<td>{}</td>' .format(_NA), file=f)
                        print('<td>{}</td>' .format(_NA), file=f)
                        continue


            print("</tr>", file=f)

        return

