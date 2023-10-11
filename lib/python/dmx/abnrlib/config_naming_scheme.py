#!/usr/bin/env python
#$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/config_naming_scheme.py#1 $
#$Change: 7411538 $
#$DateTime: 2022/12/13 18:19:49 $
#$Author: lionelta $
'''
| Description: API Class for Altera IC-Manage-Configuration naming convention.
| 
| Tickets:

* http://pg-rdjira:8080/browse/DI-130
* http://fogbugz.altera.com/default.asp?354628#BugEvent.3066947

'''

## @addtogroup dmxlib
## @{

import logging
import re


class ConfigNamingScheme(object):
    '''
    Altera ICManage Configuration Naming Convention Factory Class.
    '''
    LOGGER = logging.getLogger(__name__)
    regex = {}
    regex['milestone'] = '(?P<milestone>\d\.\d)'
    #regex['thread'] = '(?P<thread>[A-Z][A-Z]\d)'
    #regex['rev'] = 'rev(?P<rev>[A-Z]\d?(P[1-9])?)'
    regex['thread'] = '(?P<thread>[A-Z]+\d*)'
    regex['rev'] = 'rev(?P<rev>[A-Z]\d*(P[0-9]+)?)'
    regex['string'] = '[a-zA-Z]([_-]?[a-zA-Z0-9])*'
    regex['label'] = "(?P<label>{})".format(regex['string'])
    regex['timestamp'] = '(?P<year>\d\d)ww(?P<ww>\d\d)(?P<day>\d)(?P<index>[a-z])'
    regex['branch_id'] = "(?P<branch_id>{})".format(regex['string'])

    ### Regular Expression for the 3 categories(RELEASE/BRANCH/SNAP)
    SCHEME = ['RELEASE', 'BRANCH', 'SNAP', 'WIP']
    regex['RELEASE'] = '^REL{}{}{}(--{})?__{}$'.format(regex['milestone'], regex['thread'], regex['rev'], regex['label'], regex['timestamp'])
    #regex['norm_ic'] = '(?P<norm_ic>REL{}{}{}(-{})?-{})'.format(   regex['milestone'], regex['thread'], regex['rev'], regex['label'], regex['timestamp_rel'])
    regex['norm_ic'] = '(?P<norm_ic>.*(?!(__|--| )).*)'
    regex['BRANCH'] = '^b{}__{}__dev$'.format(regex['norm_ic'], regex['branch_id'])
    regex['SNAP'] = '^snap-{}__{}$'.format(regex['norm_ic'], regex['timestamp'])
    regex['wipname'] = '(?P<wipname>{})'.format(regex['string'])
    regex['WIP'] = '^{}__{}$'.format(regex['wipname'], regex['timestamp'])


    @classmethod
    def get_data_for_release_config(cls, configname):
        '''
        Extract the given ``configname`` and return the data in a ``dict``. Example-

        ::

            configname = "REL4.5ND5revA--SECTOR-f1_and-f2__16ww072a"
            return = {
                'index': 'a', 
                'thread': 'ND5', 
                'year': '16', 
                'rev': 'A', 
                'label': 'SECTOR-f1_and-f2', 
                'ww': '07', 
                'milestone': '4.5', 
                'type': 'RELEASE', 
                'day': '2'}

        return ``{}`` if it does not match.

        '''
        return cls.get_data_for_config_base_function('RELEASE', configname)


    @classmethod
    def get_data_for_branch_config(cls, configname):
        '''
        Extract the given ``configname`` and return the data in a ``dict``. Example-

        ::
            configname = 'bREL4.5ND5revA-SECTOR-f1-and-f2-16ww072a__this-is-branch-id__dev'
            return = {
                'type': 'BRANCH',
                'norm_ic': 'REL4.5ND5revA-SECTOR-f1-and-f2-16ww072a',
                'branch_id': 'this-is-branch-id', }

        return ``{}`` if it does not match.

        '''
        return cls.get_data_for_config_base_function('BRANCH', configname)


    @classmethod
    def get_data_for_snap_config(cls, configname):
        '''
        Extract the given ``configname`` and return the data in a ``dict``. Example-

        ::
            configname = 'snap-REL4.5ND5revA-SECTOR-f1-and-f2-16ww072a__17ww234c'
            return = {
                'day': '4',
                'index': 'c',
                'norm_ic': 'REL4.5ND5revA-SECTOR-f1-and-f2-16ww072a',
                'type': 'SNAP',
                'ww': '23',
                'year': '17'}

        return ``{}`` if it does not match.

        '''
        return cls.get_data_for_config_base_function('SNAP', configname)


    @classmethod
    def get_data_for_wip_config(cls, configname):
        '''
        Extract the given ``configname`` and return the data in a ``dict``. Example-

        ::
            configname = 'some-normal-texts__17ww234c'
            return = {
                'wipname': 'some-normal-texts',
                'index': 'c',
                'type': 'WIP',
                'ww': '23',
                'day': '4',
                'year': '17'}

        return ``{}`` if it does not match.

        '''
        return cls.get_data_for_config_base_function('WIP', configname)


    @classmethod
    def get_data_for_config(cls, configname):
        '''
        | This is a factory function of this class.
        | This function tries to match the given ``configname`` to any of the possible defined naming scheme.
        | It returns the respective ``dict`` returned from the ``get_data_for_<type>_config`` if it matches.
        | Else, return ``{}``

        '''
        for sch in cls.SCHEME:
            ret = cls.get_data_for_config_base_function(sch, configname)
            if ret:
                return ret
        return {}


    @classmethod
    def get_data_for_config_base_function(cls, category, configname):
        '''
        '''
        match = re.search(cls.regex[category], configname)
        if match == None:
            cls.LOGGER.debug('{}:{}'.format(configname, {}))
            return {}
        else:
            ret = match.groupdict()
            ret['type'] = category
            cls.LOGGER.debug('{}:{}'.format(configname, ret))
            return ret


    @classmethod
    def normalize_config(cls, configname):
        '''
        Normalize the config name by replacing ``--`` and ``__`` with a single ``-``.
        '''
        return re.sub("__", '-', re.sub("--", '-', configname))



## @}
