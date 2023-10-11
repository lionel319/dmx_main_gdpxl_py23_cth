all_test: test_auto test_manual

export DMXDATA_ROOT = /p/psg/flows/common/dmxdata/14.4


### If you want to generate coverage, then run it like this
###    > make -f jenkins.Makefile COVER='coverage run -a'
COVER :=
OPTS := -v -l dmx -e '^(manual|_)'
TCEXE := sleep 1; $(COVER) ./run_tests.py
TCOPTS := -v --exe -e '^(manual|_)' --with-xunit --xunit-file=../../gdp47827_tests/test-reports/`date +"%s"`.xml
test_auto:
	echo "Running test_auto ..."
	$(TCEXE) $(TCOPTS) ./cmxcmd/
	$(TCEXE) $(TCOPTS) ./utillib/
	$(TCEXE) $(TCOPTS) ./abnrlib/flows/

test_manual:
	echo "Running test_manual ..."

.PHONY: all_test test_auto test_manual
