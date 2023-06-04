"""
  LiGo Tensorflow Python Backend

  Contact: arthur.r.song@gmail.com
"""

import os
import json
import logging
import importlib
from enum import Enum, unique

from serving.core import debug
from serving.core import exception

DEPS = ['tensorflow', 'numpy']
for dep in DEPS:
    if importlib.util.find_spec(dep) is None:
        logging.error('failed to locate backend (%s) dependencies: %s', __name__, dep)
        raise exception.BackendDependencyError

import tensorflow as tf
import numpy as np

from serving.core.memory import IMAGES_POOL, FEATURE_GATE
from serving.backend import abstract_backend as ab


def new_backend(configurations):
    return TfPyBackend(configurations)

class TfPyBackend(ab.AbstractBackend):
    def __init__(self, configurations={}):
        super().__init__(configurations)
        self.input_tensor_vec = []
        self.output_tensor_vec = []

    @debug.profiler("TfPyBackend::_loadModel")
    def _load_model(self):
        try:
            # load tensorflow session
            model_type = self.model_configs['impl'].split('.')[1]
            if model_type == 'frozen':
                self.__loadFrozenModel()
            if model_type == 'unfrozen':
                self.__loadUnfrozenModel()
            # set input/output tensor
            logging.debug("load model extention: %s", self.model_configs['modelext'])
            tensor_map = json.loads(self.model_configs['modelext']).get('tensors')
            self.input_tensor_vec = []
            for it in tensor_map['input']:
                self.input_tensor_vec.append(self.model_object.graph.get_tensor_by_name(it))
            self.output_tensor_vec = []
            for it in tensor_map['output']:
                self.output_tensor_vec.append(self.model_object.graph.get_tensor_by_name(it))
            return True
        except Exception as err:
            self.output_tensor_vec = []
            self.input_tensor_vec = []
            raise err

    @debug.profiler("TfPyBackend::__loadFrozenModel")
    def __loadFrozenModel(self):
        with tf.Graph().as_default():
            graph_def = tf.GraphDef()
            path = os.path.join(self.copy_folder, self.model_filename)
            with open(path, "rb") as model_file:
                graph_def.ParseFromString(model_file.read())
                tf.import_graph_def(graph_def, name="")
            config = tf.ConfigProto()
            if FEATURE_GATE['on_tensorflow_gpu_3splits']:
                config.gpu_options.allow_growth=True
                config.gpu_options.per_process_gpu_memory_fraction = (1-0.01)/3
            self.model_object = tf.Session(config=config)
            self.model_object.run(tf.global_variables_initializer())

    @debug.profiler("TfPyBackend::__loadUnfrozenModel")
    def __loadUnfrozenModel(self):
        os.rename(os.path.join(self.copy_folder, self.model_filename),
                  os.path.join(self.copy_folder, "saved_model.pb"))
        config = tf.ConfigProto()
        if FEATURE_GATE['on_tensorflow_gpu_3splits']:
            config.gpu_options.allow_growth=True
            config.gpu_options.per_process_gpu_memory_fraction = (1-0.01)/3
        self.model_object = tf.Session(graph=tf.Graph(), config=config)
        tf.saved_model.loader.load(
            self.model_object,
            [tf.saved_model.tag_constants.SERVING],
            self.copy_folder)

    def _load_parameter(self):
        pass

    @debug.flow("@abs::ab._infer_data")
    @debug.profiler("TfPyBackend::_infer_data")
    def _infer_data(self, task_list, batchsize):
        if batchsize < 1:
            raise Exception("batchsize smaller than one")
        feed_lists, passby_lists = self.__buildBatch(task_list, batchsize)
        infer_lists = self.__inferBatch(feed_lists)
        result_lists = self.__processBatch(infer_lists, passby_lists, batchsize)
        logging.debug("raw result: %s", result_lists)
        return result_lists

    @debug.profiler("TfPyBackend::__buildBatch")
    def __buildBatch(self, task_list, batchsize):
        predp_data = [None] * batchsize
        #id_lists = [None] * batchsize
        feed_lists = np.array([[None] * batchsize] * len(self.input_tensor_vec))
        passby_lists = [None] * batchsize
        input_type = json.loads(self.model_configs['modelext']).get('tensors')['input_type']

        for i in range(batchsize):
            image_frame = IMAGES_POOL[task_list[i].image_id]
            del IMAGES_POOL[task_list[i].image_id]
            predp_data[i] = self.model_predp.pre_dataprocess({'img': image_frame})
            passby_lists[i] = predp_data[i]['passby']
            for j in range(len(self.input_tensor_vec)):
                feed_lists[j][i] = np.squeeze(predp_data[i]['feed_list'][j])

        feed_lists_return = []
        for i in range(len(self.input_tensor_vec)):
            if int(input_type[i]) == 1:
                feed_lists_return.append(np.array(feed_lists[i].tolist()))
            if int(input_type[i]) == 0:
                feed_lists_return.append(feed_lists[i][0])

        return feed_lists_return, passby_lists

    @debug.profiler("TfPyBackend::__inferBatch")
    def __inferBatch(self, feed_list):
        feeding = {}
        for index, t in enumerate(self.input_tensor_vec):
            feeding[t] = feed_list[index]
        return self.model_object.run(self.output_tensor_vec, feed_dict=feeding)


    @debug.profiler("TfPyBackend::__processBatch")
    def __processBatch(self, infer_lists, passby_lists, batchsize):
        labels = self.model_configs.get('labels')
        threshold = [float(i) for i in self.model_configs.get('threshold')]
        mapping = self.model_configs.get('mapping')
        result_lists = [None] * batchsize

        for i in range(batchsize):
            post_frame = {
                'infers': [infer_lists[k][i] for k in range(len(infer_lists))],
                'labels': labels,
                'threshold': threshold,
                'mapping': mapping,
                'passby': passby_lists[i]
            }
            result_lists[i] = self.model_postdp.post_dataprocess(post_frame)

        return result_lists
