#!/usr/bin/env python
"""Catalog object containing various method to query/update information from dmxwebserver"""
from __future__ import print_function
import os
import re
import glob
import collections
import MySQLdb
from dmx.ecolib.ecosphere import EcoSphere
from dmx.ipqclib.settings import _BCC
from dmx.ipqclib.utils import get_ipqc_info, run_command
from dmx.ipqclib.catalog.utils import get_variants, get_releases_for_variant, \
         extract_info_from_release_name
from dmx.ipqclib.log import uiInfo, uiError, uiWarning, uiDebug
from dmx.ipqclib.catalog.mysqlconn import mysql_connection
from dmx.ipqclib.catalog.fullchip import FullChip

_FULLCHIP = 'Fullchip'
_SUBSYSTEM = 'Subsystem'
_IP = 'IP'

def _get_release_per_milestone(product, db_releases, ip): # pylint: disable=invalid-name

    list_of_release = collections.OrderedDict()
    pattern = r'\S+{}\S+__(\S+)' .format(product.name)

    for milestone in product.get_milestones():
        releases = {}
#            path = os.path.join(ipqc_path, 'dashboard', ip, milestone.name, 'rel')

        ip_releases = [r for r in db_releases if (r["ip_name"] == ip) and \
                        (r["milestone"] == milestone.name) and \
                        (r["device_name"] == product.name)]

        if ip_releases == []:
            continue

        for release in [i['release_name'] for i in ip_releases]:
            match = re.search(pattern, release)
            if match:
                releases[release] = match.group(1)

        for i, suffix in sorted(releases.items(), key=lambda x: x[1], reverse=True): # pylint: disable=unused-variable
            list_of_release[i] = os.path.join(ip, milestone.name, 'rel', i)

    return list_of_release


class Catalog(object):
    """
    IPQC release catalog class

    Attributes:
        family (str): The family name. Ex: FALCON.
        ips (list): List of IP names.
    """
    def __init__(self, family, ips=None):
        """
        The constructor for Catalog class.

        Parameters:
            family (str): The family name. Ex: FALCON.
            ips (list): List of IP names.
        """
        self._family = family

        try:
            self._ips = self.get_ips(ips)
        except AssertionError as error:
            raise AssertionError(error)

        self._products = EcoSphere().get_family(self._family).get_products()
        self._projects = [project.name for project in EcoSphere().get_family(self._family).get_icmprojects()] # pylint: disable=line-too-long
        self._ipqc_info = get_ipqc_info(self._family)

    def get_ips(self, ips):
        """Return the list of IPs for the given family."""
        list_of_ips = [ip.name for ip in EcoSphere().get_family(self._family).get_ips()]

        # pylint: disable=invalid-name
        for ip in ips:
            assert (ip in list_of_ips), "{} is not a valid IP" .format(ip)
        # pylint: enable=invalid-name

        return ips


    def get_missing_releases_db(self, project, ipname, releases):
        """
            Compare lists of ICM releases and DB releases
            Return an empty list if no missing ICM releases in DB releases.
            Then return the list of ICM releases missing in DB releases.
        """
        mydb = mysql_connection()
        mycursor = mydb.cursor()

        query_cmd = 'SELECT * FROM releases WHERE family_name="{}" AND project_name="{}" AND ip_name="{}"' .format(self._family, project, ipname) # pylint: disable=line-too-long
        mycursor.execute(query_cmd)
        db_releases = mycursor.fetchall()
        db_releases = [release["release_name"] for release in db_releases]

        return list(set(releases) - set(db_releases))


    def update_releases_db_for_variant(self, ipname, project, releases, preview=False):
        """
            Update releases table for the given project and given IP with the missing releases.
        """
        mydb = mysql_connection()
        mycursor = mydb.cursor()
        i = 0

        for release in releases:

            try:
                uiInfo("Updating {}@{} in releases DB" .format(ipname, release))
                i = i + 1

                if preview:
                    continue

                (milestone, device, revision) = extract_info_from_release_name(release)
                mycursor.execute('''INSERT INTO
                        releases(family_name,project_name,device_name,ip_name,release_name,milestone,revision)
                        VALUES("{}","{}","{}", "{}","{}","{}","{}")''' \
                        .format(self._family.upper(), project, device, ipname, release, milestone, revision)) # pylint: disable=line-too-long

            except MySQLdb.Error as err: # pylint: disable=c-extension-no-member
                uiError("Error while updating DB for {}@{}. {}" .format(ipname, release, err))

        #close out
        mydb.commit()
        mycursor.close()
        mydb.close()

        return i


    def update_releases_db(self, preview=False):
        """
            For each ICM project in family, get the list of variants.
            For each variant, get the list of releases.
            For each release check the release is stored in ipqc.releases table.
            If not in ipqc.releases table, update ipqc.releases table with the release.
            Else, do nothing since no update needed.
        """
        nb_releases = 0

        for project in self._projects:
            for variant in get_variants(project):
                releases = get_releases_for_variant(project, variant, self._products)
                missing_releases = self.get_missing_releases_db(project, variant, releases)

                if missing_releases == []:
                    continue

                nb_releases = nb_releases + self.update_releases_db_for_variant(variant, project, \
                        missing_releases, preview=preview)

        uiInfo("{} releases updates in ipqc.releases." .format(nb_releases))
        return

    def get_releases_from_db(self):
        """ Return releases available in release DB
                and releases in IPQC catalog.
        """
        mydb = mysql_connection()
        mycursor = mydb.cursor()

        release_db_query = 'SELECT * FROM releases WHERE family_name="{}"' .format(self._family)
        catalog_db_query = 'SELECT * FROM release_catalog WHERE family_name="{}"' .format(self._family) # pylint: disable=line-too-long

        if self._ips != []:
            ips = "('{}'" .format(str(self._ips[0]))

            # pylint: disable=invalid-name
            for ip in self._ips[1:]:
                ips = ips + ", '{}'" .format(str(ip))
            # pylint: enable=invalid-name
            ips = ips + ")"
            release_db_query = release_db_query + ' AND ip_name in {}' .format(ips)
            catalog_db_query = catalog_db_query + ' AND ip_name in {}' .format(ips)

        mycursor.execute(release_db_query)
        releases = mycursor.fetchall()

        mycursor.execute(catalog_db_query)
        ipqc_releases = mycursor.fetchall()

        return (releases, ipqc_releases)


    def get_missing_ipqc_releases(self):
        """
            Compare releases DB and release_catalog DB.
            Report all releases missing in release_catalog DB.
        """
        ok_releases = {}
        missing_releases = []
        mydb = mysql_connection()
        mycursor = mydb.cursor()

        mycursor.execute('SELECT * FROM releases WHERE family_name="{}"' .format(self._family))
        releases = mycursor.fetchall()

        mycursor.execute('SELECT * FROM release_catalog WHERE family_name="{}"' .format(self._family)) # pylint: disable=line-too-long
        ipqc_releases = mycursor.fetchall()

        for release in releases:

            for ipqc_release in ipqc_releases:

                if (ipqc_release["ip_name"] == release["ip_name"]) and \
                    (ipqc_release["release_name"] == release["release_name"]):

                    if ipqc_release["ip_name"] not in ok_releases.keys():
                        ok_releases[ipqc_release["ip_name"]] = [ipqc_release["release_name"]]

                    ok_releases[ipqc_release["ip_name"]].append(ipqc_release["release_name"])


        for release in releases:

            if release["ip_name"] not in ok_releases.keys():
                ok_releases[release["ip_name"]] = []
                missing_releases.append(release)


            if release["release_name"] not in ok_releases[release["ip_name"]]:
                missing_releases.append(release)

        return missing_releases


    def update_db_missing_ipqc_releases(self, preview=False):
        """ Update catalog_releases if the release is in release table but not in catalog_releases
            table.
        """
        missing_releases = self.get_missing_ipqc_releases()
        ipqc_path = self._ipqc_info["rel"]["path"]
        need_to_update = []

        for release in missing_releases:
            ipqc_releases = glob.glob(os.path.join(ipqc_path, 'dashboard', release["ip_name"], \
                        release["milestone"], 'rel/*'))
            for ipqc_release in ipqc_releases:
                ipqc_release = os.path.basename(os.path.normpath(ipqc_release))

                if ipqc_release == release["release_name"]:
                    need_to_update.append(release)

        if need_to_update == []:
            return

        mydb = mysql_connection()
        mycursor = mydb.cursor()

        for release in need_to_update:
            uiInfo("Updating {}@{} in release_catalog DB" .format(release["ip_name"], \
            release["release_name"]))

            if preview:
                continue

            # pylint: disable=line-too-long
            query_cmd = 'INSERT INTO release_catalog(family_name,ip_name,release_name) VALUES("{}","{}","{}")' \
                .format(release["family_name"], release["ip_name"], release["release_name"])
            # pylint: enable=line-too-long

            try:
                mycursor.execute(query_cmd)
            except MySQLdb.Error as err: # pylint: disable=c-extension-no-member
                uiError("Error while updating DB for {}@{}. {}" .format(release["ip_name"], \
                release["release_name"], err))

        #close out
        mydb.commit()
        mycursor.close()
        mydb.close()

#    def get_missing_ipqc_dashboard(self):
#        (releases, ipqc_releases) = self.get_releases_from_db()
#        ipqc_path = self._ipqc_info["rel"]["path"]
#        need_to_update = []
#        no_need_to_update = []
#
#        for release in releases:
#            ipqc_releases = glob.glob(os.path.join(ipqc_path, 'dashboard', release["ip_name"], \
#            release["milestone"], 'rel/*'))
#
#            if ipqc_releases == []:
#                need_to_update.append(release)
#                continue
#
#            for r in ipqc_releases:
#                r = os.path.basename(os.path.normpath(r))
#
#                if r == release["release_name"]:
#                    no_need_to_update.append(release)
#
#            if release not in no_need_to_update:
#                need_to_update.append(release)
#
#        if need_to_update != []:
#            uiWarning("Missing dashboards in {}" .format(ipqc_path))
#
#        return need_to_update

    def generate_dashboard(self, preview=False):
        """
        Check if releases in release catalog DB.
        Generate IPQC dashboard for missing releases.
        """
        missing_dashboards = self.get_missing_ipqc_releases()
        for missing in missing_dashboards:
            os.chdir(self._ipqc_info["WorkspaceArea"])
            # pylint: disable=line-too-long
            ipqc_cmd = 'ipqc dry-run -p {} -i {}@{} -m {} --output-format html --sendmail --log-file ipqc_{}_{}.log ' \
            .format(missing["project_name"], missing["ip_name"], missing["release_name"], missing["milestone"], \
            missing["ip_name"], missing["release_name"])
            # pylint: enable=line-too-long
            cmd = '{} || mail -s "IPQC dashboard generation  - FAILURE - {}" {}' \
            .format(ipqc_cmd, ipqc_cmd, _BCC[0])
            uiInfo("Running {}" .format(cmd))

            if preview:
                continue

            (code, out) = run_command(cmd)

            if code != 0:
                uiError("Error while generating dashboard: {}" .format(out))
            uiDebug(out)

        return

    def releases_db_equivalency_check(self):
        """
        Equivalency check between releases DB and releases catalog DB.
        """
        (releases, catalog_releases) = self.get_releases_from_db()
        if len(releases) != len(catalog_releases):
            uiInfo("Discrepency between releases in ICM ({}) and releases in Catalog ({})" \
            .format(len(releases), len(catalog_releases)))
            releases_name = [(release["ip_name"], release["release_name"]) for release in releases]
            catalog_releases_name = [(release["ip_name"], release["release_name"]) for release in catalog_releases] # pylint: disable=line-too-long
            missing_releases = list(set(catalog_releases_name).difference(releases_name))

            if missing_releases:
                uiWarning("Missing values in releases table: {}" .format(missing_releases))

            missing_catalog_releases = list(set(releases_name).difference(catalog_releases_name))

            if missing_catalog_releases:
                uiWarning("Missing values in releases catalog table: {}" \
                .format(missing_catalog_releases))
        else:
            return

    def get_last_released_fullchip(self, product, revision):
        """ The last full chip released serves as reference to set Fullchip, subsystem, IP type.
        """
        releases = []
        keys = []
        mydb = mysql_connection()
        mycursor = mydb.cursor()
        # pylint: disable=line-too-long
        mycursor.execute('SELECT * FROM releases WHERE ip_name LIKE "z%" AND family_name = "{}" AND device_name="{}" AND revision="{}"' \
                .format(self._family, product, revision))
        # pylint: enable=line-too-long


        for row in mycursor.fetchall():
            if re.search(r'^z[0-9][0-9][0-9][0-9]\w$', row['ip_name']):
                releases.append(row)
                keys.append(row['id'])

        uiDebug("Full chip releases are {}" .format(releases))

        if releases == []:
            return None

        last = max(keys)

        for release in releases:
            if int(release['id']) == int(last):
                return release

        return None

    def create_ip_category(self, last_fc_release, product, preview):
        """Based on the latest and greatest Fullchip release, set the IP categorey:
            --> Fullchip
            --> Subsystem
            --> IP
        """

        mydb = mysql_connection()
        mycursor = mydb.cursor()

        ipqc_catalog_settings_path = os.path.join(self._ipqc_info["rel"]['path'], 'settings')
        # pylint: disable=invalid-name
        fc = FullChip(last_fc_release["ip_name"], last_fc_release["project_name"], \
                last_fc_release["release_name"], product, ipqc_catalog_settings_path)
        # pylint: enable=invalid-name
        # pylint: disable=line-too-long
        query_cmd = 'INSERT INTO ip_category(ip_name, device_name, family_name, category, fc_release) VALUES("{}", "{}", "{}", "{}", "{}")' \
                    .format(fc.name, product, self._family, _FULLCHIP, fc.release)
        # pylint: enable=line-too-long
        uiInfo(query_cmd)

        if preview is False:
            mycursor = mydb.cursor()
            mycursor.execute(query_cmd)

        # pylint: disable=invalid-name
        for ip in fc.integration_ips:
            # pylint: disable=line-too-long
            query_cmd = 'INSERT INTO ip_category(ip_name, device_name, family_name, category, fc_release) VALUES("{}","{}","{}","{}","{}")' \
                        .format(ip, fc.device, self._family, _SUBSYSTEM, fc.release)
            # pylint: enable=line-too-long
            uiInfo(query_cmd)

            if preview is False:
                mycursor = mydb.cursor()
                mycursor.execute(query_cmd)
                mydb.commit()

        for ip in fc.ips:

            if ip in fc.integration_ips:
                continue

            # pylint: disable=line-too-long
            query_cmd = 'INSERT INTO ip_category(ip_name, device_name, family_name, category, fc_release) VALUES("{}","{}","{}","{}","{}")' \
                        .format(ip, fc.device, self._family, _IP, fc.release)
            # pylint: enable=line-too-long

            uiInfo(query_cmd)

            if preview is False:
                mycursor = mydb.cursor()
                mycursor.execute(query_cmd)
                mydb.commit()
        # pylint: enable=invalid-name

        #close out
        mycursor.close()
        mydb.close()

        return

    def update_ip_category(self, last_fc_release, product, preview):
        """Based on the latest and greatest Fullchip release, set the IP categorey:
            --> Fullchip
            --> Subsystem
            --> IP
        """
        mydb = mysql_connection()
        mycursor = mydb.cursor()

        ipqc_catalog_settings_path = os.path.join(self._ipqc_info["rel"]['path'], 'settings')
        # pylint: disable=invalid-name
        fc = FullChip(last_fc_release["ip_name"], last_fc_release["project_name"], \
                last_fc_release["release_name"], product, ipqc_catalog_settings_path)
        # pylint: enable=invalid-name
        # pylint: disable=line-too-long
        query_cmd = 'UPDATE ip_category SET category = "{}", fc_release="{}" WHERE family_name="{}" AND ip_name="{}" AND device_name="{}"' \
                    .format(_FULLCHIP, fc.release, self._family, fc.name, product)
        # pylint: enable=line-too-long
        uiInfo(query_cmd)

        if preview is False:
            mycursor = mydb.cursor()
            mycursor.execute(query_cmd)

        # pylint: disable=invalid-name
        for ip in fc.integration_ips:
            # pylint: disable=line-too-long
            query_cmd = 'UPDATE ip_category SET category = "{}", fc_release="{}" WHERE family_name="{}" AND ip_name="{}" AND device_name="{}"' \
                         .format(_SUBSYSTEM, fc.release, self._family, ip, fc.device)
            # pylint: enable=line-too-long
            uiInfo(query_cmd)

            if preview is False:
                mycursor = mydb.cursor()
                mycursor.execute(query_cmd)
                mydb.commit()

        for ip in fc.ips:

            if ip in fc.integration_ips:
                continue

            # pylint: disable=line-too-long
            query_cmd = 'UPDATE ip_category SET category = "{}", fc_release="{}" WHERE family_name="{}" AND ip_name="{}" AND device_name="{}"' \
                        .format(_IP, fc.release, self._family, ip, fc.device)
            # pylint: enable=line-too-long

            uiInfo(query_cmd)

            if preview is False:
                mycursor = mydb.cursor()
                mycursor.execute(query_cmd)
                mydb.commit()
        # pylint: enable=invalid-name

        #close out
        mycursor.close()
        mydb.close()

        return

    def _update_tmp_file_with_release_per_milestone(self, fid, list_of_release, product):
        for milestone in product.get_milestones():
            generate_menu_header = 0
            for release, path in list_of_release.items():

                pattern = "^REL" +milestone.name+product.name + r"\S*$"
                prel_pattern = "^PREL" +milestone.name+product.name+ r"\S*$"
                if re.search(pattern, release) or re.search(prel_pattern, release):

                    if generate_menu_header == 0:
                        # pylint: disable=line-too-long
                        print('<h6 class="dropdown-header" align="center" style="background-color:#3366FF; color:#FFFFFF; font-weight:bold">Milestone {}</h6>' .format(milestone.name), file=fid)
                        # pylint: enable=line-too-long
                        print('<div class="dropdown-divider"></div>', file=fid)
                        generate_menu_header = 1

                    htmlfile = os.path.join(path, 'ipqc.html')
                    print('<a class="dropdown-item" href="/{}_dashboards/{}">{}</a>' \
                            .format(self._family.lower(), htmlfile, release), file=fid)


    def _update_tmp_file(self, product, list_of_types, db_releases, filepath_tmp):

        list_of_ips = []
        keyorder = [_FULLCHIP, _SUBSYSTEM, _IP]

        with open(filepath_tmp, 'w+') as fid:
            print('{% block content %}', file=fid)
            print('<nav aria-label="breadcrumb"> \
                <ol class="breadcrumb"> \
                <li class="breadcrumb-item">{}</li> \
                <li class="breadcrumb-item active" aria-current="page">{} - REL</li> \
                </ol> \
            </nav>' .format(self._family, product.name), file=fid)
            print('<table style="width:100%; table-layout: fixed;">', file=fid)

            # Header table
            print('\t<tr style="background: #E0E0E0; font-size: 20px">', file=fid)
            for k, value in sorted(list_of_types.items(), key=lambda j: keyorder.index(j[0])):
                print('\t<th style="text-align:center">{}</th>' .format(k), file=fid)
            print('\t</tr>', file=fid)
            # End header table

            print('\t<tr>', file=fid)
            # Table filled with IPs
            for k, value in sorted(list_of_types.items(), key=lambda j: keyorder.index(j[0])):
                print('\t\t<td style="text-align:center; vertical-align:top">', file=fid)
                # pylint: disable=line-too-long
                # foreach IP, parse /p/psg/falcon/ipqc_rel/dashboard/<ip>/<milestone>/rel/<release_name>/ and display ipqc.html
                # pylint: enable=line-too-long
                # pylint: disable=invalid-name
                for ip in sorted(value):
                    if ip in list_of_ips:
                        continue

                    list_of_ips.append(ip)

                    # foreach milestone loop
                    list_of_release = _get_release_per_milestone(product, db_releases, ip)

                    if list_of_release == {}:
                        continue

                    print('<br>', file=fid)
                    print('<div class="btn-group dropright">', file=fid)
                    # pylint: disable=line-too-long
                    print('<button type="button" class="btn btn-secondary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" style="height:40px;min-width:200px; background: transparent; color: black; border: none">', file=fid)
                    # pylint: enable=line-too-long
                    print('{}' .format(ip), file=fid)
                    print('</button>', file=fid)
                    print('<div class="dropdown-menu">', file=fid)

                    self._update_tmp_file_with_release_per_milestone(fid, list_of_release, product)

                    print('</div>', file=fid)
                    print('</div>', file=fid)

                print('\t\t</td>', file=fid)
            print('\t</tr>', file=fid)

            print('</table>', file=fid)
            print('{% endblock %}', file=fid)

    def _get_releases_per_device_and_revision(self, product, revision):

        mydb = mysql_connection()
        mycursor = mydb.cursor()
        # pylint: disable=line-too-long
        query_cmd = 'SELECT * FROM releases WHERE family_name="{}" AND device_name="{}" AND revision="{}"' \
                    .format(self._family, product.name, revision.name)
        # pylint: enable=line-too-long
        mycursor.execute(query_cmd)
        db_releases = mycursor.fetchall()

        #close out
        mycursor.close()
        mydb.close()

        return db_releases

    def _get_ipqc_releases_per_family(self):

        mydb = mysql_connection()
        mycursor = mydb.cursor()
        query_cmd = 'SELECT * FROM release_catalog WHERE family_name="{}"' \
                    .format(self._family)
        mycursor.execute(query_cmd)
        ipqc_releases = mycursor.fetchall()

        #close out
        mycursor.close()
        mydb.close()

        return ipqc_releases

    def _get_fc_release(self, last_fc_release, product): #pylint: disable=no-self-use

        mydb = mysql_connection()
        mycursor = mydb.cursor()

        # pylint: disable=line-too-long
        query_cmd = 'SELECT * FROM ip_category WHERE ip_name="{}" AND device_name="{}" AND fc_release="{}"' \
                    .format(last_fc_release["ip_name"], product.name, \
                            last_fc_release["release_name"])
        # pylint: enable=line-too-long

        mycursor.execute(query_cmd)
        release = mycursor.fetchall()

        if release == ():
            # Check if FC release exists for the existing device
            mycursor = mydb.cursor()
            query_cmd = 'SELECT * FROM ip_category WHERE ip_name="{}" AND device_name="{}"' \
                        .format(last_fc_release["ip_name"], product.name)

            mycursor.execute(query_cmd)
            release = mycursor.fetchall()

        #close out
        mycursor.close()
        mydb.close()

        return release


    def _get_ip_types_for_fc(self, product, last_fc_release): #pylint: disable=no-self-use

        mydb = mysql_connection()
        mycursor = mydb.cursor()

        query_cmd = 'SELECT * FROM ip_category WHERE device_name="{}" AND fc_release="{}"' \
                            .format(product.name, last_fc_release["release_name"])
        mycursor.execute(query_cmd)
        ip_types = mycursor.fetchall()

        #close out
        mycursor.close()
        mydb.close()

        return ip_types



    def push_in_catalog(self, preview=False):
        """ Push the releases in the IPQC catalog HTML
        """
        for product in self._products:

            for revision in product.get_revisions():
                last_fc_release = self.get_last_released_fullchip(product.name, revision.name)
                list_of_types = {}

                # Get the list of IP in releases DB per device and revision
                db_releases = self._get_releases_per_device_and_revision(product, revision)

                # Get the list of IP in release catalog DB
                ipqc_releases = self._get_ipqc_releases_per_family()

                if last_fc_release is None:
                    list_of_types[_FULLCHIP] = []
                    list_of_types[_SUBSYSTEM] = []
                    list_of_types[_IP] = [d['ip_name'] for d in ipqc_releases]
                else:

                    release = self._get_fc_release(last_fc_release, product)

                    if release == ():
                        self.create_ip_category(last_fc_release, product.name, preview)
                    else:
                        self.update_ip_category(last_fc_release, product.name, preview)

                    # Get list of IP in IP category
                    ip_types = self._get_ip_types_for_fc(product, last_fc_release)

                    list_of_types[_FULLCHIP] = [d['ip_name'] for d in ip_types \
                                               if d["category"] == _FULLCHIP]
                    list_of_types[_SUBSYSTEM] = [d['ip_name'] for d in ip_types \
                                                if d["category"] == _SUBSYSTEM]
                    list_of_types[_IP] = [d['ip_name'] for d in ip_types if d["category"] == _IP]

                    for i in db_releases:
                        if not i["ip_name"] in list_of_types[_FULLCHIP] \
                            + list_of_types[_SUBSYSTEM] \
                            + list_of_types[_IP]:
                            list_of_types[_IP].append(i["ip_name"])

                ipqc_catalog_settings_path = os.path.join(self._ipqc_info["rel"]['path'], \
                        'settings')
                filepath = os.path.join(ipqc_catalog_settings_path, \
                        self._family.lower().capitalize() + '_' + product.name + \
                           revision.name + '.html')
                filepath_tmp = os.path.join(ipqc_catalog_settings_path, \
                        self._family.lower().capitalize() + '_' + product.name + \
                               revision.name + '.html_tmp')

                self._update_tmp_file(product, list_of_types, db_releases, filepath_tmp)
                os.system('cp -f {} {}' .format(filepath_tmp, filepath))
