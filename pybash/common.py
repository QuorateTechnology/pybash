import contextlib
import pybash
import shutil
import sys
import tempfile


@contextlib.contextmanager
def temporary_directory():
    path = None

    try:
        path = tempfile.mkdtemp()
        yield path
    finally:
        if path is not None:
            shutil.rmtree(path)


def lazy_switch(name, key, **kwargs):
    value = kwargs.get(key)

    if value is None:
        raise Exception('Unknown %s: %s' % (name, key))

    return value()


def pipeline_to_stdout(pipeline):
    stdout = pipeline.execute()

    while True:
        data = stdout.read(pybash.DEFAULT_BUFFER_SIZE)

        if len(data) == 0:
            break

        sys.stdout.write(data)
