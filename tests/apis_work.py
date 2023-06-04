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

def run():
    node0 = ligo.LiGo()

    print(node0.ping())

    _u = "http://-:8080/file/"
    _m = "-"
    _code = None
    with urllib.request.urlopen(_u+_m+".code") as response:
        _code = str(response.read(), 'utf-8').strip()
    node0.update_storage_path("/tmp/storage")
    node0.update_preheat_image("/tmp/image")

    node0.import_model_from_uri(model_hash=_m, uri=_u+_m+".tar.gz")
    node0.update_model_configs_from_url(model_hash=_m, url=_u+_m+".json")

    outlet_config = ligo.get_mqtt_outlet()

    ret, bid = node0.create_and_load_encrypted_model(
        ty="tensorflow.frozen",
        backend_extension="",
        model_hash=_m,
        outlets=[outlet_config],
        password=_code,
        privatekey="/tmp/private.pem",
    )
    if ret == False:
        raise RuntimeError("failed to load model")

    sw0 = ligo.new_stream_work(
        address="rtsp://-:554/mpeg4/ch1/sub",
        backend_id='0',
        outlet_id='0',
    )
    print(sw0)
    ret = node0.create_work(sw0)
    print("create:", ret)
    wid = ret['msg']

    ligo.set_callback_for_mqtt(
        topic=wid,
        on_message_callback=_get_result,
        mqtt_outlet=outlet_config
    )

    print(node0.list_all_works())
    print(node0.inspect_work(wid))
    print("enable:", node0.enable_work(wid))
    print(node0.list_all_configs())
    print(node0.inspect_work(wid))
    print("run:", node0.run_work(wid))
    print(node0.inspect_work(wid))
    time.sleep(10)
    print("stop:", node0.stop_work(wid))
    print(node0.inspect_work(wid))
    print("disable:", node0.disable_work(wid))
    print(node0.list_all_configs())
    print(node0.inspect_work(wid))
    print("delete", node0.delete_work(wid))
    print(node0.list_all_works())

    print(node0.terminate_backend(bid))


def _get_result(client, userdata, msg):
    print(msg.topic+": "+str(msg.payload))

if __name__ == '__main__':
    print("Running Test:", __file__, "based on SDK:", ligo.__VERSION__)
    run()
