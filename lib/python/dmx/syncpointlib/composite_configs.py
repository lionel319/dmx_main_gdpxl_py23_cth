#!/usr/bin/env python
'''
$Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/dmx/syncpointlib/composite_configs.py#1 $
$Change: 7411538 $
$DateTime: 2022/12/13 18:19:49 $
$Author: lionelta $

Description: Utility classes to read an individual Composite Config or a hierarchy of Composite Configs

Author: Rudy Albachten
Copyright (c) Altera Corporation 2012
All rights reserved.
'''
from __future__ import print_function
from builtins import zip
from builtins import str
from builtins import object
import re
import logging

from dmx.abnrlib.command import Command
from dmx.utillib.utils import run_command
import dmx.abnrlib.icm
import dmx.syncpointlib.simple_configs

LOGGER = logging.getLogger(__name__)

class Error(Exception): pass 
class RecursionError(Error): pass 
class CompositeConfigLoadError(Error): pass

def _keyvalstring_to_dict(line):
    '''take a string like "a:b c:d foo:10" and turn it into a dictionary
    NOTE: key cannot have whitespace but value can'''
    result = {}
    prevkey = None
    for keyval in line.split(' '):
        try:
            key, value = keyval.split(':')
            result[key] = value
            prevkey = key
        except ValueError:
            # if this "keyval" doesn't have a ':' it is part of the previous config name
            result[prevkey] += " "
            result[prevkey] += keyval
    return result

class CompositeConfig(object):
    '''A single composite config'''

    def __init__(self, project, variant, config):
        '''read a single composite config'''
        self.project = project
        self.variant = variant
        self.config  = config
        cmd = "icmp4 print '//depot/icm/configs/%s/%s/%s.icmCfg'" % (project, variant, config)
        (status, stdout, stderr) = run_command(cmd)
        if status != 0 or stderr:
            raise CompositeConfigLoadError("Cannot read configuration: %s %s %s" % (project, variant, config))
        lines = str(stdout).split('\n')
        firstline = lines.pop(0)
        self.path = re.match(r'(.*\.icmCfg#\d+) - ', firstline).group(1)
        self.data = [_keyvalstring_to_dict(line) for line in lines if line != ""]

    def get_pvc(self):
        return (self.project, self.variant, self.config)

    def get_configname(self):
        return self.config

    def get_name(self):
        return "%s/%s/%s" % self.get_pvc()

    def dump(self):
        '''dump the config'''
        print("COMPOSITE CONFIG", self.path)
        for entry in self.data:
            print("    ", entry)

    def get_libtypes(self):
        '''return a list of (libtype, config) tuples for the local simple configs'''
        return [(entry['L'], entry['C']) for entry in self.data if entry.get('T') == 'local']

    def get_simple_configs(self):
        result = []
        for libtype, config in self.get_libtypes():
            result.append(abnrlib.simple_configs.SimpleConfig(self.project, self.variant, libtype, config))
        return result

    def get_libraries(self):
        '''return a list of (libtype, library, release, config) tuples for the local simple configs'''
        project = self.project
        variant = self.variant
        config = self.config
        cmd = "pm configuration -l %(project)s %(variant)s -n %(config)s -D+MaGiC+" % vars()
        (status, stdout, stderr) = run_command(cmd)
        if status != 0 or stderr:
            LOGGER.error("Cannot read configuration: %s %s %s", project, variant, config)
            assert(0)
            return
        lines = [x.split('+MaGiC+') for x in str(stdout).strip().split('\n')]

        # Stupid icmanage bug
        if lines[2] != ["Project", "Variant", "LibType", "Library", "Release", "Configuration", "Location", "Description"]:
            lines[2:2] = [["Project", "Variant", "LibType", "Library", "Release", "Configuration", "Location", "Description"]]

        assert(lines[0] == ["Configuration", "ConfType", "Desc", "LibDefsPath"])
        assert(lines[2] == ["Project", "Variant", "LibType", "Library", "Release", "Configuration", "Location", "Description"])
        result = []
        for line in lines[3:]:
            category_and_proj, var, libtype, lib, rel, config, location, desc = line
            if var == variant:
                result.append((libtype, lib, rel, config))
        return sorted(result)

    def get_libtypes_for_tree(self):
        '''return a set of libtypes in the config subtree'''
        result = set()
        for libtype, lib, rel, config in self.get_libraries():
            result.add(libtype)
        return result

    def get_items(self):
        items = []
        for entry in self.data:
            if entry['T'] == 'local':
                config = entry['C']
                libtype = entry['L']
                item = "%(config)s@%(libtype)s" % vars()
                items.append(item)
            elif entry['T'] == 'foreign':
                config = entry['C']
                project = entry['P']
                variant = entry['V']
                item = "%(config)s@%(project)s/%(variant)s" % vars()
                items.append(item)
        return items

    def get_children(self):
        '''return a list of (project, variant, config) tuples for the foreign children of this config'''
        return [(entry['P'], entry['V'], entry['C']) for entry in self.data if entry.get('T') == 'foreign']

    def replace_config(self, project, variant, config1, config2):
        for entry in self.data:
            if entry.get('T') == 'foreign' and entry['P'] == project and entry['V'] == variant and entry['C'] == config1:
                entry['C'] = config2

    def check_rel_configs(self, allowsnaps=False):
        '''Make sure all the simple and composite configs this references are named RELxxx'''
        errors = 0
        project = self.project
        variant = self.variant
        config = self.config
        for (project2, variant2, config2) in self.get_children():
            if allowsnaps:
                if not config2.startswith(('REL', 'snap-')):
                    LOGGER.error('Config references a non-REL and non-snap composite config: %(project2)s/%(variant2)s/%(config2)s' % vars())
                    errors += 1
            else:
                if not config2.startswith('REL'):
                    LOGGER.error('Config references a non-REL composite config: %(project2)s/%(variant2)s/%(config2)s' % vars())
                    errors += 1
        for (libtype2, config2) in self.get_libtypes():
            if allowsnaps:
                if not config2.startswith(('REL', 'snap-')):
                    LOGGER.error('Config references a non-REL and non-snap simple config: %(libtype2)s/%(config2)s' % vars())
                    errors += 1
            else:
                if not config2.startswith('REL'):
                    LOGGER.error('Config references a non-REL simple config: %(libtype2)s/%(config2)s' % vars())
                    errors += 1
        return errors

class CompositeConfigHierarchy(object):
    '''a hierarchy of composite configs'''

    def __init__(self, project, variant, config):
        '''Recursively load all the configs in a composite config hierarchy'''
        self.project = project
        self.variant = variant
        self.config = config
        self._data = {}
        self.libraries = None
        active = {}
        def _load_composite_config(project, variant, config):
            '''private helper for recursively loading composite configs'''
            if (project, variant, config) in self._data:
                return
            if (project, variant, config) in active:
                raise RecursionError("Recursion detected for configuration %s %s %s" % (project, variant, config))
            config_data = CompositeConfig(project, variant, config)
            self._data[project, variant, config] = config_data
            active[project, variant, config] = True
            for project2, variant2, config2 in config_data.get_children():
                _load_composite_config(project2, variant2, config2)
            del active[project, variant, config]
        _load_composite_config(project, variant, config)

    def dump(self):
        '''dump all the configs and their contents to stdout'''
        for project2, variant2, config2 in sorted(self._data.keys()):
            self._data[project2, variant2, config2].dump()

    def show(self, tree=False, show_simple=False, nohier=False, show_libraries=False, labels=True, nochildren=False, show_user=False):
        '''show all the configs in the hierarchy
           Overall format:
               default mode: each config is listed once with no indentation
               "tree" mode: configs are shown in an indented tree and may be listed multiple times
           Simple configs are not shown unless "show_simple" is set
           '''
        if nochildren:
            tree = False
            show_libraries = False
            show_simple = False
        elif show_libraries:
            show_simple = True
        active = set()
        def _printline(prefix, labelnames, values, user=None):
            line = prefix
            assert(len(labelnames) == len(values))
            first = True
            if user:
                labelnames.append('user')
                values.append(user)
            for lab, val in zip(labelnames, values):
                if first:
                    first = False
                else:
                    line += ' '
                if labels:
                    line += "%(lab)s: %(val)s" % vars()
                else:
                    line += "%(val)s" % vars()
            print(line)
        def _show_tree(project, variant, config, indent=""):
            '''private helper for recursively showing composite configs in a tree view'''
            newindent = indent + "  "
            assert((project, variant, config) not in active)
            active.add((project, variant, config))
            config_data = self._data[project, variant, config]
            user = abnrlib.icm.get_config_username(project, variant, config) if show_user else None
            _printline(indent, ['composite_config'], ["%(project)s/%(variant)s/%(config)s" % vars()], user=user)
            if show_simple:
                for libtype, libconfig in config_data.get_libtypes():
                    user = abnrlib.icm.get_simple_config_username(project, variant, libtype, libconfig) if show_user else None
                    _printline(newindent, ['simple_config'], ['%(libtype)s/%(libconfig)s' % vars()], user=user)
                    if show_libraries:
                        for project2, variant2, libtype2, library, release, config2 in self._get_librefs(project, variant, libconfig, libtype):
                            _printline(newindent, ['library', 'release'], [library, release])
            for project2, variant2, config2 in config_data.get_children():
                _show_tree(project2, variant2, config2, newindent)
            active.remove((project, variant, config))

        if nohier:
            project, variant, config = self.project, self.variant, self.config
            config_data = self._data[project, variant, config]
            user = abnrlib.icm.get_config_username(project, variant, config) if show_user else None
            _printline("", ['config'], ["%(project)s/%(variant)s/%(config)s" % vars()])
            if show_simple:
                for libtype, libconfig in config_data.get_libtypes():
                    user = abnrlib.icm.get_simple_config_username(project, variant, libtype, libconfig) if show_user else None
                    _printline("    ", ['simple_config'], ["%(libtype)s/%(libconfig)s" % vars()], user=user)
                    if show_libraries:
                        for project2, variant2, libtype2, library, release, config2 in self._get_librefs(project, variant, libconfig, libtype):
                            _printline("      ", ['library', 'release'], [library, release])
            if not nochildren:
                for project2, variant2, config2 in config_data.get_children():
                    user = abnrlib.icm.get_config_username(project2, variant2, config2) if show_user else None
                    _printline("    ", ['composite_config'], ["%(project2)s/%(variant2)s/%(config2)s" % vars()], user=user)
        elif tree:
            _show_tree(self.project, self.variant, self.config)
        else:
            for project, variant, config in self.get_configs():
                config_data = self._data[project, variant, config]
                user = abnrlib.icm.get_config_username(project, variant, config) if show_user else None
                _printline("", ["composite_config"], ["%(project)s/%(variant)s/%(config)s" % vars()], user=user)
                if show_simple:
                    for libtype, libconfig in config_data.get_libtypes():
                        user = abnrlib.icm.get_simple_config_username(project, variant, libtype, libconfig) if show_user else None
                        _printline("    ", ["simple_config"], ["%(libtype)s/%(libconfig)s" % vars()], user=user)
                        if show_libraries:
                            for project2, variant2, libtype2, library, release, config2 in self._get_librefs(project, variant, libconfig, libtype):
                                _printline("      ", ['library', 'release'], [library, release])
                if not nochildren:
                    for project2, variant2, config2 in config_data.get_children():
                        user = abnrlib.icm.get_config_username(project2, variant2, config2) if show_user else None
                        _printline("    ", ["composite_config"], ["%(project2)s/%(variant2)s/%(config2)s" % vars()], user=user)

    def check_activerel_activedev(self):
        '''Check a config tree to make sure there aren't any activerel or activedev library references'''
        errors = 0
        for project, variant, config in self.get_configs():
            config_data = self._data[project, variant, config]
            for libtype, libconfig in config_data.get_libtypes():
                for project2, variant2, libtype2, library, release, config2 in self._get_librefs(project, variant, libconfig, libtype):
                    if release in ('#ActiveDev', '#ActiveRel'):
                        errors += 1
                        print("ERROR: found %(release)s reference:" % vars(), end=' ')
                        print("%(project)s/%(variant)s/%(config)s" % vars(), end=' ')
                        print("-> %(project)s/%(variant)s/%(libtype)s/%(libconfig)s" % vars(), end=' ')
                        print("-> %(library)s" % vars(), end=' ')
                        print("-> %(release)s" % vars())
        return errors

    def check_simple_config_names(self, names):
        '''Check a config tree to make sure all simple configs are named 'RELxxx' 'snap-xxx' etc'''
        assert(isinstance(names, tuple))
        assert(len(names) >= 1)
        errors = 0
        for project, variant, config in self.get_configs():
            config_data = self._data[project, variant, config]
            for libtype, libconfig in config_data.get_libtypes():
                if not libconfig.startswith(names):
                    errors += 1
                    if len(names) > 1:
                        print("ERROR: all referenced simple configs must start with one of %s:" % str(names), end=' ')
                    else:
                        print("ERROR: all referenced simple configs must start with %s:" % names[0], end=' ')
                    print("%(project)s/%(variant)s/%(config)s" % vars(), end=' ')
                    print("-> %(project)s/%(variant)s/%(libtype)s/%(libconfig)s" % vars())
        return errors

    def check_clone_hier(self, newconfig, check_simple_configs, reuse_prefixes):
        '''check that none of the destination configs exist'''
        active = {}
        done = {}
        destconfigs = {}
        # make sure reuse_prefixes is a tuple, not a list or some other kind of sequence
        assert(isinstance(reuse_prefixes, tuple))
        def _check(project, variant, config, newconfig):
            '''private helper for recursively checking composite configs'''
            errors = 0
            if (project, variant, config) in done:
                return 0
            assert((project, variant, config) not in active)
            active[project, variant, config] = True
            config_data = self._data[project, variant, config]
            if check_simple_configs:
                for libtype, libtypeconfig in config_data.get_libtypes():
                    if not libtypeconfig.startswith(reuse_prefixes) and abnrlib.icm.config_exists(project, variant, libtype, newconfig):
                        LOGGER.error("Simple config already exists: Project=%(project)s Variant=%(variant)s Libtype=%(libtype)s Config=%(newconfig)s" % vars())
                        errors += 1
            for project2, variant2, config2 in config_data.get_children():
                reuse = config2.startswith(reuse_prefixes)
                destconfig = config2 if reuse else newconfig
                if (project2, variant2) in destconfigs:
                    prevconfig = destconfigs[project2, variant2]
                    if prevconfig != destconfig:
                        LOGGER.error("Cloned hierarchy would contain conflicting versions of %s/%s: %s and %s", project2, variant2, prevconfig, destconfig)
                        errors += 1
                else:
                    destconfigs[project2, variant2] = destconfig
                if not config2.startswith(reuse_prefixes):
                    errors += _check(project2, variant2, config2, destconfig)
            del active[project, variant, config]
            done[project, variant, config] = True
            if abnrlib.icm.composite_config_exists(project, variant, newconfig):
                LOGGER.error("Composite config already exists: Project=%(project)s Variant=%(variant)s Config=%(newconfig)s" % vars())
                errors += 1
            return errors
        errors = _check(self.project, self.variant, self.config, newconfig)
        return errors == 0

    def clone_hier(self, newconfig, echo, execute, clone_simple_configs, reuse_prefixes):
        '''do a bottoms-up clone of the config hierarchy to a new config name'''

        active = {}
        done = {}
        # make sure reuse_prefixes is a tuple, not a list or some other kind of sequence
        assert(isinstance(reuse_prefixes, tuple))
        def _clone(project, variant, config, newconfig):
            '''private helper for recursively cloning composite configs'''
            if (project, variant, config) in done:
                return
            assert((project, variant, config) not in active)

            active[project, variant, config] = True
            config_data = self._data[project, variant, config]
            child_items = []

            # get the local simple configs, clone them if clone_simple_configs is True
            for libtype, libtypeconfig in config_data.get_libtypes():
                if clone_simple_configs and not libtypeconfig.startswith(reuse_prefixes):
                    cmd = "pm configuration %(project)s %(variant)s %(libtypeconfig)s -n %(newconfig)s -t %(libtype)s" % vars()
                    if newconfig.startswith(('REL', 'snap-')):
                        abnrlib.icm.write_rel_config(cmd)
                    else:
                        Command.do_command(cmd)
                    item = "%s@%s" % (newconfig, libtype)
                else:
                    item = "%s@%s" % (libtypeconfig, libtype)
                child_items.append(item)

            for project2, variant2, config2 in config_data.get_children():
                if config2.startswith(reuse_prefixes):
                    child_items.append("%(config2)s@%(project2)s/%(variant2)s" % vars())
                else:
                    _clone(project2, variant2, config2, newconfig)
                    child_items.append("%(newconfig)s@%(project2)s/%(variant2)s" % vars())
            del active[project, variant, config]
            done[project, variant, config] = True

            cmd = " ".join(["pm configuration %(project)s %(variant)s %(newconfig)s" % vars()] + child_items)
            if newconfig.startswith(('REL', 'snap-')):
                abnrlib.icm.write_rel_config(cmd)
            else:
                Command.do_command(cmd)

        _clone(self.project, self.variant, self.config, newconfig)

    def get_config(self, project, variant, config):
        return self._data[project, variant, config]

    def get_configs_bottom_up(self):
        '''return (p,v,c)'s in bottoms up order'''
        done = {}
        results = []
        def _helper(project, variant, config):
            '''private helper for recursively walking the tree'''
            if (project, variant, config) in done:
                return
            config_data = self._data[project, variant, config]
            for project2, variant2, config2 in config_data.get_children():
                _helper(project2, variant2, config2)
            done[project, variant, config] = True
            results.append(self._data[project, variant, config])
        _helper(self.project, self.variant, self.config)
        return results

    def get_configs_top_down(self):
        '''return (p,v,c)'s in top down order'''
        results = []
        parents = {}
        queue = [(self.project, self.variant, self.config)]
        done = set()
        notdone = set([pvc for pvc in self._data])

        # build parents map
        for (project, variant, config), config_data in list(self._data.items()):
            parents.setdefault((project, variant, config), set())
            for project2, variant2, config2 in config_data.get_children():
                parents.setdefault((project2, variant2, config2), set()).add((project, variant, config))

        while queue:
            pvc = queue.pop()
            results.append(self._data[pvc])
            notdone.remove(pvc)
            done.add(pvc)
            for pvc2 in self._data[pvc].get_children():
                parents[pvc2].remove(pvc)
                if not parents[pvc2] and pvc2 not in done:
                    queue.append(pvc2)
        return results

    def get_all_configs(self):
        return list(self._data.values())

    def get_configs(self):
        '''return (p,v,c)'s in alphabetical order'''
        return sorted(self._data.keys())

    def check_config_consistency(self, merge_equivalent=False):
        '''Check for different configs of a variant referenced from different places in the config hierarchy'''
        data = {}
        errors = 0
        for config_data in self.get_configs_top_down():
            for project2, variant2, config2 in config_data.get_children():
                data.setdefault((project2, variant2), {}).setdefault(config2, []).append(config_data.get_name())
        for project, variant in data:
            if len(data[project, variant]) > 1:
                if merge_equivalent and self._all_equivalent(project, variant, data[project, variant]):
                    LOGGER.warn("Multiple equivalent configurations of %(project)s %(variant)s found:" % vars())
                    confignames = list(data[project, variant].keys())
                    configname1 = confignames[0]
                    for configname2 in confignames[1:]:
                        self._replace_config(project, variant, configname1, configname2)
                    for config in data[project, variant]:
                        for source in data[project, variant][config]:
                            LOGGER.warn("  %(project)s/%(variant)s/%(config)s called from %(source)s" % vars())
                else:
                    errors += 1
                    LOGGER.error("Multiple configurations of %(project)s %(variant)s found:" % vars())
                    for config in data[project, variant]:
                        for source in data[project, variant][config]:
                            LOGGER.error("  %(project)s/%(variant)s/%(config)s called from %(source)s" % vars())
        return not errors

    def _replace_config(self, project, variant, configname1, configname2):
        # first replace all references to configname2 with configname1
        for project2, variant2, config2 in self.get_configs():
            config_data = self._data[project2, variant2, config2]
            config_data.replace_config(project, variant, configname2, configname1)
        # then delete the now unused config
        del self._data[(project, variant, configname2)]

    def _all_equivalent(self, project, variant, configs):
        confignames = list(configs.keys())
        configname1 = confignames[0]
        for configname2 in confignames[1:]:
            if not self._equivalent(project, variant, configname1, configname2):
                return False
        return True

    def get_libraries(self):
        if not self.libraries:
            self.libraries = self._get_librefs(self.project, self.variant, self.config)
        return self.libraries

    def _get_librefs(self, project, variant, config, libtype=None): # pylint: disable=R0201
        cmd = "pm configuration -l %(project)s %(variant)s -n %(config)s -D+MaGiC+" % vars()
        if libtype:
            cmd += " -t %(libtype)s" % vars()
        (status, stdout, stderr) = run_command(cmd)
        if status != 0 or stderr:
            LOGGER.error("Cannot read configuration: %s %s %s", project, variant, config)
            return False
        lines = [x.split('+MaGiC+') for x in str(stdout).strip().split('\n')]

        # stupid icmanage bug
        if lines[2] != ['Project', 'Variant', 'LibType', 'Library', 'Release', 'Configuration', 'Location', 'Description']:
            lines[2:2] = [['Project', 'Variant', 'LibType', 'Library', 'Release', 'Configuration', 'Location', 'Description']]

        assert(lines[0] == ['Configuration', 'ConfType', 'Desc', 'LibDefsPath'])
        assert(lines[2] == ['Project', 'Variant', 'LibType', 'Library', 'Release', 'Configuration', 'Location', 'Description'])
        result = []
        for line in lines[3:]:
            category_and_proj, var, libtype, lib, rel, config, location, desc = line
            proj = category_and_proj.split(':')[-1] if ':' in category_and_proj else category_and_proj
            result.append((proj, var, libtype, lib, rel, config))
        return sorted(result)

    def _equivalent(self, project, variant, config1, config2):
        refs1 = self._get_librefs(project, variant, config1)
        refs2 = self._get_librefs(project, variant, config2)
        return refs1 == refs2
