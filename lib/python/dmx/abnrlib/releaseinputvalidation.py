#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/releaseinputvalidation.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Library containing functionality to validate standard release command inputs,
such as milestone, thread, label, etc.

Author: Lee Cartwright

Copyright (c) Altera Corporation 2015
All rights reserved.
'''

## @addtogroup abnrlib
## @{

import os

import dmx.ecolib.ecosphere
from dmx.abnrlib.namevalidator import AlteraName

class RoadmapValidationError(Exception): pass
class LabelValidationError(Exception): pass
class WaiverFileValidationError(Exception): pass

def validate_inputs(project, milestone, thread, label, waiver_files):
    '''
    Function used to validate the common, release specific, inputs to abnr release commands.

    :param project: The IC Manage project name
    :type project: str
    :param milestone: The Altera milestone
    :type milestone: str
    :param thread: The Altera thread
    :type thread: str
    :param label: The release label
    :type label: str
    :param waiver_files: List of waiver file paths
    :type waiver_files: list
    :raises: RoadmapValidationError, LabelValidationError, WaiverFileValidationError
    '''
    validate_roadmap(project, milestone, thread)
    validate_label(label)
    validate_waiver_files(waiver_files)

def validate_roadmap(project, milestone, thread):
    '''
    Validates the project, milestone and thread against the roadmap.

    :param project: The IC Manage project name
    :type project: str
    :param milestone: The Altera milestone
    :type milestone: str
    :param thread: The Altera thread
    :type thread: str
    :raises: RoadmapValidationError
    '''
    family = dmx.ecolib.ecosphere.EcoSphere().get_family_for_thread(thread)
    if not family.verify_roadmap(milestone, thread):
        raise RoadmapValidationError('Thread {0} and milestone {1} are not valid for project {2}'.format(
                                     thread, milestone, project
        ))

def validate_label(label):
    '''
    Validates the release label

    :param label: The release label
    :type label: str
    :raises: LabelValidationError
    '''
    if label and not AlteraName.is_label_valid(label):
        raise LabelValidationError('{0} is not a valid release label'.format(label))

def validate_waiver_files(waiver_files):
    '''
    Validates the waiver files.

    :param waiver_files: List of waiver file paths
    :type waiver_files: list
    :raises: WaiverFileValidationError
    '''
    if waiver_files is not None:
        for waiver_file in waiver_files:
            if not os.path.exists(waiver_file):
                raise WaiverFileValidationError('Waiver file {0} does not exist'.format(waiver_file))

## @}
