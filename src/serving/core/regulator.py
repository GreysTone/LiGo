"""
  Core.Regulator: Regulates functionality with expected behaviour

  Contact: arthur.r.song@gmail.com
"""

import json
import logging

from serving.core import config
from serving.core import exception
from serving.core.memory import FEATURE_GATE, BACKEND

def if_feature_on_run(gate_option, feature_func):
    """When `gate_option` is `True`, inserts `feature_func` before original one
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if gate_option:
                feature_func()
                return func(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def if_feature_off_raise(gate_option, err):
    """When `gate_option` is `False`, raise the given `err`
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if gate_option is not True:
                raise err
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate(validator):
    """Use `validator` to validate passed in arguments
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            validator(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def limit(gate_option, feature_func):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if gate_option:
                isExist = feature_func(*args, **kwargs)
                if isExist:
                    raise exception.ExistBackendError
                return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator

def backend_initialize(args):
    logging.debug("   raw args: %s", args)
    if args.get('impl') is None:
        args['impl'] = '.'
    if args.get('storage') is None:
        args['storage'] = config.storage()
    if args.get('preheat') is None:
        args['preheat'] = config.preheat()
    if args.get('batchsize') is None:
        args['batchsize'] = 1
    if args.get('inferprocnum') is None:
        args['inferprocnum'] = 1
    #ConstrainBackendInfo(args)

def backend_bid(args):
    if args.get('bid') is None:
        raise exception.ParamValidationError(": backend id")

def backend_load(args):
    logging.debug("   raw args: %s", args)
    if args.get('model') is None:
        raise exception.ParamValidationError(": model")
    if args.get('encrypted') is None:
        args['encrypted'] = 0
    if args['encrypted'] != 0 and args['encrypted'] != 1:
        args['encrypted'] = 0
    if not FEATURE_GATE['on_sandbox'] and args.get('encrypted') == 1:
        raise exception.ParamValidationError(": sandbox feature conflicts with encrypted option")
    if FEATURE_GATE['on_sandbox'] and args['encrypted'] == 1:
        if args.get('a64key') is None or args.get('pvtkey') is None:
            raise exception.ParamValidationError(": access code, decrypt private key")
    # TODO(): move this to models
    #if args.get('model').get('implhash') is None:
    #    args['model']['implhash'] = model.generate_model_implhash(args)

def backend_append_outlet(args):
    if args.get('type') is None:
        raise exception.ParamValidationError(": type")
    if args.get('configs') is None:
        raise exception.ParamValidationError(": configs")
    args['configs'] = json.loads(args['configs'])
    logging.debug(" updated args: %s", args)

def backend_remove_outlet(args):
    if args.get('key') is None:
        raise exception.ParamValidationError(": key")

def compute_required(args):
    if args.get('uuid') is None:
        raise exception.ParamValidationError(": uuid")
    if args.get('outlet') is None:
        raise exception.ParamValidationError(": outlet id")

def compute_local(args):
    if args.get('path') is None:
        raise exception.ParamValidationError(": path")

def compute_remote(args):
    if args.get('data') is None or args.get('extra') is None or args.get('dtype') is None:
        raise exception.ParamValidationError(": data, extra or dtype")

def outlet_required(args):
    if args.get('instance') is None:
        raise exception.ParamValidationError(": instance")

def outlets_option(args):
    if args.get('outlets') is None:
        args['outlets'] = []

def work_whash(args):
    if args.get('whash') is None:
        raise exception.ParamValidationError(": hash")

def reader_source_required(args):
    if args.get('source') is None:
        raise exception.ParamValidationError(": source")

def model_hash(args):
    if args.get('mhash') is None:
        raise exception.ParamValidationError(": mhash")

def ConstrainBackendInfo(info):
    limitation = config.lim_max_batchsize()
    if not isinstance(limitation, int) or limitation < 1:
        limitation = 1
    if info['batchsize'] > limitation:
        raise exception.ConstrainBackendInfoError(msg="batchsize exceed limitation")

    limitation = config.lim_max_compute_process()
    if not isinstance(limitation, int) or limitation < 2:
        limitation = 2
    if info['inferprocnum'] > limitation:
        raise exception.ConstrainBackendInfoError(msg="inference process number exceed limitation")

# def CheckBackendExistInstance(info, passby_model):
#     if passby_model is None:
#         return False
#     for key, _ in BACKEND.items():
#         backendInfo = backend.list_backend_spec({'bid': key})
#         if int(json.loads(backendInfo['status'])["0"]) == 4 and backendInfo['info']['impl'] == info['impl'] \
#                 and backendInfo['model']['version'] == passby_model['version'] \
#                 and backendInfo['model']['implhash'] == passby_model['implhash']:
#             return True
#         backend.terminate_backend(info)

def LimitBackendInstance():
    limitation = config.lim_max_backend_count()
    if not isinstance(limitation, int) or limitation < 1:
        limitation = 1
    if len(BACKEND) + 1 > limitation:
        raise exception.LimitBackendError(msg="backend instance exceed limitation")
