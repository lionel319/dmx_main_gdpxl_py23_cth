#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012,2013 Altera Corporation. All rights reserved.
# This source code is highly confidential and proprietary information of Altera
# and is to be used for internal Altera purposes only.   Altera assumes no
# responsibility or liability arising out of the application or use of this
# source code for non-Altera purposes.
#
# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/dmlib/deliverables/utils/General.py#1 $

"""
General-purpose utilities
"""


import os
import math
import resource
import collections
import time
import string  # pylint: disable = W0402
import logging

##########################################################################################

##########################################################################################
# Universal object attribute dumper; used for debugging
##########################################################################################
def dumpAny(obj):
    logging.info ("obj.type =" + str (type(obj)))
    if obj is None:
        return
    for attr in dir(obj):
        logging.info ("obj.%s = %s", attr, getattr(obj, attr))


##########################################################################################
def nearestMultiple(value,factor):
    '''Returns the multiple of 'factor' nearest to 'value' ''' 
    assert type(value) is float and type(factor) is float and factor >= 0.0
    if factor == 0.0:
        return value
    else:
        return factor * math.floor (value  / factor + 0.5)
    
        
##########################################################################################
def tsplit(sstring, delimiters):
    """
    Behaves like str.split but supports multiple delimiters.
    >>> s = 'thing1,thing2/thing3-thing4'
    >>> tsplit(s, (',', '/', '-'))
        ['thing1', 'thing2', 'thing3', 'thing4']
    """
    
    delimiters = tuple(delimiters)
    stack = [sstring,]
    
    for delimiter in delimiters:
        for i, substring in enumerate(stack):
            substack = substring.split(delimiter)
            stack.pop(i)
            for j, _substring in enumerate(substack):
                stack.insert(i+j, _substring)
            
    return stack
    

##########################################################################################
# Find in list without throwing exception if not present (returns -1 instead)
def findInList (where, what):
    if what in where:
        return where.index(what)
    else:
        return -1
    
    
##########################################################################################
def findDuplicatedElementInList (where):
    '''
    Check if list 'inLinst' has duplicates using operator == among the members. 
    O(n)
    Returns the value of the first duplicated element, None if none
    '''
    asSet = set()
    for i in where:
        if i in asSet:
            return i
        else:
            asSet.add(i)

    return None


def findAllDuplicatedElements (where):
    '''
    Returns a list of elements in 'where' that are duplicated
    '''
    counts = {}
    
    for e in where:
        if counts.get(e):
            counts [e] = counts [e] + 1
        else:
            counts [e] = 1
    
    ret = []
    for e in counts:
        if counts[e] > 1:
            ret.append (e)
            
    return ret
        
    
##########################################################################################
def almostEqual (a, b, decimalPlaces=7):
    'Check if values (assumed float) are almost equal (i.e. relative error <= 1e-places)'
    return round(abs(a-b),decimalPlaces) == 0
    
    
##########################################################################################
def cacheCall (function, arg):
    'Store the result of function(arg) to local cache; retrieve it from there if possible'     
    if not hasattr (function, 'cache_'):
        function.cache_ = {}
    
    alreadyThere = function.cache_.get (arg)
    if alreadyThere:
        return alreadyThere
    
    newlyCalculated = function (arg)
    function.cache_ [arg] = newlyCalculated
    return newlyCalculated
  

####################### Memory usage, see http://code.activestate.com/recipes/286222/    

_proc_status = '/proc/%d/status' % os.getpid()

_scale = {'kB': 1024.0, 'mB': 1024.0*1024.0,
          'KB': 1024.0, 'MB': 1024.0*1024.0}

def _VmB(VmKey):
    '''Private.
    '''
    # get pseudo file  /proc/<pid>/status
    try:
        t = open(_proc_status)
        v = t.read()
        t.close()
    except: # pylint: disable = W0702
        return 0.0  # non-Linux?
    # get VmKey line e.g. 'VmRSS:  9999  kB\n ...'
    i = v.index(VmKey)
    v = v[i:].split(None, 3)  # whitespace
    if len(v) < 3:
        return 0.0  # invalid format?
    # convert Vm value to bytes
    return float(v[1]) * _scale[v[2]]

def memory(since=0.0):
    '''Return memory usage in bytes.
    '''
    return _VmB('VmSize:') - since

def resident(since=0.0):
    '''Return resident memory usage in bytes.
    '''
    return _VmB('VmRSS:') - since

def stacksize(since=0.0):
    '''Return stack size in bytes.
    '''
    return _VmB('VmStk:') - since    


##########################################################################################
def getProcessMemory():
    '''Returns the process memory in bytes'''
    process = resource.getrusage (resource.RUSAGE_SELF).ru_maxrss * 1024
    children = resource.getrusage (resource.RUSAGE_CHILDREN).ru_maxrss * 1024
    return process + children
#    return resident()


##########################################################################################
def secondsToHMS (seconds):
    '''Convert seconds to HH:MM::SS'''
    seconds = int (seconds)
    Hours   = seconds / 3600 
    Minutes = (seconds % 3600) / 60 
    Seconds = seconds % 60 
    
    ret = '%02d:%02d:%02d' % (Hours, Minutes, Seconds)
    return ret


##########################################################################################
def findSubsequenceIndex(longer,shorter):
    '''
    Returns index where longer [index, index + len(shorter)] == shorter;
    -1 if never.
    '''
    lenShorter = len (shorter)
    for index in range (len (longer) - len (shorter)):
        if longer [index: index + lenShorter] == shorter:
            return index
    return -1 # Not found

assert findSubsequenceIndex ('0123412','12') == 1
assert findSubsequenceIndex ('0123412','13') == -1
    

##########################################################################################
PosAndLen = collections.namedtuple ('PosAndLen', 'pos_ len_')
def findLongestMatch (longerList, shorterList):
    '''Finds the longest sub-list of 'shortedList' [0..) that is found in 'longerList'.
    Returns tuple:
       matchPositionInLong, matchLen
    '''
    assert type (longerList)  is list or type (longerList) is str
    assert type (shorterList) is list or type (shorterList) is str
    
    soFar = PosAndLen (0,0)
    for curLen in range (1, len (shorterList) + 1):
        index = findSubsequenceIndex (longerList, shorterList [:curLen])
        if index != -1:
            soFar = PosAndLen (index, curLen)
    return soFar 

assert findLongestMatch ('01234523', '23')   == PosAndLen (2, 2)
assert findLongestMatch ('01234523', 'ab')   == PosAndLen (0, 0)
assert findLongestMatch ('01234523', '0789') == PosAndLen (0, 1)


##########################################################################################
def retryReadFile (fileName, maxTimeout, resultIfUnsuccessful = None):
    '''
    Try open file in a loop until successful or 'maxTimeout' (seconds) is reached.
    
    On success, returns the file contents.
    On failure, returns 'resultIfUnsuccessful'
    '''
    assert type (fileName) is str and type (maxTimeout) is float
    
    start = time.time()
    printed = False
    
    while time.time() < start + maxTimeout:
        
        try:
            f = open (fileName, 'r')
            ret = f.read()
            f.close()
            return ret
        
        except Exception: # pylint: disable = W0703
            if not printed:
                logging.info ("VpInfo: waiting for file '%s'", fileName)
                printed = True
            logging.info ("   %.1f/%.1fs so far..." , 
                          float (time.time() - start), 
                          maxTimeout)
            
        time.sleep (10)

    logging.error ("VpError: file '%s' never became available.", fileName)    
    return resultIfUnsuccessful


##########################################################################################
def retryWaitFile (fileName, maxTimeout):
    '''
    Try open file in a loop until successful or 'maxTimeout' (seconds) is reached.
    
    On success, returns True.
    On failure, returns False'
    '''
    assert type (fileName) is str and type (maxTimeout) is float
    
    start = time.time()
    printed = False
    
    while time.time() < start + maxTimeout:
        try:
            f = open (fileName, 'r')
            f.close()
            return True
        
        except Exception: # pylint: disable = W0703
            if not printed:
                logging.info ("VpInfo: waiting for file '%s'", fileName)
                printed = True
            logging.info ("   %.1f/%.1fs so far...", 
                          float (time.time() - start), 
                          maxTimeout)
            
        time.sleep (10)

    logging.error ("VpError: file '%s' never became available.", fileName)    
    return False


##########################################################################################
def retryWaitForPath (pathName, maxTimeout, additionalDelay):
    '''
    Wait:
       additionalDelay
    then:
       at most maxTimeout until pathName becomes available, 
    then:
       additionalDelay
    Times in seconds as floats. 

    On success, returns True.
    On failure, returns False'
    '''
    
    time.sleep (additionalDelay)

    assert (type (pathName)   is str and 
            type (maxTimeout) is float and
            type (additionalDelay) is float)

    start = time.time()
    printed = False

    while time.time() < start + maxTimeout:
        if os.path.exists (pathName):
            return True
        if not printed:
            logging.info ("VpInfo: waiting for path '%s'", pathName)
            printed = True
        logging.info ("   %.1f/%.1fs so far...", 
                      float (time.time() - start), 
                      maxTimeout)
        time.sleep (10)
        
    time.sleep (additionalDelay)
    

def _extractLeadingDigits(s):
    'Split a string to head containing digits only and a tail'
    digits = ''
    while s and s[0] in string.digits:
        digits += s[0]
        s = s[1:]
    return digits, s 
        

##########################################################################################
def speacialSortPredicate(a,b):
    '''
    A predicate for 'sorted()' and alike.
    Allows sorting like A[7] < A[10]
    '''
    
    assert type (a) is str and type (b) is str
    
    while True:
        if not a or not b:
            return len (a) - len (b)
        
        a0 = a[0]
        b0 = b[0]
        if a0 not in string.digits or b0 not in string.digits:
            if a0 != b0:
                return ord (a0) - ord (b0)
            a = a[1:]
            b = b[1:]
        else:
            d1, a = _extractLeadingDigits (a)
            d2, b = _extractLeadingDigits (b)
            
            d1i = int (d1)
            d2i = int (d2)
            if d1i != d2i:
                return d1i - d2i
        

##########################################################################################
def specialSort (sequence, delimiter):
    '''
    'sorted()'-like function:
       - uses 'specialSortPredicate()' (see above)
       - optionally performs delimiter.join() on the result
    '''
    mySorted = sorted (sequence, speacialSortPredicate)
    if delimiter is not None:
        assert type (delimiter) is str
        mySorted = delimiter.join (mySorted)
    return mySorted
        

def findLineNumber (multiLineString, charIndex):
    '''
    Given:
       multiLineString - a string potential new-line ('\n')s
       charIndex - index of character in it. 
    Returns the (0-based) line number of the character at index 'charIndex'
    Throws on errors (asserts)
    '''
    assert type (multiLineString) is str
    assert type (charIndex) is int and charIndex >= 0 and charIndex < len (multiLineString)  
    
    size = len (multiLineString)
    
    curLineNum = 0
    
    for i in xrange (size):
        if i == charIndex:
            return curLineNum
        if multiLineString [i] == '\n':
            curLineNum += 1
    
    assert False
    
def calculateRunningLineNumbers (multiLineString):
    '''
    Given:
       multiLineString - a string potential new-line ('\n')s
    Returns:
       List of integers of same length, containing the current line number(s) 
    '''
    assert type (multiLineString) is str
    
    size = len (multiLineString)
    
    ret = []
    curLineNum = 0
    
    for i in xrange (size):
        ret.append (curLineNum)
        if multiLineString [i] == '\n':
            curLineNum += 1
    
    return ret
    

def _translateComment (comment, fillCharacter, preserveNewLines):
    ret = ''
    for c in comment:
        if c == '\n' and preserveNewLines:
            ret += c
        else:
            ret += fillCharacter
    return ret    


def stripStringCppComments (sstring, fillCharacter, preserveNewLines):
    'Strips C++-style comments'
    
    out = ''
    
    inCLang = 1
    inCppLang = 2
    
    insideComment = None
    
    comment = ''
    for c in sstring:
        if insideComment == inCLang:
            comment += c 
            if c == '/' and comment[-2] == '*':
                translated = _translateComment (comment, fillCharacter, preserveNewLines)
                out += translated
                comment = ''
                insideComment = False
        
        elif insideComment == inCppLang:
            comment += c
            if c == '\n': # End of comment
                translated = _translateComment(comment, fillCharacter, preserveNewLines)
                out += translated
                comment = ''
                insideComment = False
                 
        elif c == '*' and out and out[-1] == '/':
            comment = '/*'
            out = out [:-1]
            insideComment = inCLang
        
        elif c == '/' and out and out[-1] == '/':
            comment = '//'
            out = out [:-1]
            insideComment = inCppLang
            
        else:
            assert not comment
            out += c
    
    # A 'open comment' is still processed
    if comment:
        translated = _translateComment(comment, fillCharacter, preserveNewLines)
        out += translated
    
    return out 
                

def printFirstFewItems (items, maxStrLen = 40):
    '''
    Create a string containing the 1st few 'items' in list, up to (approximately) 
    overall maxStrLen
    '''
    ret = ''
    for i in sorted (items):
        if len (ret) >= maxStrLen:
            ret += '...'
            break
        if ret:
            ret += ', '
        ret += str (i) 
    return ret
        

def removePrefixedItems (items, prefixSet):
    '''
    Returns 'items' in which elements (presumed strings) that
    begin with one of 'prefixSet' are *not* present (the remaining are passed intact).
    '''
    ret = []
    for i in items:
        ok = True 
        for p in prefixSet:
            if i.startswith (p):
                ok = False
        if ok:
            ret.append (i)
       
    # Try to adjust the actual return type to match the input (crazy, isn't it?): 
    if type (items) is list:
        return ret
    
    if type (items) is set:
        return set (ret)

    assert False, "unexpected input"


def sort_DAG(edge_list) :
    '''
    Topological sorting:
        http://code.activestate.com/recipes/578406-topological-sorting-again
        
    L ← Empty list that will contain the sorted elements
    S ← Set of all nodes with no incoming edges
    while S is non-empty do
        remove a node n from S
        insert n into L
        for each node m with an edge e from n to m do
            remove edge e from the graph
            if m has no other incoming edges then
                insert m into S
    if graph has edges then
        return error (graph has at least one cycle)
    else 
        return L (a topologically sorted order)    
        
    u = [
        ['a', 'b'], # a -> b, etc.
        ['a', 'c'],
        ['b', 'e'],
        ['c', 'd'],
        ['b', 'd'],
        ['e', 'f'],
        ['c', 'f'],
    ]
    
    >>> sort_direct_acyclic_graph(u)
    ['a', 'c', 'b', 'e', 'd', 'f']            
    '''
    
    assert type (edge_list) is list
    for e in edge_list:
        assert len (e) == 2
    
    if not edge_list:
        return []
    
    # edge_set is consumed, need a copy
    edge_set = set([tuple(i) for i in edge_list])
    
    # node_list will contain the ordered nodes
    node_list = list()
    
    # source_set is the set of nodes with no incomming edges
    node_from_list, node_to_list = zip(* edge_set) #pylint: disable = W0142
    source_set = set(node_from_list) - set(node_to_list)
    
    while len(source_set) != 0 :
        # pop node_from off source_set and insert it in node_list
        node_from = source_set.pop()
        
        node_list.append(node_from)
        
        # find nodes which have a common edge with node_from
        from_selection = [e for e in edge_set if e[0] == node_from]
        for edge in from_selection :
            # remove the edge from the graph
            node_to = edge[1]
            edge_set.discard(edge)
            
            # if node_to don't have any remaining incomming edge :
            to_selection = [e for e in edge_set if e[1] == node_to]
            if len(to_selection) == 0 :
                # add node_to to source_set
                source_set.add(node_to)
                
    if len(edge_set) != 0 :
        remainingStr = "Remaining edges:\n"
        for e in edge_set:
            remainingStr += str (e) + '\n'
        raise IndexError ("Not a direct acyclic graph: " + remainingStr)
    else :
        return node_list


class TreeNode(object):
    '''
    Data structure supporting pretty printing, like:
      'root'  
         'a'
           'son'
           'daughter'
         'b'
           'c'
           'd' 
    Credit: 
        http://stackoverflow.com/questions/20242479/printing-a-tree-datastructure-in-python
    '''
    def __init__(self, value, children, tab):
        self.value_ = value
        self.children_ = children
        self.tab_ = tab
        
    def __str__(self, level=0):
        ret = self.tab_ * level + repr (self.value_) + "\n"
        for child in self.children_:
            ret += child.__str__(level+1)
        return ret

    def __repr__(self):
        return '<tree node representation>'    
    
    def findNodeByValue (self, value, maxDepth):
        '''
        Find child with value_ == 'value'
        '''
        if maxDepth < 0:
            return None
        if self.value_ == value:
            return self
        for c in self.children_:
            cc = c.findChild (maxDepth - 1)
            if cc:
                return cc
                
        return None 
    
    def countNodes (self):
        ret = 1
        for c in self.children_:
            ret += c.countNodes()
        return ret
    
    @staticmethod
    def countNodesInList(nodes):
        ret = 0
        for n in nodes:
            ret += n.countNodes()
        return ret
    
    def findMaxDepth(self):
        ret = 1
        for c in self.children_:
            ret = max (ret, 1 + c.findMaxDepth())
        return ret
    
    @staticmethod
    def findMaxDepthInList(nodes):
        ret = 0
        for n in nodes:
            ret = max (ret, n.findMaxDepth())
        return ret
    
    @staticmethod
    def createRecursively (rootAndChildren, tab):
        '''
        Creates it from recursive pairs (value, children)
        (1, (2 (3, 4))) ->
        1
          2
            3
            4   
        '''
        if type (rootAndChildren) is not tuple:
            return TreeNode (rootAndChildren, [], tab)
            
        assert len (rootAndChildren) == 2
        
        root, children = rootAndChildren
        if type (children) in [list, tuple]:
            children = list (children)
        else:
            children = [children] 
        
        childrenNodes = []
        for c in children:
            childNode = TreeNode.createRecursively (c, tab)
            childrenNodes.append (childNode)
            
        return TreeNode (root, childrenNodes, tab)
    
                
##########################################################################################
# Debug code:
if __name__ == "__main__":
    pass


