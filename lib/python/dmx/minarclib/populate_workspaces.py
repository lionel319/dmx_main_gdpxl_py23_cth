import os

from dmx.ipqclib.workspace import Workspace
from dmx.ipqclib.ipqc import IPQC

from get_new_dbh import get_new_dbh
from logger import Logger

# TODO: confirm disk location to populate workspaces
#       decide on how to optimize audit generation. For now let's use IPQC

__WORK_LIB__ = '/nfs/site/disks/psg_dmx_1/ws'

def atomic_sync(rel_id): 
    cursor = get_new_dbh().cursor()
    cursor.execute("""
        SELECT IP.ip_name, Rel.rel_name, Rel.rel_id, p.project_name
        FROM Rel 
        JOIN IP ON Rel.ip_id = IP.ip_id 
        JOIN project p on p.project_id = IP.project_id
        WHERE Rel.rel_id = %s
    """, (rel_id,))
    row = cursor.fetchone()

    project = row[3]
    ip = row[0]
    release = row[1]
 
    os.chdir(__WORK_LIB__)
    dbh = get_new_dbh()
    cursor = dbh.cursor()
    
    # damage control for when syncing / mysql fails
    # however this query isn't necessary and the is_synced 
    # status can just be passed to this function
    cursor.execute("""
        SELECT is_synced, workspace_location 
        FROM Rel
        WHERE rel_id = %s
    """, (rel_id))
 
    # TODO: this is currently just resyncing the workspace.
    #       later some extra sanitation should be added for
    #       for other use cases where the sync fails. 
    workspace = Workspace(ip, bom=release)

    # set synced to 0 to show sync in progress
    # sometimes the sync takes to long, or fails to update.
    # also set the workspace location for bookkeeping
    dbh = get_new_dbh()
    dbh.cursor().execute("""
        UPDATE Rel 
        SET is_synced = 0,  
        workspace_location = %s     
        WHERE rel_id = %s
    """, (workspace._workspaceroot, rel_id))
    dbh.commit()

    # set synced to 1 to confirm that the sync was successful.
    # also just sync the ip in question.
    #
    # not just the audit files can be captured as we need to run
    # ipqc.dry_run() to get waived status.
    if not workspace.sync(specs = [
                '*/*/audit/...',
                '*/reldoc/...',
                '*/ipspec/...'
            ]
        ):

        dbh = get_new_dbh()
        dbh.cursor().execute("""
            UPDATE Rel 
            SET is_synced = 1 
            WHERE rel_id = %s
        """, (rel_id,))
        dbh.commit()

    else:
        pass
