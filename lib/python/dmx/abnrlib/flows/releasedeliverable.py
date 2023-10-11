#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/releasedeliverable.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr "releaselibrary" subcommand plugin
Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.
'''
import sys
import logging
import textwrap
import itertools
import os

from dmx.abnrlib.icm import ICManageCLI
#from dmx.abnrlib.icmsimpleconfig import SimpleConfig
#from dmx.abnrlib.icmcompositeconfig import CompositeConfig
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.releasesubmit import submit_release, ReleaseJobHandler, get_tnr_dashboard_url_for_id, convert_waiver_files
from dmx.utillib.utils import get_abnr_id, is_rel_config_against_this_thread_and_milestone, \
    format_configuration_name_for_printing
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.releaseinputvalidation import validate_inputs
import dmx.ecolib.ecosphere 
from dmx.utillib.admin import get_dmx_admins
from dmx.utillib.arcenv import ARCEnv
import dmx.abnrlib.dssc

class ReleaseDeliverableError(Exception): pass

class ReleaseDeliverable(object):
    '''
    Class that runs the releaselibrary command
    '''

    def __init__(self, project, ip, deliverable, bom, milestone,
                 thread, description, label=None, 
                 wait=False, force=False, preview=True, from_releaseview=False, views=[], regmode=False):
        self.project = project
        self.variant = ip
        if deliverable.startswith("prel_"):
            self.prel, self.libtype = deliverable.split(':')
        else:
            self.prel = None
            self.libtype = deliverable
        self.config = bom
        self.milestone = milestone
        self.thread = thread
        self.label = label
        self.description = description
        self.preview = preview
        self.cli = ICManageCLI(preview=preview)
        self.logger = logging.getLogger(__name__)
        self.wait = wait
        self.rel_config = None
        self.force = force        
        self.from_releaseview = from_releaseview
        self.views = views
        self.regmode = regmode
        
        self.family = dmx.ecolib.ecosphere.EcoSphere().get_family_for_thread(self.thread)
        self.roadmap = dmx.ecolib.ecosphere.EcoSphere().get_roadmap_for_thread(self.thread)
        self.logger.debug("ReleaseDeliverable: self.roadmap: {}".format(self.roadmap))

        # If project not given, get project from ARC
        if not self.project:
            self.logger.info('Reading from ARC environment')
            arc_projects = ARCEnv().get_project()
            for arc_project in arc_projects:
                if self.cli.variant_exists(arc_project, self.variant):
                    self.project = arc_project
                    break
            if not self.project:
                raise ReleaseDeliverableError('Variant {0} is not found in projects: {1}'.format(self.variant, arc_projects))
        else:
            # Make sure the project exists
            if not self.cli.project_exists(self.project):
                raise ReleaseDeliverableError("{0} is not a valid project".format(self.project))
            # Make sure the variant exist
            if not self.cli.variant_exists(self.project, self.variant):
                raise ReleaseDeliverableError("{0}/{1} is not a valid variant".format(self.project, self.variant))

        # If milestone not given, get milestone from ARC
        if not self.milestone:
            self.milestone = ARCEnv().get_milestone()
        # If thread not given, get thread from ARC
        if not self.thread:
            self.thread = ARCEnv().get_thread()
        self.logger.info('Releasing with milestone {} and thread {}'.format(self.milestone, self.thread))
            
        # Make sure the libtype exist
        if not self.cli.libtype_exists(self.project, self.variant, self.libtype):
            raise ReleaseDeliverableError("{0}/{1}:{2} is not a valid libtype".format(self.project, self.variant, self.libtype))
        # If we get here from releaseview and preview is set, we don't run this check
        if not from_releaseview or not self.preview:                    
            #  Make sure the variant@config exist
            if not self.cli.config_exists(self.project, self.variant, self.config):
                raise ReleaseDeliverableError('{}/{}@{} does not exist'.format(self.project, self.variant, self.config))
        
        # Make sure the libtype is defined within the system
        if not self.cli.libtype_defined(self.libtype):
            raise ReleaseDeliverableError('Libtype {0} is not defined within the system.'.format(self.libtype))

        # Common release input validation
        validate_inputs(self.project, self.milestone, self.thread, self.label,
                        waiver_files=[])            

        if not self.from_releaseview or not self.preview:
            # Make sure variant@config has ipspec config and the libtype@config to be released           
            self.source_cfg = ConfigFactory.create_from_icm(self.project, self.variant,
                                                   self.config, preview=self.preview)
        else:
            # If we come from releaseview and preview is set, we return fake data
            # Our fake composite config must have ipspec, so we create a fake REL ipspec
            ipspec = SimpleConfig('dev', self.project, self.variant, 'ipspec',
                                  'dev', '1', preview=self.preview, 
                                  use_db=False)
            # Our fake composite config must have the libtype to be released
            libtype_to_release = SimpleConfig('dev', self.project, self.variant, 
                                  self.libtype, 'dev', '1', preview=self.preview, 
                                  use_db=False)
            self.source_cfg = CompositeConfig(self.config, self.project, self.variant, 
                                     [ipspec, libtype_to_release], preview=self.preview)
           
        ipspec =  self.source_cfg.search(project=self.project, 
                               variant='^{}$'.format(self.variant), 
                               libtype='^ipspec$')
        if not ipspec:
            raise ReleaseDeliverableError('{}/{}@{} does not contain an IPSPEC BOM'.format(self.project, self.variant, self.config))
        libtype_to_release =  self.source_cfg.search(project=self.project, 
                                           variant='^{}$'.format(self.variant), 
                                           libtype='^{}$'.format(self.libtype))
        if not libtype_to_release:
            raise ReleaseDeliverableError('{}/{}@{} does not contain {} BOM to be released'.format(self.project, self.variant, self.config, self.libtype))

        # http://pg-rdjira:8080/browse/DI-1407
        # if libtype is unneeded, abort release
        unneeded_deliverables = [x.deliverable for x in self.family.get_ip(self.variant, self.project).get_unneeded_deliverables(local=False, bom=self.config, roadmap=self.roadmap)]
        if self.libtype in unneeded_deliverables:
            raise ReleaseDeliverableError('Deliverable {} is marked as unneeded. Release aborted.'.format(self.libtype))
                
         # https://jira01.devtools.intel.com/browse/PSGDMX-21
        # Check if deliverable is part of roadmap
        try:
            delobj = self.family.get_ip(self.variant, self.project).get_deliverable(self.libtype, roadmap=self.roadmap, milestone=self.milestone)
        except Exception as e:
            self.logger.error(str(e))
            raise ReleaseDeliverableError('Failed to release, deliverable {} is no longer part of roadmap.'.format(self.libtype))


        # Finally, as all checks must have passed to get here let's set up
        # the Splunk log
        self.abnr_id = get_abnr_id()
        
    def build_composite_placeholder(self, src_variant_config, src_libtype_config, snap_config):
        '''
        Builds a composite tnr-placeholder configuration from src_variant_config
        referencing snap_config to be released by replacing src_libtype_config
        Returns the config if successful
        Returns None if there's an error
        '''
        ret = None

        next_placeholder_number = self.cli.get_next_tnr_placeholder_number(self.project, 
                                                                    self.variant, src_libtype_config.libtype)
        composite_placeholder_cfg = src_variant_config.clone('tnr-placeholder-{0}-{1}-{2}'.format(src_variant_config.variant, src_libtype_config.libtype, next_placeholder_number))
        # http://pg-rdjira:8080/browse/DI-1251
        # Replace only if configs are different
        if src_libtype_config != snap_config:
            composite_placeholder_cfg.replace_object_in_tree(src_libtype_config, snap_config)

        if composite_placeholder_cfg.save(shallow=False):
            ret = composite_placeholder_cfg

        return ret

    def build_simple_snap(self, src_config, release):
        '''
        Builds a new simple snap configuration referencing release
        Returns the snap configuration object if successful
        Returns None if there's an error
        '''
        ret = None

        next_snap_number = self.cli.get_next_snap_number(src_config.project, src_config.variant,
            libtype=src_config.libtype, simple=True)
        simple_snap_cfg = SimpleConfig("snap-{0}".format(next_snap_number), src_config.project,
            src_config.variant, src_config.libtype, src_config.library, release,
            preview=self.preview, description=self.description)

        if simple_snap_cfg.save():
            ret = simple_snap_cfg

        return ret

    def send_to_queue(self, placeholder_cfg, libtype):
        '''
        Dispatches a composite config to the gated release queue.
        The config will include the snap libtype to be released, as 
        well as IPSPEC. 
        '''
        ret = False

        ret, arc_job_id = submit_release(placeholder_cfg, None, self.milestone, self.thread, 
                            self.label, self.abnr_id, libtype, preview=self.preview, 
                            description=self.description, views=self.views, regmode=self.regmode, prel=self.prel)

        if ret:
            # Log how long it took to get here
            self.logger.info("{0} has been submitted to the gated release system".format(
                        placeholder_cfg.get_full_name()))
            self.logger.info("Go here: {0} to view your release".format(
                get_tnr_dashboard_url_for_id(self.abnr_id, self.project, os.getenv('USER'), self.variant, self.libtype)))
            self.logger.info('Your release job ID is {}'.format(arc_job_id))
            if self.wait and not self.preview:
                # Register our callback handler with the queue
                # In this case the callback handler will ultimately exit
                handler = ReleaseJobHandler(arc_job_id)
                handler.wait_for_job_completion()
                if handler.rel_config is not None:
                    self.rel_config = handler.rel_config
                    self.logger.info('Release {0} created'.format(
                        format_configuration_name_for_printing(self.project, self.variant,
                                                               self.rel_config,
                                                               libtype=self.libtype))
                    )
                    ret = True
                else:
                    ret = False
                    self.logger.warn('Release of {0}/{1}:{2} was not successful. Check the dashboard for more details'.format(self.project,
                                                                                                                              self.variant,
                                                                                                                              self.libtype))
                    ### report out release errors
                    cmd = 'dmx release report -a {}'.format(arc_job_id)
                    os.system(cmd)

            elif self.wait and self.preview:
                # Set a bogus REL and move on
                ret = True
                self.rel_config = 'REL{0}{1}__YYww123z'.format(self.milestone, self.thread)
                self.logger.info('Release {0} created'.format(
                        format_configuration_name_for_printing(self.project, self.variant,
                                                               self.rel_config,
                                                               libtype=self.libtype))
                    )

        else:
            self.logger.error("Problem dispatching release request to the queue.")

        return ret

    def process_config(self):
        ret = 1

        src_variant_config =  self.source_cfg
        src_config = src_variant_config.search(project=self.project,
                                               variant='^{}$'.format(self.variant),
                                               libtype='^{}$'.format(self.libtype))[0]
        
        # Is the config pointing at #dev
        if src_config.is_active_dev():
            delobj = self.family.get_ip(src_config.variant, src_config.project).get_deliverable(src_config.libtype, roadmap=self.roadmap)
            dm = delobj.dm
            if dm == 'designsync':   
                dm_meta = delobj.dm_meta
                # Before releasing library, we need to add filelist to the libtype so that it gets released together
                dssc = dmx.abnrlib.dssc.DesignSync(dm_meta['host'], dm_meta['port'], preview=self.preview)
                dssc.add_filelist_into_icmanage_deliverable(src_config.project, src_config.variant, src_config.libtype, src_config.config, src_config.library, dm_meta)

            #release = self.cli.add_library_release_from_activedev(src_config.project, src_config.variant, src_config.libtype, self.description, library=src_config.library)
            release = self.cli.add_library_release_for_tnr(src_config.project, src_config.variant, src_config.libtype, library=src_config.library, description=self.description)
            icmrelease_obj = ConfigFactory.create_from_icm(src_config.project, src_config.variant, release, src_config.libtype)
        else:
            release = src_config.lib_release
            icmrelease_obj = src_config

        '''
        # Was the input config referencing a library release or did we fail to build a new release
        # when required to do so?
        if (release == src_config.lib_release) or (not release and src_config.is_active_dev()):
            if not self.process_config_with_existing_release(src_variant_config, src_config):
                ret = 1
            else:
                ret = 0
        elif release:
            if not self.process_config_without_existing_release(src_variant_config, src_config, release):
                ret = 1
            else:
                ret = 0
        else:
            # Something went wrong, so shout about it
            self.logger.error("Cannot build a new IC Manage library release or find an existing release that matches")
            ret = 1
        '''
        if icmrelease_obj:
            if not self.process_config_without_existing_release(src_variant_config, icmrelease_obj, src_config):
                ret = 1
            else:
                ret = 0
        else:
            # Something went wrong, so shout about it
            self.logger.error("Cannot build a new IC Manage library release or find an existing release that matches")
            ret = 1

        return ret

    def process_config_without_existing_release(self, src_variant_config, simple_snap_cfg, src_libtype_config):
        '''
        Process a config that was pointing at #ActiveDev and has content for release
        '''
        ret = False

        #simple_snap_cfg = self.build_simple_snap(src_libtype_config, new_release)
        if simple_snap_cfg is not None:
            composite_placeholder_cfg = self.build_composite_placeholder(src_variant_config, src_libtype_config, simple_snap_cfg)
            if composite_placeholder_cfg is not None:
                self.logger.debug("Dispatching to the queue")
                if not self.send_to_queue(composite_placeholder_cfg, simple_snap_cfg.libtype):
                    ret = False
                else:
                    ret = True
            else:
                self.logger.error("Problem building composite placeholder configuration")
                ret = False
        else:
            self.logger.error("Problem building simple snap configuration")
            ret = False

        return ret

    def process_config_with_existing_release(self, src_variant_config, src_libtype_config):
        '''
        Process a config that is either pointing at a named release or has
        no outstanding changes so there must have been a previous release with the
        same content
        '''
        ret = False
        # Find any snaps
        snap_configs = self.cli.get_previous_snaps_with_matching_content(src_libtype_config.project, src_libtype_config.variant,
            src_libtype_config.libtype, library=src_libtype_config.library, release=src_libtype_config.lib_release)

        if snap_configs:
            snap_configs.sort()
            last_snap = snap_configs[-1]
            simple_snap_cfg = ConfigFactory.create_from_icm(src_libtype_config.project, src_libtype_config.variant,
                last_snap, libtype=src_libtype_config.libtype, preview=self.preview)
            composite_placeholder_cfg = self.build_composite_placeholder(src_variant_config, src_libtype_config, simple_snap_cfg)
            if composite_placeholder_cfg is not None:
                if not self.send_to_queue(composite_placeholder_cfg, simple_snap_cfg.libtype):
                    ret = False
                else:
                    ret = True
            else:
                self.logger.error("Problem building composite placeholder config")
                ret = False
        else:
            # We need to build a snap and submit it
            self.logger.info("Content already released but could not find any existing snap- configurations that contain it.")
            release = self.cli.get_last_library_release_number(src_libtype_config.project, src_libtype_config.variant,
                                                               src_libtype_config.libtype,
                                                               library=src_libtype_config.library)
            ret = self.process_config_without_existing_release(src_variant_config, src_libtype_config, release)

        return ret        

    def run(self):
        ret = 1
        ret = self.process_config()
        return ret
