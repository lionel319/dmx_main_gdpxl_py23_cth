#!/usr/bin/env python
'''
This program opens up the splunk release dashboard of the give project/variant:libtype@config
'''
import os,sys
import logging
import urllib
import urlparse

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.tnrlib.dashboard_query2 import DashboardQuery2


logging.basicConfig(format="%(levelname)s [%(asctime)s]: %(message)s")
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)


def main():
    if len(sys.argv) < 5:
        print """
        USAGE:-
        =======
            ${} <project> <variant> <libtype> <config>

        """.format(sys.argv[0])
        return 0

    a = DashboardQuery2('guest', 'guest')
    rid = a.get_request_id_from_pvlc(*sys.argv[1:])
    url = 'http://dashboard.altera.com:8080/en-US/app/tnr/release_request_detail?form.request_id={}&earliest=0&latest='.format(rid)


    print "URL: {}".format(url)
    os.system("firefox '{}' &".format(url))


if __name__ == '__main__':
    sys.exit(main())
