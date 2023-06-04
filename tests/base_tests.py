#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import logging
import subprocess

import ligo


RESULT = None

def _check_running_process():
    ps = subprocess.Popen(('ps', '-aux'), stdout=subprocess.PIPE)
    output = subprocess.check_output(('grep', 'run.py'), stdin=ps.stdout)
    ps.wait()
    out = str(output, encoding='utf-8').split('\n')
    clean_out = [it for it in out if 'grep' not in it]
    return clean_out

def process_checker():
    def decorator(func):
        def wrapper(*args, **kwargs):
            np_t1 = _check_running_process()
            ret = func(*args, **kwargs)
            np_t2 = _check_running_process()
            if len(np_t2) != len(np_t1):
                raise RuntimeError("potential subprocess leaking: {}->{}\n t1:\n{}\nt2:\n{}".format(len(np_t1), len(np_t2), np_t1, np_t2))
            logging.info("subprocess checking: %s->%s", len(np_t1), len(np_t2))
            return ret
        return wrapper
    return decorator

@process_checker()
def case_corrupt_preheat(_node, _model, _ty, _out, _code, _key):
    print("TEST: --->>> case_corrupt_preheat")
    _node.update_preheat_image('/specify/wrong/path')
    ret = _node.create_backend(
        ty=_ty,
        model_id=_model,
        outlet_list=[_out],
        password=_code,
        privatekey=_key
    )
    bid = ret['msg']
    ret, _ = _node.run_backend(bid)
    if ret is not False:
        raise RuntimeError("case_corrupt_preheat does not return False")
    _node.delete_backend(backend_id=bid)

@process_checker()
def case_teminate_running_backend(_node, _model, _ty, _out, _code, _key, _preheat):
    print("TEST: --->>> case_terminate_running_backend")
    _node.update_preheat_image(_preheat)
    ret = _node.create_backend(
        ty=_ty,
        model_id=_model,
        outlet_list=[_out],
        password=_code,
        privatekey=_key
    )
    bid = ret['msg']
    ret, _ = _node.run_backend(bid)
    if ret == False:
        raise RuntimeError("case_terminate_running_backend return False")
    _node.stop_backend(backend_id=bid)
    _node.delete_backend(backend_id=bid)

@process_checker()
def case_correct_model(_node, _model, _ty, _out, _code, _key, _preheat, _target, _checker):
    print("TEST: --->>> case_correct_model")
    global RESULT
    _node.update_preheat_image(_preheat)
    ret = _node.create_backend(
        ty=_ty,
        model_id=_model,
        outlet_list=[_out],
        password=_code,
        privatekey=_key
    )
    bid = ret['msg']
    ret, _ = _node.run_backend(bid)
    if ret == False:
        raise RuntimeError("case_correct_model return False")
    _node.async_compute_image(
        backend_id=bid,
        compute_id="example_topic",
        image_path=_target)
    time.sleep(1)
    if (RESULT is None) or (not _checker(RESULT)):
        raise RuntimeError("case_correct_model failed")
    _node.stop_backend(backend_id=bid)
    _node.delete_backend(backend_id=bid)

# TODO: tensorflow will take up whole GPU memory
@process_checker()
def case_multiple_same_model(_node, _model, _ty, _out, _code, _key, _preheat, _target, _checker):
    print("TEST: --->>> case_multiple_same_model")
    global RESULT
    _node.update_preheat_image(_preheat)
    ret = _node.create_backend(
        ty=_ty,
        model_id=_model,
        outlet_list=[_out],
        password=_code,
        privatekey=_key
    )
    bid0 = ret['msg']
    ret, _ = _node.run_backend(bid0)
    if ret == False:
        raise RuntimeError("case_multiple_same_model b0 return False")
    ret = _node.create_backend(
        ty=_ty,
        model_id=_model,
        outlet_list=[_out],
        password=_code,
        privatekey=_key
    )
    bid1 = ret['msg']
    ret, _ = _node.run_backend(bid1)
    if ret == False:
        raise RuntimeError("case_multiple_same_model b1 return False")

    _node.async_compute_image(
        backend_id=bid1,
        compute_id="example_topic",
        image_path=_target)
    time.sleep(1)
    if (RESULT is None) or (not _checker(RESULT)):
        raise RuntimeError("case_multiple_same_model failed")
    _node.stop_backend(backend_id=bid0)
    _node.delete_backend(backend_id=bid0)
    _node.stop_backend(backend_id=bid1)
    _node.delete_backend(backend_id=bid1)


# TODO:
def case_multiple_diff_model(_node, _model, _ty, _out, _code, _key, _preheat, _target, _checker):
    pass

def run(_uri, _model, _ty, _code, _key, _preheat, _target, _checker):
    node0 = ligo.LiGo()
    print(node0.ping())
    node0.update_storage_path('/tmp/storage')

    # import model on-air
    node0.import_model_from_uri(model_hash=_model, uri=_uri+_model+".tar.gz")
    node0.update_model_configs_from_uri(model_hash=_model, uri=_uri+_model+".json")
    ret = node0.inspect_model(model_hash=_model)
    if ret['mhash'] != _model:
        sys.exit(-1)

    # set default mqtt outlet, bind callback
    outlet_config = ligo.mosquitto_outlet()
    ligo.receive_from_mosquitto(
        topic="example_topic",
        callback=_get_result,
        outlet=outlet_config
    )
    print(outlet_config)

    try:
        case_corrupt_preheat(node0, _model, _ty, outlet_config, _code, _key)
        case_teminate_running_backend(node0, _model, _ty, outlet_config, _code, _key, _preheat)
        case_correct_model(node0, _model, _ty, outlet_config, _code, _key, _preheat, _target, _checker)
        #case_multiple_same_model(node0, _model, _ty, outlet_config, _code, _key, _preheat, _target, _checker)
    except Exception as err:
        logging.exception(err)
        sys.exit(-1)

#    node0.delete_model(model_hash=_model)
#    node0.update_storage_path('replace_with_storage')
#    node0.update_preheat_image('replace_with_preheat_image')

def _get_result(client, userdata, msg):
    global RESULT
    print("raw("+msg.topic+"): "+str(msg.payload))
    RESULT = json.loads(str(msg.payload,encoding="utf-8"))
