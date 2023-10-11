#!/usr/bin/env python
"""Parser object for IPQC"""
import sys
import argparse

class Parser(object):
    """Parser class supports sub-commands"""
    def __init__(self):

        self._actions = ['ecosystem', 'ip-graph', 'setup', 'dry-run', 'run-all', 'catalog']

        # top-level parser
        self._parser = argparse.ArgumentParser(
            prog='ipqc',
            description='IPQC - IP Quality Checks',
            add_help=False
        )

        # default command is run-all
        if not sys.argv[1:2][0] in self._actions:
            sys.argv.insert(1, 'run-all')

        # parser for sub-commands
        subparsers = self._parser.add_subparsers(title='sub-commands')

        group_mandatory = {}
        group_exclusive = {}
        group_optional = {}

        ###############################################
        # ecosystem sub-command options
        ###############################################
        if sys.argv[1] == 'ecosystem':
            from dmx.ipqclib.parser.ecosystem import get_ecosystem_parser
            action = 'ecosystem'
            (main, group_mandatory, group_exclusive, group_optional) = \
                get_ecosystem_parser(action, subparsers, group_mandatory, group_exclusive, \
                        group_optional)
            main.set_defaults(which=action)


        ###############################################
        # ip-graph sub-command options
        ###############################################
        if sys.argv[1] == 'ip-graph':
            from dmx.ipqclib.parser.ipgraph import get_ipgraph_parser
            action = 'ip-graph'
            (main, group_mandatory, group_exclusive, group_optional) = \
                get_ipgraph_parser(action, subparsers, group_mandatory, group_exclusive, \
                        group_optional)
            main.set_defaults(which=action)


        #############################
        # parser for setup
        #############################
        if sys.argv[1] == 'setup':
            from dmx.ipqclib.parser.setup import get_setup_parser
            action = 'setup'
            (main, group_mandatory, group_exclusive, group_optional) = \
                get_setup_parser(action, subparsers, group_mandatory, group_exclusive, \
                        group_optional)
            main.set_defaults(which=action)


        #############################
        # dry-run sub-command options
        #############################
        if sys.argv[1] == 'dry-run':
            from dmx.ipqclib.parser.dryrun import get_dryrun_parser
            action = 'dry-run'
            (main, group_mandatory, group_exclusive, group_optional) = \
                get_dryrun_parser(action, subparsers, group_mandatory, group_exclusive, \
                        group_optional)
            main.set_defaults(which=action)


        ###############################################
        # run_all sub-command options (default command)
        ###############################################
        if sys.argv[1] == 'run-all':
            from dmx.ipqclib.parser.runall import get_runall_parser
            action = 'run-all'
            (main, group_mandatory, group_exclusive, group_optional) = \
                get_runall_parser(action, subparsers, group_mandatory, group_exclusive, \
                        group_optional)
            main.set_defaults(which=action)

        #############################
        # catalog sub-command options
        #############################
        if sys.argv[1] == 'catalog':
            from dmx.ipqclib.parser.catalog import get_catalog_parser
            action = 'catalog'
            (main, group_mandatory, group_exclusive, group_optional) = \
                get_catalog_parser(action, subparsers, group_mandatory, group_exclusive, \
                        group_optional)
            main.set_defaults(which=action)


        ###############################
        # options common to all actions
        ###############################
        group_optional[action].add_argument('--log-file', dest='logfile', action='store', \
                metavar='<logfile_name>', default='ipqc.log', required=False, help='Log file.')
        group_optional[action].add_argument('--output-dir', dest='output_dir', \
                action='store', metavar='<output_dir>', required=False, default=None, \
                help='Output directory. Data generated by IPQC are stored in this location.')
        group_optional[action].add_argument('--debug', dest='debug', action='store_true', \
                default=False, required=False)
        group_optional[action].add_argument('-h', '--help', action='help', \
                help='show this help message and exit')


        self.args = self._parser.parse_args()

        if (('recipients' in vars(self.args) and (self.args.recipients != None)) and \
                ('sendmail' not in vars(self.args) or not self.args.sendmail)):
            self._parser.error('The --recipients arguments requires the --sendmail option.')

    @property
    def actions(self):
        ''' actions '''
        return self._actions

    @property
    def parser(self):
        """parser"""
        return self._parser
