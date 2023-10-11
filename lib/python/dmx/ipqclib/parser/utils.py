#!/usr/bin/env python
"""Utilities for IPQC parser"""
import os
import argparse
import dmx.ecolib.ecosphere
from dmx.ipqclib.utils import file_accessible, memoize
from dmx.ipqclib.settings import _TEMPLATE_LIST, _DB_THREAD, status_data

IP_DEMO = '''
        0   IPa
             |__________
             |          |
        1   IPb         IPc
             |
             |
        2   IPd
'''

_FILTER_OPTIONS = [values['option'] for values in status_data.values() if 'option' \
                in values.keys()]

def is_valid_file(arg):
    """Check argument is a valid file. Return file if valid else error."""
    if not file_accessible(arg, os.R_OK):
        raise argparse.ArgumentTypeError("{0} does not exist".format(arg))
    return os.path.realpath(arg)

def is_valid_template_value(arg):
    """Check template format is supported. Return error if not supported."""
    for i in _TEMPLATE_LIST:
        template = arg.rsplit("#")[0]
        if template == i:
            return arg

    raise argparse.ArgumentTypeError("{0} is invalid. Use {} value" .format(arg, _TEMPLATE_LIST))


@memoize
def get_deliverables():
    """Get deliverables function from Ecosphere"""
    family = dmx.ecolib.ecosphere.EcoSphere().get_family()
    deliverables = [deliverable.name for deliverable in family.get_all_deliverables()] + \
            [view.name for view in family.get_views()]

    return deliverables
