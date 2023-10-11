#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/snaptree.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr "snaptree" subcommand plugin
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
from __future__ import print_function
from builtins import object
import os
import sys
import logging
import textwrap
import itertools

from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.utillib.utils import format_configuration_name_for_printing, normalize_config_name, get_ww_details
from dmx.utillib.multiproc import run_mp
import dmx.ecolib.ecosphere
from dmx.utillib.arcenv import ARCEnv
import dmx.abnrlib.dssc

class SnapTreeError(Exception): pass
class BadReleaseNumberError(Exception): pass

class SnapTree(object):
    '''
    Runs the snaptree abnr subcommand
    '''

    def __init__(self, project, variant, config, snapshot, libtypes=[], changelist=0, reuse=False,
                 description=None, variants=[], preview=True):
        self.project = project
        self.variant = variant
        self.config = config
        self.snapshot = snapshot
        self.reuse = reuse
        self.description = description
        self.variants = variants
        self.preview = preview
        self.cli = ICManageCLI(preview=preview)
        self.logger = logging.getLogger(__name__)

        try:
            self.changelist = int(changelist)
        except ValueError:
            raise SnapTreeError('{0} is not a valid Perforce changelist number'.format(changelist))

        if self.cli.is_name_immutable(config):
            raise SnapTreeError('config is already an immutable object. Nothing to do here.')

        if self.changelist == 0:
            #self.changelist = self.cli.get_last_submitted_changelist()
            self.changelist = None

        # If project not given, get project from IP
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise SnapTreeError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
            # Make sure the project exists
            if not self.cli.project_exists(self.project):
                raise SnapTreeError("{0} is not a valid project".format(self.project))
            # Make sure the variant exist
            if not self.cli.variant_exists(self.project, self.variant):
                raise SnapTreeError("{0}/{1} is not a valid variant".format(self.project, self.variant))
        if snapshot:
            self.snapshot = snapshot
        else:
            # DI482: generate snap name snap-<normalized_source_BOM>_<>
            normalized_config = normalize_config_name(self.config)
            (year, ww, day) = get_ww_details()
            # http://pg-rdjira:8080/browse/DI-913
            # Double underscore instead of a single underscore
            snap_name = 'snap-{0}__{1}ww{2}{3}'.format(normalized_config, year, ww, day)
            self.snapshot = self.cli.get_next_snap(self.project, self.variant, snap_name)

        formatted_config = format_configuration_name_for_printing(self.project, self.variant, self.config)
        if not self.cli.config_exists(self.project, self.variant, self.config):
            raise SnapTreeError('{0} does not exist'.format(formatted_config))

        # Make sure the target does not exist
        if self.cli.config_exists(self.project, self.variant, self.snapshot):
            raise SnapTreeError('{0} already exists'.format(format_configuration_name_for_printing(self.project, self.variant, self.snapshot)))            

        if not self.snapshot.startswith('snap-'):
            raise SnapTreeError('{0} is not a valid snap configuration name. Snap configurations must have a prefix of snap-'.format(self.snapshot))

        # Create the source configuration that we need to walk
        self.logger.info('Building input configuration tree')
        self.source_cfg = ConfigFactory.create_from_icm(self.project, self.variant, self.config,
                                                   preview=self.preview)

        self.libtypes = []
        source_cfg_projects = list(set([x.project for x in self.source_cfg.flatten_tree()]))
        for source_cfg_project in source_cfg_projects:
            family = dmx.ecolib.ecosphere.EcoSphere().get_family(os.getenv("DB_FAMILY"))
            for libtype in libtypes:            
                if libtype.startswith('view'):
                    # Ensure views are valid
                    try:
                        viewobj = family.get_view(libtype)
                    except Exception as e:
                        self.logger.error('View ({}) does not exist'.format(libtype))
                        raise SnapTreeError(e)
                    # deliverables = [(source_cfg_project, x.deliverable) for x in viewobj.get_deliverables()]
                    deliverables = [x.deliverable for x in viewobj.get_deliverables()]
                    self.libtypes = self.libtypes + deliverables
                else:
                    # self.libtypes.append((source_cfg_project, libtype))
                    self.libtypes.append(libtype)
        self.libtypes = list(set(self.libtypes))                

    def run(self):
        '''
        The method that runs it all
        '''
        ret = 1

        self.reset_icm_tmpdir_env_var()

        if self.clashes_in_tree(self.source_cfg):
            raise SnapTreeError('Problems detected in {0}'.format(self.source_cfg.get_full_name()))

        snap_tree = self.build_snap_tree(self.source_cfg)
        if not snap_tree:
            self.logger.error('Problem building snap tree')
            ret = 1
        else:
            self.logger.info('Saving new configurations')
            if not self.preview:
                if snap_tree.save(shallow=False):
                    ret = 0
                    self.logger.info('Snap Tree {0} built'.format(snap_tree.get_full_name()))
                else:
                    ret = 1
                    self.logger.error('Problem saving {0}'.format(snap_tree.get_full_name()))
            else:
                self.logger.info('Snap Tree {0} built'.format(snap_tree.get_full_name()))
                ret = 0                    

        print(snap_tree.report(show_simple=True, show_libraries=True))
        self.final_snaptree = snap_tree

        return ret

    def reset_icm_tmpdir_env_var(self):
        '''
        https://jira.devtools.intel.com/browse/PSGDMX-2095
        Due to the fact that arc will kill the job if ARC_TEMP_STORAGE is >70G,
        we need to make sure that ICM_TMPDIR is not set to ARC_TEMP_STORAGE.
        '''
        os.environ['ICM_TMPDIR'] = os.getenv("ARC_TEMP_STORAGE") + '_dmxsnap'
        os.system("mkdir -p {}".format(os.environ['ICM_TMPDIR']))


    def snap_exists(self, project, variant, libtype=None):
        '''
        Returns True if the snapshot we're tyring to create
        already exists in any of the libtype's libraries
        '''
        if libtype:
            return self.cli.get_library_from_release(project, variant, libtype, self.snapshot)
        else:
            return self.cli.config_exists(project, variant, self.snapshot)

    def clashes_in_tree(self, root_config):
        '''
        Checks the configuration tree for potential clashes
        Clashes will occur if there are multiple composite configs from
        the same project/variant or the specified snap- config
        already exists but the reuse flag has not been set.

        :param root_config: The configuration tree
        :type root_config: CompositeConfig
        :return: Boolean indicating if there is a clash
        :type return: bool
        '''
        pv_clash = False
        snap_clash = False
        pv_count = {}

        for config in root_config.flatten_tree():
            if config.is_config():
                key = '{0}/{1}'.format(config.project, config.variant)
                if key in pv_count and config not in pv_count[key]:
                    pv_count[key].append(config)
                else:
                    pv_count[key] = [config]

                if not self.reuse and self.snap_exists(config.project, config.variant) and config.is_mutable():
                    self.logger.error('{0}/{1}@{2} already exists. Use the --reuse flag or choose a different snap- configuration name.'.format(
                        config.project, config.variant, self.snapshot
                    ))
                    snap_clash = True
            else:
                if not self.reuse and self.snap_exists(config.project, config.variant, libtype=config.libtype) and config.is_mutable():
                    self.logger.error('{0}/{1}:{2}@{3} already exists. Use the --reuse flag or choose a different snap- configuration name.'.format(
                        config.project, config.variant, config.libtype, self.snapshot
                    ))
                    snap_clash = True

        for key in list(pv_count.keys()):
            if len(pv_count[key]) > 1:
                self.logger.error('Multiple versions of {0} detected:'.format(key))
                self.logger.error('{}'.format(' '.join([x.get_full_name() for x in pv_count[key]])))
                pv_clash = True

        if pv_clash:
            self.logger.error('Use abnr buildconfig to create a single composite configuration where clashes have been reported.')

        return pv_clash or snap_clash

    def build_all_simple_snaps(self, source_config):
        '''
        Builds snap- configurations for all mutable simple configs in the tree, and
        adds them to the ConfigFactory.

        :param source_config: Source composite configuration
        :type source_config: CompositeConfig
        '''

        # Get the list of arguments for all simple snap- configs we're creating
        mp_args = []
        invalid_deliverables = []
        for config in source_config.flatten_tree():
            # We only want to build new configs for mutable, simple configs where a snap-
            # config of the same name doesn't already exist
            # Also we only want to build snap for deliverable that is part of roadmap            
            #if config.is_simple() and config.is_mutable() and not self.snap_exists(config.project, config.variant, libtype=config.libtype):
            if config.is_library() and not self.snap_exists(config.project, config.variant, libtype=config.libtype):
                # https://jira01.devtools.intel.com/browse/PSGDMX-21
                # Check if deliverable is part of roadmap
                family = dmx.ecolib.ecosphere.EcoSphere().get_family(os.getenv("DB_FAMILY"))
                try:
                    delobj = family.get_ip(config.variant, config.project).get_deliverable(config.libtype, roadmap=os.getenv("DB_DEVICE"))
                except:
                    invalid_deliverables.append((config.project, config.variant, config.libtype))
                    continue

                mp_args.append([config.project, config.variant, config.libtype, config.library, self.snapshot, self.description, self.changelist, self.preview])

        if invalid_deliverables:
            error_msg = 'The following deliverables found in {} are no longer part of roadmap. Please run \'dmx ip update\' for these IPs:'.format(source_config)
            for invalid_deliverable in invalid_deliverables:
                p, i, d = invalid_deliverable
                error_msg = '{}\n\t{}/{}@{}'.format(error_msg, p, i, d)
            raise SnapTreeError(error_msg)

        #####################################################
        ### FOR DEBUGGING: This section is to run in SERIES.
        ### if the parallelization is giving trouble, then use 
        ### this series run for workaround/debugging
        #####################################################
        results = []
        '''
        for p, v, l, c, s, d, cl, pv in mp_args:
            result = build_simple_snap(p, v, l, c, s, d, cl, pv)
            snap_config = IcmLibrary(result['project'], result['variant'], result['libtype'], result['library'], result['release'], preview=self.preview, use_db=False)
            snap_config._in_db = True
            snap_config._saved = True
            ConfigFactory.add_obj(snap_config)

        '''
        #####################################################
        ### FOR DEBUGGING: This section is to run in PARALLEL.
        ### if this parallel runs are giving unpredictable troubles 
        ### (which I've(Lionel) seen it happening to gdpxl), then 
        ### disable this section and use the above SERIES section
        ### for workaround/debugging.
        #####################################################
        if mp_args:
            results = run_mp(build_simple_snap, mp_args, num_processes=3)
            for result in results:
                if result['status']:
                    snap_config = IcmLibrary(result['project'], result['variant'], result['libtype'], result['library'], result['release'], preview=self.preview, use_db=False)
                    snap_config._in_db = True
                    snap_config._saved = True
                    ConfigFactory.add_obj(snap_config)
                else:
                    raise SnapTreeError('Problem creating configuration {0}/{1}:{2}@{3}'.format(result['project'], result['variant'], result['libtype'], result['config']))
       

    def build_snap_tree(self, source_config):
        '''
        Builds the new snaptree
        :param source_config: The source IC Manage configuration
        :type source_config: CompositeConfig
        :return:
        '''
        # Filter the input tree before cloning
        filtered_tree = self.filter_tree(source_config)

        # Create a clone of the tree
        snap_tree = filtered_tree.clone(self.snapshot)
        if self.description:
            snap_tree.description = self.description

        # Build the simple snap- configs and add them to the ConfigFactory
        self.build_all_simple_snaps(snap_tree)

        config_to_snap = snap_tree.get_next_mutable_config()
        while config_to_snap is not None:
            self.logger.debug('Processing mutable config {0}'.format(config_to_snap.get_full_name()))
            snapped_config = self.snap_config(config_to_snap)
            # If we're snapping the very top level replace in tree
            # won't help, switch out the objects
            if config_to_snap == snap_tree:
                self.logger.debug('Processed top of tree so replacing')
                snap_tree = snapped_config
            else:
                self.logger.debug('Replacing {0} with {1} in {2}'.format(config_to_snap.get_full_name(),
                                                                         snapped_config.get_full_name(),
                                                                         snap_tree.get_full_name()))
                snap_tree.replace_object_in_tree(config_to_snap, snapped_config)

            config_to_snap = snap_tree.get_next_mutable_config()

        return snap_tree

    def filter_tree(self, tree):
        '''
        Applies the variant and libtype filters to the tree
        :param tree: The tree to be filtered
        :type tree: CompositeConfig
        :return: Filtered tree
        :type return: CompositeConfig
        '''

        if self.variants:
            tree = self.apply_variant_filter_to_tree(tree)

        if self.libtypes:
            tree = self.apply_libtypes_filter_to_tree(tree)

        return tree

    def apply_libtypes_filter_to_tree(self, tree):
        '''
        Applies the libtype filters to the tree
        :param tree: Tree to be filtered
        :type tree: CompositeConfig
        :return: Filtered tree
        :type return: CompositeConfig
        '''
        configs_to_remove = []
        # We only want to remove libtypes from mutable composites
        composite_configs = [x for x in tree.flatten_tree() if x.is_config()]
        for config in composite_configs:
            if config.is_mutable():
                for sub_config in config.configurations:
                    # if not sub_config.is_config() and (sub_config.project, sub_config.libtype) not in self.libtypes:
                    if not sub_config.is_config() and sub_config.libtype not in self.libtypes:
                        self.logger.debug('Removing simple config {0}'.format(sub_config))
                        configs_to_remove.append(sub_config)

        tree.remove_objects_from_tree(configs_to_remove)

        # Remove any empty composite configurations that are now present in the tree
        tree.remove_empty_configs()

        return tree

    def apply_variant_filter_to_tree(self, tree):
        '''
        Applies the variant filters to the tree
        :param tree: Tree to be filtered
        :type tree: CompositeConfig
        :return: Filtered tree
        :type return: CompositeConfig
        '''
        configs_to_remove = [x for x in tree.flatten_tree() if x.variant not in self.variants]
        tree.remove_objects_from_tree(configs_to_remove)

        # Remove any empty composite configurations that are now present in the tree
        tree.remove_empty_configs()

        return tree

    def snap_config(self, config_to_snap):
        '''
        Snaps a configuration and it's simple configs
        :param config_to_snap: The composite configuration to snap
        :type config_to_snap: CompositeConfig
        :return: The snapped configuration
        :type return: CompositeConfig
        '''
        ret = None
        if self.snap_exists(config_to_snap.project, config_to_snap.variant):
            if self.reuse:
                ret = ConfigFactory.create_from_icm(config_to_snap.project, config_to_snap.variant, self.snapshot, preview=self.preview)
            else:
                raise SnapTreeError('{0} already exists'.format(format_configuration_name_for_printing(config_to_snap.project, config_to_snap.variant, self.snapshot)))
        else:
            # If config_to_snap.config is already self.snapshot that
            # means we're most likely processing the top of the tree.
            # No need to clone again
            if config_to_snap.config == self.snapshot:
                snapped_config = config_to_snap
            else:
                snapped_config = config_to_snap.clone(self.snapshot)
                if self.description:
                    snapped_config.description = self.description

            # We don't want to modify the list of sub configs while
            # iterating through it, so store the original + replacement
            # in a separate list that can be walked through afterwards
            replacement_pairs = []

            # We should only have to deal with simple configurations at this point
            for sub_config in config_to_snap.configurations:
                #if sub_config.is_simple() and sub_config.is_mutable():
                if sub_config.is_library():
                    # Get this sub config's snap- config from the factory
                    snapped_sub_config = ConfigFactory.get_obj(sub_config.project, sub_config.variant, self.snapshot, sub_config.libtype)
                    replacement_pairs.append([sub_config, snapped_sub_config])

            for pair in replacement_pairs:
                snapped_config.replace_object_in_tree(pair[0], pair[1])

            if self.preview:
                # Return a fake config
                ret = snapped_config
            else:                
                if snapped_config.save():                
                    ret = snapped_config
                else:
                    raise SnapTreeError('Problem saving {0}'.format(snapped_config.get_full_name()))

        return ret

# Pool processing tasks are simpler to work with if they live outside
# of the class
def get_release_number(project, variant, libtype, library, max_changenum, preview, config=None):
    '''
    'Gets' the release number for the given IC Manage library
    This can either be retreiving the last release or creating a
    new release and returning that, if necessary
    :param project: The IC Manage project
    :type project: str
    :param variant: The IC Manage variant
    :type variant: str
    :param libtype: The IC Manage library type
    :type libtype: str
    :param library: The IC Manage library
    :type library: str
    :param max_changenum: The maximum changenumber we can release
    :type max_changenum: int
    :param preview: Flag indicating whether or not we're running in preview mode
    :type preview: bool
    :return: The release number
    :type return: int
    '''
    release = 0
    changenum = 0
    cli = ICManageCLI(preview=preview)
    # Make sure max_changenum is an int
    max_changenum = int(max_changenum)

    family = dmx.ecolib.ecosphere.EcoSphere(preview=preview).get_family(os.getenv("DB_FAMILY"))
    delobj = family.get_ip(variant, project).get_deliverable(libtype, roadmap=os.getenv("DB_DEVICE"))
    dm = delobj.dm
    if dm == 'designsync':                
        dm_meta = delobj.dm_meta
        # Before releasing library, we need to add filelist to the libtype so that it gets released together
        dssc = dmx.abnrlib.dssc.DesignSync(dm_meta['host'], dm_meta['port'], preview=preview)
        dssc.add_filelist_into_icmanage_deliverable(project, variant, libtype, config, library, dm_meta)        

        # For designsync library, need to always take the latest changelist to get the filelist that we just added in
        outstanding_changes = sorted(cli.get_list_of_changelists(project, variant, libtype, library=library))
        if not preview:
            changenum = int(outstanding_changes[-1])
        else:
            # for preview run
            changenum = 0
    else:
        # Are there any outstanding changes equal to or lower than max_changenum?
        outstanding_changes = cli.get_list_of_changelists(project, variant, libtype, library=library)
        for change in outstanding_changes:
            # Convert it to an integer so int comparisons work
            int_change = int(change)
            if int_change > changenum and int_change <= max_changenum:
                changenum = int_change

    if changenum:
        release = cli.add_library_release_up_to_changelist(project, variant, libtype, library,
                                                           '', upper_changenum=changenum)
    else:
        release = cli.get_library_release_closest_to_changelist(project, variant, libtype, library,
                                                                max_changenum)

    if int(release) < 1:
        err_msg = 'Release number {0} is not a valid release number'.format(release)
        err_msg += '\nThere is a problem with {0}/{1}:{2}/{3}. The library may be empty.'.format(
            project, variant, libtype, library
        )
        err_msg += '\nContact psgicmsupport@intel.com for help.'
        raise BadReleaseNumberError(err_msg)

    return release

def build_simple_snap(project, variant, libtype, config, snap_name, description, max_changelist, preview):
    '''
    Builds a simple snap- configuration in a multiprocessing friendly way.

    :param project: The IC Manage project
    :type project: str
    :param variant: The IC Manage variant
    :type variant: str
    :param libtype: The IC Manage libtype
    :type libtype: str
    :param config: The source IC Manage configuration
    :type config: str
    :param snap_name: The name of the new snap- configuration
    :type snap_name: str
    :param description: The description for the new config
    :type description: str
    :param max_changelist: The maximum changelist to release against, if necessary
    :type max_changelist: int
    :param preview: Boolean indicating whether or not we're in preview mode
    :type preview: bool
    :return: Dictionary containing save status and new configuration details
    :rtype: dict
    '''
    save_status = False
    source_config = ConfigFactory.create_from_icm(project, variant, config, libtype=libtype, preview=preview)

    snap_config = source_config.clone(snap_name)
    if description:
        snap_config.description = description

    '''
    if snap_config.is_active_dev() or snap_config.is_active_rel():
        snap_config.lib_release = get_release_number(project, variant, libtype, snap_config.library, max_changelist, preview, config=config)
    '''
    snap_config.changenum = max_changelist
    save_status = snap_config.save()

    return {
        'project' : snap_config.project,
        'variant' : snap_config.variant,
        'libtype' : snap_config.libtype,
        'config' : snap_config.name,
        'library' : snap_config.library,
        'release' : snap_config.lib_release,
        'status' : save_status,
    }
        
