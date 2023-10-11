# $Header: //depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python/py23comlib/arc_utils/1.7_py23/arc_orm/arc_orm_settings.py#1 $
SECRET_KEY = 'good_enough'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'djarc',
        'USER': 'arcreader',
        'PASSWORD': 'not.writer',
        'HOST': 'sj-arc-db2'
    },
    'sj-arc': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'arc',
        'USER': 'arcreader',
        'PASSWORD': 'not.writer',
        'HOST': 'sj-arc-db2'
    },
    'sj-ice-arc': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'arc',
        'USER': 'arcreader',
        'PASSWORD': 'not.writer',
        'HOST': 'sj-arc-db2'
    },
    'pg-arc': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'arc',
        'USER': 'arcreader',
        'PASSWORD': 'not.writer',
        'HOST': 'pg-arc-db2'
    },
    'to-arc': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'arc',
        'USER': 'arcreader',
        'PASSWORD': 'not.writer',
        'HOST': '137.57.142.63'
    },
    'psg-png-arc.png.intel.com': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'arc',
        'USER': 'arcreader',
        'PASSWORD': 'not.writer',
        'HOST': 'pgpnghubarcdb1.png.intel.com.',
    },
    'psg-sc-arc.sc.intel.com': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'arc',
        'USER': 'arcreader',
        'PASSWORD': 'not.writer',
        'HOST': 'scyarcdb5.zsc7.intel.com.'
    },
    'png': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'arc',
        'USER': 'arcreader',
        'PASSWORD': 'not.writer',
        'HOST': 'pgpnghubarcdb1.png.intel.com.',
    },
    'zsc7': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'arc',
        'USER': 'arcreader',
        'PASSWORD': 'not.writer',
        'HOST': 'scyarcdb5.zsc7.intel.com.'
    },
    'sc': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'arc',
        'USER': 'arcreader',
        'PASSWORD': 'not.writer',
        'HOST': 'scyarcdb5.zsc7.intel.com.'
    },
}
