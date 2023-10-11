#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/propagate.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr "propagate" subcommand plugin
Author: Tara Clark
Copyright (c) Intel Corporation
'''
from __future__ import print_function

from builtins import str
from builtins import object
import logging
import os
import sys
import glob
import shutil
import re
import time

from dmx.abnrlib.icm import ICManageCLI
from dmx.utillib.utils import get_abnr_id, format_configuration_name_for_printing, split_pvlc, run_command 
from dmx.abnrlib.icmcompositeconfig import CompositeConfig
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.icmsimpleconfig import SimpleConfig
from dmx.abnrlib.flows.releasetree import ReleaseTree
from dmx.abnrlib.flows.edittree import EditTree
from dmx.abnrlib.releaseinputvalidation import validate_inputs
LOGGER = logging.getLogger(__name__)

def check_dmz_version():
    DMZ_PATH = os.environ['ALTERA_DMZ_ROOT']  
    version =  DMZ_PATH.split('/')[-1]
    if version < '1.12':
        LOGGER.error('Propagate requires altera_dmz resource to be at least version 1.12')
        LOGGER.error('Current altera_dmz version {}'.format(version))
        return False
    return True            

class PropagateError(Exception): pass

class Propagate(object):
    '''
    Runner subclass for the abnr propagate command
    '''

    def __init__(self, project, variant, config, replace_config, path, 
                 remove=False,
                 release_config=False, milestone=None, 
                 thread=None, label=None, description=None, 
                 preview=True):
        self.project = project
        self.variant = variant       
        self.replace_config = replace_config
        self.path = path
        self.remove = remove
        self.release_config = release_config
        self.workspace = ''
        self.milestone = milestone
        self.thread = thread
        self.label = label
        self.description = description
        self.preview = preview
        self.waiver_files = []

        self.LOGGER = LOGGER
        self.cli = ICManageCLI()

        if not check_dmz_version():
            raise PropagateError('Please ensure altera_dmz resource of at least version 1.12 is loaded.')

        if not self.cli.project_exists(self.project):
            raise PropagateError("Project {0} does not exist".format(self.project))
        
        if not self.cli.variant_exists(self.project, self.variant):
            raise PropagateError("Variant {0} does not exist in project {1}".format(self.variant, self.project))

        self.rep_simple = []
        for pvlc in self.replace_config:
            try:
                p,v,l,c = split_pvlc(pvlc) 
            except:   
                raise PropagateError('{} is not in a valid project/variant:libtype@config format.'.format(pvlc)) 
            if not self.cli.config_exists(p, v, c, libtype = l):
                raise PropagateError('Config {} does not exist for {}/{}:{}'.format(c,p,v,l))
            self.rep_simple.append(['{}/{}:{}'.format(p,v,l),c])                
                 
        if not os.path.isdir(self.path):
            raise PropagateError('Directory {0} does not exist'.format(self.path))
        
        # if release_config is specified, ensure that milestone,thread,description are given
        if self.release_config:
            if not description:
                raise PropagateError('Description is not given. Please provide a description for release')
            
            # As long as check passes for propagate, every error is to be waived in TNR
            # Create a waiver.csv with all wildcards
            waiver_file = '{}/waiver.csv'.format(os.getcwd())
            with open(waiver_file, 'w') as f:
                waivers = ['*', '*', '*', 'Waived by quick propagate', '*']
                f.write(','.join(waivers))
            self.waiver_files.append(waiver_file)                

            # Common release input validation
            validate_inputs(self.project, self.milestone, self.thread, self.label,
                            self.waiver_files, production=True)            
            
        self.config = ConfigFactory.create_from_icm(self.project, self.variant, config,
                                                    preview=True)

    def run_dmzIntfcLibChk(self, filename):
        ''' Run the check on one file'''
        status = 'FAIL'
        error = ''
        command = 'dmzIntfcLibChk -auditfile {}'.format(filename)
        self.LOGGER.debug('Running {}'.format(command))

        (exitcode, stdout, stderr) = run_command(command)
        output = stdout.splitlines() + stderr.splitlines()

        # *PASS* means okay to-release; *FAIL* means fail.
        for line in output:
            m = re.match('.*\*(PASS|FAIL|FAILED)\*.*', line)
            if m:                
                status = m.group(1)
                if status != 'PASS':
                    for line2 in output:
                        m = re.match('.*ERROR: (.*)', line2)
                        if m:
                            error = m.group(1)                                    
                            break
                break                        
           
        return (status, error)

    def check_dmz_audit_files(self, workspace_root, variant, libtype):
        '''
        Go into the temporary workspace and look for all the dmz audit files for this IP.  We need to look in
        the libtypes complib, complibphys and netlist, but don't include incfclib audit file.
        The audit files look like audit.cell.dmzcomplib.dmzblockbinder.xml

        Run the dmzIntfcLibCheck on each one.

        :param variant: The IP we're processing
        :type variant: string
        :return check_passed: boolean
        '''

        # Get this IP's root
        libtype_dir = '{}/{}/{}'.format(workspace_root, variant, libtype)
        results = []

        if os.path.isdir(libtype_dir) and os.path.isdir(os.path.join(libtype_dir, "audit")):
            audit_dir = '{}/{}'.format(libtype_dir, "audit")
            os.chdir(audit_dir)
            
            audit_files = glob.glob("*.dmzblockbinder.xml")
            
            for audit_file in audit_files:
                status, error = self.run_dmzIntfcLibChk(audit_file) 
                if 'FAIL' in status:
                    results.append((audit_file, error))

        return results

    def release_config_via_releasetree(self):
        releasetree = ReleaseTree(self.project, self.variant, self.new_config.config, self.milestone,
                                  self.thread, self.description, label=self.label, required_only=False, 
                                  intermediate=False, 
                                  waiver_files=self.waiver_files, force=False,
                                  preview=self.preview)
        releasetree.run()

        # If successfully reached here, it means that REL is successfully created, remove staging config and workspace
        self.remove = True

    def print_progressbar(self, index, total):
        sys.stdout.write('\r')
        sys.stdout.write("[%-20s] %d%%" % ('='*int(index/total*20), int(index/total*100)))
        sys.stdout.flush()
        if index == total:
            print('')

    def run(self):
        '''
        Runs the Propagate runner
        '''
        ret = 1
        
        '''
        Propagate flow as follows:
        1. Clone source config into a new config
        2. Replace the configurations in the new config with the ones given by user
        3. Create a workspace based on the new config
        4. Runs dmzlibcheck on all netlist, complib and complibphys in the workspace
        5. If there are errors, error out and print the errors
        6. If no errors, attempt to release new config via releasetree 
        '''

        # Replace config via edittree
        timestamp = str(time.time()).replace('.', '')
        user = os.environ['USER']
        new_config = 'propagate_{}_{}'.format(user, timestamp)
        
        self.LOGGER.info('Cloning source config {} to staging config {}'.format(self.config, new_config))
        runner = EditTree(self.project, self.variant, self.config.config, new_config=new_config,
                          rep_simple=self.rep_simple, preview=self.preview)
        runner.run()
                
        self.new_config = ConfigFactory.create_from_icm(self.project, self.variant, new_config)   

        # Capture the original working directory so we can cd
        # back to it when we're done
        original_wd = os.getcwd()

        try:       
            # add a workspace
            self.LOGGER.info('Creating workspace...')
            self.workspace = self.cli.add_workspace(self.project, self.variant, self.new_config.config, dirname = self.path)
            workspace_root = "{0}/{1}".format(self.path, self.workspace)
            self.LOGGER.info('Workspace {} created'.format(workspace_root))
    
            # syncs only audit xmls 
            self.LOGGER.info('Syncing workspace...')
            specs = ['*/*/audit/...', '*/ipspec/...', '....dmz']
            self.cli.sync_workspace(self.workspace, skeleton = False, specs = specs)

            # cd into workspace root
            os.chdir(workspace_root)
    
            self.LOGGER.info('Checking for dmz audit files...')
            libtypes_to_check = [x for x in self.new_config.flatten_tree() if x.is_simple() and (x.libtype == 'netlist' or x.libtype == 'complib' or x.libtype == 'complibphys')]

            failed = []
            for index, libtype in enumerate(libtypes_to_check):
                self.print_progressbar(index+1, len(libtypes_to_check))
                results = self.check_dmz_audit_files(workspace_root, libtype.variant, libtype.libtype)
                if results:
                    failed.append((libtype.project, libtype.variant, 
                                   libtype.libtype, libtype.config, results))

            if failed:
                print('The following project/variant:libtypes failed dmzIntfcLibChk:')
                for project, variant, libtype, config, results in sorted(failed):
                    print('{}/{}:{}@{}'.format(project, variant, libtype, config))
                    for index, (audit, error) in enumerate(results):
                        print('\t{}. Audit: {}'.format(index+1, audit))
                        print('\t{}. Error: {}'.format(index+1, error))

                print('\nThe following project/variant:libtypes failed dmzIntfcLibChk:')
                for project, variant, libtype, config, results in sorted(failed):
                    print('{}/{}:{}@{}'.format(project, variant, libtype, config))                        

                if not self.remove:
                    self.LOGGER.info('You may check the errors and source files in this workspace created by propagate: {}'.format(workspace_root))
                    self.LOGGER.info('You may use this staging config {} created by propagate to aid you in fixing the errors.'.format(self.new_config))

            else:
                if self.release_config:
                    self.LOGGER.info('No errors found.')
                    self.LOGGER.info('Attempting to release {}/{}@{} via abnr releasetree...'.format(self.project, self.variant, self.new_config.config))
                    self.release_config_via_releasetree()
                else:                    
                    print('No errors found. You may now release the configuration {} via abnr releasetree'.format(self.new_config.config))     

            ret = 0
        except Exception as e:
            self.LOGGER.error(e)
            raise
        finally:
            if self.remove:
                self.LOGGER.info('Removing workspace...')
                self.cli.del_workspace(self.workspace, preserve=False)
                if os.path.exists('%s/%s' % (self.path, self.workspace)):
                    shutil.rmtree("%s/%s" % (self.path, self.workspace))

                self.LOGGER.info('Removing staging configuration...')
                configs_to_remove = list(set(self.new_config.search(name=self.new_config.config)))
                while configs_to_remove:
                    config = configs_to_remove.pop()
                    try:
                        self.cli.del_config(config.project, config.variant, config.config)
                    except:
                        configs_to_remove.insert(0, config)

            # Remove waiver files
            if self.waiver_files:
                for file in self.waiver_files:
                    os.remove(file)                        

            # cd back to the original working directory
            if original_wd:
                os.chdir(original_wd)
        
        return ret
