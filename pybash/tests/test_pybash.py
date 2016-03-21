import filecmp
import mock
from numpy import random
import os
from pybash import pybash
import shutil
import StringIO
import subprocess
import tempfile


class BaseTest(object):
    duplicate_counts = (2,)  # TODO: 1, 10, 100
    modes = ('call', 'simple')

    @staticmethod
    def _script_abs_path(script_name):
        return os.path.realpath(os.path.join(os.path.dirname(__file__), '..', script_name))

    def _assert_shell_call(self, command):
        print 'subprocess:', command
        assert subprocess.call(command, shell=True) == 0


class RandomDataTest(BaseTest):
    data = ''.join(chr(i) for i in random.RandomState(1).randint(256, size=1024 * 6))
    chunk_sizes = [1, 10, 100, 1000, 200, 20, 2, 30, 300]
    chunk_sizes.append(len(data) - sum(chunk_sizes))
    assert all(chunk_size > 0 for chunk_size in chunk_sizes)
    assert sum(chunk_sizes) == len(data)
    buffer_sizes = (1, 2, pybash.DEFAULT_BUFFER_SIZE - 1, pybash.DEFAULT_BUFFER_SIZE, pybash.DEFAULT_BUFFER_SIZE + 1,
                    pybash.DEFAULT_BUFFER_SIZE * 2)

    @staticmethod
    def _generator():
        index = 0

        for chunk_size in RandomDataTest.chunk_sizes:
            chunk = RandomDataTest.data[index:index + chunk_size]
            assert len(chunk) == chunk_size
            index += chunk_size
            yield chunk


class TestReadableGenerator(RandomDataTest):
    # TODO: read(0)?
    # TODO: pass an exhausted generator
    # TODO: pass a None generator
    # TODO: what if generator returns zero length before finishing?

    def test_readable_generator_using_iterator(self):
        readable_generator = pybash.ReadableGenerator(RandomDataTest._generator())
        chunk_index = 0
        data_index = 0
        data = ''

        for chunk in readable_generator:
            chunk_size = len(chunk)
            assert chunk_size == RandomDataTest.chunk_sizes[chunk_index]
            assert chunk == RandomDataTest.data[data_index:data_index + chunk_size]
            chunk_index += 1
            data_index += chunk_size
            data += chunk

        assert data == RandomDataTest.data

    def test_readable_generator_using_read_all(self):
        readable_generator = pybash.ReadableGenerator(RandomDataTest._generator())
        assert readable_generator.read() == RandomDataTest.data

    def _test_readable_generator_using_read(self, read_size):
        readable_generator = pybash.ReadableGenerator(RandomDataTest._generator())
        data = ''

        while True:
            chunk = readable_generator.read(read_size)

            if len(chunk) == 0:
                break

            data += chunk

        assert data == RandomDataTest.data

    def test_readable_generator_using_read_1(self):
        for buffer_size in RandomDataTest.buffer_sizes:
            yield self._test_readable_generator_using_read, buffer_size


class TestReadWriteThread(RandomDataTest):
    @staticmethod
    def _test_using_string_io_source(buffer_size):
        source = StringIO.StringIO(RandomDataTest.data)
        sink = StringIO.StringIO()
        sink.close = mock.MagicMock()

        pybash.read_write_thread(source, sink, buffer_size=buffer_size)

        assert not source.closed
        assert sink.getvalue() == RandomDataTest.data
        sink.close.assert_called_with()

    def test_using_string_io_source(self):
        for buffer_size in RandomDataTest.buffer_sizes:
            yield TestReadWriteThread._test_using_string_io_source, buffer_size

    @staticmethod
    def _test_using_readable_generator_source(buffer_size):
        source = pybash.ReadableGenerator(RandomDataTest._generator())
        sink = StringIO.StringIO()
        sink.close = mock.MagicMock()

        pybash.read_write_thread(source, sink)

        assert sink.getvalue() == RandomDataTest.data
        sink.close.assert_called_with()

    def test_using_readable_generator_source(self):
        for buffer_size in RandomDataTest.buffer_sizes:
            yield TestReadWriteThread._test_using_readable_generator_source, buffer_size


class FileBasedTest(BaseTest):
    source_file_path = None

    def __init__(self):
        self.actual_file_path = None
        self.expected_file_path = None

    def setup(self):
        temporary_directory_path = tempfile.mkdtemp()
        self.actual_file_path = os.path.join(temporary_directory_path, 'actual')
        self.expected_file_path = os.path.join(temporary_directory_path, 'expected')

    def teardown(self):
        if self.actual_file_path is not None:
            shutil.rmtree(os.path.dirname(self.actual_file_path))


class TestCat(RandomDataTest, FileBasedTest):
    @staticmethod
    def setup_class():
        FileBasedTest.source_file_path = os.path.join(tempfile.mkdtemp(), 'source')

        with open(FileBasedTest.source_file_path, 'wb') as source_file:
            source_file.write(RandomDataTest.data)

    @staticmethod
    def teardown_class():
        if FileBasedTest.source_file_path is not None:
            shutil.rmtree(os.path.dirname(FileBasedTest.source_file_path))

    @staticmethod
    def _test_operation(operation, duplicate_count, buffer_size):
        operation = operation(None, (FileBasedTest.source_file_path,) * duplicate_count, buffer_size=buffer_size)
        expected = ''

        for _ in xrange(duplicate_count):
            expected += RandomDataTest.data

        assert len(expected) > 0
        assert operation.execute().read() == expected

    def test_operation(self):
        for operation in (pybash.PyBashCatCall, pybash.PyBashCatSimple):
            for duplicate_count in RandomDataTest.duplicate_counts:
                for buffer_size in RandomDataTest.buffer_sizes:
                    yield TestCat._test_operation, operation, duplicate_count, buffer_size

    @staticmethod
    def _test_pipeline(pipeline_creator, duplicate_count):
        input_file_paths = (FileBasedTest.source_file_path,) * duplicate_count
        pipeline = pipeline_creator(input_file_paths)
        expected = ''

        for _ in xrange(duplicate_count):
            expected += RandomDataTest.data

        assert len(expected) > 0
        actual = pipeline.execute().read()
        assert actual == expected, (len(actual), len(expected))

    def test_pipeline(self):
        pipeline_creators = (
            lambda input_file_paths: pybash.PyBashPipeline().cat_call(*input_file_paths),
            lambda input_file_paths: pybash.PyBashPipeline().cat_simple(*input_file_paths),
            lambda input_file_paths: pybash.PyBashPipeline().cat_call(*input_file_paths).cat_simple(),
            lambda input_file_paths: pybash.PyBashPipeline().cat_simple(*input_file_paths).cat_call(),
            lambda input_file_paths: pybash.PyBashPipeline().cat_call(*input_file_paths).cat_call(),
            lambda input_file_paths: pybash.PyBashPipeline().cat_simple(*input_file_paths).cat_simple(),
        )

        for pipeline_creator in pipeline_creators:
            for duplicate_count in RandomDataTest.duplicate_counts:
                yield TestCat._test_pipeline, pipeline_creator, duplicate_count

    def _test_shell_create_expected(self, duplicate_count):
        source_file_paths = ' '.join((FileBasedTest.source_file_path,) * duplicate_count)
        self._assert_shell_call('cat %s > %s' % (source_file_paths, self.expected_file_path))
        return source_file_paths

    def _test_shell_from_file(self, duplicate_count, mode):
        source_file_paths = self._test_shell_create_expected(duplicate_count)
        self._assert_shell_call(
            'python %s --mode %s %s > %s' %
            (BaseTest._script_abs_path('pycat.py'), mode, source_file_paths, self.actual_file_path))
        assert filecmp.cmp(self.actual_file_path, self.expected_file_path, shallow=False)

    def test_shell_from_file(self):
        for duplicate_count in RandomDataTest.duplicate_counts:
            for mode in BaseTest.modes:
                yield TestCat._test_shell_from_file, duplicate_count, mode

    def _test_shell_from_stdin(self, duplicate_count, mode):
        source_file_paths = self._test_shell_create_expected(duplicate_count)
        self._assert_shell_call(
            'cat %s | python %s --mode %s > %s' %
            (source_file_paths, BaseTest._script_abs_path('pycat.py'), mode, self.actual_file_path))
        assert filecmp.cmp(self.actual_file_path, self.expected_file_path, shallow=False)

    def test_shell_from_stdin(self):
        for duplicate_count in RandomDataTest.duplicate_counts:
            for mode in BaseTest.modes:
                yield TestCat._test_shell_from_stdin, duplicate_count, mode


class TestGrep(FileBasedTest):
    # TODO: test operation
    # TODO: test pipeline

    @staticmethod
    def setup_class():
        FileBasedTest.source_file_path = os.path.join(os.path.dirname(__file__), 'lorem_ipsum.txt')

    def _create_expected(self, duplicate_count):
        source_file_paths = ' '.join((FileBasedTest.source_file_path,) * duplicate_count)
        self._assert_shell_call('grep "" %s > %s' % (source_file_paths, self.expected_file_path))
        return source_file_paths

    def _test_shell_from_file(self, duplicate_count, cat_mode, grep_mode):
        source_file_paths = self._create_expected(duplicate_count)
        self._assert_shell_call(
            'python %s --cat-mode %s --grep-mode %s "" %s > %s' %
            (BaseTest._script_abs_path('pygrep.py'), cat_mode, grep_mode, source_file_paths, self.actual_file_path))
        assert filecmp.cmp(self.actual_file_path, self.expected_file_path, shallow=False)

    def _test_shell_from_stdin(self, duplicate_count, grep_mode):
        source_file_paths = self._create_expected(duplicate_count)
        self._assert_shell_call(
            'cat %s | python %s --grep-mode %s "" > %s' %
            (source_file_paths, BaseTest._script_abs_path('pygrep.py'), grep_mode, self.actual_file_path))
        assert filecmp.cmp(self.actual_file_path, self.expected_file_path, shallow=False)

    def test_shell_from_file(self):
        for duplicate_count in RandomDataTest.duplicate_counts:
            for grep_mode in BaseTest.modes:
                for cat_mode in BaseTest.modes:
                    yield TestGrep._test_shell_from_file, duplicate_count, cat_mode, grep_mode

    def test_shell_from_stdin(self):
        for duplicate_count in RandomDataTest.duplicate_counts:
            for grep_mode in BaseTest.modes:
                yield TestGrep._test_shell_from_stdin, duplicate_count, grep_mode
