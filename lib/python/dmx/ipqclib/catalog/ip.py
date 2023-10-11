#!/usr/bin/env python
"""IP object for catalog"""
from dmx.ipqclib.catalog.mysqlconn import mysql_connection

class IP(object):
    """
    IP object class

    Attributes:
        family (str): The family name. Ex: FALCON.
        ipname (str): IP name.
        releases (tuple): list of releases in release DB
        ipqc_releases (tuple): list of releases in release catalog DB
    """
    def __init__(self, family, ipname):
        """
        The constructor for IP class.

        Parameters:
            family (str): The family name. Ex: FALCON.
            ipname (str): IP name.
            releases (tuple): list of releases in release DB
            ipqc_releases (tuple): list of releases in release catalog DB
        """
        self._family = family
        self._ipname = ipname
        (self._releases, self._ipqc_releases) = self._get_releases()


    def _get_releases(self):
        """Get releases from release DB and release_catalog DB"""
        mydb = mysql_connection()
        mycursor = mydb.cursor()

        mycursor.execute('SELECT * FROM releases WHERE family_name="{}" AND ip_name="{}"' \
                .format(self._family, self._ipname))
        releases = mycursor.fetchall()
        releases = [release["release_name"] for release in releases]

        mycursor.execute('SELECT * FROM release_catalog WHERE family_name="{}" AND ip_name="{}"' \
                .format(self._family, self._ipname))
        ipqc_releases = mycursor.fetchall()
        ipqc_releases = [release["release_name"] for release in ipqc_releases]

        return (releases, ipqc_releases)


    @property
    def name(self):
        """name property"""
        return self._ipname

    @property
    def releases(self):
        """releases property"""
        return self._releases

    @property
    def ipqc_releases(self):
        """ipqc_releases property"""
        return self._ipqc_releases
