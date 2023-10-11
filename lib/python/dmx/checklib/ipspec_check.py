import os
import argparse
import sys
import re
import csv
import itertools

from dmx.python_common.uiExecuteCommands import run_command, run
from dmx.python_common.uiScriptMain import automain
from dmx.python_common.uiPrintMessage import uiInfo, uiError
from dmx.dmxlib.workspace import Workspace
from dmx.abnrlib.icm import ICManageCLI

@automain
def main(debug=False, logfile=None):

    g_ip        = args.ip
    g_milestone = args.milestone
    deliverable = "ipspec"
    project     = ""
    bom         = ""
    variant     = ""
    ipspec_cfg  = ""
    
    ### Temporary additional options that are not necessary to run dmx workspace check
    thread      = os.getenv("DB_THREAD")

    ####  TO DO
    ws = Workspace(preview=False)
    properties = ws.get_workspace_attributes()
    project=properties['Project']
    variant=properties['Variant']
    bom=properties['Config']
    
    pattern = "(\S+)/{}@(\S+)" .format(re.escape(g_ip))
    (code, out) = run_command("dmx report content -p {} -i {} -b {} --ip-filter {}" .format(project, variant, bom, g_ip))
    out = out.strip('\n')

    match = re.search(pattern, out)
    if match != None:
        ip_project = match.group(1)
        ipspec_cfg = match.group(2)
    else:
        ip_project = out.split('/')[0]
        ipspec_cfg = out.split('@')[1]
                
    cmd = "dmx workspace check -p {} -i {} -b {} -m {} -t {} -d {}" .format(ip_project, g_ip, ipspec_cfg, g_milestone, thread, deliverable)

    uiInfo("Running {}" .format(cmd))
    code = run(cmd)

    if code != 0:
        sys.exit(code)

if __name__ == '__main__':

    # top-level parser
    parser = argparse.ArgumentParser(
        prog='ipspec_check',
        description='ipspec_check',
        add_help=False
    )

    parser.add_argument('-i', '--ip_name', dest='ip', action='store', required=True)
    parser.add_argument('-m', '--milestone', dest='milestone', action='store', required=True)
    parser.add_argument('--logfile', dest='logfile', action='store', metavar='<logfile_name>', required=False, help='Log file.')
    parser.add_argument('--debug', dest='debug', action='store_true', default=False, required=False)

    args = parser.parse_args()


    try:
        main(debug=args.debug, logfile=args.logfile)
        sys.exit(0)
    except NameError as err:
        uiError(err)
        sys.exit(1)
