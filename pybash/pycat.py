#!/usr/bin/env python
import argparse
import common
import pybash
import sys


# TODO: behaviour differs from standard cat (run and type and hit return, then control-C exit)


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('source_file_paths', nargs='*')
    argument_parser.add_argument('--mode', default='simple')
    parsed_arguments = argument_parser.parse_args()

    if len(parsed_arguments.source_file_paths) == 0:
        pipeline = pybash.PyBashPipeline.from_stream(sys.stdin)
    else:
        pipeline = pybash.PyBashPipeline()

    pipeline = common.lazy_switch(
        'mode', parsed_arguments.mode,
        call=lambda: pipeline.cat_call(*parsed_arguments.source_file_paths),
        simple=lambda: pipeline.cat_simple(*parsed_arguments.source_file_paths))

    common.pipeline_to_stdout(pipeline)


if __name__ == "__main__":
    main()
