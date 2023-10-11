#!/usr/bin/env python
"""report_functionality"""
from __future__ import print_function
import os
import datetime
from operator import attrgetter
from dmx.ipqclib.utils import percentage
from dmx.ipqclib.settings import _PASSED, _FAILED, _FATAL, _NA, _WARNING, _UNNEEDED, status_data
from dmx.ipqclib.report.html.report import ReportCell

def print_cell_pass_status(fid, cell, report_html):
    """print_cell_pass_status"""
    if cell.nb_pass == 0:
        print("<td>{}</td>"  .format(cell.nb_pass), file=fid)
    else:
        print("<td style=\"background-color: {};\"><a href={}>{}</td>"  \
            .format(status_data[_PASSED]['color'], report_html, cell.nb_pass), file=fid)

def print_cell_warning_status(fid, cell, report_html):
    """print_cell_warning_status"""

    if cell.nb_warning == 0:
        print("<td>{}</td>"  .format(cell.nb_warning), file=fid)
    else:
        print("<td style=\"background-color: {};\"><a href={}>{}</td>"  \
            .format(status_data[_WARNING]['color'], report_html, cell.nb_warning), file=fid)

def print_cell_fail_status(fid, cell, report_html):
    """print_cell_fail_status"""
    if cell.nb_fail == 0:
        print("<td>{}</td>"  .format(cell.nb_fail), file=fid)
    else:
        print("<td style=\"background-color: {};\"><a href={}>{}</td>"  \
            .format(status_data[_FAILED]['color'], report_html, cell.nb_fail), file=fid)

def print_cell_fatal_status(fid, cell, report_html):
    """print_cell_fatal_status"""
    if cell.nb_fatal == 0:
        print("<td>{}</td>"  .format(cell.nb_fatal), file=fid)
    else:
        print("<td style=\"color: #FFFFFF; background-color: {};\"><a href={} \
            style=\"color: #FFFFFF;\">{}</td>"  .format(status_data[_FATAL]['color'], \
            report_html, cell.nb_fatal), file=fid)

def print_cell_unneeded_status(fid, cell, report_html, filter_unneeded):
    """print_cell_unneeded_status"""
    if not filter_unneeded:
        if cell.nb_unneeded == 0:
            print("<td>{}</td>"  .format(cell.nb_unneeded), file=fid)
        else:
            print("<td style=\"background-color: {};\"><a href={}>{}</td>"  \
                .format(status_data[_UNNEEDED]['color'], report_html, cell.nb_unneeded), file=fid)

def print_cell_na_status(fid, cell):
    """print_cell_na_status"""
    if cell.nb_nc == 0:
        print("<td>{}</td>"  .format(cell.nb_nc), file=fid)
    else:
        print("<td style=\"background-color: {};\">{}</td>"  .format(status_data[_NA]['color'], \
                cell.nb_nc), file=fid)

def print_total_score(fid, total, cell_score, filter_unneeded):
    """print_total_score"""

    print("<tr style=\"background-color: #AAD4FF;font-weight: bold; font-family: arial, \
            helvetica, sans-serif;\">", file=fid)
    print('<th>Total</th>', file=fid)
    print('<th></th>', file=fid)
    print("<th>{}</th>" .format(cell_score["nb_passed"]), file=fid)
    print("<th>{}</th>" .format(cell_score["nb_warning"]), file=fid)
    print("<th>{}</th>" .format(cell_score["nb_failed"]), file=fid)
    print("<th>{}</th>" .format(cell_score["nb_fatal"]), file=fid)
    if not filter_unneeded:
        print("<th>{}</th>" .format(cell_score["nb_unneeded"]), file=fid)
    print("<th>{}</th>" .format(cell_score["nb_na"]), file=fid)
    print('<th>{}</th>' .format(total), file=fid)
    print("</tr>", file=fid)

def print_total_percentage(fid, total, cell_score, filter_unneeded):
    """print_total_percentage"""

    print("<tr style=\"background-color: #AAD4FF;font-weight: bold; font-family: arial, \
            helvetica, sans-serif;\">", file=fid)
    print('<th>Total %</th>', file=fid)
    print('<th></th>', file=fid)
    print("<th>{}%</th>" .format(cell_score["nb_passed"] if cell_score["nb_passed"] == 0 else \
            percentage(cell_score["nb_passed"], total)), file=fid)
    print("<th>{}%</th>" .format(cell_score["nb_warning"] if cell_score["nb_warning"] == 0 \
            else percentage(cell_score["nb_warning"], total)), file=fid)
    print("<th>{}%</th>" .format(cell_score["nb_failed"] if cell_score["nb_failed"] == 0 else \
            percentage(cell_score["nb_failed"], total)), file=fid)
    print("<th>{}%</th>" .format(cell_score["nb_fatal"] if cell_score["nb_fatal"] == 0 else \
            percentage(cell_score["nb_fatal"], total)), file=fid)
    if not filter_unneeded:
        print("<th>{}%</th>" .format(cell_score["nb_unneeded"] if cell_score["nb_unneeded"] \
                == 0 else percentage(cell_score["nb_unneeded"], total)), file=fid)
    print("<th>{}%</th>" .format(cell_score["nb_na"] if cell_score["nb_na"] == 0 else \
            percentage(cell_score["nb_na"], total)), file=fid)
    print('<th>{}%</th>' .format(total if total == 0 else int(percentage(total, total))), file=fid)
    print("</tr>", file=fid)


class ReportFunctionality(object):
    """ReportFunctionality"""
    def __init__(self, url, ipobj, functionality, filter_status=[]):
        self.url = url
        self.ipobj = ipobj
        self.functionality = functionality
        self.date = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        self.filename = os.path.join(self.ipobj.workdir, 'ipqc_'+self.ipobj.name+'_'+\
                self.functionality+'.html')
        self.waivers = 'waivers'
        self._filter_status = filter_status

        # https://hsdes.intel.com/resource/1409433556
        #IPQC report for power - remove unneeded count from final
        self._filter_unneeded = False
        if status_data[_UNNEEDED]['option'] in filter_status:
            self._filter_unneeded = True


    def header(self, fid):
        """header"""
        print("<!DOCTYPE html>", file=fid)
        print("<html>", file=fid)
        print("<head>", file=fid)
        print("<title>IPQC Dashboard - {} {}</title>" .format(self.ipobj.name, \
                self.functionality), file=fid)
        print("</head>", file=fid)
        print("<body>", file=fid)
        print("<div>", file=fid)

        print('<header style="background-color: #DFE2DB"> \
                <p style="text-align:right; font-family: arial, helvetica, sans-serif;"> \
                    <span style="float: left"><a style=\"color: blue;\" href={}>HOME</a></span> \
                    <span style="float: right">Intel - PSG</span> \
                </p> \
                <br> \
                <h2 style="text-align:center;font-family: arial, helvetica, sans-serif;">Report for\
                IP {} ({})</h2> \
                <p style="text-align:center; color: #0000CC; font-size:11px;">Date of execution {} \
                by {}</p> \
                <br> \
                </header>' .format(self.url, self.ipobj.name, self.functionality, self.date, \
                os.environ["USER"]), file=fid)

        print('<div style="width: 100%; display:table; border-left: 1px solid #ccc; border-bottom: \
                1px solid #ccc; border-right: 1px solid #ccc; margin-left: 0%">', file=fid)


    def executive_summary_ip(self, fid):
        """executive_summary_ip"""

        (nb_passed, nb_failed, nb_fatal, nb_warning, nb_unneeded, nb_na) = (0, 0, 0, 0, 0, 0)
        nb_columns = len([nb_passed, nb_failed, nb_fatal, nb_warning, nb_unneeded, nb_na]) - \
                len(self._filter_status)
        bom = ''

        for cell in self.ipobj.topcells:

            if cell.functionality != self.functionality:
                continue

            for deliverable in cell.deliverables:
                nb_passed = nb_passed + deliverable.nb_pass
                nb_failed = nb_failed + deliverable.nb_fail
                nb_fatal = nb_fatal + deliverable.nb_fatal
                nb_warning = nb_warning + deliverable.nb_warning
                if not self._filter_unneeded:
                    nb_unneeded = nb_unneeded + deliverable.nb_unneeded
                nb_na = nb_na + deliverable.nb_na

        total = nb_passed + nb_failed + nb_fatal + nb_warning + nb_unneeded + nb_na

        print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 5%; \
                background-color: #B4D8E7">Executive summary for IP {} ({})</h2> \
                <table width="90%" style="padding-left:10%; text-align:left; font-family: arial, \
                helvetica, sans-serif;"> \
                    <tr><td style=\"width: 30%; font-weight: bold;\">Project:</td><td>{}</td></tr> \
                    <tr><td style=\"width: 30%; font-weight: bold;\">IP:</td><td>{} ({} type)</td>\
                    </tr> \
                    <tr><td style=\"font-weight: bold;\">Deliverable name:</td><td>{}</td></tr> \
                    <tr><td style=\"font-weight: bold;\">Milestone:</td><td>{}</td></tr> \
                    <tr><td style=\"font-weight: bold;\">Number of tests:</td><td>{} ({} passed / \
                    {} waived / {} failed / {} fatal / {} unneeded / {} NA)</td></tr> \
                </table>' .format(self.ipobj.name, self.functionality, \
                self.ipobj.workspace.project, self.ipobj.name, self.ipobj.iptype, bom, \
                self.ipobj.milestone, total, nb_passed, nb_warning, nb_failed, nb_fatal, \
                nb_unneeded, nb_na), file=fid)

        print("<br>", file=fid)

        return nb_columns


    def generate(self):
        """generate"""
        fid = open(self.filename, 'w')

        ##########################################################################
        # IPQC Results - Functionality
        ##########################################################################
        # header section
        self.header(fid)

        ##########################################################################
        # IP Functionality Results - IP Functionality Summary Section
        ##########################################################################
        nb_columns = self.executive_summary_ip(fid)

        ##########################################################################
        # Topcells Results - Topcell Report
        ##########################################################################
        print('<table border="1" width="89%" style="margin-left:10%; border: 1px solid; \
                border-color:black; border-collapse: collapse;"> \
                <tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black; \
                background-color: #1874CD; font-weight: bold; font-family: arial, helvetica, \
                sans-serif;"> \
                <th border="1" rowspan=2 width="10%" style=" border: 1px solid; \
                border-color:black; border-collapse: collapse;">IP(s)</th> \
                <th border="1" rowspan=2 width="27%" style=" border: 1px solid; \
                border-color:black; border-collapse: collapse;">Top Cell(s)</th> \
                <th border="1" colspan={} width="36%" style=" border: 1px solid; \
                border-color:black; border-collapse: collapse;">Test Result</th> \
                <th border="1" rowspan=2 width="16%" style=" border: 1px solid; \
                border-color:black; border-collapse: collapse;">Total Test</th> \
                </tr>' .format(nb_columns), file=fid)

        print('<tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black; \
                background-color: #1874CD; font-weight: bold; font-family: arial, helvetica, \
                sans-serif;"> \
                <th border="1" width="6%" style=" border: 1px solid; border-color:black; \
                border-collapse: collapse;">Pass</th> \
                <th border="1" width="6%" style=" border: 1px solid; border-color:black; \
                border-collapse: collapse;">Waived</th> \
                <th border="1" width="6%" style=" border: 1px solid; border-color:black; \
                border-collapse: collapse;">Fail</th> \
                <th border="1" width="6%" style=" border: 1px solid; border-color:black; \
                border-collapse: collapse;">Fatal</th>', file=fid)

        if not self._filter_unneeded:
            print('<th border="1" width="6%" style=" border: 1px solid; border-color:black; \
                    border-collapse: collapse;">Unneeded</th>', file=fid)
        print('<th border="1" width="6%" style=" border: 1px solid; border-color:black; \
                border-collapse: collapse;">NA</th> \
                </tr>', file=fid)

        cell_score = {"nb_passed": 0, "nb_warning": 0, "nb_failed" :0, "nb_fatal": 0, \
                "nb_unneeded" :0, "nb_na": 0}

        for cell in sorted(self.ipobj.topcells, key=attrgetter('name')):

            if cell.functionality != self.functionality:
                continue

            cell_score["nb_passed"] = cell_score["nb_passed"] + cell.nb_pass
            cell_score["nb_warning"] = cell_score["nb_warning"] + cell.nb_warning
            cell_score["nb_failed"] = cell_score["nb_failed"] + cell.nb_fail
            cell_score["nb_fatal"] = cell_score["nb_fatal"] + cell.nb_fatal
            if not self._filter_unneeded:
                cell_score["nb_unneeded"] = cell_score["nb_unneeded"] + cell.nb_unneeded
            cell_score["nb_na"] = cell_score["nb_na"] + cell.nb_nc
            total_cell = cell.nb_pass + cell.nb_warning + cell.nb_fail + cell.nb_fatal + cell.nb_nc
            if not self._filter_unneeded:
                total_cell = total_cell + cell.nb_unneeded

            cell_report = ReportCell(self.url, self.ipobj, cell)
            cell_report.generate()

            print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", \
                    file=fid)
            print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (self.ipobj.name), file=fid)
            print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (cell.name), file=fid)

            filename = 'ipqc_'+cell.name+'.html'
            report_html = os.path.join(self.ipobj.workdir, filename)

            print_cell_pass_status(fid, cell, report_html)
            print_cell_warning_status(fid, cell, report_html)
            print_cell_fail_status(fid, cell, report_html)
            print_cell_fatal_status(fid, cell, report_html)
            print_cell_unneeded_status(fid, cell, report_html, self._filter_unneeded)
            print_cell_na_status(fid, cell)

            print("<td>{}</td>"  .format(total_cell), file=fid)

            print("</tr>", file=fid)


        total = cell_score["nb_passed"] + cell_score["nb_warning"] + cell_score["nb_failed"] + \
            cell_score["nb_fatal"] + cell_score["nb_na"]

        if not self._filter_unneeded:
            total = total + cell_score["nb_unneeded"]

        # total of passed, waived, failed, fatal, unneeded, na for topcells
        print_total_score(fid, total, cell_score, self._filter_unneeded)

        # percentage of passed, waived, failed, fatal, unneeded, na for topcells
        print_total_percentage(fid, total, cell_score, self._filter_unneeded)

        print("</table>", file=fid)

        print("<br>", file=fid)
        print("<br>", file=fid)


        fid.close()
