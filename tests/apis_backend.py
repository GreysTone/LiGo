#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import urllib

# relocate package, when ligo_sdk is not installed
sys.path.append(os.path.dirname(__file__)+os.sep+'../')
print(sys.path)
import ligo

def run(_u, _m):
    node0 = ligo.LiGo()

    print(node0.ping())

    #_u = "http://10.53.3.11:8080/file/"
    #_m = "226a7354795692913f24bee21b0cd387-1"
    _code = None
    with urllib.request.urlopen(_u+_m+".code") as response:
        _code = str(response.read(), 'utf-8').strip()
    node0.update_storage_path("/tmp/storage")
    node0.update_preheat_image("/tmp/image")

    node0.import_model_from_uri(model_hash=_m, uri=_u+_m+".tar.gz")
    node0.update_model_configs_from_uri(model_hash=_m, uri=_u+_m+".json")

    out0 = ligo.mosquitto_outlet()
    ligo.receive_from_mosquitto(
        topic="example_topic",
        callback=_get_result,
        outlet=out0,
    )

    ret = node0.create_backend(
        ty="tensorflow",
        model_id=_m,
        password=_code,
        privatekey="/tmp/private.pem",
        outlet_list=[out0]
    )
    print("CREATE:", ret)
    bid = ret['msg']
    print(node0.list_all_backends())
    print(node0.inspect_backend(bid))
    #print("ENABLE:", node0.enable_backend(bid))
    #print(node0.list_all_configs())
    #print(node0.inspect_backend(bid))
    print("RUN:", node0.run_backend(bid))
    node0.async_compute_image(
        compute_id="example_topic",
        backend_id=ret['msg'],
        image_path="/tmp/image"
    )
    time.sleep(1)
    print("STOP:", node0.stop_backend(bid))
    print(node0.inspect_backend(bid))
    #print("DISABLE:", node0.disable_backend(bid))
    #print(node0.list_all_configs())
    #print(node0.inspect_backend(bid))
    print("DEL", node0.delete_backend(bid))
    print(node0.list_all_backends())


def _get_result(client, userdata, msg):
    print(msg.topic+": "+str(msg.payload))

if __name__ == '__main__':
    print("Running Test:", __file__, "based on SDK:", ligo.__VERSION__)
    run(sys.argv[1], sys.argv[2])
