#!/bin/sh
#########################
# PROJECT ENVIRONMENT ? #
#########################
if [ -z ${DB_FAMILY+x} ] || [ -z ${DB_DEVICE+x} ] || [ -z ${DB_PROJECT+x} ] || [ -z ${DB_PROCESS} ]; then
    echo ""
    echo " No project environment !"
    echo " Set DB_FAMILY, DB_PROJECT, DB_DEVICE and DB_PROCESS environment variables."
    echo " Exit 1"
    echo ""
    echo "####################################################"
    exit 1
fi

python ${DMX_ROOT}/lib/python/dmx/ipqclib/min_arc/min_arc_version.py ${1+"$@"}

