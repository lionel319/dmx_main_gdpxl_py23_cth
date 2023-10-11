#!/usr/bin/env python

from dmx.minarclib.get_new_dbh import get_new_dbh
from dmx.minarclib.store_configs import search_regex

dbh = get_new_dbh()
cursor = dbh.cursor()
cursor.execute("""
    SELECT project_name, IP.project_id, ip_name, ip_id
    FROM IP
    JOIN project ON project.project_id = IP.project_id
    WHERE project_name = %s
""", ('i10socfm',))

#TODO: handle ww 39 d3-6
for row in cursor.fetchall():
    for i in range (40, 45):
        for j in range(0,7):
            search_regex(row[0], row[1], row[2], row[3], 'REL*19ww{}{}*'.format(i, j))
