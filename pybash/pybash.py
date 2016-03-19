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


class PyBashPipeline(object):
    def __init__(self, head):
        self.head = head

    @staticmethod
    def cat_call(*input_file_paths):
        return PyBashPipeline(PyBashCatCall(input_file_paths))

    @staticmethod
    def cat_simple(*input_file_paths):
        return PyBashPipeline(PyBashCatSimple(input_file_paths))

    def call(self, *arguments):
        self.head = PyBashCall(self.head, arguments)
        return self

    def grep_call(self, pattern):
        self.head = PyBashGrepCall(self.head, pattern)
        return self

    def grep_simple(self, pattern):
        self.head = PyBashGrepSimple(self.head, pattern)
        return self

    def stream(self):
        return self.head.stream()


class ReadableGenerator(object):
    def __init__(self, generator):
        self.iterator = iter(generator)
        self.residual = ''

    def __iter__(self):
        return self.iterator

    def read(self, size):
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

    def stream(self):
        raise NotImplementedError()


class PyBashCall(PyBashOperation):
    def __init__(self, source, arguments, source_may_be_none=False, buffer_size=DEFAULT_BUFFER_SIZE):
        super(PyBashCall, self).__init__(source, source_may_be_none=source_may_be_none)
        self.arguments = arguments
        self.buffer_size = buffer_size
        self.process = None
        self.thread = None

    def stream(self):
        if self.source is None:
            stdin = subprocess.PIPE
            source = None
        else:
            stdin = self.source.stream()

            if hasattr(stdin, 'fileno'):
                source = None
            else:
                source = stdin
                stdin = subprocess.PIPE

        print >> sys.stderr, type(self), ' '.join(self.arguments)
        self.process = subprocess.Popen(self.arguments, bufsize=self.buffer_size, stdin=stdin, stdout=subprocess.PIPE)

        if source is not None:
            name = self.arguments[0] + '_read_write_thread'
            print >> sys.stderr, type(self), 'Starting thread', name
            self.thread = threading.Thread(target=read_write_thread, name=name, args=(source, self.process.stdin),
                                           kwargs=dict(buffer_size=self.buffer_size))
            self.thread.daemon = True
            self.thread.start()

        return self.process.stdout


class PyBashCatCall(PyBashCall):
    def __init__(self, input_file_paths, buffer_size=DEFAULT_BUFFER_SIZE):
        super(PyBashCatCall, self).__init__(None, ('cat',) + input_file_paths, source_may_be_none=True,
                                            buffer_size=buffer_size)


class PyBashGrepCall(PyBashCall):
    def __init__(self, source, pattern, buffer_size=DEFAULT_BUFFER_SIZE):
        super(PyBashGrepCall, self).__init__(source, ('grep', pattern), buffer_size=buffer_size)


class PyBashCatSimple(PyBashOperation):
    def __init__(self, input_file_paths, buffer_size=DEFAULT_BUFFER_SIZE):
        super(PyBashCatSimple, self).__init__(None, source_may_be_none=True)
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

    def stream(self):
        return ReadableGenerator(self._generator())


class PyBashGrepSimple(PyBashOperation):
    def __init__(self, source, pattern):
        super(PyBashGrepSimple, self).__init__(source)
        self.pattern = re.compile(pattern)

    def stream(self):
        return ReadableGenerator(line for line in self.source.stream() if self.pattern.search(line) is not None)


def main():
    print 'Test 1'
    pipeline = PyBashPipeline.cat_call('D:\\source.txt', 'D:\\sink.txt') \
        .grep_simple('neque vel') \
        .grep_call('neque vel') \
        .grep_simple('neque vel') \
        .grep_call('neque vel')

    for line in pipeline.stream():
        print line,

    print 'Test 2'
    pipeline = PyBashPipeline.cat_call('D:\\source.txt', 'D:\\sink.txt') \
        .grep_call('neque vel') \
        .grep_simple('neque vel') \
        .grep_call('neque vel') \
        .grep_simple('neque vel')

    for line in pipeline.stream():
        print line,

    print 'Test 3'
    pipeline = PyBashPipeline.cat_call('D:\\source.txt', 'D:\\sink.txt') \
        .grep_simple('neque vel') \
        .grep_call('neque vel') \
        .grep_call('neque vel') \
        .grep_simple('neque vel')

    for line in pipeline.stream():
        print line,

    print 'Test 4'
    pipeline = PyBashPipeline.cat_call('D:\\source.txt', 'D:\\sink.txt') \
        .grep_call('neque vel') \
        .grep_simple('neque vel') \
        .grep_simple('neque vel') \
        .grep_call('neque vel')

    for line in pipeline.stream():
        print line,

    print 'Test 5'
    pipeline = PyBashPipeline.cat_simple('D:\\source.txt', 'D:\\sink.txt') \
        .grep_simple('neque vel') \
        .grep_call('neque vel') \
        .grep_simple('neque vel') \
        .grep_call('neque vel')

    for line in pipeline.stream():
        print line,

    print 'Test 6'
    pipeline = PyBashPipeline.cat_simple('D:\\source.txt', 'D:\\sink.txt') \
        .grep_call('neque vel') \
        .grep_simple('neque vel') \
        .grep_call('neque vel') \
        .grep_simple('neque vel')

    for line in pipeline.stream():
        print line,

    print 'Test 7'
    pipeline = PyBashPipeline.cat_simple('D:\\source.txt', 'D:\\sink.txt') \
        .grep_simple('neque vel') \
        .grep_call('neque vel') \
        .grep_call('neque vel') \
        .grep_simple('neque vel')

    for line in pipeline.stream():
        print line,

    print 'Test 8'
    pipeline = PyBashPipeline.cat_simple('D:\\source.txt', 'D:\\sink.txt') \
        .grep_call('neque vel') \
        .grep_simple('neque vel') \
        .grep_simple('neque vel') \
        .grep_call('neque vel')

    for line in pipeline.stream():
        print line,


if __name__ == "__main__":
    main()

# class PyBashGrep(object):
#     def __init__(self, pattern):
#         self.pattern = re.compile(pattern)
#
#     def advance(self, input_stream):
#         for line in input_stream():
#             if self.pattern.match(line) is not None:
#                 yield line
#
#
# class PyBashTo(object):
#     def __init__(self, source, output_file_path):
#         self.source = source
#         self.output_file_path = output_file_path
#
#     def execute(self):
#         with open(self.output_file_path, 'wt') as output_file:
#             for line in self.source.advance():
#                 output_file.write(line)
#                 output_file.write('\n')
#
#
# def main():
#     PyBashPipeline.cat('D:/source.txt') \
#         .grep(r'book') \
#         .to('D:/temp.txt') \
#         .stream()
#
#
# main()
#
#
# class MultiFile(io.RawIOBase):
#     def __init__(self, buffer_size=DEFAULT_BUFFER_SIZE, *input_file_paths):
#         super(MultiFile, self).__init__()
#         self.input_file_paths = input_file_paths
#         self.buffer_size = buffer_size
#
#     def read(self, n):
#         for input_file_path in self.input_file_paths:
#             input_file_path = os.path.expanduser(input_file_path)
#             input_file_path = os.path.realpath(input_file_path)
#
#             with open(input_file_path, 'rt') as input_file:
#                 while True:
#                     buffer = sys.stdin.read(self.buffer_size)
#
#                     if len(buffer) == 0:
#                         break
#
#                     sys.stdout.write(buffer)
#         return super(MultiFile, self).read(*args, **kwargs)
#
#
# class CheckedStream(object):
#     def __init__(self, stream):
#         self.stream = stream
#
#     def read(self, n):
#         buffer = self.stream.read(n)
#
#         if len(buffer) == 0:
#             self.process.wait()
#
#             if self.process.returncode != 0:
#                 raise subprocess.CalledProcessError(self.process.returncode, self.arguments)
#
#         return buffer