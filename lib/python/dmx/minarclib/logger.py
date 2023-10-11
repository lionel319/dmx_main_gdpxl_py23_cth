import datetime

class Logger():

    def __init__(self):
        self._fh = open('minarc-preprocess-log.txt', 'a')

    def info(self, string):
        self._fh.write('[I] '+str(datetime.datetime.now())+': '+string+'\n')

    def warn(self, string):
        self._fh.write('[W] '+str(datetime.datetime.now())+': '+string+'\n')

    def error(self, string):
        self._fh.write('[E] '+str(datetime.datetime.now())+': '+string+'\n')



