#!/usr/bin/env python

"""
Base class of interacting with TeamCity.
Input and Output to the rest api is in XML format.

Explanation:-
-------------
- username/password OR token needs to be given.
  > username/password is user's userid/password
  > if use token(recommanded) instead, token can be generated (refer below on 'token generation' section)
- by default, the returned output format is 'xml'
  > other options: json


Example:-
---------
from dmx.utillib.teamcity_base_api import TeamcityBaseApi
from pprint import pprint
import json

a = TeamcityBaseApi(token='abcd1234xxxx', output_format='json')
ret = a.get_projects()
print a.prettyformat(ret)


Token Generation
----------------
- open up your Teamcity page
- click at your username link at the top right
- click at 'Access Token' at the left panel
- click 'Create access token'

"""
from __future__ import print_function

from builtins import str
import sys
import os
import logging
import xml.etree.ElementTree as ET
import xml.dom.minidom
import json
from pprint import pprint, pformat
import re
import datetime
import tempfile

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, ROOTDIR)


LOGGER = logging.getLogger(__name__)

def FactoryCicqApi(project, ip, thread, dryrun=False):
    if is_cicq_platform_jenkins():
        import dmx.utillib.jenkins_cicq_api
        return dmx.utillib.jenkins_cicq_api.JenkinsCicqApi(project, ip, thread)
    else:
        import dmx.utillib.teamcity_cicq_api
        return dmx.utillib.teamcity_cicq_api.TeamcityCicqApi(project, ip, thread, dryrun=dryrun)

def is_cicq_platform_jenkins():
    val = os.getenv("CICQ_PLATFORM", "")
    if val in ("jenkins", "JENKINS", "jenkin", "JENKIN"):
        return True
    return False

if __name__ == '__main__':
    logging.basicConfig(format='-%(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)

