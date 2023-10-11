#! /usr/bin/env python

'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/py23comlib/arc_utils/1.7_py23/arc_util.py#1 $

arc_util provides utilities for analyzing ARC resources.
'''
from __future__ import print_function

import argparse
import logging
from pprint import pprint
import os
import sys
import re

from arc_orm.arc_orm import ArcORM, resource_info_diff, detail_diff

def print_leaves(orm, res_name):
    '''
    Print the sorted, unique set of leaves that are reachable
    from the given collection resource.
    '''

    all_leaves = set()

    for (_rname, _hier, _collections, leaves) in orm.walk_collection(res_name):
        # all we care about is the leaves
        all_leaves |= set(leaves)

    for leaf in sorted(all_leaves):
        print(leaf)
    
def print_res_tree(orm, res_name, limit, want_url = False):
    '''
    Print out the resource tree for the given 'res_name', indenting 3
    dots for each 'indent' level.  If 'limit' is given, do not print
    anything deeper than 'limit' levels.
    '''

    if not res_name:
        return

    print('#==================================================')
    print('# Resource name: {0}'.format(res_name))
    if limit:
        print('# (limited to {0} levels)'.format(limit))
    print('#==================================================')

    for (rname, hier, collections, leaves) in orm.walk_collection(res_name):

        indent = len(hier)

        url = ''
        if want_url:
            url = ' ' + orm.resource_url(rname)

        print('{0}[{1}] {2}{3}'.format('...'*indent, indent, rname, url))

        if limit and limit <= len(hier):
            # Empty out the collections list so we don't go any deeper
            collections[:] = []
            # And don't print this guy's leaves
            continue

        indent += 1

        for leaf in leaves:
            url = ''
            if want_url:
                url = ' ' + orm.resource_url(leaf)
            print('{0}[{1}] {2}{3}'.format('...'*indent, indent, leaf, url))


def print_to_leaf(orm, res_name, to_leaf):
    '''
    Print out the resource tree for the given 'res_name', indenting 3
    dots for each 'indent' level.  If 'limit' is given, do not print
    anything deeper than 'limit' levels.
    '''

    if not res_name:
        return

    print('#==================================================')
    print('# Resource name: {0}'.format(res_name))
    print('#     Paths to leaf: {0}'.format(to_leaf))
    print('#==================================================')

    for (rname, hier, collections, leaves) in orm.walk_collection(res_name):
        matches = []
        for leaf in leaves:
            if (re.match(to_leaf, leaf)):
                matches.append(leaf)

        if matches:
            indent = 0
            full_hier = list(hier)
            full_hier.append(rname)

            for res in full_hier:
                print('{0}[{1}] {2}'.format('...'*indent, indent, res))
                indent += 1
                
            for leaf in matches:
                print('{0}[{1}] {2}'.format('...'*indent, indent, leaf))

            print("")

def resource_collection_expand(opts):
    '''
    Print an expansion of the collection given, optionally printing
    only the leaves.
    '''
    orm = ArcORM()

    if (opts.leaf_only):
        print_leaves(orm, opts.resource)
    elif (opts.to_leaf):
        print_to_leaf(orm, opts.resource, opts.to_leaf)
    else:
        print_res_tree(orm, opts.resource, opts.limit, opts.want_url)

def resource_diff(opts):
    '''
    Print the "diff"s between two resources, ignoring fields
    that will always be different:
    - __resource_name
    - created_at
    - definition_source
    - description
    - id
    '''

    if (':' in opts.resource1):
        site1, res1 = opts.resource1.split(':')
        orm1 = ArcORM(site1)
    else:
        orm1 = ArcORM()
        res1 = opts.resource1

    if (':' in opts.resource2):
        site2, res2 = opts.resource2.split(':')
        orm2 = ArcORM(site2)
    else:
        orm2 = ArcORM()
        res2 = opts.resource2

    info1 = orm1.resource_info(res1)
    info2 = orm2.resource_info(res2)
    diffs = resource_info_diff(info1, info2, opts.all)

    if not diffs:
        print("No diffs")
    else:
        pprint(diffs)

def resources_using(opts):
    '''
    List the resource collections which have the given resource in
    their resource list.
    '''

    orm = ArcORM()

    logging.debug('Calling orm.resources_using(\'{0}\')'.format(opts.resource))

    used_in = orm.resources_using(opts.resource)
    pprint(used_in)

def resource_lint(opts):
    '''
    Lint the given resource:
    1) If it's a collection:
        a) does 'resolved' == 'resources'?
        b) does it directly set any env vars?
    2) If it sets any foo_PATH env vars, do those directories exist?
    3) If it sets any LD_LIBRARY_PATH env vars, do those directories exist?
    4) If it's a config, does it have a default?
    5) Does it do any 'includes'?
    6) Does it have a csh_command?
    7) Does it have a command?
    8) Is the .pm file checked in?
    '''

    print('#==================================================')
    print('# Linting resource name: {0}'.format(opts.rname))
    print('#==================================================')

    orm = ArcORM()
    rinfo = orm.resource_info(opts.rname)
    if 'resolved' in rinfo:

        # Did all of the resources resolve?
        if rinfo['resolved'] != rinfo['resources']:
            logging.error("Resources did not resolve:")
            ddiff = detail_diff((rinfo['resources'], rinfo['resolved']))
            pprint(ddiff)

        # Does this collection set any env vars directly?
        for attr in rinfo:
            if attr.isupper() or attr.startswith(('+', '-')):
                logging.warning("Environment variables set by collection: {0} => {1}".format(attr, rinfo[attr]))

    # # Do /tools/paths given in resource exist?
    # for attr in rinfo:
    #     if attr.isupper() or attr.startswith(('+', '-')):
    #         maybe_path = rinfo[attr].replace('$ARC_TOOLS', '/tools/')
    #         if maybe_path.startswith('/tools'):
    #             if not os.path.exists(maybe_path):
    #                 logging.warning("Path does not exist: {0} => {1}".format(attr, rinfo[attr]))
    #             else:
    #                 logging.info("OK path {0} => {1}".format(attr, rinfo[attr]))

    # todo: does config have a default?

    if 'includes' in rinfo:
        logging.warning("Includes found: {0}".format(rinfo['includes']))
    if 'csh_command' in rinfo:
        logging.warning("csh_command found: {0}".format(rinfo['csh_command']))
    if 'command' in rinfo:
        logging.warning("command found: {0}".format(rinfo['command']))

    # todo: is the .pm file checked in?

def verbose_to_level(verbose):
    if (verbose > 1):
        return logging.DEBUG
    if (verbose > 0):
        return logging.INFO
    return logging.WARNING

def parse_args():
    '''
    Parse the arguments, using subparsers for each command type.
    '''
    
    # create the top-level parser
    parser = argparse.ArgumentParser(prog = 'arc_util',
                                     description = '''
Utilities for examining ARC resources.
'arc_util <subcommand> --help' will give help for the given subcommand.
''')

    # parser.add_argument('--dry_run', action = 'store_true', help = 'Report what would be done; don\'t really do it.')
    parser.add_argument('--trace', action = 'store_true', help = 'Trace python execution.')
    subparsers = parser.add_subparsers()

    parser.add_argument('--verbose','-v',  action = 'count', default = 0,
                        help = 'Add verbose messages.')

    # create the parser for the "resource-collection-expand" command
    parser_resource_coll_expand = subparsers.add_parser('resource-collection-expand',
                                                              help = 'Expand a collection\'s resources')
    parser_resource_coll_expand.add_argument('--limit', '-l', type = int, default = 0,
                                                   help = 'limit to n levels')
    parser_resource_coll_expand.add_argument('--leaf_only', '-L', action = 'store_true',
                                                   help = 'print leaves only')
    parser_resource_coll_expand.add_argument('--to_leaf', '-t',
                                                   help = 'show full expansion down to each matching resource')
    parser_resource_coll_expand.add_argument('--want_url', '-u', action = 'store_true',
                                                   help = 'give url to show_resource page')
    parser_resource_coll_expand.add_argument('resource', help = 'resource name')
    parser_resource_coll_expand.set_defaults(func = resource_collection_expand)

    # create the parser for the "resource-diff" command
    parser_resource_diff = subparsers.add_parser('resource-diff',
                                                 help = 'diff two resources')
    parser_resource_diff.add_argument('--all', '-a', action = 'store_true',
                                             help = 'print all diffs')
    parser_resource_diff.add_argument('resource1', help = 'name of first resource')
    parser_resource_diff.add_argument('resource2', help = 'name of second resource')
    parser_resource_diff.set_defaults(func = resource_diff)

    # create the parser for the "resources-using" command
    parser_resources_using = subparsers.add_parser('resources-using',
                                                   help = 'Output the list of collections this resource is found in.')
    parser_resources_using.add_argument('resource', help = 'resource name')
    parser_resources_using.set_defaults(func = resources_using)

    # create the parser for the "resource-lint" command
    parser_resource_coll_expand = subparsers.add_parser('resource-lint',
                                                              help = 'Lint the resource given')
    parser_resource_coll_expand.add_argument('rname', help = 'resource name')
    parser_resource_coll_expand.set_defaults(func = resource_lint)

    opts = parser.parse_args()
    return opts

def main():
    '''
    Utilities for getting information about ARC resources.
    '''

    opts = parse_args()

    logging.basicConfig(level = verbose_to_level(opts.verbose))

    if opts.trace:
        import trace
        tracer = trace.Trace(ignoredirs = [sys.prefix, sys.exec_prefix, '/tools/django/trunk/1.3.1'], count = 0)
        tracer.runfunc(opts.func, opts)
    else:
        opts.func(opts)

if __name__ == '__main__':
    main()
