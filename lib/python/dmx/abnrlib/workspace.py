#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/workspace.py#2 $
$Change: 7654946 $
$DateTime: 2023/06/12 01:22:46 $
$Author: wplim $

Description: Abstract base class used for representing IC Manage boms. 
See: http://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/ICMConfigurationClass for more details

Author: Kevin Lim Khai - Wern
Copyright (c) Altera Corporation 2016
All rights reserved.
'''

## @addtogroup dmxlib
## @{
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
from past.utils import old_div
import multiprocessing
import os, sys
import logging
import re
import dmx.dmlib.ICManageWorkspace
import dmx.abnrlib.icm
from dmx.utillib.utils import format_configuration_name_for_printing, is_workspace_path_allowed, get_approved_disks, run_command
import dmx.abnrlib.flows.workspace
import dmx.ecolib.ecosphere
import dmx.abnrlib.config_factory 
import dmx.sionlib.sion_utils
import configparser
import dmx.abnrlib.dssc
import dmx.tnrlib.release_runner
import argparse
from multiprocessing import Process
from joblib import Parallel, delayed
import dmx.sionlib.sion_utils
import tempfile

class WorkspaceError(Exception):
    pass

class Workspace(object):
    def __init__(self, workspacepath=None, project=None, ip=None, bom=None, 
                 deliverable=None, preview=False):
        workspacepath = workspacepath if workspacepath else os.getcwd()
        self._project = project
        self._ip = ip
        self._bom = bom
        self._deliverable = deliverable        
        self.preview=preview
        self.cli = dmx.abnrlib.icm.ICManageCLI(preview=self.preview)
        self.logger = logging.getLogger(__name__)
        self._workspace = None
        self._workspacename = None
        self.isworkspace = False        
        self._workspaceroot = None
        self.errors = []
        self.cfobj = None   # ConfigFactory Object
        
        if not os.path.exists(workspacepath):
            raise WorkspaceError('{} does not exist'.format(workspacepath))
        self._workspacepath = os.path.realpath(os.path.abspath(workspacepath))                                                      
        if not self._project and not self._bom and not self._ip:
            self._workspace = dmx.dmlib.ICManageWorkspace.ICManageWorkspace(self._workspacepath)
            self.isworkspace = True
            self._project = str(self._workspace._projectName)
            self._ip = str(self._workspace._ipName)
            self._bom = str(self._workspace._configurationName)
            self._workspaceroot = self._workspace._workspaceroot
            # Don't assume the workspacename is part of the path.
            # pg-rdjira:8080/browse/DI-1150
            # self._workspacename = self._workspaceroot.split('/')[-1]
            self._workspacename = self._workspace.workspaceName
            #self._deliverable = str(self._workspace._attributesAlwaysAccessViaMethod['libtype']) if self._workspace._attributesAlwaysAccessViaMethod['libtype'] else None
            self._deliverable = None
        else:
            # Check if config exists
            if not self.cli.config_exists(self._project, self._ip, self._bom, libtype=self._deliverable):
                raise WorkspaceError('{} does not exist'.format(format_configuration_name_for_printing(
                    self._project, self._ip, self._bom, libtype=self._deliverable
                )))
            # Check if path is within another workspace
            try:
                dmx.dmlib.ICManageWorkspace.ICManageWorkspace.findWorkspace(self._workspacepath)
                raise WorkspaceError('{} is within another workspace path'.format(self._workspacepath))
            except WorkspaceError as e:                 
                raise WorkspaceError(e)
            except:
                pass

            # Check if directory is allowed to create a workspace for this project
            if not is_workspace_path_allowed(self._project, self._ip, self._workspacepath):
                disks = get_approved_disks(self._project)
                error_msg = "{0}/{1} is not allowed to be created at {2}. These are the approved disks for {0}:\n".format(self._project, self._ip, self._workspacepath)
                for disk in disks:
                    error_msg = error_msg + '\t{}\n'.format(disk)
                error_msg = error_msg + 'Please contact da_icm_admin@intel.com if you need further help'                
                raise WorkspaceError(error_msg)

    @property
    def bom(self):
        return self.get_workspace_attributes()['Config']

    @property
    def ip(self):
        return self.get_workspace_attributes()['Variant']

    @property
    def project(self):
        return self.get_workspace_attributes()['Project']

    @property
    def path(self):
        return self.get_workspace_attributes()['Dir']

    @property
    def name(self):
        return self.get_workspace_attributes()['Workspace']

    def create(self, ignore_clientname=False):
        ret = 1
        if self.isworkspace:
            raise WorkspaceError('{} is already a workspace'.format(self._workspacepath))
        else:            
            if not self.preview:
                user = os.environ['USER']
                ret = self.cli.add_workspace(self._project, self._ip, self._bom, 
                                             user, self._workspacepath, ignore_clientname, occupied_ok=True, libtype=self._deliverable)     
                self._workspacename = ret
                if ignore_clientname:
                    self._workspaceroot = self._workspacepath                
                else:
                    self._workspaceroot = '{}/{}'.format(self._workspacepath, self._workspacename)
                self.isworkspace = True
                ret = self.sync(skeleton=True)                

                self._workspace = dmx.dmlib.ICManageWorkspace.ICManageWorkspace(self._workspaceroot)
        return ret

    def sync_for_release(self, ip, milestone, thread, deliverable=None, views=None):
        '''
        'dmx release/workspace check' command needs to only sync the "required" files.
        Syncing unnecessary files will take up a lot of runtime.
        Definition of "required" files are for example:-
        - variant/ipspec/...
        - variant/libtype/audit/...
        - variant/libtype/tnrwaivers.csv
        - required chksum files from audit.xml
        - type_check files
        - etc ...
        '''
        args = argparse.ArgumentParser().parse_args([])
        args.variant = ip
        args.libtype = deliverable
        [args.project, args.configuration] = self.get_project_bom(ip, deliverable=None)
        args.milestone = milestone
        args.thread = thread
        args.views = views

        args.work_dir = None
        args.devmode = True

        rr = dmx.tnrlib.release_runner.ReleaseRunner(args)
        rr.workspace_path = self._workspaceroot

        # We must be in the workspace folder for things like icmp4 sync to work.
        cwd = os.getcwd()
        os.chdir(self._workspaceroot)
        rr.populate_workspace()
        os.chdir(cwd)

    def sync_cache(self, cfgfile=None, update_without_skeleton_sync=False):
        '''
        1. Skeleton sync workspacce
        2. Populate workspace cache in central disk
        3. Link files from workspace to cache
        4. Run server side sync in workspace for immutable libraries
        '''
        broken_link = [] 
        self.logger.debug("Running icm.sync_cache: cfgfile: {}".format(cfgfile))
        ret = 1
        # Skeleton sync the workspace first
        self.cli.sync_workspace(self._workspacename, skeleton=True, update_without_skeleton_sync=update_without_skeleton_sync) 
        all_processes = []

        self.logger.debug('Initiating cache mode with sion caching')
        if not self.preview:
            # Populating cache using sion populate
            if cfgfile=='':
                cfgfile = None
            misc = "cfgfile:%s" % (cfgfile)
            ret = dmx.sionlib.sion_utils.run_as_headless_user_cache_mode('populate', self.project, self.ip, None, self.bom, user=os.getenv('USER'), cache_only=True, misc=misc)
            if ret:
                raise WorkspaceError('Failed to run sion populate with cache for {}/{}@{}'.format(self.project, self.ip, self.bom))

            '''
            # Create file symlink
            broken_link = dmx.sionlib.sion_utils.link_ws(self._workspaceroot, project=self.project, ip=self.ip, bom=self.bom, cfgfile=cfgfile)
            self.logger.info('Create file symlink done')

            # Run server side sync for immutable libraries
            cfobj = self.get_config_factory_object()

            self.logger.info('Locking all immutable bom.')
            self.sync_dash_k_immutable_bom(self._workspaceroot, cfobj)

            n_jobs = dmx.sionlib.sion_utils.auto_get_n_jobs_for_parallelism()
            self.logger.debug('Run parallel start')
            try:
                Parallel(n_jobs=n_jobs, backend="threading")(delayed(dmx.sionlib.sion_utils.server_side_sync_cfg)(self._workspaceroot, cfg) for cfg in cfobj.flatten_tree())
            except Exception as e:
                self.logger.error(e)
                sys.exit(1)
            self.logger.debug('Run parallel end')
            '''
        ret = 0
        return broken_link 

    def sync_dash_k_immutable_bom(self,target_dir, cfobj):
        filename = self.create_dash_k_immutable_bom(target_dir, cfobj)
        cmd = 'xlp4 -x {} sync -k'.format(filename)
        cwd = os.getcwd()
        os.chdir(target_dir)
        exitcode, stdout, stderr = run_command(cmd)
        if exitcode:
            self.logger.error(stdout)
            self.logger.error(stderr)
            raise WorkspaceError('\"{}\" run failed'.format(cmd))
        os.chdir(cwd)

    def create_dash_k_immutable_bom(self,target_dir, cfobj):
        new_file, filename = tempfile.mkstemp()
        fo = open(filename, 'w+')
        self.logger.debug(filename)
        for cfg in cfobj.flatten_tree():
            if not cfg.is_config() and not cfg.is_mutable():
                to_be_sync_path = '{}/{}/{}/...'.format(target_dir, cfg.variant, cfg.libtype)
                fo.write(to_be_sync_path+'\n')
        fo.close()
        return filename

    def auto_get_n_jobs_for_parallelism(self):
        n = old_div(multiprocessing.cpu_count(),2) - 4
        if n < 1:
            n = 1
        if n > 5:
            n = 5
        return n


    def server_side_sync_immutable_lib(self, cfg_is_simple, cfg_is_mutable, cfg_variant, cfg_libtype):
        self.logger.info('server_side_sync_immutable_lib start')
        #if cfg.is_simple() and not cfg.is_mutable():
        if cfg_is_simple() and not cfg_is_mutable():
            #command = 'icmp4 sync -k {}/{}/{}/...'.format(self._workspaceroot, cfg.variant, cfg.libtype)
            command = 'xlp4 sync -k {}/{}/{}/...'.format(self._workspaceroot, cfg_variant, cfg_libtype)
            exitcode, stdout, stderr = run_command(command)
            self.logger.info('Server_side_sync_immu : '.format(command))
            self.logger.info('Server_side_sync_immu : '.format(stdout))
            if exitcode:
                self.logger.error(stderr)
                raise WorkspaceError('Error running {}'.format(command))




    def is_flatten_bom_contain_immutable_and_cached_and_otherdmdeliverable(self):
        other_dm_deliverable = self.get_deliverable_dm_non_icm_and_naa()

        if self._deliverable != None:
            self.logger.debug('Deliverable workspace: Sync cache only, contain immutable')
            return True, False, False

        flatten_config = self.cli.get_flattened_config_details(self._project, self._ip, self._bom, ['name', 'variant:parent:name', 'project:parent:name', 'config:parent:name', 'libtype:parent:name'])
        contain_immutable = False
        all_immutable_cached = True
        contain_other_dm_deliverable = False

        sion_disk = dmx.sionlib.sion_utils.SionDisk()

        for config in flatten_config:
            config_name = config['name']
            project = config['project:parent:name']
            ip = config['variant:parent:name']
            deliverable = config['libtype:parent:name']
            if deliverable in other_dm_deliverable:
                contain_other_dm_deliverable = True

            if self.cli.is_name_immutable(config_name):
                contain_immutable = True
                if deliverable and not sion_disk.is_pvcd_in_sion_disk(project, ip, deliverable, config_name) and not deliverable in other_dm_deliverable :
                    self.logger.info('{} {} {} {} not yet cached'.format(project, ip, deliverable, config_name))
                    all_immutable_cached = False
                    break

        self.logger.info('Flatten bom contain immutable: {}, all_cached: {}, other_dm_deliverable: {}'.format(contain_immutable, all_immutable_cached, contain_other_dm_deliverable))
        if not contain_immutable:
            return contain_immutable, False, contain_other_dm_deliverable
        else:
            return contain_immutable, all_immutable_cached, contain_other_dm_deliverable

    def sync(self, skeleton=False, variants=['all'], libtypes=['all'], specs=[], force=False, verbose=False, sync_cache=False, cfgfile='', skip_update=False, update_without_skeleton_sync=False):
        broken_link = []
        ret = 1
        if not self.isworkspace:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))
        else:
            variants_libtypes_specs = []
            if os.path.isfile(cfgfile):
                config = self.read_sync_config_file(cfgfile)
                for section in config.sections():
                    variants = []
                    libtypes = []
                    specs = []
                    if config.has_option(section, 'specs'):
                        specs = config.get(section, 'specs').split()
                        variants_libtypes_specs.append((variants, libtypes, specs))    
                    else:
                        variants = config.get(section, 'variants').split()
                        elements = config.get(section, 'libtypes').split()
                        if '*' in variants or 'all' in variants:
                            # if *, get all ips in workspace
                            variants = self.get_ips()

                        for variant in variants:
                            project = self.get_project_of_ip(variant)
                            if project:
                                family = dmx.ecolib.ecosphere.EcoSphere(preview=self.preview).get_family(os.getenv("DB_FAMILY"))
                                libtypes = []
                                for element in elements:
                                    if element.startswith('view'):
                                        # Expand view into libtypes
                                        libtypes = libtypes + [x.deliverable for x in family.get_view(element).get_deliverables()]
                                    else:
                                        libtypes.append(element)
                                libtypes = sorted(list(set(libtypes)))
                                variants_libtypes_specs.append(([variant], libtypes, specs))
            else:
                variants_libtypes_specs.append((variants, libtypes, specs))

            if not self.preview:
                contain_immutable, all_immutable_cached, is_contain_other_dm = self.is_flatten_bom_contain_immutable_and_cached_and_otherdmdeliverable()

                if contain_immutable and not all_immutable_cached and sync_cache:
                    broken_link = self.sync_cache(cfgfile, update_without_skeleton_sync)
                    self.logger.info('Sync Cache done')
                
                if not self._deliverable :
                   # Create file symlink
                   broken_link = dmx.sionlib.sion_utils.link_ws(self._workspaceroot, project=self.project, ip=self.ip, bom=self.bom, cfgfile=cfgfile)
                   self.logger.info('Create file symlink done')
   
                   # Run server side sync for immutable libraries
                   cfobj = self.get_config_factory_object()
   
                   self.sync_dash_k_immutable_bom(self._workspaceroot, cfobj)
   

                # First sync the ICManage workspace
                if (self.cli.get_icmanage_build_number() >= 36054):
                    ret = self.cli.sync_workspace(self._workspacename, skeleton=skeleton, variants=['all'], libtypes=['all'], specs=[], force=force, verbose=verbose, skip_update=skip_update, update_without_skeleton_sync=update_without_skeleton_sync, variants_libtypes_specs=variants_libtypes_specs)
                # Syncs the workspace
                # Workaround for icm/36054 and below
                else:
                    for variants, libtypes, specs in variants_libtypes_specs:
                        ret = self.cli.sync_workspace_slow(self._workspacename, skeleton=skeleton, variants=variants, libtypes=libtypes, specs=specs, force=force, verbose=verbose)
                self._workspace = dmx.dmlib.ICManageWorkspace.ICManageWorkspace(self._workspaceroot)

                if skeleton:
                    return ret

                # Next sync from other data management system
                if is_contain_other_dm:
                    for variants, libtypes, specs in variants_libtypes_specs:
                        # For non-icmanage deliverable, parse the wildcards, ips and deliverables
                        if '*' in variants or 'all' in variants:
                            # if *, get all ips in workspace
                            workspace_ips = self.get_ips()
                        else:
                            workspace_ips = variants
                        for workspace_ip in workspace_ips:
                            if '*' in libtypes or 'all' in libtypes:
                                # if *, get all deliverables in workspace for the ip
                                workspace_deliverables = self.get_deliverables_for_ip(workspace_ip)
                            else:
                                workspace_deliverables = libtypes
                            project = self.get_project_of_ip(workspace_ip)
                            try:
                                family = dmx.ecolib.ecosphere.EcoSphere(preview=self.preview).get_family(os.getenv("DB_FAMILY"))
                                ip = family.get_ip(workspace_ip, project_filter=project)
                            except:
                                ### This exception part is introduced because without this, it will fail when someone is trying to
                                ### populate workspace with 2 Families, example:-
                                ### - user arc shell to Falcon project/bundle (DB_FAMILY=Falcon)
                                ### - and then user populates a workspace which contains (Falcon_Mesa + WHR + GDR) data.
                                family = dmx.ecolib.ecosphere.EcoSphere(preview=self.preview).get_family_for_icmproject(project)
                                ip = family.get_ip(workspace_ip, project_filter=project)
    
                            for workspace_deliverable in workspace_deliverables:
                                if ip.has_deliverable(workspace_deliverable):
                                    delobj = ip.get_deliverable(workspace_deliverable)
                                    dm = delobj.dm
                                    ### we do not need to run dssc sync if sync_cache mode because this has already been handled during sync_cache()
                                    ### ONLY SKIP IF libtype is immutable !!!! DO NOT SKIP if libtype is mutable !!!!!!
                                    if dm == 'designsync' and (self.is_varlib_mutable(workspace_ip, workspace_deliverable) or not sync_cache):
                                        # For designsync deliverable, call dssc to populate the files from designsync
                                        wsbom = '{}/{}@{}'.format(self.project, self.ip, self.bom)
                                        dm_meta = delobj.dm_meta
                                        dssc = dmx.abnrlib.dssc.DesignSync(dm_meta['host'], dm_meta['port'], preview=self.preview)
                                        dssc.sync_designsync_deliverable_to_icmanage_workspace(self._workspaceroot, workspace_ip, workspace_deliverable, wsbom, dm_meta=dm_meta)
                
        return ret, broken_link


    def get_deliverable_dm_non_icm_and_naa(self):
        try:
            family = dmx.ecolib.ecosphere.EcoSphere(preview=self.preview).get_family(os.getenv("DB_FAMILY"))
        except:
            family = dmx.ecolib.ecosphere.EcoSphere(preview=self.preview).get_family_for_icmproject(project)

        # Get deliverable that dm is not icm and naa
        deliverables = family.get_all_deliverables()
        other_dm_deliverable = []
        for deliverable in deliverables:
            manifest = dmx.ecolib.manifest.Manifest(family.name, deliverable.name)
            if manifest.dm != 'icm' and manifest.dm != 'naa':
                other_dm_deliverable.append(deliverable)

        return other_dm_deliverable

        
    def is_varlib_mutable(self, variant, libtype):
        cfobj = self.get_config_factory_object()
        matches = cfobj.search(variant='^{}$'.format(variant), libtype='^{}$'.format(libtype))
        return matches[0].is_mutable()






    def populate(self, skeleton=False, variants=['all'], libtypes=['all'], specs=[], force=False, verbose=False, sync_cache=True, cfgfile=''):
        '''
        Populate is similar to sync, but utilizes sion caching for immutable BOM
        '''
        return self.sync(skeleton=skeleton, variants=variants, libtypes=libtypes, specs=specs, force=force, verbose=verbose, sync_cache=sync_cache, cfgfile=cfgfile)

    def read_sync_config_file(self, cfgfile):
        '''
        Read quicksync configuration file and return the config object
        Validate and make sure all sections contain these key:-
        - variants & libtypes -or-
        - specs
        '''
        error = ''
        config = configparser.RawConfigParser()
        config.read(cfgfile)
        for section in config.sections():
            if 'specs' in config.options(section):
                continue
            if 'variants' not in config.options(section):
                error += 'variants: key not found in section [{}] in cfgfile {}\n'.format(section, cfgfile)
            if 'libtypes' not in config.options(section):
                error += 'libtypes: key not found in section [{}] in cfgfile {}'.format(section, cfgfile)
        if error:
            self.logger.debug(error)
            raise WorkspaceError('ConfigFile provided is invalid')
        return config

    def update(self, config=None):
        ret = 1
        if not self.isworkspace:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))
        else:
            if not self.preview:
                ret = self.cli.update_workspace(self._workspacename, config=config)
                self._workspace = dmx.dmlib.ICManageWorkspace.ICManageWorkspace(self._workspaceroot)
        return ret

    def delete(self, preserve=True, force=False):
        ret = 1
        if not self.isworkspace:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))
        else:
            if not self.preview:
                if self.cli.del_workspace(self._workspacename, preserve=preserve, force=force):
                    self._workspace = None
                    self.isworkspace = False
                    ret = 0

        return ret  

    def save(self, saveworkspacepath=None, savedirname=None):
        ret = 1
        if self.isworkspace:
            self._workspace.saveEveryIP(savepath, savedirname)  
            ret = 0
        else:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))
        return ret 
        
    def check(self, ip, milestone, thread, deliverable=None, logfile=None, dashboard=None, celllist_file=None, nowarnings=False, waiver_file=[], views=None, validate_deliverable_existence_check=True, validate_type_check=True, validate_checksum_check=True, validate_result_check=True, validate_goldenarc_check=False, familyobj=None, only_run_flow_subflow_list=None):
        ret = 1
        if not self.isworkspace:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))
        else:
            [project, bom] = self.get_project_bom(ip, deliverable)
            self.logger.debug("This is the info sent to check_action() ==> {}/{}:{}@{}".format(project, ip, deliverable, bom))
            wsobj = dmx.abnrlib.flows.workspace.Workspace()

            # We must be in the workspace folder for things like icmp4 sync to work.
            cwd = os.getcwd()
            os.chdir(self._workspaceroot)
            if not wsobj.check_action(project, ip, bom, milestone, thread, libtype=deliverable, logfile=logfile, dashboard=dashboard, celllist_file=celllist_file, nowarnings=nowarnings, waiver_file=waiver_file, preview=self.preview, views=views, validate_deliverable_existence_check=validate_deliverable_existence_check, validate_type_check=validate_type_check, validate_checksum_check=validate_checksum_check, validate_result_check=validate_result_check, validate_goldenarc_check=validate_goldenarc_check, cfobj=self.cfobj, familyobj=familyobj, only_run_flow_subflow_list=only_run_flow_subflow_list):
                ret = 0
            self.errors = wsobj.errors
            os.chdir(cwd)
        return ret        

    def get_config_factory_object(self):
        '''
        Return the config_factory object of the workspace
        '''
        if not self.cfobj:
            self.cfobj = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self._workspace.projectName, self._workspace.ipName, self._workspace.configurationName)
        return self.cfobj

    def get_project_bom(self, ip, deliverable=None):
        '''
        Given an IP and/or DELIVERABLE, search thru the config_factory tree and return the [project, config] name.
        Raise error if no matching ip/deliverable is available.
        '''
        self.cfobj = self.get_config_factory_object()
        if not deliverable:
            results = self.cfobj.search(project='.*', variant='^{}$'.format(ip), libtype=None)
        else:
            results = self.cfobj.search(project='.*', variant='^{}$'.format(ip), libtype='^{}$'.format(deliverable))
        try:
            project = results[0].project
            if results[0].is_config():
                bom = results[0].config
            elif results[0].is_release():
                bom = results[0].lib_release
            elif results[0].is_library():
                bom = results[0].library
        except:
            self.logger.fatal("Could not find any matching variant:libtype ({}:{})".format(ip, deliverable))
            raise
        return [project, bom]

    def get_type_check_errors(self, deliverable=''):
        '''
        The prerequisite for this method to function is that check() should be run first.
        '''
        if not self.errors:
            raise WorkspaceError("Prerequisite to run this method is that the check() method should be run first.")

        data = {}
        for key in self.errors:
            data[key] = []
            for err in self.errors[key]:
                if err.subflow == 'type':
                    if not deliverable or err.libtype==deliverable:
                        data[key].append(err)
        return data

    def get_deliverable_existence_errors(self, deliverable=''):
        '''
        The prerequisite for this method to function is that check() should be run first.
        '''
        if not self.errors:
            raise WorkspaceError("Prerequisite to run this method is that the check() method should be run first.")

        data = {}
        for key in self.errors:
            data[key] = []
            for err in self.errors[key]:
                if err.flow == 'deliverable' and err.subflow == 'existence':
                    if not deliverable or 'Libtype {} is required by the roadmap'.format(deliverable) in err.error:
                        data[key].append(err)
        return data

    def get_empty_xml_errors(self):
        '''
        The prerequisite for this method to function is that check() should be run first.
        '''
        if not self.errors:
            raise WorkspaceError("Prerequisite to run this method is that the check() method should be run first.")

        data = {}
        for key in self.errors:
            data[key] = []
            for err in self.errors[key]:
                if 'Empty audit XML file is not allowed' in err.error:
                    data[key].append(err)
        return data

    def get_unwaivable_errors(self):
        '''
        The prerequisite for this method to function is that check() should be run first.
        '''
        if not self.errors:
            raise WorkspaceError("Prerequisite to run this method is that the check() method should be run first.")

        data = {}
        for key in self.errors:
            data[key] = []
            for err in self.errors[key]:
                if 'UNWAIVABLE' in err.error:
                    data[key].append(err)
        return data

    def get_checksum_errors(self):
        '''
        The prerequisite for this method to function is that check() should be run first.
        '''
        if not self.errors:
            raise WorkspaceError("Prerequisite to run this method is that the check() method should be run first.")

        data = {}
        for key in self.errors:
            data[key] = []
            for err in self.errors[key]:
                if ' checksum for ' in err.error:
                    data[key].append(err)
        return data

    def get_result_errors(self):
        '''
        The prerequisite for this method to function is that check() should be run first.
        '''
        if not self.errors:
            raise WorkspaceError("Prerequisite to run this method is that the check() method should be run first.")

        data = {}
        for key in self.errors:
            data[key] = []
            for err in self.errors[key]:
                if ' test results indicated failure' in err.error:
                    data[key].append(err)
        return data


    def get_workspace_attributes(self):
        if self.isworkspace:
            return self._workspace._attributesAlwaysAccessViaMethod       
        else:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))

    def get_workspace_attribute(self, attr):
        if self.isworkspace:  
            return self._workspace.getWorkspaceAttribute(attr)
        else:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))

    def get_ip_for_cell(self, cell):
        if self.isworkspace:
            return self._workspace.getIPNameForCellName(cell)     
        else:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath)) 
    
    def get_ips(self):
        if self.isworkspace:
            if self._deliverable:
                return [self._ip]
            else:
                return self._workspace.get_ips()
        else:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))

    def get_projects(self):
        if self.isworkspace:
            if self._deliverable:
                return [self._project]
            else:
                return self._workspace.get_projects()
        else:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))

    def get_ips_with_project(self):
        if self.isworkspace:
            return self._workspace.get_ips_with_project()
        else:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))    

    def get_project_of_ip(self, ip):
        if self.isworkspace:
            if self._deliverable:   
                if ip == self._ip:
                    return self._project
                else:
                    raise WorkspaceError('IP {} does not exist in workspace'.format(ip))
            else:
                return self._workspace.get_project_of_ip(ip)
        else:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))           
        
    def get_deliverables_for_ip(self, ip): 
        if self.isworkspace:     
            if self._deliverable:
                if ip == self._ip:
                    return [self._deliverable]
                else:
                    raise WorkspaceError('IP {} does not exist in workspace'.format(ip))
            else:
                return self._workspace.get_deliverables(ip)
        else:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))

    def get_cells_for_ip(self, ip):
        if self.isworkspace:
            return self._workspace.get_cells(ip)
        else:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))
        
    def get_unneeded_deliverables_for_ip(self, ip):
        if self.isworkspace:
            return self._workspace.get_unneeded_deliverables_for_ip(ip)
        else:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))

    def get_unneeded_deliverables_for_cell(self, ip, cell):
        if self.isworkspace:
            return self._workspace.get_unneeded_deliverables_for_cell(ip, cell)  
        else:
            raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))

    def get_ip(self, cwd=True):
        ip = None
        if cwd:
            if self.isworkspace:            
                m = re.match('{}\/(.*)'.format(self._workspaceroot.replace('.', '\.').replace('/', '\/')), os.getcwd())
                if m:
                    ip = m.group(1).split('/')[0]
                if ip not in self.get_ips():
                    ip = None
            else:
                raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))
                
        return ip                                

    @classmethod
    def get_broken_symlinks(cls, path):
        '''
        Return all broken symlink in workspace
        '''
        broken_link = []
        cmd = 'find {} -type l -exec file {{}} \; |grep broken'.format(path)
        exitcode, stdout, stderr = run_command(cmd)
        result = stdout.rstrip().split('\n')
        for line in result:
            broken_link.append(line.split(':')[0])
        return broken_link

    def get_ip_object(self, ip):
        ### make sure ip exist
        if ip not in self.get_ips():
            raise WorkspaceError("IP:{} not found in workspace.".format(ip))

        project = self.get_project_of_ip(ip)
        eco = dmx.ecolib.ecosphere.EcoSphere()
        family = eco.get_family(os.getenv("DB_FAMILY"))
        ipobj = family.get_ip(ip, project_filter=project)
        return ipobj


    def get_deliverable(self, cwd=True):
        deliverable = None
        if cwd:
            if self.isworkspace:            
                ip = self.get_ip(cwd=True)
                m = re.match('{}\/{}\/(.*)'.format(self._workspaceroot.replace('.', '\.').replace('/', '\/'), ip), os.getcwd())
                deliverable = None
                if m:
                    deliverable = m.group(1).split('/')[0]
                if deliverable not in self.get_deliverables_for_ip(ip):
                    deliverable = None
            else:
                raise WorkspaceError('{} is not a workspace'.format(self._workspacepath))

        return deliverable            
        

    def untar_files(self, varlibs=None, cfgfile=None):
        '''
        Untar all tarred files from the supported areas.

        Example:-
            varlibs == [(variant1, libtype1), (variant2, libtype2)]
            Untar these files:-
                - wsroot/variant1/libtype1/__tobe_untarred/*
                - wsroot/variant1/libtype1/*/__tobe_untarred/*
                - wsroot/variant2/libtype2/__tobe_untarred/*
                - wsroot/variant2/libtype2/*/__tobe_untarred/*

        if varlibs is not provided, untar everything, ie:-
                - wsroot/*/*/__tobe_untarred/*
                - wsroot/*/*/*/__tobe_untarred/*

        cfgfile here is the same quicksync.cfg config file that is used for 'dmx workspace sync'.
            Only the 'variants:/libtypes:' section will be honored. 
            'specs:' section will not be taken into consideration.

        cfgfile supercedes varlibs.
            if both are given, only cfgfile will be honered.
            if neither were given, everything will be untarred.

        Documentation:-
            https://wiki.ith.intel.com/display/tdmaInfra/Adding+support+for+transparent+handing+of+tar.gz+files+to+dmx+release

        '''
        UNTARDIR = '__tobe_untarred'

        if not cfgfile:
            if not varlibs:
                varlibs = [('*', '*')]

        else:
            varlibs = []
            config = self.read_sync_config_file(cfgfile)
            for section in config.sections():
                variants = []
                libtypes = []
                if config.has_option(section, 'variants') and config.has_option(section, 'libtypes'):
                    variants = config.get(section, 'variants').split()
                    libtypes = config.get(section, 'libtypes').split()
                    for v in variants:
                        for l in libtypes:
                            varlibs.append((v,l))

        self.logger.debug("untar varlibs:{}".format(varlibs))

        # We must be in the workspace_root this to work.
        cwd = os.getcwd()
        os.chdir(self._workspaceroot)

        for var,lib in varlibs:
            cmdlist = []
            cmdlist.append('ls {}/{}/{}/*    | xargs -t -n1 tar -xvf'.format(var, lib, UNTARDIR))
            cmdlist.append('ls {}/{}/*/{}/*  | xargs -t -n1 tar -xvf'.format(var, lib, UNTARDIR))
            for cmd in cmdlist:
                self.logger.debug("Running {}".format(cmd))
                exitcode, stdout, stderr = run_command(cmd)
                self.logger.debug(stdout)
                self.logger.debug(stderr)

        os.chdir(cwd)

    def report_broken_link(self, list_of_link):
        if not list_of_link: return
        for link_list in list_of_link:
            if type(link_list) is not list: continue
            for link in link_list:
                if not os.path.exists(link):
                    self.logger.warning('Broken Link: {}'.format(link))
## @}
