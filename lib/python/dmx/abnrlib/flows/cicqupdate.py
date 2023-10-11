#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/abnrlib/flows/cicqupdate.py#2 $
$Change: 7437460 $
$DateTime: 2023/01/09 18:36:07 $
$Author: lionelta $

Description: plugin for "abnr clonconfigs"

Author: Lee Cartwright
Copyright (c) Altera Corporation 2014
All rights reserved.
'''
from __future__ import print_function
from builtins import str
from builtins import object
import sys
import os
import logging
import textwrap
import tempfile
import re
from pprint import pprint, pformat

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, ROOTDIR)

import dmx.abnrlib.config_factory
from dmx.abnrlib.icm import ICManageCLI
import dmx.utillib.utils
import dmx.utillib.server
#import dmx.utillib.teamcity_cicq_api
import dmx.utillib.factory_cicq_api
import dmx.utillib.diskutils


class CicqUpdateError(Exception): pass

class CicqUpdate(object):
    '''
    Runner class for abnr cloneconfigs
    '''
    def __init__(self, project, variant, config, suffix='', reuse_immutable=True, cfgfile='', init=False, dryrun=False):

        if config.startswith(("REL", "PREL", "snap-")):
            raise Exception("This command does not support running on an immutable bom.")

        self.import_cicq_modules()

        self.project = project
        self.variant = variant
        self.config = config
        self.suffix = suffix    # Thread
        self.reuse_immutable = reuse_immutable
        self.init = init
        self.dryrun = dryrun
        self.logger = logging.getLogger(__name__)
        self.icm = ICManageCLI()
        self.desc = 'branched from dmx cicq update {}/{}@{}'.format(self.project, self.variant, self.config)
        self.cfgfile = cfgfile
        self.sshexe = '/p/psg/da/infra/admin/setuid/tnr_ssh'
        self.server = None

        self.centralize_workdir = ''    # /nfs/site/disks/psg_cicq_1/users/cicq/
        #self.centralize_workdir = self.get_centralize_workdir()
        self.cbb = list(cicq.settings.get_bom_variables())
            
        self.is_naming_convention_compatible_with_teamcity()
            
        #self.tcapi = dmx.utillib.teamcity_cicq_api.TeamcityCicqApi(self.project, self.variant, self.suffix)
        self.tcapi = dmx.utillib.factory_cicq_api.FactoryCicqApi(self.project, self.variant, self.suffix)

        ### Cicq Backend Boms
        if self.suffix:
            for i,n in enumerate(self.cbb):
                self.cbb[i] = '{}_{}'.format(self.cbb[i], suffix)
        self.logger.debug("CBB:{}".format(self.cbb))

        self.cfgfileobj = ''
        if self.cfgfile:
            ### Validate cfgfile by making sure it is able to be loaded without raising any exception.
            self.cfgfileobj = self.get_cfgfile_object()
            self.cfgfile_source = 'local'
        else:
            self.cfgfile_source = 'central'


        self.logger.debug("dryrun: {}".format(self.dryrun))
        self.logger.debug("init: {}".format(self.init))

    def get_centralize_workdir(self):
        if not self.centralize_workdir:
            jobname = '{}.{}.{}'.format(self.project, self.variant, self.suffix)
            disk_postfix = os.path.join('users', 'cicq', jobname)
            if self.init:
                du = dmx.utillib.diskutils.DiskUtils(site='sc')
                dd = du.get_all_disks_data('_cicq_')
                sdd = du.sort_disks_data_by_key(dd, key='Avail')
                largest_available_disk = sdd[0]['StandardPath']
                self.centralize_workdir = os.path.join(largest_available_disk, disk_postfix)
            else:
                ### Get the info from teamcity
                ret = self.tcapi.get_centralize_workdir()
                if not ret:
                    raise Exception("Can not find centralize_workdir for {}!".format(jobname))
                self.centralize_workdir = os.path.join(os.path.dirname(ret), jobname)

        return self.centralize_workdir


    def is_naming_convention_compatible_with_teamcity(self):
        '''
        TeamCity has a limitation when creating jobs.
        The ID can only be alphanumeric or underscore.
        https://jira.devtools.intel.com/browse/PSGDMX-2079
        '''
        for prop in ['project', 'variant', 'suffix']:
            val = getattr(self, prop, '')
            if val:
                m = re.match("^[\.\w\d_]+$", val)
                if not m:
                    raise Exception("{}:{} contains unsupported character. It should be a string which contains only alphabets, numbers, dots and underscores.".format(prop, val))
        return True


    def is_thread_name_conflict(self):
        retlist = self.tcapi.get_all_threads_name(teamcity_compliant=False)
        if self.suffix in retlist:
            return retlist
        return []


    def run(self):
        '''
        Executes the abnr cloneconfigs command
        :return: 0 == success, non-zero == failure
        :type return: int
        '''
        ret = 1
    
        if self.init:
            threads_name = self.is_thread_name_conflict()
            if threads_name:
                errmsg = ''' The thread name that you picked conflicts with an existing thread name.
                Kindly pick another one which is not within the following list which is already in used:-
                {} '''.format(pformat(threads_name))
                self.logger.error(errmsg)
                return 1
            else:
                self.logger.debug("No thread name conflict found.")
        else:
            data = self.tcapi.get_buildtype(self.tcapi.buildtypeId)
            if 'Could not find' in data:
                self.logger.error(data)
                self.logger.error("Could not find the corresponding cicq job from TeamCity. Program Terminated.")
                return 1

        if self.dryrun:
            self.logger.info("Dryrun mode. Nothing else can be done. Aborting.")
            return 0

        if self.cfgfile:
            self.server = dmx.utillib.server.Server().get_working_server()
            self.create_centralize_workdir()
            self.upload_cfgfile()
        else:
            self.cfgfile = tempfile.mkstemp(dir='/tmp')[1]
            self.download_cfgfile()

        self.deliverables = self.get_deliverables_from_cfgfile() 
        self.logger.info("deliverables:{}".format(self.deliverables))

        for dstconfig in self.cbb:
        
            if not self.init and self.is_2_bom_structures_equal(self.project, self.variant, self.config, self.project, self.variant, dstconfig, self.deliverables):
                self.logger.info("CBB bom {} structure matches source bom {} structure. Skip updating CBB boms.".format([self.project, self.variant, self.config], [self.project, self.variant, dstconfig]))
                continue
            else:
                self.logger.info("CBB bom structure mismatch with source bom. Starting updating process ...")
                if self.dryrun:
                    self.logger.info("Dryrun mode. Do nothing !")
                    continue

            srccf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(self.project, self.variant, self.config, None)
            self.logger.debug("ConfigFactory of srcconfig: {}".format(srccf))
            
            ### This part make all the preparation (ie: create all the missing libtypes' dstconfig)
            ### - create all the new libtypes library
            ### - create all the new libtypes config
            for x in srccf.flatten_tree():
                if not x.is_config() and x.libtype in self.deliverables:
                    dup_add_libraries = self.icm.add_libraries(x.project, x.variant, [x.libtype], dstconfig, self.desc)
                    #dup_add_configs = self.icm.add_libtype_configs(x.project, x.variant, [x.libtype], dstconfig, '#dev', dstconfig)    # No longer needed in gdpxl
                    if x.libtype == 'ipspec':
                        self.icm.add_library_properties(x.project, x.variant, x.libtype, dstconfig, {"Owner": os.getenv("USER")})

            ### The algorithm for this section is
            ### - collect all the [project,variant] from toplevel and store in todo_pvs
            ### - foreach of [project, variant] from todo_pvs:
            ###   >   check if all of the immediate children(variant) of project/variant is already available in icm. IF yes, then may proceed to next step:-
            ###     *   create a ConfigFactory(cfobj) for project/variant
            ###     *   remove all immediate configs
            ###     *   see what configs the source-bom has, and add them back in one-by-one
            ###     *   do a shallow_save.
            todo_pvs = [[x.project, x.variant] for x in srccf.flatten_tree() if x.is_config()]
            ### uniqify list
            todo_pvs = [list(y) for y in set([tuple(x) for x in todo_pvs])]
            done_pvs = []
            repeatcount = {}
            while len(done_pvs) < len(todo_pvs):
                self.logger.debug("{} todo_pvs({}): {}".format(dstconfig, len(todo_pvs), todo_pvs))
                self.logger.debug("{} done_pvs({}): {}".format(dstconfig, len(done_pvs), done_pvs))
                for p,v in todo_pvs:
                    sub_srccf = srccf.search(project="^{}$".format(p), variant="^{}$".format(v), libtype=None)[0]

                    if not self._is_all_sub_variant_config_done(sub_srccf, done_pvs):
                        self.logger.info("Temporary skip {} as its subvariants are not ready yet.".format([p,v]))
                        continue

                    else:

                        if [p,v] in done_pvs:
                            self.logger.info("Skipping {} because it was done.".format([p,v]))
                            continue

                        if self.reuse_immutable and not sub_srccf.is_mutable() and [p, v] != [self.project, self.variant]:
                            done_pvs.append([p, v])
                            continue

                        ### if dstcf exist, create_From_icm, otherwise, clone from srccf
                        try:
                            dstcf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(p, v, dstconfig)
                            self.logger.debug("-- config exists: creating from icm ...")
                        except:
                            dstcf = sub_srccf.clone(dstconfig)
                            self.logger.debug("-- config doesnt exist: cloning from source ...")
                        
                        self.logger.info("Updating {} ...".format(dstcf.get_full_name()))

                        ### Remove everything from dstcf, so that we start from a clean state
                        ### later on only we add in one-by-one those sub ip/libtype's config
                        self.logger.debug("- Removing all configs from {} ...".format(dstcf.get_full_name()))
                        for x in dstcf.configurations.copy():
                            dstcf.remove_configuration(x)
                            self.logger.debug("  > removed {} from {} ...".format(x.get_full_name(), dstcf.get_full_name()))

                        self.logger.debug("- Adding all configs into {} ...".format(dstcf.get_full_name()))
                        for c in sub_srccf.configurations:

                            ### Skip is self
                            if c == sub_srccf:
                                continue

                            if c.is_config():
                                libtype = None
                            else:
                                libtype = c.libtype
                                if libtype not in self.deliverables:
                                    self.logger.info("  > Skip adding {}. It is not in cfgfile's deliverable list.".format(libtype))
                                    continue

                            ### Support reuse_immutable option. Reuse immutable if the source config is immutable
                            ### https://jira.devtools.intel.com/browse/PSGDMX-1687
                            if self.reuse_immutable and not c.is_mutable():
                                newconfig = c.config
                            else:
                                newconfig = dstconfig

                            subcf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(c.project, c.variant, newconfig, libtype=libtype)
                            dstcf.add_configuration(subcf)
                            self.logger.debug("  > added {} into {} ...".format(subcf.get_full_name(), dstcf.get_full_name()))

                        dstcf.save(shallow=True)

                        done_pvs.append([p, v])

                ### Add a failsafe mechanism so that it does not run into infinite loop is something wrong happens
                key = str(len(done_pvs))
                if key in repeatcount:
                    repeatcount[key] += 1
                else:
                    repeatcount[key] = 1
                self.logger.debug("{} repeatcount:{}".format(dstconfig, repeatcount))
                if repeatcount[key] > 10:
                    self.logger.error("Something went wrong! This loop has been repeated for more than 10 times. Aborting job. Please contact psgicmsupport@intel.com for further investigation.")
                    return 1

        self.logger.info("CBB configs/branches successfully created.")
        if self.init:
            self.logger.info("Setting up TeamCity build ...")
            workdir = self.get_centralize_workdir()
            self.tcapi.setup_build(workdir=workdir)
            self.logger.info("Done setting up TeamCity.")

        if self.cfgfile_source == 'local':
            self.update_teamcity_settings()

        self.tcapi.set_refbom(self.config)

        ret = 0

        return ret




    def update_teamcity_settings(self):
        c = self.get_cfgfile_object()

        if c._arc_resources:
            self.logger.info("Setting Teamcity param for arc_resources: {}".format(c._arc_resources))
            self.tcapi.set_arc_resources(c._arc_resources)

        if c._trigger:
            self.logger.info("Ignore Setting Teamcity trigger: {}. This feature is deprecated !".format(c._trigger))
            #self.tcapi.setup_trigger(c._trigger)  


    def is_2_bom_structures_equal(self, project1, variant1, config1, project2, variant2, config2, deliverables):
        '''
        2 parts of checking:-
            #1. Make sure that all srcconfig's subconfigs are found + identical in dstconfig
            #2. Make sure that no additional deliverables other than the given deliverables are in dstconfig
        Any failure of the above mentioned check will return 'False'.
        '''

        self._mismatch = []  # this variable is meant/used for unit testing.

        self.logger.info("Crosscheck content of {} vs {} and see if they are matching ...".format([project1, variant1, config1], [project2, variant2, config2]))
        srccf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(project1, variant1, config1, None)
        cbbcf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(project2, variant2, config2, None)
       
        src_flattened = srccf.flatten_tree()
        cbb_flattened = cbbcf.flatten_tree()

        ### Check #1: srcconfig's subconfigs are found + identical in dstconfig
        errcount = 0
        for sc in src_flattened:

            scproregex = '^{}$'.format(sc.project)
            scvarregex = '^{}$'.format(sc.variant)
            if not sc.is_config():
                if sc.libtype in deliverables:
                    sclibregex = '^{}$'.format(sc.libtype)
                else:
                    continue
            else:
                sclibregex = None
                if sc.project == project1 and sc.variant == variant1 and sc.config == config1:
                    self.logger.debug("Skipped checking highest level composite config {}".format(sc))
                    continue

            scbomregex = '^{}$'.format(sc.name)
            found = cbbcf.search(scproregex, scvarregex, sclibregex)
            matched = False
            if found:
                sobj = found[0]
                if sc.name == sobj.name:
                    matched = True

            if not matched:
                msg = "Mismatch: {} - {}".format(cbbcf, [scproregex, scvarregex, sclibregex, scbomregex])
                self.logger.debug(msg)
                self._mismatch.append(msg)
                errcount += 1
            else:
                msg = "Match: {} - {}".format(cbbcf, [scproregex, scvarregex, sclibregex, scbomregex])
                self.logger.debug(msg)

        ### check #2: no additional deliverables exist in dstconfig
        for cc in cbb_flattened:
            if not cc.is_config() and cc.libtype not in deliverables:
                errcount += 1
                msg = "Mismatch: {} not in cfgfile's deliverable's list:".format(cc)
                self.logger.debug(msg)
                self._mismatch.append(msg)

        self.logger.info("Total Mismatch:{}".format(errcount))

        if errcount:
            return False
        return True


    def get_deliverables_from_cfgfile(self):
        c = self.get_cfgfile_object()
        return c._deliverables

    def get_cfgfile_object(self):
        if not self.cfgfileobj:
            self.logger.debug("Creatint cicq.ini obj from {}".format(self.cfgfile))
            self.cfgfileobj = cicq.cicqlib.config.Configuration(self.cfgfile, self.project, self.variant, self.suffix)
        return self.cfgfileobj


    def create_centralize_workdir(self):
        '''
        mkdir -p <centralize_workdir>
        '''
        workdir = self.get_centralize_workdir()
        mkdir_cmd = 'mkdir -p {}'.format(workdir)
        ssh_cmd = "{} -q {} '{}'".format(self.sshexe, self.server, mkdir_cmd)
        self.logger.debug("Running: {}".format(ssh_cmd))
        self.logger.info("""
        +===========================================================+
        | PLEASE DO NOT ENTER ANY PASSWORD WHEN BEING ASKED FOR IT! |
        | DOING THIS MIGHT GET THE HEADLESS ACCOUNT LOCKED !!!      |
        |                 !!! JUST WAIT !!!                         |
        |          THANK YOU FOR YOUR PATIENCE !!!                  |
        +===========================================================+
        """)

        if not self.dryrun:
            exitcode, stdout, stderr = dmx.utillib.utils.run_command(ssh_cmd)
            self.logger.debug("exitcode:{}, stdout:{}, stderr:{}".format(exitcode, stdout, stderr))
        else:
            self.logger.info("dryrun mode. Nothing happens.")
            exitcode = 0
        return exitcode


    def upload_cfgfile(self):
        '''
        upload the given cicq.ini cfgfile to the centralized CICQ work area.

        We need to upload it as headless:psginfraadm
        However, headless might not have permission to access the file.
        Thus, we need to 
        - copy the file to a place which is accessible by both (headless + user)
            > /tmp should be the place.
        - rsync the file over to centralize_workspace (in SC)
        '''
        workdir = self.get_centralize_workdir()
        tmpfile = tempfile.mkstemp(dir='/tmp')[1]
        os.system("cp -rf {} {}".format(self.cfgfile, tmpfile))
        os.system("chmod 777 {}".format(tmpfile))
        rsync_cmd = 'rsync -avxz --chmod=u=rwx,go-wx {} {}:{}'.format(tmpfile, self.server, os.path.join(workdir, 'cicq.ini'))
        ssh_cmd = "{} -q localhost '{}'".format(self.sshexe, rsync_cmd)
        self.logger.debug("Running: {}".format(ssh_cmd))
        self.logger.info("""
        +===========================================================+
        | PLEASE DO NOT ENTER ANY PASSWORD WHEN BEING ASKED FOR IT! |
        | DOING THIS MIGHT GET THE HEADLESS ACCOUNT LOCKED !!!      |
        |                 !!! JUST WAIT !!!                         |
        |          THANK YOU FOR YOUR PATIENCE !!!                  |
        +===========================================================+
        """)
        if not self.dryrun:
            exitcode, stdout, stderr = dmx.utillib.utils.run_command(ssh_cmd)
            self.logger.debug("exitcode:{}, stdout:{}, stderr:{}".format(exitcode, stdout, stderr))
        else:
            self.logger.info("dryrun mode. Nothing happens.")
            exitcode = 0
        os.system("rm -rf {}".format(tmpfile))
        return exitcode


    def download_cfgfile(self):
        '''
        download the given cicq.ini cfgfile from the centralized CICQ work area.

        We need to download it as headless:psginfraadm
        However, headless might not have permission to access the file.
        Thus, we need to 
        - rsync the file to a place which is accessible by both (headless + user)
            > /tmp should be the place.
        - cp the file over to cwd
        '''
        workdir = self.get_centralize_workdir()
        tmpfile = tempfile.mkstemp(dir='/tmp')[1] + '_psginfraadm'
        if not self.server:
            self.server = dmx.utillib.server.Server().get_working_server()
        rsync_cmd = 'rsync -avxz --chmod=ugo=rwx {}:{} {}'.format(self.server, os.path.join(workdir, 'cicq.ini'), tmpfile)
        ssh_cmd = "{} -q localhost '{}'".format(self.sshexe, rsync_cmd)
        self.logger.debug("Running: {}".format(ssh_cmd))
        self.logger.info("""
        +===========================================================+
        | PLEASE DO NOT ENTER ANY PASSWORD WHEN BEING ASKED FOR IT! |
        | DOING THIS MIGHT GET THE HEADLESS ACCOUNT LOCKED !!!      |
        |                 !!! JUST WAIT !!!                         |
        |          THANK YOU FOR YOUR PATIENCE !!!                  |
        +===========================================================+
        """)

        if not self.dryrun:
            exitcode, stdout, stderr = dmx.utillib.utils.run_command(ssh_cmd)
            self.logger.debug("exitcode:{}, stdout:{}, stderr:{}".format(exitcode, stdout, stderr))
        else:
            self.logger.info("dryrun mode. Nothing happens.")
            exitcode = 0
        self.logger.debug("""
            exitcode: {}
            stdout: {}
            stderr: {}
        """.format(exitcode, stdout, stderr))

        if 'failed: No such file or directory' in stdout+stderr:
            raise Exception("Project [{}.{}.{}] not found/setup in centralize area!".format(self.project, self.variant, self.suffix))

        if not self.cfgfile:
            self.cfgfile = './cicq.ini'

        return os.system("cp -f {} {}".format(tmpfile, self.cfgfile))


    def _is_all_sub_variant_config_done(self, cfobj, done_pvs):
        '''
        check and see if all variant configs that are directly included in this level exist in icm.
        
        cfobj: ICMConfig object
        dstconfig: destination config name (str)
        return: True if yes, False if no.
        '''
        for cf in cfobj.configurations:
            if cf.is_config() and [cf.project, cf.variant] not in done_pvs:
                return False
        return True


    def import_cicq_modules(self):
        '''
        We can not do this import at the very top of the code because, if we do so,
        any dmx command invoked will require cicq resource, (eg:- dmx help, dmx report list, ...),
        and we do not want that to happen. Thus, we have no choice, but to only load this when 
        necessary.
        '''
        try:
            CICQROOTDIR = os.path.join(os.environ['CICQ_ROOT'], 'lib')
            sys.path.insert(0, CICQROOTDIR)
            sys.path.insert(0, '/p/psg/flows/common/cicq/latestdev_gdpxl/lib')
            global cicq
            import cicq.settings
            import cicq.cicqlib.config
        except:
            raise
            raise CicqUpdateError("Incorrect/Missing cicq arc resource. Please make sure cicq/3.3 or newer version is loaded.")


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)   
    
    project = 'i10socfm'
    variant = 'liotestfc1'
    config = 'dev'
    thread = 'test3'
    init = False
    a = CicqUpdate(project, variant, config, suffix=thread, init=init, dryrun=True)
    a.get_centralize_workdir()
    print("centralize_workdir: {}".format(a.centralize_workdir))


