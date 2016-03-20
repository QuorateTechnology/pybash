import os
import re
import subprocess
import sys
import threading

# TODO: .kaldi-binary(woth, kaldi, options)
# TODO: test with very large data: check memory usage, and compare call vs. simple speeds
# TODO: logging
# TODO: make fastest version (call vs. simple) default, use argument to use alternate instead of two separate methods


DEFAULT_BUFFER_SIZE = 4096


def get_standard_input_pipeline(source_file_paths, mode):
    if len(source_file_paths) == 0:
        pipeline = PyBashPipeline.from_stream(sys.stdin)
    elif mode == 'call':
        pipeline = PyBashPipeline().cat_call(*source_file_paths)
    elif mode == 'simple':
        pipeline = PyBashPipeline().cat_simple(*source_file_paths)
    else:
        raise Exception('Unknown mode:', mode)

    return pipeline


class PyBashPipeline(object):
    def __init__(self, input_operation=None):
        self.head = input_operation

    @staticmethod
    def from_stream(input_stream):
        return PyBashPipeline(PyBashInputStream(input_stream))

    def call(self, *arguments):
        self.head = PyBashCall(self.head, arguments)
        return self

    def cat_call(self, *input_file_paths):
        self.head = PyBashCatCall(self.head, input_file_paths)
        return self

    def cat_simple(self, *input_file_paths):
        self.head = PyBashCatSimple(self.head, input_file_paths)
        return self

    def grep_call(self, pattern, *input_file_paths):
        self.head = PyBashGrepCall(self.head, pattern, input_file_paths)
        return self

    def grep_simple(self, pattern, *input_file_paths):
        self.head = PyBashGrepSimple(self.head, pattern, input_file_paths)
        return self

    def execute(self):
        return self.head.execute()


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


def read_write_thread(source, sink, buffer_size=DEFAULT_BUFFER_SIZE):
    while True:
        data = source.read(buffer_size)

        if len(data) == 0:
            break

        sink.write(data)

    sink.close()


class PyBashOperation(object):
    def __init__(self, source, source_may_be_none=False):
        assert source_may_be_none or source is not None
        self.source = source

    def execute(self):
        raise NotImplementedError()


class PyBashInputStream(PyBashOperation):
    def __init__(self, input_stream):
        super(PyBashInputStream, self).__init__(None, source_may_be_none=True)
        self.input_stream = input_stream

    def execute(self):
        return self.input_stream


class PyBashCall(PyBashOperation):
    def __init__(self, source, arguments, source_may_be_none=False, buffer_size=DEFAULT_BUFFER_SIZE):
        super(PyBashCall, self).__init__(source, source_may_be_none=source_may_be_none)
        self.arguments = arguments
        self.buffer_size = buffer_size
        self.process = None
        self.thread = None

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
            name = self.arguments[0] + '_read_write_thread'
            self.thread = threading.Thread(target=read_write_thread, name=name, args=(source, self.process.stdin),
                                           kwargs=dict(buffer_size=self.buffer_size))
            self.thread.daemon = True
            self.thread.start()

        return self.process.stdout


class PyBashCatCall(PyBashCall):
    def __init__(self, source, input_file_paths, buffer_size=DEFAULT_BUFFER_SIZE):
        assert (source is None and len(input_file_paths) > 0) or \
               (source is not None and len(input_file_paths) == 0)
        super(PyBashCatCall, self).__init__(source, ('cat',) + input_file_paths, source_may_be_none=True,
                                            buffer_size=buffer_size)


class PyBashGrepCall(PyBashCall):
    def __init__(self, source, pattern, input_file_paths, buffer_size=DEFAULT_BUFFER_SIZE):
        assert (source is None and len(input_file_paths) > 0) or \
               (source is not None and len(input_file_paths) == 0)
        super(PyBashGrepCall, self).__init__(source, ('grep', pattern) + input_file_paths, source_may_be_none=True,
                                             buffer_size=buffer_size)


class PyBashCatSimple(PyBashOperation):
    def __init__(self, source, input_file_paths, buffer_size=DEFAULT_BUFFER_SIZE):
        assert (source is None and len(input_file_paths) > 0) or \
               (source is not None and len(input_file_paths) == 0)
        super(PyBashCatSimple, self).__init__(source, source_may_be_none=True)
        self.input_file_paths = input_file_paths
        self.buffer_size = buffer_size

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
    def __init__(self, source, pattern, input_file_paths, buffer_size=DEFAULT_BUFFER_SIZE):
        assert (source is None and len(input_file_paths) > 0) or \
               (source is not None and len(input_file_paths) == 0)
        super(PyBashGrepSimple, self).__init__(source, source_may_be_none=True)
        self.pattern = re.compile(pattern)
        self.input_file_paths = input_file_paths
        self.buffer_size = buffer_size

    def _generator_from_files(self):
        for input_file_path in self.input_file_paths:
            input_file_path = os.path.expanduser(input_file_path)
            input_file_path = os.path.realpath(input_file_path)

            with open(input_file_path, 'rt') as input_file:
                for line in input_file:
                    if self.pattern.search(line) is not None:
                        if len(self.input_file_paths) > 0:
                            yield '%s: %s' % (input_file_path, line)
                        else:
                            yield line

    def _generator_from_source(self):
        for line in self.source.execute():
            if self.pattern.search(line) is not None:
                yield line

    def execute(self):
        if self.source is None:
            return ReadableGenerator(self._generator_from_files())
        else:
            return ReadableGenerator(self._generator_from_source())
