from pybash import common, pybash


class PyKaldiPipeline(pybash.PyBashPipeline):
    def __init__(self, input_operation=None):
        super(PyKaldiPipeline, self).__init__(input_operation=input_operation)

    @common.actual_kwargs()
    def paste_feats(self, in_rs, out_w, binary=True, length_tolerance=0, config='', print_args=True, verbose=0,
                    buffer_size=common.DEFAULT_BUFFER_SIZE):
        self.head = PyKaldiPasteFeats(self.head, in_rs, out_w, **self.paste_feats.actual_kwargs)
        return self

    @common.actual_kwargs()
    def copy_feats(self, in_r, out_w, binary=True, compress=False, htk_in=False, sphinx_in=False, config='',
                   print_args=True, verbose=0, buffer_size=common.DEFAULT_BUFFER_SIZE):
        self.head = PyKaldiCopyFeats(self.head, in_r, out_w, **self.copy_feats.actual_kwargs)
        return self


class PyKaldiPasteFeats(pybash.PyBashCall):
    @common.actual_kwargs()
    def __init__(self, source, in_rs, out_w, binary=True, length_tolerance=0, config='', print_args=True, verbose=0,
                 _buffer_size=common.DEFAULT_BUFFER_SIZE):
        super(PyKaldiPasteFeats, self).__init__(
            source, ('paste-feats',) + pybash.PyBashCall.flags(**self.__init__.actual_kwargs) + tuple(in_rs) + (out_w,),
            source_may_be_none=True, buffer_size=_buffer_size)


class PyKaldiCopyFeats(pybash.PyBashCall):
    @common.actual_kwargs()
    def __init__(self, source, in_r, out_w, binary=True, compress=False, htk_in=False, sphinx_in=False, config='',
                 print_args=True, verbose=0, _buffer_size=common.DEFAULT_BUFFER_SIZE):
        super(PyKaldiCopyFeats, self).__init__(
            source, ('copy-feats',) + pybash.PyBashCall.flags(**self.__init__.actual_kwargs) + (in_r, out_w),
            source_may_be_none=True, buffer_size=_buffer_size)
