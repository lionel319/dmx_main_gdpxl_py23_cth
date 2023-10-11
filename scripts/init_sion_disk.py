#! /usr/bin/env python

import logging
import argparse
import os
import subprocess
import sys
import re
import unicodedata
import dmx.utillib.loggingutils
import dmx.sionlib.sion_utils
import glob
import dmx.ecolib.ecosphere
'''
//depot/da/infra/dmx/main/scripts/init_sion_disk.py#1

There are two method in the init_sion_disk script.
1, add_new_proj
add_new_proj is used when there is a new project and we want to setup the new proj sion link. You will need to arc shell correct dmxdata to make it work

The script will first read all the proj information in dmxdata, and compare with all the sion disk in /p/psg/sion2. if the proj is not yet create in /p/psg/sion2, it will then create a proj directory in both /p/psg/sion2/<icmproj> and <newdisk>/<icmproj>, then it will symlink it to new disk

E.g.:
    python /nfs/site/disks/da_infra_1/users/wplim/init_sion_disk.py add_new_proj --newdisk /nfs/site/disks/psg_sion2_1

    2, add_new_disk
    add_new_disk is used when there is a new disk and we want to add new disk if existing disk already full.

    The script will first read all the sion disk in /p/psg/sion2. and resolve the symlink. if the symlink path is /nfs/<site>/disks/psg_sion2_<num>, it will check wther the directory is empty or not. If it is empty it will remove the link, then added new link to the new disk. The reason for this is to maintain the <num>, we will only add num if there is exiting folder populated before, else we reuse. 

    python /nfs/site/disks/da_infra_1/users/wplim/init_sion_disk.py add_new_disk --newdisk /nfs/site/disks/psg_sion2_1
'''

class InitSionDiskError(Exception): pass

logger = dmx.utillib.loggingutils.setup_logger(level=logging.INFO)

def main():
    args = _add_args()
    args.func(args)

def clean_output(output):
    if os.path.exists(output):
        cmd = 'rm -rf {}'.format(output)
        subprocess.call([cmd], shell=True)


def add_new_disk(args):
    newdisk = args.newdisk
    dryrun = args.dry_run
    output = args.output

    clean_output(output)

    check_if_disk_match_sion_naming(newdisk)
    if args.debug:
        logger = setup_logger(level=logging.DEBUG)
    else:
        logger = setup_logger(level=logging.INFO)

    e = dmx.ecolib.ecosphere.EcoSphere()
    all_projs = e.get_icmprojects()

    sd = dmx.sionlib.sion_utils.SionDisk()
    sion_projs = sd.all_proj_disk

    for proj, all_disks in sion_projs.items():
        for ea_disk in all_disks:
            abspath = os.readlink(ea_disk)
            match = re.search('/nfs/\S+/disks/psg_sion2_(\d+)', abspath)
            if match:
                if not os.listdir(abspath):
                   logger.info('No bom being populated before') 
                   logger.info('Remove exisiting sion link {}'.format(ea_disk)) 
                   #cmd = 'echo \'rm -rf {}\' >> {}'.format(ea_disk, output)
                   if not dryrun:
                        cmd = 'rm -rf {}'.format(ea_disk)
                        subprocess.call([cmd], shell=True)
                   else:
                        logger.info('Dry-run: {}'.format(cmd))

    create_new_proj_directory(all_projs, newdisk, dryrun, output)
    add_link_to_newdisk(newdisk, dryrun, output)

def add_link_to_newdisk(newdisk, dryrun, output):
    sd = dmx.sionlib.sion_utils.SionDisk()
    sion_projs_disk = sd.all_proj_disk

    e = dmx.ecolib.ecosphere.EcoSphere()
    all_projs = e.get_icmprojects()

 
    for ea_proj in all_projs:
        num = len(sion_projs_disk.get(ea_proj))+1 if sion_projs_disk.get(ea_proj) else 1
        #cmd = 'echo \'ln -s {1}/{0} /p/psg/sion2/{0}/{0}_sion2_{3}\' >> {2}'.format(ea_proj, newdisk, output, num)
        cmd = 'ln -s {1}/{0} /p/psg/sion2/{0}/{0}_sion2_{2}'.format(ea_proj, newdisk, num)
        if not dryrun:
            logger.info('Cmd: {}'.format(cmd))
            subprocess.call([cmd], shell=True)
            pass
        else:
            logger.info('Dry-run: {}'.format(cmd))


    


def add_new_proj(args):
    newdisk = args.newdisk
    dryrun = args.dry_run
    output = args.output

    clean_output(output)

    check_if_disk_match_sion_naming(newdisk)
    if args.debug:
        logger = setup_logger(level=logging.DEBUG)
    else:
        logger = setup_logger(level=logging.INFO)

    sd = dmx.sionlib.sion_utils.SionDisk()
    sion_projs = sd.all_proj_disk.keys()

    e = dmx.ecolib.ecosphere.EcoSphere()
    all_projs = e.get_icmprojects()

    my_projs = set(all_projs) - set(sion_projs)
    #print my_projs
    create_new_proj_directory(my_projs, newdisk, dryrun, output) 
    create_unlink_project(my_projs, newdisk, dryrun, output)

def check_if_disk_match_sion_naming(newdisk):
    match = re.search('/nfs/site/disks/psg_sion2_(\d+)', newdisk)
    if not match:
        logger.error('{} does not match naming convention /nfs/site/disks/psg_sion2_'.format(newdisk))
        sys.exit(1)


def create_new_proj_directory(projs, newdisk, dryrun, output):

    for ea_proj in projs:
        path = '/p/psg/sion2/{0}'.format(ea_proj)
        newdisk_path = '{}/{}'.format(newdisk, ea_proj)
        if not os.path.exists(path) or not os.path.exists(newdisk_path):
           # cmd = 'echo \'mkdir -p {0} ; mkdir -p {1}/{2}\' >> {3}'.format(path, newdisk, ea_proj, output)
            cmd = 'mkdir -p {0} ; mkdir -p {1}/{2}'.format(path, newdisk, ea_proj)
            if not dryrun:
                logger.info('Cmd : {}'.format(cmd))
                subprocess.call([cmd], shell=True)
            else:
                logger.info('Dry-run: {}'.format(cmd))

def create_unlink_project(projs, newdisk, dryrun, output):
    for ea_proj in projs:
        #cmd = 'echo \'ln -s {1}/{0} /p/psg/sion2/{0}/{0}_sion2_1\' >> {2}'.format(ea_proj, newdisk, output)
        cmd = 'ln -s {1}/{0} /p/psg/sion2/{0}/{0}_sion2_1'.format(ea_proj, newdisk)
        if not dryrun:
            logger.info('Cmd : {}'.format(cmd))
            subprocess.call([cmd], shell=True)
            pass
        else:
            logger.info('Dry-run: {}'.format(cmd))


def _add_args():
    ''' Parse the cmdline arguments '''
    # Sub-Parser Example
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(help='sub-command help')

    # update_latest_variant subcommand parser
    parser_add_proj = subparser.add_parser('add_new_proj', help='add_new_proj help')
    parser_add_proj.add_argument('--newdisk', required=True, help="newdisk.")
    parser_add_proj.add_argument("-d", "--debug", action='store_true', help="debug level")
    parser_add_proj.add_argument("-n", "--dry_run", action='store_true', help="dry run")
    parser_add_proj.add_argument("-o", "--output", default='psgengadm_runme.txt', help="output")
    parser_add_proj.set_defaults(func=add_new_proj)

    # update_latest_wrapper subcommand parser
    parser_add_disk = subparser.add_parser('add_new_disk', help='add disk help')
    parser_add_disk.add_argument('--newdisk', required=True, help="newdisk.")
    parser_add_disk.add_argument("-d", "--debug", action='store_true', help="debug level")
    parser_add_disk.add_argument("-n", "--dry_run", action='store_true', help="dry run")
    parser_add_disk.add_argument("-o", "--output", default='psgengadm_runme.txt', help="output")
    parser_add_disk.set_defaults(func=add_new_disk)
    args = parser.parse_args()


    return args


def setup_logger(name=None, level=logging.INFO):
    ''' Setup the logger for the logging module.

    If this is a logger for the top level (root logger),
        name=None
    else
        the __name__ variable from the caller should be passed into name

    Returns the logger instant.
    '''

    if name:
        LOGGER = logging.getLogger(name)
    else:
        LOGGER = logging.getLogger()

    if level <= logging.DEBUG:
        fmt = "%(levelname)s [%(asctime)s] - [%(lineno)s][%(pathname)s]: %(message)s"
    else:
        fmt = "%(levelname)s: %(message)s"

    logging.basicConfig(format=fmt)
    LOGGER.setLevel(level)

    return LOGGER


if __name__ == '__main__':
    sys.exit(main())

   
