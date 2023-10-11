import os as _os

#########################################################
# which command
# A minimal version of the UNIX which utility, in Python.
# Return full-path if found, None if not found.
#########################################################
def which(name):
    for path in _os.getenv("PATH").split(_os.path.pathsep):
        full_path = path + _os.sep + name
        if _os.path.exists(full_path):
            """
            if os.stat(full_path).st_mode & stat.S_IXUSR:
                return(full_path)
            """
            return(full_path)

    return(None)
