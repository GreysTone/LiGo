import os
import logging
import importlib

from serving.core import debug
from serving.core import exception

DEPS = ['hiai']
for dep in DEPS:
    if importlib.util.find_spec(dep) is None:
        logging.error('failed to locate backend (%s) dependencies: %s', __name__, dep)
        raise exception.BackendDependencyError

import hiai

from serving.core.memory import IMAGES_POOL, FEATURE_GATE
from serving.backend import abstract_backend as ab


def new_backend(configurations):
    return AtlasBackend(configurations)

class AtlasBackend(ab.AbstractBackend):
    def __init__(self, configurations={}):
        super().__init__(configurations)
        self.graph_id = 1000
        self.model_engine_id = 100

    def __del__(self):
        if self.model_object is not None:
            self.model_object.destroy()

    @debug.profiler("AtlasBackend::_load_model")
    def _load_model(self):
        try:
            path = os.path.join(self.copy_folder, self.model_filename)
            inferenceModel = hiai.AIModelDescription('YoloV3', path)
            graph = hiai.Graph(hiai.GraphConfig(graph_id = self.graph_id))
            if graph is None:
                raise RuntimeError("Failed to initialize atlas model graph")
            with graph.as_default():
                model_engine = hiai.Engine(hiai.EngineConfig(engine_name='ModelInferenceEngine', side=hiai.HiaiPythonSide.Device, internal_so_name='/lib64/libhiai_python_device.so', engine_id=self.model_engine_id))
                if model_engine is None:
                    raise RuntimeError("Failed to get atlas model engine")
            with model_engine.as_default():
                if (None == model_engine.inference(input_tensor_list=hiai.NNTensorList(), ai_model=inferenceModel)):
                    raise RuntimeError("Failed to initialize atlas model engine")
            if hiai.HiaiPythonStatust.HIAI_PYTHON_OK == graph.create_graph():
                self.model_object = graph
            else:
                raise RuntimeError("Failed to create atlas model graph")
            return True
        except Exception as err:
            raise exception.CreateAndLoadModelError()

    @debug.profiler("AtlasBackend::_load_parameter")
    def _load_parameter(self):
        pass

    @debug.profiler("AtlasBackend:_infer_data")
    def _infer_data(self, task_list, batchsize):
        if batchsize != 1:
            raise Exception("generic backend only supports batchsize as one")
        feed_lists, passby_lists = self.__buildBatch(task_list, batchsize)
        infer_lists = self.__inferBatch(feed_lists, passby_lists)
        result_lists = self.__processBatch(infer_lists, passby_lists, batchsize)
        logging.debug("raw result: %s", result_lists)
        return result_lists

    @debug.profiler("AtlasBackend::__buildBatch")
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

    @debug.profiler("AtlasBackend::__inferBatch")
    def __inferBatch(self, feed_lists, passby_lists):
        results = []
        for feed_instance in feed_lists:
            input_tensor = hiai.NNTensor(feed_instance)
            nntensor_list = hiai.NNTensorList(input_tensor)
            result = self.model_object.proc(nntensor_list)
            results.append(result)
        return results

    @debug.profiler("AtlasBackend::__ProcessBatch")
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