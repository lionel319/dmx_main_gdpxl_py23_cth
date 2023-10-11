#!/usr/bin/env python
""" log.py """
from __future__ import print_function
import os
import re
import shutil
from dmx.ipqclib.utils import file_accessible, load_logs

LOGS = load_logs()

def set_log(ipobj, cell, deliverable, checker):
    """ set_log function"""
    if LOGS == {}:
        return checker.logfile

    if not checker.wrapper_name in LOGS.keys() or not "Logs" in LOGS[checker.wrapper_name].keys():
        return checker.logfile

    data = LOGS[checker.wrapper_name]["Logs"].strip()
    data = data.splitlines()
    checker_logs = []

    for line in data:
        string = line.strip()
        string = re.sub('&wkspace_root;', ipobj.workspace.path, string)
        string = re.sub('&ip_name;', ipobj.name, string)
        string = re.sub('&cell_name;', cell.name, string)
        if file_accessible(string, os.R_OK):
            checker_logs.append(string)

    if checker_logs != []:
        logfile = checker.logfile + '.html'
        if checker.logfile == '':
            logfile = os.path.join(os.path.realpath(ipobj.output_dir),  deliverable.name, \
                                'ipqc_' + cell.name + '_' + checker.wrapper_name) + '.html'
        else:
            logfile = checker.logfile + '.html'

        with open(logfile, 'w') as fid:

            print("""<!DOCTYPE html>
                        <html>
                        <head>
                        <title>IPQC {} - logs</title>
                        </head>
                        <body>
                    """ .format(deliverable.name), file=fid)


            for log in checker_logs:

                if not file_accessible(log, os.F_OK):
                    continue

                if not cell.name in os.path.basename(log):
                    dst_log = "{}_{}_{}_{}" .format(cell.name, checker.flow, checker.subflow, \
                            os.path.basename(log))
                else:
                    dst_log = os.path.basename(log)

                shutil.copyfile(log, os.path.join(ipobj.workdir, deliverable.name, dst_log))
                print("<p><a href={} ; type=\"text/plain\">{}</a></p>" .format(dst_log, \
                        os.path.basename(log)), file=fid)
            print("<p><a href={} ; type=\"text/plain\">{}</a></p>" \
                    .format(os.path.basename(checker.logfile), os.path.basename(checker.logfile)), \
                    file=fid)

            print("""</body>
                    </html>
                """, file=fid)
    else:
      #  if checker.logfile == '':
      #      logfile = os.path.join(os.path.realpath(ipobj.output_dir),  deliverable.name, \
      #                          'ipqc_' + cell.name + '_' + checker.wrapper_name) + '.html'
     #   else:
        logfile = checker.logfile 


    return logfile
