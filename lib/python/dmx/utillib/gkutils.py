#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/gkutils.py#5 $
$Change: 7698488 $
$DateTime: 2023/07/14 01:08:08 $
$Author: lionelta $

Description: 
    API functions which interacts with Gatekeeper

Here's the methodology for GK setting in PSG
=============================================

https://wiki.ith.intel.com/display/tdmaInfra/GateKeeper+Recipes+In+PSG+Methodology

1. whenever a new icm-library is created in cthfe libtype,
   a. a centralizee git-repo needs to be created at $GIT_REPOS/git_repos
      - the naming convention of the git_repo follows this syntax:-
         > PVLLid-a0 (Project/variant/libtype/library's ID)
         > eg: L124352-a0
   b. the (cluster + stepping) value needs to be updated in gk config file
      - GkConfig.clusterstepping.pl file needs to be updated.
      - cluster  = L123456
      - stepping = a0

'''
from __future__ import print_function

from builtins import object
import os
import logging
import sys
import re
import tempfile
import datetime
from pprint import pprint,pformat
import time

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.insert(0, LIB)

import dmx.utillib.utils
import dmx.utillib.server
import dmx.abnrlib.icm
import dmx.utillib.contextmgr
import dmx.abnrlib.workspace
import dmx.utillib.git

LOGGER = logging.getLogger(__name__)

class GkUtils(object):

    def __init__(self, cache=True):
        self.ssh = '/p/psg/da/infra/admin/setuid/ssh_psgcthadm'
        self.server = 'rsync.zsc7.intel.com'
        self.clustersteppingfile = 'GkConfig.clusterstepping.pl'
        self.icm = dmx.abnrlib.icm.ICManageCLI()
        self.gkserver = 'scygatkpr327.zsc7.intel.com'
        self.git = dmx.utillib.git.Git()
        self.site = os.getenv("EC_SITE", "")

    def update_everything(self, libtype, days, tmplpath, repopath, preview=True):
        ''' Update everything. Here's what it will do:-
        1)run 'get_new_libraries'
        2)run 'init_git_repo' 
        3)run 'update_gk_config'
        4)run 'reread_config'
        5)run 'dump_config'
        '''

        if preview:
            LOGGER.info("DRYRUN mode on !")

        errlist = []

        icmlibs = self.get_newly_created_icm_libraries(libtype, days)
        LOGGER.info("NEWLY CREATED LIBRARIES: {}".format(icmlibs))

        if not icmlibs:
            LOGGER.info("There are no newly created icmlibs. There is nothing to do. Exiting ...")
            return 0

        clusters, steppings, clusteps = self.reformat_icmobjs_to_clusters_steppings(icmlibs)
        LOGGER.info("NEW CLUSTERS: {}".format(clusters))
        LOGGER.info("NEW STEPPINGS {}".format(steppings))

        for name in clusteps:
            newrepo = os.path.join(repopath, name)
            retcode = self.clone_git_template_to_git_repo(tmplpath, newrepo)
            if retcode:
                errlist.append("FAIL to create git_repo: {}".format(newrepo))

        missing_clusters_and_steppings = self.update_gk_clusters_steppings(clusters, steppings, preview=preview)

        if not missing_clusters_and_steppings:
            LOGGER.info("There are no missing cluster/stepping. All cluster and stepping are already up-to-date.\nNothing else to do here. Exiting ...")
            return 0

        self.reread_config(preview=preview)
        self.dump_config()
        self.report_errors(errlist)


    def report_errors(self, errlist):
        if not errlist:
            print("===================================================")
            print(" Job Completed Successfully With No Errors ! ")
            print("===================================================")
        else:
            print("===================================================")
            print(" Job Completed With {} Errors ! ".format(len(errlist)))
            print("===================================================")
            for i, err in enumerate(errlist):
                print("{}. {}".format(i, err))
            print("===================================================")


   
    def reformat_icmobjs_to_clusters_steppings___old(self, icmobjs):
        '''
        icmobjs = 
            {u'project:parent:name': u'da_i18a', u'path': u'/intel/da_i18a/dmz_test/cthfe/dev', u'created': u'2022-09-21T20:26:12.671Z', u'variant:parent:name': u'dmz_test', u'name': u'dev'}, 
            {u'project:parent:name': u'da_i18a', u'path': u'/intel/da_i18a/regword/cthfe/dev', u'created': u'2022-09-23T04:25:08.070Z', u'variant:parent:name': u'regword', u'name': u'rc'},

        return = [
            ('da_i18a.dmx_test.cthfe', 'da_i18a.regword.cthfe'), # clusters
            ('dev', 'rc'), # steppings
            ('da_i18a.dmz_test.cthfe-dev', 'da_i18.regword.cthfe-rc') # clusters-steppings (git-repo naming convention)
        ]
        '''
        clusters = set()
        steppings = set()
        clusteps = set()
        for obj in icmobjs:
            c = '{}.{}.{}'.format(obj['project:parent:name'], obj['variant:parent:name'], obj['libtype:parent:name'])
            s = obj['name']
            clusters.add(c)
            steppings.add(s)
            clusteps.add('{}-{}'.format(c, s))

        return [clusters, steppings, clusteps]


    def reformat_icmobjs_to_clusters_steppings(self, icmobjs):
        '''
        icmobjs = 
            {u'id': L123456, u'project:parent:name': u'da_i18a', u'path': u'/intel/da_i18a/dmz_test/cthfe/dev', u'created': u'variant:parent:name': u'dmz_test', u'name': u'dev'}, 
            {u'id': L777888, u'project:parent:name': u'da_i18a', u'path': u'/intel/da_i18a/regword/cthfe/dev', u'created': u'variant:parent:name': u'regword', u'name': u'rc'},

        return = [
            ('L123456', 'L777888'), # clusters
            ('a0'), # steppings (hardcode to always return ('a0')
            ('L123456-a0', 'L777888-a0') # clusters-steppings (git-repo naming convention)
        ]
        '''
        clusters = set()
        steppings = set()
        clusteps = set()
        for obj in icmobjs:
            c = obj['id']
            s = 'a0'
            clusters.add(c)
            steppings.add(s)
            clusteps.add('{}-{}'.format(c, s))

        return [clusters, steppings, clusteps]



    def clone_git_template_to_git_repo(self, tmplpath, repopath):
        ''' Do a bare git clone of `tmplpath` to `repopath`.
        This can only be done by `psgcthadm` headless.
        
        tmplpath = '/nfs/site/disks/psg.git.001/git_templates/new_template'
        repopath = '/nfs/site/disks/psg.git.001/git_repos/i10socfm.cw_lib.cthfe-fp8_dev'
        '''
        reponame = os.path.basename(repopath)
        repodir = os.path.dirname(repopath)
        cmd = 'cd {}; groups; whoami; /p/hdk/rtl/proj_tools/git/da_tools/master/latest/make_git_repo -d -b -r -t {} {}'.format(repodir, tmplpath, reponame)
        finalcmd = """ {} {} -q '{}' """.format(self.ssh, self.server, cmd)
        exitcode, stdout, stderr = self.__runcmd(finalcmd)
        pass_str = 'Push returned successful'
        if pass_str in stdout+stderr:
            LOGGER.info("PASS: Git Repo ({}) successfully created.".format(repopath))
            retval = 0
        else:
            LOGGER.error("FAIL: Git Repo ({}) FAILED to be created.".format(repopath))
            retval = 1
        return retval

    def add_power_users(self, project, cluster, stepping, userlist, preview=True):
        ''' Add users as poweruser to project/cluster/stepping '''
        LOGGER.debug("HOSTNAME: {}".format(os.system("hostname -f")))
        LOGGER.debug("project={}, cluster={}, stepping={}, users={}, dryrun={}".format(project, cluster, stepping, userlist, preview))
        cfgdir = self.crt_clone_gk_config()
        if not cfgdir:
            return 1
        powerfile = os.path.join(cfgdir, 'powerusers', 'powerusers.{}.{}.{}.txt'.format(project, cluster, stepping))
        LOGGER.debug("- powerfile: {}".format(powerfile))
        existing_users = self.get_existing_users_from_powerfile(powerfile)
        LOGGER.debug("- existing_users: {}".format(existing_users))
        full_user_list = list(set(existing_users + userlist))
        LOGGER.debug("- full_user_list: {}".format(full_user_list))
        self.add_users_to_powerfile(powerfile, full_user_list)
        
        self.checkin_configfiles(cfgdir, filelist=[powerfile], msg='Automated: add power user for {}/{}/{}'.format(project, cluster, stepping))
        if not preview:
            LOGGER.info("Running: crt install config ......")
            self.crt_install_configfiles(cfgdir)
        else:
            LOGGER.info("Dryrun mode: Skipping crt install config stage.")
            
        return 0


    def add_users_to_powerfile(self, powerfile, userlist):
        os.system("rm -rf {}".format(powerfile))
        with open(powerfile, 'w') as f:
            for user in userlist:
                f.write("{}\n".format(user))
        os.system("cat {}".format(powerfile))


    def get_existing_users_from_powerfile(self, powerfile):
        if not os.path.isfile(powerfile):
            return []
            
        ret = []
        with open(powerfile) as f:
            for line in f:
                sline = line.strip()
                if line and not sline.startswith("#"):
                    ret.append(sline)
        return ret

    def update_gk_clusters_steppings(self, clusters=None, steppings=None, preview=True):
        ''' Add Clusters/Steppings in GK configs 
        
        This API required some access permission.
        If you do not have them, kindly follow the wiki to request for those:-
        https://wiki.ith.intel.com/display/tdmaInfra/GateKeeper%28gk%29+Administrative+Backend+Infrastructure

        return = [missing_clusters, missing_steppings]
        '''
        LOGGER.debug("clusters={}, steppings={}".format(clusters, steppings))
        cfgdir = self.crt_clone_gk_config()
        if not cfgdir:
            return 1
        curr_clusters, curr_steppings = self.get_current_clusters_steppings_from_config(cfgdir)
        LOGGER.debug("curr_clusters: {}\ncurr_steppings: {}\n".format(curr_clusters, curr_steppings))

        missing_clusters = self.get_missing_elements(curr_clusters, clusters)
        missing_steppings = self.get_missing_elements(curr_steppings, steppings)
        LOGGER.debug('missing_clusters: {}'.format(missing_clusters))
        LOGGER.debug('missing_steppings: {}'.format(missing_steppings))

        if not missing_clusters and not missing_steppings:
            LOGGER.info("There are no missing cluster/stepping. All cluster and stepping are already up-to-date.\nNothing else to do here. Exiting ...")
            return []

        LOGGER.info("Adding missing cluster/stepping to configfile ...")
        self.add_missing_clusters_steppings_to_configfile(cfgdir, missing_clusters, missing_steppings)

        self.checkin_configfiles(cfgdir, filelist=[self.clustersteppingfile])
        if not preview:
            LOGGER.info("Running: crt install config ......")
            self.crt_install_configfiles(cfgdir)
        else:
            LOGGER.info("Dryrun mode: Skipping crt install config stage.")
            
        return [missing_clusters, missing_steppings]


    def checkin_configfiles(self, cfgdir, filelist, msg='automated update gk clusterstepping config.'):
        with dmx.utillib.contextmgr.cd(cfgdir):
            for f in filelist:
                self.__runcmd("git add {}".format(f))
            self.__runcmd("git commit -m '{}'".format(msg))

    def crt_install_configfiles(self, cfgdir, tool='gatekeeper_configs/psg'):
        ### /p/hdk/pu_tu/prd/crt/latest/client/crt
        cmd = '/nfs/site/disks/crt_linktree_1/crt/latest/client/crt install -tool {}  --updatelink latest -onduplication link --src {} '.format(tool, cfgdir)
        exitcode, stdout, stderr = self.__runcmd(cmd)
       
    def reread_config(self, preview=True):
        if preview:
            LOGGER.info("dryrun mode on: Will run -info instead of -rereadconfig.")
            cmd = ''' ssh localhost -q "/nfs/site/proj/hdk/pu_tu/prd/liteinfra/1.8.p02/commonFlow/bin/cth_psetup -p psg -cfg KM5A0P00_FE_RC.cth -cmd 'turnin -proj psg -c softip -s a0 -info'" '''
        else:
            cmd = ''' ssh localhost -q "/nfs/site/proj/hdk/pu_tu/prd/liteinfra/1.8.p02/commonFlow/bin/cth_psetup -p psg -cfg KM5A0P00_FE_RC.cth -cmd 'turnin -proj psg -c softip -s a0 -rereadconfig'" '''
        exitcode, stdout, stderr = self.__runcmd(cmd)
        LOGGER.info("\n{}".format(stdout))
      

    def dump_config(self):
        cmd = ''' ssh localhost -q "/nfs/site/proj/hdk/pu_tu/prd/liteinfra/1.8.p02/commonFlow/bin/cth_psetup -p psg -cfg KM5A0P00_FE_RC.cth -cmd 'turnin -proj psg -c softip -s a0 -dumpconfig'" '''
        exitcode, stdout, stderr = self.__runcmd(cmd)
        LOGGER.info("\n{}".format(stdout))


    def get_missing_elements(self, oldlist, newlist):
        if not newlist or newlist == None:
            return set()
        return set(newlist) - set(oldlist)


    def get_newly_created_icm_libraries(self, libtype='cthfe', days=7):
        ''' By default, return all newly created icm-libraries for cthfe libtype
        for the past 7 days

        return = [
            {u'project:parent:name': u'da_i18a', u'path': u'/intel/da_i18a/dmz_test/cthfe/dev', u'created': u'2022-09-21T20:26:12.671Z', u'variant:parent:name': u'dmz_test', u'name': u'dev'}, 
            {u'project:parent:name': u'da_i18a', u'path': u'/intel/da_i18a/regword/cthfe/dev', u'created': u'2022-09-23T04:25:08.070Z', u'variant:parent:name': u'regword', u'name': u'dev'},
            ... ... ...
        ]
        '''
        delta = datetime.timedelta(days=int(days))
        today = datetime.datetime.now().date()
        deltadate = today - delta
        criteria = """path:~/{}/ created:>{}""".format(libtype, deltadate)
        retlist = self.icm._find_objects('library', criteria, retkeys=['id', 'project:parent:name', 'variant:parent:name', 'libtype:parent:name', 'name', 'path', 'created'])
        return retlist


    def add_missing_clusters_steppings_to_configfile(self, cfgdir, missing_clusters, missing_steppings):
        ''' '''
        cfgfile = os.path.join(cfgdir, self.clustersteppingfile)
        _, tmpfile = tempfile.mkstemp(dir=cfgdir, text=True)
        with open(tmpfile, 'w') as of:
            with open(cfgfile) as f:
                for line in f:
                    of.write(line)
                    if re.search('^\$GkConfig{validClusters}\s*=', line):
                        for e in missing_clusters:
                            of.write("    {}\n".format(e))
                    elif re.search('^\$GkConfig{validSteppings}\s*=', line):
                        for e in missing_steppings:
                            of.write("    {}\n".format(e))
        LOGGER.debug("new clusterstepping config file created at: {}".format(tmpfile))
        self.__runcmd('mv -f {} {}'.format(tmpfile, cfgfile))



    def get_current_clusters_steppings_from_config(self, cfgdir):
        ''' get the current clusters/steppings from the config file.

        Example of the file content:-
        ... ... ...
        # tell GK what cluster(s) are valid
        $GkConfig{validClusters}  = [ qw(
            softip
            i18asoc
            Kinneloa_Mesa
        )];
        # tell GK what stepping(s) are valid
        $GkConfig{validSteppings} = [ qw(
            a0
        )];
        ... ... ...
        '''
        cfgfile = os.path.join(cfgdir, self.clustersteppingfile)
        clusterStart = 0
        steppingStart = 0
        clusters = []
        steppings = []
        LOGGER.debug("Reading config file {} ...".format(cfgfile))
        with open(cfgfile) as f:
            for line in f:
                if re.search('^\$GkConfig{validClusters}\s*=', line):
                    clusterStart = 1
                elif line.startswith(')];'):
                    clusterStart = 0
                    steppingStart = 0
                elif re.search('^\$GkConfig{validSteppings}\s*=', line):
                    steppingStart = 1
                elif clusterStart:
                    sline = line.strip()
                    if sline and not sline.isspace():
                        clusters.append(sline)
                elif steppingStart:
                    sline = line.strip()
                    if sline and not sline.isspace():
                        steppings.append(sline)
        return [clusters, steppings]


    def crt_clone_gk_config(self, tool='gatekeeper_configs/psg'):
        ''' Clone the Gatekeeper Config git-repo from crt.

        if job is successful, return the fullpath of the crt cloned folder
        else, return ''
        '''
        tempdir = tempfile.mkdtemp()
        ### /p/hdk/pu_tu/prd/crt/latest/client/crt
        cmd = '/nfs/site/disks/crt_linktree_1/crt/latest/client/crt clone -tool {} --target {}'.format(tool, tempdir)  
        exitcode, stdout, stderr = self.__runcmd(cmd)
        pass_str = "-I- crt: Finished clone of '{}' into".format(tool)
        if pass_str in stdout + stderr:
            LOGGER.info("PASS: crt clone tool({}) to {}".format(tool, tempdir))
            retval = tempdir
        else:
            LOGGER.error("FAIL: crt clone tool({}) to {}".format(tool, tempdir))
            retval = ''
        return retval


    def run_turnin_from_icm_workspace(self, wsroot, project, variant, libtype, thread, milestone, gkproj='psg', mock=True, tag=''):
        ''' https://wiki.ith.intel.com/pages/viewpage.action?pageId=2442526927

        1. self.prepare_turnin_run_for_icm()
        2. turnin mock
            > cd $STAGE
            > run turnin
        '''
        stepping = 'a0'

        LOGGER.info("Getting library info from wsroot's {}/{}/{} ...".format(project, variant, libtype))
        library = self.get_library_from_workspace_pvl(wsroot, project, variant, libtype)
        LOGGER.info("Library == {}".format(library))

        LOGGER.info("Preparing Turnin Run For ICM ...")
        [pvllid, stage_repo] = self.prepare_turnin_run_for_icm(wsroot, project, variant, libtype, library, thread, milestone, tag=tag)
       
        turninmode = ['Real', 'Mock']
        LOGGER.info("Running {} Turnin. Please be patient, as this might take a while  ...".format(turninmode[mock]))
        exitcode, stdout, stderr = self.run_turnin(stage_repo, gkproj, pvllid, stepping, mock=mock)

        LOGGER.info("Waiting for Turnin to complete. Please be patient, as this might take a while  ...")
        retcode, retmsg = self.report_turnin_result(stage_repo, mock=mock)

        return [retcode, retmsg]

    def get_library_from_workspace_pvl(self, wsroot, project, variant, libtype):
        ws = dmx.abnrlib.workspace.Workspace(wsroot)
        cfobj = ws.get_config_factory_object()
        retlist = cfobj.search(project='^{}$'.format(project), variant='^{}$'.format(variant), libtype='^{}$'.format(libtype))
        return retlist[0].library


    def report_turnin_result(self, stage_repo, mock=True):
        ''' 
        if PASS:
            return [0, message]
        if FAIL:
            return [1, message]
        '''
        retcode = 0
        retmsg = ''
        if mock:
            logfile = os.path.join(stage_repo, 'MockTurnin', 'GATEKEEPER', 'mockturnin.log')
            cmd = 'grep "Mockturnin passed." {}'.format(logfile)
            exitcode, _, _ = self.__runcmd(cmd)
            if not exitcode:
                retcode = 0
                retmsg = ''' MockTurnin PASS: '''
            else:
                retcode = 1
                retmsg = ''' MockTurnin FAIL: You can refer to the logfile for the run at {}'''.format(logfile)

        else:
            _, stdout, _ = self.__runcmd('cat {}'.format(self.get_turninid_logfile(stage_repo)))
            tid = stdout.strip()
            retcode = self.run_turnininfo(tid)
            if not retcode:
                retmsg = ''' Turnin PASS: '''
            else:
                retmsg = ''' Turnin FAIL: You can review the errors from http://goto/psg_gkweb (turnin id = {}) '''.format(tid)

        return [retcode, retmsg]

    
    def run_turnininfo(self, tid, interval=60):
        ''' keep looping `turnininfo` until turnin job has completed.

        Return 0 if status is pass, else 1.
        '''
        passlist = ['accepted', 'released']
        faillist = ['rejected', 'killed', 'cancelled', 'failed']
        cmd = """ssh localhost -q '/p/hdk/bin/cth_psetup -p psg -cfg KM5A0P00_FE_RC.cth -cmd "turnininfo -format json -id {}"' """.format(tid)
        
        while True:
            exitcode, stdout, stderr = self.__runcmd(cmd)
           
            m = re.search('"status" : "([^"]+)"', stdout+stderr)
            if not m:
                return 1
            if m.group(1) in passlist:
                return 0
            elif m.group(1) in faillist:
                return 1

            time.sleep(int(interval))


    def run_turnin(self, repopath, proj, cluster, stepping='a0', mock=True):
        if mock:
            ### mockturnin can not start feeder in vnc, thus, we can not use ssh. We need to use arc submit
            ### Alternatively, we could ssh to rsync.zsc7.intel.com ????
            #cmd = """arc submit --no-inherit --watch -- '/p/hdk/bin/cth_psetup -p psg -cfg KM5A0P00_FE_RC.cth -w {} -cmd "turnin -proj {} -c {} -s {} -d -mock -rmmock"' """.format(repopath, proj, cluster, stepping)
            server = self.gkserver
            if self.site == 'png':
                server = 'ppgcron03.png.intel.com'
                server = 'rsync.png.intel.com'
            cmd = """ssh {} -q '/p/hdk/bin/cth_psetup -p psg -cfg KM5A0P00_FE_RC.cth -w {} -cmd "turnin -proj {} -c {} -s {} -d -mock -rmmock"' """.format(server, repopath, proj, cluster, stepping)
        else:
            turnin_id_file = self.get_turninid_logfile(repopath)
            cmd = """ssh localhost -q '/p/hdk/bin/cth_psetup -p psg -cfg KM5A0P00_FE_RC.cth -w {} -cmd "turnin -proj {} -c {} -s {} -d -save_id {} -release_when_accepted "' """.format(repopath, proj, cluster, stepping, turnin_id_file)
        exitcode, stdout, stderr = self.__runcmd(cmd)
        return [exitcode, stdout, stderr]

    def get_turninid_logfile(self, repopath):
        return os.path.join(repopath, '.turninid')

    def prepare_turnin_run_for_icm(self, wsroot, project, variant, libtype, library, thread=None, milestone=None, tag=''):
        ''' https://wiki.ith.intel.com/pages/viewpage.action?pageId=2442526927

        1. Create staging git repo
            > git clone $GIT_MASTER $STAGE  
        2. copy files from $ICMWS/$variant/$libtype/... to $STAGE
            > rsync -avxzl --delete --remove-source-files --exclude=.git --exclude='.icm*'  $ICMWS/$variant/$libtype/   $STAGE/
        3. copy GkUtil.cfg file to $STAGE
            >cp $gkutil_config_file $STAGE/cfg/gk/GkUtils.cfg
        4. commit everything
            > cd $STAGE
            > git add .; git commit

        return [$PVLLID, $STAGE ]
        '''
        pvllid = self.git.get_id_from_pvll(project, variant, libtype, library)
        if not pvllid:
            raise Exception("Invalid project/variant/libtype/library ({}/{}/{}/{})!".format(project, variant, libtype, library))

        srcdir = os.path.join(wsroot, variant, libtype)
        if not os.path.isdir(srcdir):
            raise Exception("Source folder not found: {}!".format(srcdir))

        cfgfile = self.get_gkutil_cfg_file(thread, milestone)
        if not cfgfile:
            raise Exception("Can not find GkUtil cfg file: {}!".format(cfgfile))

        master_repo = self.git.get_master_git_repo_path(idtag=pvllid)
        '''
        if not os.path.isdir(master_repo):
            raise Exception("Can not find master git repo: {}!".format(master_repo))
        '''

        ### Start Work
        stagedir = os.path.join(wsroot, '.gkmock')
        self.__runcmd('mkdir -p {}'.format(stagedir))
        stage = tempfile.mkdtemp(dir=stagedir)

        ### git clone
        server = None
        if self.site == 'png':
            server = self.server
        self.git.git_clone(master_repo, stage, server=server)

        ### rsync data from srcdir to $STAGE
        LOGGER.info("srcdir:{}, stage:{}".format(srcdir, stage))
        self.git.rsync_data_from_icm_to_git(srcdir, stage)


        ### copy GkUtil to $STAGE
        cfg_dst_file = os.path.join(stage, 'cfg', 'gk', 'GkUtils.cfg')
        cmd = "mkdir -p {}/cfg/gk".format(stage)
        self.__runcmd(cmd)
        cmd = "cp -rf {} {}".format(cfgfile, cfg_dst_file)
        self.__runcmd(cmd)

        ### Touch unique file, so that turnin gets run everytime
        ### (turnin will reject if there is no changes found)
        uniqfile = os.path.join(stage, '.turnin.date')
        self.__runcmd('date >> {}'.format(uniqfile))

        ### git add git commit
        with dmx.utillib.contextmgr.cd(stage):
            self.git.git_add()
            self.git.git_commit(msg="prepare_turnun_run_for_dmx")

            ### If tag is given, create tag
            if tag:
                self.git.git_addtag(tagname=tag, msg=tag)

        return [pvllid, stage]

    
    def get_gk_cfg_dir(self):
        ### /p/hdk/pu_tu/prd/gatekeeper_configs/psg/
        return os.getenv("GK_CONFIG_DIR", '/p/hdk/pu_tu/prd/gatekeeper_configs/psg/latest')

    def get_turnin_exe(self):
        return '/p/hdk/pu_tu/prd/gatekeeper4/master/4.50.06_22ww37a/bin/turnin'

    def get_gkutil_cfg_file(self, thread, milestone):
        ''' return the fullpath of the GkUtils.*.cfg file

        if thread, milestone is given:
            return $GK_CONFIG_DIR/cfg/gk/GkUtils.<thread>.<milestone>.cfg
        if thread and milestone == None:
            return $GK_CONFIG_DIR/cfg/gk/GkUtils.cfg
        if the file does not exist:
            return None
        '''
        gk_cfg_dir = self.get_gk_cfg_dir()
        if not thread and not milestone:
            filepath = os.path.join(gk_cfg_dir, 'cfg', 'gk', 'GkUtils.cfg')
        else:
            filepath = os.path.join(gk_cfg_dir, 'cfg', 'gk', 'GkUtils.{}.{}.cfg'.format(thread, milestone))
        LOGGER.debug("Finding gkutils cfg file: {}".format(filepath))
        if os.path.isfile(filepath):
            return filepath
        else:
            return None
      

    def change_repo_group(self, group, repopath):
        ''' change the group of git_repo '''
        if not self.is_path_git_repo(repopath):
            LOGGER.error("repopath: {} is not a git_repo. Aborting !".format(repopath))
            return 1

        cmd = "/p/psg/da/infra/admin/setuid/ssh_psgcthadm localhost -q 'stodfs chgrp --cell sc --options {} --path {}'".format(group, repopath)
        os.system(cmd)
      
      
    def create_branch(self, cluster, step, branch, fromrev=None):
        ''' Create new branch for git repo 
        Native Command: /p/hdk/pu_tu/prd/gatekeeper4/master/4.50.06_22ww37a/bin/turnin -cfgdir /p/hdk/pu_tu/prd/gatekeeper_configs/psg/latest/ -c liotest3 -s a0 -create_branch 0.8 40534b6422808dafa9597a14a328a9296dc5c0fc
        '''
        ### We do not need to worry about ssh_as_psgcthadm because our standalone cmx/bin/update_gk_repo_and_config wrapper will do the magic.
        cmd = '{} -cfgdir {} -c {} -s {} -create_branch {}'.format(self.get_turnin_exe(), self.get_gk_cfg_dir(), cluster, step, branch)
        if fromrev:
            cmd += ' {}'.format(fromrev)
        os.system(cmd)


    def list_branches(self, cluster, step):
        ''' list all branches '''
        cmd = '{} -cfgdir {} -c {} -s {} -list_branches'.format(self.get_turnin_exe(), self.get_gk_cfg_dir(), cluster, step)
        os.system(cmd)


    def is_path_git_repo(self, repopath):
        ''' check if the given path is a git_repo '''
        retcode = os.system('env GIT_DIR={} git rev-parse --git-dir'.format(repopath))
        if not retcode:
            return True
        return False

    def __runcmd(self, cmd):
        exitcode, stdout, stderr = dmx.utillib.utils.run_command(cmd)
        LOGGER.debug("cmd: {}\n- exitcode:{}\n- stdout: {}\n- stderr: {}\n".format(cmd, exitcode, stdout, stderr))
        return exitcode, stdout, stderr

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)

    pprint(x)
