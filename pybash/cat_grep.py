import os
import sys
import timeit

import argparse

import pybash


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('source_file_path')
    argument_parser.add_argument('pattern')
    argument_parser.add_argument('cat_mode')
    argument_parser.add_argument('grep_mode')
    parsed_arguments = argument_parser.parse_args()

    source_file_path = parsed_arguments.source_file_path
    source_file_path = os.path.expanduser(source_file_path)
    source_file_path = os.path.realpath(source_file_path)

    assert os.path.exists(source_file_path)

    start = timeit.default_timer()

    if parsed_arguments.cat_mode == 'call':
        pipeline = pybash.PyBashPipeline.cat_call(parsed_arguments.source_file_path)
    elif parsed_arguments.cat_mode == 'simple':
        pipeline = pybash.PyBashPipeline.cat_simple(parsed_arguments.source_file_path)
    else:
        raise Exception('Unknown mode:', parsed_arguments.mode)

    if parsed_arguments.grep_mode == 'call':
        pipeline = pipeline.grep_call(parsed_arguments.pattern)
    elif parsed_arguments.grep_mode == 'simple':
        pipeline = pipeline.grep_simple(parsed_arguments.pattern)
    else:
        raise Exception('Unknown mode:', parsed_arguments.mode)

    for line in pipeline.stream():
        print line,

    print >> sys.stderr, timeit.default_timer() - start


if __name__ == "__main__":
    main()
