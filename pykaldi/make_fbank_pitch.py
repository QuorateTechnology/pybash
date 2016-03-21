#!/usr/bin/env python
import argparse
from os import path
import pykaldi
import string

"""
This script is inteded to demonstrate the use of pybash to wrap some Kaldi binaries.

The intent is to replace the standard step script for making filter bank and pitch features.

DO NOT USE! Currently far from complete!

Based on https://github.com/kaldi-asr/kaldi/blob/master/egs/wsj/s5/steps/make_fbank_pitch.sh
"""


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('data_dir')
    argument_parser.add_argument('log_dir')
    argument_parser.add_argument('fbank_pitch_dir')
    argument_parser.add_argument('--fbank-config', default='conf/fbank.conf')
    argument_parser.add_argument('--pitch-config', default='conf/pitch.conf')
    argument_parser.add_argument('--pitch-postprocess-config', default=None)
    argument_parser.add_argument('--paste-length-tolerance', type=int, default=2)
    argument_parser.add_argument('--compress', type=bool, default=True)
    parsed_arguments = argument_parser.parse_args()

    def s(template):
        values = dict(parsed_arguments)
        values.update(locals())
        return string.Template(template).substitute(**values)

    if parsed_arguments.pitch_postprocess_config is None:
        postprocess_config_opt = {}
    else:
        postprocess_config_opt = dict(config=parsed_arguments.pitch_postprocess_config)

    if path.exists(s('$data/spk2warp')):
        print s('$0 [info]: using VTLN warp factors from $data/spk2warp')
        vtln_opts = dict(vtln_map=s('ark:$data/spk2warp'), utt2spk=s('ark:$data/utt2spk'))
    elif path.exists(s('$data/utt2warp')):
        print s('$0 [info]: using VTLN warp factors from $data/utt2warp')
        vtln_opts = dict(vtln_map=s('ark:$data/utt2warp'))
    else:
        vtln_opts = {}

    fbank_feats = pykaldi.PyKaldiPipeline() \
        .extract_segments(s('$logdir/segments.JOB'), s('scp,p:$scp')) \
        .compute_fbank_feats(verbose=2, config=parsed_arguments.fbank_config, **vtln_opts)

    pitch_feats = pykaldi.PyKaldiPipeline() \
        .extract_segments(s('$logdir/segments.JOB'), s('scp,p:$scp')) \
        .compute_kaldi_pitch_feats(verbose=2, config=parsed_arguments.pitch_config, **vtln_opts) \
        .process_kaldi_pitch_feats(**postprocess_config_opt)

    feature_wspecifier = 'ark,scp:' \
                         + s('$fbank_pitch_dir/raw_fbank_pitch_$name.JOB.ark,') \
                         + s('$fbank_pitch_dir/raw_fbank_pitch_$name.JOB.scp')

    pipeline = pykaldi.PyKaldiPipeline() \
        .paste_feats(fbank_feats.command('ark:', '|'), pitch_feats.command('ark,s,cs:', '|'),
                     length_tolerance=parsed_arguments.paste_length_tolerance) \
        .copy_feats(feature_wspecifier=feature_wspecifier, compress=parsed_arguments.compress)

    print pipeline.command()


if __name__ == '__main__':
    main()
