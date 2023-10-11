#!/usr/bin/env python

import xmlrpclib

ip = 'http://scc919025.sc.intel.com:8000'
ip = 'http://localhost:8000'

s = xmlrpclib.ServerProxy(ip)
print s.pow(2,3)  # Returns 2**3 = 8
print s.add(2,3)  # Returns 5
print s.div(5,2)  # Returns 5//2 = 2

print s.run_command('ls -al')

# Print list of available methods
print s.system.listMethods()
