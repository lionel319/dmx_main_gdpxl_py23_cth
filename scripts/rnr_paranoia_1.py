#!/usr/bin/env python

import os
import sys
from dmx.utillib.utils import run_command
from dmx.abnrlib.config_factory import ConfigFactory

def main():

    if '-h' in ' '.join(sys.argv):
        print """
        Usage:-
        -------
        {} <project> <variant> <config>
        """.format(sys.argv[0])
        return

    project, variant, config = sys.argv[1:4]
    print "{}/{}@{}".format(project, variant, config)

    for cf in ConfigFactory.create_from_icm(project, variant, config).flatten_tree():
        if cf.is_composite():
            continue

        p = cf.project
        v = cf.variant
        c = cf.config
        l = cf.libtype

        prefix = c[:14]
        exitcode, stdout, stderr = run_command("dmx bom latest -p {} -i {} -d {} -b '^{}' --limit 1".format(p, v, l, prefix))

        #print "exitcode:{}, stdout:{}, stderr:{}".format(exitcode, stdout, stderr)
        status = ''
        msg = '{}/{}:{}@{}'.format(p, v, l, c)
        latestconfig = stdout.strip()
        if latestconfig == c:
            status = 'PASS'
        else:
            status = 'FAIL'
            msg += ' - {}'.format(latestconfig)
        print "{}: {}".format(status, msg)


if __name__ == '__main__':
    sys.exit(main())
