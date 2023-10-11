#!/usr/bin/env python

import os
import sys
import tempfile

pinglist = [
    'teamcity01-fm.devtools.intel.com',
    'psg-sc-arc.sc.intel.com',
    'psg-png-arc.png.intel.com',
    'sw-web.altera.com',
    'ppgicm.png.intel.com',
    'sjicm.sc.intel.com',
    'sjicm02.sc.intel.com',
    'sjdacron.sc.intel.com',
    'sjcron02.sc.intel.com',
    'ppgdacron01.png.intel.com',
]

curllist = [
    'https://elkprdkibana1.intel.com:6601/',
    'https://sjdmxweb01.sc.intel.com/ddv_server/dmxdata/family',
    'http://dashboard.altera.com:8080',
]

pingcmd = 'ping -c1 -W5 {0} > /dev/null'
curlcmd = 'env -i curl -skm 5 {0} > /dev/null'

errors = []
errlist = []

def main():
    '''
    A lot of times, there were intermittent connection/network problems.
    These glithces causes a lot of false alarm in the notification.
    A stupid way to workaround this is to run the checking 3 times in a row.
    if it fails all 3 times, it probably means it has a high chance it is a REAL problem, and thus, 
    warrant a notification.
    '''
    global errors
    for i in range(5):
        errors = []
        checkping()
        checkcurl()
        errlist.append(set(errors[:]))

    for e in errlist:
        print e

    errors = set.intersection(*errlist)
    notify()

def checkping():
    for e in pinglist:
        report(e, pingcmd)

def checkcurl():
    for e in curllist:
        report(e, curlcmd)

def report(url, cmd):
    exe = cmd.format(url)
    exitcode = os.system(exe)
    if not exitcode:
        status = 'PASS'
    else:
        status = 'FAIL'
        errors.append(url)

    print '{0}: {1}'.format(status, url)
    if '--debug' in sys.argv:
        print '  {0}'.format(exe)

def notify():
    print '====== Sending Notification ====='
    if errors:
        tmpfile = tempfile.mkstemp()[1]
        with open(tmpfile, 'w') as f:
            f.write("Failing Hosts:\n")
            f.write('{0}'.format(errors))

        if '--nomail' not in sys.argv:
            os.system("cat {0} | mail -s 'heartbeat error' lionelta,jwquah,limty,cftham,kwli".format(tmpfile))

        errstr = 'Failing Hosts: {0}'.format(','.join(errors))
        send_telegram(errstr)

def send_telegram(errstr):
    makefile = os.path.join(os.path.dirname(__file__), 'telegram', 'Makefile')
    cmd = "make -f {0} send_message MSG='{1}'".format(makefile, errstr)
    print "PWD:{0}".format(os.getcwd())
    print "CMD:{0}".format(cmd)
    os.system(cmd)


if __name__ == '__main__':
    main()

