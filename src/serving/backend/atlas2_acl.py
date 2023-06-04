import acl
import struct
import logging
import numpy as np

from serving.core.constants import *


class AclModel(object):
    def __init__(self, run_mode, model_path):
        self._run_mode = run_mode
        self.model_path = model_path    # string
        self.model_id = None            # pointer
        self.input_dataset = None
        self.output_dataset = None
        self._output_info = []
        self.model_desc = None          # pointer when using
        self.init_resource()

    def __del__(self):
        self._release_dataset()
        if self.model_id:
            ret = acl.mdl.unload(self.model_id)
            check_ret("acl.mdl.unload", ret)
        if self.model_desc:
            ret = acl.mdl.destroy_desc(self.model_desc)
            check_ret("acl.mdl.destroy_desc", ret)
        logging.info("Atlas2_acl:: Model release source success")

    def init_resource(self):
        logging.info("Atlas2_acl:: class Model init resource stage:")
        self.model_id, ret = acl.mdl.load_from_file(self.model_path)
        check_ret("acl.mdl.load_from_file", ret)
        self.model_desc = acl.mdl.create_desc()
        ret = acl.mdl.get_desc(self.model_desc, self.model_id)
        check_ret("acl.mdl.get_desc", ret)
        output_size = acl.mdl.get_num_outputs(self.model_desc)
        self._gen_output_dataset(output_size)
        logging.info("Atlas2_acl:: class Model init resource stage success")
        self._get_output_info(output_size)

        return SUCCESS

    def _get_output_info(self, output_size):
        for i in range(output_size):
            dims = acl.mdl.get_output_dims(self.model_desc, i)
            datatype = acl.mdl.get_output_data_type(self.model_desc, i)
            self._output_info.append({"shape": tuple(dims[0]["dims"]), "type": datatype})

    def _gen_output_dataset(self, size):
        logging.info("Atlas2_acl:: create model output dataset:")
        dataset = acl.mdl.create_dataset()
        for i in range(size):
            temp_buffer_size = acl.mdl.\
                get_output_size_by_index(self.model_desc, i)
            temp_buffer, ret = acl.rt.malloc(temp_buffer_size,
                                             ACL_MEM_MALLOC_NORMAL_ONLY)
            check_ret("acl.rt.malloc", ret)
            dataset_buffer = acl.create_data_buffer(temp_buffer,
                                                    temp_buffer_size)
            _, ret = acl.mdl.add_dataset_buffer(dataset, dataset_buffer)
            if ret:
                acl.destroy_data_buffer(dataset)
                check_ret("acl.destroy_data_buffer", ret)
        self.output_dataset = dataset
        logging.info("Atlas2_acl:: create model output dataset success")

    def _gen_input_dataset(self, data1, data1_size, data2, data2_size):
        self.input_dataset = acl.mdl.create_dataset()

        input_dataset_buffer = acl.create_data_buffer(data1, data1_size)
        _, ret = acl.mdl.add_dataset_buffer(
            self.input_dataset,
            input_dataset_buffer)
        if ret:
            ret = acl.destroy_data_buffer(self.input_dataset)
            check_ret("acl.destroy_data_buffer", ret)

        input_dataset_buffer = acl.create_data_buffer(data2, data2_size)
        _, ret = acl.mdl.add_dataset_buffer(
            self.input_dataset,
            input_dataset_buffer)
        if ret:
            ret = acl.destroy_data_buffer(self.input_dataset)
            check_ret("acl.destroy_data_buffer", ret)

    def execute(self, data1, data1_size, data2, data2_size):
        self._gen_input_dataset(data1, data1_size, data2, data2_size)
        ret = acl.mdl.execute(self.model_id,
                              self.input_dataset,
                              self.output_dataset)
        check_ret("acl.mdl.execute", ret)
        return self._output_dataset_to_numpy()

    def _output_dataset_to_numpy(self):
        dataset = []
        num = acl.mdl.get_dataset_num_buffers(self.output_dataset)
        for i in range(num):
            buffer = acl.mdl.get_dataset_buffer(self.output_dataset, i)
            data = acl.get_data_buffer_addr(buffer)
            size = acl.get_data_buffer_size(buffer)
            if self._run_mode == ACL_HOST:
                data = copy_data_device_to_host(data, size)
            data_array = acl.util.ptr_to_numpy(data, (size, ), NPY_BYTE)
            data_array = self._unpack_output_item(data_array, self._output_info[i]["shape"], self._output_info[i]["type"])
            dataset.append(data_array)
        return dataset

    def _unpack_output_item(self, byte_array, shape, datatype):
        tag = ""
        np_type = None
        if datatype == ACL_FLOAT:
            tag = 'f'
            np_type = np.float
        elif datatype == ACL_INT32:
            tag = 'i'
            np_type = np.int32
        elif datatype == ACL_UINT32:
            tag = 'I'
            np_type = np.uint32
        else:
            logging.info("Atlas2_acl:: unsurpport datatype {}".format(datatype))
            return
        size = byte_array.size / 4
        unpack_tag = str(int(size)) + tag
        st = struct.unpack(unpack_tag, bytearray(byte_array))
        return np.array(st).astype(np_type).reshape(shape)

    def _release_dataset(self):
        for dataset in [self.input_dataset, self.output_dataset]:
            if not dataset:
                continue
            num = acl.mdl.get_dataset_num_buffers(dataset)
            for i in range(num):
                data_buf = acl.mdl.get_dataset_buffer(dataset, i)
                if data_buf:
                    ret = acl.destroy_data_buffer(data_buf)
                    check_ret("acl.destroy_data_buffer", ret)
            ret = acl.mdl.destroy_dataset(dataset)
            check_ret("acl.mdl.destroy_dataset", ret)


class AclDvpp():
    def __init__(self, stream, run_model):
        self._stream = stream
        self._run_mode = run_model
        self._dvpp_channel_desc = None

    def __del__(self):
        if self._dvpp_channel_desc:
            acl.media.dvpp_destroy_channel(self._dvpp_channel_desc)
            acl.media.dvpp_destroy_channel_desc(self._dvpp_channel_desc)

    def init_resource(self):
        self._dvpp_channel_desc = acl.media.dvpp_create_channel_desc()
        ret = acl.media.dvpp_create_channel(self._dvpp_channel_desc)
        if ret != ACL_ERROR_NONE:
            logging.error("Atlas2_acl:: Dvpp create channel failed")
            return FAILED
        return SUCCESS

    def convert_jpeg_to_yuv(self, image):
        logging.info('Atlas2_acl:: vpc decode stage:')
        device_image = image.copy_to_device(self._run_mode)
        output_desc, out_buffer = self._gen_jpegd_out_pic_desc(image)
        ret = acl.media.dvpp_jpeg_decode_async(self._dvpp_channel_desc,
                                               device_image.data(),
                                               image.size,
                                               output_desc,
                                               self._stream)
        if ret != ACL_ERROR_NONE:
            logging.error("Atlas2_acl:: dvpp_jpeg_decode_async failed ret={}".format(ret))
            return None

        ret = acl.rt.synchronize_stream(self._stream)
        if ret != ACL_ERROR_NONE:
            logging.error("Atlas2_acl:: dvpp_jpeg_decode_async failed ret={}".format(ret))
            return None

        width = align_up128(image.width)
        height = align_up16(image.height)
        return AclImage(out_buffer, width, height, yuv420sp_size(width, height), MEMORY_DVPP)

    def _gen_jpegd_out_pic_desc(self, image):
        stride_width = align_up128(image.width)
        stride_height = align_up16(image.height)

        out_buffer_size, ret = acl.media.dvpp_jpeg_predict_dec_size( \
            image.data(), image.size, PIXEL_FORMAT_YUV_SEMIPLANAR_420)
        if ret != ACL_ERROR_NONE:
            logging.error("predict jpeg decode size failed, return {}".format(ret))
            return None

        out_buffer, ret = acl.media.dvpp_malloc(out_buffer_size)
        check_ret("acl.media.dvpp_malloc", ret)

        pic_desc = acl.media.dvpp_create_pic_desc()
        acl.media.dvpp_set_pic_desc_data(pic_desc, out_buffer)
        acl.media.dvpp_set_pic_desc_format(pic_desc, PIXEL_FORMAT_YUV_SEMIPLANAR_420)
        acl.media.dvpp_set_pic_desc_width(pic_desc, image.width)
        acl.media.dvpp_set_pic_desc_height(pic_desc, image.height)
        acl.media.dvpp_set_pic_desc_width_stride(pic_desc, stride_width)
        acl.media.dvpp_set_pic_desc_height_stride(pic_desc, stride_height)
        acl.media.dvpp_set_pic_desc_size(pic_desc, out_buffer_size)

        return pic_desc, out_buffer

    def _gen_input_pic_desc(self, image):
        stride_width = align_up128(image.width)
        stride_height = align_up16(image.height)

        pic_desc = acl.media.dvpp_create_pic_desc()
        acl.media.dvpp_set_pic_desc_data(pic_desc, image.data())
        acl.media.dvpp_set_pic_desc_format(pic_desc, PIXEL_FORMAT_YUV_SEMIPLANAR_420)
        acl.media.dvpp_set_pic_desc_width(pic_desc, image.width)
        acl.media.dvpp_set_pic_desc_height(pic_desc, image.height)
        acl.media.dvpp_set_pic_desc_width_stride(pic_desc, stride_width)
        acl.media.dvpp_set_pic_desc_height_stride(pic_desc, stride_height)
        acl.media.dvpp_set_pic_desc_size(pic_desc, image.size)

        return pic_desc

    def _gen_resize_out_pic_desc(self, resize_width, resize_height):
        stride_width = align_up16(resize_width)
        stride_height = align_up2(resize_height)
        out_buffer_size = yuv420sp_size(stride_width, stride_height)
        out_buffer, ret = acl.media.dvpp_malloc(out_buffer_size)
        check_ret("acl.media.dvpp_malloc", ret)

        pic_desc = acl.media.dvpp_create_pic_desc()
        acl.media.dvpp_set_pic_desc_data(pic_desc, out_buffer)
        acl.media.dvpp_set_pic_desc_format(pic_desc, PIXEL_FORMAT_YUV_SEMIPLANAR_420)
        acl.media.dvpp_set_pic_desc_width(pic_desc, resize_width)
        acl.media.dvpp_set_pic_desc_height(pic_desc, resize_height)
        acl.media.dvpp_set_pic_desc_width_stride(pic_desc, stride_width)
        acl.media.dvpp_set_pic_desc_height_stride(pic_desc, stride_height)
        acl.media.dvpp_set_pic_desc_size(pic_desc, out_buffer_size)

        return pic_desc, out_buffer, out_buffer_size

    def crop_and_resize(self, image, width, height, crop_and_resize_width, crop_and_resize_height):
        input_desc = self._gen_input_pic_desc(image)
        output_desc, out_buffer, out_buffer_size = \
            self._gen_resize_out_pic_desc(crop_and_resize_width, crop_and_resize_height)
        self._crop_config = acl.media.dvpp_create_roi_config(0, (width >> 1 << 1) - 1, 0, (height >> 1 << 1) - 1)

        ret = acl.media.dvpp_vpc_crop_async(self._dvpp_channel_desc,
                                            input_desc,
                                            output_desc,
                                            self._crop_config,
                                            self._stream)
        check_ret("acl.media.dvpp_vpc_crop_async", ret)
        ret = acl.rt.synchronize_stream(self._stream)
        check_ret("acl.rt.synchronize_stream", ret)
        stride_width = align_up16(crop_and_resize_width)
        stride_height = align_up2(crop_and_resize_height)

        return AclImage(out_buffer, stride_width,
                        stride_height, out_buffer_size, MEMORY_DVPP)


class AclImage():
    def __init__(self, image, width=0, height=0,
                 size=0, memory_type=MEMORY_NORMAL):
        self._data = None
        self._np_array = None
        self._memory_type = memory_type
        self.width = 0
        self.height = 0
        self.channels = 0
        self.size = 0

        if isinstance(image, int):
            self._instance_by_buffer(image, width, height, size)
        elif isinstance(image, np.ndarray):
            self._instance_by_npndarray(image, width, height, size)
        else:
            logging.error("Atlas2_acl:: Create instance failed for unknow image data type")

    def _instance_by_npndarray(self, image_array, width, height, size):
        self._data = image_array
        self._type = IMAGE_DATA_NUMPY
        self.size = size
        self.width = width
        self.height = height

    def _instance_by_buffer(self, image_buffer, width, height, size):
        self.width = width
        self.height = height
        self.size = size
        self._data = image_buffer
        self._type = IMAGE_DATA_BUFFER

    def data(self):
        if self._type == IMAGE_DATA_NUMPY:
            return acl.util.numpy_to_ptr(self._data)
        else:
            return self._data

    def copy_to_device(self, run_mode):
        ptr = acl.util.numpy_to_ptr(self._data)
        device_ptr = None
        if run_mode == ACL_HOST:
            device_ptr = copy_data_host_to_device(ptr, self.size)
        else:
            device_ptr = copy_data_device_to_device(ptr, self.size)

        return  AclImage(device_ptr, self.width, self.height, self.size, MEMORY_DEVICE)

    def destroy(self):
        if self._memory_type == MEMORY_DEVICE:
            acl.rt.free(self._data)
        elif self._memory_type == MEMORY_HOST:
            acl.rt.free_host(self._data)
        elif self._memory_type == MEMORY_DVPP:
            acl.media.dvpp_free(self._data)

    def __del__(self):
        self.destroy()


## acl utils func
def check_ret(message, ret):
    if ret != ACL_ERROR_NONE:
        logging.error("{} failed ret={}".format(message, ret))

def copy_data_device_to_host(device_data, data_size):
    host_buffer, ret = acl.rt.malloc_host(int(data_size))
    check_ret("acl.rt.malloc_host", ret)
    ret = acl.rt.memcpy(host_buffer, data_size,
                        device_data, data_size,
                        ACL_MEMCPY_DEVICE_TO_HOST)
    check_ret("acl.rt.memcpy", ret)
    return host_buffer

def copy_data_device_to_device(device_data, data_size):
    host_buffer, ret = acl.rt.malloc(data_size, ACL_MEM_MALLOC_HUGE_FIRST)
    check_ret("acl.rt.malloc_host", ret)
    ret = acl.rt.memcpy(host_buffer, data_size,
                        device_data, data_size,
                        ACL_MEMCPY_DEVICE_TO_DEVICE)
    check_ret("acl.rt.memcpy", ret)
    return host_buffer

def copy_data_host_to_device(device_data, data_size):
    host_buffer, ret = acl.rt.malloc(data_size, ACL_MEM_MALLOC_HUGE_FIRST)
    check_ret("acl.rt.malloc_host", ret)
    ret = acl.rt.memcpy(host_buffer, data_size,
                        device_data, data_size,
                        ACL_MEMCPY_HOST_TO_DEVICE)
    check_ret("acl.rt.memcpy", ret)
    return host_buffer

def align_up(value, align):
    return int(int((value + align - 1) / align) * align)

def align_up128(value):
    return align_up(value, 128)

def align_up16(value):
    return align_up(value, 16)


def align_up2(value):
    return align_up(value, 2)

def yuv420sp_size(width, height):
    return int(width * height * 3 / 2)