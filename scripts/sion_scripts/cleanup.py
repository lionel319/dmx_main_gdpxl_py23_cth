#!/usr/bin/env python
import sys
import os
import re
import argparse
import logging
import subprocess
import datetime
from decimal import *
from abnrlib.icm import ICManageCLI

def main():
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest='subparser_name')

    unused_dir_parser = subparser.add_parser('remove-unused')
    unused_dir_parser.add_argument("-p","--path",help="path to release readonly dir", required=True)
    unused_dir_parser.add_argument("-n","--dry-run",help="dry run option, doesn't do actual removal", action = "store_true")
    unused_dir_parser.set_defaults(func=remove_unused_directory)

    temp_dir_parser = subparser.add_parser('remove-temp')   
    temp_dir_parser.add_argument("-n","--dry-run",help="dry run option, doesn't do actual removal",action= "store_true") 
    temp_dir_parser.set_defaults(func=remove_temp_workspace)

    temp_dir_parser = subparser.add_parser('remove-workspace-wo-dir')   
    temp_dir_parser.add_argument("-n","--dry-run",help="dry run option, doesn't do actual removal",action= "store_true") 
    temp_dir_parser.set_defaults(func=remove_workspace_without_dir)
    

    lock_file_parser = subparser.add_parser('remove-redundant-lock')   
    lock_file_parser.add_argument("-n","--dry-run",help="dry run option, doesn't do actual removal",action= "store_true") 
    lock_file_parser.set_defaults(func=remove_redundant_lock)

    args = parser.parse_args()
    
    args.func(args)

def remove_redundant_lock(args):        
    lock_dir = "/ice_rel/readonly/.locks"
    command = "pm workspace -l -u %s" % os.getenv('USER')
    exitcode, stdout, stderr = run_command(command)
    if exitcode:
        if "No workspace found" in stderr:
            return
        print_errors(command, stdout, stderr)
        sys.exit(1)
    workspaces = []
    for line in "".join(stdout).split('\n'):
        m = re.match(r'.*Config=\"(.*?)\".*Variant=\"(.*?)\".*LibType=\"(.*?)\".*Project=\"(.*?)\"', line)
        if m:
            project = m.group(4)
            variant = m.group(2)
            libtype = m.group(3)
            config = m.group(1)
            workspaces.append([project, variant, libtype, config])            
    
    for root, dir, files in os.walk(lock_dir):
        for lock in files:
            m = re.match(r'^(.*?)\.(.*?)\.(.*?)\.(\S+\.\S+)$', lock)
            rel_dir = None
            project = ""
            variant = ""
            libtype = ""
            config = ""
            rel_dir = ""
            if m:
                project = m.group(1)
                variant = m.group(2)
                libtype = m.group(3)
                config = m.group(4)
                rel_dir = "/ice_rel/readonly/%s/%s/%s/%s" % (project, variant, libtype, config)
            else:
                m = re.match(r'^(.*?)\.(.*?)\.(\S+\.\S+)$', lock)
                if m:
                    project = m.group(1)
                    variant = m.group(2)
                    config = m.group(3)
                    rel_dir = "/ice_rel/readonly/%s/%s/%s" % (project, variant, config)
            if rel_dir:
                if not os.path.exists(rel_dir) and [project, variant, libtype, config] not in workspaces:
                    lock_file = "/ice_rel/readonly/.locks/%s" % lock
                    print "Removing %s..." % lock_file
                    os.remove(lock_file) 
    
def print_errors(command, stdout, stderr):
    print "Hostname: %s" % os.getenv('HOSTNAME')
    print "User: %s" % os.getenv('USER')
    print "ARC JOB ID: %s" % os.getenv('ARC_JOB_ID')
    print "Command = %s has encountered error" % command
    print "Stdout: %s" % stdout
    print "Stderr: %s" % stderr

def remove_workspace_without_dir(args):    
    command = "pm workspace -l -u %s" % os.getenv('USER')
    exitcode, stdout, stderr = run_command(command)
    if exitcode:
        if "No workspace found" in stderr:
            return
        print_errors(command, stdout, stderr)
        sys.exit(1)        

    current_site = os.getenv('HOSTNAME')          
    for line in stdout.split('\n'):
        if line:
            m = re.match(r'Workspace="(.*?)" .* Dir="(.*?)" .* Loc="(.*?)" .*', line)
            workspace = m.group(1)
            dir = m.group(2)
            site = m.group(3)
            if site == "PenangProxy":
                site = "pg"
            elif site == "TorontoProxy":
                site = "to"             
            else:
                site = "sj"                           
            if site in current_site:
                print dir
                if not os.path.exists(dir):
                    print "Removing %s" % workspace

                    command = "pm workspace -x -F %s" % workspace
                    print "Running %s" % command
                    if not args.dry_run:
                        exitcode, stdout, stderr = run_command(command)
                        if exitcode:
                            print_errors(command, stdout, stderr)
                            sys.exit(1)
                    print "Successfully removed %s from ICM" % workspace
    
def remove_temp_workspace(args):    
    command = "pm workspace -l -u %s" % os.getenv('USER')
    exitcode, stdout, stderr = run_command(command)
    if exitcode:
        if "No workspace found" in stderr:
            return
        print_errors(command, stdout, stderr)
        sys.exit(1)        

    current_site = os.getenv('HOSTNAME')          
    for line in stdout.split('\n'):
        if line:
            m = re.match(r'Workspace="(.*?)" .* Dir="(.*?)" .* Loc="(.*?)" .*', line)
            workspace = m.group(1)
            dir = m.group(2)
            site = m.group(3)
            if site == "PenangProxy":
                site = "pg"
            elif site == "TorontoProxy":
                site = "to"             
            else:
                site = "sj"                           
            if 'TEMP' in dir and site in current_site:
                print "Removing %s" % workspace

                command = "pm workspace -x -F %s" % workspace
                print "Running %s" % command
                if not args.dry_run:
                    exitcode, stdout, stderr = run_command(command)
                    if exitcode:
                        print_errors(command, stdout, stderr)
                        sys.exit(1)
                print "Successfully removed %s from ICM" % workspace

                if os.path.exists(dir):
                    command = "rm -rf %s" % dir
                    print "Running %s" % command
                    if not args.dry_run:
                        exitcode, stdout, stderr = run_command(command)
                        if exitcode:
                            print_errors(command, stdout, stderr)
                            sys.exit(1)
                    print "Successfully removed %s from local directory (%s)" % (workspace, dir)

def remove_unused_directory(args):       
    if args.path.endswith("/"):
        args.path = args.path[:-1]     
    cli = ICManageCLI()        

    to_be_removed = []
    #read storage files to get all the directories of data that have been populated to /ice_rel/readonly
    for root, dirs, files in os.walk('{}/.locks'.format(args.path)):
        for lock in files:
            project = variant = libtype = config = ''
            temp = lock.split('.')
            if len(temp) == 3:
                project = temp[0]
                variant = temp[1]
                config = temp[2]
            elif len(temp) > 3:
                project = temp[0]
                variant = temp[1]
                if cli.libtype_exists(project, variant, temp[2]):
                    libtype = temp[2]
                    config = '.'.join(temp[3:])
                else:
                    config = '.'.join(temp[2:])
            else:
                continue
            if not libtype:                    
                dir = '{}/{}/{}/{}'.format(args.path, project, variant, config)        
            else:                
                dir = '{}/{}/{}/{}/{}'.format(args.path, project, variant, libtype, config)   

            if os.path.isdir(dir):
                print "Querying %s" % dir
                #find total number of files for a release
                command = "find %s -type f | wc -l" % dir
                exitcode, stdout, stderr = run_command(command)
                if exitcode:
                    print_errors(command, stdout, stderr)
                    sys.exit(1)
                num_of_files = int(stdout)
                #find total number of files that have not been accessed for more than 45 days for a release
                command = "find %s -type f -atime +45 | wc -l" % dir
                exitcode, stdout, stderr = run_command(command)
                if exitcode:                
                    print_errors(command, stdout, stderr)               
                    sys.exit(1)
                num_of_files_not_accessed_45_days = int(stdout)
                #calculate total size of a release
                command = "du -sk %s" % dir
                exitcode, stdout, stderr = run_command(command)
                if exitcode:
                    print_errors(command, stdout, stderr)
                    sys.exit(1)                
                actual_size = int("".join(stdout).split("\t")[0])
                #calculate aged percentage
                #aged_percentage (rounded to 2 fraction numbers) = num_of_files_not_accessed_45_days)/num_of_files * 100
                aged_percentage = "%.2f" % round(Decimal(num_of_files_not_accessed_45_days)/Decimal(num_of_files) * Decimal(100), 2)
                #remove only release data that has 100% aged percentages
                if aged_percentage == "100.00":
                    print "%s will be removed (aged percentage = 100)" % dir
                    date_removed = datetime.date.today()
                    to_be_removed.append(dir)
            else:
                print '{} does not exist...'.format(dir)
                command = "rm -f {}/{}".format(root, lock)
                print "Running %s" % command
                exitcode, stdout, stderr = run_command(command)
                if exitcode:
                    print_errors(command, stdout, stderr)
                                           
    for dir in to_be_removed:
        #remove release directory first
        command = "rm -rf %s" % dir
        print "Running %s" % command
        if not args.dry_run:
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                print_errors(command, stdout, stderr)
            else:           
                tmp = dir.split('/')
                lock_file = ""
                if len(tmp) == 6:
                    tmp, disk, dir, project, variant, config = dir.split('/')
                    #remove lock file for the release                
                    lock_file = "/%s/%s/.locks/%s.%s.%s" % (disk, dir, project, variant, config)
                elif len(tmp) == 7:
                    tmp, disk, dir, project, variant, libtype, config = dir.split('/')                  
                    #remove lock file for the release                
                    lock_file = "/%s/%s/.locks/%s.%s.%s.%s" % (disk, dir, project, variant, libtype, config)
                if os.path.exists(lock_file):
                    command = "rm -f %s" % lock_file
                    print "Running %s" % command
                    exitcode, stdout, stderr = run_command(command)
                    if exitcode:
                        print_errors(command, stdout, stderr)
        print "Successfully removed %s from local directory" % dir
    
def run_command(command):
    '''
    Run a system command and returns a tuple of (exitcode, stdout, stderr)
    >>> run_command('echo foo')
    (0, 'foo\\n', '')
    >>> run_command('ls /foo/bar')
    (2, '', 'ls: /foo/bar: No such file or directory\\n')
    '''
    proc = subprocess.Popen(command, bufsize=1, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = proc.communicate(None)
    exitcode = proc.returncode
    return (exitcode, stdout, stderr) 

if __name__ == "__main__":
    sys.exit(main())
