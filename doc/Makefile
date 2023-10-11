# Make sure to arc shell doxygen....or you get an ancient version.

# Currently the parent Makefile has an option where LIB can be passed in so
# that only a single library is regenerated; however, it's not supported.
# We only have one Doxyfile config file called Doxyfile_dmx.
LIB := dmx

# If you have a new python package, add it here with the suffix 'graph'
# TODO  Why not just list the name of the package?
GEN_ALL_GRAPH := checklib_graph djangolib_graph dmlib_graph dmxlib_graph ecolib_graph helplib_graph ipqclib_graph plugins_graph sionlib_graph syncpointlib_graph tnrlib_graph utillib_graph

# LIB_FOR_ALL_GRAPH isn't defined; what's it supposed to be?
.PHONY: doc clean callgraph dot all_graph all_doc $(LIB_FOR_ALL_GRAPH)

doc: clean dot callgraph
	@arc submit  --interactive project/falcon/branch/fm8dot2main/rc -- doxygen Doxyfile_$(LIB)

doc_nograph: clean
	@arc submit  --interactive project/falcon/branch/fm8dot2main/rc -- doxygen Doxyfile_$(LIB)


clean:
	rm -rf ./$(LIB)
	rm -rf images/$(LIB).dot
	rm -rf images/$(LIB).png


callgraph: dot
	@arc submit  --interactive project/falcon/branch/fm8dot2main/rc -- dot -v -Tpng -oimages/$(LIB).png images/$(LIB).dot


dot:
	@mkdir -p images
	@arc submit  --interactive project/falcon/branch/fm8dot2main/rc -- "python $(PWD)/pyan.py $(wildcard ../lib/python/dmx/$(LIB)/*.py) --dot -c -g -e --skipErrorClasses > $(PWD)/images/$(LIB).dot"


# This is the target called by the parent dmx Makefile
all_doc: all_graph
	rm -rf ./dmx/
	arc submit --no-inherit --watch project/falcon/branch/fm8dot2main/rc -- /usr/intel/bin/doxygen Doxyfile_dmx

all_graph: $(GEN_ALL_GRAPH)
	@echo "Done generating all graphs ..."

$(GEN_ALL_GRAPH):
	$(eval mylib := $(subst _graph,,$@))
	mkdir -p ./images
	rm -rf ./images/$(mylib).dot
	rm -rf ./images/$(mylib).png
	make callgraph LIB=$(mylib)

