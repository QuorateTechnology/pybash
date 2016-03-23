#!/usr/bin/env python
import argparse
import logging
from os import path
from pybash import basic, common, pybash
import pykaldi
import sys

"""
This script demonstrates the use of pybash to wrap some Kaldi binaries. It is a direct replacement for
make_fbank_pitch.sh [1]. We have deliberately kept the style similar to the original script but a true replacement could
be made more Pythonic.

CAUTION: This script is currently incomplete and will not run correctly!

[1] https://github.com/kaldi-asr/kaldi/blob/master/egs/wsj/s5/steps/make_fbank_pitch.sh
"""


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('data_dir')
    argument_parser.add_argument('log_dir')
    argument_parser.add_argument('fbank_pitch_dir')
    argument_parser.add_argument('--cmd', default='run.pl')
    argument_parser.add_argument('--collect', type=bool, default=True)
    argument_parser.add_argument('--compress', type=bool, default=True)
    argument_parser.add_argument('--fbank-config', default='conf/fbank.conf')
    argument_parser.add_argument('--nj', type=int, default=4)
    argument_parser.add_argument('--paste-length-tolerance', type=int, default=2)
    argument_parser.add_argument('--pitch-config', default='conf/pitch.conf')
    argument_parser.add_argument('--pitch-postprocess-config', default=None)
    parsed_arguments = argument_parser.parse_args()

    logging.info(' '.join(sys.argv))  # Print the command line for logging

    data = parsed_arguments.data_dir
    logdir = parsed_arguments.log_dir
    fbank_pitch_dir = parsed_arguments.fbank_pitch_dir
    fbank_config = parsed_arguments.fbank_config
    pitch_config = parsed_arguments.pitch_config

    # make $fbank_pitch_dir an absolute pathname.
    fbank_pitch_dir = path.abspath(parsed_arguments.fbank_pitch_dir)

    # use "name" as part of name of the archive.
    name = path.basename(parsed_arguments.data_dir)

    common.makedirs(fbank_pitch_dir)
    common.makedirs(parsed_arguments.log_dir)

    if path.exists('{data}/feats.scp'.format(**locals())):
        common.makedirs('{data}/.backup'.format(**locals()))
        logging.info('moving {data}/feats.scp to {data}/.backup'.format(**locals()))
        basic.mv('{data}/feats.scp'.format(**locals()), '{data}/.backup'.format(**locals()))

    scp = '{data}/wav.scp'.format(**locals())

    for f in (scp, fbank_config, pitch_config):
        if not path.exists(f):
            raise Exception('make_fbank_pitch.sh: no such file ' + f)

    if parsed_arguments.pitch_postprocess_config is not None:
        postprocess_config_opt = dict(config=parsed_arguments.pitch_postprocess_config)
    else:
        postprocess_config_opt = {}

    basic.call('utils/validate_data_dir.sh', '--no-text', '--no-feats', data)

    if path.exists('{data}/spk2warp'.format(**locals())):
        logging.info('using VTLN warp factors from {data}/spk2warp'.format(**locals()))
        vtln_opts = dict(vtln_map='ark:{data}/spk2warp'.format(**locals()),
                         utt2spk='ark:{data}/utt2spk'.format(**locals()))
    elif path.exists('{data}/utt2warp'.format(**locals())):
        logging.info('using VTLN warp factors from {data}/utt2warp'.format(**locals()))
        vtln_opts = dict(vtln_map='ark:{data}/utt2warp'.format(**locals()))
    else:
        vtln_opts = {}

    for n in basic.seq(parsed_arguments.nj):
        # the next command does nothing unless $fbank_pitch_dir/storage/ exists, see
        # utils/create_data_link.pl for more info.
        basic.call('utils/create_data_link.pl', '{fbank_pitch_dir}/raw_fbank_pitch_{name}.{n}.ark'.format(**locals()))

    if path.exists('{data}/segments'.format(**locals())):
        logging.info('segments file exists: using that.')

        split_segments = ['{logdir}/segments.{n}'.format(**locals()) for n in basic.seq(parsed_arguments.nj)]

        basic.call('utils/split_scp.pl', '{data}/segments'.format(**locals()), *split_segments)
        basic.rm('{logdir}/.error'.format(**locals()), ignore_errors=True)

        fbank_feats = pykaldi.PyKaldiPipeline() \
            .extract_segments('{logdir}/segments.JOB'.format(**locals()),
                              wav_rspecifier='scp,p:{scp}'.format(**locals())) \
            .compute_fbank_feats(verbose=2, config=parsed_arguments.fbank_config, **vtln_opts)

        pitch_feats = pykaldi.PyKaldiPipeline() \
            .extract_segments('{logdir}/segments.JOB'.format(**locals()),
                              wav_rspecifier='scp,p:{scp}'.format(**locals())) \
            .compute_kaldi_pitch_feats(verbose=2, config=parsed_arguments.pitch_config, **vtln_opts) \
            .process_kaldi_pitch_feats(**postprocess_config_opt)

        feature_wspecifier = 'ark,scp:{fbank_pitch_dir}/raw_fbank_pitch_{name}.JOB.ark,' \
                             '{fbank_pitch_dir}/raw_fbank_pitch_{name}.JOB.scp'.format(**locals())

        pipeline = pykaldi.PyKaldiPipeline() \
            .paste_feats((fbank_feats.command('"ark:', ' |"'), pitch_feats.command('"ark,s,cs:', ' |"')),
                         length_tolerance=parsed_arguments.paste_length_tolerance) \
            .copy_feats(feature_wspecifier=feature_wspecifier, compress=parsed_arguments.compress)

        basic.call(parsed_arguments.cmd, 'JOB=1:{parsed_arguments.nj}'.format(**locals()),
                   '{logdir}/make_fbank_pitch_{name}.JOB.log'.format(**locals()), pipeline.command())

    else:
        logging.info('no segments file exists: assuming wav.scp indexed by utterance.')

        split_scps = ['{logdir}/wav.{n}.scp'.format(**locals()) for n in basic.seq(parsed_arguments.nj)]

        basic.call('utils/split_scp.pl', scp, *split_scps)

        fbank_feats = pykaldi.PyKaldiPipeline() \
            .compute_fbank_feats(wav_rspecifier='scp,p:{logdir}/wav.JOB.scp'.format(**locals()), verbose=2,
                                 config=parsed_arguments.fbank_config, **vtln_opts)

        pitch_feats = pykaldi.PyKaldiPipeline() \
            .compute_kaldi_pitch_feats(wav_rspecifier='scp,p:{logdir}/wav.JOB.scp'.format(**locals()), verbose=2,
                                       config=parsed_arguments.pitch_config, **vtln_opts) \
            .process_kaldi_pitch_feats(**postprocess_config_opt)

        feature_wspecifier = 'ark,scp:{fbank_pitch_dir}/raw_fbank_pitch_{name}.JOB.ark,' \
                             '{fbank_pitch_dir}/raw_fbank_pitch_{name}.JOB.scp'.format(**locals())

        pipeline = pykaldi.PyKaldiPipeline() \
            .paste_feats((fbank_feats.command('"ark:', ' |"'), pitch_feats.command('"ark,s,cs:', ' |"')),
                         length_tolerance=parsed_arguments.paste_length_tolerance) \
            .copy_feats(feature_wspecifier=feature_wspecifier, compress=parsed_arguments.compress)

        basic.call(parsed_arguments.cmd, 'JOB=1:{parsed_arguments.nj}'.format(**locals()),
                   '{logdir}/make_fbank_pitch_{name}.JOB.log'.format(**locals()), pipeline.command())

    if path.exists('{logdir}/.error.{name}'.format(**locals())):
        logging.error('Error producing fbank & pitch features for {name}:'.format(**locals()))
        exit(1)

    # concatenate the .scp files together.
    pybash.PyBashPipeline().cat_call(
        *['{fbank_pitch_dir}/raw_fbank_pitch_{name}.{n}.scp'.format(**locals())
          for n in basic.seq(parsed_arguments.nj)]) \
        .execute('{data}/feats.scp'.format(**locals()))

    basic.rm(('{logdir}/wav.*.scp'.format(**locals()), '{logdir}/segments.*'.format(**locals())), ignore_errors=True)

    nf = pybash.PyBashPipeline().cat_call('{data}/feats.scp'.format(**locals())).wc_call(lines=True).execute().read()
    nu = pybash.PyBashPipeline().cat_call('{data}/utt2spk'.format(**locals())).wc_call(lines=True).execute().read()

    if nf != nu:
        logging.warn('It seems not all of the feature files were successfully processed ({nf} != {nu});'
                     .format(**locals()))
        logging.warn('consider using utils/fix_data_dir.sh {data}'.format(**locals()))

    logging.info('Succeeded creating filterbank & pitch features for {name}'.format(**locals()))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
