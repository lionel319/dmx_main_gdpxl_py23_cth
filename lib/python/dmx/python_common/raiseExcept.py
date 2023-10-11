
#Module to raise exceptions within the uiTypeCheck module

import sys
import os
import argparse
import datetime
import logging

def raiseE(excName, dispFullExc, excMssg=''):
	print "----------------------------------------------------------------------------"
	print 'FINAL RESULT: CRITICAL ERROR - UNABLE TO PROCEED'
	print 'The program has encountered a %s exception' % excName 
	if (excMssg != ''):
		print excMssg 
	if (dispFullExc == True):
		print '************************EXCEPTION INFORMATION BELOW************************'
		raise
	pass

