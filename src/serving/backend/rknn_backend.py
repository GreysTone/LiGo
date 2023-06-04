"""
  LiGo RKNN Backend

  Contact: arthur.r.song@gmail.com
"""

import os
import json
import logging
import importlib

from serving.core import debug
from serving.core import exception

DEPS = ['rknn']
for dep in DEPS:
    if importlib.util.find_spec(dep) is None:
        logging.error('failed to locate backend (%s) dependencies: %s', __name__, dep)
        raise exception.BackendDependencyError

from rknn.api import RKNN

from serving.core.memory import IMAGES_POOL
from serving.backend import abstract_backend as ab

def new_backend(configurations):
    return RKNNPyBackend(configurations)

class RKNNPyBackend(ab.AbstractBackend):
    def __del__(self):
        if self.model_object is not None:
            self.model_object.release()

    @debug.profiler("RKNNPyBackend::_load_model")
    def _load_model(self):
        self.model_object = RKNN()
        path = os.path.join(self.copy_folder, self.model_filename)
        with open(path, "rb") as _model_check:
            check_str = _model_check.read(100)
            if "VPMN" not in str(check_str):
                logging.warning("A non-precompiled model is given, loading will take long time")
            logging.debug("VPMN signature is detected in the given model")
        self.model_object.load_rknn(path)
        ret = self.model_object.init_runtime()
        if ret != 0:
            raise RuntimeError("Failed to initialize RKNN runtime enrvironment")
        return True

    @debug.profiler("RKNNPyBackend::_load_parameter")
    def _load_parameter(self):
        pass

    @debug.profiler("RKNNPyBackend::_infer_data")
    def _infer_data(self, task_list, batchsize):
        if batchsize != 1:
            raise Exception("currently not support rknn batchsize mode")
        feed_lists, passby_lists = self.__buildBatch(task_list, batchsize)
        infer_lists = self.__inferBatch(feed_lists)
        result_lists = self.__processBatch(infer_lists, passby_lists, batchsize)
        logging.debug("raw result: %s", result_lists)
        return result_lists

    @debug.profiler("RKNNPyBackend::__buildBatch")
    def __buildBatch(self, task_list, batchsize):
        predp_data = [None] * batchsize
        feed_lists = [None] * batchsize
        passby_lists = [None] * batchsize
        for i in range(batchsize):
            image_frame = IMAGES_POOL[task_list[i].image_id]
            del IMAGES_POOL[task_list[i].image_id]
            predp_data[i] = self.model_predp.pre_dataprocess({'img': image_frame})
            feed_lists[i] = predp_data[i]['feed_list']
            passby_lists[i] = predp_data[i]['passby']
        return feed_lists, passby_lists

    @debug.profiler("RKNNPyBackend::__inferBatch")
    def __inferBatch(self, feed_lists):
        return [self.model_object.inference(feed_lists[0])]

    @debug.profiler("RKNNPyBackend::__processBatch")
    def __processBatch(self, infer_lists, passby_lists, batchsize):
        labels = self.model_configs.get('labels')
        threshold = [float(i) for i in self.model_configs.get('threshold')]
        mapping = self.model_configs.get('mapping')
        result_lists = [None] * batchsize
        for i in range(batchsize):
            result_lists[i] = self.model_postdp.post_dataprocess({
                'infers': infer_lists[i],
                'labels': labels,
                'threshold': threshold,
                'mapping': mapping,
                'passby': passby_lists[i],
            })
        return result_lists
