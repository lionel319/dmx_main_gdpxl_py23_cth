#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import fcntl
import subprocess
import re
import pwd
import argparse
import logging
import shutil

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.abnrlib.flows.list import List
from dmx.abnrlib.flows.printconfig import PrintConfig
from dmx.abnrlib.flows.diffconfigs import DiffConfigs

#Mapping table for ICMP4 group to UNIX group
icm_groups = {
             #ICM group   :UNIX group
             "all.users"    :"psgeng",
             "i10.users" :"psgi10",
             "fln.users" : "psgfln"
            }

default_prot_group = 'psgeng'
default_immutable_disk = "/p/psg/falcon/sion"
default_immutable_directory = "/p/psg/falcon/sion"
default_headless_account = "psginfraadm"
LOGGER = logging.getLogger()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-cmd', '--command')
    parser.add_argument('-p', '--project')
    parser.add_argument('-v', '--variant')
    parser.add_argument('-l', '--libtype')
    parser.add_argument('-c', '--config')
    parser.add_argument('-dir', '--directory')
    parser.add_argument('-u', '--user')
    parser.add_argument('-cfg', '--cfgfile')
    parser.add_argument('-icmcmd', '--icm-command')
    parser.add_argument('-misc')

    args = parser.parse_args()
    command = args.command

    #preparing to run command
    if command == "populate":
        project = args.project
        variant = args.variant
        libtype = args.libtype
        config = args.config
        if args.directory == "None":
            user_directory = None
        else:            
            user_directory = os.path.abspath(args.directory)
        user = args.user
        if args.cfgfile == "None":
            cfgfile = None
        else:
            cfgfile = os.path.abspath(args.cfgfile)
        misc = args.misc
        tag, wsname = misc.split(",")
        if "tag" in tag and "tag:None" not in tag:
            tag = tag.split(":")[1]
        else:
            tag = ""            
        if "wsname" in wsname and "wsname:None" not in wsname:
            wsname = wsname.split(":")[1]             
        else:
            wsname = ""            

        #check if p/v/c exist or p/v/c/l exist
        if libtype == 'None':
            cmd = 'pm configuration -l %s %s -n %s' % (project, variant, config)
        else:
            cmd = 'pm configuration -l %s %s -n %s -t %s' % (project, variant, config, libtype)
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            if libtype == 'None':
                LOGGER.error("%s/%s/%s does not exist" % (project, variant, config))
                LOGGER.error("Please ensure that you have key in the right project, variant and configuration")
            else:
                LOGGER.error("%s/%s/%s/%s does not exist" % (project, variant, libtype, config))
                LOGGER.error("Please ensure that you have key in the right project, variant, libtype and configuration")               
            sys.exit(1)

        #check if user even has permission to populate data
        must_have_group = get_proj_prot_group(project)
        cmd = "groups %s" % user
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)
        user_groups = stdout.strip().split(" ")[2:]
        if must_have_group not in user_groups:
            LOGGER.error("%s does not have permission to access %s data" % (user,project))
            sys.exit(1)
        
        #now we check for psginfraadm access level
        # ignore psgda.users
        cmd = "icmp4 groups | grep users | grep -v contractor | grep -v psg | grep -v runda | grep -v tsmc | grep -v soci | grep -v whr | grep -v t16ff"
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)
        current_icm_groups = stdout.strip().split("\n") 
        cmd = "icmp4 groups %s" % default_headless_account
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)
        headless_icm_groups = stdout.split('\n')[:-1]
        cmd = "groups %s" % default_headless_account 
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)
        headless_unix_groups = stdout.strip().split(" ")[2:]
        for group in current_icm_groups:
            #Check if script is updated with latest groups in ICM and UNIX
            if group in icm_groups:
                #Check if psginfraadm has all the appropriate groups in ICM
                if group not in headless_icm_groups:
                    LOGGER.error("%s ICM group is not found in %s account" % (group, default_headless_account))
                    LOGGER.error("Please contact psgicmsupport@intel.com with the error messages")
                    sys.exit(1)
                #Check if psginfraadm has all the appropriate groups in UNIX
                if icm_groups[group] not in headless_unix_groups:
                    LOGGER.error("%s UNIX group is not found in %s account" % (icm_groups[group], default_headless_account))
                    LOGGER.error("Please contact psgicmsupport@intel.com with the error messages")
                    sys.exit(1)
            else:
                LOGGER.error("%s ICM group is not found in ICM group mapping table" % group)
                LOGGER.error("Please contact psgicmsupport@intel.com with the error messages")
                sys.exit(1)             
        
        #get the right directory 
        if config.startswith('REL') or config.startswith('snap'):
            if user_directory:                               
                if user_directory.endswith('/'):
                    user_directory = user_directory[:-1]                             
             
                #check if psginfraadm is able to write into the user directory
                if not os.access(user_directory, os.W_OK | os.X_OK):              
                    LOGGER.error('%s is not writable by %s. Please chmod the directory to 777.' % (user_directory,default_headless_account))
                    sys.exit(1)
                if wsname:
                    target_directory = "%s/%s" % (user_directory,wsname)                    
                else:                    
                    if libtype == 'None':
                        target_directory = "%s/%s/%s/%s" % (user_directory,project,variant,config)
                    else:
                        target_directory = "%s/%s/%s/%s/%s" % (user_directory,project,variant,libtype,config)
                temp_directory = "%s.TEMP%s" % (target_directory, os.environ['ARC_JOB_ID'])

                build_workspace(project, variant, libtype, config, temp_directory, default_headless_account, cfgfile, wsname)

                #if the target directory exist, remove that directory, otherwise we cannot rename our temp dir to target dir
                if os.path.isdir(target_directory):
                    cmd = "rm -rf %s" % target_directory
                    exitcode, stdout, stderr = run_command(cmd)
                    if exitcode:
                        print_errors(cmd, exitcode, stdout, stderr)

                os.rename(temp_directory, target_directory)                
            else:                
                if libtype == 'None':
                    target_directory = "%s/%s/%s/%s" % (default_immutable_directory,project,variant,config)
                else:
                    target_directory = "%s/%s/%s/%s/%s" % (default_immutable_directory,project,variant,libtype,config)
    
                temp_directory = "%s.TEMP%s" % (target_directory, os.environ['ARC_JOB_ID'])
                                                
                #Check that .storage exists
                global storage_path
                storage_path = "%s/.storage" % default_immutable_directory
                if not os.path.exists(storage_path):
                    LOGGER.error("%s does not exist" % storage_path)
                    LOGGER.error("Please contact psgicmsupport@intel.com with the error messages")
                    sys.exit(1) 
        
                #check .locks dir exist
                lockdir = "%s/.locks" % default_immutable_directory
                if not os.path.exists(lockdir):
                    LOGGER.error("%s does not exist" % lockdir)
                    LOGGER.error("Please contact psgicmsupport@intel.com with the error messages")
                    sys.exit(1) 
                if libtype == 'None':               
                    lockfile = "%s/%s.%s.%s" % (lockdir, project, variant, config)
                else:
                    lockfile = "%s/%s.%s.%s.%s" % (lockdir, project, variant, libtype, config)                
                #check if lockfile exist
                if os.path.exists(lockfile):
                    if libtype == 'None':
                        LOGGER.error("%s/%s/%s is being populated at the moment. Please try again later." % (project,variant,config))
                    else:
                        LOGGER.error("%s/%s/%s/%s is being populated at the moment. Please try again later." % (project,variant,libtype,config))
                    sys.exit(1)
                else:
                    open(lockfile, 'w')
                    try:
                        build_workspace(project, variant, libtype, config, temp_directory, default_headless_account, None, None)
                    except Exception as e:
                        LOGGER.error(e)
                        #if build workspace fails, remove the lock file
                        os.remove(lockfile)
                        sys.exit(1)                    
                    try:                        
                        shutil.rmtree(target_directory)                        
                    except:
                        pass                        
                    os.rename(temp_directory, target_directory)       
                    record_workspace_size(target_directory)                     
        else:
            if user_directory:                               
                if user_directory.endswith('/'):
                    user_directory = user_directory[:-1]
               
                #check if psginfraadm is able to write into the user directory
                if not os.access(user_directory, os.W_OK | os.X_OK):              
                    LOGGER.error('%s is not writable by %s. Please chmod the directory to 777.' % (user_directory,default_headless_account))
                    sys.exit(1)
                if wsname:
                    target_directory = "%s/%s" % (user_directory,wsname)
                else:                    
                    if libtype == 'None':
                        target_directory = "%s/%s/%s/%s" % (user_directory,project,variant,config)
                    else:
                        target_directory = "%s/%s/%s/%s/%s" % (user_directory,project,variant,libtype,config)
            else:
                LOGGER.error('Directory needs to be provided for mutable configuration')
                sys.exit(1)

            #append tag behind target directory path
            if tag:
                target_directory = "%s_%s" % (target_directory, tag)                    
                    
            temp_directory = "%s.TEMP%s" % (target_directory, os.environ['ARC_JOB_ID'])

            build_workspace(project, variant, libtype, config, temp_directory, default_headless_account, cfgfile, wsname)

            #if the target directory exist, remove that directory, otherwise we cannot rename our temp dir to target dir
            if os.path.isdir(target_directory):
                cmd = "rm -rf %s" % target_directory
                exitcode, stdout, stderr = run_command(cmd)
                if exitcode:
                    print_errors(cmd, exitcode, stdout, stderr)

            os.rename(temp_directory, target_directory)                

        #due to how altera_icm_release work to release data to /ice_rel/ by appending TEMP to workspace name
        #we have to remove TEMP away from cds.libicm since this file is created post sync trigger and takes in workspace name during creation
        fix_cds_libicm(target_directory)
   
        try:
            #similar to cdslib.icm, we have to fix saveworkspace json as well..
            fix_saveworkspace_json(target_directory)
        except:
            pass
 
        LOGGER.info("Content has been populated to: %s" % target_directory)
    elif command == "delete":
        user_directory = args.directory
        
        #fail-safe to ensure sion doesn't accidentally delete stuffs in release directory 
        if default_immutable_disk in os.path.abspath(user_directory):
            LOGGER.error("Sion cannot remove a directory from the official release directory.")
            sys.exit(1)

        #can only delete directories with .sion file
        #ensure that sion can delete only directory created by sion
        sion_file = "%s/.sion" % user_directory
        if not os.path.exists(sion_file):
            LOGGER.error("Please ensure the given path is a directory created via sion populate command")
            sys.exit(1)                            

        stat_info = os.stat(sion_file)
        uid = stat_info.st_uid
        owner = pwd.getpwuid(uid)[0]
        if owner != default_headless_account:
             LOGGER.error("It appears that .sion file in this directory is not created via sion populate. Please contact the tool administrator about this error.")
             sys.exit(1)
       
        cmd = "rm -rf %s" % user_directory
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)

        LOGGER.info("%s has been deleted." % user_directory)
    elif command == "list":
        project = None if args.project == 'None' else args.project
        variant = None if args.variant == 'None' else args.variant
        libtype = None if args.libtype == 'None' else args.libtype
        config = None if args.config == 'None' else args.config
        library = None
        props = None
        switches = None
        regex = None
        List(project, variant, libtype, library, config, switches, props, regex).run()
    elif command == "command":
        icm_command = " ".join(args.icm_command.split("=MaGiC="))

        LOGGER.info("%s" % icm_command)
        exitcode, stdout, stderr = run_command(icm_command)
        if exitcode or stderr:
            print(stderr)
        if stdout:            
            print(stdout)
    elif command == "printconfig":
        project = args.project
        variant = args.variant
        config = args.config            
        misc = args.misc
        show_simple_args, show_libraries_args = misc.split(',')
        show_simple = False
        if show_simple_args.split(":")[1] == 'True':
            show_simple = True
        show_libraries = False
        if show_libraries_args.split(":")[1] == 'True':
            show_libraries = True
        
        PrintConfig(project, variant, config, show_simple=show_simple, show_libraries=show_libraries).run()
    elif command == "diffconfigs":
        project = args.project
        variant = args.variant
        first_config = args.config            
        misc = args.misc
        second_config = misc.split(":")[1]
        
        DiffConfigs(project, variant, first_config, second_config, None, None, True).run()       
                           
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
    cmd = "icmp4 protects //depot/icm/proj/%s/icmrel/%s/ | grep group | egrep -i 'read|list' | tail -n1" % (project, variant)    
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
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
    cmd = "icmp4 protects //depot/icm/proj/%s/icmrel/ | grep group | egrep -i 'read|list' | tail -n1" % (project)    
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
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

def record_workspace_size(target_dir):
    '''
    Record workspace content sizes for analysis
    '''
    cmd = "du -sh %s" % target_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
    storage_file = open(storage_path, 'a')
    storage_file.write(stdout)
    storage_file.close()  

def build_workspace(project, variant, libtype, config, target_dir, user, configfile, wsname):
    #first, create workspace
    LOGGER.info("Creating workspace...")
    desc = "SITE: {} ARC_JOB: {}".format(os.environ['ARC_SITE'], os.environ['ARC_JOB_ID'])
    if libtype == 'None':
        cmd = 'pm workspace -c %s %s %s %s %s "%s"' % (project, variant, config, user, target_dir, desc)
    else:
        cmd = 'pm workspace -c -t %s %s %s %s %s %s "%s"' % (libtype, project, variant, config, user, target_dir, desc)
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)        
    m = re.match(r'Workspace (\S+) created', stdout or '')
    workspace = m.group(1)

    #next, sync workspace    
    LOGGER.info("Populating workspace...")
    #a little tricky for mutable config, we need to first perform skeleton sync on the workspace
    cmd = 'pm workspace -R %s' % workspace
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)  

    #set logging to file after workspace is created as logfile needs to live in workspace root
    LOGGER.handlers=[]
    logfile = '{}/.sion.log'.format(target_dir)
    logging.basicConfig(filename=logfile, 
                        filemode='w', 
                        format='-%(levelname)s-[%(module)s]: %(message)s', 
                        level=logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('-%(levelname)s-[%(module)s]: %(message)s')
    ch.setFormatter(formatter)
    LOGGER.addHandler(ch)

    #create a .sion file in each directory so that sion knows this directory is created via populate command
    dirs = [x[0] for x in os.walk(target_dir)]
    #need to append directory not covered by os.walk
    if not wsname:
        if libtype:
            # for libtype
            dirs.append("{}".format(os.path.dirname(target_dir)))
        # for variant
        dirs.append("{}".format((os.path.dirname(os.path.dirname(target_dir)))))
        # for project
        dirs.append("{}".format(os.path.dirname(os.path.dirname(os.path.dirname(target_dir)))))
                                    
    for dir in dirs:
        cmd = "touch %s/.sion" % dir
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)                                                  
    #then, to perform quick sync we need to chdir to the workspace dir
    os.chdir(target_dir)
    #now we can perform quick sync
    cfgfile = configfile            
    yes_to_all = True
    force = None
    preview = None

    # import from altera_abnr/3.4.4 as sion requires the latest update available in that resource        
    from dmx.abnrlib.flows.workspace import Workspace       
    sync = Workspace()
    try:
        sync.sync_action(cfgfile, yes_to_all, force, preview)
    except:
        # Due to the softlink issue with ICM, we have to perform sync twice
        sync.sync_action(cfgfile, yes_to_all, force, preview)        

    #chmod to 770 if not rel, otherwise 750
    if default_immutable_directory in target_dir:
        cmd = "chmod -R 750 %s" % target_dir
    else:        
        cmd = "chmod -R 770 %s" % target_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)        

    # ensure user cannot remove .sion file (needed for sion delete to work properly)
    for dir in dirs:
        cmd = "chmod 750 %s/.sion" % dir
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            print_errors(cmd, exitcode, stdout, stderr)
        
    #then, run saveworkspace        
    LOGGER.info("Running saveworkspace...")
    try:
        cmd = "saveworkspace --workspace %s" % target_dir
        exitcode, stdout, stderr = run_command(cmd)
        if libtype == 'None':
            cmd = "saveworkspace --workspace %s --every" % target_dir
            exitcode, stdout, stderr = run_command(cmd)
    except Exception as e:
        LOGGER.debug(e)
        pass

    # Do not remove workspace (DI221)
    '''
    #finally, remove workspace
    LOGGER.info("Cleaning up workspace...")
    cmd = 'pm workspace -R -x %s' % workspace
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)        
    '''

    # Modify workspace location to actual directory
    actual_dir = target_dir.split('.TEMP')[0]
    cmd = 'pm workspace -f %s %s' % (workspace, actual_dir)
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)        
    
def fix_saveworkspace_json(target_dir):
    cmd = "find %s -name info.json -maxdepth 3" % target_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
    jsons = stdout.split("\n")

    cmd = "find %s -name workspace.json -maxdepth 3" % target_dir
    exitcode, stdout, stderr = run_command(cmd)
    if exitcode:
        print_errors(cmd, exitcode, stdout, stderr)
    jsons = jsons + stdout.split("\n")
    
    tempname = ".TEMP" + os.environ['ARC_JOB_ID']        
    for json in jsons:
        if json:
            if not os.access(json,os.W_OK):       
                os.chmod(json,0o750)
            r = open(json)        
            lines = r.readlines()
            w = open(json, 'w')
            for line in lines:
                if tempname in line:
                    new_line = line.split(tempname)
                    w.write(''.join(new_line))
                else:
                    w.write(line)
            r.close()
            w.close()        
                           
def fix_cds_libicm(target_dir):
    cds = target_dir + "/cds.libicm"
    if not os.path.isfile(cds):
        return
    if not os.access(cds,os.W_OK):       
        os.chmod(cds,0o750)
    cds_reader = open(cds)
    lines = cds_reader.readlines()
    cds_writer = open(cds, 'w')

    tempname = ".TEMP" + os.environ['ARC_JOB_ID']
    for line in lines:
        if tempname in line:
            temp = line.split(tempname)
            cds_writer.write(''.join(temp))

    cds_reader.close()
    cds_writer.close()

def print_errors(cmd, exitcode, stdout, stderr):
    LOGGER.error("User = %s" % os.getenv('USER'))
    LOGGER.error("Hostname = %s" % os.getenv('HOSTNAME'))
    LOGGER.error("ARC Job ID = %s" % os.getenv('ARC_JOB_ID'))
    LOGGER.error("Command = %s" % cmd)
    LOGGER.error("Exitcode = %s" % exitcode)
    LOGGER.error("Stdout = %s" % stdout)
    LOGGER.error("Stderr = %s" % stderr)
    sys.exit(1)
        
if __name__ == "__main__":
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.INFO)
    sys.exit(main())
