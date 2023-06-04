"""
Constants for atlas2 backend
"""

IMAGE_DATA_NUMPY = 0
IMAGE_DATA_BUFFER = 1

SUCCESS = 0
FAILED = 1

ACL_DEVICE = 0
ACL_HOST = 1

MEMORY_NORMAL = 0
MEMORY_HOST = 1
MEMORY_DEVICE = 2
MEMORY_DVPP = 3

# error code
ACL_ERROR_NONE = 0
ACL_ERROR_INVALID_PARAM = 100000
ACL_ERROR_UNINITIALIZE = 100001
ACL_ERROR_REPEAT_INITIALIZE = 100002
ACL_ERROR_INVALID_FILE = 100003
ACL_ERROR_WRITE_FILE = 100004
ACL_ERROR_INVALID_FILE_SIZE = 100005
ACL_ERROR_PARSE_FILE = 100006
ACL_ERROR_FILE_MISSING_ATTR = 100007
ACL_ERROR_FILE_ATTR_INVALID = 100008
ACL_ERROR_INVALID_DUMP_CONFIG = 100009
ACL_ERROR_INVALID_PROFILING_CONFIG = 100010
ACL_ERROR_INVALID_MODEL_ID = 100011
ACL_ERROR_DESERIALIZE_MODEL = 100012
ACL_ERROR_PARSE_MODEL = 100013
ACL_ERROR_READ_MODEL_FAILURE = 100014
ACL_ERROR_MODEL_SIZE_INVALID = 100015
ACL_ERROR_MODEL_MISSING_ATTR = 100016
ACL_ERROR_MODEL_INPUT_NOT_MATCH = 100017
ACL_ERROR_MODEL_OUTPUT_NOT_MATCH = 100018
ACL_ERROR_MODEL_NOT_DYNAMIC = 100019
ACL_ERROR_OP_TYPE_NOT_MATCH = 100020
ACL_ERROR_OP_INPUT_NOT_MATCH = 100021
ACL_ERROR_OP_OUTPUT_NOT_MATCH = 100022
ACL_ERROR_OP_ATTR_NOT_MATCH = 100023
ACL_ERROR_OP_NOT_FOUND = 100024
ACL_ERROR_OP_LOAD_FAILED = 100025
ACL_ERROR_UNSUPPORTED_DATA_TYPE = 100026
ACL_ERROR_FORMAT_NOT_MATCH = 100027
ACL_ERROR_BIN_SELECTOR_NOT_REGISTERED = 100028
ACL_ERROR_KERNEL_NOT_FOUND = 100029
ACL_ERROR_BIN_SELECTOR_ALREADY_REGISTERED = 100030
ACL_ERROR_KERNEL_ALREADY_REGISTERED = 100031
ACL_ERROR_INVALID_QUEUE_ID = 100032
ACL_ERROR_REPEAT_SUBSCRIBE = 100033
ACL_ERROR_STREAM_NOT_SUBSCRIBE = 100034
ACL_ERROR_THREAD_NOT_SUBSCRIBE = 100035
ACL_ERROR_WAIT_CALLBACK_TIMEOUT = 100036
ACL_ERROR_REPEAT_FINALIZE = 100037
ACL_ERROR_BAD_ALLOC = 200000
ACL_ERROR_API_NOT_SUPPORT = 200001
ACL_ERROR_INVALID_DEVICE = 200002
ACL_ERROR_MEMORY_ADDRESS_UNALIGNED = 200003
ACL_ERROR_RESOURCE_NOT_MATCH = 200004
ACL_ERROR_INVALID_RESOURCE_HANDLE = 200005
ACL_ERROR_STORAGE_OVER_LIMIT = 300000
ACL_ERROR_INTERNAL_ERROR = 500000
ACL_ERROR_FAILURE = 500001
ACL_ERROR_GE_FAILURE = 500002
ACL_ERROR_RT_FAILURE = 500003
ACL_ERROR_DRV_FAILURE = 500004
# rule for mem
ACL_MEM_MALLOC_HUGE_FIRST = 0
ACL_MEM_MALLOC_HUGE_ONLY = 1
ACL_MEM_MALLOC_NORMAL_ONLY = 2
# rule for memory copy
ACL_MEMCPY_HOST_TO_HOST = 0
ACL_MEMCPY_HOST_TO_DEVICE = 1
ACL_MEMCPY_DEVICE_TO_HOST = 2
ACL_MEMCPY_DEVICE_TO_DEVICE = 3
# input
LAST_ONE = -1
LAST_TWO = -2
type_dict = {
    "bool": 0,
    "int8": 1,
    "int16": 2,
    "int32": 4,
    "int64": 8,
    "uint8": 1,
    "uint16": 2,
    "uint32": 4,
    "uint64": 8,
    "float16": 2,
    "float32": 4,
    "float64": 8,
    "float_": 8
}
NPY_BOOL = 0
NPY_BYTE = 1
NPY_UBYTE = 2
NPY_SHORT = 3
NPY_USHORT = 4
NPY_INT = 5
NPY_UINT = 6
NPY_LONG = 7
NPY_ULONG = 8
NPY_LONGLONG = 9
NPY_ULONGLONG = 10

ACL_DT_UNDEFINED = -1
ACL_FLOAT = 0
ACL_FLOAT16 = 1
ACL_INT8 = 2
ACL_INT32 = 3
ACL_UINT8 = 4
ACL_INT16 = 6
ACL_UINT16 = 7
ACL_UINT32 = 8
ACL_INT64 = 9
ACL_UINT64 = 10
ACL_DOUBLE = 11
ACL_BOOL = 12



# data format
ACL_FORMAT_UNDEFINED = -1
ACL_FORMAT_NCHW = 0
ACL_FORMAT_NHWC = 1
ACL_FORMAT_ND = 2
ACL_FORMAT_NC1HWC0 = 3
ACL_FORMAT_FRACTAL_Z = 4
ACL_DT_UNDEFINED = -1
ACL_FLOAT = 0
ACL_FLOAT16 = 1
ACL_INT8 = 2
ACL_INT32 = 3
ACL_UINT8 = 4
ACL_INT16 = 6
ACL_UINT16 = 7
ACL_UINT32 = 8
ACL_INT64 = 9
ACL_UINT64 = 10
ACL_DOUBLE = 11
ACL_BOOL = 12
acl_dtype = {
    "dt_undefined": -1,
    "float": 0,
    "float16": 1,
    "int8": 2,
    "int32": 3,
    "uint8": 4,
    "int16": 6,
    "uint16": 7,
    "uint32": 8,
    "int64": 9,
    "double": 11,
    "bool": 12
}
ACL_CALLBACK_NO_BLOCK = 0
ACL_CALLBACK_BLOCK = 1
PIXEL_FORMAT_YUV_400 = 0  # 0, YUV400 8bit
PIXEL_FORMAT_YUV_SEMIPLANAR_420 = 1  # 1, YUV420SP NV12 8bit
PIXEL_FORMAT_YVU_SEMIPLANAR_420 = 2  # 2, YUV420SP NV21 8bit
PIXEL_FORMAT_YUV_SEMIPLANAR_422 = 3  # 3, YUV422SP NV12 8bit
PIXEL_FORMAT_YVU_SEMIPLANAR_422 = 4  # 4, YUV422SP NV21 8bit
PIXEL_FORMAT_YUV_SEMIPLANAR_444 = 5  # 5, YUV444SP NV12 8bit
PIXEL_FORMAT_YVU_SEMIPLANAR_444 = 6  # 6, YUV444SP NV21 8bit
PIXEL_FORMAT_YUYV_PACKED_422 = 7  # 7, YUV422P YUYV 8bit
PIXEL_FORMAT_UYVY_PACKED_422 = 8  # 8, YUV422P UYVY 8bit
PIXEL_FORMAT_YVYU_PACKED_422 = 9  # 9, YUV422P YVYU 8bit
PIXEL_FORMAT_VYUY_PACKED_422 = 10  # 10, YUV422P VYUY 8bit
PIXEL_FORMAT_YUV_PACKED_444 = 11  # 11, YUV444P 8bit
PIXEL_FORMAT_RGB_888 = 12  # 12, RGB888
PIXEL_FORMAT_BGR_888 = 13  # 13, BGR888
PIXEL_FORMAT_ARGB_8888 = 14  # 14, ARGB8888
PIXEL_FORMAT_ABGR_8888 = 15  # 15, ABGR8888
PIXEL_FORMAT_RGBA_8888 = 16  # 16, RGBA8888
PIXEL_FORMAT_BGRA_8888 = 17  # 17, BGRA8888
PIXEL_FORMAT_YUV_SEMI_PLANNER_420_10BIT = 18  # 18, YUV420SP 10bit
PIXEL_FORMAT_YVU_SEMI_PLANNER_420_10BIT = 19  # 19, YVU420sp 10bit
PIXEL_FORMAT_YVU_PLANAR_420 = 20  # 20, YUV420P 8bit
# images format
IMG_EXT = ['.jpg', '.JPG', '.jpeg', '.JPEG']
