import logging
import shutil
import subprocess
import os


def mv(src, dst):
    return shutil.move(src, dst)


def call(*arguments):
    command = ' '.join(arguments)
    logging.debug('Calling %s', command)
    return_code = subprocess.call(arguments)

    if return_code != 0:
        raise Exception('Called %s, received return code %s' % (command, return_code))


def seq(n):
    return range(1, n + 1)


def rm(paths, ignore_errors=False):
    if not isinstance(paths, (tuple, list)):
        paths = (paths,)

    for path in paths:
        try:
            os.remove(path)
        except BaseException:
            if not ignore_errors:
                raise
