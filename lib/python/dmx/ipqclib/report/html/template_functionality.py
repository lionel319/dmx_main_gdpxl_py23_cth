#!/usr/bin/env python
from __future__ import print_function
import os
from operator import attrgetter
from dmx.ipqclib.log import uiInfo, uiWarning, uiError, uiCritical, uiDebug
from dmx.ipqclib.report.html.report_deliverable import ReportDeliverable
from dmx.ipqclib.utils import get_catalog_paths, percentage, dsum, file_accessible
from dmx.ipqclib.report.html.legend import legend
from dmx.ipqclib.report.html.utils import set_array_ip_table, get_deliverables_description
from dmx.ipqclib.settings import _PASSED, _FAILED, _FATAL, _FATAL_SYSTEM, _NA, _NA_ERROR, _WARNING, _ALL_WAIVED, _UNNEEDED, _NA_MILESTONE, _NOT_POR, \
    status_data, _DB_FAMILY, _REL, _SNAP, _DB_DEVICE
from dmx.ipqclib.report.html.report_functionality import ReportFunctionality
from dmx.ipqclib.report.html.report_deliverable_functionality import ReportDeliverableFunctionality


def get_deliverable_score(deliverable_list, ipqc):
    
    for deliverable in ipqc.ip.deliverables:
                    
        if deliverable.name in deliverable_list.keys():
            deliverable_list[deliverable.name]['status'].append(deliverable.status)
            deliverable_list[deliverable.name]['nb_passed'] = deliverable_list[deliverable.name]['nb_passed'] + deliverable.nb_pass
            deliverable_list[deliverable.name]['nb_failed'] = deliverable_list[deliverable.name]['nb_failed'] + deliverable.nb_fail
            deliverable_list[deliverable.name]['nb_fatal'] = deliverable_list[deliverable.name]['nb_fatal'] + deliverable.nb_fatal
            deliverable_list[deliverable.name]['nb_warning'] = deliverable_list[deliverable.name]['nb_warning'] + deliverable.nb_warning
            deliverable_list[deliverable.name]['nb_unneeded'] = deliverable_list[deliverable.name]['nb_unneeded'] + deliverable.nb_unneeded
            deliverable_list[deliverable.name]['nb_na'] = deliverable_list[deliverable.name]['nb_na'] + deliverable.nb_na
            if (deliverable.deliverable_existence['unwaived'] != []) and  (deliverable_list[deliverable.name]['existence'] == ''):
                for message in deliverable.deliverable_existence['unwaived']:
                    if message[1] == deliverable.name:
                        deliverable_list[deliverable.name]['existence'] = message

            continue
        
        existence = ''
        if deliverable.deliverable_existence['unwaived'] != []:
            for message in deliverable.deliverable_existence['unwaived']:
                if message[1] == deliverable.name:
                    existence = message

        deliverable_list[deliverable.name] = {'status' : [deliverable.status], 'bom' : deliverable.bom, 'nb_passed' : deliverable.nb_pass, 'nb_failed' : deliverable.nb_fail, 'nb_fatal' : deliverable.nb_fatal, 'nb_warning' : deliverable.nb_warning, 'nb_unneeded': deliverable.nb_unneeded,'nb_na' : deliverable.nb_na, 'err': deliverable.err, 'existence': existence}
    return deliverable_list

def set_report_template_functionality(ipqc, deliverable_list, g_url_path, ipqc_info, f, filter_status=[]):

    (nb_passed, nb_warning, nb_failed, nb_fatal, nb_unneeded, nb_na, total) = (0, 0, 0, 0, 0, 0, 0)

    list_of_ips_per_functionality = {}
    score_functionality = {}

    deliverables_description = get_deliverables_description()

    # https://hsdes.intel.com/resource/1409433556
    #IPQC report for power - remove unneeded count from final
    filter_unneeded =  False
    if status_data[_UNNEEDED]['option'] in filter_status:
        filter_unneeded = True    

    l = [ipqc] + ipqc.hierarchy

    for sub_ipqc in l: 
        deliverable_list = get_deliverable_score(deliverable_list, sub_ipqc)


    ################### BEGIN
    set_array_ip_table(f, filter_status=filter_status)

    for deliverable, values in sorted(deliverable_list.items()):

        nb_checkers = deliverable_list[deliverable]['nb_na'] + deliverable_list[deliverable]['nb_unneeded'] + deliverable_list[deliverable]['nb_warning'] + deliverable_list[deliverable]['nb_fatal'] + deliverable_list[deliverable]['nb_failed'] + deliverable_list[deliverable]['nb_passed']

        print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)
        print("<td>{}</td>" .format(deliverable), file=f)
        print("<td style=\"background-color: #E0E0E0;\">{}</td>" .format(deliverables_description[deliverable.upper()]), file=f)


        # Report per deliverable
        deliverable_report = ReportDeliverableFunctionality(os.path.join(g_url_path, 'ipqc.html'), ipqc, deliverable, deliverable_list, filter_status=filter_status)
        deliverable_report.generate()
            
        report_html = deliverable_report.filename

        # For passed, passed with waivers, failed, fatal put a report link
        # For waived deliverables and not applicable milestone deliverable do not need report
#                if (deliverable.status == _ALL_WAIVED) or (deliverable.status == _NA_MILESTONE) or (deliverable.is_unneeded == True):

        if deliverable_list[deliverable]['nb_passed'] == 0:
            print("<td>{}</td>"  .format(deliverable_list[deliverable]['nb_passed']), file=f)
        else:
            print("<td style=\"background-color: {};\"><a href={}>{}</td>"  .format(status_data[_PASSED]['color'], report_html, deliverable_list[deliverable]['nb_passed']), file=f)

        if deliverable_list[deliverable]['nb_warning'] == 0:
            print("<td>{}</td>"  .format(deliverable_list[deliverable]['nb_warning']), file=f)
        else:
            print("<td style=\"background-color: {};\"><a href={}>{}</td>"  .format(status_data[_WARNING]['color'], report_html, deliverable_list[deliverable]['nb_warning']), file=f)

        if deliverable_list[deliverable]['nb_failed'] == 0:
            print("<td>{}</td>"  .format(deliverable_list[deliverable]['nb_failed']), file=f)
        else:
            print("<td style=\"background-color: {};\"><a href={}>{}</td>"  .format(status_data[_FAILED]['color'], report_html, deliverable_list[deliverable]['nb_failed']), file=f)
    
        if deliverable_list[deliverable]['nb_fatal'] == 0:
            print("<td>{}</td>"  .format(deliverable_list[deliverable]['nb_fatal']), file=f)
        else:
            print("<td style=\"color: #FFFFFF; background-color: {};\">{}</td>"  .format(status_data[_FATAL]['color'], deliverable_list[deliverable]['nb_fatal']), file=f)

        if not(filter_unneeded):
            if deliverable_list[deliverable]['nb_unneeded'] == 0:
                print("<td>{}</td>"  .format(deliverable_list[deliverable]['nb_unneeded']), file=f)
            else:
                print("<td style=\"background-color: {};\"><a href={}>{}</td>"  .format(status_data[_UNNEEDED]['color'], report_html, deliverable_list[deliverable]['nb_unneeded']), file=f)
            nb_unneeded     = nb_unneeded + deliverable_list[deliverable]['nb_unneeded']

        if deliverable_list[deliverable]['nb_na'] == 0:
            print("<td>{}</td>"  .format(deliverable_list[deliverable]['nb_na']), file=f)
        else:    
            print("<td style=\"background-color: {};\">{}</td>"  .format(status_data[_NA]['color'], deliverable_list[deliverable]['nb_na']), file=f)
            
        print("<td>{}</td>"  .format(nb_checkers), file=f)

        print("</tr>", file=f)

        nb_passed       = nb_passed + deliverable_list[deliverable]['nb_passed']
        nb_warning      = nb_warning + deliverable_list[deliverable]['nb_warning']
        nb_failed       = nb_failed + deliverable_list[deliverable]['nb_failed'] 
        nb_fatal        = nb_fatal + deliverable_list[deliverable]['nb_fatal']
        nb_na           = nb_na + deliverable_list[deliverable]['nb_na']

    total = nb_passed + nb_warning + nb_failed + nb_fatal + nb_unneeded + nb_na

    # total of passed, waived, failed, fatal, unneeded, na for topcells
    print("<tr style=\"background-color: #AAD4FF;font-weight: bold; font-family: arial, helvetica, sans-serif;\">", file=f)
    print('<th>Total</th>', file=f)
    print('<th></th>', file=f)
    print("<th>{}</th>" .format(nb_passed), file=f)
    print("<th>{}</th>" .format(nb_warning), file=f)
    print("<th>{}</th>" .format(nb_failed), file=f)
    print("<th>{}</th>" .format(nb_fatal), file=f)

    if not(filter_unneeded):
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

    if not(filter_unneeded):
        print("<th>{}%</th>" .format(nb_unneeded if nb_unneeded==0 else percentage(nb_unneeded, total)), file=f)

    print("<th>{}%</th>" .format(nb_na if nb_na==0 else percentage(nb_na, total)), file=f)
    print('<th>{}%</th>' .format(total if total==0 else int(percentage(total, total))), file=f)
    print("</tr>", file=f)

    print("</table>", file=f)
    print("<br>", file=f)
    print("<br>", file=f)

################### END

    (nb_passed, nb_warning, nb_failed, nb_fatal, nb_unneeded, nb_na) = (0, 0, 0, 0, 0, 0)
    nb_columns = len([nb_passed, nb_warning, nb_failed, nb_fatal, nb_unneeded, nb_na]) - len(filter_status)

    print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 10%; background-color: #B4D8E7">Report Summary by IPs</h2>', file=f)

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

    if not(filter_unneeded):
        print('<th border="1" width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Unneeded</th>', file=f)

    print('<th border="1" width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">NA</th>', file=f)
    print("</tr>", file=f)

    
    
    list_of_ips_per_functionality = {}
    score_functionality = {}

    l = ipqc.hierarchy + [ipqc]

    for sub_ipqc in l: 

        for functionality in sub_ipqc.ip.functionality:

            list_of_cells = []

            try:
                list_of_ips_per_functionality[functionality]
            except KeyError:
                list_of_ips_per_functionality[functionality] = {}
                score_functionality[functionality] = {_PASSED: 0, _WARNING: 0, _FAILED: 0, _FATAL: 0, _UNNEEDED: 0, _NA: 0}

            for cell in sub_ipqc.ip.topcells:
                if cell.functionality == functionality:
                    list_of_cells.append(cell)
                    if not(filter_unneeded):
                        score_functionality[functionality] = dsum(score_functionality[functionality], {_PASSED: cell.nb_pass, _WARNING: cell.nb_warning, _FAILED: cell.nb_fail, _FATAL: cell.nb_fatal, _UNNEEDED: cell.nb_unneeded, _NA: cell.nb_nc})
                    else:
                        score_functionality[functionality] = dsum(score_functionality[functionality], {_PASSED: cell.nb_pass, _WARNING: cell.nb_warning, _FAILED: cell.nb_fail, _FATAL: cell.nb_fatal, _NA: cell.nb_nc})
                    
            list_of_ips_per_functionality[functionality][sub_ipqc.ip] = list_of_cells


    nb_passed   = 0
    nb_warning  = 0
    nb_failed   = 0
    nb_fatal    = 0
    nb_unneeded = 0
    nb_na       = 0
    total       = 0

    # Get score per functionality
    for functionality, ips in sorted(list_of_ips_per_functionality.items()):
        total_functionality = score_functionality[functionality][_PASSED] + score_functionality[functionality][_WARNING] + score_functionality[functionality][_FAILED] + score_functionality[functionality][_FATAL] + score_functionality[functionality][_UNNEEDED] + score_functionality[functionality][_NA]
 
        print('<tr border="1" style="border: 1px solid; text-align: center; background-color: #99BB99; font-weight: bold; font-family: arial, helvetica, sans-serif;">', file=f)
        print('<th border="1" style="border: 1px solid; text-align: center; background-color: #99BB99; font-weight: bold; font-family: arial, helvetica, sans-serif;">{}</th>' .format(functionality), file=f)
        print('<th border="1" style="border: 1px solid; text-align: center; background-color: #99BB99; font-weight: bold; font-family: arial, helvetica, sans-serif;"></th>', file=f)
        print('<th border="1" style="border: 1px solid; text-align: center; background-color: #99BB99; font-weight: bold; font-family: arial, helvetica, sans-serif;">{}</th>' .format(score_functionality[functionality][_PASSED]), file=f)
        print('<th border="1" style="border: 1px solid; text-align: center; background-color: #99BB99; font-weight: bold; font-family: arial, helvetica, sans-serif;">{}</th>' .format(score_functionality[functionality][_WARNING]), file=f)
        print('<th border="1" style="border: 1px solid; text-align: center; background-color: #99BB99; font-weight: bold; font-family: arial, helvetica, sans-serif;">{}</th>' .format(score_functionality[functionality][_FAILED]), file=f)
        print('<th border="1" style="border: 1px solid; text-align: center; background-color: #99BB99; font-weight: bold; font-family: arial, helvetica, sans-serif;">{}</th>' .format(score_functionality[functionality][_FATAL]), file=f)

        if not(filter_unneeded):
            print('<th border="1" style="border: 1px solid; text-align: center; background-color: #99BB99; font-weight: bold; font-family: arial, helvetica, sans-serif;">{}</th>' .format(score_functionality[functionality][_UNNEEDED]), file=f)

        print('<th border="1" style="border: 1px solid; text-align: center; background-color: #99BB99; font-weight: bold; font-family: arial, helvetica, sans-serif;">{}</th>' .format(score_functionality[functionality][_NA]), file=f)
        print('<th border="1" style="border: 1px solid; text-align: center; background-color: #99BB99; font-weight: bold; font-family: arial, helvetica, sans-serif;">{}</th>' .format(total_functionality), file=f)
        print("</tr>", file=f)

        for ip in ips:

            if ip.err != '':
                print("<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">", file=f)
                print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (ip.name), file=f)
                print("<td style=\"background-color: #E0E0E0;\">%s</td>" % (ip.bom), file=f)
                print("<td colspan={} style=\"background-color: {};\">{}</td>" .format(nb_columns, status_data[_FATAL_SYSTEM]['color'], ip.err), file=f)
                print("</tr>", file=f)
                continue                


            # Report IP
            functionality_report = ReportFunctionality(os.path.join(g_url_path, 'ipqc.html'), ip, functionality, filter_status=filter_status)
            functionality_report.generate()
            report_html = functionality_report.filename

            print('<tr style="text-align:center; font-family: arial, helvetica, sans-serif;">', file=f)
            print('<td style="background-color: {};">{}</td>' .format(status_data[_NA]['color'], ip.name), file=f)
            print('<td style="background-color: {};">{}</td>' .format(status_data[_NA]['color'], ip.bom), file=f)

            ip_nb_passed   = 0
            ip_nb_warning  = 0
            ip_nb_failed   = 0
            ip_nb_fatal    = 0
            ip_nb_unneeded = 0
            ip_nb_na       = 0

            for cell in list_of_ips_per_functionality[functionality][ip]:
                ip_nb_passed   = ip_nb_passed + cell.nb_pass
                ip_nb_warning  = ip_nb_warning + cell.nb_warning
                ip_nb_failed   = ip_nb_failed + cell.nb_fail
                ip_nb_fatal    = ip_nb_fatal + cell.nb_fatal

                if not(filter_unneeded):
                    ip_nb_unneeded = ip_nb_unneeded + cell.nb_unneeded

                ip_nb_na       = ip_nb_na + cell.nb_nc

            ip_total = ip_nb_passed + ip_nb_warning + ip_nb_failed + ip_nb_fatal + ip_nb_unneeded + ip_nb_na

       
            if ip_nb_passed == 0:
                print('<td>{}</td>'  .format(ip_nb_passed), file=f)
            else:
                print('<td style="background-color: {};"><a href={}>{}</td>'  .format(status_data[_PASSED]['color'], report_html, ip_nb_passed), file=f)
    
            if ip_nb_warning == 0:
                print('<td>{}</td>'  .format(ip_nb_warning), file=f)
            else:
                print('<td style="background-color: {};"><a href={}>{}</td>'  .format(status_data[_WARNING]['color'], report_html, ip_nb_warning), file=f)
    
            if ip_nb_failed == 0:
                print('<td>{}</td>'  .format(ip_nb_failed), file=f)
            else:
                print('<td style="background-color: {};"><a href={}>{}</td>'  .format(status_data[_FAILED]['color'], report_html, ip_nb_failed), file=f)

            if ip_nb_fatal == 0:
                print('<td>{}</td>'  .format(ip_nb_fatal), file=f)
            else:
                print('<td style="background-color: {};"><a href={}>{}</td>'  .format(status_data[_FATAL]['color'], report_html, ip_nb_fatal), file=f)


            if not(filter_unneeded):
                if ip_nb_unneeded == 0:
                    print('<td>{}</td>'  .format(ip_nb_unneeded), file=f)
                else:
                    print('<td style="background-color: {};"><a href={}>{}</td>'  .format(status_data[_UNNEEDED]['color'], report_html, ip_nb_unneeded), file=f)
                nb_unneeded     = nb_unneeded + ip_nb_unneeded

            if ip_nb_na == 0:
                print('<td>{}</td>'  .format(ip_nb_na), file=f)
            else:
                print('<td style="background-color: {};"><a href={}>{}</td>'  .format(status_data[_NA]['color'], report_html, ip_nb_na), file=f)
            
            print('<td>{}</td>' .format(ip_total), file=f)
            print("</tr>", file=f)

            nb_passed       = nb_passed + ip_nb_passed
            nb_warning      = nb_warning + ip_nb_warning
            nb_failed       = nb_failed + ip_nb_failed
            nb_fatal        = nb_fatal + ip_nb_fatal
            nb_na           = nb_na + ip_nb_na
            total           = total + ip_total

    # total of passed, waived, failed, fatal, unneeded, na for topcells
    print("<tr style=\"background-color: #AAD4FF;font-weight: bold; font-family: arial, helvetica, sans-serif;\">", file=f)
    print('<th>Total</th>', file=f)
    print('<th></th>', file=f)
    print("<th>{}</th>" .format(nb_passed), file=f)
    print("<th>{}</th>" .format(nb_warning), file=f)
    print("<th>{}</th>" .format(nb_failed), file=f)
    print("<th>{}</th>" .format(nb_fatal), file=f)

    if not(filter_unneeded):
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
    if not(filter_unneeded):
        print("<th>{}%</th>" .format(nb_unneeded if nb_unneeded==0 else percentage(nb_unneeded, total)), file=f)
    print("<th>{}%</th>" .format(nb_na if nb_na==0 else percentage(nb_na, total)), file=f)
    print('<th>{}%</th>' .format(total if total==0 else int(percentage(total, total))), file=f)
    print("</tr>", file=f) 

    print("</table>", file=f)

    print("<br>", file=f)
    print("<br>", file=f)
