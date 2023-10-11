import MySQLdb

def get_new_dbh():
    return MySQLdb.connect(
        host='sjdmxweb01.sc.intel.com', 
        user='admin', passwd='mY5Q1@dm', 
        db='Min_ARC_Resource'
    )
