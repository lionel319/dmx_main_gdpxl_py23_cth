#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import subprocess
import re
import pwd
import argparse

#Mapping table for ICMP4 group to UNIX group
icm_groups = {
             #ICM group         :UNIX group
             "all.users"        :"psgeng",
             "i10.users"        :"psgi10",
             "fln.users"        :"psgfln",
             "whr.users"        :"psgwhr",
             "psgi10arm.users"  :"psgi10arm",
             "t16ff.users"      :"psgt16ff",
             "psgsynopsys.users"    :"psgsynopsys",
             "psgnd.users"      :"psgnd",
             "psgship.users"    :"psgship",
             "gdr.users"        :"psggdr",
             "rnr.users"        :"psgrnr",
             "psgpbut180.users" :"psgt180",
             "psgpbui65.users"  :"psgi65",
             "psgpbutj65.users" :"psgtj65",
             "knl.users"        :"psgknl",
             "dmdip.users"      :"psgdmd",
             "dmdhps.users"     :"psgt16arm",
             "psgdpt.users"     :"psgdpt",
             "psgavc.users"     :"psgavc",
             "psgvlc.users"     :"psgvlc",
             "cdr.users"        :"psgcdr",
             "psgart.users"     :"psgart",
             "psgrambus.users"  :"psgrambus",
             "psgcadence.users"     :"psgcadence",
             "psgsynopsys.users"    :"psgsynopsys",
             "psgipxsmx_arm.users"   :"psgipxsmx_arm",
             "psgn5.users"      :"psgn5",
             "psgavr.users"     :"psgavr", 
             "psgacr.users"     :"psgacr",
             "psgn5arm.users"   :"psgn5arm",
             "psgrtm.users"   :"psgrtm",
             "psgknr.users"   :"psgknr",
             "psgi5.users"      :"psgi5",
             "ip5nm.users"      :"ip5nm"
            }

default_prot_group = 'psgeng'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-dir", required=True)
    parser.add_argument("--client", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--variant", required=True)
    args = parser.parse_args()

    error_msg = "[POSTSYNC] ICM has encountered error in performing these actions. Please visit goto://psg_icm_faq and search for postsync for more information."

    client_dir = args.client_dir
    client = args.client
    project = args.project
    variant = args.variant
    user = os.environ['USER']
    #get workspace configuration
    command = "pm workspace -w %s -l" % client
    status, stdout, stderr = run_command(command)
    if status or stderr:
        print(error_msg)
        print("command: %s" % command)
        print("stdout: %s" % stdout)
        print("stderr: %s" % stderr)
        sys.exit(1)

    m = re.match(r'.* Config="(.*?)" .* LibType="(.*?)" .*',stdout)
    if m:
        config = m.group(1)
        libtype = m.group(2)

    #get all projects/variants referenced by the workspace configuration
    project_variant = []
    if libtype:
        command = "pm configuration -n %s -l %s %s -t %s" % (config,project,variant,libtype)   
    else:
        command = "pm configuration -n %s -l %s %s" % (config,project,variant)        
    status, stdout, stderr = run_command(command)
    if status or stderr:
        print(error_msg)
        print("command: %s" % command)
        print("stdout: %s" % stdout)
        print("stderr: %s" % stderr)
        sys.exit(1)

    for line in stdout.split('\n'):
        result = re.match('Project=".*:(.*?)" Variant="(.*?)" .* Configuration="(.*?)"',line)
        if result:
            p = result.group(1)
            v = result.group(2)
            if [p,v] not in project_variant:
                project_variant.append([p,v])

    required_groups = []
    required_groups.append(get_proj_prot_group(project))
    for p,v in project_variant:
        required_groups.append(get_var_prot_group(p, v))
    required_groups = list(set(required_groups))
    command = "groups"
    status, stdout, stderr = run_command(command)
    if status or stderr:
        print(error_msg)
        print("command: %s" % command)
        print("stdout: %s" % stdout)
        print("stderr: %s" % stderr)
        sys.exit(1)
    user_groups = stdout.strip().split(' ')
    for required_group in required_groups:
        if required_group not in user_groups:
            print("[POSTSYNC] %s does not have %s NIS group" % (user, required_group))
            print(error_msg)
            sys.exit(1)                        

    #Secure parent directory with appropriate UNIX group
    group = get_proj_prot_group(project)
    command = "chgrp -R %s %s" % (group, client_dir)
    status, stdout, stderr = run_command(command)
    if status or stderr:
        print(error_msg)
        print("command: %s" % command)
        print("stdout: %s" % stdout)
        print("stderr: %s" % stderr)
        sys.exit(1)                

#   2019/08/16 - comment out as redundant with previous action
#    #for each project/variant, lock the directory with the right permission
#    for p,v in project_variant:
#        target_dir = "%s/%s" % (client_dir,v)
#        group = get_var_prot_group(p, v)
#        command = "chgrp -R %s %s" % (group, target_dir)
#        status, stdout, stderr = run_command(command)
#        if status or stderr:
#            print "[POSTSYNC] ICM has encountered error in performing these actions. Please contact psgicmsupport@intel.com with these error messages for more assistance."
#            print "command: %s" % command
#            print "stdout: %s" % stdout
#            print "stderr: %s" % stderr
#            sys.exit(1)
        
    #turn off global access bit for all subdirectory
    command = "find %s -type d | xargs chmod o-rwx,g+s" % client_dir
    status, stdout, stderr = run_command(command)
    if status or stderr:
        print(error_msg)
        print("command: %s" % command)
        print("stdout: %s" % stdout)
        print("stderr: %s" % stderr)
        sys.exit(1)

def get_proj_prot_group(project):
    '''
    Given project, this function returns a UNIX group to secure directory with
    Function depends on ICMP4 protect table to determine which group to protect with
    Examples:
    > get_proj_prot_group(i14socnd)
      nd
    /i14socnd/ will be locked with nd

    > get_proj_prot_group(t20socanf)
      eng
    /t20socanf/ will be locked with eng
    '''
    command = "icmp4 -uicmAdmin protects -a //depot/icm/proj/%s/icmrel/ | grep group | egrep -i 'read|list' | tail -n1" % (project)    
    status, stdout, stderr = run_command(command)
    if status:
        print("Error running %s" % command)
        print("stdout:", stdout)
        print("stderr:", stderr)
        sys.exit(1)
    '''
    The above commands returns in this format:
    protection_mode  group/user  name       client_host_id  depot_path_pattern
    Example:
    read             group       soci.users *               //depot/icm/proj/i14socnd/icmrel/soc...
    Group name is what we want
    '''
    if stdout:
        group = stdout.strip().split()[2]
        return icm_groups[group]
    else:
        #if command returns null, protect dir with default group: eng
        group = default_prot_group
        return group

def get_var_prot_group(project, variant):
    '''
    Given project and variant, this function returns a UNIX group to secure directory with
    Function depends on ICMP4 protect table to determine which group to protect with
    Examples:
    > get_var_prot_group(i14socnd, aux)
      nd
    /i14socnd/aux will be locked with nd

    > get_var_prot_group(i14socnd, soc_sha_wrapper)
      soci
    /i14socnd/soc_sha_wrapper will be locked with soci
    '''
    command = "icmp4 -u icmAdmin protects -a //depot/icm/proj/%s/icmrel/%s/ | grep group | egrep -i 'read|list' | tail -n1" % (project, variant)    
    status, stdout, stderr = run_command(command)
    if status:
        print("Error running %s" % command)
        print("stdout:", stdout)
        print("stderr:", stderr)
        sys.exit(1)
    '''
    The above commands returns in this format:
    protection_mode  group/user  name       client_host_id  depot_path_pattern
    Example:
    read             group       soci.users *               //depot/icm/proj/i14socnd/icmrel/soc...
    Group name is what we want
    '''
    if stdout:
        group = stdout.strip().split()[2]
        return icm_groups[group]
    else:
        #if command returns null, protect dir with default group: eng 
        group = default_prot_group
        return group

def run_command(command, stdin=None, timeout=None):
    '''
    Run a sub-program in subprocess.
    Returns a tuple of exitcode, stdout, stderr
    '''
    proc = subprocess.Popen(command, bufsize=1, shell=True,
              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(stdin)
    exitcode = proc.returncode
    return (exitcode, stdout, stderr)

if __name__ == "__main__":
    main()
    sys.exit(0)
