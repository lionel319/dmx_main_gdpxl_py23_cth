#! /usr/bin/env python

'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/py23comlib/arc_utils/1.7_py23/arc_orm/arc_orm.py#1 $

Definition for Class ArcORM - the object relational model for ARC.

This class provides object-oriented access to the SQL databases that
hold information for the ARC resources.
'''
from __future__ import print_function
from __future__ import absolute_import

from builtins import str
from builtins import object
import os
import sys
import time
from pprint import pprint

os.environ['DJANGO_SETTINGS_MODULE'] = 'arc_orm.arc_orm_settings'

from .models import Jobs, JobData, JobRequirements, JobResources, Resources, ResourceMap, ResourceData

from altera.decorators import memoized

class ArcOrmException(Exception):
    pass

def decompose_res_name(resource):
    '''Decompose the resource name into resource type and address
    >>> decompose_res_name('project/nightfury/1.10')
    ('project', '/nightfury/1.10')
    '''
    res_list = resource.split('/', 1)
    if len(res_list) == 2:
        res_type = res_list[0]
        res_address = '/' + res_list[1]
    else:
        res_type = res_list
        res_address = None

    return res_type, res_address

#@memoized
def resource_info_with_site(resource, site):
    '''Return a dictionary of attributes matching the definition of
    the given resource at the given site.  This function is 'memoized'
    so that any given resource + site pair is looked up only once.
    Any subsequent lookup will have the cached lookup result returned
    instead.
    '''

    res_type, res_address = decompose_res_name(resource)

    # Find the resource specified.  Currently it has to be the full
    # resource path (e.g. 'project/nightfury/1.12' rather than
    # 'project/nightfury').
    try:
        res = Resources.objects.using(site).get(type = res_type, address = res_address)
    except Resources.DoesNotExist:
        raise ArcOrmException(("ERROR: Resource {0} not found: type = {1}, address = {2}\n".format(
                    resource, res_type, res_address)))

    # Put the resource entry info into the result dictionary
    res_dict = {}
    res_dict['id'] = str(res.id)
    res_dict['type'] = str(res.type)
    res_dict['user'] = str(res.user)
    res_dict['owner'] = str(res.owner)
    res_dict['created_at'] = time.ctime(res.created_at)

    # Also gather the resource_data entries that correspond to the
    # resource id (e.g. env var settings).
    rdata_set = ResourceData.objects.using(site).filter(resource = res.id)
    for item in rdata_set:
        res_dict[str(item.name)] = str(item.value)

    return res_dict

def dict_diff(first, second):
    """
    Return a dict of keys that differ between two dicts.
    If a value is not found in one of the dicts, it will be
    represented by '<KEYNOTFOUND>'.

    @param first:   Fist dictionary to diff.
    @param second:  Second dictionary to diff.
    @return diff:   Dict of Key => (first.val, second.val)
    """

    keynotfound = '<KEYNOTFOUND>'
    diff = {}

    # Check all keys in first dict
    for key in list(first.keys()):
        if (not key in second):
            diff[key] = (first[key], keynotfound)
        elif (first[key] != second[key]):
            diff[key] = (first[key], second[key])

    # Check all keys in second dict to find missing
    for key in list(second.keys()):
        if (not key in first):
            diff[key] = (keynotfound, second[key])

    return diff

def detail_diff(diff_tuple):
    '''
    Given two strings with comma-separated attributes, break them
    apart and return new strings with common attributes removed from
    each string.
    '''

    lside, rside = diff_tuple
    lset = set(lside.split(','))
    rset = set(rside.split(','))

    new_lside = ','.join(sorted(lset - rset))
    new_rside = ','.join(sorted(rset - lset))

    return (new_lside, new_rside)

def resource_info_diff(rinfo1, rinfo2, show_all = False):
    '''
    Return a set of tuples giving the diffs between the attributes
    given in the two resource infos.  Skip attributes that will
    always be different (e.g. 'created_at').
    '''

    all_diffs = dict_diff(rinfo1, rinfo2)
    filtered_diffs = all_diffs

    if not show_all:
        # remove fields that will always diff
        filtered_diffs.pop('__resource_name', None)
        filtered_diffs.pop('created_at', None)
        filtered_diffs.pop('definition_source', None)
        filtered_diffs.pop('description', None)
        filtered_diffs.pop('id', None)

    # do detailed diff on 'resources' and 'resolved'
    if ('resources' in filtered_diffs):
        filtered_diffs['resources'] = detail_diff(filtered_diffs['resources'])
    if ('resolved' in filtered_diffs):
        filtered_diffs['resolved'] = detail_diff(filtered_diffs['resolved'])
        
    return filtered_diffs

class ArcORM(object):
    '''
    This class provides object-oriented access to the SQL databases
    that hold information for the ARC resources.
    '''

    # The default ARC site is whatever ARC site the
    # arc.cshrc/arc.bashrc set.
    default_site = os.environ.get('ARC_BROWSE_HOST', 'sj-ice-arc')
    default_site = default_site.replace('.altera.com','');
    default_site = os.environ.get("EC_SITE")

    def __init__(self, site = None):
        if site:
            site = site.replace('.altera.com','')
        self._site = self.default_site if site is None else site

    def psite(self):
        '''
        Debug routine to print the 'site' for this instance of ArcORM.
        '''

        print('site is {0}'.format(self._site))

    def job_info(self, job_id):
        '''Return a dictionary of attributes of that job #
        '''

        # **** This is a work in progress, do not use this call ***
        pass

        try:
            job = Jobs.objects.using(self._site).get(id = job_id)
        except Jobs.DoesNotExist:
            raise ArcOrmException("ERROR: Job {0} not found".format(job_id))

        # Put the resource entry info into the result dictionary
        job_dict = {}
        job_dict['id'] = str(job.id)
        job_dict['command'] = str(job.command)
        job_dict['status'] = str(job.status)
        job_dict['parent'] = str(job.parent)
        job_dict['priority'] = str(job.priority)
        job_dict['type'] = str(job.type)
        job_dict['user'] = str(job.user)
        job_dict['storage'] = str(job.storage)
        job_dict['name'] = str(job.name)
        if (job.family):
            job_dict['family'] = str(job.family)
        job_dict['iwd'] = str(job.iwd)
        job_dict['os'] = str(job.os)
        job_dict['grp'] = str(job.grp)
        job_dict['return_code'] = str(job.return_code)

        # Add the requirements for the job
        try:
            requirements = JobRequirements.objects.using(self._site).filter(job = job_id)
            job_dict['requirements'] = []
            for req in requirements:
                job_dict['requirements'].append(str('{0}/{1}'.format(req.type, req.address)))
        except JobRequirements.DoesNotExist:
            raise ArcOrmException("ERROR: Job {0} requirements not found".format(job_id))

        # Add the resources for the job
        try:
            resources = JobResources.objects.using(self._site).filter(job = job_id)
            job_dict['resources'] = []
            for job_res in resources:
                res = Resources.objects.using(self._site).get(id = job_res.resource)
                job_dict['resources'].append(str('{0}/{1}'.format(res.type, res.address)))
        except JobResources.DoesNotExist:
            raise ArcOrmException("ERROR: Job {0} resources not found".format(job_id))

        # Add the scarce resources for the job

        # Add the processes for the job

        # Also gather the job_data entries that correspond to the
        # job id
        jdata_set = JobData.objects.using(self._site).filter(job = job.id)
        for item in jdata_set:
            job_dict[str(item.name)] = str(item.value)

        return job_dict


    def resource_is_collection(self, resource):
        '''
        Returns True if the resource is a collection, False otherwise.
        '''

        return 'ARC::Resource::Collection' == self.resource_class(resource)

    def resource_url(self, resource):
        '''Return the url of the show_resource page for the resource.
        '''

        rinfo = resource_info_with_site(resource, self._site)
        return 'http://' + self._site + '/arc/dashboard/reports/show_resource/' + rinfo['id']

    def resource_info(self, resource):
        '''Return a dictionary of attributes matching the definition
        of the given resource at the given site.
        '''

        # Send this out to the resource_info_with_site function so the
        # result of the resource + site pair can be memoized (return
        # values cached).
        return resource_info_with_site(resource, self._site)

    def resource_class(self, resource):
        '''Return the resource class of the given resource.
        '''
        res_type, _res_address = decompose_res_name(resource)

        try:
            resmap = ResourceMap.objects.using(self._site).get(type = res_type)
        except ResourceMap.DoesNotExist:
            raise ArcOrmException("ERROR: Resource {0} not found: type = {1}\n".format(
                    resource, res_type))
        res_class = str(resmap.class_field)

        return res_class

    def resource_list(self, res_type):
        '''Return a list of resources matching the res_type.
        '''

        try:
            res_list = Resources.objects.using(self._site).filter(type = res_type)
        except Resources.DoesNotExist:
            raise ArcOrmException("ERROR: Resource type {0} not found".format(res_type))

        rnames = []
        for res in res_list:
            rnames.append(str(res.type + res.address))
        rnames.sort()
        return rnames

    def resource_map_list(self):
        '''Return a list of resource map entries.
        '''

        try:
            map_list = ResourceMap.objects.using(self._site).all()
        except ResourceMap.DoesNotExist:
            raise ArcOrmException("ERROR: Resource map not found")

        mnames = []
        for res_map in map_list:
            mnames.append(str(res_map.type))
        mnames.sort()
        return mnames

    def resource_name(self, res_id):
        '''Return the resource name matching the given resource id.
        '''
        try:
            res = Resources.objects.using(self._site).get(pk = res_id)
            res_name = res.type + res.address
        except Resources.DoesNotExist:
            res_name = 'UnknownResource_' + str(res_id)
        return res_name


    def resources_using(self, resource):
        '''
        Return the collections or bundles which directly include the
        given resource.
        '''

        res_data_set = ResourceData.objects.using(self._site).filter(name = 'resolved', value__regex = resource)

        rlist = []
        for res_data in res_data_set:
            res = res_data.resource
            rlist.append(str(res.type + res.address))
        rlist.sort()
        return rlist


    def resource_diff(self, rname1, rname2):
        '''
        Return a set of tuples giving the diffs between the attributes
        given in the two ARC resources.  Skip attributes that will
        always be different (e.g. 'created_at').
        '''

        rinfo1 = self.resource_info(rname1)
        rinfo2 = self.resource_info(rname2)

        return resource_info_diff(rinfo1, rinfo2)

    def walk_collection(self, res_name, hier = None):
        '''
        Walk the tree of resources that are specified by the given collection.

        For each level, return a tuple of
        (res name, hier, collections, leaves) where
        'res_name' is the name of the resource being returned
        'hier' is a list containing the resources expanded to get here
        'collections' is a list of collections from the 'resources' list
        'leaves' is a list of leaf resouces from the 'resources' list

        No attempt is made to remember which collections have already
        been returned.  If the caller wants to modify the descent, he
        can do so by modifying the 'collections' list.
        '''
        if not res_name or res_name == '':
            return

        if not hier:
            hier = []

        info = self.resource_info(res_name)

        resolved = []
        if ('resolved' in info):
            reslist = info['resolved']
            if reslist:
                resolved = reslist.split(',')

        collections, leaves = [], []
        for res in resolved:
            if self.resource_is_collection(res):
                collections.append(res)
            else:
                leaves.append(res)

        collections.sort()
        leaves.sort()

        yield res_name, hier, collections, leaves

        for res in collections:
            new_hier = list(hier)
            new_hier.append(res_name)

            for yielded in self.walk_collection(res, new_hier):
                yield yielded
