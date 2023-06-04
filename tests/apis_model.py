#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

# relocate package, when ligo_sdk is not installed
sys.path.append(os.path.dirname(__file__)+os.sep+'../')
print(sys.path)
import ligo

def run():
    node0 = ligo.Trueno()
    print(node0.ping())
    print(node0.update_storage_path('/tmp/storage'))

    ret = node0.create_model(
        labels=['exlabel1', 'exlabel1'],
        head_structure='head',
        bone_structure='bone',
        model_type='tensorflow.frozen',
        version='1',
        threshold=['0.6', '0.6'],
        mapping=['mplabel1', 'mplabel2'],
        extension={'name': 'example_model'},
    )
    print("CRATE:", ret)
    print("INSP:", node0.inspect_model(model_hash=ret['msg']))
    print("LIST ALL:", node0.list_all_models())

    print("EXPORT:", node0.export_model_to_local(model_hash=ret['msg'], saved_path="."))
    print("DEL:", node0.delete_model(model_hash=ret['msg']))
    print("LIST ALL:", node0.list_all_models())
    print("IMPORT:", node0.import_model_from_local(model_hash=ret['msg'], local_path="."))
    print("INSP:", node0.inspect_model(model_hash=ret['msg']))
    print("UPDATE:", node0.update_model_configs(
        model_hash=ret['msg'],
        threshold=['0.9', '0.9'],
        mapping=['mappingA', 'mappingB'],
        extension={'name': 'another_model_name'},
    ))
    print("INSP:", node0.inspect_model(model_hash=ret['msg']))
    print("DEL:", node0.delete_model(model_hash=ret['msg']))
    print("LIST ALL:", node0.list_all_models())

    _u = "http://10.53.3.11:8080/file/"
    _m = "226a7354795692913f24bee21b0cd387-1"
    #print("EXPORT:", node0.export_model_to_local(model_hash=_m, saved_path="."))
    print("IMPORT URI:", node0.import_model_from_uri(model_hash=_m, uri=_u+_m+".tar.gz"))
    print("INSP:", node0.inspect_model(model_hash=_m))
    print("UPDATE URI:", node0.update_model_configs_from_uri(model_hash=_m, uri=_u+_m+".json"))
    print("INSP:", node0.inspect_model(model_hash=_m))
    print("DEL:", node0.delete_model(model_hash=_m))

    print(node0.update_storage_path('replace_with_storage'))

def _get_result(client, userdata, msg):
    print(msg.topic+": "+str(msg.payload))

if __name__ == '__main__':
    print("Running Test:", __file__, "based on SDK:", ligo.__VERSION__)
    run()
