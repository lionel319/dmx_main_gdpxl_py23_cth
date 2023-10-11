#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/ip.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: dmx "ip import" subcommand plugin

Author: Mitchell Conkin
Copyright (c) Intel Corporation 2019
All rights reserved.
'''
from __future__ import print_function
from builtins import next
from builtins import str
from builtins import object
import os
import subprocess

import dmx.utillib.utils
import dmx.abnrlib.icm
import dmx.utillib.eximport_utils
import logging
from dmx.abnrlib.flows.createconfig import CreateConfig
from dmx.abnrlib.flows.overlaydeliverable import OverlayDeliverable
from dmx.utillib.eximport_utils import get_config_file, parse_rules_file

def run_shell_command(cmd):
    """
    Run a shell command, ensure it worked, and return its result.
    getstatusoutput() maps stderr to stdout so we don't clutter up our xterm.
    Success if return of cmd is 0, otherwise raise RuntimeError.
    
    cmd exits normally.
    >>> run_shell_command("echo 'run normal'")
    'run normal'
    
    cmd exits abnormally.
    >>> run_shell_command("echo 'run error'; exit 1")
    Traceback (most recent call last):
        ...
    RuntimeError: Failed to execute 'echo 'run error'; exit 1'; return code: 1; output: 'run error'
    """
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = str(process.communicate(input)[0]).strip()
    return_code = process.poll()

    return (return_code, output)

class IPError(Exception): pass
logger = logging.getLogger(__name__)

class IP(object):
    '''
    Runner class to import a 3rd party IP into DMX
    '''


    @classmethod
    def migrate_to_dmx(self, project, ip, deliverables, format_file, source_bom, dest_bom):
        
        '''
        Read the conf file
        '''
        approved_mappings = []
        approved_generators = []

        source_path = os.getenv('WARD')
        if not source_path:
            print('ERROR: $WARD environment variable not defined')
            return

        os.putenv('SOURCE', source_path)

        for key, value in list(parse_rules_file(get_config_file('import', format_file, 'rules', 'conf')).items()):
            if key == 'MAPPINGS':
                approved_mappings = value

            elif key == 'GENERATORS':
                approved_generators = value

            else:
                value = str(value)
                os.putenv(key, value)
       
        '''
        Sanity check
        '''
        if deliverables: 
            for deliverable in deliverables:
                if deliverable not in approved_mappings and deliverable not in approved_generators:
                    print('ERROR: this deliverable is not defined in the configuration file')
                    print('Are you sure you meant to add this deliverable?')
                    return
            
        '''
        Clone the bom if it does not exist
        '''
        migrate_root = '/nfs/site/disks/psg_dmx_1/ws'

        icm = dmx.abnrlib.icm.ICManageCLI()
        if not icm.config_exists(project, ip, dest_bom):

            family = os.getenv("DB_FAMILY")
            dev = dmx.utillib.utils.get_default_dev_config(family, icmproject=project)

            # @TODO: is there a flows/ api for bom clone? 
            #        would be much faster than fork/exec
            subprocess.check_output('dmx bom clone -p ' + project + ' -i ' + ip + ' -b ' + dev + ' --dstbom ' + dest_bom, shell=True)  

        wsname = ''
        ws = ''
        ws_new = False
        try:
            wsname = icm.add_workspace(project, ip, dest_bom, dirname=migrate_root, ignore_clientname=False)

        except dmx.abnrlib.icm.ICManageError as e:
            icmworkspace = dmx.dmlib.ICManageWorkspace.ICManageWorkspace(workspacePath=ws)
            wsname = icmworkspace.workspaceName
            ws_new = True
        
        icm.sync_workspace(wsname, skeleton=True)
        ws = os.path.join(migrate_root, wsname)
        os.chdir(ws)
        
        os.putenv('DEST', ws + '/' + ip )
        if deliverables:
            for deliverable in deliverables:
                self.run_mappers_and_generators(project, ip, deliverable, format_file, approved_generators, dest_bom, ws)
        
        else:
            for deliverable in approved_mappings:
                self.run_mappers_and_generators(project, ip, deliverable, format_file, approved_generators, dest_bom, ws)

        '''
        Cleanup
        '''
        if ws_new:
            icm.del_workspace(wsname)

    @classmethod
    def run_mappers_and_generators(self, project, ip, deliverable, format_file, approved_generators, dest_bom, ws):
        mapping = get_config_file('import', format_file, deliverable, 'mapping')
        os.system(mapping)

        if deliverable in approved_generators:
            generator = get_config_file('import', format_file, deliverable, 'generator')
            os.system(generator)

        # @TODO: is there an api here as well?
        #        replacing with api will be better 
        #        here

        overlay = OverlayDeliverable(project, ip, deliverable, None, None, preview=False)
        overlay.run()
         
        return

    @classmethod
    def get_all_format_name(self):
        result = dmx.utillib.eximport_utils.get_format_name('import')
        logger.info('Available format name for import: {}'.format(result))
    
    @classmethod
    def package_for_release(self, project, ip, dest_bom, stage):

        ward = os.getenv("WARD")
        if not ward:
            ward = os.getenv("WORKAREA")

        if not stage:
            stage = 'be_package_release'

        # check if reldoc is there
        (ret,dmxws)  = run_shell_command("ls -d {}/psg/*".format(ward))
        if(ret):
            raise IPError("dmx workspace not found in {}/psg".format(ward))
        
        if "\n" in dmxws:
            raise IPError("-E- More than 1 workspace found")

        # @TODO: hook into dmx api
        cells = os.path.join(dmxws, ip, 'ipspec', 'cell_names.txt')
        if not os.path.exists(cells):
           raise IPError("no cells were defined")
        
        all_pass = 0
        error = 0
        os.environ["IP_PACKAGE_VARIANT"] = ip
        cell = 'CELL'
        dmx_package = "{}/common/icmadmin/prod/icm_home/scripts/dmx_package.py".format(os.getenv("PSG_FLOWS"))
        check_in = "{} -i {} -c {} -s {} -ci".format(dmx_package,ip,cell,stage)
        revert   = "{} -i {} -c {} -s {} -r".format(dmx_package,ip,cell,stage)

        for cell in open(cells, 'r').read().split('\n'):
            if not cell:
                 continue

            os.environ["IP_PACKAGE_VARIANT"] = ip
            os.environ["IP_PACKAGE_CONFIG"] = dest_bom
            os.environ["IP_PACKAGE_TOPCELL"] = cell
            packagefile  = os.path.join(os.getenv("DMXDATA_ROOT"), os.getenv("DB_FAMILY").capitalize(), 'package', stage, 'package.tcsh')
            #print command
            if not os.path.exists(packagefile):
                raise IPError("'{}' is not a valid stage. Valid stages are:\n{}".format(stage, self.get_all_stage_name()))
            #print subprocess.check_output(command, shell=True)

            command = "{}/common/icmadmin/prod/icm_home/scripts/dmx_package.py -i {} -c {} -s {}".format(os.getenv("PSG_FLOWS"),ip,cell,stage)
            logger.info("Running {}".format(command))
            (ret,out) = run_shell_command(command)

            if(ret):
                logger.info("dmx_package.py encountered some error")
                error = out

                # if error, revert dmx_package.csv file
                logger.info("-I- reverting dmx_package.csv")
                logger.info(revert)
                try:
                    print(subprocess.check_output(revert, shell=True))
                except subprocess.CalledProcessError as e:
                    print(e.output)
                raise IPError(error)

                return(ret)
            else:
                logger.info(out)

        # if no error during the process
        logger.info("-I- checking in dmx_package.csv")
        logger.info(check_in)
        try:
            print(subprocess.check_output(check_in, shell=True))
        except subprocess.CalledProcessError as e:
            raise IPError(e.output)
            

    @classmethod
    def get_all_stage_name(self):
        return next(os.walk(os.path.join(os.environ.get('DMXDATA_ROOT'), os.environ.get('DB_FAMILY').capitalize(), 'package')))[1]

    @classmethod
    def unpackage(self, project, ip, cell, bom, stage):

        ward = os.getenv("WARD")
        if not ward:
            ward = os.getenv("WORKAREA")

        if not stage:
            stage = 'be_package_release'

        # check if reldoc is there
        (ret,dmxws)  = run_shell_command("ls -d {}/psg/*".format(ward))
        if(ret):
            raise IPError("dmx workspace not found in {}/psg".format(ward))
        
        if "\n" in dmxws:
            raise IPError("-E- More than 1 workspace found")

        # @TODO: hook into dmx api
        cells = os.path.join(dmxws, ip, 'ipspec', 'cell_names.txt')
        if not os.path.exists(cells):
           raise IPError("no cells were defined")
           
        for cell in open(cells, 'r').read().split('\n'):
            if not cell:
                 continue
            try:
                command = os.path.join(os.getenv("DMXDATA_ROOT"), os.getenv("DB_FAMILY").capitalize(), 'unpackage', 'test_unpackage.py')
                print(subprocess.check_output("{} -s {} -i {} -c {} -t {}".format(command, stage, ip, cell, bom), shell=True))
            except subprocess.CalledProcessError as e:
                raise IPError(e.output)


