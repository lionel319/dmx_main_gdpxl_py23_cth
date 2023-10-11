#!/usr/bin/env python
"""Parser for ipgraph sub-command"""
import argparse

def get_ipgraph_parser(action, subparsers, group_mandatory, group_exclusive, group_optional):
    """Create parser for ipgraph sub-command"""
    ipgraph = subparsers.add_parser(action, formatter_class=argparse.RawTextHelpFormatter, \
        add_help=False, description='Report a graph representing IP and its hierarchybased \
        on IP name.')

    # mandatory arguments
    group_mandatory[action] = ipgraph.add_argument_group('mandatory arguments')
    group_mandatory[action].add_argument('-i', '--ip_name', dest='ip', action='store', \
        metavar='<ip_name>@<bom>', required=True, help='IP name. @<bom> is optionnal if \
        you need to specify a config other than dev (RC_, WIP, snap-, REL)')

    # optional arguments
    group_optional[action] = ipgraph.add_argument_group('optional arguments')

    return (ipgraph, group_mandatory, group_exclusive, group_optional)
