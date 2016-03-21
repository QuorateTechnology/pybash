from pybash import common, pybash


class PyKaldiPipeline(pybash.PyBashPipeline):
    def __init__(self, input_operation=None):
        super(PyKaldiPipeline, self).__init__(input_operation=input_operation)

    def command(self, prefix='', suffix=''):
        return TODO

    @common.actual_kwargs()
    def paste_feats(
            self, out_wspecifier='ark:-', binary=True, length_tolerance=0, config='', print_args=True,
            verbose=0, buffer_size=common.DEFAULT_BUFFER_SIZE, *in_rspecifiers):
        self.head = PyKaldiPasteFeats(self.head, *in_rspecifiers, **self.paste_feats.actual_kwargs)
        return self

    @common.actual_kwargs()
    def copy_feats(
            self, feature_rspecifier='ark:-', feature_wspecifier='ark:-', binary=True, compress=False, htk_in=False,
            sphinx_in=False, config='', print_args=True, verbose=0, buffer_size=common.DEFAULT_BUFFER_SIZE):
        self.head = PyKaldiCopyFeats(self.head, **self.copy_feats.actual_kwargs)
        return self

    @common.actual_kwargs()
    def extract_segments(
            self, segments_file, wav_rspecifier='ark:-', wav_wspecifier='ark:-', max_overshoot=0.5,
            min_segment_length=0.1, config='', print_args=True, verbose=0, buffer_size=common.DEFAULT_BUFFER_SIZE):
        self.head = PyKaldiExtractSegments(self.head, segments_file, **self.copy_feats.actual_kwargs)
        return self

    @common.actual_kwargs()
    def compute_fbank_feats(
            self, wav_rspecifier='ark:-', feats_wspecifier='ark:-', channel=-1, debug_mel=False, dither=1,
            energy_floor=0, frame_length=25, frame_shift=10, high_freq=0, htk_compat=False, low_freq=20, min_duration=0,
            num_mel_bins=23, output_format='kaldi', preemphasis_coefficient=0.97, raw_energy=True,
            remove_dc_offset=True, round_to_power_of_two=True, sample_frequency=16000, snip_edges=True,
            subtract_mean=False, use_energy=False, use_log_fbank=True, utt2spk='', vtln_high=-500, vtln_low=100,
            vtln_map='', vtln_warp=1, window_type='povey', config='', print_args=True, verbose=0,
            buffer_size=common.DEFAULT_BUFFER_SIZE):
        self.head = PyKaldiComputeFbankFeats(self.head, **self.copy_feats.actual_kwargs)
        return self

    @common.actual_kwargs()
    def compute_kaldi_pitch_feats(
            self, wav_rspecifier='ark:-', feats_wspecifier='ark:-', delta_pitch=0.005, frame_length=25, frame_shift=10,
            frames_per_chunk=0, lowpass_cutoff=1000, lowpass_filter_width=1, max_f0=400, max_frames_latency=0,
            min_f0=50, nccf_ballast=7000, nccf_ballast_online=False, penalty_factor=0.1, preemphasis_coefficient=0,
            recompute_frame=500, resample_frequency=4000, sample_frequency=16000, simulate_first_pass_online=False,
            snip_edges=True, soft_min_f0=10, upsample_filter_width=5, config='', print_args=True, verbose=0,
            buffer_size=common.DEFAULT_BUFFER_SIZE):
        self.head = PyKaldiComputeKaldiPitchFeats(self.head, **self.copy_feats.actual_kwargs)
        return self

    @common.actual_kwargs()
    def process_kaldi_pitch_feats(
            self, feat_rspecifier='ark:-', feats_wspecifier='ark:-', add_delta_pitch=True,
            add_normalized_log_pitch=True, add_pov_feature=True, add_raw_log_pitch=False, delay=0,
            delta_pitch_noise_stddev=0.005, delta_pitch_scale=10, delta_window=2, normalization_left_context=75,
            normalization_right_context=75, pitch_scale=2, pov_offset=0, pov_scale=2, srand=0, config='',
            print_args=True, verbose=0, buffer_size=common.DEFAULT_BUFFER_SIZE):
        self.head = PyKaldiProcessKaldiPitchFeats(self.head, **self.copy_feats.actual_kwargs)
        return self


class PyKaldiPasteFeats(pybash.PyBashCall):
    @common.actual_kwargs()
    def __init__(self, source, out_wspecifier='ark:-', binary=True, length_tolerance=0, config='',
                 print_args=True, verbose=0, _buffer_size=common.DEFAULT_BUFFER_SIZE, *in_rspecifiers):
        super(PyKaldiPasteFeats, self).__init__(
            source, ('paste-feats',) + pybash.PyBashCall.flags(**self.__init__.actual_kwargs) + tuple(in_rspecifiers) +
                    (out_wspecifier,), source_may_be_none=True, buffer_size=_buffer_size)


class PyKaldiCopyFeats(pybash.PyBashCall):
    @common.actual_kwargs()
    def __init__(self, source, feature_rspecifier='ark:-', feature_wspecifier='ark:-', binary=True, compress=False,
                 htk_in=False, sphinx_in=False, config='',
                 print_args=True, verbose=0, _buffer_size=common.DEFAULT_BUFFER_SIZE):
        super(PyKaldiCopyFeats, self).__init__(
            source, ('copy-feats',) + pybash.PyBashCall.flags(**self.__init__.actual_kwargs) +
                    (feature_rspecifier, feature_wspecifier), source_may_be_none=True, buffer_size=_buffer_size)


class PyKaldiExtractSegments(pybash.PyBashCall):
    @common.actual_kwargs()
    def __init__(self, source, segments_file, wav_rspecifier='ark:-', wav_wspecifier='ark:-', max_overshoot=0.5,
                 min_segment_length=0.1, config='', print_args=True, verbose=0,
                 _buffer_size=common.DEFAULT_BUFFER_SIZE):
        super(PyKaldiExtractSegments, self).__init__(
            source, ('extract-segments',) + pybash.PyBashCall.flags(**self.__init__.actual_kwargs) +
                    (wav_rspecifier, segments_file, wav_wspecifier), source_may_be_none=True, buffer_size=_buffer_size)


class PyKaldiComputeFbankFeats(pybash.PyBashCall):
    @common.actual_kwargs()
    def __init__(self, source, wav_rspecifier='ark:-', feats_wspecifier='ark:-', channel=-1, debug_mel=False, dither=1,
                 energy_floor=0, frame_length=25, frame_shift=10, high_freq=0, htk_compat=False, low_freq=20,
                 min_duration=0, num_mel_bins=23, output_format='kaldi', preemphasis_coefficient=0.97, raw_energy=True,
                 remove_dc_offset=True, round_to_power_of_two=True, sample_frequency=16000, snip_edges=True,
                 subtract_mean=False, use_energy=False, use_log_fbank=True, utt2spk='', vtln_high=-500, vtln_low=100,
                 vtln_map='', vtln_warp=1, window_type='povey', config='', print_args=True, verbose=0,
                 _buffer_size=common.DEFAULT_BUFFER_SIZE):
        super(PyKaldiComputeFbankFeats, self).__init__(
            source, ('compute-fbank-feats',) + pybash.PyBashCall.flags(**self.__init__.actual_kwargs) +
                    (wav_rspecifier, feats_wspecifier), source_may_be_none=True, buffer_size=_buffer_size)


class PyKaldiComputeKaldiPitchFeats(pybash.PyBashCall):
    @common.actual_kwargs()
    def __init__(self, source, wav_rspecifier='ark:-', feats_wspecifier='ark:-', delta_pitch=0.005, frame_length=25,
                 frame_shift=10, frames_per_chunk=0, lowpass_cutoff=1000, lowpass_filter_width=1, max_f0=400,
                 max_frames_latency=0, min_f0=50, nccf_ballast=7000, nccf_ballast_online=False, penalty_factor=0.1,
                 preemphasis_coefficient=0, recompute_frame=500, resample_frequency=4000, sample_frequency=16000,
                 simulate_first_pass_online=False, snip_edges=True, soft_min_f0=10, upsample_filter_width=5, config='',
                 print_args=True, verbose=0, _buffer_size=common.DEFAULT_BUFFER_SIZE):
        super(PyKaldiComputeKaldiPitchFeats, self).__init__(
            source, ('compute-kaldi-pitch-feats',) + pybash.PyBashCall.flags(**self.__init__.actual_kwargs) +
                    (wav_rspecifier, feats_wspecifier), source_may_be_none=True, buffer_size=_buffer_size)


class PyKaldiProcessKaldiPitchFeats(pybash.PyBashCall):
    @common.actual_kwargs()
    def __init__(self, source, feat_rspecifier, feats_wspecifier, add_delta_pitch=True, add_normalized_log_pitch=True,
                 add_pov_feature=True, add_raw_log_pitch=False, delay=0, delta_pitch_noise_stddev=0.005,
                 delta_pitch_scale=10, delta_window=2, normalization_left_context=75, normalization_right_context=75,
                 pitch_scale=2, pov_offset=0, pov_scale=2, srand=0, config='', print_args=True, verbose=0,
                 _buffer_size=common.DEFAULT_BUFFER_SIZE):
        super(PyKaldiProcessKaldiPitchFeats, self).__init__(
            source, ('process-kaldi-pitch-feats',) + pybash.PyBashCall.flags(**self.__init__.actual_kwargs) +
                    (feat_rspecifier, feats_wspecifier), source_may_be_none=True, buffer_size=_buffer_size)
