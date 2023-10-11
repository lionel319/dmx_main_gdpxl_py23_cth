#! /usr/bin/env python

'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/py23comlib/arc_utils/1.7_py23/arc_admin.py#1 $

arc_admin provides utilities for manipulating ARC resources.
'''
from __future__ import print_function

import argparse
import logging
import os
import P4
import re
import sys

# from arc_orm.arc_orm import ArcORM, resource_info_diff

def perl_protect(string):
    '''
    Return a string that is transformed in the way resource names need
    to be for ARC resource names used in a Perl script.  This means each path
    component needs to have underscores before any leading digits, and
    underscores instead of any dot or dash.
    >>> perl_protect('a2b')
    'a2b'
    >>> perl_protect('1.0')
    '_1_0'
    >>> perl_protect('project/agathon/1.0/13')
    'project/agathon/_1_0/_13'
    '''

    if '/' in string:
        # Each path component needs to be protected separately,
        # so recurse for each part and then join them back again.
        parts = string.split('/')
        protected_parts = [perl_protect(part) for part in parts]
        return '/'.join(protected_parts)
    
    str_protected = re.sub('^(?=[0-9])|\.|-', '_', string)
    return str_protected

def p4connect(client):
    '''
    Connect to the p4, using the client given or the default client.
    Exits on failure (should be fixed to raise an exception instead).
    Returns the client connection.
    '''
    p4c = P4.P4()
    if (client):
        p4c.client = client

    try:
        p4c.connect()
    except P4.P4Exception:
        for exception in p4c.errors:
            print(exception)
        sys.exit(-1)

    clientspec = p4c.fetch_client()

    if 'Update' not in clientspec:
        print('Client {0} not found.'.format(p4c.client))
        sys.exit(-1)
    else:
        logging.info('Using client {0}.'.format(p4c.client))
    
    return p4c
        
def resource_clone(opts):
    '''
    Clone the resource definition from opts.from_resource into opts.to_resource
    by copying the from_resource .pm file into a new to_resource .pm file.
    The from_resource .pm file must exist, and the to_resource .pm file
    must not (previously) exist.
    '''
    from_resource = opts.from_resource
    to_resource = opts.to_resource
    client = opts.client
    set_perl_var = opts.set_perl_var
    force = opts.force
    
    logging.debug('entering resource_clone()')
    logging.debug('clone from {0} to {1}, client {2}'.format(
            from_resource, to_resource, client if client else 'unspecified'))

    p4c = p4connect(client)

    # Make sure that we can find the source file
    from_resource_protected = perl_protect(from_resource)
    to_resource_protected = perl_protect(to_resource)
    from_package = '::'.join(from_resource_protected.split('/'))
    to_package = '::'.join(to_resource_protected.split('/'))
    depot_from_path = '//depot/devenv/psg_resources/{0}.pm'.format(from_resource_protected)
    depot_to_path = '//depot/devenv/psg_resources/{0}.pm'.format(to_resource_protected)

    try:
        whereis_from_pm = p4c.run_where(depot_from_path)
    except P4.P4Exception as p4exception:
        print(p4exception)
        sys.exit(-1)
    
    fs_from_path = whereis_from_pm[0]['path']

    if not os.path.exists(fs_from_path):
        raise ValueError
    
    # Todo: refactor the p4 access and error checking into a method/class of its own
    try:
        whereis_to_pm = p4c.run_where(depot_to_path)
    except P4.P4Exception as p4exception:
        print(p4exception)
        sys.exit(-1)
    
    fs_to_path = whereis_to_pm[0]['path']

    if os.path.exists(fs_to_path):
        if force:
            logging.warning("'{}' already exists".format(fs_to_path))
        else:
            logging.error("'{}' already exists".format(fs_to_path))
            sys.exit(-1)
    
    with open(fs_from_path, 'r') as from_file:
        from_lines = from_file.readlines()

    # Is there a better way to do multiple replacements across all lines of a file?
    # In this case, the file is very tiny so it doesn't need to be efficient anyway.
    to_lines = from_lines
    to_lines = [to_line.replace(from_package, to_package) for to_line in to_lines]
    to_lines = [to_line.replace(depot_from_path, depot_to_path) for to_line in to_lines]
    to_lines = [to_line.replace(from_resource, to_resource) for to_line in to_lines]
    for pvar_setting in set_perl_var:
        (var, value) = pvar_setting.split('=')
        from_pattern = '^my \\${0} = .*;'.format(var)
        to_replacement = 'my ${0} = \'{1}\';'.format(var, value)
        to_lines = [re.sub(from_pattern, to_replacement, to_line) for to_line in to_lines]

    # Do a p4 copy fs_from_path to fs_to_path, then p4 edit of fs_to_path.
    # This informs p4 that they are related, so that p4v can show the relationships in the version graph.
    try:
        copy_retval = p4c.run_copy(fs_from_path, fs_to_path)
    except P4.P4Exception as p4exception:
        print(p4exception)
        sys.exit(-1)

    # print 'copy_retval is', copy_retval

    try:
        edit_retval = p4c.run_edit(fs_to_path)
    except P4.P4Exception as p4exception:
        print(p4exception)
        sys.exit(-1)

    # print 'edit_retval is', edit_retval

    with open(fs_to_path, 'w') as to_file:
        to_file.writelines(to_lines)
    
    logging.debug('leaving resource_clone()')
              
def parse_args():
    '''
    Parse the arguments, using sub-parsers for each command type.
    '''
    
    # create the top-level parser
    parser = argparse.ArgumentParser(prog = 'arc_admin',
                                     description = '''
Utilities for manipulating ARC resources. 'arc_admin <sub-command> --help'
will give help for the given sub-command.
''')

    parser.add_argument('--dry_run', action = 'store_true',
                        help = 'Report what would be done; don\'t really do it.')
    parser.add_argument('--trace', action = 'store_true',
                        help = 'Trace python execution.')
    parser.add_argument('--verbose', '-v', action = 'count', default = 0,
                        help = 'Add verbose messages.')

    subparsers = parser.add_subparsers()

    # create the sub-parser for the "resource-clone" command
    parser_resource_clone = subparsers.add_parser('resource-clone',
                                                        help = 'Clone a resource\'s .pm file')
    parser_resource_clone.add_argument('--force', '-f', action = 'store_true',
                                       help = 'Allow overwrite of existing .pm file')
    parser_resource_clone.add_argument('--client', '-c', help = 'Perforce client (e.g. \'-c workspace1\')')
    parser_resource_clone.add_argument('--set_perl_var', '-s', action = 'append', default = [],
                                             help = 'set perl variable (e.g. \'-s my_version=6.4\').  May be repeated.')
    parser_resource_clone.add_argument('from_resource',
                                             help = 'from resource name (e.g. \'example/1.0\')')
    parser_resource_clone.add_argument('to_resource',
                                             help = 'to resource name (e.g. \'example/1.1\')')
    parser_resource_clone.set_defaults(func = resource_clone)

    opts = parser.parse_args()

    return opts

def verbose_to_level(verbose):
    '''
    Use the verbosity level (set with the verbose option, e.g. '-v' or '-v2' or '-v -v')
    to choose a logging level.
    verbose = 2 or greater will turn on DEBUG, INFO, WARNING, and ERROR messages.
    verbose = 1 will turn on INFO, WARNING, and ERROR messages.
    verbose = 0 will turn on WARNING and ERROR messages.
    >>> logging.getLevelName(verbose_to_level(2))
    'DEBUG'
    >>> logging.getLevelName(verbose_to_level(1))
    'INFO'
    >>> logging.getLevelName(verbose_to_level(0))
    'WARNING'
    '''
    if (verbose > 1):
        return logging.DEBUG
    if (verbose > 0):
        return logging.INFO
    return logging.WARNING

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
    sys.exit(0)
