#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/releaselibrary.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: abnr "releaselibrary" subcommand plugin
Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.

DEPRECATED: Repalced by releasedeliverable.py


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

class ReleaseLibraryError(Exception): pass

class ReleaseLibrary(object):
    '''
    Class that runs the releaselibrary command
    '''

    def __init__(self, project, variant, libtype, config, milestone,
                 thread, description, label=None, ipspec=None,
                 wait=False, waiver_files=None,
                 force=False, preview=True):
        self.project = project
        self.variant = variant
        self.libtype = libtype
        self.config = config
        self.milestone = milestone
        self.thread = thread
        self.label = label
        self.description = description
        self.preview = preview
        self.ipspec = ipspec
        self.cli = ICManageCLI(preview=preview)
        self.logger = logging.getLogger(__name__)
        self.wait = wait
        self.waivers = None
        self.rel_config = None
        self.force = force

        # Make sure the project exists
        if not self.cli.project_exists(project):
            raise ReleaseLibraryError("{0} is not a valid project".format(project))
        # Make sure the variant exist
        if not self.cli.variant_exists(project, variant):
            raise ReleaseLibraryError("{0}/{1} is not a valid variant".format(project, variant))
        # Make sure the libtype exist
        if not self.cli.libtype_exists(project, variant, libtype):
            raise ReleaseLibraryError("{0}/{1}:{2} is not a valid libtype".format(project, variant, libtype))

        # If we're not trying to release ipspec we need to ensure
        # the ipspec config exists and is immutable
        if self.libtype != 'ipspec' and not self.ipspec:
            raise ReleaseLibraryError('You must specify an ipspec configuration if you are releasing a non-ipspec library')
        elif self.ipspec:
            if not self.ipspec.startswith(('REL', 'snap-')):
                raise ReleaseLibraryError("{0}/{1}:ipspec@{2} is not an immutable configuration. Please specify either a REL or snap- configuration".format(
                    self.project, self.variant, self.ipspec
                ))
            else:
                self.ipspec_cfg = ConfigFactory.create_from_icm(self.project, self.variant,
                                                               self.ipspec, libtype='ipspec',
                                                               preview=self.preview)

        # Make sure the libtype is defined within the system
        if not self.cli.libtype_defined(self.libtype):
            raise ReleaseLibraryError('Libtype {0} is not defined within the system.'.format(
                self.libtype
            ))

        # Common release input validation
        validate_inputs(project, self.milestone, self.thread, self.label,
                        waiver_files)

        if waiver_files is not None:
            self.waivers = convert_waiver_files(waiver_files)

        # Finally, as all checks must have passed to get here let's set up
        # the Splunk log
        self.abnr_id = get_abnr_id()
        
    def build_composite_snap(self, sub_configs):
        '''
        Builds a composite snap configuration referencing sub_configs
        Returns the snap config if successful
        Returns None if there's an error
        '''
        ret = None

        next_snap_number = self.cli.get_next_snap_number(self.project, self.variant,
                                                         libtype=self.libtype)
        composite_snap_cfg = CompositeConfig('snap-{0}-{1}'.format(next_snap_number, self.libtype),
                                             self.project, self.variant, sub_configs,
                                             description=self.description, preview=self.preview)

        # If we're not ipspec make sure there's an ipspec in there
        if self.libtype != 'ipspec':
            if not composite_snap_cfg.is_config_in_tree(self.ipspec_cfg):
                composite_snap_cfg.add_configuration(self.ipspec_cfg)

        if composite_snap_cfg.save(shallow=False):
            ret = composite_snap_cfg

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

    def send_to_queue(self, snap_cfg, libtype):
        '''
        Dispatches a composite config to the gated release queue.
        The config will include the libtype to be released, as 
        well as IPSPEC. 
        '''
        ret = False

        ret, arc_job_id = submit_release(snap_cfg, self.config, self.milestone, self.thread, 
                            self.label, self.abnr_id, libtype, preview=self.preview, 
                            waivers=self.waivers, description=self.description)

        if ret:
            # Log how long it took to get here
            self.logger.info("{0} has been submitted to the gated release system".format(
                        snap_cfg.get_full_name()))
            self.logger.info("Go here: {0} to view your release".format(
                get_tnr_dashboard_url_for_id(self.abnr_id, self.project)))
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
            elif self.wait and self.preview:
                # Set a bogus REL and move on
                ret = True
                self.rel_config = 'REL{0}{1}_YYww123z'.format(self.milestone, self.thread)
        else:
            self.logger.error("Problem dispatching release request to the queue.")

        return ret

    def get_snap_config_that_matches_rel(self, rel_config):
        '''
        Returns a matching snap config or None if none could be found
        '''
        snaps = self.cli.get_previous_snaps_with_matching_content(rel_config.project, rel_config.variant,
            rel_config.libtype, library=rel_config.library)
        # Any snap is fine
        if snaps:
            simple_snap_cfg = ConfigFactory.create_from_icm(rel_config.project, rel_config.variant,
                snaps[-1], libtype=rel_config.libtype, preview=self.preview)
            composite_snap_cfg = self.build_composite_snap([simple_snap_cfg])
            if composite_snap_cfg is not None:
                if not self.send_to_queue(composite_snap_cfg, rel_config.libtype):
                    ret = 1
                else:
                    ret = 0
            else:
                self.logger.error("Problem building composite snap config")
                ret = 1
        else:
            self.logger.error("Couldn't find matching snap- configs")
            ret =1

        return ret

    def has_already_been_released(self, src_config):
        '''
        Checks if this content has already been released. This covers a few angles:
        Does the library appear in a simple REL configuration with the same milestone/thread
        If so, does it appear in a composite REL configuration with the same ipspec, again for
        the same milestone and thread
        '''
        already_released = False
        matching_simple_rels = []

        if not self.force:
            rel_configs = self.cli.get_previous_rels_with_matching_content(src_config.project, src_config.variant,
                src_config.libtype, library=src_config.library)

            for rel_config in rel_configs:
                if is_rel_config_against_this_thread_and_milestone(rel_config, self.thread, self.milestone):
                    matching_simple_rels.append(rel_config)
                    self.logger.info("{0} matches the content you're trying to release for this milestone/thread".format(
                        format_configuration_name_for_printing(
                            src_config.project, src_config.variant, rel_config,
                            libtype=src_config.libtype
                    )))

            if matching_simple_rels:
                # We only check at the variant level if we're releasing something other than ipspec
                # If self.ipspec is set then we're releasing something else
                if self.ipspec:
                    already_released = self.has_been_released_with_ipspec(src_config, matching_simple_rels)
                else:
                    already_released = True
                    self.rel_config = matching_simple_rels[0]


        return already_released

    def has_been_released_with_ipspec(self, src_config, simple_rels):
        '''
        Checks if this library has already been released against the specified ipspec
        '''
        already_released = False

        composite_rels = self.cli.get_rel_configs(src_config.project, src_config.variant)
        for composite_rel in composite_rels:
            if is_rel_config_against_this_thread_and_milestone(composite_rel, self.thread, self.milestone):
                rel_cfg_obj = ConfigFactory.create_from_icm(src_config.project, src_config.variant,
                                                            composite_rel)
                # There can be only one ipspec at this level
                rel_ipspec = rel_cfg_obj.search(variant=src_config.variant, libtype='ipspec')[0]
                # Are the ipspec and library REL we're looking for in this composite config
                if self.ipspec == rel_ipspec.config:
                    libs_were_trying_to_rel = rel_cfg_obj.search(variant=src_config.variant,
                                                                 libtype=src_config.libtype)
                    for lib in libs_were_trying_to_rel:
                        if lib.config in simple_rels:
                            already_released = True
                            self.rel_config = lib.config
                            self.logger.info('Found variant REL with matching library and ipspec: {0}'.format(
                                format_configuration_name_for_printing(src_config.project,
                                                                       src_config.variant,
                                                                       composite_rel)
                            ))
                            break

        return already_released



    def process_mutable_config(self):
        '''
        Process the releaselibrary request if the input is a mutable config
        '''
        ret = 1

        src_config = ConfigFactory.create_from_icm(self.project, self.variant,
                                                   self.config, libtype=self.libtype,
                                                   preview=self.preview)
        
        # Is the config pointing at #dev
        if src_config.is_active_dev():
            release = self.cli.add_library_release_from_activedev(src_config.project, src_config.variant,
                src_config.libtype, self.description, library=src_config.library)
        else:
            release = src_config.lib_release

        # Was the input config referencing a library release or did we fail to build a new release
        # when required to do so?
        if (release == src_config.lib_release) or (not release and src_config.is_active_dev()):
            if not self.process_mutable_config_with_existing_release(src_config):
                ret = 1
            else:
                ret = 0
        elif release:
            if not self.process_mutable_config_without_existing_release(src_config, release):
                ret = 1
            else:
                ret = 0
        else:
            # Something went wrong, so shout about it
            self.logger.error("Cannot build a new IC Manage library release or find an existing release that matches")
            ret = 1

        return ret

    def process_mutable_config_without_existing_release(self, src_config, new_release):
        '''
        Process a mutable config that was pointing at #ActiveDev and has content for release
        '''
        ret = False

        simple_snap_cfg = self.build_simple_snap(src_config, new_release)
        if simple_snap_cfg is not None:
            composite_snap_cfg = self.build_composite_snap([simple_snap_cfg])
            if composite_snap_cfg is not None:
                self.logger.debug("Dispatching to the queue")
                if not self.send_to_queue(composite_snap_cfg, simple_snap_cfg.libtype):
                    ret = False
                else:
                    ret = True
            else:
                self.logger.error("Problem building composite snap configuration")
                ret = False
        else:
            self.logger.error("Problem building simple snap configuration")
            ret = False

        return ret

    def process_mutable_config_with_existing_release(self, src_config):
        '''
        Process a mutable config that is either pointing at a named release or has
        no outstanding changes so there must have been a previous release with the
        same content
        '''
        ret = False
        already_released = False

        already_released = self.has_already_been_released(src_config)

        if not already_released:
            # Find any snaps
            snap_configs = self.cli.get_previous_snaps_with_matching_content(src_config.project, src_config.variant,
                src_config.libtype, library=src_config.library)
            if snap_configs:
                snap_configs.sort()
                last_snap = snap_configs[-1]
                simple_snap_cfg = ConfigFactory.create_from_icm(src_config.project, src_config.variant,
                    last_snap, libtype=src_config.libtype, preview=self.preview)
                composite_snap_cfg = self.build_composite_snap([simple_snap_cfg])
                if composite_snap_cfg is not None:
                    if not self.send_to_queue(composite_snap_cfg, simple_snap_cfg.libtype):
                        ret = False
                    else:
                        ret = True
                else:
                    self.logger.error("Problem building composite snap config")
                    ret = False
            else:
                # We need to build a snap and submit it
                self.logger.info("Content already released but could not find any existing snap- configurations that contain it.")
                release = self.cli.get_last_library_release_number(src_config.project, src_config.variant,
                                                                   src_config.libtype,
                                                                   library=src_config.library)
                ret = self.process_mutable_config_without_existing_release(src_config, release)
        else:
            ret = True

        return ret

    def process_immutable_config(self):
        '''
        Process the releaselibrary request if the input is an immutable config
        '''
        ret = 1

        name_of_snap_to_release = None

        if self.config.startswith('REL') and is_rel_config_against_this_thread_and_milestone(
            self.config, self.thread, self.milestone
        ):
            self.logger.info('{0} was already released for this milestone/thread'.format(
                format_configuration_name_for_printing(self.project, self.variant,
                                                       self.config,
                                                       libtype=self.libtype)
            ))
            ret = 0
        else:
            src_config = ConfigFactory.create_from_icm(self.project, self.variant, self.config,
                                                       libtype=self.libtype,
                                                       preview=self.preview)

            # Is this content in a REL for this milestone/thread/ipspec combination
            if self.has_already_been_released(src_config):
                ret = 0
            else:
                if self.config.startswith('REL'):
                    rel_config = ConfigFactory.create_from_icm(self.project, self.variant,
                                                               self.config, libtype=self.libtype,
                                                               preview=self.preview)

                    name_of_snap_to_release = self.get_snap_config_that_matches_rel(rel_config)
                elif self.config.startswith('snap-'):
                    name_of_snap_to_release = self.config

                if name_of_snap_to_release is not None:
                    simple_snap_cfg = ConfigFactory.create_from_icm(self.project, self.variant,
                                                                    name_of_snap_to_release,
                                                                    libtype=self.libtype,
                                                                    preview=self.preview)
                    composite_snap_cfg = self.build_composite_snap([simple_snap_cfg])
                    if composite_snap_cfg is not None:
                        if not self.send_to_queue(composite_snap_cfg, simple_snap_cfg.libtype):
                            ret = 1
                        else:
                            ret = 0
                    else:
                        self.logger.error("Problem building composite snap config")
                        ret = 1

        return ret

    def run(self):
        '''
        Runs the release flow - entry point for the class
        '''
        ret = 1

        if self.config.startswith(('REL', 'snap-')):
            ret = self.process_immutable_config()
        else:
            ret = self.process_mutable_config()

        return ret
