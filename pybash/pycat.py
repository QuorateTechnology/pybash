#!/usr/bin/env python
import argparse
import pybash
import sys


# TODO: behaviour differs from standard cat (run and type and hit return, then control-C exit)


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('source_file_paths', nargs='*')
    argument_parser.add_argument('--mode', default='simple')
    parsed_arguments = argument_parser.parse_args()
    stdout = pybash.get_standard_input_pipeline(parsed_arguments.source_file_paths, parsed_arguments.mode).execute()

    while True:
        data = stdout.read(pybash.DEFAULT_BUFFER_SIZE)

        if len(data) == 0:
            break

        sys.stdout.write(data)


if __name__ == "__main__":
    main()
