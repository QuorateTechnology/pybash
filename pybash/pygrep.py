import argparse
import pybash
import sys


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('pattern')
    argument_parser.add_argument('source_file_paths', nargs='*')
    argument_parser.add_argument('--cat-mode', default='simple')
    argument_parser.add_argument('--grep-mode', default='simple')
    parsed_arguments = argument_parser.parse_args()
    pipeline = pybash.get_standard_input_pipeline(parsed_arguments.source_file_paths, parsed_arguments.cat_mode)

    if parsed_arguments.grep_mode == 'call':
        pipeline = pipeline.grep_call(parsed_arguments.pattern)
    elif parsed_arguments.grep_mode == 'simple':
        pipeline = pipeline.grep_simple(parsed_arguments.pattern)
    else:
        raise Exception('Unknown grep-mode:', parsed_arguments.grep_mode)

    stdout = pipeline.execute()

    while True:
        data = stdout.read(pybash.DEFAULT_BUFFER_SIZE)

        if len(data) == 0:
            break

        sys.stdout.write(data)


if __name__ == "__main__":
    main()
