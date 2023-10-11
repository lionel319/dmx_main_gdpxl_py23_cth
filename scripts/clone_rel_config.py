#!/usr/bin/env python

import argparse
import os, sys
import re
import logging
LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib', 'python')
sys.path.insert(0, LIB)
from dmx.utillib.utils import *
from dmx.abnrlib.icm import ICManageCLI
from dmx.abnrlib.config_factory import ConfigFactory
from dmx.abnrlib.config_naming_scheme import ConfigNamingScheme

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--project', required=True)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('-n', '--preview', action='store_true')
    parser.add_argument('--thread', '-t', required=True)
    parser.add_argument('--from-milestone', '-m', required=True)
    parser.add_argument('-v', '--variant')
    args = parser.parse_args()
    project = args.project
    thread = args.thread
    debug = args.debug
    from_milestone = int(args.from_milestone.replace('.',''))
    preview = args.preview
    variant = args.variant

    if debug:
        LOGGER.setLevel(logging.DEBUG)


    cli = ICManageCLI(preview=preview)
    if variant:
        variants = [variant]
    else:
        variants = cli.get_variants(project)

    for variant in variants:
        LOGGER.info('Looking for RELs in variant {}'.format(variant))
        # Get all config that begins with REL
        rel_configs = cli.get_rel_configs(project, variant)

        # Get all REL configs that follow naming convention
        proper_rel_configs = []
        for rel_config in rel_configs:
            try:
                rel_data = ConfigNamingScheme.get_data_for_release_config(rel_config)
            except:
                continue
            if rel_data:
                rel_milestone = int(rel_data['milestone'].replace('.',''))
                if rel_milestone >= from_milestone:
                    proper_rel_configs.append(rel_config)

        # Create ConfigFactory object
        for rel_config in proper_rel_configs:
            oldconfigobj = ConfigFactory.create_from_icm(project, variant, rel_config, preview=preview)
            LOGGER.info('Renaming {}'.format(oldconfigobj))
            
            rel_data = ConfigNamingScheme.get_data_for_release_config(oldconfigobj.config)
            oldrelprefix = 'REL{}{}'.format(rel_data['milestone'], rel_data['thread'])
            newrelprefix = 'REL{}{}'.format(rel_data['milestone'], thread)
            newconfigname = oldconfigobj.config.replace(oldrelprefix, newrelprefix)
            if cli.config_exists(oldconfigobj.project, oldconfigobj.variant, newconfigname):
                LOGGER.info('{} exists, skipping'.format(newconfigname))
                continue
            else:
                configobj = oldconfigobj.clone(newconfigname)

            for config in configobj.flatten_tree():
                rel_data = ConfigNamingScheme.get_data_for_release_config(config.config)
                if not rel_data:
                    # if confignamingscheme cannot grab the milestone and thread, we have to get it the old fashioned way
                    m = re.match('REL([0-9.]{3})([A-Z0-9]{3})rev', config.config)
                    if m:            
                        rel_data = {
                                'milestone': m.group(1),
                                'thread': m.group(2)
                                }
                    else:
                        raise Exception('Failed to get milestone and thread for {}'.format(config.config))

                oldrelprefix = 'REL{}{}'.format(rel_data['milestone'], rel_data['thread'])
                newrelprefix = 'REL{}{}'.format(rel_data['milestone'], thread)
                newconfigname = config.config.replace(oldrelprefix, newrelprefix)

                if config.is_simple():
                    newconfig_exist = cli.config_exists(config.project, config.variant, newconfigname, libtype=config.libtype)
                else:
                    newconfig_exist = cli.config_exists(config.project, config.variant, newconfigname)

                if newconfig_exist:
                    if config.is_simple():
                        newconfigobj = ConfigFactory.create_from_icm(config.project, config.variant, newconfigname, libtype=config.libtype)
                    else:
                        newconfigobj = ConfigFactory.create_from_icm(config.project, config.variant, newconfigname)
                    LOGGER.info('{} exists, replacing into config ...'.format(newconfigobj))
                else:
                    newconfigobj = config.clone(newconfigname)
                    LOGGER.info('{} does not exist, cloning ...'.format(newconfigobj))

                if newconfigobj.is_simple():
                    configobj.replace_all_instances_in_tree(newconfigobj.project, newconfigobj.variant, newconfigobj, libtype=newconfigobj.libtype)
                else:
                    configobj.replace_all_instances_in_tree(newconfigobj.project, newconfigobj.variant, newconfigobj)


            LOGGER.info('Saving {}'.format(configobj))
            if not preview:
                configobj.save()

















 




if __name__ == '__main__':
    logging.basicConfig(format="%(levelname)s [%(asctime)s]: %(message)s")
    LOGGER.setLevel(logging.INFO)
    main()
    sys.exit(0)

