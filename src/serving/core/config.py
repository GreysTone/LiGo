"""
  Core.Config: Configs Manager

  Contact: arthur.r.song@gmail.com
"""

import json
import logging

import yaml

from serving.core import exception
from serving.core.memory import SYS_CONFIGS, WORK


def load_configs_from_disk(config_path):
    """Load all configs of Trueno
    """
    logging.debug("loading configs from %s", config_path)
    with open(config_path, 'r') as config_file:
        confs = yaml.safe_load(config_file)
        _flush_memory_configs(confs)

def _dump_configs_to_disk(config_path="confs.yaml"):
    logging.debug("dumping configs to %s", config_path)
    with open(config_path, 'w') as config_file:
        yaml.dump(SYS_CONFIGS, config_file, default_flow_style=False)
    return {'code': 0, 'msg': "config saved"}

def _flush_memory_configs(configs):
    global SYS_CONFIGS
    SYS_CONFIGS = configs
    logging.debug("flushed system configs to: %s", configs)

def list_all_configs(request):
    """List all configs of Trueno
    """
    logging.debug("request from: %s", request['client'])
    _configs = []
    for key in SYS_CONFIGS:
        _configs.append({
            'key': key,
            'val': json.dumps(SYS_CONFIGS[key])
        })
    return _configs

def update_config(request):
    """Update config of Trueno
    """
    if request.get('key') is None:
        raise exception.ParamValidationError(": key")
    if request.get('val') is None:
        raise exception.ParamValidationError(": val")
    if '.' not in request['key']:
        raise exception.ParamValidationError(": invalid key format")
    raw_split = request['key'].split('.')
    if len(raw_split) != 2:
        raise exception.ParamValidationError(": invalid key format")
    if raw_split[0] != 'backend' and raw_split[0] != 'customize':
        raise exception.ParamValidationError(": invalid key format")
    if raw_split[0] == 'backend' and \
        raw_split[1] != 'storage' and \
        raw_split[1] != 'preheat':
        raise exception.ParamValidationError(": config ({}) access deined".format(request['key']))
    SYS_CONFIGS[raw_split[0]][raw_split[1]] = request['val']
    return _dump_configs_to_disk()

def exist_persist_work(whash):
    if SYS_CONFIGS.get('work') is None:
        return 0
    w = SYS_CONFIGS['work'].get(whash)
    if w is None:
        return 0
    else:
        return 1

def enable_persist_work(request):
    global SYS_CONFIGS
    if exist_persist_work(request['whash']):
        return {'code': 0, 'msg': request['whash']}
    if SYS_CONFIGS.get('work') is None:
        SYS_CONFIGS['work'] = {}
    SYS_CONFIGS['work'][request['whash']] = {
        'wtype': request['wtype'],
        'configs': request['configs'],
        'link': request['link'],
    }
    return _dump_configs_to_disk()

def disable_persist_work(whash):
    if not exist_persist_work(whash):
        return {'code': 0, 'msg': whash}
    del SYS_CONFIGS['work'][whash]
    return _dump_configs_to_disk()

def debug_option():
    return SYS_CONFIGS['sys']['debug']['enabled']

# TODO: rename to verbose
def debug_vvv():
    return SYS_CONFIGS['sys']['debug']['detailed']

def multiple_mode():
    return SYS_CONFIGS['multiple']

def profile_option():
    return SYS_CONFIGS['sys']['debug']['profiler']

def grpc_port():
    return SYS_CONFIGS['sys']['grpc_port']

def restful_port():
    return SYS_CONFIGS['sys']['restful_port']

def gates():
    return SYS_CONFIGS['ext']['gates']

def plugins():
    return SYS_CONFIGS['ext']['plugins']

def backend_factory():
    return SYS_CONFIGS['ext']['backend']

def outlet_factory():
    return SYS_CONFIGS['ext']['outlet']

def work_factory():
    return SYS_CONFIGS['ext']['work']

def storage():
    return SYS_CONFIGS['backend']['storage']

def preheat():
    return SYS_CONFIGS['backend']['preheat']

def lim_max_batchsize():
    return SYS_CONFIGS['lmt']['max_batchsize']

def lim_max_backend_count():
    return SYS_CONFIGS['lmt']['max_backend_count']

def lim_max_compute_process():
    return SYS_CONFIGS['lmt']['max_compute_process']

#
def _get_str(key, default_val):
    return str(_get_val(key, default_val))

def _get_bool(key, default_val):
    return bool(_get_val(key, default_val))

def _get_dict(key, default_val):
    return json.loads(_get_val(key, default_val))

def _get_val(key, default_val):
    _val = SYS_CONFIGS.get(key)
    if _val is None:
        return default_val
    return _val
