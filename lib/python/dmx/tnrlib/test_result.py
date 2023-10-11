#!/usr/bin/env python
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/tnrlib/test_result.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $
"""
Test results consist of TestFailures or TestResults
named tuples.
"""
from collections import namedtuple

# When a test fails, we add one of these to the list of failed tests.
TestFailure = namedtuple('TestFailure', 'variant libtype topcell flow subflow error')
"""
:param variant: the variant being tested which experienced a failure
:param libtype: the libtype being tested which experienced a failure
:param topcell: the topcell being tested which experienced a failure
:param flow: the test flow which saw a failure
:param subflow: the test subflow which saw a failure
:param error: the detailed error message
"""

# When a test passes, failed, or is skipped, we add one of these to the list of results
# result_type is either "pass", "fail", or "skip"
# This is a generalization of TestFailure, but that still remains for backward compatibility
TestResult = namedtuple('TestResult', 'result_type variant libtype topcell flow subflow message')
"""
:param result_type: the type of result, either "pass", "fail", or "skip"
:param variant: the variant being tested 
:param libtype: the libtype being tested
:param topcell: the topcell being tested
:param flow: the test flow that got this result
:param subflow: the test subflow that got this result
:param message: the detailed message explaining the result
"""
