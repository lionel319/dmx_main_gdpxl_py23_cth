import os as _os
import sys as _sys
import datetime
import shutil
from functools import wraps as _wraps


def trace(tmp_path='/tmp'):
    def decorated(func):
        @_wraps(func)
        def wrapper():

            try:

                if not(_os.path.exists(tmp_path)):
                    raise NotADirectoryError("Directory not found")

                 # date and time
                i = datetime.datetime.now()
                i = i.strftime('%Y-%m-%d-%H_%M_%S')
                dst_path = (_os.path.join(tmp_path , _os.environ["USER"]+'_'+i))

                _os.mkdir(dst_path)
               
                # cmd
                with open(_os.path.join(dst_path, 'cmd'), 'w') as f:
                    f.write('{} {}' .format(_os.path.basename(_sys.argv[0]), " ".join(_sys.argv[1:])))
                    f.close()

                func()

            except NotADirectoryError:
                func()

        return wrapper
    return decorated

