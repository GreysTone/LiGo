import os
import logging
import importlib

from serving.core import debug
from serving.core import exception

DEPS = ['acl', 'numpy', 'struct', 'cv2']
for dep in DEPS:
    if importlib.util.find_spec(dep) is None:
        logging.error('failed to locate backend (%s) dependencies: %s', __name__, dep)
        raise exception.BackendDependencyError

import acl
import cv2
import numpy as np

from serving.backend.atlas2_acl import *
from serving.core.memory import IMAGES_POOL
from serving.backend import abstract_backend as ab


def new_backend(configurations):
    return Atlas2Backend(configurations)

class Atlas2Backend(ab.AbstractBackend):
    def __init__(self, configurations={}):
        super().__init__(configurations)
        self.device_id = 0
        self.context = None
        self.stream = None
        self._image_info_size = None
        self.model_object = None
        self.run_mode = None
        self._model_width = 416
        self._model_height = 416
        self._dvpp = None
        self._image_info_dev = None

    def __del__(self):
        if self.model_object is not None:
            del self.model_object
        if self._dvpp:
            del self._dvpp
        if self.stream:
            acl.rt.destroy_stream(self.stream)
        if self.context:
            acl.rt.destroy_context(self.context)
        acl.rt.reset_device(self.device_id)
        acl.finalize()

    @debug.profiler("Atlas2Backend::_load_model")
    def _load_model(self):
        try:
            # model path
            path = os.path.join(self.copy_folder, self.model_filename)
            # init acl resource
            self._init_acl_resource()
            # load model
            self.model_object = AclModel(self.run_mode, path)
            ret = self.model_object.init_resource()
            check_ret("Acl model init", ret)
        except Exception as err:
            raise exception.CreateAndLoadModelError()

    @debug.profiler("AtlasBackend::_init_acl_resource")
    def _init_acl_resource(self):
        # acl resource
        ret = acl.init()
        check_ret("acl.init", ret)
        ret = acl.rt.set_device(self.device_id)
        check_ret("acl.rt.set_device", ret)
        self.context, ret = acl.rt.create_context(self.device_id)
        check_ret("acl.rt.create_context", ret)
        self.stream, ret = acl.rt.create_stream()
        check_ret("acl.rt.create_stream", ret)
        self.run_mode, ret = acl.rt.get_run_mode()
        check_ret("acl.rt.get_run_mode", ret)
        self._dvpp = AclDvpp(self.stream, self.run_mode)
        ret = self._dvpp.init_resource()
        check_ret("acl.dvpp.init_resource", ret)

        # acl image info
        image_info = np.array([self._model_width, self._model_height,
                               self._model_width, self._model_height],
                              dtype=np.float32)
        ptr = acl.util.numpy_to_ptr(image_info)
        self._image_info_size = image_info.itemsize * image_info.size
        self._image_info_dev = copy_data_device_to_device(
            ptr, self._image_info_size)

    @debug.profiler("Atlas2Backend::_load_parameter")
    def _load_parameter(self):
        pass

    @debug.profiler("Atlas2Backend:_infer_data")
    def _infer_data(self, task_list, batchsize):
        feed_lists, passby_lists = self.__buildBatch(task_list, batchsize)
        infer_lists = self.__inferBatch(feed_lists, passby_lists)
        result_lists = self.__processBatch(infer_lists, passby_lists, batchsize)
        logging.debug("raw result: %s", result_lists)
        return result_lists

    @debug.profiler("Atlas2Backend::__buildBatch")
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

    @debug.profiler("Atlas2Backend::__inferBatch")
    def __inferBatch(self, feed_lists, passby_lists):
        results = []
        for feed_instance in feed_lists:
            h, w, _ = feed_instance.shape
            _, feed_instance = cv2.imencode('.jpg' ,feed_instance)
            feed_instance = np.array(feed_instance).tostring()
            feed_instance = np.asarray(bytearray(feed_instance), dtype=np.byte)
            feed_instance = AclImage(feed_instance, w, h, feed_instance.size)
            yuv_instance = self._dvpp.convert_jpeg_to_yuv(feed_instance)
            resized_feed_instance = \
                self._dvpp.crop_and_resize(yuv_instance, feed_instance.width, feed_instance.height, self._model_width, self._model_height)
            result = self.model_object.execute(resized_feed_instance.data(), resized_feed_instance.size,
                                               self._image_info_dev, self._image_info_size)
            results.append(result)
        return results

    @debug.profiler("Atlas2Backend::__ProcessBatch")
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