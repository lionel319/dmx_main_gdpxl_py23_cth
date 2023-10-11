#!/usr/bin/env python
## @addtogroup ecolib
## @{

''' axc
This is documentation

@author Lionel Tan, Kevin Lim
@image html dmx.ecolib.png 

-the end-
'''

from builtins import str
import os, sys
import json
from dmx.utillib.decorators import memoized
import logging
from dmx.utillib.utils import get_tools_path, is_pice_env

FAMILY = "family.json"
CHECKERS = "checkers.json"
DELIVERABLES_BY_IP_TYPE = "deliverables_by_ip_type.json"
MANIFEST = "manifest.json"
ROADMAPS = "roadmaps.json"
VIEWS = "views.json"
PRELS = "prels.json"
SLICES = "slices.json"
ROADMAP_AND_REVISION_BY_PRODUCT = "roadmap_and_revisions_by_product.json"
CTH_FILELIST_MAPPING = "cthfe_filelist_mapping.json" 
# http://pg-rdconfluence:8090/pages/viewpage.action?pageId=4523652
# No longer needed
'''
DELIVERABLES_AND_CHECKERS_BY_MILESTONE = "deliverables_and_checkers_by_milestone.json"
ROADMAP = "roadmap.json"
'''

LOGGER = logging.getLogger(__name__)

class LoaderError(Exception): pass

def get_dmxdata_path():
    return os.getenv("DMXDATA_ROOT")

## Loads roadmaps info from json into dictionary
##
## @param family Family
## @exception dmx::ecolib::loader::LoaderError Raise if json file cannot be found
## @return dictionary of roadmap info
@memoized
def load_roadmaps(family):
    family = family.lower().title()
    filename = "{}/{}/{}".format(get_dmxdata_path(), family, ROADMAPS)
    LOGGER.debug('Loading roadmaps {}'.format(filename))
    if not os.path.exists(filename):
        raise LoaderError("Roadmaps does not exist for {}".format(family))

    try:
        with open(filename, 'r') as t:
            raw_roadmaps_dict = json.load(t)
    except Exception as e:
        LOGGER.error(str(e))
        raise LoaderError("Fail loading roadmaps file: {}".format(filename))

    ### http://pg-rdjira:8080/browse/DI-1137
    roadmaps_dict = _expand_reuse_data(raw_roadmaps_dict)


    ### Auto generate milestone 99
    ### http://pg-rdjira:8080/browse/DI-698
    for roadmap in roadmaps_dict:
        all_deliverables = []
        for milestone in roadmaps_dict[roadmap]:
            all_deliverables += roadmaps_dict[roadmap][milestone]
        roadmaps_dict[roadmap]['99'] = list(set(all_deliverables))
    return roadmaps_dict
   


def _expand_reuse_data(data):
    '''
    Input:
    {
        "FM8": {
            "1.0": ['a'],
            "2.0": ['a', 'b'],
        },
        "FM4": {
            "1.0": ['FM8:1.0'],
            "2.0": ['FM8:1.0']
        }
    }

    Return:
    {
        "FM8": {
            "1.0": ['a'],
            "2.0": ['a', 'b'],
        },
        "FM4": {
            "1.0": ['a'],
            "2.0": ['a'],
        }
    }

    http://pg-rdjira:8080/browse/DI-1137
    '''
    has_change = False  # to support nested referencing

    for roadmap in data:
        for milestone in data[roadmap]:
            libtypes = data[roadmap][milestone]
            if ':' in libtypes[0]:
                has_change = True
                ref_roadmap, ref_milestone = libtypes[0].split(':')
                LOGGER.debug('{}:{} ==> {}:{}'.format(roadmap, milestone, ref_roadmap, ref_milestone))
                try:
                    data[roadmap][milestone] = data[ref_roadmap][ref_milestone]
                except:
                    LOGGER.error("ERROR: Referenced reuse roadmap({}:{}) in {}:{} not found.".format(ref_roadmap, ref_milestone, roadmap, milestone))
                    raise

    if has_change:
        return _expand_reuse_data(data)

    return data


## Loads manifest info from json into dictionary
##
## @param family Family
## @exception dmx::ecolib::loader::LoaderError Raise if json file cannot be found
## @return dictionary of manifest info      
@memoized
def load_manifest(family):
    family = family.lower().title()
    manifest = "{}/{}/{}".format(get_dmxdata_path(), family, MANIFEST)
    LOGGER.debug('Loading manifest {}'.format(manifest))
    if not os.path.exists(manifest):
        raise LoaderError("Manifest does not exist for {}".format(family))

    try:
        with open(manifest, 'r') as t:
            manifest_dict = json.load(t)
    except Exception as e:
        LOGGER.error(str(e))
        raise LoaderError("Fail loading manifest file: {}".format(manifest))
    return manifest_dict        
  
## Loads family info from json into dictionary
##
## @exception dmx::ecolib::loader::LoaderError Raise if json file cannot be found
## @return dictionary of family info
@memoized      
def load_family():
    
    ### https://jira01.devtools.intel.com/browse/PSGDMX-1521
    env = os.getenv("DMX_FAMILY_LOADER", '')
    if not env:
        family = "{}/{}".format(get_dmxdata_path(), FAMILY)
    else:
        family = "{}/{}".format(get_dmxdata_path(), env)
    
    
    LOGGER.debug('Loading family {}'.format(family))
    if not os.path.exists(family):
        raise LoaderError("Family {} does not exist".format(family))

    try:
        with open(family, 'r') as t:
            family_dict = json.load(t)
    except Exception as e:
        LOGGER.error(str(e))
        raise LoaderError("Fail loading family file: {}".format(family))


    return family_dict


## Loads checkers info from json into dictionary
##
## @param family Family
## @exception dmx::ecolib::loader::LoaderError Raise if json file cannot be found
## @return dictionary of checkers info    
@memoized
def load_checkers(family):
    family = family.lower().title()
    checkers = "{}/{}/{}".format(get_dmxdata_path(), family, CHECKERS)
    LOGGER.debug('Loading checkers {}'.format(checkers))
    if not os.path.exists(checkers):
        raise LoaderError("Checkers does not exist for {}".format(family))

    try:
        with open(checkers, 'r') as t:
            checkers_dict = json.load(t)
    except Exception as e:
        LOGGER.error(str(e))
        raise LoaderError("Fail loading checkers file: {}".format(checkers))

    ### Add '99' into every list of milestone
    ### http://pg-rdjira:8080/browse/DI-739
    for checker in checkers_dict:
        for roadmap in checkers_dict[checker]['Milestones']:
            if '99' not in checkers_dict[checker]['Milestones'][roadmap]:
                checkers_dict[checker]['Milestones'][roadmap].append('99')
        
    return checkers_dict

## Loads milestone info from json into dictionary
##
## @param family Family
## @exception dmx::ecolib::loader::LoaderError Raise if json file cannot be found
## @return dictionary of milestone info
@memoized
def load_deliverables_by_ip_type(family):
    family = family.lower().title()
    deliverables_by_ip_type = "{}/{}/{}".format(get_dmxdata_path(), family, DELIVERABLES_BY_IP_TYPE)
    LOGGER.debug('Loading deliverables_by_ip_type {}'.format(deliverables_by_ip_type))
    if not os.path.exists(deliverables_by_ip_type):
        raise LoaderError("Deliverables_by_ip_type does not exist for {}".format(family))

    try:
        with open(deliverables_by_ip_type, 'r') as t:
            deliverables_by_ip_type_dict = json.load(t)
    except Exception as e:
        LOGGER.error(str(e))
        raise LoaderError("Fail loading deliverables_by_ip_type file: {}".format(deliverables_by_ip_type))
    return deliverables_by_ip_type_dict    

## Loads views info from json into dictionary
##
## @param family Family
## @exception dmx::ecolib::loader::LoaderError Raise if json file cannot be found
## @return dictionary of product info
@memoized
def load_views(family):
    family = family.lower().title()
    views = "{}/{}/{}".format(get_dmxdata_path(), family, VIEWS)
    LOGGER.debug('Loading views {}'.format(views))
    if not os.path.exists(views):
        raise LoaderError("views does not exist for {}".format(family))

    try:
        with open(views, 'r') as t:
            views_dict = json.load(t)
    except Exception as e:
        LOGGER.error(str(e))
        raise LoaderError("Fail loading view file: {}".format(view))
    return views_dict 

## Loads prels info from json into dictionary
##
## @param family Family
## @exception dmx::ecolib::loader::LoaderError Raise if json file cannot be found
## @return dictionary of product info
@memoized
def load_prels(family):
    family = family.lower().title()
    prels = "{}/{}/{}".format(get_dmxdata_path(), family, PRELS)
    LOGGER.debug('Loading prels {}'.format(prels))
    if not os.path.exists(prels):
        raise LoaderError("prels does not exist for {}".format(family))

    try:
        with open(prels, 'r') as t:
            prels_dict = json.load(t)
    except Exception as e:
        LOGGER.error(str(e))
        raise LoaderError("Fail loading prel file: {}".format(prel))
    return prels_dict 

## Loads checkers info from json into dictionary
##
## @param family Family
## @exception dmx::ecolib::loader::LoaderError Raise if json file cannot be found
## @return dictionary of checkers info    
@memoized
def load_roadmap_and_revisions_by_product(family):
    family = family.lower().title()
    roadmap_and_revisions_by_product = "{}/{}/{}".format(get_dmxdata_path(), family, ROADMAP_AND_REVISION_BY_PRODUCT)
    LOGGER.debug('Loading roadmap_and_revisions_by_product {}'.format(roadmap_and_revisions_by_product))
    if not os.path.exists(roadmap_and_revisions_by_product):
        raise LoaderError("Roadmap_and_revisions_by_product does not exist for {}".format(family))

    try:
        with open(roadmap_and_revisions_by_product, 'r') as t:
            roadmap_and_revisions_by_product_dict = json.load(t)
    except Exception as e:
        LOGGER.error(str(e))
        raise LoaderError("Fail loading roadmap_and_revisions_by_product file: {}".format(roadmap_and_revisions_by_product))
    return roadmap_and_revisions_by_product_dict    

## Loads slices info from json into dictionary
##
## @param family Family
## @exception dmx::ecolib::loader::LoaderError Raise if json file cannot be found
## @return dictionary of checkers info    
@memoized
def load_slices(family):
    family = family.lower().title()
    slices = "{}/{}/{}".format(get_dmxdata_path(), family, SLICES)
    LOGGER.debug('Loading slices {}'.format(slices))
    if not os.path.exists(slices):
        raise LoaderError("Slices does not exist for {}".format(family))

    try:
        with open(slices, 'r') as t:
            slices_dict = json.load(t)
    except Exception as e:
        LOGGER.error(str(e))
        raise LoaderError("Fail loading slices file: {}".format(slices))
    return slices_dict

## Loads cth filelist mapping info from json into dictionary
##
## @param family Family
## @exception dmx::ecolib::loader::LoaderError Raise if json file cannot be found
## @return dictionary of cth filelist mapping info
@memoized
def load_cth_filelist_mapping(family):
    family = family.lower().title()
    cth_filelist_mapping = "{}/{}/{}".format(get_dmxdata_path(), family, CTH_FILELIST_MAPPING)
    LOGGER.debug('Loading CTH_FILELIST_MAPPING {}'.format(cth_filelist_mapping))
    if not os.path.exists(cth_filelist_mapping):
        raise LoaderError("Cth_filelist_mapping does not exist for {}".format(family))

    try:
        with open(cth_filelist_mapping, 'r') as t:
            cth_filelist_mapping_dict = json.load(t)
    except Exception as e:
        LOGGER.error(str(e))
        raise LoaderError("Fail loading cth_filelist_mapping file: {}".format(cth_filelist_mapping))
    return cth_filelist_mapping_dict    


# http://pg-rdconfluence:8090/pages/viewpage.action?pageId=4523652
# No longer needed
'''

## Loads product info from json into dictionary
##
## @param family Family
## @exception dmx::ecolib::loader::LoaderError Raise if json file cannot be found
## @return dictionary of product info
@memoized
def load_deliverables_and_checkers_by_milestone(family):
    deliverables_and_checkers_by_milestone = "{}/{}/{}".format(get_dmxdata_path(), family, DELIVERABLES_AND_CHECKERS_BY_MILESTONE)
    LOGGER.debug('Loading deliverables_and_checkers_by_milestone {}'.format(deliverables_and_checkers_by_milestone))
    if not os.path.exists(deliverables_and_checkers_by_milestone):
        raise LoaderError("Deliverables_and_checkers_by_milestone does not exist for {}".format(family))

    try:
        with open(deliverables_and_checkers_by_milestone, 'r') as t:
            deliverables_and_checkers_by_milestone_dict = json.load(t)
    except Exception as e:
        LOGGER.error(str(e))
        raise LoaderError("Fail loading deliverables_and_checkers_by_milestone file: {}".format(deliverables_and_checkers_by_milestone))
    return deliverables_and_checkers_by_milestone_dict

## Loads roadmap info from json into dictionary
##
## @param family Family
## @exception dmx::ecolib::loader::LoaderError Raise if json file cannot be found
## @return dictionary of roadmap info
@memoized
def load_roadmap(family):
    roadmap = "{}/{}/{}".format(get_dmxdata_path(), family, ROADMAP)
    LOGGER.debug('Loading roadmap {}'.format(roadmap))
    if not os.path.exists(roadmap):
        raise LoaderError("Roadmap does not exist for {}".format(family))

    try:
        with open(roadmap, 'r') as t:
            roadmap_dict = json.load(t)
    except Exception as e:
        LOGGER.error(str(e))
        raise LoaderError("Fail loading roadmap file: {}".format(roadmap))
    return roadmap_dict      
'''

## @}
