#!/usr/bin/env python

import datetime
import argparse
import sys

from dmx.minarclib.get_new_dbh import get_new_dbh
from dmx.minarclib.parse_audit_files import atomic_parse
from dmx.minarclib.populate_workspaces import atomic_sync

def main(project):

    dbh = get_new_dbh()
    cursor = dbh.cursor()

    cursor.execute("""
        SELECT project_id
        FROM project
        WHERE project_name = %s
    """, (project,))
    dbh.commit()

    if not cursor.rowcount:
        raise Exception("ERROR: project name " + project + " does not exist")

    project_id = cursor.fetchone()[0]
 
    cursor.execute("""
        SELECT i.ip_name, ms.ms_name, r.rel_id
        FROM Rel r
        LEFT JOIN IP i ON i.ip_id = r.ip_id
        LEFT JOIN ms ON ms.ms_id = r.ms_id
        WHERE (
            r.is_synced IS NULL 
            -- OR is_synced = 0
        )
        AND r.ms_id != 3
        AND r.is_parsed IS NULL
        AND i.project_id = %s
        ORDER BY r.rel_id DESC
    """, (project_id))

    # lock up the rels to prevent race condition between cronjobs
    #
    # TODO: there is still a use case where cron x SELECTS while cron y
    #       UPDATES. It may be necessary to implement a lock if the data
    #       gets duplicated.
    rows = cursor.fetchall()
    for row in rows: 
        cursor.execute("""
            UPDATE Rel
            SET is_synced = 0
            WHERE rel_id = %s
        """, (row[2],))
        dbh.commit()

    for row in rows:
        try: 
            atomic_sync(str(row[2]))
            atomic_parse(row[0], row[1], rel_id=int(row[2]), preserve_workspace=False)
        except Exception as e:
            sys.stderr.write('couldn\'t parse ' + str(row[2]))
            sys.stderr.write(str(e))
            continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--project', type=str, dest='project', action='store', required=True, help='Project name in ICM (ex: i10socfm, gdr, ...)')
    args = parser.parse_args()

    main(args.project)
