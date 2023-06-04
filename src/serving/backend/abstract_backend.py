"""
  Abstract Backend

  Contact: arthur.r.song@gmail.com
"""

import os
import abc
import sys
import json
import time
import uuid
import queue
import signal
import hashlib
import logging
import importlib
from enum import Enum, unique
from shutil import copyfile, rmtree
from multiprocessing import Process, Queue, Value

from serving.core import debug
from serving.core import model
from serving.core import config
from serving.core import runtime
from serving.core import sandbox
from serving.core import exception
from serving.core import regulator
from serving.core import scheduler
from serving.core.memory import FEATURE_GATE, IMAGES_POOL, PLUGIN, OUTLET_FACTORY


class AbstractBackend(metaclass=abc.ABCMeta):
    """Backend Abstract Class

    All specific Backend Class inherit from this abstract Class

    """
    def __init__(self, configurations):
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.configs = {
            'btype': configurations.get('btype'),
            'storage': configurations.get('storage'),
            'preheat': configurations.get('preheat'),
            'batchsize': configurations.get('batchsize'),
            'cpcount': configurations.get('cpcount'),

            'mhash': configurations.get('mhash'),
            'mcode': configurations.get('mcode'),
            'mpvtk': configurations.get('mpvtk'),
            'configs': configurations.get('configs'),

            'outlets': configurations.get('outlets'),
        }
        if self.configs.get('storage') is None:
            self.configs['storage'] = config.storage()
        if self.configs.get('preheat') is None:
            self.configs['preheat'] = config.preheat()
        self.backend_hash = AbstractBackend._gen_hash(self.configs)

        # initiate compute process objects
        self.cproc = [None] * self.configs['cpcount']
        self.cproc_sync_state = Value('B', Status.Unloaded.value)
        self.cproc_self_state = [Value('B', Status.Unloaded.value)] * self.configs['cpcount']

        # initiate model object
        split = self.configs['mhash'].split('-')
        self.model_configs = model._load_model_configs({'mhash': self.configs['mhash']})
        self.model_filepath = os.path.join(self.configs['storage'], "models", split[0], split[1])
        self.model_filename = "model_core"
        self.model_object = None
        self.model_predp = None
        self.model_postdp = None
        self.copy_folder = None

        # initiate outlet objects
        self.outlets = []
        for out in self.configs['outlets']:
            outlet_config = json.loads(out['configs'])
            if out['otype'] == "sync":
                outlet_config['queue'] = self.result_queue
            o = OUTLET_FACTORY[out['otype']].new_outlet(outlet_config)
            logging.debug("connected to outlet: %s", o)
            self.outlets.append(o)

    def hash(self):
        return self.backend_hash

    def report(self):
        compute_status = []
        for cs in self.cproc_self_state:
            compute_status.append(cs.value)
        return {
            'bhash': self.backend_hash,
            'btype': self.configs['btype'],
            'mhash': self.configs['mhash'],
            'mcode': self.configs['mcode'],
            'mpvtk': self.configs['mpvtk'],
            'storage': self.configs['storage'],
            'preheat': self.configs['preheat'],
            'batchsize': self.configs['batchsize'],
            'cpcount': self.configs['cpcount'],
            'outlets': self.configs['outlets'],
            'configs': self.configs['configs'],
            'persist': config.exist_persist_work(self.backend_hash),
            'cpstatus': compute_status,
        }

    @staticmethod
    def _gen_hash(configs):
        hash_string = "{}{}{}{}{}{}{}{}{}{}".format(
            configs['btype'],
            configs['mhash'],
            configs['mcode'],
            configs['mpvtk'],
            configs['storage'],
            configs['preheat'],
            configs['batchsize'],
            configs['cpcount'],
            configs['outlets'],
            configs['configs'],
        )
        return 'B'+hashlib.md5(hash_string.encode('utf-8')).hexdigest()

    @debug.flow("ab.run")
    @regulator.if_feature_on_run(FEATURE_GATE['on_authorized'], runtime.validate_device)
    def run(self):
        self.stop()
        # loading
        self.model_configs = model._load_model_configs({'mhash': self.configs['mhash']})
        # TODO: add test of multiple backend loaded with difference pre/post
        sys.path.append(self.model_filepath)
        self.model_predp = importlib.import_module('pre_dataprocess')
        self.model_predp = importlib.reload(self.model_predp)
        self.model_postdp = importlib.import_module('post_dataprocess')
        self.model_postdp = importlib.reload(self.model_postdp)
        sys.path.remove(self.model_filepath)
        # start compute process
        for i in range(self.configs['cpcount']):
            self.cproc[i] = Process(
                target=self._predict_loop,
                args=(i, self.cproc_sync_state, self.cproc_self_state[i], self.task_queue,))
            self.cproc[i].daemon = True
            self.cproc[i].start()
        self.cproc_sync_state.value = Status.Running.value
        return {'code': 0, 'msg': self.backend_hash}

    @debug.flow("ab._predict_loop")
    @regulator.if_feature_on_run(FEATURE_GATE['on_authorized'], runtime.validate_device)
    def _predict_loop(self, process_idx, sync_status, load_status, input_queue):
        try:
            # loading model object
            load_status.value = Status.Loading.value
            is_load_completed = False
            copy_folder_name = "process_{}".format(process_idx)
            self.copy_folder = os.path.join(self.model_filepath, copy_folder_name)
            os.mkdir(self.copy_folder)
            if FEATURE_GATE['on_sandbox'] and self.configs['mcode'] != "":
                sandbox.decode_model(
                    self.configs['mcode'], self.configs['mpvtk'],
                    self.model_filepath, self.model_filename, copy_folder_name + "/model_dore")
            else:
                copyfile(os.path.join(self.model_filepath, 'model_dore'),
                         os.path.join(self.copy_folder, 'model_dore'))
                logging.warning("loaded a model WITHOUT encryption")
            self.model_filename = "model_dore"
            try:
                # TODO(): still exist leaking risks
                is_loaded_param = self._load_model()
            finally:
                rmtree(self.copy_folder)


            if self.model_object is None:
                raise exception.ReloadModelOnBackendError()
            if not is_load_completed:
                self._load_parameter()
            # preheat
            if self.configs.get('preheat') is not None:
                load_status.value = Status.Preheating.value
                logging.debug("iproc-%d preheating", process_idx)
                img_uuid = str(uuid.uuid4())
                logging.debug("preheat image path: %s", self.configs['preheat'])
                ret = PLUGIN['reader'].read_image({'source': self.configs['preheat']})
                if ret is None:
                    raise exception.ReloadModelOnBackendError(": preheat image returns None")
                IMAGES_POOL[img_uuid] = PLUGIN['reader'].read_image({'source': self.configs['preheat']})
                preheat_task = scheduler.Task(task_id="preheat_{}".format(process_idx), image_id=img_uuid)
                self.infer_data([preheat_task], 1)
                logging.debug("iproc-%d preheated", process_idx)

            # predicting loop
            load_status.value = Status.Running.value
            while True:
                idx = -1
                task_list = [None] * self.configs['batchsize']
                while idx < self.configs['batchsize']-1:
                    try:
                        task = input_queue.get(timeout=0.5)
                        idx = idx + 1
                        task_list[idx] = task
                    except queue.Empty:
                        logging.debug("check status: %s", sync_status)
                        if sync_status.value == Status.Exited.value:
                            break
                        logging.debug("fetch timeout: %s, got %s", self.configs['batchsize'], idx+1)

                if sync_status.value == Status.Exited.value:
                    break
                idx = -1
                logging.debug("iproc-%d get %d task(s)", process_idx, self.configs['batchsize'])
                result_list = self.infer_data(task_list, self.configs['batchsize'])
                logging.debug("raw result: %s", result_list)
                for idx in range(self.configs['batchsize']):
                    self._finish_task(task_list[idx], result_list[idx])
            load_status.value = Status.Exited.value
        except Exception as err:
            # capture all possible exceptions
            logging.error(err)
            if config.debug_option():
                logging.exception(err)
            # handle RKNN failed
            if "RKNN_ERR_DEVICE_UNAVAILABLE" in repr(err):
                os.kill(runtime.MAIN_PROCESS_PID, signal.SIGTERM)
            # set backend with error status
            load_status.value = Status.Cleaning.value
            self.model_object = None
            if isinstance(err, ValueError):
                load_status.value = Status.Error_labels.value
            else:
                load_status.value = Status.Error.value

    @debug.flow("ab._finish_task")
    def _finish_task(self, task, result):
        logging.debug("prepare to send task(%s)'s result: %s", task, result)
        for o in self.outlets:
            o.post_result(task, json.dumps(result))

    @debug.flow("ab.stop")
    def stop(self):
        self.cproc_sync_state.value = Status.Exited.value
        time.sleep(2)  # wait for predicting while-loop exit
        for i in range(self.configs['cpcount']):
            if self.cproc[i] is not None:
                logging.debug("iproc-%s status: %s", i, self.cproc[i].is_alive())
                self.cproc[i].terminate()
                logging.debug("terminate iproc-%s", i)
        return {'code': 0, 'msg': self.backend_hash}

    @debug.flow("ab.enable_persist")
    def enable_persist(self):
        raise NotImplementedError()

    @debug.flow("ab.enable_persist")
    def disable_persist(self):
        raise NotImplementedError()

    # TODO: let task own a outlet_id
    @debug.flow("ab.enqueue_task")
    def enqueue_task(self, task):
        self.task_queue.put(task, block=False)

    @debug.flow("ab.dequeue_result")
    def dequeue_result(self):
        ret = self.result_queue.get()
        print(ret)
        return ret

    @debug.flow("ab.append_outlet")
    def append_outlet(self, configs):
        key = configs.get('key')
        if key is None:
            key = str(len(self.outlets))
        self.outlets[key] = configs['instance']
        if self.cproc_sync_state.value != Status.Unloaded.value:
            logging.warning("appended outlet will not be available until reload")
        return key

    @debug.flow("ab.list_outlet")
    def list_outlets(self):
        outlet_list = []
        for o in self.outlets:
            outlet_list.append(json.dumps({
                'key': o,
                'type': type(self.outlets[o]).__name__,
                'configs': str(self.outlets[o].configs),
            }))
        return outlet_list

    @debug.flow("ab.remove_outlet")
    def remove_outlet(self, key):
        del self.outlets[key]


    @abc.abstractmethod
    def _load_model(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _load_parameter(self):
        raise NotImplementedError()

    @debug.timeout(60)
    def infer_data(self, task_list, batchsize):
        return self._infer_data(task_list, batchsize)

    @abc.abstractmethod
    def _infer_data(self, task_list, batchsize):
        raise NotImplementedError()

@unique
class Status(Enum):
    """Backend Status Class
    """
    Unloaded = 0
    Cleaning = 1
    Loading = 2
    Preheating = 3
    Running = 4
    Exited = 5
    Error = 6
    Error_labels = 7
