#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/releasevariant.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr "releasevariantiant" subcommand plugin
Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
from __future__ import print_function
from builtins import object
import sys
import logging
import textwrap
import itertools
import os
from pprint import pprint

from dmx.abnrlib.icm import ICManageCLI
#from dmx.abnrlib.icmcompositeconfig import CompositeConfig
#from dmx.abnrlib.icmsimpleconfig import SimpleConfig
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.releasesubmit import submit_release, ReleaseJobHandler, \
    get_tnr_dashboard_url_for_id, convert_waiver_files
from dmx.utillib.utils import get_abnr_id, format_configuration_name_for_printing, get_thread_and_milestone_from_rel_config, get_thread_and_milestone_from_prel_config
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.releaseinputvalidation import validate_inputs
import dmx.ecolib.ecosphere
import dmx.syncpointlib.syncpoint_plugins.check
import dmx.syncpointlib.composite_configs 
import dmx.syncpointlib.syncpoint_webapi
from dmx.utillib.arcenv import ARCEnv
# import dmx.abnrlib.certificate_db   # http://pg-rdjira:8080/browse/DI-1244
import dmx.abnrlib.flows.checkconfigs

class ReleaseVariantError(Exception): pass

class ReleaseVariant(object):
    '''
    Runs the releasevariantiant command
    '''

    def __init__(self, project, variant, config, milestone, thread, description, 
                 label=None, wait=False, waiver_files=None, 
                 force=False, preview=True, from_releasetree=False, views=[], syncpoint='', 
                 skipsyncpoint='', skipmscheck='', regmode=False, prel=None):
        self.project = project
        self.variant = variant
        self.config = config
        self.milestone = milestone
        self.thread = thread
        self.label = label
        self.description = description
        self.preview = preview
        self.cli = ICManageCLI(preview=preview)
        self.logger = logging.getLogger(__name__)
        self.wait = wait
        self.waivers = None
        self.rel_config = None
        self.force = force
        self.from_releasetree = from_releasetree
        self.views = views
        self.prel = prel
        self.syncpoint = syncpoint
        self.skipsyncpoint = skipsyncpoint
        self.skipmscheck = skipmscheck
        self.regmode = regmode
        
        self.family = dmx.ecolib.ecosphere.EcoSphere().get_family_for_thread(self.thread)
        self.roadmap = dmx.ecolib.ecosphere.EcoSphere().get_roadmap_for_thread(self.thread)

        if self.views and self.prel:
            raise ReleaseVariantError("Prel:{} and Views:{} can not be used concurrently.".format(self.prel, self.views))

        # If project not given, get project from ARC
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise ReleaseVariantError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
             # Make sure the project exists
            if not self.cli.project_exists(self.project):
                raise ReleaseVariantError("{0} is not a valid project".format(self.project))
            # Make sure the variant exist
            if not self.cli.variant_exists(self.project, self.variant):
                raise ReleaseVariantError("{0}/{1} is not a valid variant".format(self.project, self.variant))

        # If milestone not given, get milestone from ARC
        if not self.milestone:
            self.milestone = ARCEnv().get_milestone()
        # If thread not given, get thread from ARC
        if not self.thread:
            self.thread = ARCEnv().get_thread()
        self.logger.info('Releasing with milestone {} and thread {}'.format(self.milestone, self.thread))            

        formatted_config_name = format_configuration_name_for_printing(self.project,
                                                                       self.variant,
                                                                       self.config)

        # If we get here from releasetree and preview is set, we don't run this check
        if not from_releasetree or not self.preview:            
            if not self.cli.config_exists(self.project, self.variant, self.config):
                raise ReleaseVariantError('{0} does not exist'.format(formatted_config_name))

        # Common release input validation
        validate_inputs(self.project, self.milestone, self.thread, self.label,
                        waiver_files)

        if waiver_files is not None:
            self.waivers = convert_waiver_files(waiver_files)        

        # THIS SECTION HAS TO BE REVISITED IN THE FUTURE AS SYNCPOINT APIS ARE STILL USING
        # COMPOSITE CONFIG HIERARCHY MODULE WHICH HAS BEEN DEPRECATED
        # http://pg-rdjira:8080/browse/DI-1060
        # If syncpoint is given, cross check with the given config
        if syncpoint:
            self.spapi =  dmx.syncpointlib.syncpoint_webapi.SyncpointWebAPI()
            if not self.spapi.syncpoint_exists(syncpoint):
                syncpoints = self.spapi.get_syncpoints()
                self.logger.info('Valid syncpoints are:')
                for syncpoint, category in sorted(syncpoints):
                    print('\t{}'.format(syncpoint))
                raise ReleaseVariantError('Syncpoint {} does not exist'.format(self.syncpoint))

            '''
            #check if syncpoint has any conflict in its configuration tree
            checkconflict = dmx.syncpointlib.syncpoint_plugins.check.CheckConflict(self.syncpoint)
            if checkconflict.get_list_of_conflicts():
                checkconflict.print_conflicts()
                raise ReleaseVariantError("Syncpoint {} has conflicts, please run syncpoint check first. DMX cannot release {} against this syncpoint.".format(self.syncpoint, self.variant))

            #check for conflicts with the variant to be released
            checkconflict.check_config_conflict(self.project, self.variant, self.config)
            if checkconflict.get_list_of_conflicts():
                checkconflict.print_conflicts()
                raise ReleaseVariantError("{0}/{1}@{2} conflicts with BOMs in syncpoint {3}. Release aborted.".format(self.project, self.variant, self.config, self.syncpoint))
            '''
            cc = dmx.abnrlib.flows.checkconfigs.CheckConfigs(project=self.project, variant=self.variant, config=self.config, syncpoints=[self.syncpoint])
            self.conflicts = cc.run()
            if self.conflicts and not self.nocheck:
                self.LOGGER.error("Conflicts found ! Program aborted")
                self.LOGGER.error(pformat(self.conflicts))
                raise ReleaseError("{0}/{1}@{2} conflicts with configurations in syncpoint {3}. Release aborted.".format(self.project,self.variant,self.config,self.syncpoint))            
             

        # Finally, as all checks must have passed to get here let's set up
        # the Splunk log
        self.abnr_id = get_abnr_id()

    def verify_variant(self):
        '''
        Verifies that the variant has been created correctly
        '''
        ret = False
        variant_properties = self.cli.get_variant_properties(self.project, self.variant)
        if 'iptype' not in variant_properties:
            self.logger.error("Variant {0} has no type - it was not created with createvariant".format(self.variant))
            ret = False
        else:
            ret = True

        return ret

    def verify_config(self, cfg):
        '''
        Verifies that cfg is ready to be submitted to the gated release system
        The config should only contain REL configs
        The config must contain a local ipsepc reference - project/variant:ipspec@REL...
        '''
        self.logger.info("Checking configuration {0}".format(
            format_configuration_name_for_printing(self.project, self.variant,
                                                   self.config)
        ))

        non_rel = False
        ipspec_found = False
        matching_milestone = False
        unreleased_configs = []

        if not self.prel:
            for sub_config in cfg.configurations:
                if not sub_config.is_released(shallow=False):
                    unreleased_configs += [x for x in sub_config.flatten_tree() if not x.is_released(shallow=True)]
        else:
            for sub_config in cfg.configurations:
                if not sub_config.is_preleased(shallow=False):
                    unreleased_configs += [x for x in sub_config.flatten_tree() if not x.is_preleased(shallow=True)]

        if unreleased_configs:
            non_rel = True
            msg = '{0} contains the following unreleased BOMs:\n'.format(cfg.get_full_name())
            for config in sorted([x.get_full_name() for x in unreleased_configs]):
                msg = '{}\t{}\n'.format(msg, config)
            self.logger.error(msg)

        local_ipspecs = cfg.search(project=self.project, variant=self.variant, libtype='ipspec')
        if not local_ipspecs:
            self.logger.error("{0} does not contain an ipspec from {1}/{2}".format(
                cfg.get_full_name(), self.project, self.variant
            ))
        else:
            ipspec_found = True
    
        # http://pg-rdjira:8080/browse/DI-1179
        # If skipmscheck is provided, don't check for under-delivery milestone
        if not self.skipmscheck:            
            matching_milestone = self.verify_release_matching_milestones(cfg)
        else:
            matching_milestone = True

        return not non_rel and ipspec_found and matching_milestone

    def verify_release_matching_milestones(self, cfg):
        '''
        http://pg-rdjira:8080/browse/DI-653
        Ensure that every released config's milestone is greater or equal to the milestone to release
        '''
        ret = False
        # Get all released simple configs in the tree - all the releases here are required for ip release
        if not self.prel:
            released_simple_configs = [x for x in cfg.configurations if not x.is_config() and x.is_released()]
        else:
            released_simple_configs = [x for x in cfg.configurations if not x.is_config() and x.is_preleased()]
        
        if self.prel:
            func = get_thread_and_milestone_from_prel_config
        else:
            func = get_thread_and_milestone_from_rel_config
        errors = []
        for simple_config in released_simple_configs:
            thread, milestone = func(simple_config.name)
            if milestone < self.milestone:
                errors.append(simple_config.get_full_name())

        # Get all released composite configs in the tree - all the releases here are required for final ip release
        if not self.prel:
            released_composite_configs = [x for x in cfg.configurations if x.is_config() and x.is_released()]
        else:
            released_composite_configs = [x for x in cfg.configurations if x.is_config() and x.is_preleased()]
        # cdb = dmx.abnrlib.certificate_db.CertificateDb(usejson=True) # http://pg-rdjira:8080/browse/DI-1244
        for composite_config in released_composite_configs:
            thread, milestone = func(composite_config.config)
            if milestone < self.milestone:
                errors.append(composite_config.get_full_name())
                '''
                ### This is for Recertified. http://pg-rdjira:8080/browse/DI-1244
                if cdb.is_certified(self.thread, self.milestone, composite_config.project, composite_config.variant, composite_config.config):
                    self.logger.debug("{}/{}@{} certified for {}/{}.".format(composite_config.project, composite_config.variant, composite_config.config, self.thread, self.milestone))
                else:
                    self.logger.debug("{}/{}@{} not certified for {}/{}.".format(composite_config.project, composite_config.variant, composite_config.config, self.thread, self.milestone))
                    errors.append(composite_config.get_full_name())
                '''
        if errors:
            error_msg = '{} contains the following BOMs that don\'t match milestone {}:\n'.format(cfg.get_full_name(), self.milestone)
            for error in sorted(errors):
                error_msg = '{}\t{}\n'.format(error_msg, error)
            # http://pg-rdjira:8080/browse/DI-1084
            # Reinstate error status 
            raise ReleaseVariantError(error_msg)
            ret = True
        else:
            ret = True  
            
        return ret                    

    def get_rels_for_milestone_and_thread(self):
        '''
        Returns a list of REL configurations for against
        self.milestone and self.thread
        '''
        all_rel_configs = self.cli.get_rel_configs(self.project, self.variant)
        # We only want to consider REL configs of the same milestone and thread
        rel_config_prefix = 'REL{0}{1}'.format(self.milestone, self.thread)

        return [x for x in all_rel_configs if x.startswith(rel_config_prefix)]

    def is_config_already_released(self, src_config):
        '''
        Checks if there are any REL composite configurations within self.variant
        that were released against the same milestone/thread with the same sub-configs
        '''
        match_found = False

        if self.prel:
            return match_found


        if not self.force:
            retkeys = ['project:parent:name', 'variant:parent:name', 'libtype:parent:name', 'name']

            config_details = self.cli.get_config(self.project, self.variant, self.config, retkeys=retkeys)
            goldref = []
            for e in config_details:
                goldref.append('{}/{}:{}@{}'.format(e['project:parent:name'], e['variant:parent:name'], e['libtype:parent:name'], e['name']))
            goldref = sorted(goldref)
            
            rel_configs = self.get_rels_for_milestone_and_thread()
            for rel_config in rel_configs:
                config_details = self.cli.get_config(self.project, self.variant, rel_config, retkeys=retkeys)
                ref = []
                for e in config_details:
                    ref.append('{}/{}:{}@{}'.format(e['project:parent:name'], e['variant:parent:name'], e['libtype:parent:name'], e['name']))
                ref = sorted(ref)

                if goldref == ref:
                    match_found = True
                    self.logger.info('{0}/{1}@{2} has already been released and has identical content to {3}'.format(self.project, self.variant, rel_config, src_config.get_full_name()))
                    break

        return match_found

    def get_config(self):
        '''
        Gets the cCompositeConfig object that references project/variant@config
        '''
        self.logger.info("Loading configuration tree")
        if not self.from_releasetree or not self.preview:
            return ConfigFactory.create_from_icm(self.project, self.variant, self.config, preview=self.preview)
        else:
            # If we come from releasetree and preview is set, we return fake data
            # Our fake composite config must have ipspec, so we create a fake REL ipspec
            ipspec = SimpleConfig('REL{0}{1}__YYww123z'.format(self.milestone, self.thread),
                                  self.project, self.variant, 'ipspec',
                                  'dev', '1', preview=self.preview, 
                                  use_db=False)
            return CompositeConfig(self.config, self.project, self.variant, [ipspec], preview=self.preview)

    def create_snap_cfg(self, src_config):
        '''
        Creates a snap configuration based upon src_config
        '''
        ret = None

        snap_number = self.cli.get_next_snap_number(src_config.project, src_config.variant)
        try:
            int(snap_number)
        except ValueError:
            self.logger.error("{0} is not a valid snap number".format(snap_number))
            raise

        snap_cfg = src_config.clone('snap-{}'.format(snap_number))
        if snap_cfg:
            snap_cfg.description = self.description
            if snap_cfg.save(shallow=True):
                self.logger.info("Created snap configuration {0}".format(snap_cfg.get_full_name()))
                ret = snap_cfg

        return ret

    def send_to_queue(self, snap_cfg):
        '''
        Sends the release request to the queue
        '''
        ret = False
        result, arc_job_id = submit_release(snap_cfg, self.config, self.milestone, self.thread, 
                         self.label, self.abnr_id,
                         preview=self.preview, libtype=None, 
                         waivers=self.waivers, description=self.description,
                         views=self.views, syncpoint=self.syncpoint, skipsyncpoint=self.skipsyncpoint, 
                         skipmscheck=self.skipmscheck, regmode=self.regmode, prel=self.prel)
        if result:                         
            self.logger.info("{0} has been submitted to the gated release system".format(
                snap_cfg.get_full_name()))
            self.logger.info("Go here: {0} to view your release".format(
                get_tnr_dashboard_url_for_id(self.abnr_id, self.project, os.getenv('USER'), self.variant, 'None')))
            self.logger.info('Your release job ID is {}'.format(arc_job_id))
            if self.wait and not self.preview:
                # Register our callback handler with the queue
                # In this case the callback handler will ultimately exit
                handler = ReleaseJobHandler(arc_job_id)
                handler.wait_for_job_completion()
                if handler.rel_config is not None:
                    self.rel_config = handler.rel_config
                    ret = True
                    self.logger.info('Release {0} created'.format(
                        format_configuration_name_for_printing(self.project, self.variant,
                                                               self.rel_config)
                    ))
                else:
                    ret = False
                    self.logger.warn('Release of {0}/{1} was not successful. Check the dashboard for more details'.format(self.project,
                                                                                                                          self.variant))
                    ### report out release errors
                    cmd = 'dmx release report -a {}'.format(arc_job_id)
                    os.system(cmd)

            elif self.wait and self.preview:
                # Set a bogus REL and move on
                ret = True
                self.rel_config = 'REL{0}{1}__YYww123z'.format(self.milestone, self.thread)
                self.logger.info('Release {0} created'.format(
                        format_configuration_name_for_printing(self.project, self.variant,
                                                               self.rel_config)
                    ))
            else:
                ret = True
        else:
            self.logger.error("Problem submitting {0} to the gated release system".format(
                snap_cfg.get_full_name()))
            ret = False

        return ret

    def filter_tree(self, root_config):
        '''
        Filters root_config to remove any configurations not needed for the thread/milestone

        :param root_config: The root IC Manage configuration object
        :type root_config: CompositeConfig
        '''
        # Filter deliverables that are not needed to be delivered for the variant
        ipspec_config = root_config.search(project='^{}$'.format(self.project),
                                           variant='^{}$'.format(self.variant),
                                           libtype='^{}$'.format('ipspec'))
        if not ipspec_config:
            self.logger.error("{0} does not contain an ipspec from {1}/{2}".format(root_config.get_full_name(), self.project, self.variant))
        else:
            ipspec_config = ipspec_config[0]

        all_simple_configs = [x for x in root_config.configurations if not x.is_config()]
        
        # Now apply the filters to the tree
        for simple_config in all_simple_configs:
            if self.is_unneeded(simple_config, ipspec_config):
                root_config.remove_object_from_tree(simple_config)

        # Only apply the filter to unreleased simple configs
        # that aren't ipspec
        if not self.prel:
            unreleased_simple_configs = [x for x in root_config.configurations if not x.is_config() and not x.is_released()]
        else:
            unreleased_simple_configs = [x for x in root_config.configurations if not x.is_config() and not x.is_preleased()]
        unreleased_simple_configs = [x for x in unreleased_simple_configs if x.libtype != 'ipspec']
        
        # Now apply the filters to the tree
        for unreleased_simple in unreleased_simple_configs:
            if not self.should_release_config(unreleased_simple):
                root_config.remove_object_from_tree(unreleased_simple)

        return root_config                

    def should_release_config(self, simple_config):
        '''
        Checks if simple_config should be released
        Returns True if it should, False if it shouldn't
        :param simple_config: Simple Configuration being checked
        :type simple_config: SimpleConfig
        :return: bool
        '''
        ret = True

        # Do we need to release this config according to the roadmap?
        if not self.is_libtype_required_by_milestone_and_thread(simple_config):
            ret = False

        return ret                

    def is_libtype_required_by_milestone_and_thread(self, simple_config):
        '''
        Determines if the content referenced by simple_config is required to be
        released within this milestone/thread combination
        :param simple_config: The Simple Config being considered for release
        :return: bool
        '''
        ret = False

        product = self.thread[:3]
        ip = self.family.get_ip(simple_config.variant, simple_config.project)
        required_libtypes = [x.deliverable for x in ip.get_all_deliverables(milestone=self.milestone, roadmap=self.roadmap)]

        if simple_config.libtype in required_libtypes:
            ret = True

        return ret

    def is_unneeded(self, simple_config, ipspec_config):
        '''
        Determines if the simple config is needed to be delivered per ipspec
        :param simple_config: The Simple Config being considered for release
        :return: bool
        '''
        ret = False

        product = self.thread[:3]
        ip = self.family.get_ip(simple_config.variant, simple_config.project)
        if self.preview:
            # For preview run, if we failed to get unneeded_libtypes, just set it none
            try:
                unneeded_libtypes = [x.deliverable for x in ip.get_unneeded_deliverables(bom='ipspec@{}'.format(ipspec_config.name), local=False, roadmap=self.roadmap)]
            except:
                unneeded_libtypes = []
        else:
            unneeded_libtypes = [x.deliverable for x in ip.get_unneeded_deliverables(bom='ipspec@{}'.format(ipspec_config.name), local=False, roadmap=self.roadmap)]

        if simple_config.libtype in unneeded_libtypes:
            ret = True

        return ret

    def run(self):
        '''
        Runs the releasevariantiant command
        '''
        ret = 1

        if self.verify_variant():
            cfg = self.get_config()

            # Filter the configuration tree to remove anything we don't need
            cfg = self.filter_tree(cfg)

            if self.verify_config(cfg):
                # Has this content already been released for this milestone and thread?
                if self.is_config_already_released(cfg):
                    ret = 0
                else:
                    # If the input config is mutable we need to create a snap
                    # If it's immutable then we just re-use it
                    if cfg.is_mutable():
                        snap = self.create_snap_cfg(cfg)
                    else:
                        snap = cfg

                    if snap:
                        if self.send_to_queue(snap):
                            ret = 0
                        else:
                            ret = 1
                    else:
                        self.logger.error("Problem building snap configuration from {0}".format(
                            cfg.get_full_name()))

        return ret
