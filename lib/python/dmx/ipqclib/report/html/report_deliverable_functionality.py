#!/usr/bin/env python
""" report_deliverable_functionality.py """
from __future__ import print_function
import os
import datetime
from dmx.ipqclib.log import uiDebug
from dmx.ipqclib.utils import dir_accessible
from dmx.ipqclib.settings import _PASSED, _FAILED, _FATAL, _NA, _WARNING, _UNNEEDED, \
    _FATAL_SYSTEM, status_data
from dmx.ipqclib.report.html.legend import legend
from dmx.ipqclib.report.html.report_deliverable import ReportDeliverable


class ReportDeliverableFunctionality(object):
    """class ReportDeliverableFunctionality"""
    def __init__(self, url, ipqc, deliverable, deliverable_list, filter_status=[]):
        self.url = url
        self.ipqc = ipqc
        self.deliverable = deliverable
        self.deliverable_list = deliverable_list
        self.date = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        if not dir_accessible(os.path.join(self.ipqc.ip.workdir, self.deliverable), os.F_OK):
            os.makedirs((os.path.join(self.ipqc.ip.workdir, self.deliverable)))
        self.filename = os.path.join(self.ipqc.ip.workdir, 'ipqc_'+deliverable+'.html')
        self.waivers = 'waivers'
        self._filter_status = filter_status

        # https://hsdes.intel.com/resource/1409433556
        #IPQC report for power - remove unneeded count from final
        self._filter_unneeded = False
        if status_data[_UNNEEDED]['option'] in filter_status:
            self._filter_unneeded = True

    def generate(self):
        """ generate() """
        fid = open(self.filename, 'w')

        ##########################################################################
        # IPQC Results - Cell Check Section
        ##########################################################################
        print("<!DOCTYPE html>", file=fid)
        print("<html>", file=fid)
        print("<head>", file=fid)
        print("<title>IPQC Dashboard - {} {}</title>" .format(self.ipqc.ip.name, self.deliverable),\
                file=fid)
        print("</head>", file=fid)
        print("<body>", file=fid)
        print("<div>", file=fid)

        print('<header style="background-color: #DFE2DB"> \
                <p style="text-align:right; font-family: arial, helvetica, sans-serif;"> \
                    <span style="float: right">Intel - PSG</span> \
                </p> \
                <br> \
                <h2 style="text-align:center;font-family: arial, helvetica, sans-serif;">Report \
                for deliverable {}</h2> \
                <p style="text-align:center; color: #0000CC; font-size:11px;">Date of execution {} \
                by {}</p> \
                <br> \
                </header>' .format(self.deliverable, self.date, os.environ["USER"]), file=fid)

        print('<div style="width: 100%; display:table; border-left: 1px solid #ccc; border-bottom: \
                1px solid #ccc; border-right: 1px solid #ccc; margin-left: 0%">', file=fid)

        nb_passed = 0
        nb_failed = 0
        nb_fatal = 0
        nb_warning = 0
        nb_unneeded = 0
        nb_na = 0

        if self.deliverable in self.deliverable_list.keys():
            nb_passed = self.deliverable_list[self.deliverable]['nb_passed']
            nb_failed = self.deliverable_list[self.deliverable]['nb_failed']
            nb_fatal = self.deliverable_list[self.deliverable]['nb_fatal']
            nb_warning = self.deliverable_list[self.deliverable]['nb_warning']
            nb_unneeded = self.deliverable_list[self.deliverable]['nb_unneeded']
            nb_na = self.deliverable_list[self.deliverable]['nb_na']

        total = nb_passed + nb_failed + nb_fatal + nb_warning + nb_unneeded + nb_na


        ##########################################################################
        # Deliverable Results - Deliverable Summary Section
        ##########################################################################
        print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 5%; \
                background-color: #B4D8E7">Executive summary for deliverable {}</h2> \
                <table width="90%" style="padding-left:10%; text-align:left; font-family: arial, \
                helvetica, sans-serif;"> \
                    <tr><td style=\"font-weight: bold;\">Deliverable name:</td><td>{}</td></tr> \
                    <tr><td style=\"font-weight: bold;\">Milestone:</td><td>{}</td></tr> \
                    <tr><td style=\"font-weight: bold;\">Number of tests:</td><td>{} ({} passed / \
                    {} waived / {} failed / {} fatal / {} unneeded / {} NA)</td></tr> \
                </table>' .format(self.deliverable, self.deliverable, self.ipqc.ip.milestone, \
                total, nb_passed, nb_warning, nb_failed, nb_fatal, nb_unneeded, nb_na), file=fid)

        print("<br>", file=fid)


        ##########################################################################
        # Deliverable Results - Hierarchy IP Report
        ##########################################################################
        (total_nb_passed, total_nb_warning, total_nb_failed, total_nb_fatal, total_nb_unneeded,\
                total_nb_na) = (0, 0, 0, 0, 0, 0)
        nb_columns = len([total_nb_passed, total_nb_warning, total_nb_failed, total_nb_fatal,\
                total_nb_unneeded, total_nb_na]) - len(self._filter_status)
        print("<h2 style=\"font-family: arial, helvetica, sans-serif; padding-left: 5%;\
                background-color: #B4D8E7\">Report summary of {} hierarchy</h2>"\
                .format(self.ipqc.ip.name), file=fid)
        print("<br>", file=fid)
        print("<table bgcolor={} align=\"center\" border=\"1\" style=\"width:90%; margin-left:5%;\
                border: 1px solid; border-color:black; border-collapse: collapse;\">"\
                .format(status_data[_NA]['color']), file=fid)

        ### Array of IPs
        print('<table border="1" width="90%" style="margin-left:5%; border: 1px solid;\
                border-color:black; border-collapse: collapse;">', file=fid)
        print('<tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black;\
                border-collapse: collapse; background-color: #1874CD; font-weight: bold; \
                font-family: arial, helvetica, sans-serif;">', file=fid)
        print('<th border="1" rowspan=2 width="10%" style="border: 1px solid; border-color:black;\
                border-collapse: collapse;">IP(s)</th>', file=fid)
        print('<th border="1" rowspan=2 width="20%" style="border: 1px solid; border-color:black;\
                border-collapse: collapse;">Version</th>', file=fid)
        print('<th border="1" rowspan=2 width="17%" style="border: 1px solid; border-color:black;\
                border-collapse: collapse;">Owner</th>', file=fid)
        print('<th border="1" colspan={} width="36%" style="border: 1px solid; border-color:black;\
                border-collapse: collapse;">Test Result</th>' .format(nb_columns), file=fid)
        print('<th border="1" rowspan=2 width="6%" style="border: 1px solid; border-color:black; \
                border-collapse: collapse;">Total Test</th>', file=fid)
        print("</tr>", file=fid)
        print('<tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black; \
                border-collapse: collapse; background-color: #1874CD; font-weight: bold; \
                font-family: arial, helvetica, sans-serif;">', file=fid)
        print('<th border="1" width="6%" style="border: 1px solid; border-color:black; \
                border-collapse: collapse;">Pass</th>', file=fid)
        print('<th border="1" width="6%" style="border: 1px solid; border-color:black; \
                border-collapse: collapse;">Waived</th>', file=fid)
        print('<th border="1" width="6%" style="border: 1px solid; border-color:black; \
                border-collapse: collapse;">Fail</th>', file=fid)
        print('<th border="1" width="6%" style="border: 1px solid; border-color:black; \
                border-collapse: collapse;">Fatal</th>', file=fid)

        if not self._filter_unneeded:
            print('<th border="1" width="6%" style="border: 1px solid; border-color:black; \
                    border-collapse: collapse;">Unneeded</th>', file=fid)

        print('<th border="1" width="6%" style="border: 1px solid; border-color:black; \
                border-collapse: collapse;">NA</th>', file=fid)
        print("</tr>", file=fid)

        for i in sorted(self.ipqc.ip.boms.keys()):
            if i != self.ipqc.ip.name:
                sub_ipqc = self.ipqc.get_ipqc(i)
            else:
                sub_ipqc = self.ipqc

            if sub_ipqc == None:
                continue

            if sub_ipqc.ip.err != '':
                print("<tr style=\"text-align:center; font-family: arial, helvetica, \
                        sans-serif;\">", file=fid)
                print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (sub_ipqc.ip.name), \
                        file=fid)
                print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (sub_ipqc.ip.bom), \
                        file=fid)
                print("<td colspan=6 style=\"background-color: {};\">{}</td>" \
                        .format(status_data[_FATAL_SYSTEM]['color'], sub_ipqc.ip.err), file=fid)
                print("</tr>", file=fid)
                continue

            d = sub_ipqc.ip.get_deliverable_ipqc(self.deliverable)

            if d is None:
                continue


            if (d.report != None) or (sub_ipqc.ip.cache is True):
                (nb_pass, nb_warning, nb_fail, nb_fatal, nb_unneeded, nb_na) = (d.nb_pass, \
                        d.nb_warning, d.nb_fail, d.nb_fatal, d.nb_unneeded, d.nb_na)
            else:
                (nb_pass, nb_warning, nb_fail, nb_fatal, nb_unneeded, nb_na) = (0, 0, 0, 0, 0, 0)

                for cell in sub_ipqc.ip.topcells:

                    for deliverable in cell.deliverables:

                        if deliverable.name == d.name:
                            (tmp_nb_pass, tmp_nb_fail, tmp_nb_fatal, tmp_nb_warning, \
                                    tmp_nb_unneeded, tmp_nb_na) = deliverable.get_check_info()
                            nb_pass = tmp_nb_pass + nb_pass
                            nb_warning = tmp_nb_warning + nb_warning
                            nb_fail = tmp_nb_fail + nb_fail
                            nb_fatal = tmp_nb_fatal + nb_fatal
                            nb_unneeded = tmp_nb_unneeded + nb_unneeded
                            nb_na = tmp_nb_na + nb_na

                url_path = sub_ipqc.ip.workdir
                deliverable_report = ReportDeliverable(os.path.join(url_path, 'ipqc.html'), \
                        sub_ipqc, d.name)
                deliverable_report.generate()
                d.report = deliverable_report.filename
                d.nb_pass = nb_pass
                d.nb_warning = nb_warning
                d.nb_fail = nb_fail
                d.nb_fatal = nb_fatal
                d.nb_unneeded = nb_unneeded
                d.nb_na = nb_na

            total_nb_passed = total_nb_passed + nb_pass
            total_nb_warning = total_nb_warning + nb_warning
            total_nb_failed = total_nb_failed + nb_fail
            total_nb_fatal = total_nb_fatal + nb_fatal
            total_nb_unneeded = total_nb_unneeded + nb_unneeded
            total_nb_na = total_nb_na + nb_na

            print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", \
                    file=fid)
            print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (sub_ipqc.ip.name), file=fid)
            if d.bom != '':
                print("<td style=\"background-color: #E0E0E0;\">%s@%s</td>" % (d.name, d.bom), \
                        file=fid)
            else:
                print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (_NA), file=fid)

            if d.owner != '':
                print("<td style=\"background-color: #E0E0E0;\">\
                        <a href=\"mailto:{}@intel.com?subject=ipqc dashboard\">{}@intel.com</td>" \
                        .format(d.owner, d.owner), file=fid)
            else:
                print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (_NA), file=fid)

            if nb_pass == 0:
                print("<td>{}</td>"  .format(nb_pass), file=fid)
            else:
                print("<td style=\"background-color: {};\"><a href={}>{}</td>"  \
                        .format(status_data[_PASSED]['color'], d.report, nb_pass), file=fid)

            if nb_warning == 0:
                print("<td>{}</td>"  .format(nb_warning), file=fid)
            else:
                print("<td style=\"background-color: {};\"><a href={}>{}</td>"  \
                        .format(status_data[_WARNING]['color'], d.report, nb_warning), file=fid)

            if nb_fail == 0:
                print("<td>{}</td>"  .format(nb_fail), file=fid)
            else:
                print("<td style=\"background-color: {};\"><a href={}>{}</td>"  \
                        .format(status_data[_FAILED]['color'], d.report, nb_fail), file=fid)

            if nb_fatal == 0:
                print("<td>{}</td>"  .format(nb_fatal), file=fid)
            elif d.bom == '':
                print("<td style=\"color: #FFFFFF; background-color: {};\">{}</td>"  \
                        .format(status_data[_FATAL]['color'], nb_fatal), file=fid)
            else:
                print("<td style=\"color: #FFFFFF; background-color: {};\"><a href={} \
                        style=\"color: #FFFFFF;\">{}</td>"  .format(status_data[_FATAL]['color'], \
                        d.report, nb_fatal), file=fid)

            if not self._filter_unneeded:
                if nb_unneeded == 0:
                    print("<td>{}</td>"  .format(nb_unneeded), file=fid)
                elif d.bom == '':
                    print("<td td style=\"background-color: {};\">{}</td>"  \
                            .format(status_data[_UNNEEDED]['color'], nb_unneeded), file=fid)
                else:
                    print("<td td style=\"background-color: {};\"><a href={}>{}</td>"  \
                            .format(status_data[_UNNEEDED]['color'], d.report, nb_unneeded), \
                            file=fid)

            if nb_na == 0:
                print("<td>{}</td>"  .format(nb_na), file=fid)
            else:
                print("<td style=\"background-color: {};\">{}</td>"  \
                        .format(status_data[_NA]['color'], nb_na), file=fid)

            total = nb_pass + nb_warning + nb_fail + nb_fatal + nb_na

            if not self._filter_unneeded:
                total = total + nb_unneeded

            print("<td>{}</td>"  .format(total), file=fid)
            print("</tr>", file=fid)

        # total of passed, waived, failed, fatal, unneeded, na for top IP
        print("<tr style=\"background-color: #AAD4FF; font-weight: bold; font-family: arial, \
                helvetica, sans-serif;\">", file=fid)
        print('<th>Total</th>', file=fid)
        print('<th></th>', file=fid)
        print('<th></th>', file=fid)
        print("<th>{}</th>" .format(total_nb_passed), file=fid)
        print("<th>{}</th>" .format(total_nb_warning), file=fid)
        print("<th>{}</th>" .format(total_nb_failed), file=fid)
        print("<th>{}</th>" .format(total_nb_fatal), file=fid)

        if not self._filter_unneeded:
            print("<th>{}</th>" .format(total_nb_unneeded), file=fid)
        print("<th>{}</th>" .format(total_nb_na), file=fid)
        print('<th>{}</th>' .format(total_nb_passed + total_nb_warning + total_nb_failed + \
                total_nb_fatal + total_nb_unneeded + total_nb_na), file=fid)
        print("</tr>", file=fid)

        print("</table>", file=fid)
        print("<br>", file=fid)
        print("<br>", file=fid)

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
