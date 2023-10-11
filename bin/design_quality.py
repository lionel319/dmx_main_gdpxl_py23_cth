#!/usr/bin/env python

# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/bin/design_quality.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $
"""
| This is a program that will be ran as a daily cron as user:icetnr.
| Basically this is what the workflow looks like:-

* Read in a given `config file`_.
* for each of the items

  * cd /ice_da/tnr/nadder/design_quality/<project>/<variant>/
  * update workspace to its <project>/<variant>/<config>
  * sync workspace
  * for each of the libtypes and variants,

    * if it is a REL* config, extract the waived-errors count
    * if it is not a REL* config, run ``quick check``, and then get the waived-errors count

  * Log all these information into a splunk-like json event file

* Generate a html page for the results
* send out email notification of the run's summary

The plan is to have this cronjob installed in ``sj-ice-cron`` by user ``icetnr``.

There is a flexibility any user to set up a manual run for their own usage too.
https://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/HowToSetUpDesignQuality

For more info please visit Fogbugz :case:`335766` or http://pg-rdjira:8080/browse/DI-18


.. _workflow:

=================================
Design Quality Overview Workflow
=================================

.. image:: ../images/design_quality_workflow.PNG

.. _config file:

=========================
Config File Sample
=========================

::

    #thread   milestone  project   variant  config              notifylist.cfg(a config file that decides how notification works)
    ND5revA   4.0        Nadder    z1493a   dev                 /home/yltan/notify.cfg
    ND5revA   4.5        Nadder    z1493a   stable_45_config    /home/yltan/notify2.cfg
    ND5revA   5.0        Nadder    z1493a   stable50            /home/yltan/notify3.cfg


.. _notify cfg:

============================
Notify List Config File
============================

This is a configuration file that tells the system how email notification should be sent.
It controls which libtypes should be tabulated, and who should receive the email notification.
The format of the file looks like this::

    [RTL/Netlisting]
    libtypes: ipspec,complib,rtl,netlist,compchk,None
    users: yltan,xxx

    [Phys/FullChip Physical Integration]
    libtypes: cdl,ipspec,laymisc,oa,oasis,pv,intfc,complib,complibphys,schmisc,upf,None
    users: yltan,xxx

    [Timing]
    libtypes: timemod,bcmrbc,ipspec,stamod,pnr,rcxt,rtl,None
    users: yltan,xxx

    [All]
    libtypes: all
    users: yltan,tylim,mkhitryk,alalin,wcleong,whchin

For more information, please see documentation for function `load_users_notify_file`.

.. _working dir:

============================
Working Directory Structure
============================

The directory structure of the ``--workdir=/a/b/design_quality/Nadder/z1493a`` looks like this::

    /a/b/design_quality/Nadder/z1493a/      # Root of the WORKING DIR
      thread/                               # eg:- ND5revA
        milestone/                          # eg:- 4.0
          icmworkspace/                     # The IC-Managed Workspace that populated the given project/variant/config
          results/                          # The placeholder dir that stores all the slunklog data
            20151123/...                    # The exact location that stores the splunklog data of the run for that day
            20151124/                       #    all the runs within the same timestamp/ folder should have the same id
              job.<id>.variant.libtype.splunklog # the splunklog data for all the jobs ran on the variant.libtype
              ... ... ... 
              unneeded.<id>.variant.libtype.splunklog   # the splunklog data that stores unneeded and needed libtypes for the variant.
          html/
            20151123.html                   # The generated job html results which is sent thru email notification
            20151124.html
            ... ... ...
      runner_splunklog/
        runner.<id>.splunklog           # The runner splunklog. 
        runner.<id>.splunklog   
        ... ... ...


| For the detail event's data of each splunklog, please refer to each of the individual functions
| - `gen_base_splunklog_dict`
| - `gen_runner_splunklog`
| - `gen_job_splunklog`
| - `gen_unneeded_and_needed_splunklog`



"""

### std libraries
import os
import sys
import logging
import argparse
from datetime import datetime
import time
import json
import xml.etree.ElementTree as ET
import ConfigParser
import csv


### in-house libraries
from altera.email import AlteraEmailer
from django.template import Context
from django.utils.safestring import mark_safe
from altera.decorators import memoized

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.dmlib.ICManageWorkspace import ICManageWorkspace
from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.utillib.utils import run_command
from dmx.tnrlib.dashboard_query2 import DashboardQuery2
from dmx.tnrlib.test_runner import TestRunner
from dmx.ecolib.ecosphere import EcoSphere
import dmx.abnrlib.flows.workspace


### Global Varianbles
LOGGER = logging.getLogger()
EXE = os.path.abspath(__file__)
WEBLIB = os.path.join(LIB, 'dmx', 'tnrlib')

### Change colors to mellower tone
### https://html-color.codes/hex/f8de7e
### http://pg-rdjira:8080/browse/DI-1391 (Phase #3)
COLOR = {
    'RED'       : '#ffb4b4',
    'GREEN'     : '#b4ffb4',
    'YELLOW'    : '#fcefbf',
    'GREY'      : '#d3d8dc',
}

def main():

    args = _add_args()
    _setup_logger(args)
    icm_pmlog_enable(mode=False)
    return args.func(args)


def work_area_preparation(args):
    '''
    Check and make sure that all the necessary `working dir`_ are ready before any runs.
    '''
    LOGGER.debug("Preparing Work Area ...")
    if args.dry:
        LOGGER.debug("dry mode: Work area preparation Done")
        return 0

    os.system("mkdir -p {}".format(get_icmws_dir(args.workdir, args.thread, args.milestone)))
    os.system("mkdir -p {}".format(get_job_results_dir(args.id, args.workdir, args.thread, args.milestone)))
    os.system("mkdir -p {}".format(get_runner_splunklog_dir(args.workdir)))
    os.system("mkdir -p {}".format(get_errors_dir(args.id, args.workdir, args.thread, args.milestone)))
    os.system("mkdir -p {}".format(os.path.dirname(get_job_html_filepath(args.id, args.workdir, args.thread, args.milestone))))

    os.system("mkdir -p {}".format(os.path.dirname(get_css_file(args.workdir))))
    os.system("cp -rf {} {}".format(os.path.join(WEBLIB, 'css', 'style.css'), get_css_file(args.workdir)))

    os.system("mkdir -p {}".format(get_js_dir(args.workdir)))
    for js in ['jquery-1.5.1.min.js', 'jquery.freezeheader.js']:
        os.system("cp -rf {} {}".format(
            os.path.join(WEBLIB, 'javascript', js), 
            os.path.join(get_js_dir(args.workdir), js)))

    LOGGER.debug("Work Area Preparation Done.")

def get_js_dir(workdir):
    '''
    Returns the js full path.
    '''
    return os.path.join(os.path.abspath(workdir), 'javascript')

def get_css_file(workdir):
    '''
    Returns the css style full path.
    '''
    return os.path.join(os.path.abspath(workdir), 'css', 'style.css')

def get_icmws_dir(workdir, thread, milestone, wsrun=False):
    ''' 
    Returns the directory of the icmanage workspace.
    For more info, see `working dir`_
    '''
    if wsrun:
        return workdir
    return os.path.join(os.path.abspath(workdir), thread, milestone, 'icmworkspace')

def get_job_results_dir(id, workdir, thread, milestone):
    '''
    Returns the directory that stores all the job splunklogs.
    For more info, see `working dir`_
    '''
    yyyymmdd = get_yyyymmdd_from_id(id)
    return os.path.join(os.path.abspath(workdir), thread, milestone, 'results', yyyymmdd)

def get_errors_dir(id, workdir, thread, milestone):
    '''
    Returns the directory that stores all the checker errors .
    '''
    yyyymmdd = get_yyyymmdd_from_id(id)
    return os.path.join(os.path.abspath(workdir), thread, milestone, 'errors', yyyymmdd)

def get_consolidated_error_file(id, workdir, thread, milestone):
    errdir = get_errors_dir(id, workdir, thread, milestone)
    outcsv = 'consolidated.{}.csv'.format(id)
    return os.path.join(errdir, outcsv)


def get_runner_splunklog_dir(workdir):
    '''
    Returns the directory that stores all the runner splunklogs.
    For more info, see `working dir`_
    '''
    return os.path.join(os.path.abspath(workdir), 'runner_splunklog')

def get_job_html_filepath(id, workdir, thread, milestone):
    '''
    Returns the full path of the html file of the results of the run.
    For more info, see `working dir`_
    '''
    yyyymmdd = get_yyyymmdd_from_id(id)
    return os.path.join(os.path.abspath(workdir), thread, milestone, 'html', yyyymmdd+'.html')


def get_password():
    '''
    | Passing around password thru the command line is not a very wise idea (as
    | (as it will be publickly published when you do it thru ``arc submit``. :p )
    | So, to work around that, we get the password from ``/home/<user>/.password``
    | Please make sure this file is having a ``0700`` mode for security purposes. *DUH...*
    '''
    try:
        filename = '/home/{}/.password'.format(os.getenv("USER"))
        line = open(filename).read()
        return line.strip()
    except:
        return ''


def runsingle_action(args):
    '''
    | This function takes care of the entire run of a single given ``cfg``.
    | A ``cfg`` is the data of one of the single line from the `config file`_.
    | The things that this function does is:-

        * Make sure that all the needed directory structures are ready ( `work_area_preparation` )
        * Update and sync the ``.../design_quality/icmworkspace`` ( `update_and_sync_workspace` )
        * Generate all reports/status for all variants/libtypes ( `generate_reports_for_all` )

    '''
    work_area_preparation(args)
    if not args.wsrun:
        update_and_sync_workspace(args)
    generate_reports_for_all(args)


def generate_reports_for_all(args):
    '''
    | Run the jobs individually for each of the variants and libtypes.
    | It basically dispatch the job to ``design_quality.py genreport``
    | Please see `genreport_action` for more info.
    '''
    LOGGER.debug("Generating reports for all ...")
    drymode = ''
    if args.dry:
        drymode = '--dry'

    ccobj = ConfigFactory.create_from_icm(args.project, args.variant, args.config)
    for c in ccobj.flatten_tree():
        if c.is_composite():
            clibtype = 'None'
        else:
            clibtype = c.libtype
        LOGGER.debug("Generating single report for {}".format([c.project, c.variant, clibtype, c.config]))
        cmd = "arc submit name='{}/{}@{}' lsfq={} -- {} genreport --debug --project {} --variant {} --config {} --id '{}' --milestone {} --thread {} --workdir {} --lsfq {} {}".format(
            c.variant, clibtype, c.config, args.lsfq, EXE, c.project, c.variant, c.config, args.id, args.milestone, args.thread, args.workdir, args.lsfq, drymode)
        if not c.is_composite():
            cmd += ' --libtype {}'.format(c.libtype)

        if args.wsrun:
            cmd += ' --wsrun '
        os.system(cmd)


def genreport_action(args):
    '''
    Generate the splunklog report for a given pvlc.
      * If it is a released config, get the waivers/errors information from splunk dashboard
      * if it is not a released config, run ``quick check`` to get the waivers/errors info.
    '''
    if args.dry:
        LOGGER.debug("Dry run: sleeping for 10 sec, then return ...")
        time.sleep(10)
        return 0

    if args.config.startswith("REL"):
        error_count = '0'
        waiver_count = get_release_waiver_count(args.project, args.variant, args.libtype, args.config, '')
        chksum_waiver_count = get_release_checksum_waiver_count(args.project, args.variant, args.libtype, args.config)
        notrun_waiver_count = get_release_notrun_waiver_count(args.project, args.variant, args.libtype, args.config)
        output_link = get_release_link(args.project, args.variant, args.libtype, args.config)

        ### for http://pg-rdjira:8080/browse/DI-755
        errors = get_waived_errors_from_pvlc(args.project, args.variant, args.libtype, args.config)

    else:
        ### for http://pg-rdjira:8080/browse/DI-755
        ws = dmx.abnrlib.flows.workspace.Workspace()
        if not args.libtype:
            ws.check_action(args.project, args.variant, args.config, args.milestone, args.thread, nowarnings=True)
        else:
            ws.check_action(args.project, args.variant, args.config, args.milestone, args.thread, nowarnings=True, libtype=args.libtype)
        errors = []
        for err in ws.errors['waived']:
            errors.append([args.project, args.variant, args.libtype, args.config, err.flow, err.subflow, err.error, 'yes'])
        for err in ws.errors['unwaived']:
            errors.append([args.project, args.variant, args.libtype, args.config, err.flow, err.subflow, err.error, 'no'])
        output_file = os.path.join(os.getenv("ARC_JOB_STORAGE"), 'stderr.txt')
        output_link = 'https://' + os.getenv("ARC_BROWSE_HOST") + output_file
        error_count, chksum_waiver_count, notrun_waiver_count = parse_quick_check_output(output_file)
        waiver_count = '0'


    LOGGER.debug("errors:{}".format(errors))
    if errors:
        gen_errors_file(args.id, args.workdir, args.project, args.variant, args.libtype, args.config, args.milestone, args.thread, errors)

    ### Get the number of topcells listed in the unneeded_deliverables.
    unneeded_topcell_count = 0
    if args.libtype:
        unneeded_deliverables = get_unneeded_deliverables(args.workdir, args.project, args.variant, args.libtype, args.config, args.milestone, args.thread, args.wsrun)
        unneeded_topcell_count = len(get_unneeded_topcell_for_libtype(unneeded_deliverables, args.libtype))

    gen_job_splunklog(args.id, args.workdir, args.project, args.variant, args.libtype, args.config, args.milestone, args.thread, 
        error_count, waiver_count, chksum_waiver_count, notrun_waiver_count, output_link, unneeded_topcell_count)

    if not args.libtype:
        unneeded_libtypes = get_unneeded_libtypes(args.workdir, args.project, args.variant, args.libtype, args.config, args.milestone, args.thread, args.wsrun)
        needed_libtypes = get_needed_libtypes(args.workdir, args.project, args.variant, args.libtype, args.config, args.milestone, args.thread)
        gen_unneeded_and_needed_splunklog(args.id, args.workdir, args.project, args.variant, args.libtype, args.config, args.milestone, args.thread, unneeded_libtypes, needed_libtypes)


    ### Purposely raise Traceback Error
    ### For Debugging Purpose 
    #os.chdir('/a/b/c')


def get_unneeded_topcell_for_libtype(unneeded_deliverables, libtype):
    '''
    Get the topcells that are unneeded from the ``unneeded_deliverables`` list.
    '''
    return [cell for (cell,lib) in unneeded_deliverables if lib == libtype]

def get_unneeded_deliverables(workdir, project, variant, libtype, config, milestone, thread, wsrun=False):
    '''
    return a ``list`` of ``tuple`` of 2 elements, which list the ``(topcell,libtype)`` which 
    are declared in unneeded_deliverable.txt file. The return data looks like this::

        [ ('topcell1', 'libtype1'), ('topcell2', 'libtype2'), ('ar_lib_top', 'upf'), ... ]
    
    '''
    wsroot = get_icmws_dir(workdir, thread, milestone, wsrun)
    tr = TestRunner(project, variant, libtype, config, wsroot, milestone, thread)
    ud = tr.get_unneeded_deliverables()
    return ud


def get_unneeded_libtypes(workdir, project, variant, libtype, config, milestone, thread, wsrun=False):
    ''' 
    return a ``list`` of libtypes whereby all the topcells listed in ``ipspec/cell_names.txt``
    have their corresponding libtype stated in their respective ``ipspec/<topcell>.unneeded_deliverables.txt``
    '''
    wsroot = get_icmws_dir(workdir, thread, milestone, wsrun)
    ud = get_unneeded_deliverables(workdir, project, variant, libtype, config, milestone, thread)
    tr = TestRunner(project, variant, libtype, config, wsroot, milestone, thread)
    return tr.get_libtype_where_all_topcells_unneeded(ud)


def get_needed_libtypes(workdir, project, variant, libtype, config, milestone, thread):
    ''' 
    return a ``list`` of libtypes that needs to be delivered by this variant.
    '''
    ''' Modify this for dmx compatible ...
    wsroot = get_icmws_dir(workdir, thread, milestone)
    tr = TestRunner(project, variant, libtype, config, wsroot, milestone, thread)
    return tr.get_required_libtypes()
    '''
    ret = EcoSphere().get_family_for_icmproject(project).get_ip(variant).get_all_deliverables(milestone=milestone)
    return [x.name for x in ret]


def parse_quick_check_output(outputfile):
    ''' 
    | Given the output file which has the output of ``quick check``, 
    | parse the file and return the ``[error_count, checksum_error_count, auditfile_notfound_count]``.
    | A sample of the output looks like this
    
    '''
    error_count = '0'
    notrun_waiver_count = 0
    chksum_waiver_count = 0

    error_syntax = 'ERRORS NOT WAIVED          : '
    notrun_syntax = 'Could not find any audit file'
    chksum_syntax1 = 'does not match audit requirement'
    chksum_syntax2 = 'can not access file'
    f = open(outputfile)
    for line in f:
        sline = line.strip()
        if 'DEBUG-' in sline:
            continue
        if sline.startswith(error_syntax):
            error_count = sline.lstrip(error_syntax)
            continue
        if notrun_syntax in sline:
            notrun_waiver_count += 1
            continue
        if chksum_syntax1 in sline:
            chksum_waiver_count += 1
            continue
        if chksum_syntax2 in sline:
            chksum_waiver_count += 1
            continue
    f.close()
    return [str(error_count), str(chksum_waiver_count), str(notrun_waiver_count)]


def update_and_sync_workspace(args):
    '''
    Update and Sync the ICM workspace
    If workspace is not an icm workspace, create it.
    '''
    LOGGER.debug("updating and syncing workpsace ...")
    if args.dry:
        LOGGER.debug("dry run: updating and syncing workspace done.")
        return 0

    icm = ICManageCLI()
    os.chdir( get_icmws_dir(args.workdir, args.thread, args.milestone) )
    try:
        icmws = ICManageWorkspace()
        wsname = icmws.workspaceName
        icm.update_workspace(wsname, args.config)
        LOGGER.debug("Workspace exists.")
    except:
        wsname = icm.add_workspace(args.project, args.variant, args.config, ignore_clientname=True)
        LOGGER.debug("Workspace does not exist. Creates a new one now.")
    icm.sync_workspace(wsname, skeleton=False, specs=['...'])
    LOGGER.debug("Workspace sync done.")


@memoized
def get_release_waiver_count(project, variant, libtype, config, errmsg):
    '''
    Query splunk dashboard to get the waived-errors count for the given project/variant/libtype/config.
    For variant level, use ``libtype="None"``.
    ``password`` is needed for splunk authentication during the query. If it is not supplied, by default,
    it will get it from the ``PASSWORD`` environment variable.

    '''
    '''
    d = DashboardQuery2('guest', 'guest')
    rid = get_request_id_from_pvlc(project, variant, libtype, config)
    if errmsg:
        search = 'search index=qa request_id={} status=waived error="{}" | stats count'.format(rid, errmsg)
    else:
        search = 'search index=qa request_id={} status=waived | stats count'.format(rid)

    ret = d.run_query(search)
    try:
        LOGGER.debug(ret)
        return ret[0]['count']
    except:
        return '0'
    '''
    LOGGER.debug("get_release_waiver_count({}, {}, {}, {}, {})".format(project, variant, libtype, config, errmsg))
    errors = get_waived_errors_from_pvlc(project, variant, libtype, config)
    ret = 0
    if errmsg:
        for e in errors:
            if errmsg.strip('*') in e[6]:
                ret += 1
    else:
        ret = len(errors)
    LOGGER.debug(">>> {}".format(ret))
    return ret


@memoized
def get_waived_errors_from_pvlc(project, variant, libtype, config):
    ''' Get all the waived errors for a given project/variant@config.
    Return it in a list-of-list:-
    [
        [project, variant, libtype, config, flow, subflow, error, 'yes'],
        ...   ...   ...
    ]
    '''
    d = DashboardQuery2('guest', 'guest')
    rid = get_request_id_from_pvlc(project, variant, libtype, config)
    search = 'search index=qa request_id={} status=waived | rename user as releaser | table project, variant, libtype, flow-topcell, flow-libtype, releaser, flow, subflow, waiver-creator, waiver-reason, error'.format(rid)    
    retlist = []
    ret = []
    result = d.run_query(search)
    for res in result:
        p = res['project']
        v = res['variant']
        b = res['libtype']
        t = res['flow-topcell']
        l = res['flow-libtype']
        r = res['releaser']
        f = res['flow']
        s = res['subflow']
        try:
            wc = res['waiver-creator']
        except:
            wc = ""
        try:            
            wr = res['waiver-reason']
        except:
            wr = ""
        e = res['error']
        retlist.append([p, v, b, t, l, r, f, s, wc, wr, e])
        ret.append([project, variant, libtype, config, f, s, e, 'yes'])

    return ret



def get_release_checksum_waiver_count(project, variant, libtype, config):
    '''
    Query splunk dashboard to get the waived-errors count for checksum errors
    '''
    ret = get_release_waiver_count(project, variant, libtype, config, '*does not match audit requirement*')
    ret += get_release_waiver_count(project, variant, libtype, config, '*can not access file*')
    return ret



def get_release_notrun_waiver_count(project, variant, libtype, config):
    '''
    Query splunk dashboard to get the waived-errors count for missing audit files errors
    '''
    return get_release_waiver_count(project, variant, libtype, config, '*Could not find any audit file*')


@memoized
def get_release_link(project, variant, libtype, config):
    ''' 
    Returns the release link for splunk dashboard.
    '''
    rid = get_request_id_from_pvlc(project, variant, libtype, config)
    return 'http://dashboard.altera.com:8080/en-US/app/tnr/release_request_detail?form.request_id={}&earliest=0&latest='.format(rid)


@memoized
def get_request_id_from_pvlc(project, variant, libtype, config):
    d = DashboardQuery2('guest', 'guest')
    rid = d.get_request_id_from_pvlc(project, variant, libtype, config)
    return rid


def wsrun_action(args):
    ''' 
    | This is the main parent function.
    |
    | This is exactly the same as the normal runner_action() run, except that:-
    | - this command is ran from an icm workspace root
    | - the workdir == icm workspace root
    | - the icmworkspace == icm workspace root
    
    '''

    try:
        icmws = ICManageWorkspace()
    except:
        LOGGER.error("The given value in --workspace is not a valid ICM Workspace!")
        LOGGER.error("- {}".format(args.workspace))
        raise
    cfgdata = [{
        'thread'    : args.thread,
        'milestone' : args.milestone,
        'project'   : args.project,
        'variant'   : args.variant,
        'config'    : args.config,
        'users'     : 'auto',
    }]
    args.workdir = icmws.path

    id = generate_unique_job_id()
    LOGGER.debug("id:{}".format(id))


    drymode = ''
    if args.dry:
        drymode = '--dry'
    
    os.system("mkdir -p {}".format(get_runner_splunklog_dir(args.workdir)))
    gen_runner_splunklog(id, args.workdir, cfgdata)
    
    singlerun_job_id_list = []
    for cfg in cfgdata:
        LOGGER.info("Running single job for {}".format(cfg))
        cmd = "arc submit name='{}/{}' lsfq={} -- {} runsingle --wsrun --debug --project {} --variant {} --config {} --id '{}'  --milestone {} --thread {} --workdir {} --lsfq {} {}".format(
            cfg['milestone'], cfg['thread'], args.lsfq, EXE, cfg['project'], cfg['variant'], cfg['config'], id, cfg['milestone'], cfg['thread'], args.workdir, args.lsfq, drymode)
        LOGGER.debug('- {}'.format(cmd))
        singlerun_job_id_list.append(run_arc_submit(cmd))

    ### Block it until all the children jobs are done.
    LOGGER.debug("Waiting for children jobs {} to complete ...".format(singlerun_job_id_list))
    for jobid in singlerun_job_id_list:
        os.system("arc wait {}".format(jobid))
    LOGGER.debug("All children jobs completed!")

    LOGGER.debug("Now we can start collecting all splunklog data and send notification ...")
    cmd = "{} notify --debug --workdir {} --id {}".format(EXE, args.workdir, id)
    LOGGER.debug('- {}'.format(cmd))
    os.system(cmd)

    if args.archivedir:
        LOGGER.debug("Archiving outputs ...")
        cmd = "{} archive --debug --workdir {} --archivedir {} --id latest --override".format(EXE, args.workdir, args.archivedir)
        LOGGER.debug('- {}'.format(cmd))
        os.system(cmd)



def runner_action(args):
    ''' 
    | This is the main parent function.
    | It is called by the daily cronjob.
    '''
    cfgdata = parse_config_file(args.cfgfile)
    LOGGER.debug("cfgdata:{}".format(cfgdata))
    
    id = generate_unique_job_id()
    LOGGER.debug("id:{}".format(id))


    drymode = ''
    if args.dry:
        drymode = '--dry'
    
    os.system("mkdir -p {}".format(get_runner_splunklog_dir(args.workdir)))
    gen_runner_splunklog(id, args.workdir, cfgdata)
    
    singlerun_job_id_list = []
    for cfg in cfgdata:
        LOGGER.info("Running single job for {}".format(cfg))
        cmd = "arc submit name='{}/{}' lsfq={} -- {} runsingle --debug --project {} --variant {} --config {} --id '{}'  --milestone {} --thread {} --workdir {} --lsfq {} {}".format(
            cfg['milestone'], cfg['thread'], args.lsfq, EXE, cfg['project'], cfg['variant'], cfg['config'], id, cfg['milestone'], cfg['thread'], args.workdir, args.lsfq, drymode)
        
        singlerun_job_id_list.append(run_arc_submit(cmd))

    ### Block it until all the children jobs are done.
    LOGGER.debug("Waiting for children jobs {} to complete ...".format(singlerun_job_id_list))
    for jobid in singlerun_job_id_list:
        os.system("arc wait {}".format(jobid))
    LOGGER.debug("All children jobs completed!")

    LOGGER.debug("Now we can start collecting all splunklog data and send notification ...")
    os.system("{} notify --debug --workdir {} --id {}".format(EXE, args.workdir, id))


def load_users_notify_file(infile):
    '''
    | Load the list of users that should be notified based on a preselected libtypes.
    | If infile == 'auto', then it will automatically generate a dict with 
    |      libtype = ['all']
    |      users = [$USER]
    |
    | Example of ``infile`` 
    
    ::

        [RTL/Netlisting]
        libtypes: ipspec,complib,rtl,netlist,None
        users: yltan,killim

        [Phys/FullChip Physical Integration]
        libtypes: cdl,ipspec,laymisc,oa,oasis,pv,intfc,complib,complibphys,schmisc,upf,None
        users: yltan,kwlim

        [Timing]
        libtypes: timemod,bcmrbc,ipspec,stamod,pnr,rcxt,rtl,None
        users: yltan,cftham

    | ``None`` can be specified in ``libtypes:`` to denote variant column.
    | ``all`` can be specified in ``libtypes:`` to display all available columns of libtypes.

    | Example of returned ``dict`` 
    
    ::

        {
            'RTL/Netlisting': {
                'libtypes': ['ipspec', 'complib', 'rtl', 'netlist', 'None'],
                'users': ['yltan', 'killim'],
            },
            'Phys/FullChip Physical Integration': {
                ...   ...   ...
            },
            ...   ...   ...
        }

    '''
    if infile == 'auto':
        LOGGER.info("Auto Notify List Activated ...")
        retval = {
            'Auto Generated': {
                'libtypes'  : ['all'],
                'users'     : ['design_quality'],
            }
        }
        return retval


    retval = {}
    config = ConfigParser.RawConfigParser()
    config.read(infile)
    for sec in config.sections():
        retval[sec] = {}
        for opt in ['libtypes', 'users']:
            retval[sec][opt] = config.get(sec, opt).strip().split(',')
    return retval
        

def look_for_problemetic_jobs(parent_jobid):
    '''
    Crawl thru all children arc job stderr.txt and return the jobs that did not complete successfully.
    retlist = [
        [jobid, jobname]
        [jobid, jobname]
        ...   ...   ...
    ]
    '''
    errjobs = []
    
    (parent_exitcode, parent_stdout, parent_stderr) = run_command('arc job-query parent={}'.format(parent_jobid))
    for parent_jobid in parent_stdout.split():

        (exitcode, stdout, stderr) = run_command('arc job-query parent={}'.format(parent_jobid))
        for i,jobid in enumerate(stdout.split()):
            job_name, job_storage = run_command('arc job --csv {} name storage'.format(jobid))[1].strip().split(',')
            job_errfile = "{}/stderr.txt".format(job_storage)
            LOGGER.debug('{}: {} [{}] ...'.format(i, jobid, job_name))

            ### Grep exit code:-
            ### - 0 : found matching lines
            ### - 1 : no match found
            ### - 2 : file does not exist
            (exitcode, stdout, stderr) = run_command('grep "^Traceback" {}'.format(job_errfile))
            if exitcode != 1:
                errjobs.append([jobid, job_name])

    return errjobs


def notify_action(args):
    ''' 
    | Collect all the data from job.*.splunklog from the given ``id``,
    | and send out email notification for each ``thread/milestone``
    '''
    workdir = args.workdir
    id = args.id

    runner_splunklog = get_runner_splunklog_filepath(workdir, id)
    f = open(runner_splunklog)
    for line in f:
        data = {}       # dict that stores all the job's info
        unneeded = {}   # dict that stores all the unneeded libtypes 
        needed = {}     # dict that stores all the needed libtypes 
        libtypes = set()    # this variable is to store a distinct available libtypes.
        runnerdata = json.loads(line)
        LOGGER.debug("Runnerdata: {}".format(runnerdata))

        ### load in the list of users to be notified
        notify_dict = load_users_notify_file(runnerdata['users'])
        LOGGER.debug("Notify Dict: {}".format(notify_dict))


        dir = get_job_results_dir(id, workdir, runnerdata['thread'], runnerdata['milestone'])
        LOGGER.debug("dir:{}".format(dir))
        for slog in os.listdir(dir):

            ### Only process splunklog files with matching id
            if id not in slog:
                continue

            filename = os.path.join(dir, slog)
            if not os.path.isfile(filename):
                continue

            ### job splunklog file: job.desqual_ ..... 
            if 'job.desqual_' in filename:
                LOGGER.debug("Reading job splunklog {} ...".format(filename))
                try:
                    jobline = open(filename).read()
                    tmp = json.loads(jobline)
                    libtypes.add(tmp['libtype'])
                    if tmp['variant'] not in data:
                        data[tmp['variant']] = {}
                    data[tmp['variant']][tmp['libtype']] = {
                        'output_link': tmp['output_link'],
                        'waiver_count': tmp['waiver_count'],
                        'chksum_waiver_count': tmp['chksum_waiver_count'],
                        'notrun_waiver_count': tmp['notrun_waiver_count'],
                        'error_count': tmp['error_count'],
                        'unneeded_topcell_count': tmp['unneeded_topcell_count'],
                        'is_rel': 'yes' if tmp['config'].startswith("REL") else 'no',
                        'config': tmp['config'],
                        'project': tmp['project']
                    }
                except Exception as e:
                    LOGGER.error("- Problem reading job splunklog {} !!!".format(filename))
                    LOGGER.error(str(e))

            ### unneeded splunklog file: unneeded.desqual_ .....
            elif 'unneeded.desqual_' in filename:
                LOGGER.debug("Reading unneeded splunklog {} ...".format(filename))
                try:
                    f = open(filename)
                    for jobline in f:
                        tmp = json.loads(jobline)

                        ### Dict initialization
                        if tmp['variant'] not in unneeded:
                            unneeded[tmp['variant']] = []
                        if tmp['variant'] not in needed:
                            needed[tmp['variant']] = []

                        if 'unneeded' in tmp and tmp['unneeded']:
                            unneeded[tmp['variant']].append(tmp['unneeded'])
                        if 'needed' in tmp and tmp['needed']:
                            needed[tmp['variant']].append(tmp['needed'])
                            libtypes.add(tmp['needed'])
                    f.close()
                except Exception as e:
                    LOGGER.error("- Problem reading unneeded splunklog {} !!!".format(filename))
                    LOGGER.error(str(e))

        LOGGER.debug("=data= : {}".format(data))
        LOGGER.debug("=runnerdata= : {}".format(runnerdata))
        LOGGER.debug("=unneeded= : {}".format(unneeded))
        LOGGER.debug("=needed= : {}".format(needed))
        LOGGER.info(notify_dict)
        for section in notify_dict:

            LOGGER.info("Completed reading all splunklog data. Generating html now for category: {} ...".format(section))

            interested_libtypes = list(notify_dict[section]['libtypes'])
            if 'all' in interested_libtypes:
                libtypes = list(libtypes)
            else:
                libtypes = interested_libtypes
            libtypes.sort()
            users = ','.join(notify_dict[section]['users'])

            xmlroot = ET.fromstring('<html><head></head><body></body></html>')
            body = xmlroot.find('./body')

            ### Adding title
            h1 = ET.SubElement(body, 'h1')
            title = 'Design Quality for {} {}/{} ({})'.format(runnerdata['topvariant'], runnerdata['thread'], runnerdata['milestone'], get_yyyymmdd_from_id(id))
            h1.text = title
            h3 = ET.SubElement(body, 'h3')
            h3.text = '- {}/{}@{}'.format(runnerdata['topproject'], runnerdata['topvariant'], runnerdata['topconfig'])

            ### Adding css stylesheet
            head = xmlroot.find('./head')
            link = ET.SubElement(head, 'link')
            link.set('href', '../../../css/style.css')
            link.set('rel', 'stylesheet')
            link.set('type', 'text/css')

            ### Adding javascripts
            sc = ET.SubElement(head, 'script')
            sc.set('type', 'text/javascript')
            sc.set('src', '../../../javascript/jquery-1.5.1.min.js')
            sc = ET.SubElement(head, 'script')
            sc.set('type', 'text/javascript')
            sc.set('src', '../../../javascript/jquery.freezeheader.js')
            sc = ET.SubElement(head, 'script')
            sc.set('type', 'text/javascript')
            sc.text = '$(document).ready(function(){  $("table").freezeHeader({ top: true, left: true }); });'
            sc = ET.SubElement(head, 'script')
            sc.set('type', 'text/javascript')
            sc.set('src', '../../../javascript/design_quality.js')



            ### Create Legend table
            LOGGER.info("- creating elementtree for Legend table ...")
            u = ET.SubElement(body, 'u')
            u.text = 'LEGEND'
            table = ET.SubElement(body, 'table')
            table.set('border', '1')
            tr = ET.SubElement(table, 'tr')
            td = ET.SubElement(tr, 'td')
            td.text = '    '
            td.set('bgcolor', COLOR['GREEN'])
            td = ET.SubElement(tr, 'td')
            td.text = 'Released successfully (numbers indicate waivers taken)'
            tr = ET.SubElement(table, 'tr')
            td = ET.SubElement(tr, 'td')
            td.text = '     '
            td.set('bgcolor', COLOR['RED'])
            td = ET.SubElement(tr, 'td')
            td.text = 'Not released (numbers you see are output from "quick check")'
            tr = ET.SubElement(table, 'tr')
            td = ET.SubElement(tr, 'td')
            td.text = 'N/A'
            td.set('bgcolor', COLOR['RED'])
            td = ET.SubElement(tr, 'td')
            td.text = 'Required libtype not found'

            # http://pg-rdjira:8080/browse/DI-1391
            # Remove pink legend
            #tr = ET.SubElement(table, 'tr')
            #td = ET.SubElement(tr, 'td')
            #td.text = 'N/A'
            #td.set('bgcolor', 'pink')
            #td = ET.SubElement(tr, 'td')
            #td.text = 'Libtype listed in unneeded deliverable (when it is NOT required by the deliverable roadmap. Please fix IPSPEC)'

            # http://pg-rdjira:8080/browse/DI-1391
            # Remove yellow legend
            tr = ET.SubElement(table, 'tr')
            td = ET.SubElement(tr, 'td')
            td.text = 'N/A'
            td.set('bgcolor', COLOR['YELLOW'])
            td = ET.SubElement(tr, 'td')
            td.text = 'Libtype listed in unneeded deliverable (when it is required by the deliverable roadmap)'

            tr = ET.SubElement(table, 'tr')
            td = ET.SubElement(tr, 'td')
            td.text = 'N/A'
            td.set('bgcolor', COLOR['GREY'])
            td = ET.SubElement(tr, 'td')
            td.text = 'Not needed to be delivered (per the deliverable roadmap)'


            ### Newlines
            ET.SubElement(body, 'br')
            ET.SubElement(body, 'br')

            ### There are 4 tables that will be created
            ### 1. waivers (total waivers)
            ### 2. unneeded (total topcells in uneeded_deliverables.txt)
            ### 3. chksum (total chksum errors waived)
            ### 4. notrun (total checks not ran / missing audit files)
            TABLES = {
                'waivers': 'Variant release readiness dashboard',
                'unneeded': 'Number of topcells with unneeded deliverables',
                'chksum': 'Total number of checksum errors',
                'notrun': 'Total number of missing audit files (indicating checker not run)'
            }
            
            TABLEKEYS = ['unneeded', 'notrun', 'chksum', 'waivers']
            eco = dmx.ecolib.ecosphere.EcoSphere()
            unneeded_deliverables_name = {}
            for tablename in TABLEKEYS:

                ### Create Main Table 
                LOGGER.info("- creating elementtree for {} table ...".format(tablename))
                h2 = ET.SubElement(body, 'h2')

                # http://pg-rdjira:8080/browse/DI-1391 (Phase #2)
                # Removed 'Missing Audit' section (notrun) if it is a REL config
                if tablename == 'notrun' and runnerdata['topconfig'].startswith("REL"):
                    h2.text = 'Total number of missing audit files (This table is irrelevant for a Released configuration)'
                    continue


                h2.text = '{}'.format(TABLES[tablename])
                table = ET.SubElement(body, 'table')
                table.set('border', '1')
                thead = ET.SubElement(table, 'thead')
                tbody = ET.SubElement(table, 'tbody')
              
                ### 'unneeded' table do not have 'Variant' column
                if tablename == 'unneeded' and 'None' in libtypes:
                    libtypes.remove('None')
                elif tablename != 'unneeded' and 'None' not in libtypes:
                    libtypes.insert(0, 'None')

                ### - Adding libtypes header
                tr = ET.SubElement(thead, 'tr')
                th = ET.SubElement(tr, 'th')
                th.text = 'Variant name'
                for libtype in libtypes:
                    th = ET.SubElement(tr, 'th')
                    th.set('class', libtype)
                    th.text = libtype
                    if libtype == 'None':
                        th.text = 'Variant status'

                ### - Main Table content
                for variant in sorted(data.keys()):
                    tr = ET.SubElement(tbody, 'tr')
                    td = ET.SubElement(tr, 'td')
                    td.text = variant

                    ### http://pg-rdjira:8080/browse/DI-1391 (Phase #2)
                    ### Make unneeded_deliverables yellow color
                    if variant not in unneeded_deliverables_name:
                        family = eco.get_family_for_icmproject(data[variant]['None']['project'])
                        ip = family.get_ip(variant, project_filter=data[variant]['None']['project'])
                        ip_unneeded_deliverables = ip.get_unneeded_deliverables(local=False, bom='ipspec@{}'.format(data[variant]['ipspec']['config']))
                        unneeded_deliverables_name[variant] = [x.name for x in ip_unneeded_deliverables]
                        LOGGER.debug('ip_unneeded_deliverables({}:ipspec/{}): {}'.format(variant, data[variant]['ipspec']['config'], unneeded_deliverables_name[variant]))

                    for libtype in libtypes:
                        td = ET.SubElement(tr, 'td')
                        td.set('class', libtype)
                        if libtype in data[variant]:
                            a = ET.SubElement(td, 'a')
                            a.set('href', data[variant][libtype]['output_link'])
                            a.set('target', '_blank')
                            if data[variant][libtype]['is_rel'] == 'yes':
                                #a.text = '{}/{}'.format(data[variant][libtype]['waiver_count'], data[variant][libtype]['unneeded_topcell_count'])
                                #a.text += '({}/{})'.format(data[variant][libtype]['chksum_waiver_count'], data[variant][libtype]['notrun_waiver_count'])
                                if tablename == 'waivers':
                                    a.text = '{}'.format(data[variant][libtype]['waiver_count'])
                                elif tablename == 'unneeded':
                                    a.text = '{}'.format(data[variant][libtype]['unneeded_topcell_count'])
                                elif tablename == 'chksum':
                                    a.text = '{}'.format(data[variant][libtype]['chksum_waiver_count'])
                                elif tablename == 'notrun':
                                    a.text = '{}'.format(data[variant][libtype]['notrun_waiver_count'])


                                accepted = [0, '0']
                                if data[variant][libtype]['chksum_waiver_count'] in accepted and data[variant][libtype]['notrun_waiver_count'] in accepted and data[variant][libtype]['unneeded_topcell_count'] in accepted:
                                    td.set('bgcolor', COLOR['GREEN'])
                                else:
                                    td.set('bgcolor', COLOR['GREEN'])
                            else:
                                #a.text = '{}/{}'.format(data[variant][libtype]['error_count'], data[variant][libtype]['unneeded_topcell_count'])
                                #a.text += '({}/{})'.format(data[variant][libtype]['chksum_waiver_count'], data[variant][libtype]['notrun_waiver_count'])
                                if tablename == 'waivers':
                                    a.text = '{}'.format(data[variant][libtype]['error_count'])
                                elif tablename == 'unneeded':
                                    a.text = '{}'.format(data[variant][libtype]['unneeded_topcell_count'])
                                elif tablename == 'chksum':
                                    a.text = '{}'.format(data[variant][libtype]['chksum_waiver_count'])
                                elif tablename == 'notrun':
                                    a.text = '{}'.format(data[variant][libtype]['notrun_waiver_count'])


                                td.set('bgcolor', COLOR['RED'])
                        else:
                            td.text = 'N/A'
                            if variant in needed and libtype in needed[variant]:
                                #if libtype in unneeded[variant]:
                                if libtype in unneeded_deliverables_name[variant]:
                                    td.set('bgcolor', COLOR['YELLOW'])
                                else:
                                    td.set('bgcolor', COLOR['RED'])
                            else:
                                if variant in unneeded and libtype in unneeded[variant]:
                                    td.set('bgcolor', 'pink')
                                else:
                                    td.set('bgcolor', COLOR['GREY'])


                ET.SubElement(body, 'br')
                ET.SubElement(body, 'br')

            ### Libtype Filtering Feature
            ### http://pg-rdjira:8080/browse/DI-856
            i = ET.SubElement(body, 'i')
            i.text = '(key in libtypes column to hide, separated by comma, no space allowed)'
            ET.SubElement(body, 'br')
            a = ET.SubElement(body, 'input')
            a.set('id', 'libtype_filter')
            a.set('name', 'libtype_filter')
            a.set('type', 'text')
            a.set('size', '100%')
            ET.SubElement(body, 'br')
            a = ET.SubElement(body, 'button')
            a.set('id', 'hide')
            a.set('type', 'button')
            a.text = 'Hide'
            a = ET.SubElement(body, 'button')
            a.set('id', 'show')
            a.set('type', 'button')
            a.text = 'Show All'

            ET.SubElement(body, 'br')
            ET.SubElement(body, 'br')

            
            ### Add arc_job_id link
            LOGGER.info("- creating elementtree for arc job id ...")
            a = ET.SubElement(body, 'a')
            a.set('href', 'https://{}/arc/dashboard/reports/show_job/{}'.format(runnerdata['arc_browse_host'], runnerdata['arc_job_id']))
            a.set('target', '_blank')
            a.text = 'Arc Job Report'


            htmlstr = ''

            ### Check if all children jobs has completed successfully without raised errors.
            LOGGER.info("Checking if children jobs has completed successfully for arc_job_id {} ...".format(runnerdata['arc_job_id']))
            errjobs = look_for_problemetic_jobs(runnerdata['arc_job_id'])
            if errjobs:
                LOGGER.info("- Some children arc job did not complete successfully.")
                htmlstr += '<h2>Some children jobs did not complete successfully.</h2>'
                htmlstr += '<h3>You might need to rerun the job again.</h3>'
                htmlstr += 'Here are the list of children jobs that has problem:<br>'
                for jobid,jobname in errjobs:
                    htmlstr += "<a href={}>{}</a> - [{}] <br>".format(get_arc_job_dashboard_link(jobid), jobid, jobname)


            LOGGER.info("- sending email to users: {} ...".format(users))
            htmlstr += ET.tostring(xmlroot, method='html')
            htmlfile = get_job_html_filepath(id, workdir, runnerdata['thread'], runnerdata['milestone'])
            #ET.ElementTree(xmlroot).write(htmlfile, method="html")
            with open(htmlfile, 'w') as f:
                f.write(htmlstr)
            send_email(users, title, htmlstr)

            
            # http://pg-rdjira:8080/browse/DI-755
            errdir = get_errors_dir(id, workdir, runnerdata['thread'], runnerdata['milestone'])
            prefix = 'errors.{}.*'.format(id)
            outcsv = 'consolidated.{}.csv'.format(id)
            header = "project,variant,libtype,config,flow,subflow,error,waived"
            os.system("cd {}; echo '{}' > {}; cat {} >> {}".format(errdir, header, outcsv, prefix, outcsv))

    f.close()

def archive_action(args):
    '''
    | Archive all outputs from a given workdir/id to an archive area.
    | Currently only copy 2 files:-
    | - html (4 tables)
    | - consolidated errors (csv) file
    '''
    if args.id == 'latest':
        runner_splunklog = get_latest_runner_splunklog_filepath(args.workdir)
    else:
        runner_splunklog = get_runner_splunklog_filepath(args.workdir, args.id)
    f = open(runner_splunklog)
    for line in f:
        runnerdata = json.loads(line)
        LOGGER.debug("Runnerdata: {}".format(runnerdata))
        inhtmlfile = get_job_html_filepath(runnerdata['id'], args.workdir, runnerdata['thread'], runnerdata['milestone'])
        inerrfile = get_consolidated_error_file(runnerdata['id'], args.workdir, runnerdata['thread'], runnerdata['milestone'])
        outdir = os.path.abspath(args.archivedir)
        outhtmlfile = os.path.join(outdir, 'index.html')
        outerrfile = os.path.join(outdir, 'consolidated_errors.csv')

        if not args.override and (os.path.isfile(outhtmlfile) or os.path.isfile(outerrfile)):
            LOGGER.error("{} already contains output files, and --override is not turned on.")
            LOGGER.error("Skipping archive command.")
        else: 
            LOGGER.info("Archiving ... ")
            os.system('mkdir -p {}'.format(outdir))
            os.system('cp -rf {} {}'.format(inhtmlfile, outhtmlfile))
            #os.system('cp -rf {} {}'.format(inerrfile, outerrfile))    # https://jira01.devtools.intel.com/browse/PSGDMX-23
            LOGGER.info("- outputs from {} successfully archived to {}".format(args.workdir, outdir))


def get_arc_job_dashboard_link(jobid):
    return 'https://{}/arc/dashboard/reports/show_job/{}'.format(      
        os.getenv("ARC_BROWSE_HOST", "arc_browse_host_env_var_not_found"), jobid)


def send_email(recipients, subject, body):
    ''' Sends email to specified recipients with specified subject and body. '''
    EMAIL_TEMPLATES = os.path.join(WEBLIB, "email_templates")
    from_addr = 'desqual_noreply@altera.com'
    emailer = AlteraEmailer(EMAIL_TEMPLATES, from_addr)
    context = Context() 
    context['title'] = subject
    context['content'] = mark_safe(body)
    context['date'] = datetime.now()
    email = emailer.render_email_body("generic_email.html", context)
    email_list = []
    for user in recipients.split(','):
        email_list.append(user.strip() + '@altera.com')
    ret = emailer.send_email(email, subject, email_list, cc=None)
    return ret


def _add_args():
    ''' Parse the cmdline arguments '''
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers()

    parser_wsrun = subparser.add_parser('wsrun', help='Run design quality based on an icm-workspace.(This command needs to be run from an icm-workspace root)')
    parser_wsrun.add_argument('--dry', required=False, default=False, action='store_true', help="Dry run(for debugging and dev purpose)")
    parser_wsrun.add_argument('--debug', required=False, default=False, action='store_true', 
        help="Turn on debug mode (which will print out all the debugging strings when running.")
    parser_wsrun.add_argument('--milestone', required=True, help="The milestone.")
    parser_wsrun.add_argument('--thread', required=True, help="The thread.")
    parser_wsrun.add_argument('--project', required=True, help="The icm project.")
    parser_wsrun.add_argument('--variant', required=True, help="The icm variant.")
    parser_wsrun.add_argument('--config', required=True, help="The icm config.")
    parser_wsrun.add_argument('--lsfq', required=False, default='ice_arc_small', help="The lsfq that the job should be running at.")
    parser_wsrun.add_argument('--notify_off', required=False, action='store_true', help="Turn off email notification.")
    parser_wsrun.add_argument('--archivedir', required=False, help="If an archive dir is given, upon completion, output files will be copied over to the archive area.")
    parser_wsrun.set_defaults(func=wsrun_action)

    parser_runner = subparser.add_parser('runner', help='A runner job which is ran thru a daily cronjob that.')
    parser_runner.add_argument('--dry', required=False, default=False, action='store_true', help="Dry run(for debugging and dev purpose)")
    parser_runner.add_argument('--debug', required=False, default=False, action='store_true', 
        help="Turn on debug mode (which will print out all the debugging strings when running.")
    parser_runner.add_argument('--workdir', required=True, help="The root directory that runs all the daily cronjobs and stores all the results.")
    parser_runner.add_argument('--cfgfile', required=True, help="The configuration file for the Design Quality Runner.")
    parser_runner.add_argument('--lsfq', required=False, default='ice_arc_small', help="The lsfq that the job should be running at.")
    parser_runner.add_argument('--notify_off', required=False, action='store_true', help="Turn off email notification.")
    parser_runner.set_defaults(func=runner_action)

    parser_runsingle = subparser.add_parser('runsingle', help='Runs and generates report based on a given single pvc thread/milestone')
    parser_runsingle.add_argument('--dry', required=False, default=False, action='store_true', help="Dry run(for debugging and dev purpose)")
    parser_runsingle.add_argument('--debug', required=False, default=False, action='store_true', 
        help="Turn on debug mode (which will print out all the debugging strings when running.")
    parser_runsingle.add_argument('--workdir', required=True, help="The root directory that runs all the daily cronjobs and stores all the results.")
    parser_runsingle.add_argument('--project', required=True, help='The ICManage project name')
    parser_runsingle.add_argument('--variant', required=True, help='The ICManage variant name')
    parser_runsingle.add_argument('--config', required=True, help='The ICManage config name')
    parser_runsingle.add_argument('--thread', required=True, help='The thread (as stated in the cfgfile)')
    parser_runsingle.add_argument('--milestone', required=True, help='The milestone (as stated in the cfgfile)')
    parser_runsingle.add_argument('--id', required=True, help='Unique ID for runner job.')
    parser_runsingle.add_argument('--lsfq', required=False, default='ice_arc_small', help="The lsfq that the job should be running at.")
    parser_runsingle.add_argument('--wsrun', required=False, default=False, action='store_true', help="Notify that this job is a wsrun job.(ran from a workspace)")
    parser_runsingle.set_defaults(func=runsingle_action)

    parser_genreport = subparser.add_parser('genreport', help='''
        Generates the splunklog report.
        - if the given pvlc is a released configuration
          > run a dashboard query to get the waived-errors.
        - if the given pvlc is NOT a released configuration
          > run quick check and get the results. 
        ''')
    parser_genreport.add_argument('--dry', required=False, default=False, action='store_true', help="Dry run(for debugging and dev purpose)")
    parser_genreport.add_argument('--debug', required=False, default=False, action='store_true',
        help="Turn on debug mode (which will print out all the debugging strings when running.")
    parser_genreport.add_argument('--workdir', required=True, help="The root directory that runs all the daily cronjobs and stores all the results.")
    parser_genreport.add_argument('--project', required=True, help='The ICManage project name')
    parser_genreport.add_argument('--variant', required=True, help='The ICManage variant name')
    parser_genreport.add_argument('--libtype', required=False, help='The ICManage libtype name (Do not specify if it is a variant level)')
    parser_genreport.add_argument('--config', required=True, help='The ICManage config name')
    parser_genreport.add_argument('--thread', required=True, help='The thread (as stated in the cfgfile)')
    parser_genreport.add_argument('--milestone', required=True, help='The milestone (as stated in the cfgfile)')
    parser_genreport.add_argument('--id', required=True, help='Unique ID for runner job.')
    parser_genreport.add_argument('--lsfq', required=False, default='ice_arc_small', help="The lsfq that the job should be running at.")
    parser_genreport.add_argument('--wsrun', required=False, default=False, action='store_true', help="Notify that this job is a wsrun job.(ran from a workspace)")
    parser_genreport.set_defaults(func=genreport_action)

    parser_notify = subparser.add_parser('notify', help='Send notification of the results.')
    parser_notify.add_argument('--debug', required=False, default=False, action='store_true',
        help="Turn on debug mode (which will print out all the debugging strings when running.")
    parser_notify.add_argument('--workdir', required=True, help='The root directory that runs all the daily cronjobs and stores all the results.')
    parser_notify.add_argument('--id', required=True, help='Unique ID for runner job.')
    parser_notify.set_defaults(func=notify_action)

    parser_archive = subparser.add_parser('archive', help='Copy all outputs from a workdir/id to an archive area.')
    parser_archive.add_argument('--debug', required=False, default=False, action='store_true',
        help="Turn on debug mode (which will print out all the debugging strings when running.")
    parser_archive.add_argument('--workdir', required=True, help='The root directory that runs all the jobs and stores all the results.')
    parser_archive.add_argument('--archivedir', required=True, help='The root directory of the archive directory. The output files will be copied to here.')
    parser_archive.add_argument('--id', required=False, default='latest', help='Unique ID for runner job. If not given, will get the latest id from --workdir.')
    parser_archive.add_argument('--override', default=False, required=False, action='store_true', help='By default, will not override if files already exist in --archive area. Turning on this option will negate that.')
    parser_archive.set_defaults(func=archive_action)



    args = parser.parse_args()
    return args


def is_arc_job_running(arc_job_id):
    '''
    Given an arc job id, return ``True`` if it is still alive, else ``False``.
    '''
    exitcode, stdout, stderr = run_command('arc job {} status'.format(str(arc_job_id)))

    if not stdout.strip():
        return False
   
    status = stdout.split()[0].strip()
    if status == 'running' or status == 'queued':
        return True

    return False


def run_arc_submit(arc_submit_cmd):
    '''
    Runs the given ``arc_submit_cmd``, and return the arc job id.
    '''
    exitcode, stdout, stderr = run_command(arc_submit_cmd)
    if exitcode != 0:
        LOGGER.error("Error when running {}".format(arc_submit_cmd))
        LOGGER.error(_formatted_run_command_output(exitcode, stdout, stderr))
        return ''
    arc_job_id = stdout.split()[0].strip()
    return arc_job_id

def _formatted_run_command_output(exitcode, stdout, stderr):
    return """
        exitcode:{}
        stdout:{}
        stderr:{}
    """.format(exitcode, stdout, stderr)

def _setup_logger(args):
    ''' Setup the logging interface '''
    level = logging.INFO
    if 'debug' in args and args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
          

def generate_unique_job_id():
    '''
    | Generates a unique job id (basically for `splunklog` purpose)
    | id is in the following syntax

    ``desqual_<hostname>_<timestamp>``

    Example: ``desqual_pg-ice-nx16_2015-11-20_14:06:58.819831``

    '''
    host = os.getenv("HOST", '')
    timestamp = str(datetime.now())
    id = 'desqual_{}_{}'.format(host, timestamp.replace(' ', '_'))
    return id

def get_yyyymmdd_from_id(id):
    '''
    From the unique ``id`` generated by `generate_unique_job_id`, 
    return the timestamp in ``yyyymmdd`` format.

    '''
    splitted = id.split('_')
    return splitted[2].replace('-', '')


def parse_config_file(cfgfile):
    ''' 
    Parse the `config file`_.

    Returns a ``list`` of ``dict`` that looks like this::

        [
            {   'thread': 'ND5revA',    
                'milestone': '4.0',
                'project': 'Nadder',
                'variant': 'z1493a',
                'config': 'dev',
                'users': 'yltan,kwlim,wcleong',
            },
            { ...   ...   ... },
            ...   ...   ...
        ]

    '''
    retlist = []
    header = ['thread', 'milestone', 'project', 'variant', 'config', 'users']
    
    f = open(cfgfile)
    for line in f:
        sline = line.strip()

        # skip if line is commented
        if sline.startswith("#"):
            continue
        
        # skip if line is empty
        if not sline:
            continue
        
        # skip if line does not have 6 elements
        splitted = sline.split()
        if len(splitted) != len(header):
            LOGGER.warn("Line:{} does not have {} elements!".format(line, len(header)))
            LOGGER.warn("- {}".format(splitted))
            continue
        
        d = {}
        for i,val in enumerate(splitted):
            d[header[i]] = val
        retlist.append(d)

    return retlist


def gen_base_splunklog_dict(id):
    '''

    ::

        {   
            ### Automatic generated data
            u'arc_browse_host': u'pg-arc',
            u'arc_job_id': u'62920906',
            u'arc_job_storage': u'/data/yltan/job/20150904/0000/62920906',
            u'host': u'pg-iccf0298',
            u'id': u'desqual_pg-iccf0298_2015-09-04_00:02:37.864894',
            u'timestamp': u'2015-09-04 00:02:37.992381',
        }
    '''
    data = {}
    data['arc_browse_host'] = os.getenv("ARC_BROWSE_HOST", "")
    data['arc_job_id'] = os.getenv("ARC_JOB_ID", "")
    data['arc_job_storage'] = os.getenv("ARC_JOB_STORAGE", '')
    data['host'] = os.getenv("HOST", '')
    data['id'] = id
    data['timestamp'] = str(datetime.now())
    return data


def gen_runner_splunklog(id, workdir, cfgdata):
    '''

    ::

        {
            ### Data that should be provided
            u'thread': u'ND5revA',
            u'milestone': u'4.0',
            u'topproject': u'i14socnd',
            u'topvariant': u'ar_lib',
            u'topconfig': u'REL4.0ND5revA__15ww123a',
            u'users': u'yltan,kwlim',
        }
        ...   ...   ...

    '''
    data = gen_base_splunklog_dict(id)
    data['workdir'] = workdir

    filepath = get_runner_splunklog_filepath(workdir, id)
    f = open(filepath, 'w')
    for cfg in cfgdata:
        data['topproject'] = cfg['project']
        data['topvariant'] = cfg['variant']
        data['topconfig'] = cfg['config']
        data['milestone'] = cfg['milestone']
        data['thread'] = cfg['thread']
        data['users'] = cfg['users']
        json.dump(data, f)
        f.write("\n")
    f.close()

def get_runner_splunklog_filepath(workdir, id):
    '''
    Returns the fullpath of the runner splunklog.
    '''
    return os.path.join(get_runner_splunklog_dir(workdir), 'runner.{}.splunklog'.format(id))

def get_latest_runner_splunklog_filepath(workdir):
    '''
    Returns the fullpath of the latest runner splunklog.

    Example of runner splunklog filename:-
        runner.desqual_ppglcf0029.png.intel.com_2017-06-19_11:10:44.358844.splunklog
    '''
    splunklogdir = get_runner_splunklog_dir(workdir)
    LOGGER.debug("Getting latest runner splunklog from {}".format(splunklogdir))
    filelist = [os.path.join(splunklogdir, f) for f in os.listdir(splunklogdir) if f.startswith('runner.desqual_') and os.path.isfile(os.path.join(splunklogdir, f))]
    LOGGER.debug("- filelist:{}".format(filelist))

    dtformat = '%Y-%m-%d_%H:%M:%S.%f'
    latest = filelist[0]
    for f in filelist:
        ts1 = os.path.basename(latest).split('_', 2)[-1][:26]
        ts2 = os.path.basename(f).split('_', 2)[-1][:26]
        if datetime.strptime(ts2, dtformat) > datetime.strptime(ts1, dtformat):
            latest = f
    LOGGER.debug("latest = {}".format(latest))
    return latest 


def gen_job_splunklog(id, workdir, project, variant, libtype, config, milestone, thread, error_count, waiver_count, 
        chksum_waiver_count, notrun_waiver_count, output_link, unneeded_topcell_count):
    '''

    ::

        {
            ### Data that should be provided
            u'thread': u'ND5revA',
            u'milestone': u'4.0',
            u'project': u'i14socnd',
            u'variant': u'ar_lib',
            u'libtype': u'None',
            u'config': u'REL4.0ND5revA__15ww123a',
            u'error_count': 0,
            u'waiver_count': 34,
            u'chksum_waiver_count': 12,
            u'notrun_waiver_count': 15,
            u'output_link': 'http://dashboard:8080/......',
            u'unneeded_topcell_count': 3
        }
        ...   ...   ...

    '''
    data = gen_base_splunklog_dict(id)
    data['project'] = project
    data['variant'] = variant
    data['libtype'] = str(libtype)  # Make sure None is converted to str 'None'
    data['config'] = config
    data['milestone'] = milestone
    data['thread'] = thread
    data['error_count'] = error_count
    data['waiver_count'] = waiver_count
    data['chksum_waiver_count'] = chksum_waiver_count
    data['notrun_waiver_count'] = notrun_waiver_count
    data['output_link'] = output_link
    data['unneeded_topcell_count'] = unneeded_topcell_count

    filepath = os.path.join(get_job_results_dir(id, workdir, thread, milestone), 'job.{}.{}.{}.splunklog'.format(id, variant, libtype))
    f = open(filepath, 'w')
    json.dump(data, f)
    f.close()

def gen_errors_file(id, workdir, project, variant, libtype, config, milestone, thread, errors):
    '''
    Generate the csv file of the checker's errors
    '''
    LOGGER.debug("Generating error file ...")
    filepath = os.path.join(get_errors_dir(id, workdir, thread, milestone), 'errors.{}.{}.{}.csv'.format(id, variant, libtype))
    with open(filepath, 'w') as csvfile:
        writer = csv.writer(csvfile)
        for err in errors:
            writer.writerow(err)
    LOGGER.debug("Successfully generated error file: {}".format(filepath))

def gen_unneeded_and_needed_splunklog(id, workdir, project, variant, libtype, config, milestone, thread, unneeded_libtypes, needed_libtypes):
    '''
    | ``unneeded_libtypes`` is a list of ``string``, each represents the libtype name.
    | One event will be created for each of the libtype in ``unneeded_libtypes``. 
    | These events are deposited in the same directory with the *job splunklog*, which is 
    | generated by `gen_job_splunklog`, in `get_job_results_dir` as ``unneeded.desqual_<id>...``

    | Example of one of the events,

    ::

        {
            ### Data that should be provided
            u'thread': u'ND5revA',
            u'milestone': u'4.0',
            u'project': u'i14socnd',
            u'variant': u'ar_lib',
            u'libtype': u'None',
            u'config': u'REL4.0ND5revA__15ww123a',
            u'unneeded': 'rtl'
        }
        ...   ...   ...

    '''
    data = gen_base_splunklog_dict(id)
    data['project'] = project
    data['variant'] = variant
    data['libtype'] = str(libtype)  # Make sure None is converted to str 'None'
    data['config'] = config
    data['milestone'] = milestone
    data['thread'] = thread

    filepath = os.path.join(get_job_results_dir(id, workdir, thread, milestone), 'unneeded.{}.{}.{}.splunklog'.format(id, variant, libtype))
    f = open(filepath, 'w')
    for unneeded_lib in unneeded_libtypes:
        data['unneeded'] = unneeded_lib
        json.dump(data, f)
        f.write("\n")

    data.pop('unneeded', None)
    for needed_lib in needed_libtypes:
        data['needed'] = needed_lib
        json.dump(data, f)
        f.write("\n")
    f.close()


def icm_pmlog_enable(mode=True):
    '''
    | Enable logging of pm/icmp4 commands to icm_pmlog.txt.
    | if ``mode`` is set to ``True``, loggings are logged to ``icm_pmlog.txt``.
    | if ``mode`` is set to ``False``, loggings are set to ``/dev/null``.
    '''
    if mode:
        os.environ['ICM_PM_LOG_FILE'] = 'icm_pmlog.txt'
    else:
        os.environ['ICM_PM_LOG_FILE'] = os.devnull



if __name__ == "__main__":
    sys.exit(main())

