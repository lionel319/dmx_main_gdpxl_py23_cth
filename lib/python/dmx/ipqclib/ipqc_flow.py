#!/usr/bin/env python
""" Flow engine for ipqc run-all sub-command
    The FlowFlat object contains:
        --> build function to prepare environment, build data, scripts
            The main script ipqc.py contains the targets (checkers)
        --> run function to run the flow. Run the ipqc.py script.

"""
from __future__ import print_function
import os
import re
import multiprocessing
import time
import glob
from dmx.ipqclib.utils import run_command, file_accessible, remove_file
from dmx.ipqclib.log import uiInfo, uiError, uiDebug
from dmx.ipqclib.settings import _ARC_PREFIX, _ARC_URL_PICE, _NA_MILESTONE
from dmx.utillib.utils import quotify
import grp 

_LSF_STATUS = ['done', 'passed', 'failed', 'killed', 'collected', 'error', 'expired']

#####################################################################
# IPQC Flow checkers execution
# For each IP create an ipqc.py script executing checkers for this IP
#####################################################################
class FlowFlat(object):
    """ Flow object
    """
    def __init__(self, ipqc):
        self.ipqc = ipqc
        (self._ip_targets, self._checker_targets, self._targets) = self.get_targets()
        self.jobname = 'ipqc_top_' + self.ipqc.ip.name
        self.jobfile = os.path.join(os.path.dirname(self.ipqc.ip.workdir), self.jobname+'.job')
        self.executable = os.path.join(self.ipqc.ip.workdir, "ipqc.py")
        self.dmx_executable = os.path.join(os.path.dirname(__file__)+'/../../../../bin/_dmxsetupclean')
        self.logfile = os.path.join(self.ipqc.ip.workdir, 'ipqc.log')
        self._jobid = None
        self.jobfile_checkers = os.path.join(os.path.dirname(self.ipqc.ip.workdir), "ipqc_top_checkers.job")
        self.jobfile_da_checkers = os.path.join(os.path.dirname(self.ipqc.ip.workdir), "ipqc_top_da_checkers.job")
        self.all_custom_runme = self.get_custom_runme()
        remove_file(self.jobfile_da_checkers)
        remove_file(self.jobfile_checkers)
        self.setenvcmd = self.get_setenv_cmd()

        self._perip = {}

    def get_setenv_cmd(self):
        ### This is needed for StandAlone dmx
        needed_envvar = ['DMXDATA_ROOT', 'DB_FAMILY']
        setenvcmd = ''
        for ev in needed_envvar:
            evval = os.getenv(ev, "")
            if not evval:
                raise("{} env var not set!".format(ev))
            setenvcmd = setenvcmd + 'setenv {} {};'.format(ev, evval)
        return setenvcmd

    ##################################
    # Get all custom runme in the workspace 
    ##################################
    def get_custom_runme(self):
        ret = {}
        custom_runme_files = glob.glob(self.ipqc.ip._ws.path+'/*/*/ipqc.runme')
        for ea_runme in custom_runme_files:
            match = re.search(self.ipqc.ip._ws.path+'/(\S+)/(\S+)/ipqc.runme', ea_runme)
            if match:
                match_ip = match.group(1)
                match_deliverable = match.group(2)
                ret[match_ip, match_deliverable] = ea_runme
        return ret

    ##################################
    # Targets for IPQC are the IPs
    ##################################
    def get_targets(self):
        """Get the targets/checkers"""
        ip_targets = []
        targets = []
        checker_targets = []

        for sub_ipqc in self.ipqc.hierarchy + [self.ipqc]:
            if sub_ipqc.ip.name in self.ipqc.exclude_ip:
                continue

            if (sub_ipqc.ip.is_immutable) and (sub_ipqc.requalify is False):
                continue

            ip_targets.append(sub_ipqc)

            for cell in sub_ipqc.ip.topcells:

                # if deliverable option is invoked run the checkers only for this deliverable
                for deliverable in cell.deliverables:
                    if (deliverable.is_unneeded) or (deliverable.status == _NA_MILESTONE):
                        continue

                    for checker in deliverable.checkers:
                        if checker.has_checker_execution() and checker._milestone in checker.milestones and not checker.is_waived(cell.name, \
                                        sub_ipqc.ip.config) and not checker.is_skipped(cell.name, sub_ipqc.ip.config) and not checker._skipped is True:
                            target = re.sub('-', '_', checker.checker_id)
                            target = '{}_{}_{}_{}' .format(sub_ipqc.ip.name, cell.name, \
                                    deliverable.name, target)
                            targets.append(target)
                            checker_targets.append(checker)

        return (ip_targets, checker_targets, targets)


    def get_code_and_out_jobid(self, code, out):
        jobid = ''
        if code != 0:
            uiError(out)

        '''
        with open(self.jobfile, 'r') as fid:
            content = fid.read()
            self._jobid = content.split()[0]
        '''
        ### EXtract The arc-job-id
        '''
        A successful arc submission looks like this:

        13975259
        Job <13306404> is submitted to queue <batch>.
        '''
        results = out.splitlines()
        jobid = results[0]

        if not jobid.isdigit():
            errstr = '''Problem Dispatching Job.
            exitcode: {}
            stdout: {}
            '''.format(code, out)
            uiError(out)
        return jobid

    ##################################
    # Submit checkers execution on ARC
    ##################################
    def run(self):
        """Execute the flow."""
        uiInfo("")
        uiInfo("-------------------------")
        uiInfo("Running Tests Flow       ")
        uiInfo("-------------------------")
        uiInfo("")
        all_jobid_runme = []
        command = "{} -t name={} -- \'{} {} {} | tee {}\' | head -1 | tee {}" .format(_ARC_PREFIX, \
                self.jobname, self.setenvcmd, self.dmx_executable, self.executable, self.logfile, self.jobfile)
        uiDebug("Running {}" .format(command))
        uiDebug("Running dmxexecutable {}" .format(self.dmx_executable))
        (code, out) = run_command('{}' .format(command))
        jobid_default = self.get_code_and_out_jobid(code, out)
        self._jobid = jobid_default
        

        cwd = os.getcwd()
        for sub_ipqc in sorted(self._ip_targets, key=lambda x: x.ipname): 
            for deliverable in sub_ipqc.deliverables:
               # remove audit file if applicable
                runme = self.all_custom_runme.get((sub_ipqc.ip.name, deliverable))
                if runme:
                    runme_dir = os.path.dirname(runme)
                    command = "{} -t name={} -- \'{} cd {}; sh {} | tee {}\' | head -1 | tee {}" .format(_ARC_PREFIX,  \
                            self.jobname, self.setenvcmd, runme_dir, runme, self.logfile, self.jobfile)
                    (code, out) = run_command('{}' .format(command))
                    jobid_runme = self.get_code_and_out_jobid(code, out)
                    all_jobid_runme.append(jobid_runme)

        os.chdir(cwd)
        all_jobid = all_jobid_runme + [jobid_default]

        for ea_jobid in all_jobid:
            uiInfo("firefox {}{}" .format(_ARC_URL_PICE, ea_jobid))

        ### Loop for 10 times on 'arc wait' command, just to be very sure, because sometimes, 
        ### the 'arc wait' command might get killed by some IT policies.
        jobtreecmd = "curl http://psg-sc-arc-web01.sc.intel.com/arc/api/jobtree/{}/ | jq 'map({{id,status}})'".format(self._jobid)
        uiDebug("To see your job has reached which stage, run the following command:- {}".format(jobtreecmd))
        cmd = 'arc wait {}'.format(' '.join(all_jobid))
        for i in range(1, 11):
            uiDebug("arc wait ({}): {}".format(i, cmd))
            os.system(cmd)
            time.sleep(10)


        '''
        status = ''
        while status not in _LSF_STATUS:
            (code, out) = run_command('arc job {} --status' .format(self._jobid))
            status = out.split()[0]

        # wait for jobs checkers
        uiInfo("Waiting checkers jobs submission")
        jobs_dict = {}

        if not file_accessible(os.path.join(os.path.dirname(self.ipqc.ip.workdir), \
                        "ipqc_top_checkers.job"), os.R_OK):
            return

        with open(os.path.join(os.path.dirname(self.ipqc.ip.workdir), "ipqc_top_checkers.job"), \
                'r') as fid:
            content = fid.read()
            jobsid = content.split()

            for jobid in jobsid:
                status = ''

                while status not in _LSF_STATUS:
                    (code, out) = run_command('arc job {} --status' .format(jobid))
                    status = out.split()[0]

                if not jobid in jobs_dict.keys():
                    cmd = 'arc job-query parent={} >> {}' .format(jobid, self.jobfile_da_checkers)
                    run_command(cmd)
                    jobs_dict[jobid] = 1


        uiInfo("End checkers jobs submission")

        # wait for jobs DA checkers
        uiInfo("Waiting da checkers jobs submission")
        with open(os.path.join(os.path.dirname(self.ipqc.ip.workdir), self.jobfile_da_checkers), \
                'r') as fid:
            content = fid.read()
            jobsid = content.split()

            for jobid in jobsid:
                status = ''
                while status not in _LSF_STATUS:
                    (code, out) = run_command('arc job {} --status' .format(jobid))
                    status = out.split()[0]
        uiInfo("End da checkers jobs submission")
        '''

    ###################################
    # Setup task
    # task requires environment setup:
    #   --> cd into collateral
    ###################################
    def _setup(self, sub_ipqc, target, fid, cellname, deliverable, checker, ran_by_cell=''): #pylint: disable=no-self-use

        print("def task_setup_{}():" .format(target), file=fid)
        #####################################################
        # FB503671
        # https://fogbugz.altera.com/default.asp?503671
        # cd into cdc/topcell otherwise audit generation fail
        #####################################################
        if deliverable.name == 'cdc':
            cd_cmd = 'cd {}' .format(os.path.join(sub_ipqc.ip.workspace.path, sub_ipqc.ip.name, deliverable.name, cellname))
        else:
            cd_cmd = 'cd {}' .format(os.path.join(sub_ipqc.ip.workspace.path, sub_ipqc.ip.name, deliverable.name))

        checker_cmd = checker.get_command(cellname, sub_ipqc.ip.config)

        if ran_by_cell:
            checker_cmd = 'echo Skip_this_PerIp_job_as_it_has_been_run_by_{}_{}'.format(ran_by_cell, checker.checker_id)

        cmd = "'echo \"{}\" > {}; echo \"{}\" >> {}'" .format(cd_cmd, checker.logfile, checker_cmd, checker.logfile)

        cmd = """ echo {} > {}; echo {} >> {} """.format(quotify(cd_cmd), checker.logfile, quotify(checker_cmd), checker.logfile)
        print("\treturn { \\", file=fid)
        print("\t\t'actions': [{}] \\" .format(quotify(cmd)), file=fid)
        print("\t}", file=fid)
        print("\n", file=fid)

        return cd_cmd


    ##################################
    # Build flow ipqc.py script
    ##################################
    def build(self):
        """Build the flow environment, scripts, ..."""
        
        with open(self.executable, "w") as fid:
            print('#!/usr/bin/env python', file=fid)
            print("\n", file=fid)

            print("DOIT_CONFIG = {", file=fid)
            print("\t'num_process': {}," .format(multiprocessing.cpu_count()*2), file=fid)
            print("\t'backend': 'json',", file=fid)
            print("\t'dep_file': 'doit-db.json',", file=fid)
            print("#\t'default_tasks': {}," .format(self._targets), file=fid)
            print("\t'continue': True,", file=fid)
            print("\t'verbosity': 2", file=fid)
            print("}", file=fid)
            print("\n", file=fid)

            for sub_ipqc in sorted(self._ip_targets, key=lambda x: x.ipname):

                for cell in sub_ipqc.ip.topcells:

                    for deliverable in cell.deliverables:

                        for checker in deliverable.checkers:

                            if not checker in self._checker_targets:
                                continue

                            # remove audit file if applicable
                            if checker.has_audit_verification():
                                remove_file(checker.audit.get_file(cell.name))

                            ### If there are any custom runme file for the deliverable, do not create any checker on that 
                            if self.all_custom_runme.get((sub_ipqc.ip.name, deliverable.name), None):
                                uiInfo('Skip: {}/{}/{}/{}. Contain custom runme file : {}'.format(sub_ipqc.ip.name, deliverable, cell, checker.checker_id, self.all_custom_runme.get((sub_ipqc.ip.name, deliverable.name))))
                                continue

                            cellname = ''
                            if checker.is_run_perip():
                                cellname = self.has_checker_been_registered_to_task(sub_ipqc.ip.name, checker.checker_id)
                                if not cellname:
                                    self.register_perip_checker_to_dict(sub_ipqc.ip.name, checker.checker_id, cell.name)
                            if cellname:
                                checker_cmd = 'echo Skip_this_PerIp_job_as_it_has_been_run_by_{}_{}'.format(cellname, checker.checker_id)
                            else:
                                checker_cmd = checker.get_command(cell.name, sub_ipqc.ip.config)

                            target = re.sub('-', '_', checker.checker_id)
                            target = '{}_{}_{}_{}' .format(sub_ipqc.ip.name, cell.name, deliverable.name, target)
                            cmd = self._setup(sub_ipqc, target, fid, cell.name, deliverable, checker, ran_by_cell=cellname)

                            jobname = sub_ipqc.ip.name + '.' + cell.name + '.' + deliverable.name + '.' + checker.checker_id
                            cfname = sub_ipqc.ip.name + '_' + cell.name + '_' + deliverable.name + '_' + checker.checker_id + '_' + checker.uid
                            if os.environ.get('CTH_SETUP_CMD'):
                                arc_prefix = "arc submit --no-inherit -t name={} nb_name={} {} " .format(jobname, cfname, checker.get_arcparam(cell.name, sub_ipqc.ip.config))
                            else:
                                arc_prefix = "{} -t name={} nb_name={} {} " .format(_ARC_PREFIX, jobname, cfname, checker.get_arcparam(cell.name, sub_ipqc.ip.config))
                            if checker.has_dependencies():
                                dep_checker = deliverable.get_checker(dependency=checker.dependencies) #pylint: disable=line-too-long
                                dependent_job = sub_ipqc.ip.name + '_' + cell.name + '_' + deliverable.name + '_' + checker.dependencies + '_' + dep_checker.uid

                                arc_prefix = arc_prefix + " nb_depends_on='" + dependent_job + "[OnFinish]'"
                            arc_prefix = arc_prefix + " -- "

                            basecmd = """{}; {} """.format(cmd, checker_cmd)
                            run_cmd = """ {} {} | head -1 | tee -a {} """ .format(arc_prefix, quotify(basecmd), self.jobfile_checkers)
                            #run_cmd = "{} '{}; {}' | head -1 | tee -a {}" .format(arc_prefix, cmd, checker.get_command(cell.name, sub_ipqc.ip.config), self.jobfile_checkers)

                            print("def task_{}():" .format(target), file=fid)
                            print("\treturn { \\", file=fid)
                            print("""\t\t'actions': [{}], \\""".format(quotify(run_cmd)), file=fid)
                            print("\t\t'setup': ['setup_{}'], \\" .format(target), file=fid)

                            if checker.has_dependencies():
                                print("\t\t'task_dep':[\"{}_{}_{}_{}\"], \\" .format(\
                                            sub_ipqc.ip.name, cell.name, deliverable.name, \
                                            re.sub('-', '_', checker.dependencies)), file=fid)
                            print("\t\t'verbosity' : 2}", file=fid)
                            print("\n", file=fid)

            print("if __name__ == \'__main__\':", file=fid)
            print("\tfrom dmx.ipqclib.flow import doit", file=fid)
            print("\tdoit.run(globals())", file=fid)

            fid.close()
            # Make ipqc.py executable
            os.chmod(self.executable, 0o775)

            uiDebug("self._perip: {}".format(self._perip))

    def has_checker_been_registered_to_task(self, ipname, checkerid):
        cellname = ''
        if ipname in self._perip:
            if checkerid in self._perip[ipname]:
                cellname = self._perip[ipname][checkerid]
        return cellname

    def register_perip_checker_to_dict(self, ipname, checkerid, cellname):
        if ipname not in self._perip:
            self._perip[ipname] = {}
        self._perip[ipname][checkerid] = cellname



    @property
    def jobid(self):
        """ARC job ID of the flow"""
        return self._jobid
