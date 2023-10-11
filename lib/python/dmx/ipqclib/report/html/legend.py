#!/usr/bin/env python
""" legend.py - legend color and description"""

from __future__ import print_function
from dmx.ipqclib.settings import _PASSED, _FAILED, _FATAL, _FATAL_SYSTEM, _NA, \
        _WARNING, _UNNEEDED, _NA_MILESTONE, status_data

def legend(fid):
    """Legend color and description"""

    print('<table width="50%" style="font-family: arial, helvetica, sans-serif; padding-left: 10%; \
            text-align:left;">', file=fid)
    print('<tr><td style="background-color: {}; width:4%"></td><td>{}</td></tr>' \
            .format(status_data[_PASSED]['color'], status_data[_PASSED]['description']), file=fid)
    print('<tr><td style="background-color:{}"></td><td>{}</td></tr>' \
            .format(status_data[_WARNING]['color'], status_data[_WARNING]['description']), file=fid)
    print('<tr><td style="background-color:{}"></td><td>{}</td></tr>' \
            .format(status_data[_FAILED]['color'], status_data[_FAILED]['description']), file=fid)
    print('<tr><td style="background-color:{}"></td><td>{}</td></tr>' \
            .format(status_data[_FATAL]['color'], status_data[_FATAL]['description']), file=fid)
    print('<tr><td style="background-color:{}"></td><td>{}</td></tr>' \
            .format(status_data[_FATAL_SYSTEM]['color'], \
            status_data[_FATAL_SYSTEM]['description']), file=fid)
    print('<tr><td style="background-color:{}"></td><td>{}</td></tr>' \
            .format(status_data[_UNNEEDED]['color'], status_data[_UNNEEDED]['description']), \
            file=fid)
    print('<tr><td style="text-align: center; background-color:{}">{}</td><td>{}</td></tr>' \
            .format(status_data[_NA]['color'], _NA, status_data[_NA]['description']), file=fid)
    print('<tr><td style="background-color:{}"></td><td>{}</td></tr>' \
            .format(status_data[_NA_MILESTONE]['color'], \
            status_data[_NA_MILESTONE]['description']), file=fid)
    print('</table>', file=fid)
