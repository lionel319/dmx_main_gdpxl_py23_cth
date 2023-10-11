#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/multireleases.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Library containing functionality common across two or more abnr release commands

Author: Lee Cartwright

Copyright (c) Altera Corporation 2015
All rights reserved.
'''

## @addtogroup dmxlib
## @{

import os

from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.config_factory import ConfigFactory
#from dmx.abnrlib.icmcompositeconfig import CompositeConfig
#from dmx.abnrlib.icmsimpleconfig import SimpleConfig
from dmx.abnrlib.icmconfig import IcmConfig
from dmx.abnrlib.icmlibrary import IcmLibrary
from dmx.abnrlib.flows.releaselibrary import ReleaseLibrary
from dmx.abnrlib.flows.releasevariant import ReleaseVariant
from dmx.abnrlib.flows.releasedeliverable import ReleaseDeliverable
from dmx.utillib.utils import split_pvlc, split_pvc

class ReleaseError(Exception): pass

# http://pg-rdjira.altera.com:8080/browse/DI-560
# Support for hierarchical release with the new release flow
def release_deliverable(project, variant, libtype, config, milestone,
                          thread, label, description, preview, force, views=[], regmode=False):
    '''
    Tries to release the simple configuration.

    :param project: The IC Manage project
    :type project: str
    :param variant: The IC Manage variant
    :type variant: str
    :param libtype: The IC Manage libtype
    :type libtype: str
    :param config: The IC Manage config
    :type config: str
    :param ipspec_config: The ipspec configuration to use with this release. None if libtype == ipspec
    :type ipspec_config: str or None
    :param milestone: The Altera project milestone
    :type milestone: str
    :param thread: The Altera project thread
    :type thread: str
    :param label: The release label.
    :type label: str
    :param description: The release description
    :type description: str
    :param preview: Boolean indicating whether or not we're in preview mode
    :type preview: bool
    :param waiver_files: List of waiver files to use with the release
    :type waiver_files: list
    :param releasetree_id: The abnr_id of the calling releasetree instance
    :type releasetree_id: str
    :param force: Boolean indicating whether or not to force a release
    :type force: bool
    :return: Dictionary containing success status and details of released configuration
    :rtype: dict
    :raises: ReleaseError, ReleaseLibError
    '''
    ret = {
        'project' : project,
        'variant' : variant,
        'libtype' : libtype,
        'original_config' : config,
        'success' : False,
    }

    releasedel = ReleaseDeliverable(project, variant, libtype, config, milestone, thread,
                            description, label=label,
                            wait=True,
                            force=force, preview=preview,
                            from_releaseview=True,
                            views=views, regmode=regmode)

    results = releasedel.run()
    if results == 0 and releasedel.rel_config is not None:        
        ret['released_config'] = releasedel.rel_config
        ret['success'] = True
    else:
        raise ReleaseError('Problem releasing {0}/{1}:{2} from {0}/{1}@{3}'.format(
            project, variant, libtype, config
        ))

    return ret

def release_simple_config(project, variant, libtype, config, ipspec_config, milestone,
                          thread, label, description, preview, waiver_files,
                          force):
    '''
    Tries to release the simple configuration.

    :param project: The IC Manage project
    :type project: str
    :param variant: The IC Manage variant
    :type variant: str
    :param libtype: The IC Manage libtype
    :type libtype: str
    :param config: The IC Manage config
    :type config: str
    :param ipspec_config: The ipspec configuration to use with this release. None if libtype == ipspec
    :type ipspec_config: str or None
    :param milestone: The Altera project milestone
    :type milestone: str
    :param thread: The Altera project thread
    :type thread: str
    :param label: The release label.
    :type label: str
    :param description: The release description
    :type description: str
    :param preview: Boolean indicating whether or not we're in preview mode
    :type preview: bool
    :param waiver_files: List of waiver files to use with the release
    :type waiver_files: list
    :param releasetree_id: The abnr_id of the calling releasetree instance
    :type releasetree_id: str
    :param force: Boolean indicating whether or not to force a release
    :type force: bool
    :return: Dictionary containing success status and details of released configuration
    :rtype: dict
    :raises: ReleaseError, ReleaseLibError
    '''
    ret = {
        'project' : project,
        'variant' : variant,
        'libtype' : libtype,
        'original_config' : config,
        'success' : False,
    }

    releaselib = ReleaseLibrary(project, variant, libtype, config, milestone, thread,
                            description, label=label, ipspec=ipspec_config,
                            wait=True,
                            waiver_files=waiver_files,
                            force=force, preview=preview)

    results = releaselib.run()
    if results == 0 and releaselib.rel_config is not None:        
        ret['released_config'] = releaselib.rel_config
        ret['success'] = True
    else:
        raise ReleaseError('Problem releasing {0}/{1}:{2}@{3}'.format(
            project, variant, libtype, config
        ))

    return ret

def release_composite_config(project, variant, sub_configs, milestone, thread, label,
                             description, preview, waiver_files,
                             force, views=[], syncpoint='', skipsyncpoint='', 
                             skipmscheck='', prel=None, regmode=False):
        '''
        Releases a composite configuration.

        :param project: The IC Manage project
        :type project: str
        :param variant: The IC Manage variant
        :type variant: str
        :param sub_configs: List of configuration names to include in the release. Names are in Altera format (project/variant[:libtype]@config)
        :type sub_configs: list
        :param milestone: The Altera project milestone we're releasing against
        :type milestone: str
        :param thread: The Altera project thread we're releasing against
        :type thread: str
        :param label: The release label
        :type label: str
        :param description: The release description.
        :type description: str
        :param preview: Boolean indicating whether or not we're running in preview mode
        :type preview: bool
        :param waiver_files: List of waiver files to process with the release
        :type waiver_files: list
        :param releasetree_id: The abnr_id of the calling releasetree instance
        :type releasetree_id: str
        :param force: Boolean indicating whether or not to force a release
        :type force: bool
        :returns: Dictionary describing the release status and name
        :rtype: dict
        :raises: ReleaseError, ReleaseVariantError
        '''
        ret = {
            'project' : project,
            'variant' : variant,
            'success' : False
        }

        snap_config = build_composite_snap(project, variant, sub_configs, preview)

        releasevariant = ReleaseVariant(project, variant, snap_config.config, milestone,
                                       thread, description, label=label,
                                       wait=True,
                                       waiver_files=waiver_files,
                                       force=force, preview=preview,
                                       from_releasetree=True,
                                       views=views, syncpoint=syncpoint,
                                       skipsyncpoint=skipsyncpoint,
                                       skipmscheck=skipmscheck, prel=prel, regmode=regmode)

        results = releasevariant.run()
        if results == 0 and releasevariant.rel_config is not None:        
            ret['released_config'] = releasevariant.rel_config
            ret['success'] = True
        else:
            raise ReleaseError('Problem releasing {0}/{1}@{2}'.format(
                project, variant, snap_config.config
            ))

        return ret

def build_composite_snap(project, variant, sub_configs, preview):
    '''
    Builds a snap composite config in project/variant
    containing the specified sub configs.

    :param project: The IC Manage project
    :type project: str
    :param variant: The IC Manage variant
    :type variant: str
    :param sub_configs: List of configuration names in Altera format (project/variant[:libtype]@config)
    :type sub_configs: list
    :param preview: Boolean indicating whether or not we're running in preview mode
    :type preview: bool
    :return: The new IC Manage composite config object
    :raises: ReleaseError, CompositeConfigError
    '''
    # We're only using this object to read so always set preview to True
    cli = ICManageCLI(preview=preview)

    # Convert the sub_config strings into IC Manage configuration objects
    sub_config_objects = []
    for sub_config in sub_configs:
        if not preview:
            sub_config_objects.append(ConfigFactory.create_config_from_full_name(sub_config, preview=preview))
        else:
            # For preview mode, we simply create fake configs to pass to snap
            if ':' in sub_config:
                simple_project, simple_variant, simple_libtype, simple_config = split_pvlc(sub_config)
                sub_config_objects.append(SimpleConfig(simple_config, simple_project, simple_variant, simple_libtype, 'dev', '1', preview=preview, use_db=False))
            else:
                comp_project, comp_variant, comp_config = split_pvc(sub_config)
                sub_config_objects.append(CompositeConfig(comp_config, comp_project, comp_variant, [], preview=preview))

    # Get the next snap number for this variant as we need to create a new configuration
    # that contains all the newly created REL sub-configs
    snap_number = cli.get_next_snap_number(project, variant)

    # Create and try to release a copy of root but with all sub configurations released
    #composite_cfg = CompositeConfig('snap-{}'.format(snap_number), project, variant, sub_config_objects, preview=preview)
    composite_cfg = IcmConfig('snap-{}'.format(snap_number), project, variant, sub_config_objects, preview=preview)

    if not preview:
        if not composite_cfg.save():
            raise ReleaseError('Problem saving composite configuration {0}'.format(composite_cfg.get_full_name()))

    return composite_cfg

## @}
