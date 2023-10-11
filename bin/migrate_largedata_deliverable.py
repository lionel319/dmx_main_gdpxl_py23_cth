#!/usr/bin/env python

import re
import logging
import os
import sys
from argparse import ArgumentParser

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)
BIN = os.path.dirname(os.path.realpath(__file__))

from dmx.abnrlib.icm import ICManageCLI
from dmx.utillib.utils import run_command
SCRATCH_WORKSPACE = os.path.realpath('/p/psg/da/infra/dmx/psgfln/ws')

def main():
    parser = ArgumentParser()
    parser.add_argument('--debug', required=False, action='store_true', default=False, help="More verbose by printing out debugging messages.")
    parser.add_argument('-p','--project', required=True, help="ICM Project")
    parser.add_argument('-i','--ip', required=True, help="ICM Variant.")
    parser.add_argument('-d','--deliverable', required=True, help="ICM Libtype.", choices=['rcxt'])
    args = parser.parse_args()
    project = args.project
    ip = args.ip
    deliverable = args.deliverable
   
    if args.debug:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.DEBUG)         
    else:
        logging.basicConfig(format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.INFO)        
    cli = ICManageCLI()
    DMX = '{}/dmx.py'.format(BIN)    
                
    '''
    1. Get all libraries in deliverable
    2. For each library
        1. Get opened files in library
            * Error out if any files are opened
        2. Get all simple configs holding the library
        3. Get all composite configs holding the simple config
        4. Create workspace based on composite config
        5. icmp4 sync -f ...
        6. dmx scm co --file ...
        7. icmp4 revert -k ...
        8. icmp4 delete -k ...
        9. dmx scm ci --file ...
    '''             

    libraries = cli.get_libraries(project, ip, deliverable)
    for library in libraries:
        library_depotpath = '//depot/icm/proj/{}/{}/{}/{}'.format(project, ip, deliverable, library)
        # Get opened files in library
        opened_files = []
        command = '_icmp4 opened -a {}/...'.format(library_depotpath)            
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            print 'stdout: {}'.format(stdout)
            print 'stderr: {}'.format(stderr)
            sys.exit(1)
        if stdout:            
            opened_files = stdout.splitlines()
        command = '_icmp4 opened -x {}/...'.format(library_depotpath)            
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            print 'stdout: {}'.format(stdout)
            print 'stderr: {}'.format(stderr)
            sys.exit(1)
        if stdout:            
            opened_files = opened_files + stdout.splitlines()
        
        if opened_files:
            print 'There are opened files in {}/{}:{}@{}'.format(project, ip, deliverable, library)
            print 'Please revert the files before attempting to migrate the deliverable:'
            for file in opened_files:
                print '\t{}'.format(file)
            sys.exit(1)                

        # Get simple configs holding the library
        command = 'pm library -l -W config -p {} {} {} {}'.format(project, ip , deliverable, library)
        exitcode, stdout, stderr = run_command(command)
        if exitcode:
            print 'stdout: {}'.format(stdout)
            print 'stderr: {}'.format(stderr)
            sys.exit(1)
        simple_configs = []            
        for line in stdout.splitlines():
            m = re.match('Configuration="(.*?)"', line)
            if m:
                simple_config = m.group(1)
                if not simple_config.startswith('snap') and not simple_config.startswith('REL'):
                    simple_configs.append(simple_config)
        if not simple_configs:
            print 'There are no mutable simple configurations with {}@{} library'.format(deliverable, library)
            sys.exit(1)
                           
        # Get composite configs holding the simple configs                           
        composite_configs = []                                    
        for simple_config in simple_configs:
            command = 'pm configuration -t {} -l -B config {} {} {}'.format(deliverable, project, ip , simple_config)
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                print 'stdout: {}'.format(stdout)
                print 'stderr: {}'.format(stderr)
                sys.exit(1)
            for line in stdout.splitlines():
                m = re.match('Configuration="(.*?)"', line)
                if m:
                    composite_config = m.group(1)
                    if not composite_config.startswith('snap') and not composite_config.startswith('REL'):
                        composite_configs.append(composite_config)  
        if not composite_configs:
            print 'There are no mutable composite configurations with {} config'.format(deliverable)
            sys.exit(1)

        try:
            # Create workspace
            composite_config = composite_configs[0]            
            print 'Creating workspace with {}/{}@{}'.format(project, ip, composite_config)
            wsname = cli.add_workspace(project, ip, composite_config, dirname=SCRATCH_WORKSPACE)
            wspath = '{}/{}'.format(SCRATCH_WORKSPACE, wsname)

            # Sync workspace
            print 'Syncing workspace {}'.format(wsname)
            cli.sync_workspace(wsname, skeleton=True, force=True)
            os.chdir(wspath)
            command = '_icmp4 sync -f "{}/{}/..."'.format(ip, deliverable)
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                print 'stdout: {}'.format(stdout)
                print 'stderr: {}'.format(stderr)
                sys.exit(1)

            # Checkout using dmx scm co
            print 'Checking out largedata files with dmx scm co'
            command = '{0} scm co {1}/{2}/...'.format(DMX, ip, deliverable)
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                print 'stdout: {}'.format(stdout)
                print 'stderr: {}'.format(stderr)
                sys.exit(1)

            # Revert all checkout files on server side
            print 'Reverting checked-out files from server side'
            command = '_icmp4 revert -k "{}/{}/..."'.format(ip, deliverable)
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                print 'stdout: {}'.format(stdout)
                print 'stderr: {}'.format(stderr)
                sys.exit(1)
                
            # Delete all files on server side
            print 'Deleting all files from server side'
            command = '_icmp4 delete -k "{}/{}/..."'.format(ip, deliverable)
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                print 'stdout: {}'.format(stdout)
                print 'stderr: {}'.format(stderr)
                sys.exit(1)
            command = '_icmp4 submit -d "Deleted files as part of {} large data migration" {}/{}/...'.format(deliverable, ip, deliverable)
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                print 'stdout: {}'.format(stdout)
                print 'stderr: {}'.format(stderr)
                sys.exit(1)
            
            # Check in files via dmx scm ci
            print 'Checking in all files to largedata repository'
            command = '{0} scm ci {1}/{2}/... --desc "Checked-in files as part of {2} large data migration"'.format(DMX, ip, deliverable)
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                print 'stdout: {}'.format(stdout)
                print 'stderr: {}'.format(stderr)
                sys.exit(1)
            print stderr
        except Exception as e:
            print e
            sys.exit(1)
        finally:
            if cli.workspace_exists(wsname):
                cli.del_workspace(wsname, preserve=False, force=True)

if __name__ == '__main__':
    logger = logging.getLogger()
    main()


