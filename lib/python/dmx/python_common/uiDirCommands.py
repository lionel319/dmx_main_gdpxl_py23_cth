import os as _os
import sys as _sys
import shutil as _shutil
from uiExceptions import permissionError


#########################################################
# dir_accessible
# Check if a directory exists and is accessible.
#########################################################
def dir_accessible(path, access) :

    if (_os.path.isdir(path) and _os.access(path, access)) :
        return True

    return False

#########################################################
# rm_dir
# Delete a directory
#########################################################
def remove_dir(path):

    if dir_accessible(path, _os.W_OK) and not(dir_accessible(path, _os.W_OK)):

        if _sys.version_info[0] == 3:
            raise PermissionError("No permission. Can't delete the folder {}." .format(path))
        else:
            raise permissionError("No permission. Can't delete the folder {}." .format(path))

    elif not(dir_accessible(path, _os.W_OK)):
        return

    _shutil.rmtree(path)
