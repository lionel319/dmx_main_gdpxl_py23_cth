### http://pg-rdjira:8080/browse/DI-1155
### Port all bamboo's regression to 'makefile' callable
### The idea is that, no matter what regression platform we are using in the future
### we are still able to decoupled easily and directing plug the makefile regression
### into that new system by just calling 'make run'

### +------------+
### | How To Run |
### +------------+
### 1. If you want to submit it, and receive email notification on the results:-
###    (this is good for cronjobs)
###     > $ make -f regression.makefile DEVICE=FM8 TYPE=unittest   VER=main   run
###     > $ make -f regression.makefile DEVICE=WHR TYPE=systemtest VER=9.1    run
###
### 2. If you want to submit it, and get a return exit code on the status after completion:-
###    (this is suitable for integrating as part of a pre-deployment)
###     > $ make -f regression.makefile DEVICE=FM8 TYPE=unittest   VER=8.3  all_unittest
###     > $ make -f regression.makefile DEVICE=WHR TYPE=systemtest VER=9.0  all_systemtest
###
### 3. If you want to run regression on an rc project/bundle (result will be sent thru email):-
###    (this is meant to qualify the rc project/bundle before its OFFICIAL release.)
###    (this should be ran as a cronjob)
###     > $ make -f regression.makefile DEVICE=FM8  ARCRES=project/falcon/fm8dot2/4.0/phys/rc  run_rc
###     > $ make -f regression.makefile DEVICE=FM6  ARCRES=project/falcon/fm8dot2/4.0/phys/rc  run_rc 
###     > $ make -f regression.makefile DEVICE=WHR  ARCRES=project/falcon/fm8dot2/4.0/phys/rc  run_rc 

### +-------+
### | Notes |
### +-------+
### All tests which DO NOT modify icm database in anyway can be submitted in parallel in any combination.
### EG:- All these tests(TYPE=unittest + rc_bundle_regression) can be submitted together at the same time, 
###     > $ make -f regression.makefile DEVICE=FM8 TYPE=unittest VER=main   run
###     > $ make -f regression.makefile DEVICE=FM6 TYPE=unittest VER=9.0    run
###     > $ make -f regression.makefile DEVICE=WHR TYPE=unittest VER=8.3    run
###     > $ make -f regression.makefile DEVICE=WHR TYPE=unittest VER=9.1    all_unittest
###     > $ make -f regression.makefile DEVICE=FM8 TYPE=unittest VER=9.1    all_unittest
###     > $ make -f regression.makefile DEVICE=FM6                          run_rc
###     > $ make -f regression.makefile DEVICE=WHR                          run_rc

###
### TYPE=systemtest are tests that DOES modify the content in icm database.
### This means these tests might run into conflicting state when run in parallel, 
### and thus, they should never be run overlapping each other.
### EG:- these tests SHOULD always be submitted only after the previous on has completed.
###     > $ make -f regression.makefile  DEVICE=FM8 TYPE=systemtest VER=main   run
###     > $ make -f regression.makefile  DEVICE=FM4 TYPE=systemtest VER=9.0    run
###     > $ make -f regression.makefile  DEVICE=WHR TYPE=systemtest VER=8.3    all_systemtest



### +-------------------------------------------------------------+
### | Support For Creatin a new regression suite For A New DEVICE |
### +-------------------------------------------------------------+
### Notes:-
### - All regression are ran as psginfraadm
### - All regressions will ssh to $(SERVER), then 'arc submit'
### - All regressions are ran in SC
###
### for a new project/bundle
### 1. Each regression contains 2 COMPULSORY variables
###    - DEVICE (FM8/FM6/WHR/...)
###    - TYPE (unittest/systemtest)
###    - VER (version of dmx to be tested)
###
### 2. 2 new p4 client needs to be create when a new $(DEVICE) is introduced.
###    - A new $(DEVICE) is introduced when a new project/bundle for that $(DEVICE) is created
###    - You can create the new p4 clients by taking these 2 as template:-
###      > psginfraadm_dmx_unittest_FM8
###      > psginfraadm_dmx_systemtest_FM8
###
### 3. Sample of client spec
###
### a. The sample of the client spec (psginfraadm_dmx_unittest_FM8) looks like this:-
###      Root:   /nfs/site/disks/da_infra_1/users/psginfraadm/regressions/psginfraadm_dmx_unittest_FM8
###      View:
###        //depot/da/infra/dmx/rel/... //psginfraadm_dmx_unittest_FM8/...
###        //depot/da/infra/dmx/main/... //psginfraadm_dmx_unittest_FM8/main/...
###      (remove the 'Host:' line so that it can be ran from any host)
###
### b. The sample of the client spec (psginfraadm_dmx_systemtest_FM8) looks like this:-
###      Root:   /nfs/site/disks/da_infra_1/users/psginfraadm/regressions/psginfraadm_dmx_systemtest_FM8
###      View:
###        //depot/da/infra/dmx/rel/... //psginfraadm_dmx_systemtest_FM8/...
###        //depot/da/infra/dmx/main/... //psginfraadm_dmx_systemtest_FM8/main/...
###      (remove the 'Host:' line so that it can be ran from any host)
###
### 4. Now go and modify the part in this makefile which defines the ARCRES variable based on DEVICE. (search for 'ARCRESMAP')
###    - this section should also give you the info of which are the currently support DEVICE's tests.
###  
### 5. Done. We are now good to go !!!!

### +================================================+
### | How to do 'icm_login' for psginfraadm headless |
### +================================================+
### There are times when something happens (server down / license expired / etc ...)
### the psginfraadm headless needs to be login using icm_login.
### Problem is we don't have the password for psginfraadm because it is a headless, and thus,
### there is no way to run 'icm_ligin'. Here's the solution:-
### (http://pg-rdconfluence:8090/display/~yltan/2017/02/21/How+To+Create+ICM+Ticket+Without+The+Need+Of+User+Password)
### 1. su as psginfraadm
###    - $sudo su - psginfraadm
### 2. login to icm as icmAdmin
###    - $icmp4 -u icmAdmin login -a 
###    - (key in icmAdmin password)
### 3. login to icm (by using icmAdmin) as psginfraadm
###    - $icmp4 -u icmAdmin login -a psginfraadm
###    - (no password needed)

SERVER := sjdacron.sc
SSH := /p/psg/da/infra/admin/setuid/tnr_ssh -q $(SERVER)
ARC := /p/psg/ctools/arc/bin/arc 
ARCOPT := -t --watch
ARCRES := project/falcon/branch/fm8dot2main/4.0/phys/rc
#ICMDEVRES := ic_manage_gdp/dev/35740
#ICMDEVRES := ic_manage_gdp/dev/38718
ICMDEVRES := ic_manage_gdp/dev/40058
DEVICE := FM8
VER := main
TYPE := unittest
CLIENT := psginfraadm_dmx_$(TYPE)_$(DEVICE)
REGDIR := /nfs/site/disks/da_infra_1/users/psginfraadm/regressions/$(CLIENT)/$(VER)
DATADIR := /nfs/site/disks/da_infra_1/users/psginfraadm/dmxdata_ciw/main/data
REPORTDIR := /nfs/site/disks/da_infra_1/users/psginfraadm/regressions_report/$(CLIENT)/$(VER)/xunit-reports
SANDBOX := $(REGDIR)/sandbox
SANDBOXRES := dmx/$(CLIENT)

REGMAKE := $(MAKE) -f regression.makefile
SETENVDMXDATA := setenv DMXDATA_ROOT $(DATADIR)
SETENVSYSTEST := setenv DMX_FAMILY_LOADER family_systest.json


RECIPIENTS := lionelta,kwlim,srabadan,nbaklits
JOBNAME := $(TYPE)/$(DEVICE)/$(VER)
EMAIL_PASS_CMD = (echo https://$$ARC_BROWSE_HOST/arc/dashboard/reports/show_job/$$ARC_JOB_ID && tail -n 222 $$ARC_JOB_STORAGE/stderr.txt) | mail -s PASS:$(JOBNAME) $(RECIPIENTS)
EMAIL_FAIL_CMD = (echo https://$$ARC_BROWSE_HOST/arc/dashboard/reports/show_job/$$ARC_JOB_ID && tail -n 222 $$ARC_JOB_STORAGE/stderr.txt) | mail -s FAIL:$(JOBNAME) $(RECIPIENTS)


ARCRESFM8 := project/falcon/branch/fm8dot2main/rc
ARCRESFM6 := project/falcon/branch/fm6dot2main/rc
ARCRESWHR := project/whr/branch/whrmain/rc
ARCRESGDR := project/gdr/branch/gdrmain/rc
ARCRESRNR := project/rnr/branch/rnrmain/rc

### Currently Support DEVICE tests (ARCRESMAP)
ifeq ($(DEVICE), FM8)
	ARCRES := $(ARCRESFM8)
else ifeq ($(DEVICE), FM6)
	ARCRES := $(ARCRESFM6)
else ifeq ($(DEVICE), WHR)
	ARCRES := $(ARCRESWHR)
else ifeq ($(DEVICE), GDR)
	ARCRES := $(ARCRESGDR)
else ifeq ($(DEVICE), RNR)
	ARCRES := $(ARCRESRNR)
else
	ARCRES := 
endif

ifeq ($(ARCRES),)
precheck:
	@echo "=============================="
	@echo "DEVICE: $(DEVICE)"
	@echo "TYPE: $(TYPE)"
	@echo "VER: $(VER)"
	@echo "=============================="
	@echo "ERROR: DEVICE not supported."
	@exit 1
else
precheck:
	@echo "=============================="
	@echo "DEVICE: $(DEVICE)"
	@echo "TYPE: $(TYPE)"
	@echo "VER: $(VER)"
	@echo "=============================="
	@echo "PASS: All variables available."

endif
.PHONY: precheck

test:
	$(eval DMXVER := $(shell arc resource-info project/whr/branch/whrmain/rc | grep "resources :" | awk '{print $$3}' | xargs arc resource | grep "resources :" | awk '{print $$3}' | perl -ne '/\b(dmx\/[0-9.]+)\b/; print $$1' ))
	$(eval DMXDATAVER := $(shell arc resource-info project/whr/branch/whrmain/rc | grep "resources :" | awk '{print $$3}' | xargs arc resource | grep "resources :" | awk '{print $$3}' | perl -ne '/\b(dmxdata\/[0-9.]+)\b/; print $$1' ))
	echo $(DMXVER)
	echo $(DMXDATAVER)


### This target will always return True (0) because of the '&&' and '||'
### For integrating the regression prior to releasing to /p/psg, 
### do not call 'run'. Call 'all_unittest' and 'all_systemtest' directly.
run:
	$(ARC) submit name=$(JOBNAME) -- '$(REGMAKE) all_$(TYPE) DEVICE=$(DEVICE) VER=$(VER) TYPE=$(TYPE) SERVER=$(SERVER) && ($(EMAIL_PASS_CMD)) || ($(EMAIL_FAIL_CMD))'
.PHONY: run

# This target is meant to be ran for all the rc bundles
# How To Run (these lines should actually be in a crontab):-
# - make -f regression.makefile DEVICE=FM8 run_rc
run_rc: JOBNAME := $(ARCRES)
run_rc:
	$(ARC) submit $(ARCRES) name=$(JOBNAME) -- '$(REGMAKE) rc_bundle_regression ARCRES=$(ARCRES) DEVICE=$(DEVICE) && ($(EMAIL_PASS_CMD)) || ($(EMAIL_FAIL_CMD))'
.PHONY: run_rc


all_unittest:
	$(REGMAKE) precheck
	$(REGMAKE) cleanup_and_sync
	$(REGMAKE) compile
	$(REGMAKE) gen_docs
	$(REGMAKE) deploy
	$(REGMAKE) unittest_abnr
	$(REGMAKE) systemtest_tnr
	$(REGMAKE) systemtest_ecolib
	$(REGMAKE) systemtest_utillib
	$(REGMAKE) systemtest_testrunner
	#$(REGMAKE) copy_testreports
	$(REGMAKE) create_sandbox_arc_res
	$(REGMAKE) inttest_dmx
	$(REGMAKE) inttest_ecosphere
	$(REGMAKE) inttest_ipqc


all_systemtest:
	$(REGMAKE) precheck
	$(REGMAKE) cleanup_and_sync
	$(REGMAKE) login
	$(REGMAKE) systemtest_abnr
	$(REGMAKE) armortest_fm
	$(REGMAKE) armortest_whr

# This target is meant to be ran for all the rc bundles
# How To Run (these lines should actually be in a crontab):-
# - arc submit -- make -f regression.makefile DEVICE=FM8 rc_bundle_regression
rc_bundle_regression:
	$(eval DMXVER := $(shell arc resource-info $(ARCRES) | grep "resources :" | awk '{print $$3}' | xargs arc resource | grep "resources :" | awk '{print $$3}' | perl -ne '/\bdmx\/([0-9.]+)\b/; print $$1' ))
	$(REGMAKE) unittest_abnr          ARCRES=$(ARCRES)  DEVICE=$(DEVICE) SANDBOX=/p/psg/flows/common/dmx/$(DMXVER)/ SETENVDMXDATA=pwd JOBNAME=$(ARCRES) OPTS=
	$(REGMAKE) systemtest_tnr         ARCRES=$(ARCRES)  DEVICE=$(DEVICE) SANDBOX=/p/psg/flows/common/dmx/$(DMXVER)/ SETENVDMXDATA=pwd JOBNAME=$(ARCRES) OPTS="--exclude=audit_file_generation --exclude=get_audit_file_paths_for_testable_item"
	$(REGMAKE) systemtest_ecolib      ARCRES=$(ARCRES)  DEVICE=$(DEVICE) SANDBOX=/p/psg/flows/common/dmx/$(DMXVER)/ SETENVDMXDATA=pwd JOBNAME=$(ARCRES) OPTS=   
	$(REGMAKE) systemtest_utillib     ARCRES=$(ARCRES)  DEVICE=$(DEVICE) SANDBOX=/p/psg/flows/common/dmx/$(DMXVER)/ SETENVDMXDATA=pwd JOBNAME=$(ARCRES) OPTS=   
	$(REGMAKE) systemtest_testrunner  ARCRES=$(ARCRES)  DEVICE=$(DEVICE) SANDBOX=/p/psg/flows/common/dmx/$(DMXVER)/ SETENVDMXDATA=pwd JOBNAME=$(ARCRES) OPTS=       
	$(REGMAKE) create_sandbox_arc_res ARCRES=$(ARCRES)  DEVICE=$(DEVICE) SANDBOX=/p/psg/flows/common/dmx/$(DMXVER)/ SETENVDMXDATA=pwd JOBNAME=$(ARCRES) OPTS=
	$(REGMAKE) inttest_dmx            ARCRES=$(ARCRES)  DEVICE=$(DEVICE) SANDBOX=/p/psg/flows/common/dmx/$(DMXVER)/ SETENVDMXDATA=pwd JOBNAME=$(ARCRES) OPTS=   
	$(REGMAKE) inttest_ecosphere      ARCRES=$(ARCRES)  DEVICE=$(DEVICE) SANDBOX=/p/psg/flows/common/dmx/$(DMXVER)/ SETENVDMXDATA=pwd JOBNAME=$(ARCRES) OPTS=     
	$(REGMAKE) inttest_ipqc           ARCRES=$(ARCRES)  DEVICE=$(DEVICE) SANDBOX=/p/psg/flows/common/dmx/$(DMXVER)/ SETENVDMXDATA=pwd JOBNAME=$(ARCRES) OPTS=    


cleanup_and_sync:
	$(SSH) 'rm -rf /nfs/site/disks/da_infra_1/users/psginfraadm/dmxdata_ciw/main'
	$(SSH) '$(ARC) submit -t --no-inherit --watch p4 perforce -- \
		"p4 -u psginfraadm -c psginfraadm_dmxdata_ciw sync -f //psginfraadm_dmxdata_ciw/main/..."'

	$(SSH) 'rm -rf $(REGDIR)'
	$(SSH) 'mkdir -p $(REGDIR)'
	$(SSH) '$(ARC) submit -t --no-inherit --watch p4 perforce -- \
		"p4 -u psginfraadm -c $(CLIENT) sync -f $(REGDIR)/..."'

login:
	$(SSH) '$(ARC) submit --interactive --local $(ARCRES)  $(ICMDEVRES)  -- icmp4 -u icmAdmin login -a fmlibrarian'
	$(SSH) '$(ARC) submit --interactive --local $(ARCRES)  $(ICMDEVRES)  -- icmp4 -u icmAdmin login -a icmtester'
	$(SSH) '$(ARC) submit --interactive --local $(ARCRES)  $(ICMDEVRES)  -- icmp4 -u icmAdmin login -a icetnr'
	$(SSH) '$(ARC) submit --interactive --local $(ARCRES)  $(ICMDEVRES)  -- icmp4 -u icmAdmin login -a icmmgr'
	$(SSH) '$(ARC) submit --interactive --local $(ARCRES)  $(ICMDEVRES)  -- icmp4 -u icmAdmin login -a psginfraadm'

compile:
	$(SSH) '$(ARC) submit -t --no-inherit --watch python -- \
		"cd $(REGDIR); make compile;"'

systemtest_abnr: OPTS := --with-xunit --xunit-file=xunit-armosys-reports/abnr_systemtest.xml
systemtest_abnr:
	$(SSH) '$(ARC) submit -t --no-inherit --watch $(ARCRES) $(ICMDEVRES) -- \
		"cd $(REGDIR); $(SETENVDMXDATA); $(SETENVSYSTEST); mkdir -p xunit-armosys-reports; python ./run_tests.py -v -x system_tests/abnr/test*.py $(OPTS) "'

armortest_fm: OPTS := --with-xunit --xunit-file=xunit-armosys-reports/fm8_armortest.xml
armortest_fm:
	$(SSH) '$(ARC) submit -t --no-inherit --watch $(ARCRES) $(ICMDEVRES) -- \
		"cd $(REGDIR); $(SETENVDMXDATA); $(SETENVSYSTEST); mkdir -p xunit-armosys-reports; python ./run_tests.py -v -x armor_tests/fm/test*.py $(OPTS) "'

armortest_whr: OPTS := --with-xunit --xunit-file=xunit-armosys-reports/whr_armortest.xml
armortest_whr:
	$(SSH) '$(ARC) submit -t --no-inherit --watch $(ARCRES) $(ICMDEVRES) -- \
		"cd $(REGDIR); $(SETENVDMXDATA); $(SETENVSYSTEST); mkdir -p xunit-armosys-reports; python ./run_tests.py -v -x armor_tests/whr/test*.py $(OPTS) "'


unittest_abnr: OPTS := --with-coverage --cover-package=dmx.abnrlib --cover-package=dmx.plugins --with-xunit --xunit-file=xunit-reports/abnr_unittest.xml --cover-html --cover-html-dir=test-report-abnr
unittest_abnr:
	$(SSH) '$(ARC) submit -t --no-inherit --watch $(ARCRES) -- \
		"cd $(SANDBOX); $(SETENVDMXDATA); mkdir -p test-report-abnr; mkdir -p xunit-reports; python ./run_tests.py -v unit_tests/abnr/test_*.py $(OPTS)"'

systemtest_tnr: OPTS := --with-coverage --cover-package=dmx.tnrlib --with-xunit --xunit-file=xunit-reports/tnr_systemtest.xml --cover-html --cover-html-dir=test-report-tnrlib
systemtest_tnr:
	$(SSH) '$(ARC) submit -t --no-inherit --watch $(ARCRES) -- \
		"cd $(SANDBOX); $(SETENVDMXDATA); mkdir -p test-report-tnrlib; mkdir -p xunit-reports; python ./run_tests.py -v system_tests/tnr/test_*.py --exe $(OPTS) "'

systemtest_ecolib: OPTS := --with-coverage --cover-package=dmx.ecolib --with-xunit --xunit-file=xunit-reports/ecolib_systemtest.xml --cover-html --cover-html-dir=test-report-ecolib
systemtest_ecolib:
	$(SSH) '$(ARC) submit -t --no-inherit --watch $(ARCRES) $(ICMDEVRES)  -- \
		"setenv DMX_FAMILY_LOADER family_systest.json; cd $(SANDBOX); $(SETENVDMXDATA); mkdir -p test-report-ecolib; mkdir -p xunit-reports; python ./run_tests.py -v system_tests/ecosphere/test_*.py --exe $(OPTS) "'

systemtest_utillib: OPTS := --with-coverage --cover-package=dmx.utillib --with-xunit --xunit-file=xunit-reports/utillib_systemtest.xml --cover-html --cover-html-dir=test-report-utillib
systemtest_utillib:
	$(SSH) '$(ARC) submit -t --no-inherit --watch $(ARCRES) -- \
		"cd $(SANDBOX); $(SETENVDMXDATA); mkdir -p test-report-utillib; mkdir -p xunit-reports; python ./run_tests.py -v system_tests/utillib/test_*.py --exe $(OPTS) "'

systemtest_testrunner:
	$(SSH) '$(ARC) submit -t --no-inherit --watch $(ARCRES) -- \
		"cd $(SANDBOX); $(SETENVDMXDATA); ./system_tests/tnr/manual_pice_test_runner.py -v"'

copy_testreports:
	$(SSH) '$(ARC) submit -t --no-inherit --watch $(ARCRES) -- \
		"cd $(REGDIR); mkdir -p ../../test-reports/`date +%Y%m%d`; cp -rf test-report-tnrlib ../../test-reports/`date +%Y%m%d`/.; cp -rf test-report-abnr ../../test-reports/`date +%Y%m%d`/.; cp -rf test-report-utillib ../../test-reports/`date +%Y%m%d`/.; cp -rf test-report-ecolib ../../test-reports/`date +%Y%m%d`/.; chmod -R 777 ../../test-reports/`date +%Y%m%d`"'

gen_docs:
	$(SSH) '$(ARC) submit -t --no-inherit --watch $(ARCRES) -- \
		"cd $(REGDIR)/doc; make all_doc"'

deploy:
	$(SSH) '$(ARC) submit -t --no-inherit --watch $(ARCRES) -- \
		"cd $(REGDIR); make create_sandbox SANDBOX_DIR=$(SANDBOX)"'

create_sandbox_arc_res:
	$(SSH) '$(ARC) resource-new $(SANDBOXRES) IPQC_ROOT=$(SANDBOX) +PYTHONPATH=$(SANDBOX)/lib/python:$(SANDBOX)/lib/python/dmx/tnrlib DMX_ROOT=$(SANDBOX) DMX_PATH=$(SANDBOX)/bin DMX_TCLLIB=/p/psg/flows/common/icd_cad_tcllib/5/linux64/lib ICD_CAD_QA_TCLLIB=$(SANDBOX)/lib/tcl/dmx/tnrlib DMX_LEGACY=1 DMX_TNRLIB=$(SANDBOX)/lib/tcl/dmx/tnrlib DMX_LIB=$(SANDBOX)/lib/python'

inttest_dmx: OPTS := --with-xunit --xunit-file=xunit-reports/dmx_inttest.xml
inttest_dmx:
	$(SSH) '$(ARC) submit -t --no-inherit --watch $(ARCRES) $(SANDBOXRES) -- \
		"cd $(SANDBOX); $(SETENVDMXDATA); python ./run_tests.py -v integration_tests/dmx/test_*.py --exe $(OPTS) "'

inttest_ecosphere: OPTS := --with-coverage --cover-package=dmx.ecolib --cover-package=dmx.plugins --with-xunit --xunit-file=xunit-reports/ecosphere_inttest.xml
inttest_ecosphere:
	$(SSH) '$(ARC) submit -t --no-inherit --watch $(ARCRES) $(SANDBOXRES) -- \
		"cd $(SANDBOX); $(SETENVDMXDATA); python ./run_tests.py -v integration_tests/ecosphere/*.py $(OPTS) "'

inttest_ipqc:
	$(SSH) '$(ARC) submit -t --no-inherit --watch $(ARCRES) $(SANDBOXRES) -- "ipqc -h"'




################################################
### This target (bundle_vs_current) checks the 
### dmx and dmxdata versions between
### - the version of dmx/dmxdata in the $(ARCRES)
### - the version symlink'ed to current
################################################
VERCHKSCRIPT := /p/psg/da/infra/users/yltan/depot/da/infra/dmx/main/scripts/check_current_is_pointing_to_correct_version.py
VERCHKSCRIPTSJ := /p/psg/da/scratch/users/yltan/depot/da/infra/dmx/main/scripts/check_current_is_pointing_to_correct_version.py
ALLARCRES := $(ARCRESFM8) $(ARCRESFM6) $(ARCRESWHR) $(ARCRESGDR) $(ARCRESRNR)
all_bundle_vs_current:
	-$(ARC) shell --watch --test project/falcon/branch/fm6dot2main/rc -- '$(VERCHKSCRIPT) $(ALLARCRES)'
	-$(SSH) '$(ARC) shell --watch --test project/falcon/branch/fm6dot2main/rc -- "$(VERCHKSCRIPTSJ) $(ALLARCRES)" '




.PHONY: cleanup_and_sync compile all_unittest unittest_abnr systemtest_tnr systemtest_ecolib systemtest_utillib systemtest_testrunner copy_testreports gen_docs deploy inttest_dmx inttest_ecosphere inttest_ipqc login systemtest_abnr armortest_fm armortest_whr all_systemtest run bundle_vs_current all_bundle_vs_current

