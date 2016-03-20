import argparse
import pybash
import sys


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('source_file_paths', nargs='+')
    argument_parser.add_argument('--mode', default='simple')
    parsed_arguments = argument_parser.parse_args()

    if parsed_arguments.mode == 'call':
        pipeline = pybash.PyBashPipeline.cat_call(*parsed_arguments.source_file_paths)
    elif parsed_arguments.mode == 'simple':
        pipeline = pybash.PyBashPipeline.cat_simple(*parsed_arguments.source_file_paths)
    else:
        raise Exception('Unknown mode:', parsed_arguments.mode)

    stdout = pipeline.stream()

    while True:
        data = stdout.read(pybash.DEFAULT_BUFFER_SIZE)

        if len(data) == 0:
            break

        sys.stdout.write(data)


if __name__ == "__main__":
    main()
