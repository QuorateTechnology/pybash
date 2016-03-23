import os
import errno

DEFAULT_BUFFER_SIZE = 4096


def lazy_switch(name, key, **kwargs):
    value = kwargs.get(key)

    if value is None:
        raise Exception('Unknown %s: %s' % (name, key))

    return value()


def read_write(source, sink, buffer_size=DEFAULT_BUFFER_SIZE, close_sink_on_completion=True):
    while True:
        data = source.read(buffer_size)

        if len(data) == 0:
            break

        sink.write(data)

    if close_sink_on_completion:
        sink.close()


def actual_kwargs():
    """
    Decorator that provides the wrapped function with an attribute 'actual_kwargs' containing just those keyword
    arguments actually passed in to the function.

    Based on code from  http://stackoverflow.com/a/1409284/127480
    """

    def decorator(function):
        def inner(*args, **kwargs):
            inner.actual_kwargs = kwargs
            inner.actual_kwargs_except = \
                lambda keys: {key: value for key, value in kwargs.iteritems() if key not in keys}
            return function(*args, **kwargs)

        return inner

    return decorator


def makedirs(path):
    """
    Ensures a directory (and all its parents) already exists without raising an exception if it does already exist.

    Taken from http://stackoverflow.com/a/5032238/127480
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
