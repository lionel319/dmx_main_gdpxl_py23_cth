#!/usr/bin/env python

import os
import sys
from pprint import pprint
import json
import logging
sys.path.insert(0, '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/dmx/main/lib/python')
import dmx.utillib.teamcity_base_api

logger = logging.getLogger()
logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)


def main():
    frm = 22
    to = 100

    a = dmx.utillib.teamcity_base_api.TeamcityBaseApi(
            host='https://teamcity01-fm.devtools.intel.com',
            token = 'eyJ0eXAiOiAiVENWMiJ9.QzBvMk9hUEZFci1XZUllRXNxVnlXcV92U2xJ.ZjhlYzE0M2YtZjk2Ny00MTgzLWJkZjUtMGFlN2I5MGI1ZDNk',   # psgcicq_tc's token
            output_format = 'json',
    )

    i = frm
    while i<=to:
        name = 'psgcicq_psginfraadm_{}'.format(i)
        templateid = 'PsgCicq_AgentRefresh_AgentRefreshTemplate'
        btid = 'PsgCicq_AgentRefresh_PsgcicqPsginfraadm{}'.format(i)
        projid = 'PsgCicq_AgentRefresh'

        a.add_buildtype(name, btid, projid)
        a.attach_template_to_buildtype(templateid, btid)
        a.set_parameter_for_buildtype(btid, 'ARC_CICQ', 'aa')
        a.set_parameter_for_buildtype(btid, 'ARC_DMX_OVERLOAD', 'aa')
        a.add_agent_requirement_for_buildtype(btid, name)

        i = i + 1

if __name__ == '__main__':
    main()
