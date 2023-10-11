#!/usr/bin/env python

import datetime
import json
import subprocess
import unittest
import os
import shutil

from dmx.dmxlib.workspace import Workspace

from dmx.minarclib.get_new_dbh import get_new_dbh
from dmx.minarclib.populate_workspaces import atomic_sync
from dmx.minarclib.parse_audit_files import atomic_parse

class TestAuditParse(unittest.TestCase):

    def test_outputs(self):

        for rel_id in range(1417,1418):
            atomic_sync(rel_id)

            dbh = get_new_dbh()            
            cursor = dbh.cursor()
            cursor.execute("""
                SELECT rel_id, workspace_location, ip_name, ms.ms_name
                FROM Rel
                JOIN IP ON Rel.ip_id = IP.ip_id
                JOIN ms ON ms.ms_id = Rel.ms_id
                WHERE rel_id = %s
            """, (rel_id,))
            row = cursor.fetchone()
            
            atomic_parse(row[2], row[3], row[0], preserve_workspace=True)
            errors = compare_output(row[0], row[1], row[2])

            self.assertEqual(errors, 0)

def compare_output(rel_id, workspace_location, ip_name):

    errors = 0
    
    # move to the workspace location so the min_arc_checker can run
    os.chdir(workspace_location)

    # create a workspace so we can delete it later
    workspace = Workspace()

    # run min_arc_checker. Do to the architecture of that module, the
    # file can't be imported directly through python and must be inited
    # via the shell
    subprocess.check_output([
        '/p/psg/flows/common/dmx/main/bin/min_arc_checker.py',
        '-v', ip_name,
        '-output', 'legacy_output'
    ])

    # extract the relevant data and make it match the structure of current
    # database. Important pieces are missing in the LEGACY data but this is an 
    # ok sanity check. More has been added in the second iteration
    with open('legacy_output') as f:
        legacy_output = json.load(f)

    for empty, deliverables in legacy_output.items():
        for deliverable, checkers in deliverables.items():
            for audit, checker in checkers.items():
                cell = audit.split('.')[1]

                if not checker['flow'] and not checker['subflow']:
                    continue

                some_sql = ''
                if audit.endswith('.f'):
                    some_sql = """
                        JOIN audit_list al
                        ON c.checker_id = al.checker_id
                        WHERE audit_list_name LIKE %s
                    """
                else:
                    some_sql = """
                        JOIN audit a 
                        ON c.checker_id = a.checker_id
                        WHERE audit_name LIKE %s
                    """

                dbh = get_new_dbh()
                cursor = dbh.cursor()
                cursor.execute("""
                    SELECT c.checker_id FROM checker c
                    JOIN deliverable d ON c.del_id = d.del_id
                    JOIN cell cl ON c.cell_id = cl.cell_id
                    """ + some_sql + """
                    AND del_name = %s
                    AND d.rel_id = %s
                    AND cell_name = %s
                    AND flow = %s
                    AND subflow = %s
                """, (
                        audit,
                        deliverable, 
                        rel_id,
                        cell,
                        checker['flow'],
                        checker['subflow']
                    )
                )

                if cursor.rowcount == 0:
                    print '[ERROR]: checker not found'
                    print 'flow='+checker['flow']+';subflow='+checker['subflow']\
                        + ';rel_id='+str(rel_id)+';del='+str(deliverable)+';cell='+str(cell)
                    errors+= 1
                    continue
                elif cursor.rowcount > 1:
                    print '[ERROR], duplicate checkers'
                    print cursor.fetchall()
                    errors+= 1
                    continue

                checker_id = cursor.fetchone()[0]
                for resource, version_info in checker.items():
                    if resource == 'flow' or resource == 'subflow':
                        continue

                    dbh = get_new_dbh()
                    cursor = dbh.cursor()
                    cursor.execute("""
                        SELECT used_ver, critical_version, min_version, status
                         FROM resource_used
                        WHERE checker_id = %s
                        AND resource_name = %s
                    """, (
                            checker_id,
                            resource
                        )
                    )
                    if cursor.rowcount == 0:
                        print '[ERROR]: resource not found'
                        print 'res_name='+resource+';check_id='+str(checker_id)
                        print 'at '+audit
                        errors+= 1
                        continue
                    elif cursor.rowcount > 1:
                        print '[ERROR], duplicate resources'
                        print cursor.fetchall()
                        errors+= 1
                        continue

                    row = cursor.fetchone()
                    if row[0] != version_info['used']:
                        print '[ERROR]: mismatched used resource'
                        print 'res_name='+resource+';check_id='+str(checker_id)
                        print 'at '+audit
                        errors+= 1
                    
                    if row[1] != version_info['minimum']:
                        print '[ERROR]: mismatched minimum resource'
                        print 'res_name='+resource+';check_id='+str(checker_id)
                        print 'at '+audit
                        errors+= 1
                    
                    if row[2] != version_info['last_important']:
                        print '[ERROR]: mismatched critical resource'
                        print 'res_name='+resource+';check_id='+str(checker_id)
                        print 'at '+audit
                        errors+= 1
                    
                    if row[3] != version_info['result']:
                        print '[ERROR]: mismatched status'
                        print 'res_name='+resource+';check_id='+str(checker_id)
                        print 'at '+audit
                        errors+= 1

    # clean up the test area to save space
    workspace.delete()
    shutil.rmtree(workspace_location)

    return errors
        
if __name__ == '__main__':
    unittest.main()

