all_test: test_auto test_manual

export DMXDATA_ROOT = /p/psg/flows/common/dmxdata/14.4

bobo:
	echo "For some reason, this is needed, otherwise, submitting to arc will hang. Not sure why !!!"
	gdp info 

EXE := ./run_tests.py
OPTS := -v -l dmx -e '^(manual|_)'
TCEXE := ../run_tests_teamcity.py
TCOPTS := 
test_auto: bobo
	echo "Running test_auto ..."
	$(TCEXE) $(TCOPTS) ./abnrlib/
	$(TCEXE) $(TCOPTS) ./ecolib/
	$(TCEXE) $(TCOPTS) ./dmxcmd/
	$(TCEXE) $(TCOPTS) ./dmlib/
	$(TCEXE) $(TCOPTS) ./utillib/
	$(TCEXE) $(TCOPTS) ./tnr/
	$(TCEXE) $(TCOPTS) ./syncpoint/

test_manual:
	echo "Running test_manual ..."
	./tnr/manual_test_goldenarc_check.py -v
	./tnr/manual_pice_test_runner.py -v

.PHONY: all_test bobo test_auto test_manual
