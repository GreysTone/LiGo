"""
  Core.Model: Model Manager

  Contact: arthur.r.song@gmail.com
"""

import os
import json
import uuid
import shutil
import hashlib
import logging
import tarfile
import urllib.request

from serving.core import debug
from serving.core import config
from serving.core import exception
from serving.core import regulator

# TODO: regulator
@debug.flow("core.create_model")
def create_model(request):
    request['mhash'] = generate_model_implhash(request)
    if _exist_model(request):
        raise RuntimeError("model already exists")
    model_hash = request['mhash'].split('-')[0]
    os.makedirs(os.path.join(config.storage(), "models", model_hash, request['version']))
    _save_model_configs(request)
    logging.debug("model created: %s", request)
    return {'code': 0, 'msg': request['mhash']}

@debug.flow("core.delete_model")
@regulator.validate(regulator.model_hash)
def delete_model(request):
    if not _exist_model(request):
        raise RuntimeError("model does not exist")
    split = request['mhash'].split('-')
    model_path = os.path.join(config.storage(), "models", split[0], split[1])
    shutil.rmtree(model_path)
    logging.debug("delete model: %s", request)
    return {'code': 0, 'msg': request['mhash']}

@debug.flow("core.list_all_models")
def list_all_models(request):
    model_list = []
    for m in os.listdir(os.path.join(config.storage(), "models")):
        for v in os.listdir(os.path.join(config.storage(), "models", m)):
            r = {'mhash': m+'-'+v}
            detail = _load_model_configs(r)
            model_list.append(detail)
    return {'models': model_list}

@debug.flow("core.inspect_model")
@regulator.validate(regulator.model_hash)
def inspect_model(request):
    return _load_model_configs(request)

@debug.flow("core.update_model_configs")
def update_model_configs(request):
    if not _exist_model(request):
        raise exception.UpdateModelError(msg="requested model not exist")
    target_dist = _load_model_configs(request)
    if target_dist['mhash'] != request['mhash']:
        raise exception.UpdateModelError(msg="incompatible model")

    if request.get('threshold') and request.get('threshold') != target_dist.get('threshold'):
        target_dist['threshold'] = request['threshold']
    if request.get('mapping') and request.get('mapping') != target_dist.get('mapping'):
        target_dist['mapping'] = request['mapping']
    if request.get('modelext') and request.get('modelext') != target_dist.get('modelext'):
        target_dist['modelext'] = request['modelext']
    target_dist['disthash'] = generate_model_disthash(target_dist)
    _save_model_configs(target_dist)
    return {'code':0, 'msg':"update"}

@debug.flow("core.update_uri_model_configs")
def update_uri_model_configs(request):
    tmp_target = os.path.join("/tmp", str(uuid.uuid4()))
    with urllib.request.urlopen(request['bundle']) as response, open(tmp_target, 'wb') as dump_file:
        shutil.copyfileobj(response, dump_file)
    with open(tmp_target, 'r') as config_file:
        configs = json.loads(config_file.read())
    return update_model_configs(configs)

@debug.flow("core.export_model")
@regulator.validate(regulator.model_hash)
def export_model(request):
    split = request['mhash'].split('-')
    tmp_path = os.path.join("/tmp", request['mhash'])
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
    shutil.copytree(os.path.join(config.storage(), "models", split[0], split[1]), tmp_path)

    if os.path.exists(os.path.join(tmp_path, "__pycache__")):
        shutil.rmtree(os.path.join(tmp_path, "__pycache__"))

    # compress
    tar = tarfile.open(os.path.join("/tmp", request['mhash']+".tar.gz"), "w:gz")
    tar.add(tmp_path, arcname=request['mhash'])
    tar.close()
    # clean tmp files
    shutil.rmtree(tmp_path)
    return {'code': 0, 'msg': request['mhash']}

@debug.flow("core.import_model")
@regulator.validate(regulator.model_hash)
def import_model(request):
    split = request['mhash'].split('-')
    bundle_path = os.path.join("/tmp", request['bundle'])
    if not os.path.exists(bundle_path):
        raise exception.ImportModelDistroError(msg="failed to find temporary bundle")

    # decompress image
    tar = tarfile.open(bundle_path, "r")
    tar.extractall("/tmp")
    tar.close()

    # import bundle
    content_path = os.path.join("/tmp", request['mhash'])
    target_model_path = os.path.join(config.storage(), "models", split[0])
    if not os.path.exists(target_model_path):
        os.makedirs(target_model_path)
    if os.path.exists(os.path.join(target_model_path, split[1])):
        raise RuntimeError("model exist specific version")
    shutil.move(content_path, os.path.join(target_model_path, split[1]))
    return {'code': 0, 'msg': request['mhash']}

@debug.flow("core.import_uri_model")
def import_uri_model(request):
    # TODO(): a more elegant way: on-air decompression
    # with urllib.request.urlopen(configs['bundle']) as response:
    #     with tarfile.TarFile(fileobj=response) as uncompress:
    target_uuid = str(uuid.uuid4())
    tmp_target = os.path.join("/tmp", target_uuid)
    with urllib.request.urlopen(request['bundle']) as response, open(tmp_target, 'wb') as dump_file:
        shutil.copyfileobj(response, dump_file)
    request['bundle'] = target_uuid
    return import_model(request)

#
@debug.flow("core.check_model_exist")
def _exist_model(request):
    split = request['mhash'].split('-')
    model_path = os.path.join(config.storage(), "models", split[0], split[1])
    existance = os.path.exists(model_path)
    logging.debug("exist (%s): %s (@%s/models)", existance, request['mhash'], config.storage())
    return existance

@debug.flow("core._load_model_configs")
def _load_model_configs(request):
    if not _exist_model(request):
        raise RuntimeError("model does not exist")
    split = request['mhash'].split('-')
    dist_path = os.path.join(config.storage(), "models", split[0], split[1], "distros.json")
    if not os.path.exists(dist_path):
        raise RuntimeError("model distro not exist: ({})".format(request['mhash']))
    with open(dist_path, 'r') as dist_file:
        detail = json.loads(dist_file.read())
    logging.debug("fetched: %s", request['mhash'])
    return detail

@debug.flow("core._save_model_configs")
def _save_model_configs(request):
    if not _exist_model(request):
        raise RuntimeError("model does not exist")
    split = request['mhash'].split('-')
    dist_path = os.path.join(config.storage(), "models", split[0], split[1], "distros.json")
    with open(dist_path, 'w') as dist_file:
        dist_file.write(json.dumps(request, indent=2))

@debug.flow("core.generate_model_implhash")
def generate_model_implhash(configs):
    """Generate model implhash from configs' label, head, bone, impl and version
    """
    hash_string = "{}{}{}{}".format(
        "".join(configs['labels']),
        configs['head'],
        configs['bone'],
        configs['impl'],
    )
    return "{}-{}".format(
        hashlib.md5(hash_string.encode('utf-8')).hexdigest(),
        configs['version'])

@debug.flow("core.generate_model_disthash")
def generate_model_disthash(configs):
    """Generate model disthash from configs' threshold and mapping
    """
    hash_string = "{}{}".format(
        "".join(configs['threshold']),
        "".join(configs['mapping']),
    )
    return hashlib.md5(hash_string.encode('utf-8')).hexdigest()
