#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/dmxapicmdlineutils.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: 
    Class that interact with /bin/dmx_api_cmdline.py

'''
from __future__ import print_function

import os
import logging
import sys
import json
import re

LOGGER = logging.getLogger(__name__)


sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
import dmx.ecolib.ecosphere
from dmx.utillib.utils import run_command
import dmx.abnrlib.config_factory

OUTPUT_LINE_PREFIX = 'DMXAPIJSON: '


def print_output(jsonstring):
    outstr = "{}{}".format(OUTPUT_LINE_PREFIX, json.dumps(jsonstring))
    print(outstr)
    return outstr


def parse_output_to_dict(outputstring):
    LOGGER.debug("outputstring: =={}==".format(outputstring))
    m = re.search(".*{}(.*)$".format(OUTPUT_LINE_PREFIX), outputstring, re.MULTILINE)
    if m:
        jsonobj = json.loads(m.group(1))
    else:
        jsonobj = json.loads('""')
    return jsonobj


