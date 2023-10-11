#!/usr/bin/env python

import os, sys
import logging
import argparse
import re
from pprint import pprint

from dmx.utillib.utils import *
from dmx.abnrlib.icm import ICManageCLI
LOGGER = logging.getLogger('dmx')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--project', required=True)
    parser.add_argument('-i', '--ip', required=True)
    parser.add_argument('-d', '--deliverable', required=True)
    parser.add_argument('-b', '--bom', required=True)
    parser.add_argument('--target-project', required=True)
    parser.add_argument('--target-bom', required=True)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('-n', '--dryrun', action='store_true', default=False)
    args = parser.parse_args()
    project = args.project
    ip = args.ip
    deliverable = args.deliverable
    bom = args.bom
    target_project = args.target_project
    target_bom = args.target_bom
    debug = args.debug
    cli = ICManageCLI()
    if debug:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.INFO)        

    if not cli.project_exists(project):
        raise Exception('Project {} does not exist'.format(project))
    if not cli.variant_exists(project, ip):
        raise Exception('Variant {} does not exist'.format(ip))
    if not cli.libtype_exists(project, ip, deliverable):
        raise Exception('Deliverable {} does not exist'.format(deliverable))

    cmd = 'pm configuration -n {} -t {} -l {} {} -H'.format(bom, deliverable, project, ip)
    exitcode, stdout ,stderr = run_command(cmd)
    if exitcode:
        raise Exception('BOM {} does not exist'.format(bom))
    source_boms = {}   
    for line in stdout.splitlines():
        m = re.match('Project="(.*?)".*Variant="(.*?)".*Configuration="(.*?)"', line)
        if m:
            p = m.group(1).split(':')[-1] if ':' in m.group(1) else m.group(1)
            v = m.group(2)
            c = m.group(3)
            pv  = '{}/{}'.format(p, v)
            pvc = '{}@{}'.format(c, pv)
            source_boms[pv] = pvc
           
    all_target_project_simple_configs = []
    all_target_project_ips = cli.get_variants(target_project)

    for all_target_project_ip in all_target_project_ips:

        ### --target_bom = 'lay'
        if 'lay' in target_bom:
            if cli.libtype_exists(target_project, all_target_project_ip, deliverable):
                lay_config = ''
                if cli.config_exists(target_project, all_target_project_ip, 'lay'):
                    ### Finding the configuration of 'oa'
                    cc = cli.get_config(target_project, all_target_project_ip, 'lay')
                    for e in cc['configurations']:
                        if 'libtype' in e and e['libtype'] == 'oa':
                            lay_config = e['config']
                            break
                else:
                    all_lay_libraries = sorted([x for x in cli.get_libraries(target_project, all_target_project_ip, deliverable) if 'lay' in x])
                    if all_lay_libraries:
                        latest_lay_library = target_bom if target_bom in all_lay_libraries else all_lay_libraries[-1] 
                        cmd = 'pm library -l -W config -p {} {} {} {}'.format(target_project, all_target_project_ip, deliverable, latest_lay_library)
                        exitcode, stdout ,stderr = run_command(cmd)
                        if exitcode:
                            raise Exception('BOM for library {}/{}:{}/{} does not exist'.format(target_project, all_target_project_ip, deliverable, latest_lay_library))
                        m = re.match('Configuration=\"(.*?)\"', stdout)
                        if m:
                            lay_config = m.group(1)
                        else:
                            lay_config = 'dev'
                            #raise Exception('Could not retrieve BOM for {}/{}:{}/{}'.format(target_project, all_target_project_ip, deliverable, latest_lay_library))

                if not lay_config:
                    lay_config = 'dev'
                all_target_project_simple_configs.append((target_project, all_target_project_ip, deliverable, lay_config))

        ### --target_bom = 'dev'
        else:            
            if cli.config_exists(target_project, all_target_project_ip, target_bom, libtype=deliverable):
                all_target_project_simple_configs.append((target_project, all_target_project_ip, deliverable, target_bom))

    items_to_add = []
    items_to_remove = []
    for simple_project, simple_ip, simple_deliverable, simple_bom in all_target_project_simple_configs:                
        items_to_add.append('{}@{}/{}'.format(simple_bom, simple_project, simple_ip))
        pv = '{}/{}'.format(simple_project, simple_ip) 
        if pv in source_boms:
            items_to_remove.append('{}#none'.format(source_boms[pv]))

    LOGGER.debug("items_to_add: {}".format(items_to_add))
    LOGGER.debug("items_to_remove:{}".format(items_to_remove))
    if args.dryrun:
        LOGGER.info("Dryrun mode. No changes will be performed. Exiting now.")
        print '========================================'
        print "items to add:"
        pprint(items_to_add)
        print '========================================'
        print 'items to remove:'
        pprint(items_to_remove)
        print '========================================'
        sys.exit(0)


    if items_to_remove:
        cmd = 'pm configuration -f -k -t {} {} {} {} {}'.format(deliverable, project, ip, bom, ' '.join(items_to_remove))
        LOGGER.debug(cmd)
        exitcode, stdout, stderr = run_command(cmd)
        LOGGER.debug("exitcode: {}".format(exitcode))
        LOGGER.debug("stdout: {}".format(stdout))
        LOGGER.debug("stderr: {}".format(stderr))

    if items_to_add:
        cmd = 'pm configuration -f -t {} {} {} {} {}'.format(deliverable, project, ip, bom, ' '.join(items_to_add))
        LOGGER.debug(cmd)
        exitcode, stdout, stderr = run_command(cmd)
        LOGGER.debug("exitcode: {}".format(exitcode))
        LOGGER.debug("stdout: {}".format(stdout))
        LOGGER.debug("stderr: {}".format(stderr))
                                
if __name__ == '__main__':
    logging.basicConfig(format="%(levelname)s [%(asctime)s]: %(message)s")
    sys.exit(main())

