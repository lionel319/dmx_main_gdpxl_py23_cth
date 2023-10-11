#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/helplib/help_plugins/map.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description:  help: A glossary and mapping of dmx commands and options to abnr commands and options

Author: Natalia Baklitskaya
        Kevin Lim
	Tara Clark

Copyright (c) Altera Corporation 2016
All rights reserved.
'''

print '\tWelcome to Data Management eXchange!'
print '\tThis page summarizes the mapping from the previous DM system to DMX'
print '\tNote that it does not describe all the available arguments'
print '\tUse \'dmx help\' for the full list of options, functionality and examples\n'
print "For detail/summary help of each command:"
print "\tdmx help <command>"
print "\tdmx help <command> <subcommand>\n"
print 'Glossary:'
print '\tProject = ICManage Project'
print '\tIP = ICManage Variant'
print '\tDeliverable = ICManage Libtype'
print '\tBOM (Bill of Materials) = ICManage Configuration\n'
print 'Mapping below follows this template:'
print '\tNadder option/command = DMX option/command\n'
print 'Options mapping:'
print '\t-v/--variant = -i/--ip'
print '\t-l/--libtype = -d/--deliverable'
print '\t-c/--config = -b/--bom\n'
print 'Commands mapping:'
print '\tabnr buildconfig = dmx bom create'
print '\tabnr checkconfigs = dmx bom validate'
print '\tabnr delconfig = dmx bom delete'
print '\tabnr latest = dmx bom latest'
print '\tabnr edittree = dmx bom edit'
print '\tabnr branchlib = dmx derive bom -p -i -b -d'
print '\tabnr branchrel = dmx derive bom -p -i -b'
print '\tabnr cloneconfigs = dmx clone bom'
print '\tabnr clonewith rels = dmx clone bom --replace-with-rels'
print '\tabnr proliferate = dmx derive proliferate'
print '\tabnr releaselib = dmx release -p -i -b -d'
print '\tabnr releasevariant = dmx release -p -i -b'
print '\tabnr releasetree = dmx release -p -i -b --hierarchy'
print '\tabnr createsnapshot = dmx snap -p -i -b -d'
print '\tabnr snaptree = dmx snap -p -i -b'
print '\tabnr createvariant = dmx ip create'
print '\tabnr updatevariant = dmx ip update'
print '\tabnr owner = dmx report owner'
print '\tabnr diffconfigs = dmx report diff'
print '\tabnr graphconfig = dmx report graph'
print '\tabnr printconfig = dmx report content'
print '\tabnr roadmap = dmx roadmap'    
print '\tabnr list = dmx report list'
print '\tabnr bom = dmx report content --verbose'
print '\tabnr print = dmx report content --file'
print '\tquick check = dmx workspace check'
print '\tquick propagate = dmx ip propagate'
print '\tquick reporttree = dmx report tree'        
print '\tquick workspace create = dmx workspace create'
print '\tquick workspace sync = dmx workspace sync'
print '\tquick workspace list = dmx workspace list'
print '\tquick workspace info = dmx workspace info'
print '\tquick workspace delete = dmx workspace delete'
print '\tfester = dmx roadmap -p -i -d\n'
print 'Additional info on \'dmx roadmap\':'
print '\tBoth roadmap and manifest info are available from \'dmx roadmap\''
print '\tIn future patch, roadmap and manifest info will be split into each individual'
print '\t  command, named \'dmx roadmap\' and another command which has yet to be named\n'
print 'Untested commands:'
print '(All commands are tested on PICE except these due to lack of design data during bring-up)'
print '\tdmx derive proliferate'
print 'ABNR commands that are not available in this DMX veresion yet:'
print '\tabnr releaselibsintree\n'
print 'Deprecated Nadder ABNR commands:'
print '\tquick publish'
print '\tquick subscribe'
print '\tquick notification'
print '\tabnr replacetree'
print '\tabnr configinfo'
print '\tabnr deliverables'
print '\tabnr showconfig'
print '\tabnr showconfigs'
print '\tabnr showdiffs\n'
