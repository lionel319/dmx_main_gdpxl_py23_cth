class MyRouter(object):

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'testdb':
            return 'testdb'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'testdb':
            return 'testdb'
        return None

    
