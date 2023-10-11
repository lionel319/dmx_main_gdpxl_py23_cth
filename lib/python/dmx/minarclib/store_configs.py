#!/usr/bin/env python

from __future__ import print_function
from builtins import str
from datetime import date
import MySQLdb
import subprocess

from dmx.abnrlib.icm import ICManageCLI
from dmx.ipqclib.ipqc import IPQC

from dmx.minarclib.get_new_dbh import get_new_dbh

def store_configs(project_name):
    dbh = get_new_dbh()
    cursor = dbh.cursor()
    cursor.execute("""
        SELECT project_name, IP.project_id, ip_name, ip_id
        FROM IP
        JOIN project ON project.project_id = IP.project_id
        WHERE project_name = %s
    """, (project_name,))
    
    for row in cursor.fetchall():
        store_releases(row[0], row[1], row[2], row[3])
  
def store_releases(project_name, project_id, ip_name, ip_id):
    
    today = date.today()
    d = today.isocalendar()
    
    # parse the year, month and date
    year = str(d[0])[2:]
    month = ''
    if d[1] < 10:
        month = '0' + str(d[1])
    else:
        month = str(d[1])
    day = today.weekday()

    regex = 'REL*{}ww{}{}*'.format(year, month, day)
    search_regex(project_name, project_id, ip_name, ip_id, regex)
    
def search_regex(project_name, project_id, ip_name, ip_id, regex):
    output = None
    try:
        output = subprocess.check_output([
            'dmx', 'report', 'list', 
            '-i', ip_name, 
            '-p', project_name,
            '-b', regex 
        ])
    except CalledProcessError as e:
        print(e)
       
    rels = output.strip().split('\n')[1:-1]

    # initialize cursor here instead of a new one for each rel.
    # fortunately the dmx report doesn't take longer than a 
    # minute so we don't have to create a new connection every
    # time.
    dbh = get_new_dbh()
    cursor = dbh.cursor()

    for rel in rels:
   
        print(rel + ' is new') 
        # parse the rels into [project, ip, release]
        x = rel.split('/', 1)
        project = x[0]
        ip = x[1].split('@',)[0]
        release = x[1].split('@')[1] 
 
        # check if today's rel has already been imported
        cursor.execute("""
            SELECT Rel.rel_id
            FROM Rel 
            JOIN IP ON Rel.ip_id = IP.ip_id
            JOIN project ON IP.project_id = project.project_id
            WHERE rel_name = %s
            AND ip_name = %s
            AND project.project_id = %s
        """, (release, ip, project_id))

        # skip if the release has been imported
        if cursor.fetchone():
            print('this rel has already been imported')
            continue

        # extract the milestone id from the release name
        #
        # TODO: are there any cases where the milestone may be in a 
        #       different format than RELX.X? for now we'll just do a
        #       sanity check and table it for later
        milestone = release[3:6]
        cursor.execute("""
            SELECT ms_id
            FROM ms
            WHERE ms_name = %s
        """, (milestone,))
        ms_id = cursor.fetchone()

        # here's the lazy sanity check for now
        if not ms_id:
            print('something went wrong when looking for milestones')
            return
        
        ms_id = ms_id[0]

        # extract the family from the relase as well
        if project_name == 'i10socfm':
            cursor.execute("""
                SELECT family_id
                FROM family
                WHERE family_name = %s
            """, (release[6:14],))
        else:
            cursor.execute("""
                SELECT family_id
                FROM family
                WHERE family_name = %s
            """, (release[6:9],))
            
        if not cursor.rowcount:
            print('can\'t find family')
            return

        family_id = cursor.fetchone()[0]
 
        print((release, ip_id, ms_id))
        # import if needed
        cursor.execute("""
            INSERT INTO Rel
            SET rel_name = %s, 
            ip_id = %s,
            ms_id = %s,
            family_id = %s
        """, (release, int(ip_id), int(ms_id), int(family_id)))
        dbh.commit()
