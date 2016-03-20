import filecmp
import mock
from numpy import random
import os
from pybash import pybash
import shutil
import StringIO
import subprocess
import tempfile


class RandomDataTest(object):
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


class TestCat(RandomDataTest):
    temporary_directory_path = None
    source_file_path = None

    @staticmethod
    def setup_class():
        TestCat.temporary_directory_path = tempfile.mkdtemp()
        TestCat.source_file_path = os.path.join(TestCat.temporary_directory_path, 'source')

        with open(TestCat.source_file_path, 'wb') as source_file:
            source_file.write(RandomDataTest.data)

    @staticmethod
    def teardown_class():
        if TestCat.temporary_directory_path is not None:
            shutil.rmtree(TestCat.temporary_directory_path)

    @staticmethod
    def _test_cat(operation, duplicate_count, buffer_size):
        operation = operation((TestCat.source_file_path,) * duplicate_count, buffer_size=buffer_size)
        expected = ''

        for _ in xrange(duplicate_count):
            expected += RandomDataTest.data

        assert len(expected) > 0
        assert operation.stream().read() == expected

    def test_call(self):
        for operation in (pybash.PyBashCatCall, pybash.PyBashCatSimple):
            for duplicate_count in (1, 2):
                for buffer_size in RandomDataTest.buffer_sizes:
                    yield TestCat._test_cat, operation, duplicate_count, buffer_size

    @staticmethod
    def _test_shell_from_file(mode, duplicate_count, expected_file_path):
        actual_file_path = os.path.join(TestCat.temporary_directory_path, 'actual')
        assert subprocess.call(['python', '../pycat.py', '--mode', mode] +
                               [TestCat.source_file_path] * duplicate_count + ['>', actual_file_path], shell=True) == 0
        assert filecmp.cmp(actual_file_path, expected_file_path, shallow=False)

    @staticmethod
    def _test_shell_from_stdin(mode, duplicate_count, expected_file_path):
        actual_file_path = os.path.join(TestCat.temporary_directory_path, 'actual')
        assert subprocess.call(['cat'] + [TestCat.source_file_path] * duplicate_count +
                               ['|', 'python', '../pycat.py', '--mode', mode] + ['>', actual_file_path],
                               shell=True) == 0
        assert filecmp.cmp(actual_file_path, expected_file_path, shallow=False)

    def test_shell_from_file(self):
        expected_file_path = os.path.join(TestCat.temporary_directory_path, 'expected')

        for duplicate_count in (1, 2):
            assert subprocess.call(['cat'] + [TestCat.source_file_path] * duplicate_count + ['>', expected_file_path],
                                   shell=True) == 0

            for mode in ('call', 'simple'):
                yield TestCat._test_shell_from_file, mode, duplicate_count, expected_file_path
                yield TestCat._test_shell_from_stdin, mode, duplicate_count, expected_file_path
