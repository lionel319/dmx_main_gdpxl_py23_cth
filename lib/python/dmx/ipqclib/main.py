# -*- coding: utf-8 -*-
"""Main script for IPQC"""
# $Id: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/ipqclib/main.py#1 $
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/ipqclib/main.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Change: 7411538 $
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/ipqclib/main.py $
# $Revision: #1 $
# $Author: lionelta $
#
# Description: IPQC is a tool that automatically performs sanity checks on IPs deliverables for a
#   given milestone and IP type
import sys

# pylint: disable=line-too-long
# Print usage before import to speed up display
_USAGE = '''ipqc <sub-command> [<args>]

        The most commonly used IPQC sub-commands are:
            dry-run             --  preview to list which tests to run and which tests are up-to-date
            run-all (default)   --  executes checkers and generates dashboard
            ecosystem           --  generates a graph based on IP type/IP name with milestone information listing deliverables/checkers information
            ip-graph            --  generates a hierarchical graph based on IP name
            catalog             --  catalog utilities

        For sub-command help: ipqc <sub-command> -h

        You will find user documentation here: https://wiki.ith.intel.com/display/tdmaInfra/4.2+IPQC+-+IP+Quality+Checks --> 4.2.2 User Documentation
        '''
# pylint: enable=line-too-long

if (__name__ == "__main__") or (__name__ == "dmx.ipqclib.parse"):
    if (sys.argv[1:] == []) or (sys.argv[1] == '--help') or (sys.argv[1] == '-h') or \
                      (sys.argv[1] == 'help'):
        print(_USAGE) # pylint: disable=superfluous-parens
        sys.exit(0)

# Import modules are placed after help message otherwise it takes >7 seconds to display help
# pylint: disable=wrong-import-position
import os
import traceback
from tabulate import tabulate
from dmx.ipqclib.parser.parse import Parser

import dmx.ipqclib.options
from dmx.ipqclib.automain import automain
from dmx.ipqclib.log import uiInfo, uiWarning, uiError, uiCritical
from dmx.ipqclib.ipqcException import ipqcException, PermissionError, IniConfigCorrupted, \
         IPQCRunAllException, IPQCDryRunException
from dmx.ipqclib.utils import run, get_status_from_record, check_if_result_clean
from dmx.ipqclib.report.report import Report
from dmx.dmlib.dmError import dmError
from dmx.ipqclib.precheck import precheck
from dmx.ipqclib.sendmail import sendmail
from dmx.dmxlib.workspace import WorkspaceError
# pylint: enable=wrong-import-position

def run_ecosystem():
    """Execute ecosystem sub-command"""
    from dmx.ipqclib.ecosystem import Ecosystem
    ecosystem = Ecosystem(ip=_ARGS.ip, \
            project=_ARGS.project, \
            milestones=_ARGS.milestones, \
            milestone=_ARGS.milestone, \
            ip_type=_ARGS.ip_type, \
            checkers=_ARGS.checkers, \
            output_dir=_ARGS.output_dir, \
            view=_ARGS.view)

    output_file = ecosystem.get_ecosystem()
    uiInfo("pdfviewer {}" .format(output_file))
    os.system('pdfviewer {} &' .format(output_file))


def run_ip_graph(output_dir):
    """Execute ecosystem sub-command"""
    from dmx.ipqclib.ecosystem import get_ip_graph

    if not(isinstance(_ARGS.ip, list)) and (_ARGS.ip != None):
        if len(_ARGS.ip.split('@')) > 1:
            ip_name = _ARGS.ip.split('@')[0]
            g_bom = _ARGS.ip.split('@')[1]
        else:
            g_bom = None
            ip_name = _ARGS.ip

    output_file = get_ip_graph(ip_name, g_bom, output_dir)
    uiInfo("pdfviewer {}" .format(output_file))
    os.system('pdfviewer {} &' .format(output_file))

def run_setup(g_options):
    """Execute setup sub-command"""
    from dmx.ipqclib.ipqc import IPQC
    from dmx.ipqclib.ipqc_flow import FlowFlat
    orig = os.getcwd()

    try:
        ipqc = IPQC(_ARGS.milestone, \
                _ARGS.ip, \
                project=_ARGS.project, \
                cellname=_ARGS.cellname, \
                deliverables=_ARGS.deliverable, \
                mode=_ARGS.which, \
                output_dir=_ARGS.output_dir, \
                no_clientname=_ARGS.no_clientname, \
                requalify=_ARGS.requalify, \
                no_hierarchy=_ARGS.no_hierarchy, \
                top=True, checkin=_ARGS.checkin, \
                no_revert=_ARGS.no_revert, \
                exclude_ip=_ARGS.exclude_ip, \
                ciw=_ARGS.ciw, \
                report_template=_ARGS.report_template, \
                options=g_options \
                )

    except IniConfigCorrupted as err:
        raise IniConfigCorrupted(err)


    if (g_options[dmx.ipqclib.options.SYNC] is True) or (len(_ARGS.ip.split('@')) > 1):
        ipqc.workspace.sync_ipqc(sync_cache=ipqc.sync_cache, dmx_cfgfile=_ARGS.dmxcfgfile, \
                requalify=_ARGS.requalify)

    ipqc.init_ip()
    ipqc.add_files_not_in_depot()
    ipqc.checkout()
    os.chdir(ipqc.ip.workdir)

    if ipqc.ip.needs_execution:
        flow = FlowFlat(ipqc)
        flow.build()

    ipqc.revert()

    uiInfo("")
    os.chdir(orig)

def run_flow(ipqc):
    """Run checkers flow"""
    from dmx.ipqclib.ipqc_flow import FlowFlat

    if ipqc.ip.needs_execution:
        flow = FlowFlat(ipqc)
        flow.build()

        try:
            flow.run()
        except KeyboardInterrupt:
            cmd = 'arc job-cancel -r -f {}' .format(flow.jobid)
            uiWarning("Killing job {} and all its children" .format(flow.jobid))
            uiWarning("Running {}" .format(cmd))
            run(cmd)

            if _ARGS.no_revert != True:
                uiWarning("Reverting file(s)")
                ipqc.revert()

            raise KeyboardInterrupt
        except:
            raise
    else:
        # pylint: disable=line-too-long
        uiWarning("No tests to run. Check that you have no deliverable waived or if you are working on immutable config, use --requalify option")
        # pylint: enable=line-too-long

def run_revert(ipqc):
    """Files revertion"""
    if _ARGS.no_revert is True:
        pass
    elif _ARGS.checkin_only_pass is True:
        ipqc.check_in_only_pass()
        ipqc.revert()
    elif _ARGS.checkin is True:
        ipqc.check_in()
        ipqc.revert()
    else:
        ipqc.revert()


def run_run_all(g_options):
    #pylint: disable=line-too-long
    """Execute run-all sub-command
        1- Create IPQC object. If the dashboard is already cached and no requalify mode ignore steps
            2, 3, 4, 5, 6.
            If not cached, this step generates the data folder structure to store results.
        2- init_ip() function creates IP(s), Cell(s), Deliverable(s), Checker(s), Audit(s) objects
            See achitecture diagram - https://wiki.ith.intel.com/display/tdmaInfra/Architecture+Specification?src=contextnavpagetreemode
        3- Optional step. If --add-to-scm (bool) is invoked, check for files in manifest that are
            not in the SCM and add them.
        4- Checkout files to open files in writable mode. Write mode is mandatory for checkers to
            execute properly.
        5- Run flow - execute the checkers. This step generates a Python makefile executable.
            This executable contains the tasks to run. The checker tasks are submitteds on the
            compute farm. Wait until the flow is completed.
        6-  If user invoked --no-revert (bool), do nothing, aka let the files opened.
            If user invoked --checkin-only-on-pass, check-in data only for deliverables in pass or
            pass with waiver(s) status.
            If user invoked --check-in, check-in data.
            Else, revert the files.
        7- Generates the report.
    """
    #pylint: enable=line-too-long
    from dmx.ipqclib.ipqc import IPQC
    orig = os.getcwd()

    #######################################################################################
    ###                         Creating IPQC object.                                   ###
    ### This is the main object of this application. It contains all objects            ###
    ### defined in the UML diagram located at this URL.                                 ###
    ###                                                                                 ###
    #######################################################################################
    try:
        ipqc = IPQC(_ARGS.milestone, \
                _ARGS.ip, \
                project=_ARGS.project, \
                cellname=_ARGS.cellname, \
                deliverables=_ARGS.deliverable, \
                mode=_ARGS.which, \
                output_dir=_ARGS.output_dir, \
                no_clientname=_ARGS.no_clientname, \
                requalify=_ARGS.requalify, \
                no_hierarchy=_ARGS.no_hierarchy, \
                top=True, \
                checkin=_ARGS.checkin, \
                no_revert=_ARGS.no_revert, \
                exclude_ip=_ARGS.exclude_ip, \
                ciw=_ARGS.ciw, \
                report_template=_ARGS.report_template, \
                options=g_options\
            )


        #######################################################################################
        ###                           Data preparation                                      ###
        ### Generates IPQC environment in reldoc deliverable. Checker execution and all     ###
        ### data generated will be run and stored in this environment.                      ###
        ### Check-out manifest and audit files.                                             ###
        #######################################################################################
        if (ipqc.cache is True) and (ipqc.requalify is False):
            (results, report_url, report_nfs) = get_status_from_record(ipqc) # pylint: disable=unused-variable
        else:
            if (g_options[dmx.ipqclib.options.SYNC] is True) or (len(_ARGS.ip.split('@')) > 1):
                ipqc.workspace.sync_ipqc(sync_cache=ipqc.sync_cache, dmx_cfgfile=_ARGS.dmxcfgfile, \
                        requalify=_ARGS.requalify)

            ipqc.init_ip()

            # add files if not in depot and if option to add files is invoked
            if g_options[dmx.ipqclib.options.ADD_TO_SCM] is True:
                ipqc.add_files_not_in_depot()

            ipqc.checkout(checkin_only_pass=_ARGS.checkin_only_pass)
            os.chdir(ipqc.ip.workdir)


            #######################################################################################
            ###                         Running IPQC flow                                       ###
            #######################################################################################
            run_flow(ipqc)
            os.chdir(ipqc.workspace.path)


            ###################
            # Report generation
            ###################
            results = ipqc.dry_run()
            Report(ipqc.ip.name, _ARGS.output_format, ipqc=ipqc, \
                    report_template=_ARGS.report_template)
            report_url = ipqc.ip.report_url
            report_nfs = ipqc.ip.report_nfs

            run_revert(ipqc)
    

        # send report by mail if --sendmail invoked
        if _ARGS.sendmail:
            sendmail(report_nfs, _ARGS.ip, ipqc=ipqc, recipients=_ARGS.recipients, mode=_ARGS.which)


        uiInfo("")
        uiInfo("")
        uiInfo("Generating report ...")

        uiInfo('\n\n{}\n' .format(tabulate(results, \
                        headers=['Cell', 'Deliverable', 'Test', 'Status'], tablefmt='orgtbl')))

        uiInfo("")
        uiInfo("firefox {}" .format(report_url))
        uiInfo("")
    except IniConfigCorrupted as err:
        raise IniConfigCorrupted(err)
    except (ipqcException, dmError) as err:
        uiError(err)
        raise IPQCRunAllException(err)
    except WorkspaceError as err:
        uiCritical(err)
    except Exception as err:
        uiWarning("Reverting file(s)")
        #traceback.print_exc()
        #template = "An exception of type {0} occurred. Arguments:\n"
        #message = template.format(type(err).__name__, err.args)
        ipqc.revert()
        raise
        raise IPQCRunAllException(err)

    os.chdir(orig)

def run_dry_run(g_options):
    """Execute dry-run sub-command"""
    from dmx.ipqclib.ipqc import IPQC
    ret = 0
    orig = os.getcwd()

    try:
        ipqc = IPQC(_ARGS.milestone, \
                _ARGS.ip, \
                project=_ARGS.project, \
                cellname=_ARGS.cellname, \
                deliverables=_ARGS.deliverable, \
                mode=_ARGS.which, \
                requalify=_ARGS.requalify, \
                no_clientname=_ARGS.no_clientname, \
                no_hierarchy=_ARGS.no_hierarchy, \
                output_dir=_ARGS.output_dir, \
                top=True, \
                report_template=_ARGS.report_template, \
                ip_filter=_ARGS.ip_filter, \
                options=g_options \
            )

    except dmError as err:
        uiError(err)
        raise ipqcException(err)
    except ipqcException as err:
        uiError(err)
        raise ipqcException(err)

    if (ipqc.cache is True) and (ipqc.requalify is False):
        (results, report_url, report_nfs) = get_status_from_record(ipqc)
    else:
        ipqc.init_ip()
        results = ipqc.dry_run()
        Report(ipqc.ip.name, _ARGS.output_format, ipqc=ipqc, \
                report_template=_ARGS.report_template, filter_status=_ARGS.filter_status)
        report_url = ipqc.ip.report_url
        report_nfs = ipqc.ip.report_nfs
        ret = check_if_result_clean(results)

    uiInfo('\n\n{}\n' .format(tabulate(results, \
                    headers=['Cell', 'Deliverable', 'Test', 'Status'], tablefmt='orgtbl')))

    uiInfo("")
    uiInfo("firefox {}" .format(report_url))
    uiInfo("")

    # send report by mail if --sendmail invoked
    if _ARGS.sendmail:
        sendmail(report_nfs, _ARGS.ip, ipqc=ipqc, recipients=_ARGS.recipients, mode=_ARGS.which)

    os.chdir(orig)
    return ret

def run_catalog():
    """Execute catalog sub-command"""
    from dmx.ipqclib.catalog.catalog import Catalog

    try:
        catalog = Catalog(_ARGS.family, ips=_ARGS.ip)
    except AssertionError as error:
        uiCritical(error)

    # 1/ Update ipqc.releases with the new ICM releases.
    # 2/ Run IPQC dry-run
    #    --> send an email if dry-run failed
    # 3/ Update ipqc.release_catalog
    if _ARGS.update_releases_db is True:
        catalog.update_releases_db(preview=_ARGS.preview)

    if _ARGS.update_catalog_db is True:
        catalog.update_db_missing_ipqc_releases(preview=_ARGS.preview)

    if _ARGS.generate_dashboard is True:
        catalog.update_releases_db(preview=_ARGS.preview)
        catalog.generate_dashboard(preview=_ARGS.preview)
        catalog.update_db_missing_ipqc_releases(preview=_ARGS.preview)
        catalog.push_in_catalog(preview=_ARGS.preview)

    if _ARGS.push_in_catalog is True:
        catalog.push_in_catalog(preview=_ARGS.preview)

    if _ARGS.db_equivalency_check is True:
        catalog.releases_db_equivalency_check()

    if _ARGS.get_releases is True:
        releases = catalog.get_releases_from_db()[0]
        header = releases[0].keys()
        rows = [x.values() for x in releases]
        uiInfo('\n{}' .format(tabulate(rows, headers=header, tablefmt='psql')))

    if _ARGS.get_catalog_releases is True:
        releases = catalog.get_releases_from_db()[1]
        header = releases[0].keys()
        rows = [x.values() for x in releases]
        uiInfo('\n{}' .format(tabulate(rows, headers=header, tablefmt='psql')))

@automain
@precheck
def main(args): # pylint: disable=unused-argument
    """Main script for IPQC"""

    g_options = dmx.ipqclib.options.LIST_OF_OPTIONS


    #######################################################################################
    ###                                 Ecosystem.                                      ###
    ### Generates graph containing deliverables dependancies, milestone, checkers.      ###
    #######################################################################################
    if _ARGS.which == 'ecosystem':
        run_ecosystem()


    #######################################################################################
    ###                                 IP-graph.                                       ###
    ### Generates graph containing IP hierarchy.                                        ###
    #######################################################################################
    if _ARGS.which == 'ip-graph':
        run_ip_graph(_ARGS.output_dir)


    #######################################################################################
    ###                                 Dry-run.                                        ###
    ### Preview to list which tests to run and which tests are up-to-date.              ###
    #######################################################################################
    if _ARGS.which == 'dry-run':

        g_options[dmx.ipqclib.options.SENDMAIL] = _ARGS.sendmail
        g_options[dmx.ipqclib.options.WORKSPACE_TYPE] = _ARGS.workspace_type
        g_options[dmx.ipqclib.options.FILTER_STATUS] = _ARGS.filter_status

        ret = run_dry_run(g_options)
        return ret
    #######################################################################################
    ###                         Build IPQC environment.                                 ###
    ### Invoking setup command will clean the environment and rebuild it from scratch.  ###
    ### All the information related to the previous run will be lost.                   ###
    #######################################################################################
    if _ARGS.which == 'setup':

        g_options[dmx.ipqclib.options.INITFILE] = _ARGS.initfile
        g_options[dmx.ipqclib.options.SENDMAIL] = _ARGS.sendmail
        g_options[dmx.ipqclib.options.WORKSPACE_TYPE] = _ARGS.workspace_type
        g_options[dmx.ipqclib.options.FILTER_STATUS] = _ARGS.filter_status
        g_options[dmx.ipqclib.options.SYNC] = _ARGS.sync
        g_options[dmx.ipqclib.options.FLOW] = _ARGS.flow
        g_options[dmx.ipqclib.options.ADD_TO_SCM] = _ARGS.add_to_scm

        run_setup(g_options)




    #######################################################################################
    ###                                     run-all                                     ###
    #######################################################################################
    if _ARGS.which == 'run-all':

        g_options[dmx.ipqclib.options.INITFILE] = _ARGS.initfile
        g_options[dmx.ipqclib.options.SENDMAIL] = _ARGS.sendmail
        g_options[dmx.ipqclib.options.WORKSPACE_TYPE] = _ARGS.workspace_type
        g_options[dmx.ipqclib.options.FILTER_STATUS] = _ARGS.filter_status
        g_options[dmx.ipqclib.options.SYNC] = _ARGS.sync
        g_options[dmx.ipqclib.options.FLOW] = _ARGS.flow
        g_options[dmx.ipqclib.options.ADD_TO_SCM] = _ARGS.add_to_scm

        run_run_all(g_options)



    #######################################################################################
    ###                                     catalog                                     ###
    #######################################################################################
    if _ARGS.which == 'catalog':
        run_catalog()

    return 0


if __name__ == '__main__':

    try:

        #######################################################################
        # Get options from the parser
        #######################################################################
        _ARGS = Parser().args

        if _ARGS.output_dir != None:
            _ARGS.output_dir = os.path.realpath(_ARGS.output_dir)


        sys.exit(main(_ARGS))

    except ipqcException as err:
        # In case of error always send an HTML report
        uiError(err)
        _REPORT = Report(_ARGS.ip.split('@')[0], 'html', msg=err)
        _REPORT.mail(_ARGS.ip, recipients=_ARGS.recipients)
        # pylint: disable=line-too-long
        uiCritical('IPQC encounters errors and cannot be executed properly. Check the errors and take action.')
        # pylint: enable=line-too-long
    except PermissionError as err:
        uiError(err)
        sys.exit(1)
    except IniConfigCorrupted as err:
        uiError(err)
        sys.exit(1)
    except AttributeError as err:
        traceback.print_exc()
        uiError(err)
        sys.exit(1)
    except (IPQCRunAllException, IPQCDryRunException) as err:
        uiError(err)
        sys.exit(1)
#    except Exception as err:
#        uiError(err)
#
#        if _ARGS.debug is True:
#            traceback.print_exc()
#        template="An exception of type {0} occurred. Arguments:\n"
#        message=template.format(type(err).__name__,err._ARGS)
#        uiError(message)
#        sys.exit(1)
