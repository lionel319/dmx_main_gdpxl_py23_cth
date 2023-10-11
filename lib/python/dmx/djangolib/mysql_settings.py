SECRET_KEY = 'good_enough'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'CLINKZ',
        'USER': 'killim',
        'PASSWORD': 'killim',
        'HOST': 'pg-icesql1'
    },
    'testdb': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'DMXTEST',
        'USER': 'killim',
        'PASSWORD': 'killim',
        'HOST': 'pg-icesql1'
    },

}
DATABASE_ROUTERS = ['djangolib.routers.MyRouter']

