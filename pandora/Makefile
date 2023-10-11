FUB := FM8
EXE := runPandora.pl 
PANDRES := dts_pandora/3.5.4
EMAILS := lionelta,cftham,wplim,srabadan
COMMONOPT := $(EXE) --link /nfs/site/disks/da_infra_1/users/yltan/depot/da/infra/dmx/main/pandora --path /nfs/site/disks/psg_data_1/lionelta/pandora --nogui --run --tag ./test1/main/ --wait --recurrent_run_enabled true --capture_runtime --clean keep::100

COMMONOPT := $(EXE) --path /nfs/site/disks/da_infra_1/users/yltan/depot/da/infra/dmx/main/pandora --nogui --run --tag ./test1/main/ --wait --recurrent_run_enabled true --capture_runtime --clean keep::100 --send_email $(EMAILS)

help:
	@echo "-----------------------------------------------------------------"
	@echo "arc shell dts_pandora/3.5.4"
	@echo
	@echo "To run rc_bundle_regression (FM6/FM8/WHR/GDR/RNR) ..."
	@echo "    arc submit $(PANDRES) -- make rc FUB=FM8"
	@echo
	@echo "To run contonuous integration test of main/ branch's codes ..."
	@echo "    arc submit $(PANDRES) -- make ci"
	@echo
	@echo "To run system and armor test of main/ branch's codes ..."
	@echo "    arc submit $(PANDRES) -- make systest"
	@echo "-----------------------------------------------------------------"

rc:
	$(COMMONOPT) --fubs "./test1/main/rc_bundle_regression%$(FUB)"  --tests rc_bundle_regression --timeout 100 --run_area_name $(FUB) 

ci:
	$(COMMONOPT) --fubs "./test1/main/main_branch_continuous_integration%main" --tests main_branch_continuous_integration --timeout 100 

systest:
	$(COMMONOPT) --fubs "./test1/main/system_and_armor_test%main" --tests "system_and_armor_test" --timeout 200 

gui:
	arc submit -i $(PANDRES) -- $(EXE) --path $(PWD)

