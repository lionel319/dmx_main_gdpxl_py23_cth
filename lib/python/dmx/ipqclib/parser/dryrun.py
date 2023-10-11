#!/usr/bin/env python
""" Parser for dry-run sub-command"""
import argparse
from dmx.ipqclib.utils import get_milestones
from dmx.ipqclib.parser.utils import get_deliverables, is_valid_template_value, is_valid_file, \
         IP_DEMO, _FILTER_OPTIONS
from dmx.ipqclib.settings import _VIEW, _WORKSPACE_TYPE

def get_dryrun_parser(action, subparsers, group_mandatory, group_exclusive, group_optional):
    """ Create parser for dry-run sub-command"""
    dry_run = subparsers.add_parser(action, formatter_class=argparse.RawTextHelpFormatter, \
            description="Preview to list which tests to run and which tests are up-to-date", \
            add_help=False)

    # mandatory arguments
    group_mandatory[action] = dry_run.add_argument_group('mandatory arguments')
    group_mandatory[action].add_argument('-i', '--ip_name', dest='ip', action='store', \
            metavar='<ip_name>', required=True, help='IP name.')
    group_mandatory[action].add_argument('-m', '--milestone', dest='milestone', \
            action='store', choices=get_milestones(), required=True, metavar='<milestone>', \
            help='milestone name. Values = {}' .format(get_milestones()))

    # optional arguments
    group_optional[action] = dry_run.add_argument_group('optional arguments')
    group_optional[action].add_argument('-p', '--project_name', dest='project', action='store', \
            metavar='<project_name>', required=False, help='project name.')
    group_optional[action].add_argument('-c', '--cell_name', dest='cellname', action='store', \
            nargs='+', default=[], required=False, metavar='<cell_name>', help='topcell name.')
    group_optional[action].add_argument('-d', '--deliverable', dest='deliverable', \
            action='store', nargs='+', default=[], required=False, \
            metavar='<deliverable_name>', help='deliverable name.')
    group_optional[action].add_argument('--requalify', dest='requalify', action='store_true', \
            default=False, required=False, help='By default, for immutable deliverable BOM, \
            IPQC will not run the check. It assumes it has been run prvious release. \
            If --requalify is invoked, IPQC will run the check on immutable BOM')
    group_optional[action].add_argument('--arc-options', dest='arc_options', action='store', \
            default='', required=False, help='Options for ARC/LSF compute farm.')
    group_optional[action].add_argument('--no-clientname', dest='no_clientname', \
            action='store_true', default=False, required=False, \
            help="Don't include client name in workspace.")
    group_optional[action].add_argument('--output-format', dest='output_format', \
            action='store', choices=['html', 'json'], default='html', required=False, \
            help='format of ipqc report.')
    group_optional[action].add_argument('--report-template', dest='report_template', \
            action='store', type=is_valid_template_value, default=_VIEW, required=False, \
            help='template of ipqc report.\n\tview: report by view (front-end, back-end, \
            timing)\n \n\tfunctionality: report by block/IP function (cram, clock, ...)\n \
            \n\tsimple: --report-template simple#<digit> If <digit>=1 report IPa, IPb, IPc. \
            If no <digit> report all\n {}\n' .format(IP_DEMO))
    group_optional[action].add_argument('--sendmail', dest='sendmail', action='store_true', \
            default=False, required=False, help='send report by email at the end of the \
            execution.')
    group_optional[action].add_argument('--recipients', dest='recipients', action='store', \
            required=False, metavar='<recipients_file>', type=is_valid_file,\
            help="File containing list of recipient email the report is sent to (use one email \
            per line). --sendmail needs to be invoked\nExample: recipients.txt\n\n\t \
            chun.fui.tham@intel.com\n\ttara.clark@intel.com\n\tsophie.rabadan@intel.com\n")
    group_optional[action].add_argument('--workspace-type', dest='workspace_type', \
            action='store', metavar='<workspace_type>', default='icmanage', required=False, \
            choices=_WORKSPACE_TYPE, help='Specify the workspace type for IPQC to be able to \
            call the right functions. Values = {}' .format(_WORKSPACE_TYPE))
    group_optional[action].add_argument('--filter-status', dest='filter_status', \
            action='store', nargs='+', metavar='<filter_status>', default=[], required=False, \
            choices=_FILTER_OPTIONS, help='Specify the status you want to filter out in the \
            HTML report. Value = {}' .format(_FILTER_OPTIONS))

    # exclusive arguments
    group_exclusive[action] = {}
    group_exclusive[action]['no_hierarchy'] = dry_run.add_mutually_exclusive_group(\
            required=False)
    group_exclusive[action]['no_hierarchy'].add_argument('--no-hierarchy', \
            dest='no_hierarchy', action='store_true', default=False, required=False, \
            help='Tabulate the data for all topcells embedded in the top level configuration.')
    group_exclusive[action]['no_hierarchy'].add_argument('--ip-filter', dest='ip_filter', \
            action='store', nargs='+', required=False, default=[], help='Exclude IPs \
            specified in --exclude-ip from checker execution')

    return (dry_run, group_mandatory, group_exclusive, group_optional)
