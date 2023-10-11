#!/usr/bin/env python

import sys
import os
import logging
import dmx.abnrlib.config_factory
import dmx.abnrlib.icm


LOGGER = logging.getLogger()

def main():
    icm = dmx.abnrlib.icm.ICManageCLI()

    project = 'Falcon_Mesa'
    variant = 'z1574b'
    config = 'REL4.0FM6revB0__20ww480a'

    '''
    project = 'i10socfm'
    variant = 'liotestfc1'
    config = 'dev'
    config = 'REL3.0FM6revA0__18ww094a'
    '''

    cf = dmx.abnrlib.config_factory.ConfigFactory.create_from_icm(project, variant, config)

    for a in cf.flatten_tree():
        if a.is_composite():
            print 'variant: {}'.format(a.variant)
            print 'project: {}'.format(a.project)
            print 'iptype: {}'.format(icm.get_variant_properties(a.project, a.variant)['Variant Type'])

            subips = []
            for c in a.configurations:
                if c.is_composite():
                    subips.append('{}/{}'.format(c.project, c.variant))
            print 'subips: {}'.format(' '.join(subips))
            print '=========================='



if __name__ == '__main__':
    if '--debug' in sys.argv:
        logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.INFO)
    main()
