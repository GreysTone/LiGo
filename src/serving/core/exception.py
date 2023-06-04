"""
  Core.Exception: Exception and Error Code

  Contact: arthur.r.song@gmail.com
"""

import logging


def proto_response(pb2, prompt, err):
    message = prompt+': {}'.format(repr(err))
    logging.exception(message)
    return pb2.ResultReply(code=err.code, msg=message)

class TruenoException(Exception):
    code = 1
    message = 'unknown error'

    def __init__(self, code=None, msg=None):
        if code:
            self.code = code
        if msg:
            self.message = msg
        super(TruenoException, self).__init__(msg)

class FunctionDeprecatedError(TruenoException):
    code = 10
    msg = 'function called is already deprecated'

class ConstrainBackendInfoError(TruenoException):
    code = 100

class LimitBackendError(TruenoException):
    code = 101
    msg = 'backend instance exceed limitation'

class ExistBackendError(TruenoException):
    code = 102
    msg = 'backend has running'

class FullHashValueError(TruenoException):
    code = 103
    msg = 'fullhash value error'

class ImportModelDistroError(TruenoException):
    code = 104
    msg = "import model error"

class DeleteModelError(TruenoException):
    code = 105
    msg = "delete model error"

class CreateAndLoadModelError(TruenoException):
    code = 106
    msg = "create and load model error"

class ReloadModelOnBackendError(TruenoException):
    def __init__(self, msg=None):
        super(ReloadModelOnBackendError, self).__init__(
            code=107,
            msg="load model error{}".format(msg),
        )

class TerminateBackendError(TruenoException):
    def __init__(self):
        super(TerminateBackendError, self).__init__(
            code=108,
            msg="terminate backend error",
        )

class ListOneBackendError(TruenoException):
    def __init__(self):
        super(ListOneBackendError, self).__init__(
            code=109,
            msg="query list backend error",
        )

class InferenceDataError(TruenoException):
    code_local = 110
    code_remote = 111
    msg = 'inference data error'

class UpdateModelError(TruenoException):
    code = 112
    msg = "update model error"

class RequireInvalidBackendError(TruenoException):
    def __init__(self):
        super(RequireInvalidBackendError, self).__init__(
            code=113,
            msg="required an invalied type of backend",
        )

class InferTimeOutError(TruenoException):
    def __init__(self):
        super(InferTimeOutError, self).__init__(
            code = 114,
            msg = "inference timeout",
        )

class BackendDependencyError(TruenoException):
    def __init__(self):
        super(BackendDependencyError, self).__init__(
            code=200,
            msg="failed to find some dependency packages of given backend",
        )

class ParamValidationError(TruenoException):
    def __init__(self, msg=None):
        super(ParamValidationError, self).__init__(
            code=201,
            msg="given parameters are invalid{}".format(msg),
        )

class BackendFactoryError(TruenoException):
    def __init__(self):
        super(BackendFactoryError, self).__init__(
            code=202,
            msg="failed to get backend factory",
        )
