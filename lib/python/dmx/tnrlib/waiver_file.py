# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/tnrlib/waiver_file.py#1 $
# $DateTime: 2022/12/13 18:19:49 $
# $Author: lionelta $
"""
Supports functionality originally requested in CASE:220974:
the ability to define waivers via a file which can then be 
provided to tools like "quick check" and the release system
which are applied in addition to the waivers defined on sw-web.

Waivers in the WaiverFile class can either be provided 
by a CSV file, or they can be loaded via a Python list.  The
latter is to support release_runner receiving this data via 
the message queueing system. 

The CSV file has these fields:

    variant, flow, subflow, waiver_reason, error_message

Leading and training spaces are stripped when the file is read.
Commas are only allowed in the error_message field.
Any field can use the asterisk (*) character as a wildcard.
(Note: this means that errors which normally contain an
asterisk will actually be intepreted as a wildcard match
when the exact error text is used to create a waiver.  However,
it will only match errors where there are additional characters
before the * since that is how Python regexps work.  In practice
this is not expected to be a problem.)

The file is read into memory using the load_from_file method.
Alternatively, the load_from_list method allows loading of
waiver definitions from a Python list.

After loading, the class can be used to identify if a given 
variant, flow, subflow, and error message matches any waiver.

Kirk Martinez
January 12, 2015
"""
from builtins import str
from builtins import object
from logging import getLogger
import re
import csv
import sys
from os import path
from collections import namedtuple
from itertools import chain
import glob
#from dmx.abnrlib.flows.hsdeswaiver import GlobalWaiver
from dmx.utillib.dmxwaiverdb import DmxWaiverDb

logger = getLogger(__name__)

# If this sturcture ever changes, update to_ascii and from_ascii.
AWaiver = namedtuple('AWaiver', 'variant flow subflow reason error filepath')

# Shamelessly stolen from http://stackoverflow.com/questions/5004687/python-csv-dictreader-with-utf-8-data
def UnicodeDictReader(utf8_data, csvfile, **kwargs):
    """
    A helper that allows reading Unicode via the standard csvfile package.
    See: http://stackoverflow.com/questions/5004687/python-csv-dictreader-with-utf-8-data
    """
    csv_reader = csv.DictReader(utf8_data, **kwargs)
    for rownum, row in enumerate(csv_reader):
        try:
            if sys.version_info[0] < 3:
                yield {key: '' if value is None else str(value, 'utf-8') for key, value in row.items()}
            else:
                yield {key: '' if value is None else str(value) for key, value in row.items()}
        except:
            raise LookupError("Incorrect waiver_file format in:-\n- file: {}\n- line: {}\n".format(csvfile, reconstruct_line(row)))

def reconstruct_line(parts):
    """
    Parts is a dict where values may be either a string or a lists of strings.
    This re-constructs the origianl line by joining the lists with commas.
    """
    result = []
    for field in ['variant','flow','subflow','reason','error']:
        part = parts[field]
        if isinstance(part, list):
            result.extend(part)
        else:
            result.append(part)
    return ','.join(result)


class WaiverFile(object):
    """
    This class is used to represent a set of waivers which may include wildcards and
    which can be read from a file.
    """
    def __init__(self):
        self.waivers = []
        self.hsdes_waivers = []
        self.rawdata = []

    def add(self, waiver):
        """
        Expect AWaiver instance.  Adds it to the list.
        """
        self.waivers.append(waiver)

    def add_hsdes_waiver(self, waiver):
        """
        Expect AWaiver instance.  Adds it to the hsdes waiver list.
        """
        self.hsdes_waivers.append(waiver)


    def load_from_file(self, filepath):
        """
        Reads in the waiver specifications from the given file
        and adds them to the list of specs in this WaiverFile instance.
        This method can be called multiple times to process multiple
        waiver files, resulting in a single instance which holds
        all the waiver specs across all files.

        Filepath must exist.  Reads the file which must be in
        this format:

            variant, flow, subflow, waiver_reason, error_message

        Leading and training spaces will be trimmed from all fields.
        Commas are only allowed in the error_message field.
        Any field can use the asterisk (*) character as a wildcard.
        """
        if sys.version_info[0] < 3:
            infile = open(filepath, 'rb')
        else:
            infile = open(filepath, 'r', newline='', encoding='utf8')

        with infile as csvfile:
            reader = UnicodeDictReader((row for row in csvfile.read().splitlines() if not row.startswith('#') and not row=='' and not row.isspace()), filepath, fieldnames=('variant','flow','subflow','reason','error'), skipinitialspace=True)
            for parts in reader:
                logger.debug("original_line:{}".format(parts))
                try:
                    line = self.reconstruct_line(parts)
                    logger.debug("reconstruct_line:{}".format(line))

                    errprefix = 'Format Error found in {}\n'.format(filepath)
                    if len(list(parts.keys()))<5:
                        raise LookupError(errprefix + "Not enough columns on this line of waiver file:\n%s"%line)
                    if len(list(parts.keys()))>5:
                        raise LookupError(errprefix + "Too many columns on this line of waiver file (you may need double quotes around fields that include commas):\n%s"%line)
                    if len(parts['variant']) < 1:
                        raise LookupError(errprefix + "<Variant> column cannot be empty on this line of waiver file:\n%s"%line)
                    if len(parts['flow']) < 1:
                        raise LookupError(errprefix + "<Flow> column cannot be empty on this line of waiver file:\n%s"%line)
                    if len(parts['subflow']) < 1:
                        raise LookupError(errprefix + "<Subflow> column cannot be empty on this line of waiver file:\n%s"%line)
                    if len(parts['reason']) < 10:
                        raise LookupError(errprefix + "<Reason> column must be at least 10 chacters on this line of waiver file:\n%s"%line)
                    if len(parts['error']) < 1:
                        raise LookupError(errprefix + "<Error> column cannot be empty on this line of waiver file:\n%s"%line)
                    
                    if sys.version_info[0] < 3:
                        if not (line == line.encode('ascii','ignore')):
                            raise LookupError(errprefix + "There are non-ASCII characters on the following line, please remove them:\n%s"%line)
                    else:
                        if not (line == line.encode('ascii','ignore').decode('ascii')):
                            raise LookupError(errprefix + "There are non-ASCII characters on the following line, please remove them:\n%s"%line)

                except TypeError:
                    raise LookupError(errprefix + "Your waiver file is malformed.  Please verify each line either starts with a # (comment), or has five entries, and that any entry containing a comma is surrounded by double quotes.")
                except:
                    logger.error(errprefix)
                    raise

                if parts['variant'] == parts['flow'] == parts['subflow'] == parts['error'] == '*':
                    logger.warning("Waiver file contains line with nothing but wildcard characters (*).  This is not advisable.")
                waiver = self.build_awaiver(parts['variant'], parts['flow'], parts['subflow'], parts['reason'], parts['error'], path.abspath(filepath))
                self.waivers.append(waiver)
                self.rawdata.append([parts['variant'], parts['flow'], parts['subflow'], parts['reason'], parts['error']])

    def load_from_documents(self, doc):
        """
        Reads in the waiver specifications from the given document from mongodb
        and adds them to the list of specs in this WaiverFile instance.
        This method can be called multiple times to process multiple
        waiver documents, resulting in a single instance which holds
        all the waiver specs across all files.

        Document format must be dict.  The dict must contain this information:

            variant, flow, subflow, waiver_reason, error_message

        Leading and training spaces will be trimmed from all fields.
        Commas are only allowed in the error_message field.
        Any field can use the asterisk (*) character as a wildcard.
        """
        logger.debug("original_line:{}".format(doc))
        filepath = 'mongodb'
        errprefix = 'Format Error found in {}\n'.format(filepath)
        variant = doc.get('variant') if doc.get('variant') else doc.get('ip')
        flow = doc.get('flow') if doc.get('flow') else doc.get('deliverable')

        try:
            line = self.reconstruct_line(doc)
            logger.debug("reconstruct_line:{}".format(line))

            if len(list(doc.keys()))<5:
                raise LookupError(errprefix + "Not enough field on this line of waiver file:\n%s"%line)
            #if len(doc.keys())>5:
            #    raise LookupError(errprefix + "Too many columns on this line of waiver file (you may need double quotes around fields that include commas):\n%s"%line)
            if len(variant) < 1:
                raise LookupError(errprefix + "<Variant> column cannot be empty on this line of waiver file:\n%s"%line)
            if len(flow) < 1:
                raise LookupError(errprefix + "<Flow> column cannot be empty on this line of waiver file:\n%s"%line)
            if len(doc['subflow']) < 1:
                raise LookupError(errprefix + "<Subflow> column cannot be empty on this line of waiver file:\n%s"%line)
            #if len(doc['reason']) < 10:
            if len(doc['reason']) < 2:
                raise LookupError(errprefix + "<Reason> column must be at least 10 chacters on this line of waiver file:\n%s"%line)
            if len(doc['error']) < 1:
                raise LookupError(errprefix + "<Error> column cannot be empty on this line of waiver file:\n%s"%line)
            if not (line == line.encode('ascii','ignore')):
                raise LookupError(errprefix + "There are non-ASCII characters on the following line, please remove them:\n%s"%line)
        except TypeError:
            raise LookupError(errprefix + "Your waiver file is malformed.  Please verify each line either starts with a # (comment), or has five entries, and that any entry containing a comma is surrounded by double quotes.")
        except:
            logger.error(errprefix)
            raise

        if variant == flow == doc['subflow'] == doc['error'] == '*':
            logger.warning("Waiver file contains line with nothing but wildcard characters (*).  This is not advisable.")
        waiver = self.build_awaiver(variant, flow, doc['subflow'], doc['reason'], doc['error'], filepath)
        self.hsdes_waivers.append(waiver)
       # self.waivers.append(waiver)
        self.rawdata.append([variant, flow, doc['subflow'], doc['reason'], doc['error']])


    def unloader(self):
        '''
        Returns the original raw data of the csv file.
        return = [
            [variant1, flow1, subflow1, reason1, error1],
            ...   ...   ...
            [variant1, flow1, subflow1, reason1, error1]
        ]
        '''
        return self.rawdata


    def reconstruct_line(self, parts):
        """
        Parts is a dict where values may be either a string or a lists of strings.
        This re-constructs the origianl line by joining the lists with commas.
        """
        result = []
        # addded new field called ip in hsdes waiver
        for field in ['variant','flow','subflow','reason','error', 'ip']:
            try:
                part = parts[field]
                if isinstance(part, list):
                    result.extend(part)
                else:
                    result.append(part)
            except KeyError:
                pass
        return ','.join(result)

    def load_from_list(self, list_of_waivers):
        """
        list_of_waivers must be a list of AWaiver named tuples or
        None (which has no effect).
        This class instance will then use this list as the waivers.
        Bypasses checks on field length done when using load_from_file.
        This is not intended for use by external programs.
        """
        # The class stores compiled regexps in its self.waivers
        # so we have to convert them...
        if list_of_waivers is not None:
            for w in list_of_waivers:
                waiver = self.build_awaiver(w.variant, w.flow, w.subflow, w.reason, w.error, w.filepath)
                self.waivers.append(waiver)

    def to_regex(self, str):
        """
        Converts the given string (which may contain the * character) 
        into a compiled Python regular expression where * matches any
        character (.*).  First strips spaces at the beginning and end 
        of the string.  The regex is also forced to match the entire
        word (not just the beginning).

        Since we only support "*" wildcards, not the full regexp syntax, 
        we also escape all the characters that are "special" to the 
        Python regex parser.
        """
        
        ### Fogbugz 391491
        ### Ignore revision number when checksum matches.
        pattern = '^(.+Revision )#\S+( of the file was used during checking, but an attempt was made to release revision )#\S+(.+)$'
        str = re.sub(pattern, '\\1#*\\2#*\\3', str) 
        
        #print str.__repr__()
        stripped = str.strip()
        #print "S:%s" %stripped.__repr__()
        escaped = re.escape(stripped)
        #print "E:%s" %escaped.__repr__()
        wildcarded = escaped.replace(r'\*', r'.*')
        #print "W: %s" % wildcarded.__repr__()
        to_the_end = '%s$' % wildcarded

        return re.compile(to_the_end, re.IGNORECASE)

    def from_regex(self, str):
        """
        Converts a regex pattern into the original unescaped version
        of the string as orginally loaded (except spaces will still
        be stripped from the ends).
        """
        without_end_of_line = str[0:-1]
        #print "FROM: %s" % str.__repr__()
        mark_dblback = without_end_of_line.replace('\\\\', r'DOUBLEBACKSLASH')
        #print "MD: %s" % mark_dblback.__repr__()
        remove_singleback = mark_dblback.replace('\\', '')
        #print "RS: %s" % remove_singleback.__repr__()
        dblback_to_singleback = remove_singleback.replace('DOUBLEBACKSLASH', '\\')
        #print "DS: %s" % dblback_to_singleback.__repr__()
        unwildcard = dblback_to_singleback.replace('.*', '*')
        #print "UW: %s" % unwildcard.__repr__()

        return unwildcard

    def build_awaiver(self, variant, flow, subflow, reason, error, filepath):
        """
        Returns an AWaiver named tuple with compiled regexps for fields
        that support them.  
        """
        variant = self.to_regex(variant)
        flow    = self.to_regex(flow)
        subflow = self.to_regex(subflow)
        reason  = reason.strip()
        error   = self.to_regex(error)
        return AWaiver(variant, flow, subflow, reason, error, filepath)

    def to_ascii(self):
        """
        Converts the regexp pattern objects into string patterns.
        Also converts the named tuples into lists since JSON-serialization
        deserialization loses the named tuples, and JSON-serialization is
        the whole point of providing these ascii serializations.
        """
        serialized_waivers = []
        if self.waivers is not None:
            for w in self.waivers:
                v = self.from_regex(w.variant.pattern)
                f = self.from_regex(w.flow.pattern)
                s = self.from_regex(w.subflow.pattern)
                r = w.reason
                e = self.from_regex(w.error.pattern)
                serialized_waivers.append([v, f, s, r, e, w.filepath])

        return serialized_waivers 

    @staticmethod
    def from_ascii(waivers):
        """
        Regenerates content generated with to_ascii.

        Also supports a limited form of backward-compatibility.
        Older versions of this class (used by some abnr release*
        which sent to_ascii data via the release queue) defined 
        AWaiver without the filepath field.  This method will
        de-serialize such data without error by providing a dummy
        filepath.  This ensures old abnr commands will still work
        only breaking the reporting of the path.  Once no one is
        using older version of abnr, this feature should be removed.
        """
        wf = WaiverFile()

        if waivers is not None:
            awaivers = []
            for w in waivers:
                if len(w)==5:
                    # Backward-compatible case
                    awaivers.append( AWaiver(w[0], w[1], w[2], w[3], w[4], 'no_filename_provided_by_old_abnr_version' ) )
                else:
                    awaivers.append( AWaiver(w[0], w[1], w[2], w[3], w[4], w[5]) )

            wf.load_from_list(awaivers)

        return wf

    def is_equal(self, wf):
        """
        Returns true if the waiver definitions for this instance 
        exactly match the definitions for the given instance.
        """
        these = self.to_ascii()
        those = wf.to_ascii()

        if len(these) != len(those):
            return False

        for w in these:
            if w not in those:
                return False

        return True

    def find_matching_waiver(self, variant, flow, subflow, error):
        """
        Returns a tuple (creator, reason, waiverfile) if a waiver exists which matches
        the given parameters.  Otherwise, returns None.
        """
        found = False

        for waiver in self.waivers:
            if waiver.variant.match(variant) and waiver.flow.match(flow) and waiver.subflow.match(subflow) and waiver.error.match(error) and not 'UNWAIVABLE' in error:
                if flow == 'deliverable' and subflow == 'existence' and not waiver.filepath.endswith('{}/reldoc/tnrwaivers.csv'.format(variant)):
                    logger.debug("deliverable:existance waivers are only allowed from reldoc/tnrwaivers.csv. ({})".format(waiver.filepath))
                else:
                    return ('CommandLine', waiver.reason, waiver.filepath)

        return None

    def find_matching_hsdes_waiver(self, variant, flow, subflow, error):
        """
        Returns a tuple (creator, reason, waiverfile) if a waiver exists which matches
        the given parameters.  Otherwise, returns None.
        """
        found = False

        for waiver in self.hsdes_waivers:
            if waiver.variant.match(variant) and waiver.flow.match(flow) and waiver.subflow.match(subflow) and waiver.error.match(error) and not 'UNWAIVABLE' in error:
                if flow == 'deliverable' and subflow == 'existence' and not waiver.filepath.endswith('mongodb'.format(variant)):
                    logger.debug("deliverable:existance waivers are only allowed from reldoc/tnrwaivers.csv. ({})".format(waiver.filepath))
                else:
                    return ('HsdesWaiver', waiver.reason, waiver.filepath)

        return None




    def get_tnrwaivers_files(self, wsroot, variant, libtype=None, filename='tnrwaivers.csv'):
        '''
        for Libtype release, 
            only get <wsroot>/variant/libtype/tnrwaivers.csv (if libtype != ipspec)
        for variant release, 
            returns <wsroot>/variant/*/tnrwaivers.csv (except variant/ipspec/tnrwaivers.csv)
        if libtype == ipspec, 
            return []
        '''
        if not libtype:
            libtype = '*'

        wsroot = path.realpath(path.abspath(wsroot))
        cmd = '{}/{}/{}/{}'.format(wsroot, variant, libtype, filename)
        logger.debug("globbing {} ...".format(cmd))
        files = glob.glob(cmd)

        return self.remove_unallowed_tnrwaivers_files(files, wsroot, variant, filename)


    def remove_unallowed_tnrwaivers_files(self, waiverfiles, wsroot, variant, filename='tnrwaivers.csv'):
        '''
        as of today, only tnrwaivers.csv from variant/ipspec libtype is disallowed.
        '''
        retlist = []
        for f in waiverfiles:
            if f != '{}/{}/{}/{}'.format(wsroot, variant, 'ipspec', filename):
                retlist.append(f)
        return retlist


    def autoload_tnr_waivers(self, wsroot, variant, libtype=None, filename='tnrwaivers.csv'):
        '''
        For more info:- 
        https://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/NewTnrWaiverProposal
        '''
        logger.debug("Loading in available waiver files ...")
        for f in self.get_tnrwaivers_files(wsroot, variant, libtype, filename):
            logger.debug("loading waiver file {}".format(f))
            self.load_from_file(f)
        logger.debug("Waivers from waiverfiles: {}".format(self.waivers))

    def autoload_hsdes_waivers(self, thread, ip, milestone):
        '''
        For more info:- 
        https://sw-wiki.altera.com/twiki/bin/view/DesignAutomation/NewTnrWaiverProposal
        '''
        all_hsdcaseid = []
        logger.debug("Loading in available hsdes waiver files ...")
        db = DmxWaiverDb()

        # ip asterik is to get global waiver
        data = {'thread': thread, "$or":[ {"ip":ip}, {"ip":'*'}], 'milestone':milestone, 'status':'sign_off'}
        #data = {'thread': thread, 'ip':ip, 'milestone':milestone}
        collection_data = db.find_waivers(data)
        logger.debug(collection_data)
        # Query from hsd
        #self.check_hsd_approval_status()        

        for ea_doc in collection_data:
            hsdes_case = ea_doc.get('hsdes_caseid')
            if hsdes_case not in all_hsdcaseid:
                all_hsdcaseid.append(hsdes_case)
            logger.debug("loading waiver file {}".format(ea_doc))
            self.load_from_documents(ea_doc)
        self.all_hsdescase = all_hsdcaseid
        logger.debug("Waivers from hsdes waiver: {}".format(self.hsdes_waivers))

    def check_hsd_approval_status(self):
        hsdes_env = HsdesConnection.HSDES_TEST_ENVIRONMENT
        hsdes = HsdesConnection(env=hsdes_env)

        support_details = hsdes.query_search("select id,title,family,release,component,support.filing_project,fpga.support.fpga_device,support.issue_type,fpga.support.milestone,priority,owner,fpga.support.customer_vendor,fpga.support.customer_vendor_priority,tag,submitted_date,submitted_by,updated_date,updated_by,closed_date,closed_by,eta,fpga.support.eta_ww,status,reason,subject where tenant='fpga' AND subject='support' AND status='open'",count=100000)

