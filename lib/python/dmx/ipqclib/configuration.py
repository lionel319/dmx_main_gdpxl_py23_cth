#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable-msg=C0103
# pylint: disable-msg=C0301
# pylint: disable-msg=R0911
# pylint: disable-msg=R0913
# pylint: disable-msg=W0102
# pylint: disable-msg=R0902
"""
The configuration of IPQC is managed by a ini-based file.
The initilization file contains all the information related to the options of the checkers.
The user should define the options only once and store the configuration file into \
        <workspace>/<ip_name>/ipqc.ini location.

   Syntax :
 	Comments
           A line that starts with "#" is commented out.

 	Blank line
           Empty lines are removed.

	Keys (Options)
           Keys is basic element representing option. Each option has a name and a value delimited \
                   by an equal sign "=". The name appears to the left of the equals sign.

            Rules for converting values:
	        If value if quoted with " chars, it’s a string.
	        If the value is "true" or "false", it’s converted to a Boolean.
       Section
           There are two section levels:
	        Checker name level: section name representing the name of the checker appears on a \
                        line by itself in square brackets.
                   All keys associated after the section declaration are associated with that \
                           section. Options defined at this level will automatically be applied to \
                           all the cells;
	        Cell name level: cell section in part of checker section. Section name \
                        representing the name of the cell appears on a \
                   line by itself in double square brackets. Options defined at cell level are \
                   applied only for this given cell. Cell level section takes precedence of \
                   checker section.
"""

# $Id: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/ipqclib/configuration.py#1 $
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/ipqclib/configuration.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Change: 7411538 $
# $File: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/ipqclib/configuration.py $
# $Revision: #1 $
# $Author: lionelta $
import re
import datetime
import shutil

from dmx.ipqclib.settings import _IPQC_INIT, _OPTIONS_TO_REMOVE
from dmx.utillib.configobj import ConfigObj, ConfigObjError
from dmx.ipqclib.log import uiWarning
from dmx.ipqclib.utils import is_non_zero_file
from dmx.ipqclib.ipqcException import IniConfigCorrupted

def is_section(config_section):
    """is_section"""
    try:
        config_section.keys()
    except AttributeError:
        return False
    else:
        return True


class Configuration(object):
    """Configuration class"""
    def __init__(self, ipname, workspace, initfile=None, ciw=False):

        self.ipname = ipname
        self.initfile = initfile

        if self.initfile != None and not is_non_zero_file(self.initfile):
            uiWarning('{} ini file is empty. Default ini file {} is used' .format(self.initfile, \
                    _IPQC_INIT))

        self.workspace = workspace
        self._ciw = ciw

        self.cell_list = self.workspace.get_cells_for_ip(self.ipname)

        # DATE
        self.date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Default options from DMXDATA
        self.default_initfile = _IPQC_INIT
        self.default_options = ConfigObj(self.default_initfile, interpolation=True)

        # Setting ipqc.ini options
        if self.initfile != None:
            try:
                self.user_options = ConfigObj(self.initfile, interpolation=True)
            except ConfigObjError as err:
                message = 'The ini file '+self.initfile+' provided is corrupted and cannot be \
                        parser properly.\n'+str(err)
                raise IniConfigCorrupted(message)

            for key, options in self.user_options.items():
                if key in self.default_options:
                    self.default_options[key] = options

        self.options = self.get_options()

        self.header = ['# Date: '+self.date, \
                        '# IPQC Configuration file: ipqc.ini', \
                        '# IP Name: '+self.ipname, \
                        '']


    # return a dictionnary containing checker name section and cell name section
    def set_options_by_cell(self, options, checker, cell):
        """
        DI-1254 - http://pg-rdjira:8080/browse/DI-1254
        Options value should always be a string.
        If Options value is a list, make it a string

        Example:
            lint_check - review
            [lint__review__cc_check]
            Options= -top upiphy_agent -waiverfile upiphy_agent.review.swl,upiphy_agent.nohier.swl

            If Options value is not double-quoted we obtain a list:
                Options --> ['-top upiphy_agent -waiverfile upiphy_agent.review.swl', 'upiphy_agent.nohier.swl']
            We want a string:
                Options --> '-top upiphy_agent -waiverfile upiphy_agent.review.swl,upiphy_agent.nohier.swl'
        """
        for key, val in self.default_options[checker].items():
            if key in options[checker][cell]:
                continue

            if key == "Waive" or key == "Skip":
                options[checker][cell][key] = bool(self.default_options.get(checker).as_bool(key))

            if isinstance(val, list):
                val = ','.join(val)

            # Do not handle cell sub-sections
            if (is_section(val) is False) and (key == 'Options'):
                options = self.process_options(options, key, val, cell, checker)

            elif (is_section(val) is False) and (key == 'Arcparams'):
                options = self.process_options(options, key, val, cell, checker)

            # cell sub-section
            elif key == cell:
                for key2, val2 in self.default_options[checker][key].items():

                    if key2 == "Waive" or key2 == "Skip":
                        options[checker][cell][key2] = \
                                self.default_options.get(checker).get(cell).as_bool(key2)
                        continue

                    if isinstance(val2, list):
                        val2 = ','.join(val2)

                    if is_section(val2) is False:
                        options = self.process_options(options, key2, val2, cell, checker)

        return options

    def process_options(self, options, key, string, cell, checker):
        """process_options"""
        string = re.sub('&wkspace_root;', self.workspace.path, string)
        string = re.sub('&ip_name;', self.ipname, string)
        string = re.sub('&cell_name;', cell, string)

        if self._ciw is True:
            for option in _OPTIONS_TO_REMOVE:
                string = re.sub(option, '', string)

        #options[checker][cell][key] = string.replace('"', '\\"')
        options[checker][cell][key] = string

        return options


    def get_options(self):
        """get_options"""
        options = {}

        for checker in self.default_options.keys():

            options[checker] = {}

            for cell in self.cell_list:

                if cell in self.default_options[checker]:
                    options[checker][cell] = self.default_options[checker][cell]
                else:
                    options[checker][cell] = {}

                options = self.set_options_by_cell(options, checker, cell)

        return options


    # store ipqc.ini file into workspace environment to keep trace and be able to reproduce IPQC run
    def save(self, dst):
        """save"""
        if self.initfile != None:
            shutil.copyfile(self.initfile, dst)
        else:
            shutil.copyfile(self.default_initfile, dst)
