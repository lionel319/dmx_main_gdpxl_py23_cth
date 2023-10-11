# -*- coding: utf-8 -*-
"""
Common user interface command to parse command line arguments
"""

from argparse import ArgumentParser as _ArgumentParser
from argparse import ArgumentError as _ArgumentError
import re as _re
import shlex as _shlex
import os as _os
import sys as _sys
from distutils import util as _util
from gettext import gettext as _

class _uiScriptOptionsClass(_ArgumentParser):
    """Object for parsing command line strings into Python objects.
    
    Keyword Arguments:
        - namespace -- String containing the options. The format of the namespace is as follow:
        - conflict_handler -- String indicating how to handle conflicts
    """

    namespace_arguments = ['option', 'long_option', 'name', 'requirement', 'type', 'default', 'description']
    d_action = {'string' : 'store', 'file' : 'string', 'boolean' : 'store_true', 'append' : 'append', 'enum' : 'store'}

    def __init__(self,
                 namespace=None,
                 conflict_handler='error'
                 ):

        superinit = super(_uiScriptOptionsClass, self).__init__
        superinit(conflict_handler=conflict_handler)
        self.namespace = namespace
        self.default_prefix = '-'

        # convert namespace string into dict
        self.d_namespace = self._convert_namespace_to_dict(self.namespace)
        
        # check the namespace options consistency
        self._check_namespace_options(self.d_namespace)

        # convert input command arguments list into dict
        self.d_args = self._args_to_dict(_sys.argv[1:])

        # add the options
        self.options = self._add_arguments(self.d_args, self.d_namespace)

    def _read_arguments_from_string(self, namespace):
        """
        Get the lines options. Remove empty lines and comments.
        Return a list of line options
        """
        arguments = []
        for line in namespace.splitlines():
            if ((line != '') and (line.strip() != '') and (_re.match("^\s*#.*", line) == None)):
                # Patch for not splitting bracket and space. Replace bracket by quote
                if (_re.match(".*enum.*(.*).*", line) != None):
                    line = _re.sub('\(|\)', '"', line)
                line_list = self._convert_arg_line_to_list(line)
                arguments.append(line_list)
        return arguments

    def _convert_arg_line_to_list(self, arg_line):
        return(_shlex.split(arg_line))

    def _convert_namespace_to_dict(self, namespace):
        """
        Convert the namespace string into dict
        """

        # pre-check on namespace
        self._check_namespace_length(self.namespace)

        args_list = self._read_arguments_from_string(namespace)
        new_args_list = []
        for args in args_list:
            args_dict = {}
            for i, index in enumerate(self.namespace_arguments):
                args_dict[index] = args[i]

            # make "-" option value equals to ""
            if args_dict['option'] == "-" :
                args_dict['option'] = ""

            # make "-" long_option value equals to ""
            if args_dict['long_option'] == "-" :
                args_dict['long_option'] = ""


            # make "-" default value equals to ""
            if args_dict['default'] == "-" :
                args_dict['default'] = ""

            # append type must be a list
            if args_dict['type'] == 'append' :
                args_dict['default'] = args_dict['default'].split()

            new_args_list.append(args_dict)

        return new_args_list

    def _check_namespace_length(self, namespace):
        """
        The length of the option in the namespace must be the lenght of the namespace_arguments
        """
        self.namespace = namespace
        arg_list = self._read_arguments_from_string(self.namespace)
        for option_line in arg_list:
            if (len(option_line) != len(self.namespace_arguments)) :
                self.error(_('missing or extra option(s) in namespace options: %s') % namespace)

    def _check_namespace_options(self, args):
        """
        Check the namespace options consistency
        Default value of boolean type must be True or False
        Default value of enum type must be a list of minimum 2 elements
        Default value of enum : make a list type
        """     
        for arg in args:
            # check boolean type
            if(arg['type'] == 'boolean'):
                try:
                    _util.strtobool(arg['default'])
                except ValueError:
                    self.error(_('default value %s of %s is not a boolean') % (arg['default'], arg['name']))
            # check enum type
            if(arg['type'] == 'enum'):
                arg['default'] = arg['default'].split()
                if len(arg['default']) < 2 :
                    self.error(_('devalut values of %s is not an enum') % arg['name'])


    def _args_to_dict(self, args):
        """
        Make a dict of arguments:
            if there is a boolean in the argument list, set argument to True
        Example:
            args    = ['-opt1', 'val1', '-opt2', 'val2', '-opt3']
            d_args  = {'-opt1': 'val1', '-opt2': 'val2', '-opt3': True}
        """

        # get the type of the options
        self.d_args_type = self._get_args_type(self.d_namespace)
        
        l_possible_options = [option['option'] for option in self.d_namespace]
        for option in self.d_namespace:
            l_possible_options.append(option['long_option'])
        l_possible_options.append("-h")
        l_possible_options.append("--help")
        l_possible_options.append("--debug")

        d_args = {}

        for index, arg in enumerate(args):
            if (_re.match('^-', arg)):
                # check if the command line option is part of the namespace
                if not arg in l_possible_options :
                    self.error(_('option %s is not defined in namespace options: %s') % (arg, self.namespace))
                elif ('-h' in args) or ('--help' in args):
                    continue
                # if a boolean is invoked, set boolean value to True
                if self.d_args_type[arg] == 'boolean':
                    d_args[arg] = 'True'
                # if append option is invoked, make a list
                elif self.d_args_type[arg] == 'append':
                    if arg in d_args :
                        d_args[arg].append(args[index+1])
                        index = index + 1
                    else :
                        d_args[arg] = []
                        d_args[arg].append(args[index+1])
                        index = index + 1
                else :
                    try:
                        d_args[arg] = args[index+1]
                        index = index + 1
                    except IndexError:
                        pass

        return d_args

    def _get_args_type(self, namespace):
        """
        Get the sys.argv[1:] options into a dict
        """

        d_type = {}

        for opt in namespace:
            d_type[opt['option']] = opt['type']
            d_type[opt['long_option']] = opt['type']

        return d_type
        
    def _add_arguments(self, args, namespace):
        """
        argparse module to set the arguments
        """

        # add arguments
        self.parser = _ArgumentParser()

        #######################
        # Mandatory arguments
        #######################
        requiredArgument = self.parser.add_argument_group('mandatory arguments')
        for arg in namespace:
            if (arg['requirement'] == 'mandatory') and (arg['option'] != "") and (arg['long_option'] != "") :

                if arg['type'] == 'boolean':
                    requiredArgument.add_argument(arg['option'],  arg['long_option'], action=self.d_action[arg['type']], dest=arg['name'], required=True, help=arg['description'])
                elif arg['type'] == 'enum':
                    requiredArgument.add_argument(arg['option'],  arg['long_option'], choices=(arg['default']), metavar=arg['name'], action=self.d_action[arg['type']], dest=arg['name'], required=True, help=arg['description'])
                else:
                    requiredArgument.add_argument(arg['option'],  arg['long_option'], metavar=arg['name'], action=self.d_action[arg['type']], dest=arg['name'], required=True, help=arg['description'])

            elif (arg['requirement'] == 'mandatory') and (arg['option'] == "") and (arg['long_option'] != "") :
                if arg['type'] == 'boolean':
                    requiredArgument.add_argument(arg['long_option'], action=self.d_action[arg['type']], dest=arg['name'], required=True, help=arg['description'])
                elif arg['type'] == 'enum':
                    requiredArgument.add_argument(arg['long_option'], choices=(arg['default']), metavar=arg['name'], action=self.d_action[arg['type']], dest=arg['name'], required=True, help=arg['description'])
                else:
                    requiredArgument.add_argument(arg['long_option'], metavar=arg['name'], action=self.d_action[arg['type']], dest=arg['name'], required=True, help=arg['description'])


        ######################
        # Optional arguments
        ######################
        requiredArgument = self.parser.add_argument_group('optional arguments')
        
        for arg in namespace:
            if (arg['requirement'] == 'optional') and (arg['option'] != "") and (arg['long_option'] != "") :
                if arg['type'] == 'boolean':
                    requiredArgument.add_argument(arg['option'], arg['long_option'], action=self.d_action[arg['type']], dest=arg['name'], required=False, default=arg['default'], help=arg['description'])
                elif arg['type'] == 'enum':
                    requiredArgument.add_argument(arg['option'], arg['long_option'], choices=(arg['default']), metavar=arg['name'], action=self.d_action[arg['type']], dest=arg['name'], required=False, help=arg['description'])
                else :
                    requiredArgument.add_argument(arg['option'], arg['long_option'], metavar=arg['name'], action=self.d_action[arg['type']], dest=arg['name'], required=False, default=arg['default'], help=arg['description'])

            elif (arg['requirement'] == 'optional') and (arg['option'] == "") and (arg['long_option'] != "") :
                if arg['type'] == 'boolean':
                    requiredArgument.add_argument(arg['long_option'], action=self.d_action[arg['type']], dest=arg['name'], required=False, default=arg['default'], help=arg['description'])
                elif arg['type'] == 'enum':
                    requiredArgument.add_argument(arg['long_option'], choices=(arg['default']), metavar=arg['name'], action=self.d_action[arg['type']], dest=arg['name'], required=False, help=arg['description'])
                else :
                    requiredArgument.add_argument(arg['long_option'], metavar=arg['name'], action=self.d_action[arg['type']], dest=arg['name'], required=False, default=arg['default'], help=arg['description'])


        options = self.parser.parse_args()

        return options


def uiScriptOptions(namespace):

    args = _uiScriptOptionsClass(namespace=namespace)

    return args.options

