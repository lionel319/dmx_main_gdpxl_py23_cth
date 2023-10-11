from __future__ import print_function
import os
import sys
import re
import datetime
from operator import attrgetter
from dmx.python_common.uiConfigParser import ConfigObj
from dmx.ipqclib.utils import dir_accessible, run_command, get_catalog_paths, percentage
from dmx.ipqclib.settings import _PASSED, _FAILED, _FATAL, _FATAL_SYSTEM, _NA, _WARNING, _UNNEEDED, status_data, _DB_DEVICE, _VIEW, _FUNCTIONALITY, _SIMPLE
from dmx.ipqclib.report.html.report import ReportCell
from dmx.ipqclib.report.html.legend import legend
from dmx.ipqclib.report.html.template_view import set_report_template_view
from dmx.ipqclib.report.html.template_functionality import set_report_template_functionality, get_deliverable_score
from dmx.ipqclib.report.html.template_simple import set_report_template_simple


######################################################################
# HTML for IP are supposed to be on the server so existing in NFS path
######################################################################
class ReportHTML():

    def __init__(self, ip_name, ipqc=None, msg=None, report_template=_VIEW, filter_status=[]):

        self.base =  os.path.basename(sys.argv[0])
        self.cmd = os.path.splitext(self.base)[0]
        self._ip_name = ip_name
        self._ipqc = ipqc
        self._msg = msg
        self._report_template = report_template

        # https://hsdes.intel.com/resource/1409433556
        #IPQC report for power - remove unneeded count from final
        self._filter_status = filter_status
        self._filter_unneeded =  False

        if status_data[_UNNEEDED]['option'] in self._filter_status:
            self._filter_unneeded = True

        self._ipqc_info   = ConfigObj(os.path.join(os.getenv('DMXDATA_ROOT'), self._ipqc.family.name, 'ipqc', 'settings.ini'))

        if self._ipqc != None:
            self.date = self._ipqc.date
            self.ip = self._ipqc.ip

            if self.ip.report_nfs != None:
                self._filename = self.ip.report_nfs
                self.ip.report_url = self.ip.report_nfs
                return
            else:

                if self.ip.is_immutable:
                    if (self._ipqc.requalify ==True):
                        (self.url_path, self.nfs_path) = (self.ip.workdir, self.ip.workdir)
                    else:
                        (self.url_path, self.nfs_path) = get_catalog_paths(self.ip.name, self.ip.bom, self.ip.milestone)
                else:
                    (self.url_path, self.nfs_path) = (self.ip.workdir, self.ip.workdir)

                self._filename = os.path.join(self.ip.workdir, 'ipqc.html')
                (self.roadmap_url, self.tests_url) = self.get_general_info()
                self.ip.report_nfs = os.path.join(self.nfs_path, 'ipqc.html')

                # IP top can have error but hierarchy is ok
                if self._ipqc.ip.err != '':

                    #for sub_ipqc in sorted(self._ipqc.top_hierarchy,  key=attrgetter('ip')):
                    for sub_ipqc in sorted(self._ipqc.top_hierarchy, key=lambda x: x.ip.name):

                        self._ipqc.ip.nb_pass_global = self._ipqc.ip.nb_pass_global + sub_ipqc.ip.nb_pass
                        self._ipqc.ip.nb_fail_global = self._ipqc.ip.nb_fail_global + sub_ipqc.ip.nb_fail
                        self._ipqc.ip.nb_warning_global = self._ipqc.ip.nb_warning_global +sub_ipqc.ip.nb_warning
                        self._ipqc.ip.nb_fatal_global = self._ipqc.ip.nb_fatal_global + sub_ipqc.ip.nb_fatal
                        self._ipqc.ip.nb_unneeded_global = self._ipqc.ip.nb_unneeded_global + sub_ipqc.ip.nb_unneeded
                        self._ipqc.ip.nb_na_global = self._ipqc.ip.nb_na_global + sub_ipqc.ip.nb_na

                else:


                    (self._ipqc.ip.nb_pass_global, self._ipqc.ip.nb_fail_global, self._ipqc.ip.nb_fatal_global, self._ipqc.ip.nb_warning_global, self._ipqc.ip.nb_unneeded_global, self._ipqc.ip.nb_na_global) = (self._ipqc.ip.nb_pass, self._ipqc.ip.nb_fail, self._ipqc.ip.nb_fatal, self._ipqc.ip.nb_warning, self._ipqc.ip.nb_unneeded, self._ipqc.ip.nb_na)

                    for i in self._ipqc.ip.flat_hierarchy:

                        s_ipqc = self._ipqc.get_ipqc(i)
                        if s_ipqc == None:
                            continue

                        self._ipqc.ip.nb_pass_global  = self._ipqc.ip.nb_pass_global + s_ipqc.ip.nb_pass
                        self._ipqc.ip.nb_fail_global  = self._ipqc.ip.nb_fail_global + s_ipqc.ip.nb_fail
                        self._ipqc.ip.nb_fatal_global   = self._ipqc.ip.nb_fatal_global + s_ipqc.ip.nb_fatal
                        self._ipqc.ip.nb_warning_global  = self._ipqc.ip.nb_warning_global + s_ipqc.ip.nb_warning
                        self._ipqc.ip.nb_unneeded_global = self._ipqc.ip.nb_unneeded_global + s_ipqc.ip.nb_unneeded
                        self._ipqc.ip.nb_na_global      = self._ipqc.ip.nb_na_global + s_ipqc.ip.nb_na

                self.generate()

        if self._msg != None:
            self.date           = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
            workdir = os.path.join("/tmp",  os.getenv('USER')+'_'+ip_name+'_'+self.date)
            (self.url_path, self.nfs_path) = (workdir, workdir)
            if not dir_accessible(workdir, os.F_OK):
                os.makedirs(workdir)
            self._filename = os.path.join(workdir, 'ipqc.html')
            self.generate()


    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value

    def get_general_info(self):
        roadmap_url = ''
        tests_url   = ''
        roadmap_url = re.sub('&device;', _DB_DEVICE, self._ipqc_info['RoadmapURL'])
        tests_url   = re.sub('&device;', _DB_DEVICE, self._ipqc_info['TestsURL'])
        return (roadmap_url, tests_url)

    def generate(self):
        self.header()
        self.summary()
        self.footer()

        if (_SIMPLE in self._report_template) and (self._ipqc.top == True):

            try:
                depth = self._report_template.split('#')[1]
            except IndexError:
                depth = 'all'

            set_report_template_simple(self._ipqc, self.url_path, depth=depth)
            self.ip.report_nfs = os.path.join(self.nfs_path, 'ipqc_simple.html')

    def header(self):
        f = open(self._filename, 'w')
        ##########################################################################
        # IPQC Results - Dashboard
        ##########################################################################
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
                <tr style="background-color: #E0E0E0"><th style="width: 10%; text-align: center; font-weight: bold; font-size: 15px; background-color: #E0E0E0;"><a style="color: blue;" href={}>HOME</a></th> \
                <th style="width: 80%; text-align: center; font-family: arial, helvetica, sans-serif; font-size:25px; background-color: #E0E0E0;">IPQC Dashboard</th> \
                <th style="width: 10%; text-align: center; font-size:15px; background-color: #E0E0E0;">Intel - PSG</th></tr> \
                </table></div>' .format(os.path.join(self.url_path, 'ipqc.html'), self.date, os.environ["USER"]), file=f)

        f.close()


    def summary(self):

        f = open(self._filename,'a')

        if self._ipqc != None:

            (code, out) = run_command("finger {} | head -n 1 | awk -F'Name: ' '{{print $2}}'" .format(self.ip.owner))
            if 'no such user' in out:
                owner = self.ip.owner
            else:
                owner = out.strip()

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
                        <tr><td style=\"width: 15%; font-weight: bold;\">Number of topcell(s):</td><td>{}</td></tr> \
                        <tr><td style=\"width: 15%; font-weight: bold;\">Number of deliverables:</td><td>{}</td></tr> \
                        <tr><td style=\"width: 15%; font-weight: bold;\">Number of tests (Top IP + Sub IPs):</td><td>{} ({} passed / {} waived / {} failed / {} fatal / {} unneeded / {} NA)</td></tr> \
                    </table>' .format(self.ip.name, self.ip.project, self.ip.family, self._ipqc.ip.graph, self.ip.name, self.ip.bom, self.ip.iptype, len(self._ipqc.top_hierarchy), owner, owner, self.ip.milestone, self.ip.nb_topcells, len(self.ip.deliverables), (self._ipqc.ip.nb_pass_global + self._ipqc.ip.nb_fail_global + self._ipqc.ip.nb_fatal_global + self._ipqc.ip.nb_warning_global + self._ipqc.ip.nb_unneeded_global + self._ipqc.ip.nb_na_global), self._ipqc.ip.nb_pass_global, self._ipqc.ip.nb_warning_global, self._ipqc.ip.nb_fail_global, self._ipqc.ip.nb_fatal_global, self._ipqc.ip.nb_unneeded_global, self._ipqc.ip.nb_na_global), file=f)

            print("<br>", file=f)

            if (self.ip.err != ''):
                print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 10%; background-color: #B4D8E7">Report Summary by deliverables and IPs</h2>', file=f)
                print("<br>", file=f)
                legend(f)
                print("<br>", file=f)
                print('<div style="width: 100%; display:table; border-left: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc; margin-left: 0%">', file=f)
                print("<h3 style=\"padding-left: 10%; background-color: {}; font-family: arial, helvetica, sans-serif; font-size:18px\"><b>ERROR: &nbsp;&nbsp;{} &nbsp;&nbsp;{} &nbsp;&nbsp;{}</b></h3>" .format(status_data[_FATAL_SYSTEM]['color'], self.ip.name, self.ip.bom, self.ip.err), file=f)
                print("<br>", file=f)
                print("<br>", file=f)

                self.set_array_hierarchy(self._ipqc, f)
                print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 10%; background-color: #B4D8E7">Report Summary by topcells</h2>', file=f)
                print("<br>", file=f)
                print("<h3 style=\"padding-left: 10%; background-color: {}; font-family: arial, helvetica, sans-serif; font-size:18px\"><b>ERROR: &nbsp;&nbsp;{} &nbsp;&nbsp;{} &nbsp;&nbsp;{}</b></h3>" .format(status_data[_FATAL_SYSTEM]['color'], self.ip.name, self.ip.bom, self.ip.err), file=f)
                print("<br>", file=f)
                print("<br>", file=f)
                self._set_environment_info(f)
                self._set_general_info(f)
                f.close()
                return


            ##########################################################################
            # IPQC - IP Report by IP
            ##########################################################################
            deliverable_list = {}

            ### Create the report with the functional template
            if self._report_template == _FUNCTIONALITY:
                set_report_template_functionality(self._ipqc, deliverable_list, self.url_path, self._ipqc_info, f, filter_status=self._filter_status)
            elif (self._report_template == _VIEW) or (_SIMPLE in self._report_template):
                deliverable_list = get_deliverable_score(deliverable_list, self._ipqc)
                set_report_template_view(self._ipqc, deliverable_list, self.url_path, f, filter_status=self._filter_status)
                self.set_array_hierarchy(self._ipqc, f)

                ##########################################################################
                # IPQC - IP Report by topcell
                ##########################################################################
                (nb_passed, nb_warning, nb_failed, nb_fatal, nb_unneeded, nb_na) = (0, 0, 0, 0, 0, 0)
                nb_column = len([nb_passed, nb_warning, nb_failed, nb_fatal, nb_unneeded, nb_na]) - len(self._filter_status)

                print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 10%; background-color: #B4D8E7">Report Summary by topcells</h2>', file=f)
                print("<br>", file=f)
                legend(f)
                print("<br>", file=f)
                print('<table border="1" width="89%" style="margin-left:10%; border: 1px solid; border-color:black; border-collapse: collapse;">', file=f)
                print("<tr border=\"1\" style=\"color: #FFFFFF; border: 1px solid; border-color:black; background-color: #1874CD; font-weight: bold; font-family: arial, helvetica, sans-serif;\">", file=f)
                print('<th border="1" rowspan=2 width="10%" style=" border: 1px solid; border-color:black; border-collapse: collapse;">IP(s)</th>', file=f)
                print('<th border="1" rowspan=2 width="27%" style=" border: 1px solid; border-color:black; border-collapse: collapse;">Top Cell(s)</th>', file=f)
                print('<th border="1" colspan={} width="36%" style=" border: 1px solid; border-color:black; border-collapse: collapse;">Test Result</th>' .format(nb_column), file=f)
                print('<th border="1" rowspan=2 width="16%" style=" border: 1px solid; border-color:black; border-collapse: collapse;">Total Test</th>', file=f)
                print("</tr>", file=f)

                print('<tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black; background-color: #1874CD; font-weight: bold; font-family: arial, helvetica, sans-serif;">', file=f)
                print('<th border="1" width="6%" style=" border: 1px solid; border-color:black; border-collapse: collapse;">Pass</th>', file=f)
                print('<th border="1" width="6%" style=" border: 1px solid; border-color:black; border-collapse: collapse;">Waived</th>', file=f)
                print('<th border="1" width="6%" style=" border: 1px solid; border-color:black; border-collapse: collapse;">Fail</th>', file=f)
                print('<th border="1" width="6%" style=" border: 1px solid; border-color:black; border-collapse: collapse;">Fatal</th>', file=f)

                if not(self._filter_unneeded):
                    print('<th border="1" width="6%" style=" border: 1px solid; border-color:black; border-collapse: collapse;">Unneeded</th>', file=f)

                print('<th border="1" width="6%" style=" border: 1px solid; border-color:black; border-collapse: collapse;">NA</th>', file=f)
                print("</tr>", file=f)

                for cell in sorted(self.ip.topcells,  key=attrgetter('name')):

                    nb_passed = nb_passed + cell.nb_pass
                    nb_warning = nb_warning + cell.nb_warning
                    nb_failed = nb_failed + cell.nb_fail
                    nb_fatal = nb_fatal + cell.nb_fatal

                    if not(self._filter_unneeded):
                        nb_unneeded = nb_unneeded + cell.nb_unneeded

                    nb_na = nb_na + cell.nb_nc
                    total_cell = cell.nb_pass + cell.nb_warning + cell.nb_fail + cell.nb_fatal + cell.nb_unneeded + cell.nb_nc

                    cell_report = ReportCell(os.path.join(self.url_path, 'ipqc.html'), self.ip, cell)
                    cell_report.generate()

                    print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)
                    print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (self.ip.name), file=f)
                    print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (cell.name), file=f)

                    filename = 'ipqc_'+cell.name+'.html'
                    report_html = os.path.join(self.url_path, filename)

                    if cell.nb_pass == 0:
                        print("<td>{}</td>"  .format(cell.nb_pass), file=f)
                    else:
                        print("<td style=\"background-color: {};\"><a href={}>{}</a></td>"  .format(status_data[_PASSED]['color'], report_html, cell.nb_pass), file=f)

                    if cell.nb_warning == 0:
                        print("<td>{}</td>"  .format(cell.nb_warning), file=f)
                    else:
                        print("<td style=\"background-color: {};\"><a href={}>{}</a></td>"  .format(status_data[_WARNING]['color'], report_html, cell.nb_warning), file=f)

                    if cell.nb_fail == 0:
                        print("<td>{}</td>"  .format(cell.nb_fail), file=f)
                    else:
                        print("<td style=\"background-color: {};\"><a href={}>{}</a></td>"  .format(status_data[_FAILED]['color'], report_html, cell.nb_fail), file=f)

                    if cell.nb_fatal == 0:
                        print("<td>{}</td>"  .format(cell.nb_fatal), file=f)
                    else:
                        print("<td style=\"color: #FFFFFF; background-color: {};\"><a href={} style=\"color: #FFFFFF;\">{}</a></td>"  .format(status_data[_FATAL]['color'], report_html, cell.nb_fatal), file=f)

                    if not(self._filter_unneeded):
                        if cell.nb_unneeded == 0:
                            print("<td>{}</td>"  .format(cell.nb_unneeded), file=f)
                        else:
                            print("<td style=\"background-color: {};\"><a href={}>{}</a></td>"  .format(status_data[_UNNEEDED]['color'], report_html, cell.nb_unneeded), file=f)

                    if cell.nb_nc == 0:
                        print("<td>{}</td>"  .format(cell.nb_nc), file=f)
                    else:
                        print("<td style=\"background-color: {};\">{}</td>"  .format(status_data[_NA]['color'], cell.nb_nc), file=f)

                    print("<td>{}</td>"  .format(total_cell), file=f)

                    print("</tr>", file=f)


                total = nb_passed + nb_warning + nb_failed + nb_fatal + nb_unneeded + nb_na

                # total of passed, waived, failed, fatal, unneeded, na for topcells
                print("<tr style=\"background-color: #AAD4FF;font-weight: bold; font-family: arial, helvetica, sans-serif;\">", file=f)
                print('<th>Total</th>', file=f)
                print('<th></th>', file=f)
                print("<th>{}</th>" .format(nb_passed), file=f)
                print("<th>{}</th>" .format(nb_warning), file=f)
                print("<th>{}</th>" .format(nb_failed), file=f)
                print("<th>{}</th>" .format(nb_fatal), file=f)
                if not(self._filter_unneeded):
                    print("<th>{}</th>" .format(nb_unneeded), file=f)
                print("<th>{}</th>" .format(nb_na), file=f)
                print('<th>{}</th>' .format(total), file=f)
                print("</tr>", file=f)

                # percentage of passed, waived, failed, fatal, unneeded, na for topcells
                print("<tr style=\"background-color: #AAD4FF;font-weight: bold; font-family: arial, helvetica, sans-serif;\">", file=f)
                print('<th>Total %</th>', file=f)
                print('<th></th>', file=f)
                print("<th>{}%</th>" .format(nb_passed if nb_passed==0 else percentage(nb_passed, total)), file=f)
                print("<th>{}%</th>" .format(nb_warning if nb_warning==0 else percentage(nb_warning, total)), file=f)
                print("<th>{}%</th>" .format(nb_failed if nb_failed==0 else percentage(nb_failed, total)), file=f)
                print("<th>{}%</th>" .format(nb_fatal if nb_fatal==0 else percentage(nb_fatal, total)), file=f)
                if not(self._filter_unneeded):
                    print("<th>{}%</th>" .format(nb_unneeded if nb_unneeded==0 else percentage(nb_unneeded, total)), file=f)
                print("<th>{}%</th>" .format(nb_na if nb_na==0 else percentage(nb_na, total)), file=f)
                print('<th>{}%</th>' .format(total if total==0 else int(percentage(total, total))), file=f)
                print("</tr>", file=f)

                print("</table>", file=f)

                print("<br>", file=f)
                print("<br>", file=f)


            self._set_environment_info(f)
            self._set_general_info(f)

        if self._msg != None:
            print('<div style="width: 100%; display:table; border-left: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc; margin-left: 0%">', file=f)
            print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 10%; background-color: #B4D8E7">Executive summary for IP {}</h2> \
                    <table width="90%" style="padding-left:10%; text-align:left; font-family: arial, helvetica, sans-serif;"> \
                        <tr><td style=\"width: 10%; font-weight: bold;\">Command:</td><td>{}</td></tr> \
                        </table>' .format(self._ip_name, 'ipqc '+ ' '.join(sys.argv[1:])), file=f)
            print("<p style=\"padding-left: 10%; background-color: {};  font-size:20px\">ERROR: {}</p>" .format(status_data[_FATAL_SYSTEM]['color'], self._msg), file=f)

            print("<br>", file=f)
            print("<br>", file=f)

        f.close()


    def footer(self):

        f = open(self._filename,'a')

        ##########################################################################
        # IPQC - Support Information Section
        ##########################################################################
        print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 10%; background-color: #B4D8E7">Support</h2> \
                <ul style="list-style-type: none; font-family: arial, helvetica, sans-serif; padding-left: 10%;"> \
                <li>Go to <a href="{}">{}</a></li> \
                <ul> \
                    <li>Family: {}</li> \
                    <li>Release: {}</li> \
                    <li>Component: {}</li> \
                </ul> \
                </ul>' .format('https://hsdes.intel.com/appstore/article/#/fpga.support', 'https://hsdes.intel.com/appstore/article/#/fpga.support', 'fpga_da', 'fpga_design_infra', 'tool.ipqc'), file=f)


        print('</div>', file=f)
        print("</div>", file=f)
        print("</div>", file=f)
        print("</body>", file=f)
        print("</html>", file=f)

        f.close()


    ##########################################################################
    # IPQC - Environment Information
    #   --> ARC Bundle
    #   --> System Information (OS, Release, Host, ...)
    ##########################################################################
    def _set_environment_info(self, f):
        print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 10%; background-color: #B4D8E7">Environment Information</h2>', file=f)
        print('<table width="90%" style="margin-left:10%; text-align:left; font-family: arial, helvetica, sans-serif;"> \
                <tr><td style="width: 15%; font-weight: bold;">Command:</td><td>{}</td></tr> \
                <tr><td style="width: 15%; font-weight: bold;">ARC bundle:</td><td>{}</td></tr> \
                <tr><td style="width: 15%; font-weight: bold;">Operating System:</td><td>{}</td></tr> \
                <tr><td style="width: 15%; font-weight: bold;">Hostname:</td><td>{}</td></tr> \
                <tr><td style="width: 15%; font-weight: bold;">Kernel Release:</td><td>{}</td></tr> \
                <tr><td style="width: 15%; font-weight: bold;">Machine:</td><td>{}</td></tr> \
            </table>' .format(self._ipqc.environment.cmd, self._ipqc.environment.arc_resources, self._ipqc.environment.os_name, self._ipqc.environment.hostname, self._ipqc.environment.release, self._ipqc.environment.machine), file=f)

        print("<br>", file=f)
        print("<br>", file=f)


    ##########################################################################
    # IPQC - General Information Section
    ##########################################################################
    def _set_general_info(self, f):
        print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 10%; background-color: #B4D8E7">General Information</h2>', file=f)
        print('<table width="90%" style="margin-left:10%; text-align:left; font-family: arial, helvetica, sans-serif;"> \
                <tr><td style="width: 20%; font-weight: bold;"><a href="{}">{} Roadmap</a></td></tr> \
                <tr><td style="width: 20%; font-weight: bold;"><a href="{}">{} Tests</a></td></tr> \
                <tr><td style="width: 20%; font-weight: bold;"></td></tr> \
                <tr><td style="width: 20%; font-weight: bold;">Process: {}</td></tr> \
                <tr><td style="width: 20%; font-weight: bold;">Product: {}</td></tr> \
                <tr><td style="width: 20%; font-weight: bold;">Device: {}</td></tr> \
                </table>' .format(self.roadmap_url, self._ipqc.family.name, self.tests_url, self._ipqc.family.name, os.getenv("DB_PROCESS"), self.ip.workspace.project, os.getenv("DB_DEVICE")), file=f)
        print("<br>", file=f)


    def set_array_hierarchy(self, ipqc, f):

        (nb_passed, nb_warning, nb_failed, nb_fatal, nb_unneeded, nb_na) = (0, 0, 0, 0, 0, 0)
        nb_columns = len([nb_passed, nb_warning, nb_failed, nb_fatal, nb_unneeded, nb_na]) -  len(self._filter_status)

        ####################################################
        # IP Hierarchy Reports
        ####################################################
        if (ipqc.top_hierarchy != []):

            ### Array of IPs
            print('<table border="1" width="89%" style="margin-left:10%; border: 1px solid; border-color:black; border-collapse: collapse;">', file=f)
            print('<tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD; font-weight: bold; font-family: arial, helvetica, sans-serif;">', file=f)
            print('<th border="1" rowspan=2 width="10%" style="border: 1px solid; border-color:black; border-collapse: collapse;">IP(s)</th>', file=f)
            print('<th border="1" rowspan=2 width="27%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Version</th>', file=f)
            print('<th border="1" colspan={} width="36%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Test Result</th>' .format(nb_columns), file=f)
            print('<th border="1" rowspan=2 width="16%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Total Test</th>', file=f)
            print("</tr>", file=f)
            print('<tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD; font-weight: bold; font-family: arial, helvetica, sans-serif;">', file=f)
            print('<th border="1" width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Pass</th>', file=f)
            print('<th border="1" width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Waived</th>', file=f)
            print('<th border="1" width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Fail</th>', file=f)
            print('<th border="1" width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Fatal</th>', file=f)

            if not(self._filter_unneeded):
                print('<th border="1" width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Unneeded</th>', file=f)
            print('<th border="1" width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">NA</th>', file=f)
            print("</tr>", file=f)



            for sub_ipqc in sorted(ipqc.top_hierarchy,  key=attrgetter('ip.name')):

                ip = sub_ipqc.ip

                ip_nb_pass = ip.nb_pass
                ip_nb_fail = ip.nb_fail
                ip_nb_warning = ip.nb_warning
                ip_nb_fatal = ip.nb_fatal
                ip_nb_unneeded = ip.nb_unneeded
                ip_nb_na = ip.nb_na

                filename = 'ipqc.html'

                if (ip.err != ''):
                    print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)
                    print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (ip.name), file=f)
                    print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (ip.bom), file=f)
                    print("<td colspan=6 style=\"background-color: {};\">{}</td>" .format(status_data[_FATAL_SYSTEM]['color'], ip.err), file=f)
                    print("</tr>", file=f)
                    continue


                print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)
                print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (ip.name), file=f)
                print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (ip.bom), file=f)

                if ip.is_immutable:
                    if (self._ipqc.requalify ==True):
                        (url_path, nfs_path) = (ip.workdir, ip.workdir)
                    else:
                        (url_path, nfs_path) = get_catalog_paths(ip.name, ip.bom, ip.milestone)
                else:
                    (url_path, nfs_path) = (ip.workdir, ip.workdir)
                    ip.report_nfs = os.path.join(nfs_path, filename)

                report_html = os.path.join(url_path, filename)

                if ip_nb_pass == 0:
                     print("<td>{}</td>"  .format(ip_nb_pass), file=f)
                else:
                    print("<td style=\"background-color: {};\"><a href={}>{}</a></td>"  .format(status_data[_PASSED]['color'], report_html, ip_nb_pass), file=f)

                if ip_nb_warning == 0:
                    print("<td>{}</td>"  .format(ip_nb_warning), file=f)
                else:
                    print("<td style=\"background-color: {};\"><a href={}>{}</a></td>"  .format(status_data[_WARNING]['color'], report_html, ip_nb_warning), file=f)

                if ip_nb_fail == 0:
                    print("<td>{}</td>"  .format(ip_nb_fail), file=f)
                else:
                    print("<td style=\"background-color: {};\"><a href={}>{}</a></td>"  .format(status_data[_FAILED]['color'], report_html, ip_nb_fail), file=f)

                if ip_nb_fatal == 0:
                    print("<td>{}</td>"  .format(ip_nb_fatal), file=f)
                else:
                    print("<td style=\"color: #FFFFFF; background-color: {};\"><a href={} style=\"color: #FFFFFF;\">{}</a></td>"  .format(status_data[_FATAL]['color'], report_html, ip_nb_fatal), file=f)

                if not(self._filter_unneeded):
                    if ip_nb_unneeded == 0:
                        print("<td>{}</td>"  .format(ip_nb_unneeded), file=f)
                    else:
                        print("<td td style=\"background-color: {};\"><a href={}>{}</a></td>"  .format(status_data[_UNNEEDED]['color'], report_html, ip_nb_unneeded), file=f)

                if ip_nb_na == 0:
                    print("<td>{}</td>"  .format(ip_nb_na), file=f)
                else:
                    print("<td style=\"background-color: {};\">{}</td>"  .format(status_data[_NA]['color'], ip_nb_na), file=f)

                print("<td>{}</td>"  .format(ip_nb_pass + ip_nb_warning + ip_nb_fail + ip_nb_fatal + ip_nb_unneeded + ip_nb_na), file=f)
                print("</tr>", file=f)

                nb_passed = nb_passed + ip_nb_pass
                nb_warning = nb_warning + ip_nb_warning
                nb_failed = nb_failed + ip_nb_fail
                nb_fatal = nb_fatal + ip_nb_fatal
                nb_unneeded = nb_unneeded + ip_nb_unneeded
                nb_na = nb_na + ip_nb_na

            total = nb_passed + nb_warning + nb_failed + nb_fatal + nb_na

            if not(self._filter_unneeded):
                total = total + nb_unneeded

            # total of passed, waived, failed, fatal, unneeded, na for sub-IPs
            print("<tr style=\"background-color: #AAD4FF;font-weight: bold; font-family: arial, helvetica, sans-serif;\">", file=f)
            print('<th>Total</th>', file=f)
            print('<th></th>', file=f)
            print("<th>{}</th>" .format(nb_passed), file=f)
            print("<th>{}</th>" .format(nb_warning), file=f)
            print("<th>{}</th>" .format(nb_failed), file=f)
            print("<th>{}</th>" .format(nb_fatal), file=f)

            if not(self._filter_unneeded):
                print("<th>{}</th>" .format(nb_unneeded), file=f)
            print("<th>{}</th>" .format(nb_na), file=f)
            print('<th>{}</th>' .format(total), file=f)
            print("</tr>", file=f)

            # percentage of passed, waived, failed, fatal, unneeded, na for sub-IPs
            print("<tr style=\"background-color: #AAD4FF;font-weight: bold; font-family: arial, helvetica, sans-serif;\">", file=f)
            print('<th>Total %</th>', file=f)
            print('<th></th>', file=f)
            print("<th>{}%</th>" .format(nb_passed if nb_passed==0 else percentage(nb_passed, total)), file=f)
            print("<th>{}%</th>" .format(nb_warning if nb_warning==0 else percentage(nb_warning, total)), file=f)
            print("<th>{}%</th>" .format(nb_failed if nb_failed==0 else percentage(nb_failed, total)), file=f)
            print("<th>{}%</th>" .format(nb_fatal if nb_fatal==0 else percentage(nb_fatal, total)), file=f)

            if not(self._filter_unneeded):
                print("<th>{}%</th>" .format(nb_unneeded if nb_unneeded==0 else percentage(nb_unneeded, total)), file=f)

            print("<th>{}%</th>" .format(nb_na if nb_na==0 else percentage(nb_na, total)), file=f)
            print('<th>{}%</th>' .format(total if total==0 else int(percentage(total, total))), file=f)
            print("</tr>", file=f)

            print("</table>", file=f)
            print("<br>", file=f)
            print("<br>", file=f)
