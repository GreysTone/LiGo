#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

# relocate package, when ligo_sdk is not installed
sys.path.append(os.path.dirname(__file__)+os.sep+'../')
print(sys.path)
import ligo

def run():
    node0 = ligo.LiGo()

    print(node0.list_all_configs())
    print(node0.update_storage_path('/tmp/storage'))
    print(node0.list_all_configs())

    # backend.proto
    print(node0.list_supported_backend_type())
    print(node0.list_all_backends())

    # connectivity.proto
    print(node0.ping())
    # print(node0.list_node_resources())

    # model.proto
    ext = {
        'tensors': {
            'input_type': ['1', '0'],
            'input':  ['Placeholder:0', 'Placeholder_1:0'],
            'output': [
                'resnet_v1_101_5/cls_score/BiasAdd:0',
                'resnet_v1_101_5/cls_prob:0',
                'add:0',
                'resnet_v1_101_3/rois/concat:0',
            ]
        }
    }
    ret = node0.create_model(
        labels=['exlabel1', 'exlabel1'],
        head_structure='rcnn',
        bone_structure='resnet',
        model_type='tensorflow.frozen',
        version='1',
        threshold=['0.6', '0.6'],
        mapping=['mplabel1', 'mplabel2'],
        extension=ext,
    )
    print(">>>> get model:", ret["msg"])
    print(node0.export_model_to_local(model_hash='b380861f4c4782b0fbd66eaf3ea46125-1', saved_path='/tmp/storage'))
    _u = "http://10.53.3.11:8080/file/"
    _m = "b380861f4c4782b0fbd66eaf3ea46125-1"
    print(node0.list_all_models())
    print(node0.update_model_configs(
        model_hash=_m,
        threshold=['0.7', '0.7'],
        mapping=['mappingA', 'mappingB'],
        extension=ext,
    ))
    print(node0.inspect_model(model_hash=_m))
    print(node0.delete_model(model_hash=_m))
    print(node0.list_all_models())
    print(node0.import_model_from_uri(model_hash=_m, uri=_u+_m+".tar.gz"))
    print(node0.inspect_model(model_hash="b380861f4c4782b0fbd66eaf3ea46125-1"))
    print(node0.update_model_configs_from_uri(model_hash=_m, uri=_u+_m+".json"))
    print(node0.inspect_model(model_hash=_m))
    print(node0.delete_model(model_hash=_m))

    print(node0.update_storage_path('replace_with_storage'))

    # public function
    mqtt_outlet = ligo.mosquitto_outlet()
    print(mqtt_outlet)

def _get_result(client, userdata, msg):
    print(msg.topic+": "+str(msg.payload, encoding=='utf-8'))

if __name__ == '__main__':
    print("Running Test:", __file__, "based on SDK:", ligo.__VERSION__)
    run()
