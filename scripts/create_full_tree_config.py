#!/usr/bin/env python
'''
This script generates a full configuration tree from scratch.

============
Inputs:-
============
    --project
    --variant
    --config
    --inputfile

    The content of --inputfile looks like this:-
        <project> <variant>
        <project> <variant>
        ...   ...   ...

=======================================
Here's the algorithm of the program:-
=======================================
    if --project/--variant@--config does not exist:

        For each <project>/<variant> in the --inputfile:
            libtypes = required libtypes of <project>/<variant> (from roadmap)
            for libtype in libtypes:
                if libtype@--config does not exist:
                    clone libtype@dev to libtype@--config
            
            if <project>/<variant>@--config does not exist:
                create <project>/<variant>@--config, include all libtypes@--config into it.

        create --project/--variant@--config, and include all <project>/<variant>@--config into it.

============
USAGE:
============
$create_full_tree_config.py \
        --project Falcon_Mesa \
        --variant z1557a \
        --config desqual___FM8revA0___50 \
        --inputfile ./fullchip.txt \
        --debug

'''

import os
import sys
from pprint import pprint
import argparse
import logging

#rootdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'python')
#sys.path.insert(0, rootdir)
import dmx.ecolib.ecosphere
import dmx.abnrlib.config_factory
import dmx.abnrlib.icmsimpleconfig
import dmx.abnrlib.icmcompositeconfig
import dmx.abnrlib.icm
import dmx.utillib.utils

LOGGER = logging.getLogger()

def main():
    args = _add_args()
    _setup_logger(args)

    icm = dmx.abnrlib.icm.ICManageCLI()

    if icm.config_exists(args.project, args.variant, args.config):
        LOGGER.info("{}/{}@{} already exists. There is nothing to be done!".format(
            args.project, args.variant, args.config))
        return 0

    pvlist = [] 
    if not args.single:
        pvlist = read_input_file(args.inputfile)
        #pvlist = [('i10socfm', 'intfclib'), ('i10socfm', 'intfclibaib'), ('i10socfm', 'intfclibcore')]
    pvlist = set(pvlist)

    if not args.single:
        ### Submitting each project/variant task to arc submit (parallelizing)
        singlerun_job_id_list = []
        variant_include_string = ' '
        for project,variant in pvlist:

            ### Skip (for now) if it is toplevel project/variant, because the toplevel config
            ### can only be built after everything else beneath it is done.
            if project==args.project and variant==args.variant:
                continue

            arccmd = 'arc submit -t name={}/{} -- {} --project {} --variant {} --config {} --inputfile dummy --debug --single'.format(
                project, variant, __file__, project, variant, args.config)
            singlerun_job_id_list.append(run_arc_submit(arccmd))
            variant_include_string += dmx.utillib.utils.format_configuration_name_for_printing(
                project, variant, args.config) + ' '

        ### Block it until all the children jobs are done.
        LOGGER.debug("Waiting for children jobs {} to complete ...".format(singlerun_job_id_list))
        for jobid in singlerun_job_id_list:
            os.system("arc wait {}".format(jobid))
        LOGGER.debug("All children jobs completed!")

        ### Creating toplevel configuration
        return single_run(args.project, args.variant, args.config, variant_include_string)
   
    else:
        return single_run(args.project, args.variant, args.config)


def single_run(project, variant, config, variant_include_string=''):
    e = dmx.ecolib.ecosphere.EcoSphere()
    family = e.get_family_for_icmproject(project)
    ip = family.get_ip(variant, project_filter=project)
    deliverables = ip.get_deliverables(local=False, bom='dev')
    icm = dmx.abnrlib.icm.ICManageCLI()

    retcode = 0

    ### Cloning all needed deliverables from 'dev' to new-config
    include_string = ' '
    for deliverable in deliverables:

        config_exists = True
        if icm.config_exists(project, variant, config, libtype=deliverable.name):
            LOGGER.info("{}/{}:{}@{} already exists. There is nothing to be done!".format(
                project, variant, deliverable.name, config))
        else:
            cmd = 'dmx bom clone -p {} -i {} -d {} -b dev --dstbom {} --debug'.format(
                project, variant, deliverable.name, config)
            LOGGER.debug("running: {}".format(cmd))
            exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
            LOGGER.info(_formatted_run_command_output(exitcode, stdout, stderr))
            if 'ERROR' in stdout or 'ERROR' in stderr:
                retcode = 1
                config_exists = False

        if config_exists:
            include_string += dmx.utillib.utils.format_configuration_name_for_printing(
                project, variant, config, deliverable.name) + ' '

    ### Building variant-level config, and include all needed-deliverables into it.
    include_string += variant_include_string
    cmd = 'dmx bom create -p {} -i {} -b {} --debug --include {}'.format(
        project, variant, config, include_string)
    LOGGER.debug("running: {}".format(cmd))
    exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
    LOGGER.info(_formatted_run_command_output(exitcode, stdout, stderr))
    if 'ERROR' in stdout or 'ERROR' in stderr:
        retcode = 1

    return retcode


def _formatted_run_command_output(exitcode, stdout, stderr):
    return """
        exitcode:{}
        stdout:{}
        stderr:{}
    """.format(exitcode, stdout, stderr)


def run_arc_submit(arc_submit_cmd):
    '''
    Runs the given ``arc_submit_cmd``, and return the arc job id.
    '''
    exitcode, stdout, stderr = dmx.utillib.utils.run_command(arc_submit_cmd)
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


def read_input_file(inputfile):
    '''
    Input File
    ----------
    project variant
    project variant
    ...   ...   ...
    '''
    retlist = []
    with open(inputfile) as f:
        for line in f:
            sline = line.strip().split()
            if sline and not sline[0].startswith("#"):
                retlist.append((sline[0], sline[1]))
    return retlist


def _add_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True)
    parser.add_argument('--variant', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--inputfile', required=True)
    parser.add_argument('--single', default=False, action='store_true', help=argparse.SUPPRESS)
    
    parser.add_argument('--debug', default=False, action='store_true')

    args = parser.parse_args()

    return args

def _setup_logger(args):
    ''' Setup the logging interface '''
    level = logging.INFO
    if 'debug' in args and args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)

if __name__ == '__main__':
    
    sys.exit(main())

