import base64
import logging

import numpy as np

from serving.core import debug
from serving.core import exception


def to_image(base64_str, path):
    raise exception.FunctionDeprecatedError

@debug.flow("plugin.exbase64.mem_cvmat_to_b64")
@debug.profiler("plugin.exbase64.mem_cvmat_to_b64")
def mem_cvmat_to_b64(cv_mat):
    logging.debug("encode dtype: %s, shape: %s", cv_mat.dtype, cv_mat.shape)
    return base64.b64encode(cv_mat), list(cv_mat.shape)

@debug.flow("plugin.exbase64.mem_b64_to_cvmat")
@debug.profiler("plugin.exbase64.mem_b64_to_cvmat")
def mem_b64_to_cvmat(b64_byte, shape):
    logging.debug("decode to uint8, shape: %s", shape)
    return np.frombuffer(base64.decodebytes(b64_byte), np.uint8).reshape(tuple(shape))

def mem_cvmat_to_b85(cv_mat):
    raise NotImplementedError

def mem_b85_to_cvmat(base85_str):
    raise NotImplementedError
