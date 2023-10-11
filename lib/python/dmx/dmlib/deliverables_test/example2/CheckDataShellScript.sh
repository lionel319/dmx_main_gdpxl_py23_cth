#! /bin/sh
# Shell script that performs a data check on the EXAMPLE2 deliverable.
#
# Exit with status zero if the file contains "Supercalifragilisticexpialidocious".
# Ignore case and white space.
#
# File dm/deliverables_test/example2/CheckDataShellScript.sh, unit tested
# in dm.Vp_test.test_example2CheckType().
#
# Do not modify this file in order to test functionality because it is
# specifically for use in the vp.py documentation.
#
# Copyright 2012 Altera Corporation
# John McGehee 2/9/2012

if [ $# -ne 1 ]; then
	echo "Usage: $0 example2.txt"
	exit 1
fi

diff -bi $1 - <<+++
supercalifragilisticexpialidocious
+++

