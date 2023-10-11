#!/usr/bin/env python
from __future__ import print_function
import os
import json
from operator import attrgetter
from dmx.ipqclib.log import uiInfo, uiWarning, uiError, uiCritical, uiDebug
from dmx.ipqclib.report.html.report_deliverable import ReportDeliverable
from dmx.ipqclib.utils import get_catalog_paths, percentage, dsum, file_accessible
from dmx.ipqclib.settings import _PASSED, _FAILED, _FATAL, _FATAL_SYSTEM, _NA, _NA_ERROR, _WARNING, _ALL_WAIVED, _UNNEEDED, _NA_MILESTONE, _NOT_POR, \
    status_data, _DB_FAMILY, _REL, _SNAP, _DB_DEVICE, _DELIVERABLES_DESCRIPTION 
from dmx.ipqclib.report.html.report_functionality import ReportFunctionality
from dmx.ipqclib.report.html.report_deliverable_functionality import ReportDeliverableFunctionality
from dmx.ipqclib.report.html.utils import header, executive_summary, score_table, set_environment_info, set_general_info


def get_deliverable_score(deliverable_list, ipqc):
    for cell in ipqc.ip.topcells:

        for deliverable in cell.deliverables:

            (deliverable.nb_pass, deliverable.nb_fail, deliverable.nb_fatal, deliverable.nb_warning, deliverable.nb_unneeded, deliverable.nb_na) = deliverable.get_check_info()
                    
            if deliverable.name in deliverable_list.keys():
                deliverable_list[deliverable.name]['status'].append(deliverable.status)
                deliverable_list[deliverable.name]['nb_passed'] = deliverable_list[deliverable.name]['nb_passed'] + deliverable.nb_pass
                deliverable_list[deliverable.name]['nb_failed'] = deliverable_list[deliverable.name]['nb_failed'] + deliverable.nb_fail
                deliverable_list[deliverable.name]['nb_fatal'] = deliverable_list[deliverable.name]['nb_fatal'] + deliverable.nb_fatal
                deliverable_list[deliverable.name]['nb_warning'] = deliverable_list[deliverable.name]['nb_warning'] + deliverable.nb_warning
                deliverable_list[deliverable.name]['nb_unneeded'] = deliverable_list[deliverable.name]['nb_unneeded'] + deliverable.nb_unneeded
                deliverable_list[deliverable.name]['nb_na'] = deliverable_list[deliverable.name]['nb_na'] + deliverable.nb_na
                if (deliverable.deliverable_existence['unwaived'] != []) and  (deliverable_list[deliverable.name]['existence'] == ''):
#                   deliverable_list[deliverable.name]['existence'] = deliverable.deliverable_existence['unwaived'][0]
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

def set_report_template_simple(ipqc, url_path, depth):

    filename = 'ipqc_simple.html'
    filepath = os.path.join(ipqc.ip.workdir, filename)

    header(filepath, url_path)
    executive_summary(filepath, ipqc)
    score_table(filepath, ipqc, depth)
    set_environment_info(filepath, ipqc)
    set_general_info(filepath, ipqc)

    return
