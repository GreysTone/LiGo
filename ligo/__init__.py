"""
  Trueno SDK

  Contact: arthur.r.song@gmail.com
"""

import os
import json
import time
import uuid
import base64
import logging

import cv2
import grpc
import redis
import paho.mqtt.client as mqtt
from google.protobuf.json_format import ParseDict, MessageToDict

from trueno.interface import common_pb2
from trueno.interface import backend_pb2
from trueno.interface import backend_pb2_grpc
from trueno.interface import connectivity_pb2
from trueno.interface import connectivity_pb2_grpc
from trueno.interface import model_pb2
from trueno.interface import model_pb2_grpc
from trueno.interface import exchange_pb2
from trueno.interface import exchange_pb2_grpc
from trueno.interface import inference_pb2
from trueno.interface import inference_pb2_grpc

__VERSION__ = "Not Available"
logging.getLogger('').setLevel(logging.DEBUG)
logging.debug("SDK located at: %s", os.path.dirname(__file__))

class Trueno():
    def __init__(self, sock="localhost:50051"):
        self.channel = grpc.insecure_channel(sock)
        self.backend = backend_pb2_grpc.BackendServiceStub(self.channel)
        self.connect = connectivity_pb2_grpc.ConnectivityStub(self.channel)
        self.model = model_pb2_grpc.ModelServiceStub(self.channel)
        self.exchange = exchange_pb2_grpc.ExchangeStub(self.channel)
        self.inference = inference_pb2_grpc.InferenceStub(self.channel)

    @staticmethod
    def _client_signature():
        return "Trueno SDK: "+__VERSION__

    def list_supported_backend_type(self):
        return MessageToDict(self.backend.ListSupportedType(
            common_pb2.PingRequest(client=Trueno._client_signature())))

    def create_backend(self, ty,
        model_id, password="", privatekey="",
        storage_path=None, preheat_path=None, batchsize=1, compute_process_num=1, outlet_list=[], configs=None):
        pass_in = {
            'btype': ty,
            'mhash': model_id,
            'mcode': password,
            'mpvtk': privatekey,
            'storage': storage_path,
            'preheat': preheat_path,
            'batchsize': batchsize,
            'cpcount': compute_process_num,
            'outlets': outlet_list,
            'configs': configs
        }
        return MessageToDict(self.backend.CreateBackend(
            ParseDict(pass_in, backend_pb2.Backend())))

    def delete_backend(self, backend_id):
        return MessageToDict(self.backend.DeleteBackend(
            backend_pb2.Backend(bhash=backend_id)))

    def list_all_backends(self):
        return MessageToDict(self.backend.ListAllBackends(
            common_pb2.PingRequest(client=Trueno._client_signature())))

    def inspect_backend(self, backend_id):
        return MessageToDict(self.backend.InspectBackend(
            backend_pb2.Backend(bhash=backend_id)))

    def enable_backend(self, backend_id):
        return MessageToDict(self.backend.EnableBackend(
            backend_pb2.Backend(bhash=backend_id)))

    def disable_backend(self, backend_id):
        return MessageToDict(self.backend.DisableBackend(
            backend_pb2.Backend(bhash=backend_id)))

    def run_backend(self, backend_id):
        ret = self.backend.RunModelOnBackend(
            backend_pb2.Backend(bhash=backend_id))
        if ret.code != 0:
            return False, -1
        logging.info("trueno prepair to run model on backend: %s", ret.msg)
        status = -1
        response = None
        while status < 4:
            time.sleep(3)
            response = self.inspect_backend(backend_id=ret.msg)
            status = response['cpstatus'][-1]
            logging.debug("cpstatus: %s", status)
        if status > 4:
            logging.error("failed to run_backend, %s", response['cpstatus'])
            logging.info("try to terminate created backend...")
            self.stop_backend(backend_id=ret.msg)
            logging.info("created backend terminated")
            return False, -1
        return True, ret.msg

    def stop_backend(self, backend_id):
        return MessageToDict(self.backend.StopModelOnBackend(
            backend_pb2.Backend(bhash=backend_id)))

    def list_backend_outlet(self, backend_id):
        pass_in = {'bid': backend_id}
        return MessageToDict(self.backend.ListOutlets(ParseDict(pass_in, backend_pb2.Outlet())))

    def append_outlet_to_backend(self, backend_id, key, outlet):
        pass_in = {
            'bid': backend_id,
            'key': key,
            'type': outlet['type'],
            'configs': outlet['configs']
        }
        return MessageToDict(self.backend.AppendOutlet(ParseDict(pass_in, backend_pb2.Outlet())))

    def remove_outlet_from_backend(self, backend_id, key):
        pass_in = {
            'bid': backend_id,
            'key': key,
        }
        return MessageToDict(self.backend.RemoveOutlet(ParseDict(pass_in, backend_pb2.Outlet())))

    """
    def reload_decrypted_model(self, backend_id, model_hash):
        return MessageToDict(self._reload_model_on_backend(backend_id, model_hash, 0, "", ""))

    def reload_encrypted_model(self, backend_id, model_hash, password, privatekey):
        return MessageToDict(self._reload_model_on_backend(backend_id, model_hash, 1, password, privatekey))

    def _reload_model_on_backend(self, backend_id, implhash, encrypted, a64key, pvtkey):
        pass_in = {
            'bid': backend_id,
            'model': {'implhash': implhash},
            'encrypted': encrypted,
            'a64key': a64key,
            'pvtkey': pvtkey,
        }
        ret = self.backend.RunModelOnBackend(ParseDict(pass_in, backend_pb2.Backend()))
        if ret.code != 0:
            return ret
        status = -1
        response = None
        while status < 4:
            time.sleep(3)
            response = self.inspect_backend(backend_id=ret.msg)
            status = response['pstatus'][-1]
        if status > 4:
            logging.error("failed to load model on backend, %s", response['pstatus'])
        return MessageToDict(ret)
    """

    def create_and_load_decrypted_model(self, ty, model_extension, model_hash, outlets):
        return self._create_and_load_model(ty, model_extension, model_hash, outlets, 0, "", "")

    def create_and_load_encrypted_model(self, ty, model_extension, model_hash, outlets, password, privatekey):
        return self._create_and_load_model(ty, model_extension, model_hash, outlets, 1, password, privatekey)

    def _create_and_load_model(self, ty, modelext, implhash, outlet_list, encrypted, a64key, pvtkey):
        pass_in = {
            'backend': {'btype': ty},
            'model': {'mhash': implhash, 'modelext': modelext},
            'outlets': outlet_list,
            'encrypted': encrypted,
            'a64key': a64key,
            'pvtkey': pvtkey,
        }
        ret = self.backend.CreateAndLoadModel(ParseDict(pass_in, backend_pb2.FullLoadRequest()))
        if ret.code != 0:
            return False, -1
        logging.info("trueno prepair to load model on bid: %s", ret.msg)
        status = -1
        response = None
        while status < 4:
            time.sleep(3)
            response = self.inspect_backend(backend_id=ret.msg)
            status = response['pstatus'][-1]
        if status > 4:
            logging.error("failed to create_and_load_backend, %s", response['pstatus'])
            logging.info("try to terminate created backend...")
            self.stop_backend(backend_id=ret.msg)
            logging.info("created backend terminated")
            return False, -1
        return True, ret.msg

    def ping(self):
        return MessageToDict(self.connect.Ping(common_pb2.PingRequest(client=Trueno._client_signature())))

    def list_node_resources(self):
        return MessageToDict(self.connect.ListNodeResources(common_pb2.PingRequest(client=Trueno._client_signature())))

    def list_all_configs(self):
        return MessageToDict(self.connect.ListConfigs(common_pb2.PingRequest(client=Trueno._client_signature())))

    def update_storage_path(self, path):
        return MessageToDict(self._update_config('backend.storage', path))

    def update_preheat_image(self, path):
        return MessageToDict(self._update_config('backend.preheat', path))

    def _update_config(self, key, val):
        return self.connect.UpdateConfig(connectivity_pb2.Config(key=key, val=val))

    def create_work(self, configs):
        print(configs)
        pass_in = {
            'wtype': configs['wtype'],
            'configs': configs['configs'],
            'link': {
                'bid': configs['bid'],
                'outlet': configs['oid'],
            }
        }
        return MessageToDict(self.connect.CreateWork(ParseDict(pass_in, connectivity_pb2.Work())))

    def delete_work(self, work_id):
        pass_in = {'whash': work_id}
        return MessageToDict(self.connect.DeleteWork(ParseDict(pass_in, connectivity_pb2.Work())))
    
    def list_all_works(self):
        return MessageToDict(self.connect.ListAllWorks(common_pb2.PingRequest(client=Trueno._client_signature())))

    def inspect_work(self, work_id):
        pass_in = {'whash': work_id}
        return MessageToDict(self.connect.InspectWork(ParseDict(pass_in, connectivity_pb2.Work())))

    def enable_work(self, work_id):
        pass_in = {'whash': work_id}
        return MessageToDict(self.connect.EnableWork(ParseDict(pass_in, connectivity_pb2.Work())))

    def disable_work(self, work_id):
        pass_in = {'whash': work_id}
        return MessageToDict(self.connect.DisableWork(ParseDict(pass_in, connectivity_pb2.Work())))

    def run_work(self, work_id):
        pass_in = {'whash': work_id}
        return MessageToDict(self.connect.RunWork(ParseDict(pass_in, connectivity_pb2.Work())))

    def stop_work(self, work_id):
        pass_in = {'whash': work_id}
        return MessageToDict(self.connect.StopWork(ParseDict(pass_in, connectivity_pb2.Work())))

    # ModelService
    def create_model(self, labels, head_structure, bone_structure, model_type, version,
            threshold, mapping, extension):
        pass_in = {
            'labels': labels,
            'head': head_structure,
            'bone': bone_structure,
            'impl': model_type,
            'version': version,
            'threshold': threshold,
            'mapping': mapping,
            'modelext': json.dumps(extension),
        }
        return MessageToDict(self.model.CreateModel(ParseDict(pass_in, model_pb2.Model())))

    def delete_model(self, model_hash):
        return MessageToDict(self.model.DeleteModel(
            model_pb2.Model(mhash= model_hash)))

    def list_all_models(self):
        return MessageToDict(self.model.ListAllModels(
            common_pb2.PingRequest(client=Trueno._client_signature())))

    def inspect_model(self, model_hash):
        return MessageToDict(self.model.InspectModel(
            model_pb2.Model(mhash= model_hash)))

    def update_model_configs(self, model_hash, threshold=None, mapping=None, extension=None):
        pass_in = {
            'mhash': model_hash,
            'threshold': threshold,
            'mapping': mapping,
        }
        if isinstance(extension, dict):
            pass_in['modelext'] = json.dumps(extension)
        else:
            pass_in['modelext'] = extension
        return MessageToDict(self.model.UpdateModelConfigs(ParseDict(pass_in, model_pb2.Model())))

    def update_model_configs_from_uri(self, model_hash, uri):
        return MessageToDict(self.model.UpdateModelConfigsFromURI(
            model_pb2.Model(mhash=model_hash, bundle=uri)))

    def import_model_from_local(self, model_hash, local_path):
        bin_name = self._upload_file(model_hash+".tar.gz", local_path)
        logging.debug(">>> %s", bin_name)
        return MessageToDict(self.model.ImportModelFromLocal(
            model_pb2.Model(mhash=model_hash, bundle=bin_name)))

    def import_model_from_uri(self, model_hash, uri):
        return MessageToDict(self.model.ImportModelFromURI(
            model_pb2.Model(mhash=model_hash, bundle=uri)))

    def export_model_to_local(self, model_hash, saved_path):
        ret = self.model.ExportModelToLocal(model_pb2.Model(mhash=model_hash))
        if ret.code != 0:
            return MessageToDict(ret)
        self._download_file(model_hash+".tar.gz", saved_path)
        return MessageToDict(ret)

    def _download_file(self, target_file, local_path):
        response = self.exchange.DownloadBin(
            Trueno._bin_request([exchange_pb2.BinData(uuid=target_file)]))
        bin_blob = []
        for r in response:
            bin_blob.append(r.pack.block)
        target = os.path.join(local_path, target_file)
        with open(target, "ab") as dump:
            for b in bin_blob:
                dump.write(b)

    def _upload_file(self, local_file, local_path):
        bin_blob = []
        chunk_size = 2 * 1024 * 1024
        target_file = os.path.join(local_path, local_file)
        with open(target_file, "rb") as f:
            blob = f.read(chunk_size)
            while blob != b"":
                bin_blob.append(blob)
                blob = f.read(chunk_size)
        responses = self.exchange.UploadBin(
            Trueno._bin_response(bin_blob))
        bin_name = None
        for r in responses:
            bin_name = r.uuid
        return bin_name

    @staticmethod
    def _bin_request(bin_list):
        for b in bin_list:
            yield b

    @staticmethod
    def _bin_response(bin_list):
        for i in range(len(bin_list)):
            yield exchange_pb2.BinData(
                pack=exchange_pb2.Block(
                    index=i,
                    block=bin_list[i],
                )
            )

    def async_compute_image(self, compute_id, backend_id, image_path, extra_data=None):
        data = b''
        with open(image_path, "rb") as image:
            data = image.read()
        return MessageToDict(self._compute_image(compute_id, backend_id, data, extra_data, 0))

    def _compute_image(self, compute_id, backend_id, data, extra, dtype):
        return self.inference.InferenceRemote(inference_pb2.InferRequest(
            bid=backend_id,
            uuid=compute_id,
            outlet='0',
            data=data, #base64.b64encode(image_obj)
            extra=extra,
            dtype=dtype,
        ))

def mosquitto_outlet(host="127.0.0.1", port=1883, qos=0, key_as_topic=True, topic=None, keep_alive=60):
    return {
        'otype': 'mosquitto',
        'configs': json.dumps({
            'host': host,
            'port': port,
            'qos': qos,
            'key_as_topic': key_as_topic,
            'topic': topic,
            'keepalive': keep_alive,
        })
    }

def new_stream_work(address, backend_id="", outlet_id=""):
    return {
        'wtype': 'stream-work',
        'bid': backend_id,
        'oid': outlet_id,
        'configs': json.dumps({
            'address': address,
        })
    }

# TODO: rename this
def receive_from_mosquitto(topic, callback, outlet):
    client = mqtt.Client('')
    client.on_message = callback
    configs = json.loads(outlet['configs'])
    client.connect(configs['host'], configs['port'], configs['keepalive'])
    client.subscribe(topic, configs['qos'])
    client.loop_start()
    time.sleep(1)

def get_redis_instance(host="localhost", port=6379, db=5):
    pool = redis.ConnectionPool(host=host, port=port, db=db)
    return redis.Redis(host, port, connection_pool=pool)
