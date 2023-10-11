#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/overlaydeliverable.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr "createsnapshot" subcommand plugin
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
import os
import re
import sys
import logging
import textwrap
import datetime
import glob
import shutil

from dmx.abnrlib.icm import ICManageCLI
import dmx.ecolib.ecosphere
#from dmx.abnrlib.icmsimpleconfig import SimpleConfig
from dmx.abnrlib.icmlibrary import IcmLibrary 
from dmx.utillib.utils import format_configuration_name_for_printing, is_pice_env, run_command, force_revert_files_by_filespec, login_to_icmAdmin
from dmx.abnrlib.config_factory import ConfigFactory
import dmx.abnrlib.scm
from dmx.utillib.arcenv import ARCEnv
import dmx.abnrlib.workspace

# This information should live in family.json in the future, leave it here for now
SCRATCH_AREA = '/nfs/site/disks/psg_dmx_1/ws'

class OverlayDeliverableError(Exception): pass

class OverlayDeliverable(object):
    '''
    Class to control running the createsnapshot command
    '''

    def __init__(self, project, variant, libtype, source_config, dest_config, cells=[], directory=None, preview=True, desc='', forcerevert=False, shared_wsroot=None, filespec=None):
        self.filespec = filespec
        self.project = project
        self.preview = preview
        self.desc = desc
        self.forcerevert = forcerevert
        self.cli = ICManageCLI(preview=preview)
        self.logger = logging.getLogger(__name__)
        # Switch to indicate if command is running in local or remote mode
        # By default, remote mode. Remote mode means command works on depot only
        # Local mode means command works on workspace locally
        self.is_local = False
        self.staging_wsname = 'dummy'   ### set a dummy name so that command won't fail
       
        # https://jira.devtools.intel.com/browse/PSGDMX-2843
        self.shared_wsroot = shared_wsroot

        if not is_pice_env():
            raise OverlayDeliverableError('dmx overlay is only supported for PICE at the moment')
        
        # Make sure cells are either a list of cells or a single filelist if cells are provided
        if cells:
            # If only a single value is found in cells, it could be a filelist or cell
            if len(cells) == 1:
                # If a dot is found, treat it as a file
                if '.' in cells[0]:
                    m = re.match('(.*)\.(.*?)$', cells[0])
                    if m:
                        filelist = m.group(1)
                        extension = m.group(2)
                    else:                        
                        raise OverlayDeliverableError('Error reading file extension of {}'.format(cells[0]))
                    # Filelist must end with .txt
                    if extension == 'txt':
                        filelist_path = os.path.abspath(cells[0])
                        if os.path.exists(filelist_path):
                            # Cells must be separated by lines
                            # Comment must begin with either '#' or '//'
                            with open(filelist_path) as f:
                                celllist = [x.strip() for x in f.readlines() if not x.startswith('#') and not x.startswith('//') and x]
                                for cell in celllist:
                                    m = re.match('^\w*$', cell)
                                    if not m:
                                        raise OverlayDeliverableError('Cell must contain only alphabets, numbers or underscores: {}'.format(cell))
                                self.cells = celllist
                        else:
                            raise OverlayDeliverableError('Filelist {} does not exist'.format(filelist_path))
                    else:
                        # Any other extension is not allowed
                        raise OverlayDeliverableError('Only file that ends with .f is allowed to be provided as filelist')
                else:
                    # If it's not a file, treat as cells
                    self.cells = cells
            elif len(cells) > 1:
                # If multiple values are found in cells, treat them all as cells
                # no combination of filelist and cells are allowed
                for cell in cells:
                    # If dot is found in cell, assume it's a file, and it's not allowed
                    if '.' in cell:
                        raise OverlayDeliverableError('File {} cannot be provided together with cells'.format(cell))
                self.cells = cells
            else:
                self.cells = cells                
        else:
            self.cells = []

        # Lower all characters and remove blanks
        self.cells = [x.lower() for x in self.cells if x]                

        '''
        http://pg-rdjira:8080/browse/DI-948
        1. IP@BoM:DEL => -i IP -b BoM -d DEL
        2. IP:DEL@BoM => -i IP:DEL -b BoM
        3. IP@BoM:DEL:SLICE => -i IP -b BoM -d DEL:SLICE
        4. IP:DEL@BoM:SLICE => -i IP:DEL -b BoM -d SLICE
        '''
        if ':' in variant:
            # This section handles item 2 and 4
            # -i IP:DELIVERABLE mode, BOM is treated as libtype configuration
            self.variant, self.libtype = variant.split(':')
            # If project not given, get project from IP
            if not self.project:
                self.logger.info('Reading from ARC environment')
                arc_projects = ARCEnv().get_project()
                for arc_project in arc_projects:
                    if self.cli.variant_exists(arc_project, self.variant):
                        self.project = arc_project
                        break
                if not self.project:
                    raise OverlayDeliverableError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
            else:
                # Make sure the project exists
                if not self.cli.project_exists(self.project):
                    raise OverlayDeliverableError("{0} is not a valid project".format(self.project))
                # Make sure the variant exist
                if not self.cli.variant_exists(self.project, self.variant):
                    raise OverlayDeliverableError("{0}/{1} is not a valid variant".format(self.project, self.variant))
            self.family = dmx.ecolib.ecosphere.EcoSphere().get_family(os.getenv("DB_FAMILY"))

            # If -d is provided, it will be treated as slice
            if libtype:
                self.slice = libtype
            else:
                self.slice = None 
            # Make sure the libtype exist
            if not self.cli.libtype_exists(self.project, self.variant, self.libtype):
                raise OverlayDeliverableError("{0}/{1}:{2} is not a valid libtype".format(self.project, self.variant, self.libtype))
            if self.slice:
                # Make sure slice is valid
                self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype).get_slice(self.slice)                                                                                   
            self.source_config = source_config
            self.dest_config = dest_config                
            self.use_local_ws_as_staging = False
        else:
            # This section handles item 1 and 3
            # -i IP mode, BOM is treated as variant configuration
            self.variant = variant      
            # If project not given, get project from IP
            if not self.project:
                self.logger.info('Reading from ARC environment')
                arc_projects = ARCEnv().get_project()
                for arc_project in arc_projects:
                    if self.cli.variant_exists(arc_project, self.variant):
                        self.project = arc_project
                        break
                if not self.project:
                    raise OverlayDeliverableError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
            else:
                # Make sure the project exists
                if not self.cli.project_exists(self.project):
                    raise OverlayDeliverableError("{0} is not a valid project".format(self.project))
                # Make sure the variant exist
                if not self.cli.variant_exists(self.project, self.variant):
                    raise OverlayDeliverableError("{0}/{1} is not a valid variant".format(self.project, self.variant))
            self.family = dmx.ecolib.ecosphere.EcoSphere().get_family(os.getenv("DB_FAMILY"))

            if not libtype:
                raise OverlayDeliverableError("Deliverable (-d) to be overlay'ed needs to be provided.")
            if ':' in libtype:
                self.libtype, self.slice = libtype.split(':')
            else:
                self.libtype = libtype
                self.slice = None    
            # Make sure the libtype exist
            if not self.cli.libtype_exists(self.project, self.variant, self.libtype):
                raise OverlayDeliverableError("{0}/{1}:{2} is not a valid libtype".format(self.project, self.variant, self.libtype))
            if self.slice:
                # Make sure slice is valid
                self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype).get_slice(self.slice)                                  
                             
            # Look for source libtype config in IP@BOM
            if source_config:
                source_variant_config = ConfigFactory.create_from_icm(self.project, self.variant, source_config)
                results = source_variant_config.search(project='^{}$'.format(self.project),
                                                       variant='^{}$'.format(self.variant),
                                                       libtype='^{}$'.format(self.libtype))
                if len(results) == 1:
                    [library, release] = self.cli.get_library_release_from_libtype_config(self.project, self.variant, self.libtype, source_config)
                    self.source_config = library
                elif len(results) == 0:
                    raise OverlayDeliverableError('BOM for {} is not found in {}/{}@{}'.format(self.libtype, self.project, self.variant, source_config))
                else:
                    raise OverlayDeliverableError('More than one BOM for {} found in {}/{}@{}'.format(self.libtype, self.project, self.variant, source_config))
            else:
                self.source_config = None

            self.use_local_ws_as_staging = False
            if dest_config:
                # Look for dest libtype config in IP@BOM
                dest_variant_config = ConfigFactory.create_from_icm(self.project, self.variant, dest_config)
            else:
                self.use_local_ws_as_staging = True
                self.ws = dmx.abnrlib.workspace.Workspace()
                dest_variant_config = ConfigFactory.create_from_icm(self.project, self.variant, self.ws._bom)
            results = dest_variant_config.search(project='^{}$'.format(self.project),
                                                 variant='^{}$'.format(self.variant),
                                                 libtype='^{}$'.format(self.libtype))

            if len(results) == 1:
                self.dest_config = results[0].library.split('/')[-1]
            elif len(results) == 0:
                raise OverlayDeliverableError('BOM for {} is not found in {}/{}@{}'.format(self.libtype, self.project, self.variant, dest_config))
            else:
                raise OverlayDeliverableError('More than one BOM for {} found in {}/{}@{}'.format(self.libtype, self.project, self.variant, dest_config))


        # Make sure dest config exist            
        if not self.cli.config_exists(self.project, self.variant, self.dest_config, libtype=self.libtype):
            raise OverlayDeliverableError("Configuration {0} does not exist in {1}/{2}:{3}".format(
                self.dest_config, self.project, self.variant, self.libtype))
        self.dest_config_object = ConfigFactory.create_from_icm(self.project, self.variant, self.dest_config, libtype=self.libtype)
        # Make sure dest library is activedev
        if not self.dest_config_object.is_active_dev():
            raise OverlayDeliverableError("Dest BOM {0}@{1} is using a released library".format(
                self.libtype, self.dest_config))

        if self.source_config:
            # Copy files from source config to dest config
            # Make sure source and dest configs are different
            if self.source_config == self.dest_config:
                raise OverlayDeliverableError("Source BOM {0}@{1} must be different from dest BOM {0}@{2}".format(self.libtype, self.source_config, self.dest_config))
            
            # Make sure source config exist            
            if not self.cli.config_exists(self.project, self.variant, self.source_config, libtype=self.libtype):
                raise OverlayDeliverableError("Configuration {0} does not exist in {1}/{2}:{3}".format(
                    self.source_config, self.project, self.variant, self.libtype))
            # Make sure source and dest configs have different libraries
            self.source_config_object = ConfigFactory.create_from_icm(self.project, self.variant, self.source_config, libtype=self.libtype)
            if self.source_config_object.library == self.dest_config_object.library:
                raise OverlayDeliverableError("Source BOM {0}@{1} must have different library from dest BOM {0}@{2}".format(
                    self.libtype, self.source_config, self.dest_config))
        else:
            # Copy files from workspace to dest config
            # http://pg-rdjira:8080/browse/DI-1425        
            # https://wiki.ith.intel.com/display/tdmaInfra/dmx+scm+ci+%28enhanced%29+-+Phase+1
            # new overlay mode to support overlaying files in a workspace to icmanage
            cwd = os.getcwd()
            self.ws = dmx.abnrlib.workspace.Workspace(cwd)
            # This is a local mode that works on a workspace
            self.is_local = True
            self.project = self.ws.get_project_of_ip(self.variant)
            self.family = dmx.ecolib.ecosphere.EcoSphere().get_family(os.getenv("DB_FAMILY"))

            # Ensure that IP is valid
            if self.variant not in self.ws.get_ips():
                raise OverlayDeliverableError('IP {} is not part of workspace'.format(self.variant))
            # Ensure that deliverable is valid
            if self.libtype not in self.ws.get_deliverables_for_ip(self.variant):
                raise OverlayDeliverableError('Deliverable {}/{} is not part of workspace'.format(self.variant, self.libtype))

        # If directory is given, check that it's valid            
        # Else use the scratch_disk provided
        if directory:
            if os.path.isdir(directory):
                self.directory= os.path.realpath(directory)
            else:
                raise OverlayDeliverableError('{} is not a valid directory'.format(directory))
        else:
            self.directory = os.path.realpath(SCRATCH_AREA)

        # https://jira01.devtools.intel.com/browse/PSGDMX-21
        # Check if deliverable is part of roadmap
        try:
            delobj = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype)
        except Exception as e:
            raise OverlayDeliverableError('Failed to overlay, deliverable {} is no longer part of roadmap.\n{}'.format(self.libtype, str(e)))


    def run(self):
        '''
        Runs the command
        '''

        ### Regardless of whether the job pass/fail, we stil wanna do the clean up, ie:-
        ### - deleted the stanging workspace.
        ### https://jira.devtools.intel.com/browse/PSGDMX-1697
        ret = 1
        try:
            if self.is_local:
                ret = self.overlay_workspace_to_depot()
            else:
                ret = self.overlay_depot_to_depot()

            return ret
       
        except Exception as e:
            self.logger.error(str(e))
            self.qos_layer(str(e))

        finally:
            self.logger.debug("=== Post Cleanup ===")
            if self.shared_wsroot:
                self.logger.info("--shared-wsroot is used. Skipping cleanup process.")
            else:
                try:
                    if self.cli.workspace_exists(self.staging_wsname):
                        os.system('pm workspace -F -x {} >& /dev/null &'.format(self.staging_wsname))
                except:
                    pass
            return ret

    
    def overlay_workspace_to_depot(self):
        ret = 1
        user = os.getenv('USER')                           
        date = datetime.datetime.today()
                 
        dest_depotpath = self.dest_config_object.get_bom(p4=True)[0].split('@')[0]
        # Get base dest depotpath
        # Example: //depot/icm/proj/i10socfm/liotest2/rtl/dev/...
        # base_source_depotpath = //depot/icm/proj/i10socfm/liotest2/rtl/dev/
        # source_changelist = 9729893                
        m = re.match('(.*?)\.\.\.', dest_depotpath)
        if m:
            base_dest_depotpath = m.group(1)
        else:
            raise OverlayDeliverableError('Fail to get base_dest_depotpath from {}'.format(dest_depotpath))

        if self.cli.get_libtype_type(self.libtype) == 'DFII':
            # If libtype is a Cadence (DFII) type, regex string is variant/libtype/variant/...
            regex_pattern = '{}/{}/{}/(.*)'.format(self.variant, self.libtype, self.variant)
        else:
            # If libtype is a Cadence (DFII) type, regex string is variant/libtype/...
            regex_pattern = '{}/{}/(.*)'.format(self.variant, self.libtype)

        source_dest_path = []
        if self.cells:            
            for cell in self.cells:
                if self.slice:
                    # If cells provided and deliverable is slice, copy files recorded in slices.json
                    # Find all paths for all patterns
                    patterns = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype).get_slice(self.slice).get_patterns(ip=self.variant, cell=cell)
                    # Find all paths for all filelists
                    filelists = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype).get_slice(self.slice).get_filelists(ip=self.variant, cell=cell)
                else:
                    # If cells provided and deliverable is not a slice, copy files recorded in manifest.json
                    # Find all paths for all patterns
                    patterns = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype).get_patterns(ip=self.variant, cell=cell)
                    # Find all paths for all filelists
                    filelists = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype).get_filelists(ip=self.variant, cell=cell)

                # Find depot path that correspond to each pattern
                for pattern in patterns:
                    m = re.match(regex_pattern, pattern)
                    if m:
                        dest_path = '{}{}'.format(base_dest_depotpath, m.group(1))
                        source_dest_path.append((pattern, dest_path))

                # Find depot path that correspond to each filelist
                for filelist in filelists:
                    m = re.match(regex_pattern, filelist)
                    if m:
                        dest_path = '{}{}'.format(base_dest_depotpath, m.group(1))
                        source_dest_path.append((filelist, dest_path))
        else:
            if self.slice:
                # If no cells provided and deliverable is a slice, copy files recorded in slices.json
                # Find all paths for all patterns
                # Replace cell_name with * since no cells are provided
                patterns = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype).get_slice(self.slice).get_patterns(ip=self.variant, cell='*')
                # Find all paths for all filelists
                filelists = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype).get_slice(self.slice).get_filelists(ip=self.variant, cell='*')
                # Find depot path that correspond to each pattern
                for pattern in patterns:
                    m = re.match(regex_pattern, pattern)
                    if m:
                        dest_path = '{}{}'.format(base_dest_depotpath, m.group(1))
                        source_dest_path.append((pattern, dest_path))

                # Find depot path that correspond to each filelist
                for filelist in filelists:
                    m = re.match(regex_pattern, filelist)
                    if m:
                        dest_path = '{}{}'.format(base_dest_depotpath, m.group(1))
                        source_dest_path.append((filelist, dest_path))
            else:                
                # If no cells provided and deliverable is not slice, copy everything without referring to manifest
                pattern = regex_pattern.replace('(.*)', '...')
                source_dest_path.append((pattern, dest_depotpath))

        # Ensure no files are opened on dest path                
        # http://pg-rdjira:8080/browse/DI-975
        opened_path = []
        for source_path, dest_path in source_dest_path:
            command = 'xlp4 opened -a {}'.format(dest_path)
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                err_msg = 'Command: {}\n \
                           Exitcode: {}\n \
                           Stdout: {}\n \
                           Stderr: {}\n \
                        '.format(command, exitcode, stdout, stderr)
                raise OverlayDeliverableError(err_msg)
            if stdout:
                opened_path.append(dest_path)    
            # current gdpxl dont hhave distributed setup
            '''
            command = 'xlp4 opened -x {}'.format(dest_path)
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                err_msg = 'Command: {}\n \
                           Exitcode: {}\n \
                           Stdout: {}\n \
                           Stderr: {}\n \
                        '.format(command, exitcode, stdout, stderr)
                raise OverlayDeliverableError(err_msg)
            if stdout:
                opened_path.append(dest_path)
            '''
        if opened_path:
            opened_path = list(set(opened_path))
            self.logger.error('Files are opened in:')
            for path in opened_path:
                self.logger.error('* {}'.format(path))
            if not self.forcerevert:
                self.logger.error("Please run the following 2 command for each of the above opened path to get what/who opened files:-")
                self.logger.error("> xlp4 opened -a <opened_path>")
                self.logger.error("> xlp4 opened -x <opened_path>")
                raise OverlayDeliverableError('Overlay aborted. Please ensure that there are no opened files in the destination library') 
            else:
                self.try_to_force_revert_opened_files(opened_path)

        delobj = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype)
        is_large = delobj.large
        large_excluded_ip = delobj.large_excluded_ip


        if self.use_local_ws_as_staging:
            workspaceroot = self.ws._workspaceroot
            self.logger.debug('Using local workspace as staging workspace.')
            self.logger.debug('Staging workspace = {}'.format(workspaceroot))
            os.chdir(workspaceroot)
        else:
            if is_large and self.variant not in large_excluded_ip:
                # Create the workspace even in preview mode as scm requires an actual workspace to run even in preview mode
                self.cli.preview = False
                # Create a workspace with dest config
                wsname = self.cli.add_workspace(self.project, self.variant, self.dest_config, dirname=self.directory, libtype=self.libtype)
                self.staging_wsname = wsname
                workspaceroot = '{}/{}'.format(self.directory, wsname)
                self.logger.debug('Staging workspace = {}'.format(workspaceroot))
                # Skeleton-sync workspace 
                self.cli.sync_workspace(wsname, skeleton=False)
                os.chdir(workspaceroot)
            else:
                # Create a workspace with dest config
                wsname = self.cli.add_workspace(self.project, self.variant, self.dest_config, dirname=self.directory, libtype=self.libtype)
                self.staging_wsname = wsname
                workspaceroot = '{}/{}'.format(self.directory, wsname)
                self.logger.debug('Staging workspace = {}'.format(workspaceroot))
                # Skeleton-sync workspace 
                if not self.preview:
                    self.cli.sync_workspace(wsname, skeleton=False, only_update_server=True)
                    os.chdir(workspaceroot)

        self.logger.debug("source_dest_path: {}".format(source_dest_path))

        if not self.use_local_ws_as_staging:
            # 1. for each source_path: cp current_ws/source_path dest_ws/source_path
            is_skip_submit = True
            for source_path, dest_path in source_dest_path: 
                source_path = source_path.replace('/...', '')
                source_ws_path = '{}/{}'.format(self.ws._workspaceroot, source_path)
                source_ws_dirs = glob.glob(source_ws_path)
                for source_ws_dir in source_ws_dirs:

                    # Strip workspaceroot to get relative path
                    relative_dir = source_ws_dir.replace(self.ws._workspaceroot, '')
                    dest_ws_dir = '{}/{}'.format(workspaceroot, relative_dir)

                    if os.path.isdir(source_ws_dir):

                        ### Make sure destination directory exists 
                        cmd = 'mkdir -p {}'.format(dest_ws_dir)
                        self.logger.info(cmd)
                        stats = run_command(cmd)
                        self.logger.debug(stats)

                        self.logger.info('Copying files from {} to {}'.format(source_ws_dir, dest_ws_dir))
                        command = 'cp -vrf {}/* {}/'.format(source_ws_dir, dest_ws_dir)
                    else:   
                        ### source_ws_dir is a file
                        
                        ### Make sure destination directory exists 
                        cmd = 'mkdir -p {}'.format(os.path.dirname(dest_ws_dir))
                        self.logger.info(cmd)
                        stats = run_command(cmd)
                        self.logger.debug(stats)

                        self.logger.info('Copying files from {} to {}'.format(source_ws_dir, dest_ws_dir))
                        command = 'cp -vrf {} {}'.format(source_ws_dir, dest_ws_dir)


                    self.logger.debug(command)
                    if not self.preview:
                        exitcode, stdout, stderr = run_command(command)
                        err_msg = 'Command: {}\n \
                                   Exitcode: {}\n \
                                   Stdout: {}\n \
                                   Stderr: {}\n \
                                '.format(command, exitcode, stdout, stderr)
                        self.logger.debug(err_msg)
                        if exitcode:
                            raise OverlayDeliverableError(err_msg)

        # If deliverable is a large data deliverable and IP is not excluded, it follows a different algorithm
        if is_large and self.variant not in large_excluded_ip:
            # Overlay the deliverable using scm module
            scm = dmx.abnrlib.scm.SCM(self.preview)
            for source_path, dest_path in source_dest_path:
                self.logger.info('Attempting to overlay {}/{}'.format(self.variant, self.libtype))
                scm.overlay_workspace_action(workspaceroot, self.variant, self.libtype)

            # Remove the staging workspace                
            if not self.use_local_ws_as_staging:
                self.cli.del_workspace(wsname, preserve=False, force=True)
            ret = 0
        else:            
            # 1. xlp4 reconcile -d -e dest_ws/source_path
            # 2. xlp4 submit
            is_skip_submit = True
            for source_path, dest_path in source_dest_path: 
                source_path = source_path.replace('/...', '')
                source_ws_path = '{}/{}'.format(self.ws._workspaceroot, source_path)
                source_ws_dirs = glob.glob(source_ws_path)
                for source_ws_dir in source_ws_dirs:
                    # Strip workspaceroot to get relative path
                    relative_dir = source_ws_dir.replace(self.ws._workspaceroot, '')
                    dest_ws_dir = '{}/{}'.format(workspaceroot, relative_dir)


                    ### need to sync -k, otherwise files that are not latest will get this error when 'submit'
                    ### DEBUG [2019-01-15 10:50:27,901] - [overlaydeliverable]: Command: xlp4 reconcile /nfs/site/disks/da_infra_1/users/yltan/lionelta.i10socfm.liotest1.336//liotest1/pnr/...                                                             ###    Exitcode: 0                                                            
                    ###    Stdout: //depot/icm/proj/i10socfm/liotest1/pnr/dev/b#3 - opened for edit                                                                                                        
                    ###     ... //depot/icm/proj/i10socfm/liotest1/pnr/dev/b - must sync/resolve #4,#5 before submitting       
                    command = 'xlp4 sync -k {}/...'.format(dest_ws_dir)
                    self.logger.debug(command)
                    exitcode, stdout, stderr = run_command(command)
                    err_msg = 'Command: {}\n \
                               Exitcode: {}\n \
                               Stdout: {}\n \
                               Stderr: {}\n \
                            '.format(command, exitcode, stdout, stderr)
                    self.logger.debug(err_msg)


                    command = 'xlp4 reconcile {}/...'.format(dest_ws_dir)
                    self.logger.debug(command)
                    if not self.preview:
                        exitcode, stdout, stderr = run_command(command)
                        if exitcode:
                            err_msg = 'Command: {}\n \
                                       Exitcode: {}\n \
                                       Stdout: {}\n \
                                       Stderr: {}\n \
                                    '.format(command, exitcode, stdout, stderr)
                            raise OverlayDeliverableError(err_msg)
                        else:
                            err_msg = 'Command: {}\n \
                                       Exitcode: {}\n \
                                       Stdout: {}\n \
                                       Stderr: {}\n \
                                    '.format(command, exitcode, stdout, stderr)
                            self.logger.debug(err_msg)
                        if 'no file(s) to reconcile' not in stderr:
                            is_skip_submit = False

            # If there is no files to remove, skip submit       
            if is_skip_submit:
                self.logger.debug('No files to copy')
            else:    
                desc = 'Copying files as part of dmx overlay by {} on {}. {}'.format(user, date, self.desc)
                command = 'xlp4 submit -d "{}"'.format(desc)
                self.logger.debug(command)
                if not self.preview:
                    exitcode, stdout, stderr = run_command(command)
                    if exitcode:
                        err_msg = 'Command: {}\n \
                                   Exitcode: {}\n \
                                   Stdout: {}\n \
                                   Stderr: {}\n \
                                '.format(command, exitcode, stdout, stderr)
                        raise OverlayDeliverableError(err_msg)
                
            # Remove the staging workspace
            if not self.preview:                
                if not self.use_local_ws_as_staging:
                    self.cli.del_workspace(wsname, preserve=False, force=True)                            
            ret = 0
        
        return ret
            
    def overlay_depot_to_depot(self):
        ret = 1
        user = os.getenv('USER')                           
        date = datetime.datetime.today()
        source_depotpath = self.source_config_object.get_bom(p4=True)[0]
        dest_depotpath = self.dest_config_object.get_bom(p4=True)[0].split('@')[0]
        self.logger.debug("source_depotpath:{}".format(source_depotpath))
        self.logger.debug("dest_depotpath:{}".format(dest_depotpath))
        # source_depotpath://depot/icm/proj/i10socfm/liotest1/ipspec/dev/...@18629209
        # dest_depotpath://depot/icm/proj/i10socfm/liotest1/ipspec/LT1_dev/...


        # Get base source depotpath
        # Example: //depot/icm/proj/i10socfm/liotest2/rtl/dev/...@9729893
        # base_source_depotpath = //depot/icm/proj/i10socfm/liotest2/rtl/dev/
        # source_changelist = 9729893
        m = re.match('(.*?)\.\.\.\@(.*)', source_depotpath)
        if m:
            base_source_depotpath = m.group(1)
            source_changelist = m.group(2)
        else:
            raise OverlayDeliverableError('Fail to get base_source_depotpath from {}'.format(source_depotpath))
        # Get base dest depotpath
        # Example: //depot/icm/proj/i10socfm/liotest2/rtl/dev/...
        # base_source_depotpath = //depot/icm/proj/i10socfm/liotest2/rtl/dev/
        # source_changelist = 9729893                
        m = re.match('(.*?)\.\.\.', dest_depotpath)
        if m:
            base_dest_depotpath = m.group(1)
        else:
            raise OverlayDeliverableError('Fail to get base_dest_depotpath from {}'.format(dest_depotpath))               
        if self.cli.get_libtype_type(self.libtype) == 'DFII':
            # If libtype is a Cadence (DFII) type, regex string is variant/libtype/variant/...
            regex_pattern = '{}/{}/{}/(.*)'.format(self.variant, self.libtype, self.variant)
        else:
            # If libtype is a Cadence (DFII) type, regex string is variant/libtype/...
            regex_pattern = '{}/{}/(.*)'.format(self.variant, self.libtype)            


        ### SKip overlay if source has been previously overlaid.
        ### https://jira.devtools.intel.com/browse/PSGDMX-1666
        last_changenum = self.cli.get_last_submitted_changelist(filespec=dest_depotpath)
        self.logger.debug("last_changenum:{}".format(last_changenum))
        last_changedesc = self.cli.get_change_description(last_changenum)
        self.logger.debug("last_changedesc:{}".format(last_changedesc))
        change_keyword = 'dmxoverlaid from {}'.format(source_depotpath)
        if change_keyword in last_changedesc:
            self.logger.info("Content from {} has been overlaid. Skipping.".format(source_depotpath))
            return 0


        source_dest_path = []
        if self.filespec:
            # Find depot path that correspond to each filespec 
            for ea_file in self.filespec:
                m = re.match(regex_pattern, ea_file)
                if m:
                    source_path = '{}{}@{}'.format(base_source_depotpath, m.group(1), source_changelist)
                    dest_path = '{}{}'.format(base_dest_depotpath, m.group(1))
                    source_dest_path.append((source_path, dest_path))
            if source_dest_path == []:
                self.logger.info('Filespec provided but does not match any depot file. Skip.')

        elif self.cells:            
            for cell in self.cells:
                if self.slice:
                    # If cells provided and deliverable is slice, copy files recorded in slices.json
                    # Find all paths for all patterns
                    patterns = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype).get_slice(self.slice).get_patterns(ip=self.variant, cell=cell)
                    # Find all paths for all filelists
                    filelists = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype).get_slice(self.slice).get_filelists(ip=self.variant, cell=cell)
                else:
                    # If cells provided and deliverable is not a slice, copy files recorded in manifest.json
                    # Find all paths for all patterns
                    patterns = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype).get_patterns(ip=self.variant, cell=cell)
                    # Find all paths for all filelists
                    filelists = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype).get_filelists(ip=self.variant, cell=cell)

                # Find depot path that correspond to each pattern
                for pattern in patterns:
                    m = re.match(regex_pattern, pattern)
                    if m:
                        source_path = '{}{}@{}'.format(base_source_depotpath, m.group(1), source_changelist)
                        dest_path = '{}{}'.format(base_dest_depotpath, m.group(1))
                        source_dest_path.append((source_path, dest_path))

                # Find depot path that correspond to each filelist
                for filelist in filelists:
                    m = re.match(regex_pattern, filelist)
                    if m:
                        source_path = '{}{}@{}'.format(base_source_depotpath, m.group(1), source_changelist)
                        dest_path = '{}{}'.format(base_dest_depotpath, m.group(1))
                        source_dest_path.append((source_path, dest_path))                       
        else:
            if self.slice:
                # If no cells provided and deliverable is a slice, copy files recorded in slices.json
                # Find all paths for all patterns
                # Replace cell_name with * since no cells are provided
                patterns = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype).get_slice(self.slice).get_patterns(ip=self.variant, cell='*')
                # Find all paths for all filelists
                filelists = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype).get_slice(self.slice).get_filelists(ip=self.variant, cell='*')
                # Find depot path that correspond to each pattern
                for pattern in patterns:
                    m = re.match(regex_pattern, pattern)
                    if m:
                        source_path = '{}{}@{}'.format(base_source_depotpath, m.group(1), source_changelist)
                        dest_path = '{}{}'.format(base_dest_depotpath, m.group(1))
                        source_dest_path.append((source_path, dest_path))

                # Find depot path that correspond to each filelist
                for filelist in filelists:
                    m = re.match(regex_pattern, filelist)
                    if m:
                        source_path = '{}{}@{}'.format(base_source_depotpath, m.group(1), source_changelist)
                        dest_path = '{}{}'.format(base_dest_depotpath, m.group(1))
                        source_dest_path.append((source_path, dest_path))
            else:                
                # If no cells provided and deliverable is not slice, copy everything without referring to manifest
                source_dest_path.append((source_depotpath, dest_depotpath))            

        # Ensure no files are opened on dest path                
        # http://pg-rdjira:8080/browse/DI-975
        opened_path = []
        for source_path, dest_path in source_dest_path:
            command = 'xlp4 opened -a {}'.format(dest_path)
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                err_msg = 'Command: {}\n \
                           Exitcode: {}\n \
                           Stdout: {}\n \
                           Stderr: {}\n \
                        '.format(command, exitcode, stdout, stderr)
                raise OverlayDeliverableError(err_msg)
            if stdout:
                opened_path.append(dest_path)    
            # current gdpxl doe snot have distributed site
            '''
            command = 'xlp4 opened -x {}'.format(dest_path)
            exitcode, stdout, stderr = run_command(command)
            if exitcode:
                err_msg = 'Command: {}\n \
                           Exitcode: {}\n \
                           Stdout: {}\n \
                           Stderr: {}\n \
                        '.format(command, exitcode, stdout, stderr)
                raise OverlayDeliverableError(err_msg)
            if stdout:
                opened_path.append(dest_path)
            '''
        if opened_path:
            opened_path = list(set(opened_path)) #uniqify
            self.logger.error('Files are opened in:')
            for path in opened_path:
                self.logger.error('* {}'.format(path))

            if not self.forcerevert:
                raise OverlayDeliverableError('Overlay aborted. Please ensure that there are no opened files in the destination library') 
            else:
                self.try_to_force_revert_opened_files(opened_path)

        delobj = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype)
        is_large = delobj.large
        large_excluded_ip = delobj.large_excluded_ip

        # If deliverable is a large data deliverable and IP is not excluded, it follows a different algorithm
        if is_large and self.variant not in large_excluded_ip:

            if self.shared_wsroot:
                self.logger.debug('shared_wsroot: {}'.format(self.shared_wsroot))
                workspaceroot = self.shared_wsroot
            else:
                # Create a workspace with dest config
                # Create the workspace even in preview mode as scm requires an actual workspace to run even in preview mode
                self.cli.preview = False
                wsname = self.cli.add_workspace(self.project, self.variant, self.dest_config, dirname=self.directory, libtype=self.libtype)
                self.staging_wsname = wsname
                workspaceroot = '{}/{}'.format(self.directory, wsname)
            self.logger.debug('Staging workspace = {}'.format(workspaceroot))
            
            if not self.shared_wsroot:
                # Skeleton-sync workspace 
                try:
                    self.cli.sync_workspace(wsname, skeleton=False)
                except Exception as e:
                    ### There are times when post-sync-trigger fails due to groups > 16.
                    ### Thus, we wanna ignore those.
                    self.logger.warning(str(e))
            os.chdir(workspaceroot)
            
            # Overlay the deliverable using scm module
            scm = dmx.abnrlib.scm.SCM(self.preview)
            for source_path, dest_path in source_dest_path:
                self.logger.info('Attempting to overlay {} to {}'.format(source_path, dest_path))
                scm.overlay_action(workspaceroot, self.variant, self.libtype, source_path, dest_path, project=self.project)

            if not self.shared_wsroot:
                # Remove the staging workspace                
                self.cli.del_workspace(wsname, preserve=False, force=True)
            ret = 0
        else:

            if self.shared_wsroot:
                self.logger.debug('shared_wsroot: {}'.format(self.shared_wsroot))
                workspaceroot = self.shared_wsroot
            else:
                # Create a workspace with dest config
                wsname = self.cli.add_workspace(self.project, self.variant, self.dest_config, dirname=self.directory, libtype=self.libtype)
                self.staging_wsname = wsname
                workspaceroot = '{}/{}'.format(self.directory, wsname)
            self.logger.debug('Staging workspace = {}'.format(workspaceroot))
            # Skeleton-sync workspace 
            if not self.preview:
                if not self.shared_wsroot:
                    try:
                        self.cli.sync_workspace(wsname)
                    except Exception as e:
                        ### There are times when post-sync-trigger fails due to groups > 16.
                        ### Thus, we wanna ignore those.
                        self.logger.warning(str(e))
                os.chdir(workspaceroot)

            # 1. for each dest_path: xlp4 delete{dest_path}
            # 2. xlp4 submit
            # 3. for each source_path: xlp4 copy {source_path} {dest_path}
            # 4. xlp4 submit
            is_skip_submit = True
            for source_path, dest_path in source_dest_path:            
                self.logger.info('Removing files from {}'.format(dest_path))   
                if self.is_filespec_empty(dest_path):
                    self.logger.info("Skipped. No files found to be deleted from {}".format(dest_path))
                    continue
                command = '_xlp4 delete -v {}'.format(dest_path)
                command = 'xlp4 delete -v {}'.format(dest_path)
                self.logger.debug(command)
                if not self.preview:                
                    exitcode, stdout, stderr = run_command(command)
                    err_msg = 'Command: {}\n \
                               Exitcode: {}\n \
                               Stdout: {}\n \
                               Stderr: {}\n \
                            '.format(command, exitcode, stdout, stderr)
                    self.logger.debug(err_msg)
                    if exitcode:
                        raise OverlayDeliverableError(err_msg)
                    if 'file(s) not on client' not in stderr:
                        is_skip_submit = False

            # If there is no files to remove, skip submit   
            #if is_skip_submit:
            if not self.got_opened_files():
                self.logger.debug('No files to remove')
            else:                
                desc = 'Removing files as part of dmx overlay by {} on {}. {}'.format(user, date, self.desc)
                command = '_xlp4 submit -d "{}"'.format(desc)
                command = 'xlp4 submit -d "{}"'.format(desc)
                self.logger.debug(command)
                if not self.preview:
                    exitcode, stdout, stderr = run_command(command)
                    if exitcode:
                        err_msg = 'Command: {}\n \
                                   Exitcode: {}\n \
                                   Stdout: {}\n \
                                   Stderr: {}\n \
                                '.format(command, exitcode, stdout, stderr)
                        raise OverlayDeliverableError(err_msg)

            is_skip_submit = 0
            for source_path, dest_path in source_dest_path:            
                self.logger.info('Copying files from {} to {}'.format(source_path, dest_path)) 
                command = '_xlp4 copy {} {}'.format(source_path, dest_path)
                command = 'xlp4 copy {} {}'.format(source_path, dest_path)
                self.logger.debug(command)
                if not self.preview:
                    exitcode, stdout, stderr = run_command(command)
                    if self.is_no_files_copied(stdout+stderr):
                        is_skip_submit += 1 
                    elif exitcode:
                        err_msg = 'Command: {}\n \
                                   Exitcode: {}\n \
                                   Stdout: {}\n \
                                   Stderr: {}\n \
                                '.format(command, exitcode, stdout, stderr)
                        raise OverlayDeliverableError(err_msg)

            # If there is no files to remove, skip submit      
            self.logger.debug("is_skip_submit:{}, len(source_dest_path):{}".format(is_skip_submit, len(source_dest_path)))
            if is_skip_submit == len(source_dest_path):
                self.logger.debug('No files to copy')
            else:    
                desc = 'Copying files as part of dmx overlay by {} on {}. {}'.format(user, date, self.desc)
                ### Only add in change_keyword if the overlay happens on the entire libtype.
                if not self.slice and not self.cells and not self.filespec:
                    desc = '{} . {}'.format(change_keyword, desc)
                command = '_xlp4 submit -d "{}"'.format(desc)
                command = 'xlp4 submit -d "{}"'.format(desc)
                self.logger.debug(command)
                if not self.preview:
                    exitcode, stdout, stderr = run_command(command)
                    if exitcode:
                        err_msg = 'Command: {}\n \
                                   Exitcode: {}\n \
                                   Stdout: {}\n \
                                   Stderr: {}\n \
                                '.format(command, exitcode, stdout, stderr)
                        raise OverlayDeliverableError(err_msg)
                
            # Remove the staging workspace                
            if not self.preview:
                if not self.shared_wsroot:
                    self.cli.del_workspace(wsname, preserve=False, force=True)                            
            ret = 0
        
        return ret

    def try_to_force_revert_opened_files(self, opened_filespecs):
        for filespec in opened_filespecs:
            for site in ['sc_gdpxl', 'png_gdpxl']:
                try:
                    login_to_icmAdmin(site=site)
                    force_revert_files_by_filespec(filespec, site=site)
                except Exception as e:
                    self.logger.warning(str(e))

    def got_opened_files(self):
        cmd = '_xlp4 opened ...'
        cmd = 'xlp4 opened ...'
        cmd = 'xlp4 opened ...'
        exitcode, stdout, stderr = run_command(cmd)
        self.logger.debug('cmd: {}\nexitcode: {}\nstdout: {}\nstderr: {}\n'.format(cmd, exitcode, stdout, stderr))
        syntax = 'not opened on this client' 
        if syntax in stdout or syntax in stderr:
            return False
        return True

    def is_filespec_empty(self, filespec):
        cmd = '_xlp4 files {} | grep -v ".icminfo" | grep -v "delete change" '.format(filespec)
        cmd = 'xlp4 files {} | grep -v ".icminfo" | grep -v "delete change" '.format(filespec)
        cmd = 'xlp4 files {} | grep -v ".icminfo" | grep -v "delete change" '.format(filespec)
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            return True
        return False


    def is_no_files_copied(self, outputstring):
        exceptlist = ['File(s) up-to-date.', 'no such file(s)']
        return [x for x in exceptlist if x in outputstring]

    def qos_layer(self, text):
        if 'Perforce password (P4PASSWD) invalid or unset' in text:
            self.logger.error("Please run 'icm_login' in all sites (PG/SJ) and then retry again.")

