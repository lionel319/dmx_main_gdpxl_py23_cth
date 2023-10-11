#!/usr/bin/env python
"""
    Arguments for catalog sub-parser
"""
import os
import argparse
from dmx.ipqclib.parser.utils import get_deliverables

def get_catalog_parser(action, subparsers, group_mandatory, group_exclusive, group_optional):
    """ Definition of catalog sub-parser options"""

    catalog = subparsers.add_parser(action, formatter_class=argparse.RawTextHelpFormatter, \
            description="Catalog", \
            add_help=False)

    # optional arguments
    group_optional[action] = catalog.add_argument_group('optional arguments')
    group_optional[action].add_argument('-f', '--family', dest='family', action='store', \
            default=os.getenv("DB_FAMILY"), required=False, metavar='<family_name>', \
            help='family name.')
    group_optional[action].add_argument('-i', '--ip_name', dest='ip', action='store', \
            nargs='+', default=[], required=False, metavar='<ip_name>', help='ip name.')
    group_optional[action].add_argument('-d', '--deliverable', dest='deliverable', \
            action='store', nargs='+', default=[], required=False, choices=get_deliverables(), \
            metavar='<deliverable_name>', help='deliverable name.')
    group_optional[action].add_argument('--update-releases-db', dest='update_releases_db', \
            action='store_true', default=False, required=False, \
            help=argparse.SUPPRESS)
    group_optional[action].add_argument('--update-catalog-db', dest='update_catalog_db', \
            action='store_true', default=False, required=False, \
            help=argparse.SUPPRESS)
    group_optional[action].add_argument('--db-equivalency-check', dest='db_equivalency_check', \
            action='store_true', default=False, required=False, \
            help=argparse.SUPPRESS)
    group_optional[action].add_argument('--generate-dashboard', dest='generate_dashboard', \
            action='store_true', default=False, required=False, \
            help=argparse.SUPPRESS)
    group_optional[action].add_argument('--push-in-catalog', dest='push_in_catalog', \
            action='store_true', default=False, required=False, \
            help=argparse.SUPPRESS)
    group_optional[action].add_argument('--all', dest='all', \
            action='store_true', default=False, required=False, \
            help=argparse.SUPPRESS)
    group_optional[action].add_argument('--get-releases', dest='get_releases', \
            action='store_true', default=False, required=False, \
            help='list the releases that are available')
    group_optional[action].add_argument('--get-catalog-releases', dest='get_catalog_releases', \
            action='store_true', default=False, required=False, \
            help='list the releases that are available in IPQC catalog')
    group_optional[action].add_argument('--preview', dest='preview', \
            action='store_true', default=False, required=False, \
            help=argparse.SUPPRESS)

    # exclusive arguments
    group_exclusive[action] = {}

    return (catalog, group_mandatory, group_exclusive, group_optional)
