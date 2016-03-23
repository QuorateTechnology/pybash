import common
import os
import re
import subprocess
import threading


# TODO: test with very large data: check memory usage, and compare call vs. simple speeds
# TODO: logging
# TODO: make fastest version (call vs. simple) default, use argument to use alternate instead of two separate methods


class PyBashPipeline(object):
    def __init__(self, input_operation=None, add_to_operations=True):
        self.head = input_operation
        self.operations = [input_operation] if add_to_operations and input_operation is not None else []

    def _add(self, operation):
        self.head = operation
        self.operations.append(operation)
        return self

    def __repr__(self):
        return ' | '.join(repr(operation) for operation in self.operations)

    @classmethod
    def from_stream(cls, input_stream):
        return cls(PyBashInputStream(input_stream), add_to_operations=False)

    def call(self, *arguments):
        return self._add(PyBashCall(self.head, arguments))

    def cat_call(self, *input_file_paths):
        return self._add(PyBashCatCall(self.head, input_file_paths))

    def cat_simple(self, *input_file_paths):
        return self._add(PyBashCatSimple(self.head, input_file_paths))

    def grep_call(self, pattern, *input_file_paths):
        return self._add(PyBashGrepCall(self.head, pattern, input_file_paths))

    def grep_simple(self, pattern, *input_file_paths):
        return self._add(PyBashGrepSimple(self.head, pattern, input_file_paths))

    @common.actual_kwargs()
    def wc_call(self, input_file_paths, bytes=False, chars=False, lines=False, max_line_length=False, words=False,
                buffer_size=common.DEFAULT_BUFFER_SIZE):
        except_keys = 'input_file_paths'
        return self._add(PyBashWcCall(self.head, input_file_paths, **self.wc_call.actual_kwargs_except(*except_keys)))

    def execute(self, output=None):
        if output is None:
            return self.head.execute()
        elif isinstance(output, basestring):
            with open(output, 'wb') as output_file:
                common.read_write(self.head.execute(), output_file)
        else:
            common.read_write(self.head.execute(), output)

    def command(self, prefix='', suffix=''):
        return prefix + repr(self) + suffix


class ReadableGenerator(object):
    def __init__(self, generator):
        self.iterator = iter(generator)
        self.residual = ''

    def __iter__(self):
        return self.iterator

    def read(self, size=-1):
        data = self.residual

        while size < 0 or len(data) < size:
            try:
                data += self.iterator.next()
            except StopIteration:
                break

        if size > 0:
            self.residual = data[size:]
            data = data[:size]

        return data


class PyBashOperation(object):
    def __init__(self, source, source_may_be_none=False):
        assert source_may_be_none or source is not None
        self.source = source

    def __repr(self):
        raise NotImplementedError()

    def execute(self):
        raise NotImplementedError()


class PyBashInputStream(PyBashOperation):
    def __init__(self, input_stream):
        super(PyBashInputStream, self).__init__(None, source_may_be_none=True)
        self.input_stream = input_stream

    def execute(self):
        return self.input_stream


class PyBashCall(PyBashOperation):
    def __init__(self, source, arguments, source_may_be_none=False, buffer_size=common.DEFAULT_BUFFER_SIZE):
        super(PyBashCall, self).__init__(source, source_may_be_none=source_may_be_none)
        self.arguments = arguments
        self.buffer_size = buffer_size
        self.process = None
        self.thread = None

    def __repr__(self):
        return self.arguments if isinstance(self.arguments, str) else ' '.join(self.arguments)

    @staticmethod
    def flags(**kwargs):
        return tuple(('-%s %s' if len(key) == 1 else '--%s=%s') % (key, kwargs[key]) for key in sorted(kwargs.keys()))

    @staticmethod
    def actual_flags(function, *except_keys):
        return PyBashCall.flags(**function.actual_kwargs_except(*except_keys))

    def execute(self):
        if self.source is None:
            stdin = subprocess.PIPE
            source = None
        else:
            stdin = self.source.execute()

            if hasattr(stdin, 'fileno'):
                source = None
            else:
                source = stdin
                stdin = subprocess.PIPE

        self.process = subprocess.Popen(self.arguments, bufsize=self.buffer_size, stdin=stdin, stdout=subprocess.PIPE)

        if source is not None:
            self.thread = threading.Thread(target=common.read_write, name=self.arguments[0] + '_read_write_thread',
                                           args=(source, self.process.stdin), kwargs=dict(buffer_size=self.buffer_size))
            self.thread.daemon = True
            self.thread.start()

        return self.process.stdout


class PyBashCatCall(PyBashCall):
    def __init__(self, source, input_file_paths, buffer_size=common.DEFAULT_BUFFER_SIZE):
        assert (source is None and len(input_file_paths) > 0) or \
               (source is not None and len(input_file_paths) == 0)
        super(PyBashCatCall, self).__init__(source, ('cat',) + input_file_paths, source_may_be_none=True,
                                            buffer_size=buffer_size)


class PyBashGrepCall(PyBashCall):
    def __init__(self, source, pattern, input_file_paths, buffer_size=common.DEFAULT_BUFFER_SIZE):
        assert (source is None and len(input_file_paths) > 0) or \
               (source is not None and len(input_file_paths) == 0)
        super(PyBashGrepCall, self).__init__(source, ('grep', pattern) + input_file_paths, source_may_be_none=True,
                                             buffer_size=buffer_size)


class PyBashWcCall(PyBashCall):
    @common.actual_kwargs()
    def __init__(self, source, input_file_paths, bytes=False, chars=False, lines=False, max_line_length=False,
                 words=False, buffer_size=common.DEFAULT_BUFFER_SIZE):
        assert (source is None and len(input_file_paths) > 0) or \
               (source is not None and len(input_file_paths) == 0)
        except_keys = 'source', 'input_file_paths', 'buffer_size'
        super(PyBashWcCall, self).__init__(source, ('wc',) + PyBashCall.actual_flags(self.__init__, except_keys) +
                                           input_file_paths, source_may_be_none=True, buffer_size=buffer_size)


class PyBashCatSimple(PyBashOperation):
    def __init__(self, source, input_file_paths, buffer_size=common.DEFAULT_BUFFER_SIZE):
        assert (source is None and len(input_file_paths) > 0) or \
               (source is not None and len(input_file_paths) == 0)
        super(PyBashCatSimple, self).__init__(source, source_may_be_none=True)
        self.input_file_paths = input_file_paths
        self.buffer_size = buffer_size

    def __repr(self):
        return 'python pycat.py' + (' ' if len(self.input_file_paths) > 0 else '') + ' '.join(self.input_file_paths)

    def _generator(self):
        for input_file_path in self.input_file_paths:
            input_file_path = os.path.expanduser(input_file_path)
            input_file_path = os.path.realpath(input_file_path)

            with open(input_file_path, 'rb') as input_file:
                while True:
                    data = input_file.read(self.buffer_size)

                    if len(data) == 0:
                        break

                    yield data

    def execute(self):
        if self.source is None:
            return ReadableGenerator(self._generator())
        else:
            return self.source.execute()


class PyBashGrepSimple(PyBashOperation):
    def __init__(self, source, pattern, input_file_paths, buffer_size=common.DEFAULT_BUFFER_SIZE):
        assert (source is None and len(input_file_paths) > 0) or \
               (source is not None and len(input_file_paths) == 0)
        super(PyBashGrepSimple, self).__init__(source, source_may_be_none=True)
        self.pattern = pattern
        self.compiled_pattern = re.compile(pattern)
        self.input_file_paths = input_file_paths
        self.buffer_size = buffer_size

    def __repr(self):
        return 'python pycat.py ' + self.pattern + (' ' if len(self.input_file_paths) > 0 else '') + \
               ' '.join(self.input_file_paths)

    def _generator_from_files(self):
        for input_file_path in self.input_file_paths:
            input_file_path = os.path.expanduser(input_file_path)
            input_file_path = os.path.realpath(input_file_path)

            with open(input_file_path, 'rt') as input_file:
                for line in input_file:
                    if self.compiled_pattern.search(line) is not None:
                        if len(self.input_file_paths) > 1:
                            yield '%s:%s' % (input_file_path, line)
                        else:
                            yield line

    def _generator_from_source(self):
        for line in self.source.execute():
            if self.compiled_pattern.search(line) is not None:
                yield line

    def execute(self):
        if self.source is None:
            return ReadableGenerator(self._generator_from_files())
        else:
            return ReadableGenerator(self._generator_from_source())
