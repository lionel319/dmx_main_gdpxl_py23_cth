#!/usr/bin/env python
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/tnrlib/servers.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $
"""
The Servers class hosts a bunch of static server names,
URLs, port, etc. used by the various qa classes/tools.  
This is the place to reference all external systems so
there are not duplicated across various modules.

They come in several flavors:

  DEV servers are used by developers in the local workspaces
      these should never be used in code in an ARC resource

  INTEG servers are used by integration tests
        these should ONLY be specified inside integration tests

  TEST servers are used by beta testers on pre-release code
       these can be used by ARC resources that are not part
       of a user bundle like project/nadder

  PROD servers are production servers used by the general population
       these are the only kind of servers usable by ARC
       resources that are part of a bundle like project/nadder

Kirk Martinez
June 12, 2014
"""

class Servers(object):
    """
    Master list of servers the icd_cad_qa scripts connect to.
    """
    WEB_DEV_SERVER   = 'sj-kmartine-l2.altera.com:8899'
    WEB_TEST_SERVER   = 'sj-kmartine-l2.altera.com:8899'
    #WEB_TEST_SERVER  = 'sj-webdev1.altera.com:80'
    WEB_INTEG_SERVER = 'sj-webdev1.altera.com:80'
    WEB_PROD_SERVER  = 'sw-web.altera.com:80'

    # These point to the Splunk REST API port (ssl on 8089, not the 8001 http port)
    SPLUNK_DEV_URL   = 'https://sj-kmartine-l2.altera.com:8089'
    # Ideally, this, but we don't have real LDAP creds in the code...
    #SPLUNK_TEST_URL  = 'https://dashboard-dev.altera.com:8294'
    SPLUNK_TEST_URL = 'https://sj-kmartine-l2.altera.com:8089'
    SPLUNK_INTEG_URL = 'https://sj-kmartine-l2.altera.com:8089'
    SPLUNK_PROD_HOST = 'dashboard.altera.com'
    SPLUNK_PROD_PORT = 8090
    SPLUNK_PROD_URL  = 'https://'+SPLUNK_PROD_HOST+':'+str(SPLUNK_PROD_PORT)

    # These are the Splunk web GUI 
    SPLUNK_DEV_UI_URL = 'http://sj-kmartine-l2.altera.com:8001'
    SPLUNK_PROD_UI_URL = 'http://dashboard.altera.com:8080'

    RABBITMQ_SERVER = 'sj-ice-rmq'
    RABBITMQ_USER   = 'tnruser'
    RABBITMQ_PASS   = 'TestBeforeRelease'

    RABBITMQ_MGMT_SERVER = 'sj-ice-rmq:15672'


