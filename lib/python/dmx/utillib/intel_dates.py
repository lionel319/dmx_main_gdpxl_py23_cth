#! /usr/bin/env python

# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/utillib/intel_dates.py#1 $
# $Datetime: $
# $Change: 7411538 $
# $Author: lionelta $
# Original Author: Steve Potter
#
# COPYRIGHT (c) ALTERA CORPORATION 2016.  ALL RIGHTS RESERVED

"""
Helper routines for dealing with Intel's non-standard work-week.

Intel Office WW:
    first week of year (WW1) starts on Jan 1
    each week starts on Sunday
    days are numbered 0-6.
ISO standard 8601:
    first week of year (WW1) has the first Thursday,
    each week starts on Monday,
    days are numbered 1-7.

See https://intelpedia.intel.com/WW%20-%20Work_Week

See also, for example 2011WW01 in
http://phonebook.fm.intel.com/cgi-bin/phonecal?mon=Jan&year=2011&mode=month&who=UNITED+ST
"""


import logging
import re
logger = logging.getLogger(__name__)

from datetime import date, timedelta


def intel_weekday(dd):
    """
    The Intel weekday of a given day of the week is that same as the iso_weekday,
    except that Sunday is day 0, not day 7.

    :param dd: Specifies the date of interest
    :type dd: datetime.date object

    :return: 0 through 6, where 0 is for Sunday and 6 is for Saturday
    :rtype: int
    """

    iso_weekday = dd.isoweekday()
    our_weekday = 0 if iso_weekday == 7 else iso_weekday
    return our_weekday


def intel_ww1_start_date(year):
    """
    Return the date for <year>WW01.0, I.E. the Sunday
    that starts the Intel work week containing Jan 1rst
    of that year.

    :param year: (int) The year whose WW01.0 date is desired.

    :return: A datetime.date specifying the first day of WW01
    :rtype: datetime.date
    """

    # Work week 1 starts the Sunday at or before Jan 1rst of that year.
    jan1 = date(year, 1, 1)
    jan1_intel_weekday = intel_weekday(jan1)
    ww1_day1_date = jan1 - timedelta(days=jan1_intel_weekday)
    logger.debug('Intel WW1 Day 1: {}'.format(ww1_day1_date))
    return ww1_day1_date


def intel_calendar(dd):
    """
    The intel_calendar function is like date.isocalendar(), but
    instead of the returning the ISO standard info it returns the
    non-standard work-week info used by Intel.

    Intel is using a non ISO-standard work week definition.  Work weeks
    start on Sunday, and work week 1 is the work week containing Jan 1rst.
    The ISO-standard work week is easily fetched from datetime.date.isocalendar(),
    but that doesn't really help us because in some years the work week numbers
    don't match the ISO work week.

    :param dd: Specifies the date of interest
    :type dd: datetime.date object

    :returns: a 3-ple of ints, (Intel year, Intel week number, Intel weekday).
    :rtype: tuple

    >>> intel_calendar(date(year=2015, month=12, day=28))
    (2016, 1, 1)
    >>> intel_calendar(date(year=2017, month=12, day=31))
    (2018, 1, 0)

    """

    # Use the end of the Intel work week (Saturday) to find out which
    # year we're talking about.
    target_intel_weekday = intel_weekday(dd)
    end_of_week = dd + timedelta(6 - target_intel_weekday)

    logger.debug('Target date: {}'.format(dd))
    logger.debug('End of week: {}'.format(end_of_week))

    intel_year = end_of_week.year
    logger.debug('Intel year: {}'.format(intel_year))

    # Work week 1 starts the Sunday at or before Jan 1rst of that year.
    intel_ww1_day1 = intel_ww1_start_date(intel_year)

    # Intel week number is 1/7th the number of days after intel_ww1_day1
    # plus one (week numbers start with 1).
    delta = dd - intel_ww1_day1
    days_from_ww1_day1 = delta.days
    logger.debug('Days from WW1 Day 1: {}'.format(days_from_ww1_day1))
    intel_week_number = (days_from_ww1_day1 // 7) + 1

    intel_info = (intel_year, intel_week_number, target_intel_weekday)
    return intel_info


def intel_ww_string_to_date(intel_ww_string):
    """
    Returns a datetime.date object for the calendar date selected by the WW string.

    :param intel_ww_string: A string in the form <yyyy>WW<ww>.<d>
    :type intel_ww_string: str

    :return: A datetime.date specifying the calendar date that WW string represents.
    :rtype: datetime.date

    >>> intel_ww_string_to_date('2016WW06.4')
    datetime.date(2016, 2, 4)
    >>> intel_ww_string_to_date('2016WW53.0')
    datetime.date(2016, 12, 25)
    """

    # The date is Jan 1, <yyyy> + (7 * (<ww> - 1)) + <d>
    re_match = re.match(r"(?P<yyyy>\d{4})WW(?P<ww>\d{2})\.(?P<d>\d)", intel_ww_string)
    if not re_match:
        raise ValueError

    year = int(re_match.group('yyyy'))
    week = int(re_match.group('ww'))
    day = int(re_match.group('d'))

    jan1 = intel_ww1_start_date(year)
    return jan1 + timedelta(days=(week - 1) * 7 + day)


def date_to_intel_ww_string(dd):
    """
    Returns a string representing the year, work-week, and day of the
    week in the form '<YYYYf>WW<MM>.<D>', using the Intel definition
    of work-week (see the intel_calendar doc string).

    :param dd: Specifies the date of interest
    :type dd: datetime.date object

    :return: The Intel WW string in the form <yyyy>WW<ww>.<d>
    :rtype: str

    >>> date_to_intel_ww_string(date(year=2015, month=12, day=27))
    '2016WW01.0'
    >>> date_to_intel_ww_string(date(year=2018, month=1, day=1))
    '2018WW01.1'
    """

    return '{}WW{:02d}.{}'.format(*intel_calendar(dd))
