#!/usr/bin/env python

# package to install python3-pytz python3-mysqlclient
# zypper -n install python3-pytz python3-mysqlclient

# apply as cron as user icmanage
# copy to  /opt/icmanage/bin/mysql_lock_mon.py3
# touch /opt/icmanage/log/mysql_lock_mon.log
#
# crontab -e
# # mysql lock mon
# */2 * * * * /opt/icmanage/bin/mysql_lock_mon.py3 --host <target hose --user icmAdmin >> /opt/icmanage/log/mysql_lock_mon.log 2>&1
#

import argparse
import logging
import MySQLdb
import os
import sys
import datetime

from pytz import reference
localtime = reference.LocalTimezone()

def main():
    version="1.2.0"
    parser = argparse.ArgumentParser(description="MySQL innodb lock monitor")

    parser.add_argument('--host',metavar="hostname",default=None,help="Target database host. If not given, localhost will be used.",dest="dbhost")
    parser.add_argument('--user',metavar="username",default="icmAdmin",help="mysql user with process privileges.  If empty default to 'icmAdmin'",dest="dbuser")
    parser.add_argument('--pass',metavar="password file",default=None,help="path to file that contains password.  If not specify, default password will be used.",dest="passfile")
    parser.add_argument("--debug",action="store_true",dest="debug",help="Turn on debug output")
    parser.add_argument('--logfile',metavar="FILE",default=None,help="Send debug output to file instead of stderr",dest="logfile")
    parser.add_argument('--version', default=False, action="store_true", help="print the version and exit",dest="version")

    options = parser.parse_args()

    dbhost=options.dbhost
    dbuser = options.dbuser
    dbpass = 'icmAdmin'

    # parsing version
    if options.version:
        print ("version: {}".format(version))
        sys.exit(0)

    # parsing password
    if options.passfile:
        passwordfile=options.passfile
        if os.path.exists(passwordfile):
            dbpass=open(passwordfile,'r').read().strip()
        else:
            print("Error: Bad password file '{}'".format(passwordfile))
            sys.exit(1)

    # parsing debug
    if options.debug:
        logging.basicConfig(filename=options.logfile,format='%(asctime)s [%(lineno)s] %(levelname)s %(message)s',
                            level=logging.DEBUG)
        logging.debug("Debug logging turned on")
        logging.debug( "%s %s" % (os.path.basename(__file__), version ))
    else:
        logging.basicConfig(filename=options.logfile,format='%(asctime)s %(levelname)s %(message)s',
                            level=logging.WARNING)

    # If --host is None, use the value in $P4PORT
    if not dbhost:
        dbhost, dbport = os.getenv("P4PORT").split(":")
        

    try:
        con=MySQLdb.connect(dbhost, dbuser, dbpass)
    except MySQLdb.OperationalError as e:
        print(repr(e))
        print("Failed to connect to server '{}' with user '{}' and password '{}'".format(dbhost, dbuser, dbpass))
        sys.exit(1)

    cur=con.cursor()

    doquery(cur,"select user()")
    results=cur.fetchall()
    logging.debug(results)

    doquery(cur,"show grants")
    results=cur.fetchall()
    logging.debug(results)

    # get the blocker and blocked threads
    blocker_trx_id=get_blocker_trx_id(cur)
    blocked_trx_id=get_blocked_trx_id(cur)

    # cur time
    now = datetime.datetime.now()
    dt = now.strftime("%d/%m/%Y %H:%M:%S " + localtime.tzname(now))

    # count the results
    blocker_count=len(blocker_trx_id)
    blocked_count=len(blocked_trx_id)

    if blocked_count == 0 and blocker_count == 0:
        # print("{}: No locking threads found.".format(dt))
        exit(0)

    # Output and exit
    now=datetime.datetime.now()
    dt=now.strftime("%d/%m/%Y %H:%M:%S " + localtime.tzname(now))
    print("################## There are waiting/blocking thread #################")
    print("Date time: {}".format(dt))

    if blocker_count == 0:
        print("There is no blocker thread.")
    else:
        for trx in blocker_trx_id:
            print("== blocker: ==")
            blocker_thread_id=get_thread_id(cur,trx)
            logging.debug("trx: %s thread: %s" % (trx, blocker_thread_id))
            print_thread_info(cur,blocker_thread_id)

    if blocked_count == 0:
        print("There is no thread being blocked.")
    else:
        for trx in blocked_trx_id:
            print("== blocked: ==")
            thread_id=get_thread_id(cur,trx)
            logging.debug("trx: blocked %s thread: %s" % (trx, thread_id))
            print_thread_info(cur,thread_id)

    con.close()


def print_thread_info(cur, thread_id):
    doquery(cur,"use information_schema")
    doquery(cur,"select user, host, time, command, info, state, progress from PROCESSLIST where id=\"%s\"" % thread_id)
    results=cur.fetchone()
    logging.debug(results)
    print("------------")
    print("BLOCKER INFO")
    print("------------")
    print("thread:  %s" % thread_id)
    print("user:    %s" % results[0])
    print("host:    %s" % results[1])
    print("time:    %s" % results[2])
    print("command: %s" % results[3])
    print("info:    %s" % results[4])
    print("state:    %s" % results[5])
    print("progress:    %s" % results[6])

def htime(sec):
    return str(datetime.timedelta(seconds=sec))

def get_thread_id(cur,trx):
    doquery(cur,"use information_schema")
    doquery(cur,"select trx_mysql_thread_id from innodb_trx where trx_id=\"%s\"" % trx)
    results=cur.fetchone()
    logging.debug(results)
    return results[0]


def get_blocker_trx_id(cur):
    doquery(cur,"use information_schema")
    doquery(cur,"select requesting_trx_id, blocking_trx_id from innodb_lock_waits")
    results=cur.fetchall()
    logging.debug(results)
    blockers=set([r[1] for r in results])
    blocked=set([r[0] for r in results])
    logging.debug("blockers: %s" % blockers)
    logging.debug("blocked: %s" % blocked)
    return tuple(blockers.difference(blocked))

def get_blocked_trx_id(cur):
    doquery(cur,"use information_schema")
    doquery(cur,"select requesting_trx_id from innodb_lock_waits")
    results=cur.fetchall()
    blocked=set([r[0] for r in results])
    return tuple(blocked)

def doquery(cur,stmt,role="SQL"):
    logging.debug("%s: %s" % (role,stmt));
    cur.execute(stmt)


if __name__ == '__main__':
  main()


