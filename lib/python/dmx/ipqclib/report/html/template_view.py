#!/usr/bin/env python
from __future__ import print_function
import os
import json
from dmx.ipqclib.log import uiInfo, uiWarning, uiError, uiCritical, uiDebug
from dmx.ipqclib.report.html.report_deliverable import ReportDeliverable
from dmx.ipqclib.utils import get_catalog_paths, percentage, dsum
from dmx.ipqclib.settings import _PASSED, _FAILED, _FATAL, _FATAL_SYSTEM, _NA, _NA_ERROR, _WARNING, _ALL_WAIVED, _UNNEEDED, _NA_MILESTONE, _NOT_POR, \
status_data, _DB_FAMILY, _REL, _SNAP, _DB_DEVICE, _VIEW_RTL, _VIEW_PHYS, _VIEW_TIMING, _VIEW_OTHER, _MAP_VIEWS, _DELIVERABLES_DESCRIPTION, _VIEW, _VIEW_ORDER
from dmx.ipqclib.report.html.legend import legend
from dmx.ipqclib.report.html.utils import get_deliverables_description

def set_report_template_view(ipqc, deliverable_list, g_url_path, f, filter_status=[]):
    
    (nb_passed, nb_warning, nb_failed, nb_fatal, nb_unneeded, nb_na) = (0, 0, 0, 0, 0, 0)
    nb_columns = len([nb_passed, nb_warning, nb_failed, nb_fatal, nb_unneeded, nb_na]) - len(filter_status)

    filter_unneeded = False

    if "unneeded" in filter_status:
        filter_unneeded = True

    deliverables_description = get_deliverables_description()
    
    text = {_VIEW_RTL: '', _VIEW_PHYS: '', _VIEW_TIMING:'', _VIEW_OTHER:''}
    score_views = {_VIEW_RTL: {_PASSED: 0, _WARNING: 0, _FAILED: 0, _FATAL: 0, _UNNEEDED: 0, _NA: 0}, _VIEW_PHYS: {_PASSED: 0, _WARNING: 0, _FAILED: 0, _FATAL: 0, _UNNEEDED: 0, _NA: 0}, _VIEW_TIMING: {_PASSED: 0, _WARNING: 0, _FAILED: 0, _FATAL: 0, _UNNEEDED: 0, _NA: 0}, _VIEW_OTHER: {_PASSED: 0, _WARNING: 0, _FAILED: 0, _FATAL: 0, _UNNEEDED: 0, _NA: 0}}

    keyorder_deliverable = [_PASSED, _WARNING, _FAILED, _FATAL, _ALL_WAIVED, _UNNEEDED, _NA_MILESTONE, _NA]

    print('<h2 style="font-family: arial, helvetica, sans-serif; padding-left: 10%; background-color: #B4D8E7">Report Summary by deliverables and IPs</h2>', file=f)
    print("<br>", file=f)
    legend(f)
    print("<br>", file=f)

    ### Array of deliverables for Top IP
    print('<table border="1" width="89%" style="margin-left:10%; border: 1px solid; border-color:black; border-collapse: collapse;">', file=f)
    print('<tr border="1" style="color: #FFFFFF; border: 1px solid; border-color:black; border-collapse: collapse; background-color: #1874CD; font-weight: bold; font-family: arial, helvetica, sans-serif;">', file=f)
    print('<th border="1" rowspan=2 width="10%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Deliverables</th>', file=f)
    print('<th border="1" rowspan=2 width="17%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Description</th>', file=f)
    print('<th border="1" rowspan=2 width="10%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Version</th>', file=f)
    print('<th border="1" colspan={} width="36%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Test Result</th>' .format(nb_columns), file=f)
    print('<th border="1" rowspan=2 width="6%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Total Test</th>', file=f)
    print('<th border="1" rowspan=2 width="10%" style="border: 1px solid; border-color:black; border-collapse: collapse;">Owner</th>', file=f)
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


    for deliverable in sorted(ipqc.ip.deliverables,  key=lambda j:keyorder_deliverable.index(j.status)):
        
        nb_checkers = deliverable_list[deliverable.name]['nb_na'] + deliverable_list[deliverable.name]['nb_warning'] + deliverable_list[deliverable.name]['nb_fatal'] + deliverable_list[deliverable.name]['nb_failed'] + deliverable_list[deliverable.name]['nb_passed']

        if not(filter_unneeded):
            nb_checkers = nb_checkers + deliverable_list[deliverable.name]['nb_unneeded']


        if (deliverable_list[deliverable.name]['existence'] != ''):
            text[deliverable.view] = text[deliverable.view] + '<tr style="text-align:center; font-family: arial, helvetica, sans-serif;">'
            text[deliverable.view] = text[deliverable.view] + '<td style="background-color: {};">{}</td>' .format(_MAP_VIEWS[deliverable.view]['color'], deliverable.name)
            text[deliverable.view] = text[deliverable.view] + '<td colspan=2 style="color: #FFFFFF; background-color: {};">{}</td>' .format(status_data[_FATAL]['color'], deliverable_list[deliverable.name]['existence'][5])
            text[deliverable.view] = text[deliverable.view] + '<td>{}</td>' .format(deliverable_list[deliverable.name]['nb_passed'])
            text[deliverable.view] = text[deliverable.view] + '<td>{}</td>' .format(deliverable_list[deliverable.name]['nb_warning'])
            text[deliverable.view] = text[deliverable.view] + '<td>{}</td>' .format(deliverable_list[deliverable.name]['nb_failed'])
            text[deliverable.view] = text[deliverable.view] + '<td style="color: #FFFFFF; background-color: {};">{}</td>' .format(status_data[_FATAL]['color'], deliverable_list[deliverable.name]['nb_fatal'])

            if not(filter_unneeded):
                text[deliverable.view] = text[deliverable.view] + '<td>{}</td>' .format(deliverable_list[deliverable.name]['nb_unneeded'])
            text[deliverable.view] = text[deliverable.view] + '<td>{}</td>' .format(deliverable_list[deliverable.name]['nb_na'])
            text[deliverable.view] = text[deliverable.view] + '<td>{}</td>' .format(nb_checkers)
            text[deliverable.view] = text[deliverable.view] + '<td style=\"background-color: {};\">{}</td>' .format(status_data[_NA]['color'], status_data[_NA]['message'])
            text[deliverable.view] = text[deliverable.view] + '</tr>'

        else:

            deliverable_report = ReportDeliverable(os.path.join(g_url_path, 'ipqc.html'), ipqc, deliverable.name, filter_status=filter_status)
            deliverable_report.generate()
                
            filename = 'ipqc.html'

            # For passed, passed with waivers, failed, fatal put a report link
            # For waived deliverables and not applicable milestone deliverable do not need report
#                    if (deliverable.status == _ALL_WAIVED) or (deliverable.status == _NA_MILESTONE) or (deliverable.is_unneeded == True):
            if (deliverable.status == _ALL_WAIVED) or (deliverable.status == _NA_MILESTONE):
                report_html = ''
            else:
                if ipqc.ip.is_immutable:
                    if (ipqc.requalify ==True):
                        (url_path, nfs_path) = (os.path.join(ipqc.ip.workdir, deliverable.name), os.path.join(ipqc.ip.workdir, deliverable.name))
                    elif deliverable.bom != '':
                        (url_path, nfs_path) = get_catalog_paths(ipqc.ip.name, ipqc.ip.bom, ipqc.ip.milestone, deliverable)
                    else:
                        (url_path, nfs_path) = (os.path.join(ipqc.ip.workdir, deliverable.name), os.path.join(ipqc.ip.workdir, deliverable.name))
                else:
                    (url_path, nfs_path) = (os.path.join(ipqc.ip.workdir, deliverable.name), os.path.join(ipqc.ip.workdir, deliverable.name))
                report_html = os.path.join(url_path, filename)

            uiDebug(">> report template view: {} {} {}" .format(deliverable, deliverable.name, deliverable.err))

            text[deliverable.view] = text[deliverable.view] + """<tr style=\"text-align:center; font-family: arial, helvetica, sans-serif;\">
                                        <td style=\"background-color: {};\">{}</td>
                            """ .format(_MAP_VIEWS[deliverable.view]['color'], deliverable.name)

            text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: #E0E0E0;\">{}</td>" .format(deliverables_description[deliverable.name.upper()])


            if (deliverable.status == _ALL_WAIVED) or (deliverable.status == _NA_MILESTONE) or (deliverable.is_unneeded == True):
                if deliverable.status == _ALL_WAIVED:
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\">{}</td>" .format(status_data[_ALL_WAIVED]['color'], status_data[_ALL_WAIVED]['message'])
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\">{}</td>"  .format(status_data[_NA]['color'], status_data[_NA]['message'])
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\">{}</td>"  .format(status_data[_NA]['color'], status_data[_NA]['message'])
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\">{}</td>"  .format(status_data[_NA]['color'], status_data[_NA]['message'])
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\">{}</td>"  .format(status_data[_NA]['color'], status_data[_NA]['message'])
                    if not(filter_unneeded):
                        text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\">{}</td>"  .format(status_data[_NA]['color'], status_data[_NA]['message'])
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\">{}</td>"  .format(status_data[_NA]['color'], status_data[_NA]['message'])
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\">{}</td>"  .format(status_data[_NA]['color'], status_data[_NA]['message'])
                    
                    reldoc_deliverable = ipqc.ip.get_deliverable_ipqc('reldoc')

                    if reldoc_deliverable != None:
                        owner = reldoc_deliverable.owner
                    else:
                        owner = deliverable.owner

                    if owner != '':
                        text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: #E0E0E0;\"><a href=\"mailto:{}@intel.com?subject=ipqc dashboard\">{}@intel.com</td>" .format(owner, owner)
                    else:
                        text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: #E0E0E0;\">{}</td>" .format(owner)

                elif deliverable.status == _NA_MILESTONE:
                    nb_col = 8 - len(filter_status)
                    text[deliverable.view] = text[deliverable.view] + "<td colspan={} style=\"background-color: {};\">{}</td>" .format(nb_col, status_data[_NA_MILESTONE]['color'], status_data[_NA_MILESTONE]['message'])
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\">{}</td>"  .format(status_data[_NA]['color'], status_data[_NA]['message'])

                elif deliverable.is_unneeded == True:
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\">{}</td>" .format(status_data[_UNNEEDED]['color'], _NOT_POR)
                    text[deliverable.view] = text[deliverable.view] + "<td>{}</td>"  .format(deliverable_list[deliverable.name]['nb_passed'])
                    text[deliverable.view] = text[deliverable.view] + "<td>{}</td>"  .format(deliverable_list[deliverable.name]['nb_warning'])
                    text[deliverable.view] = text[deliverable.view] + "<td>{}</td>"  .format(deliverable_list[deliverable.name]['nb_failed'])
                    text[deliverable.view] = text[deliverable.view] + "<td>{}</td>"  .format(deliverable_list[deliverable.name]['nb_fatal'])
                    if not(filter_unneeded):
                        text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\">{}</td>"  .format(status_data[_UNNEEDED]['color'], deliverable_list[deliverable.name]['nb_unneeded'])
                    text[deliverable.view] = text[deliverable.view] + "<td>{}</td>"  .format(deliverable_list[deliverable.name]['nb_na'])
                    text[deliverable.view] = text[deliverable.view] + "<td>{}</td>"  .format(nb_checkers)
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\">{}</td>"  .format(status_data[_NA]['color'], status_data[_NA]['message'])
    


            else:
                text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: #E0E0E0;\">{}</td>" .format(deliverable.bom)

                if deliverable_list[deliverable.name]['nb_passed'] == 0:
                    text[deliverable.view] = text[deliverable.view] + "<td>{}</td>"  .format(deliverable_list[deliverable.name]['nb_passed'])
                else:
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\"><a href={}>{}</td>"  .format(status_data[_PASSED]['color'], report_html, deliverable_list[deliverable.name]['nb_passed'])

                if deliverable_list[deliverable.name]['nb_warning'] == 0:
                    text[deliverable.view] = text[deliverable.view] + "<td>{}</td>"  .format(deliverable_list[deliverable.name]['nb_warning'])
                else:
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\"><a href={}>{}</td>"  .format(status_data[_WARNING]['color'], report_html, deliverable_list[deliverable.name]['nb_warning'])

                if deliverable_list[deliverable.name]['nb_failed'] == 0:
                    text[deliverable.view] = text[deliverable.view] + "<td>{}</td>"  .format(deliverable_list[deliverable.name]['nb_failed'])
                else:
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\"><a href={}>{}</td>"  .format(status_data[_FAILED]['color'], report_html, deliverable_list[deliverable.name]['nb_failed'])
    
                if deliverable_list[deliverable.name]['nb_fatal'] == 0:
                    text[deliverable.view] = text[deliverable.view] + "<td>{}</td>"  .format(deliverable_list[deliverable.name]['nb_fatal'])
                elif (deliverable.bom == ''):
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"color: #FFFFFF; background-color: {};\">{}</td>"  .format(status_data[_FATAL]['color'], deliverable_list[deliverable.name]['nb_fatal'])
                else:
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"color: #FFFFFF; background-color: {};\"><a href={} style=\"color: #FFFFFF;\">{}</td>"  .format(status_data[_FATAL]['color'], report_html, deliverable_list[deliverable.name]['nb_fatal'])

                if not(filter_unneeded):
                    if deliverable_list[deliverable.name]['nb_unneeded'] == 0:
                        text[deliverable.view] = text[deliverable.view] + "<td>{}</td>"  .format(deliverable_list[deliverable.name]['nb_unneeded'])
                    else:
                        text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\">{}</td>"  .format(status_data[_UNNEEDED]['color'], deliverable_list[deliverable.name]['nb_unneeded'])

                if deliverable_list[deliverable.name]['nb_na'] == 0:
                    text[deliverable.view] = text[deliverable.view] + "<td>{}</td>"  .format(deliverable_list[deliverable.name]['nb_na'])
                else:    
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: {};\">{}</td>"  .format(status_data[_NA]['color'], deliverable_list[deliverable.name]['nb_na'])
                
                text[deliverable.view] = text[deliverable.view] + "<td>{}</td>"  .format(nb_checkers)

                if deliverable.owner != '':
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: #E0E0E0;\"><a href=\"mailto:{}@intel.com?subject=ipqc dashboard\">{}@intel.com</a></td>" .format(deliverable.owner, deliverable.owner)
                else:
                    text[deliverable.view] = text[deliverable.view] + "<td style=\"background-color: #E0E0E0;\">{}</td>" .format(deliverable.owner)


            text[deliverable.view] = text[deliverable.view] + "</tr>"

        nb_passed   = nb_passed + deliverable_list[deliverable.name]['nb_passed']
        nb_warning  = nb_warning + deliverable_list[deliverable.name]['nb_warning']
        nb_failed   = nb_failed + deliverable_list[deliverable.name]['nb_failed']
        nb_fatal    = nb_fatal + deliverable_list[deliverable.name]['nb_fatal']
        nb_unneeded = nb_unneeded + deliverable_list[deliverable.name]['nb_unneeded']
        nb_na       = nb_na + deliverable_list[deliverable.name]['nb_na']

        score_views[deliverable.view] = dsum(score_views[deliverable.view], {_PASSED: deliverable_list[deliverable.name]['nb_passed'], _WARNING: deliverable_list[deliverable.name]['nb_warning'], _FAILED: deliverable_list[deliverable.name]['nb_failed'], _FATAL: deliverable_list[deliverable.name]['nb_fatal'], _UNNEEDED: deliverable_list[deliverable.name]['nb_unneeded'], _NA: deliverable_list[deliverable.name]['nb_na']})

    gran_total_view = 0

    for view, t in sorted(text.items(), key=lambda j:_VIEW_ORDER.index(j[0])):
        gran_total_view = gran_total_view + score_views[view][_PASSED] + score_views[view][_WARNING] + score_views[view][_FAILED] + score_views[view][_FATAL] + score_views[view][_NA]

        if not(filter_unneeded):
            gran_total_view = gran_total_view + score_views[view][_UNNEEDED]

    for view, t in sorted(text.items(), key=lambda j:_VIEW_ORDER.index(j[0])):

        total_view = score_views[view][_PASSED] + score_views[view][_WARNING] + score_views[view][_FAILED] + score_views[view][_FATAL] + score_views[view][_NA]

        if not(filter_unneeded):
            total_view = total_view + score_views[view][_UNNEEDED]

        print('<tr border="1" style="border: 1px solid; border-bottom: none; text-align: center; background-color:  {}; font-weight: bold; font-family: arial, helvetica, sans-serif;">' .format(_MAP_VIEWS[view]['color']), file=f)
        print('<th border="1" style="border: 1px solid; border-bottom: none; text-align: center; background-color:  {}; font-weight: bold; font-family: arial, helvetica, sans-serif;">{}</th>' .format(_MAP_VIEWS[view]['color'], _MAP_VIEWS[view]['name']), file=f)
        print('<th border="1" colspan=10 style="border: 1px solid; border-bottom: none; text-align: center; background-color:  {}; font-weight: bold; font-family: arial, helvetica, sans-serif;"></th>' .format(_MAP_VIEWS[view]['color']), file=f)
        print("</tr>", file=f)
        print('<tr border="1" style="border: 1px solid; border-top: none; text-align: center; background-color:  {}; font-weight: bold; font-family: arial, helvetica, sans-serif;">' .format(_MAP_VIEWS[view]['color']), file=f)
        print('<th border="1" style="border: 1px solid; border-top: none; text-align: center; background-color:  {}; font-weight: bold; font-family: arial, helvetica, sans-serif;">({})</th>' .format(_MAP_VIEWS[view]['color'], view), file=f)
        print('<th border="1" colspan=10 style="border: 1px solid; border-top: none; text-align: center; background-color:  {}; font-weight: bold; font-family: arial, helvetica, sans-serif;"></th>' .format(_MAP_VIEWS[view]['color']), file=f)
        print("</tr>", file=f)
        print(t, file=f)

        

        # total of passed, waived, failed, fatal, unneeded, na for view
        print('<tr style="background-color: {}; font-weight: bold; font-family: arial, helvetica, sans-serif;">' .format(_MAP_VIEWS[view]['color']), file=f)
        print('<th>Total</th>', file=f)
        print('<th></th>', file=f)
        print('<th></th>', file=f)
        print("<th>{}</th>" .format(score_views[view][_PASSED]), file=f)
        print("<th>{}</th>" .format(score_views[view][_WARNING]), file=f)
        print("<th>{}</th>" .format(score_views[view][_FAILED]), file=f)
        print("<th>{}</th>" .format(score_views[view][_FATAL]), file=f)

        if not(filter_unneeded):
            print("<th>{}</th>" .format(score_views[view][_UNNEEDED]), file=f)

        print("<th>{}</th>" .format(score_views[view][_NA]), file=f)
        print('<th>{}</th>' .format(total_view), file=f)
        print('<th></th>', file=f)
        print("</tr>", file=f)


        # percentage of passed, waived, failed, fatal, unneeded, na for view
        print("<tr style=\"background-color: {};font-weight: bold; font-family: arial, helvetica, sans-serif;\">" .format(_MAP_VIEWS[view]['color']), file=f)
        print('<th>Total %</th>', file=f)
        print('<th></th>', file=f)
        print('<th></th>', file=f)
        print("<th>{}%</th>" .format(score_views[view][_PASSED] if score_views[view][_PASSED]==0 else percentage(score_views[view][_PASSED], total_view)), file=f)
        print("<th>{}%</th>" .format(score_views[view][_WARNING] if score_views[view][_WARNING]==0 else percentage(score_views[view][_WARNING], total_view)), file=f)
        print("<th>{}%</th>" .format(score_views[view][_FAILED] if score_views[view][_FAILED]==0 else percentage(score_views[view][_FAILED], total_view)), file=f)
        print("<th>{}%</th>" .format(score_views[view][_FATAL] if score_views[view][_FATAL]==0 else percentage(score_views[view][_FATAL], total_view)), file=f)

        if not(filter_unneeded):
            print("<th>{}%</th>" .format(score_views[view][_UNNEEDED] if score_views[view][_UNNEEDED]==0 else percentage(score_views[view][_UNNEEDED], total_view)), file=f)

        print("<th>{}%</th>" .format(score_views[view][_NA] if score_views[view][_NA]==0 else percentage(score_views[view][_NA], total_view)), file=f)
        print('<th>{}%</th>' .format(total_view if total_view==0 else percentage(total_view, total_view)), file=f)
        print('<th></th>', file=f)
        print("</tr>", file=f)


    print('<tr style="background-color: #E0E0E0; font-weight: bold; font-family: arial, helvetica, sans-serif;">', file=f)
    print('<th colspan=11></th>', file=f)
    print('</tr>', file=f)

    total = nb_passed + nb_failed + nb_fatal + nb_warning + nb_unneeded + nb_na

    # total of passed, waived, failed, fatal, unneeded, na for top IP
    print("<tr style=\"background-color: #AAD4FF; font-weight: bold; font-family: arial, helvetica, sans-serif;\">", file=f)
    print('<th>Grand Total</th>', file=f)
    print('<th></th>', file=f)
    print('<th></th>', file=f)
    print("<th>{}</th>" .format(nb_passed), file=f)
    print("<th>{}</th>" .format(nb_warning), file=f)
    print("<th>{}</th>" .format(nb_failed), file=f)
    print("<th>{}</th>" .format(nb_fatal), file=f)

    if not(filter_unneeded):
        print("<th>{}</th>" .format(nb_unneeded), file=f)

    print("<th>{}</th>" .format(nb_na), file=f)
    print('<th>{}</th>' .format(total), file=f)
    print('<th></th>', file=f)
    print("</tr>", file=f)

    # percentage of passed, waived, failed, fatal, unneeded, na
    print("<tr style=\"background-color: #AAD4FF;font-weight: bold; font-family: arial, helvetica, sans-serif;\">", file=f)
    print('<th>Grand Total %</th>', file=f)
    print('<th></th>', file=f)
    print('<th></th>', file=f)
    print("<th>{}%</th>" .format(nb_passed if nb_passed==0 else percentage(nb_passed, total)), file=f)
    print("<th>{}%</th>" .format(nb_warning if nb_warning==0 else percentage(nb_warning, total)), file=f)
    print("<th>{}%</th>" .format(nb_failed if nb_failed==0 else percentage(nb_failed, total)), file=f)
    print("<th>{}%</th>" .format(nb_fatal if nb_fatal==0 else percentage(nb_fatal, total)), file=f)

    if not(filter_unneeded):
        print("<th>{}%</th>" .format(nb_unneeded if nb_unneeded==0 else percentage(nb_unneeded, total)), file=f)

    print("<th>{}%</th>" .format(nb_na if nb_na==0 else percentage(nb_na, total)), file=f)
    print('<th>{}%</th>' .format(total if total==0 else percentage(total, total)), file=f)
    print('<th></th>', file=f)
    print("</tr>", file=f)

    print("</table>", file=f)

    print("<br>", file=f)
    print("<br>", file=f)
