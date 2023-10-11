#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/namevalidator.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Container for all Altera/IC Manage object validation classes

Author: Lee Cartwright
Copyright (c) Altera Corporation 2015
All rights reserved.
'''

## @addtogroup dmxlib
## @{

import logging
import re

class Validator(object):
    '''
    Building block validation methods to be used when validatiing
    Altera/IC Manage object names
    '''

    @classmethod
    def contains_whitespace(cls, name):
        '''
        Checks if name contains any whitespace characters

        :param name: The name being checked
        :type name: str
        :return: Boolean indicating whether or not whitespace was found in name
        :rtype: bool
        '''
        ret = False

        if re.search(r'\s', name):
            ret = True

        return ret

    @classmethod
    def contains_special_character_except_underscore(cls, name):
        '''
        Checks if name contains any special characters except underscore such as '!@#$%^&*()+='

        :param name: The name being checked
        :type name: str
        :return: Boolean indicating whether or not special character was found in name
        :rtype: bool
        '''
        ret = False

        if re.search(r'[^\w_]', name):
            ret = True

        return ret

    @classmethod
    def contains_capital_letter(cls, name):
        '''
        Checks if name contains any capital letters

        :param name: The name being checked
        :type name: str
        :return: Boolean indicating whether or not capital letter was found in name
        :rtype: bool
        '''
        ret = False

        if re.search(r'[A-Z]', name):
            ret = True

        return ret
        
    @classmethod
    def starts_without_alphabet(cls, name):
        '''
        Checks if name starts without an alphabet

        :param name: The name being checked
        :type name: str
        :return: Boolean indicating whether or not name starts without an alphabet
        :rtype: bool
        '''
        ret = False

        if re.search(r'^[^a-z]', name):
            ret = True

        return ret

    @classmethod
    def ends_without_alphabet_or_number(cls, name):
        '''
        Checks if name ends without an alphabet or number

        :param name: The name being checked
        :type name: str
        :return: Boolean indicating whether or not ends without an alphabet or number
        :rtype: bool
        '''
        ret = False

        if re.search(r'[^a-z0-9]$', name):
            ret = True

        return ret
   
    @classmethod
    def is_integer(cls, name):
        '''
        Checks if name is a valid integer value

        :param name: The name to check
        :type name: str or int
        :return: Boolean indicating whether or not name is a valid integer
        :rtype: bool
        '''
        ret = False

        try:
            # This looks weird but we can't guarantee we've been given a string
            # If, for example, we were given a literal float then something like
            # int(9.99) would return True, which is not what we want.
            # So, cast everything into a string before passing it to int
            int('{}'.format(name))
            ret = True
        except ValueError:
            ret = False

        return ret

class ICMName(object):
    '''
    Contains validation methods for IC Manage object names
    '''
    _logger = logging.getLogger(__name__)

    @classmethod
    def is_project_name_valid(cls, project_name):
        '''
        Validates the project name

        :param project_name: The project name being validated
        :type project_name: str
        :return: Boolean indicating whether or not the project name is valid
        :rtype: bool
        '''
        ret = False

        if Validator.contains_whitespace(project_name):
            cls._logger.error('Project name {0} contains whitespace character(s)'.format(
                project_name
            ))
            ret = False
        else:
            ret = True

        return ret

    @classmethod
    def is_variant_name_valid(cls, variant_name):
        '''
        Validates the variant name

        :param variant_name: The variant name being validated
        :type variant_name: str
        :return: Boolean indicating whether or not the variant name is valid
        :rtype: bool
        '''
        ret = True

        if Validator.contains_special_character_except_underscore(variant_name):
            cls._logger.error('Variant name {0} contains invalid character(s)'.format(variant_name))
            cls._logger.error('Variant name can only contain alphabet, number or underscore.')
            ret = False            

        if Validator.starts_without_alphabet(variant_name):
            cls._logger.error('Variant name {0} starts with invalid character(s)'.format(variant_name))
            cls._logger.error('Variant name can only start with alphabet.')
            ret = False   
            
        if Validator.ends_without_alphabet_or_number(variant_name):
            cls._logger.error('Variant name {0} ends with invalid character(s)'.format(variant_name))
            cls._logger.error('Variant name can only end with alphabet or number.')
            ret = False    
            
        if Validator.contains_capital_letter(variant_name):
            cls._logger.error('Variant name {0} contains capital character(s)'.format(variant_name))
            cls._logger.error('Variant name can only contain small character.')
            ret = False                         

        return ret

    @classmethod
    def is_libtype_name_valid(cls, libtype_name):
        '''
        Validates the libtype name

        :param libtype_name: The libtype name being validated
        :type libtype_name: str
        :return: Boolean indicating whether or not the libtype name is valid
        :rtype: bool
        '''
        ret = False

        if Validator.contains_whitespace(libtype_name):
            cls._logger.error('LibType name {0} contains whitespace character(s)'.format(
                libtype_name
            ))
            ret = False
        else:
            ret = True

        return ret

    @classmethod
    def is_library_name_valid(cls, library_name):
        '''
        Validates the library name

        :param library_name: The library name to be validated
        :type library_name: str
        :return: Boolean indicating whether or not the library name is valid
        :rtype: bool
        '''
        ret = False

        if Validator.contains_whitespace(library_name):
            cls._logger.error('Library name {0} contains whitespace character(s)'.format(
                library_name
            ))
            ret = False
        else:
            ret = True

        return ret

    @classmethod
    def is_release_number_valid(cls, release_number):
        '''
        Validates the release number

        :param release_number: The release number to be validated
        :type release_number: str or int
        :return: Boolean indicating whether or not release_number is valid
        :rtype: bool
        '''
        ret = False

        if not Validator.is_integer(release_number):
            cls._logger.error('Release number {0} is not a number'.format(
                release_number
            ))
            ret = False
        else:
            ret = True

        # Release numbers must be greater than 0
        # If ret is true release_number must be numeric so int() is safe
        if ret and int(release_number) <= 0:
            cls._logger.error('{0} is not a valid release number. Release numbers must be greater than 0'.format(
                release_number
            ))
            ret = False

        return ret

    @classmethod
    def is_config_name_valid(cls, config_name):
        '''
        Validates the config name

        :param config_name: The configuration name being validated
        :type config_name: str
        :return: Boolean indicating whether or not the config name is valid
        :rtype: bool
        '''
        ret = False

        if Validator.contains_whitespace(config_name):
            cls._logger.error('Config name {0} contains whitespace character(s)'.format(
                config_name
            ))
            ret = False
        else:
            ret = True

        return ret

class AlteraName(object):
    '''
    Contains validation methods for Altera object names
    '''
    _logger = logging.getLogger(__name__)

    @classmethod
    def is_label_valid(cls, label):
        '''
        Validates the label

        :param label: The lable being validated
        :type label: str
        :return: Boolean indicating whether or not the label is valid
        :rtype: bool
        '''
        ret = False

        if not re.match(r'^[\w.-]+$', label):
            error_msg = 'Label {0} contains invalid characters.'.format(label)
            error_msg += ' Valid characters are a-zA-Z0-9.-_'
            cls._logger.error(error_msg)
            ret = False
        else:
            ret = True

        return ret

## @}
