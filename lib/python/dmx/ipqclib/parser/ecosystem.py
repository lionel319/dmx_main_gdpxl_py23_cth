#!/usr/bin/env python
"""Parser for ecosystem sub-command"""
import argparse
from dmx.ipqclib.utils import get_ip_types, get_milestones

def get_ecosystem_parser(action, subparsers, group_mandatory, group_exclusive, group_optional):
    """Create parser for ecosystem sub-command"""
    ecosystem = subparsers.add_parser(action, formatter_class=argparse.RawTextHelpFormatter, \
            add_help=False, description='Report a graph representing deliverable dependencies \
            based on IP name.')

    # mandatory arguments
    group_mandatory[action] = ecosystem.add_argument_group('mandatory arguments')

    # exclusive options
    group_exclusive[action] = ecosystem.add_mutually_exclusive_group(required=False)
    group_exclusive[action].add_argument('-i', '--ip_name', dest='ip', action='store', \
            metavar='<ip_name>@<bom>', default=None, required=False, help='IP name. @<bom> is \
            optionnal if you need to specify a config other than dev (RC_, WIP, snap-, REL)')
    group_exclusive[action].add_argument('--ip-type', dest='ip_type', action='store', \
            metavar='<ip_type>', choices=get_ip_types(), default=None, required=False, \
            help='IP type.')

    group_exclusive_milestone = {}
    group_exclusive_milestone[action] = ecosystem.add_mutually_exclusive_group(required=False)
    group_exclusive_milestone[action].add_argument('--milestones', dest='milestones', \
            action='store_true', default=False, required=False, help='--milestones to display \
            milestones information in the graph.')
    group_exclusive_milestone[action].add_argument('-m', '--milestone', dest='milestone', \
            action='store', choices=get_milestones(), default='99', required=False, \
            help='--milestone to display deliverable graph for the given milestone.')

    # optional arguments
    group_optional[action] = ecosystem.add_argument_group('optional arguments')
    group_optional[action].add_argument('-p', '--project_name', dest='project', action='store', \
            metavar='<project>', default=None, required=False, help='Project name from ICM.')
    group_optional[action].add_argument('--checkers', dest='checkers', action='store_true', \
            default=False, required=False, help='--checkers to display checkers information in \
            the graph.')
    group_optional[action].add_argument('--view', dest='view', action='store', default=None, \
            required=False, metavar='<view_name>', help='view name.')

    return (ecosystem, group_mandatory, group_exclusive, group_optional)
