import contextlib
import shutil
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
