#!/usr/bin/env python
import argparse
import numpy
import os


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('--source_sentences_file_path', default='lorem_ipsum.txt')
    argument_parser.add_argument('--line_count', type=int, required=True)
    argument_parser.add_argument('--sentences_per_line_poisson_lambda', type=float, default=4)
    parsed_arguments = argument_parser.parse_args()

    source_sentences_file_path = parsed_arguments.source_sentences_file_path
    source_sentences_file_path = os.path.expanduser(source_sentences_file_path)
    source_sentences_file_path = os.path.realpath(source_sentences_file_path)

    assert os.path.exists(source_sentences_file_path)
    assert parsed_arguments.line_count >= 0
    assert parsed_arguments.sentences_per_line_poisson_lambda > 0

    with open(source_sentences_file_path, 'rt') as source_sentences_file:
        source_sentences = [line.strip() for line in source_sentences_file]

    for _ in xrange(parsed_arguments.line_count):
        print ' '.join(numpy.random.choice(source_sentences, size=numpy.random.poisson(
            parsed_arguments.sentences_per_line_poisson_lambda)))


if __name__ == "__main__":
    main()
