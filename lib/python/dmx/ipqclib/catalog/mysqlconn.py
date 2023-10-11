#!/usr/bin/env python
"""MySQL connection information"""
import MySQLdb
import MySQLdb.cursors

def mysql_connection():
    """Information to establish MySQL connection."""
    mydb = MySQLdb.connect( \
      host="scypsgdmxweb01.sc.intel.com", \
      user="ipqc", \
      passwd="ip_quality_control", \
      db='ipqc', \
      cursorclass=MySQLdb.cursors.DictCursor \
    )

    return mydb
