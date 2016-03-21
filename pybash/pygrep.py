#!/usr/bin/env python
import argparse
import common
import pybash
import sys


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('pattern')
    argument_parser.add_argument('source_file_paths', nargs='*')
    argument_parser.add_argument('--mode', default='simple')
    parsed_arguments = argument_parser.parse_args()

    if len(parsed_arguments.source_file_paths) == 0:
        pipeline = pybash.PyBashPipeline.from_stream(sys.stdin)
    else:
        pipeline = pybash.PyBashPipeline()

    pipeline = common.lazy_switch(
        'mode', parsed_arguments.mode,
        call=lambda: pipeline.grep_call(parsed_arguments.pattern, *parsed_arguments.source_file_paths),
        simple=lambda: pipeline.grep_simple(parsed_arguments.pattern, *parsed_arguments.source_file_paths))

    pipeline.execute(sys.stdout)


if __name__ == '__main__':
    main()
