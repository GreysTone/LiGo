import os
import sys
import logging
import importlib

from serving.core import debug
from serving.core import exception

DEPS = ['cv2']
for dep in DEPS:
    if importlib.util.find_spec(dep) is None:
        logging.error('failed to locate backend (%s) dependencies: %s', __name__, dep)
        raise exception.BackendDependencyError

from serving.core.memory import IMAGES_POOL, FEATURE_GATE
from serving.backend import abstract_backend as ab


def new_backend(configurations):
    return GenericBackend(configurations)

class GenericBackend(ab.AbstractBackend):
    def __init__(self, configurations={}):
        super().__init__(configurations)

    @debug.profiler("GenericBackend::_load_model")
    def _load_model(self):
        try:
            os.rename(os.path.join(self.copy_folder, self.model_filename),
                      os.path.join(self.copy_folder, self.model_filename + '.py'))
            sys.path.append(self.copy_folder)
            _module = importlib.import_module(self.model_filename)
            self.model_object = _module.Model()
            sys.path.remove(self.copy_folder)
            return True
        except Exception as err:
            raise exception.CreateAndLoadModelError()

    @debug.profiler("GenericBackend::_load_parameter")
    def _load_parameter(self):
        pass

    @debug.profiler("GenericBackend:_infer_data")
    def _infer_data(self, task_list, batchsize):
        if batchsize != 1:
            raise Exception("generic backend only supports batchsize as one")
        feed_lists, passby_lists = self.__buildBatch(task_list, batchsize)
        infer_lists = self.__inferBatch(feed_lists, passby_lists)
        result_lists = self.__processBatch(infer_lists, passby_lists, batchsize)
        logging.debug("raw result: %s", result_lists)
        return result_lists

    @debug.profiler("GenericBackend::__buildBatch")
    def __buildBatch(self, task_list, batchsize):
        predp_data = [None] * batchsize
        feed_lists = [None] * batchsize
        passby_lists = [None] * batchsize
        for i in range(batchsize):
            image_frame = IMAGES_POOL[task_list[i].image_id]
            extra_info = task_list[i].extra
            del IMAGES_POOL[task_list[i].image_id]
            predp_data[i] = self.model_predp.pre_dataprocess({'img': image_frame, 'extra': extra_info})
            feed_lists[i] = predp_data[i]['feed_list']
            passby_lists[i] = predp_data[i]['passby']
        return feed_lists, passby_lists

    @debug.profiler("GenericBackend::__inferBatch")
    def __inferBatch(self, feed_lists, passby_lists):
        return [self.model_object.compute(feed_lists, passby_lists)]

    @debug.profiler("GenericBackend::__ProcessBatch")
    def __processBatch(self, infer_lists, passby_lists, batchsize):
        result_lists = [None] * batchsize
        for i in range(batchsize):
            result_lists[i] = self.model_postdp.post_dataprocess({
                'infers': infer_lists[i],
                'passby': passby_lists[i],
            })
        return result_lists