"""
  Core.Memory: Tracks all data structures

  Contact: arthur.r.song@gmail.com
"""

from multiprocessing import Manager

SYS_CONFIGS = {}

BACKEND = {}
#BACKEND_SLOT = [False] * 50 # predefined max
WORK = {}
# TODO(arth): registrer IMAGES_POOL to network
# https://www.jianshu.com/p/f93a055b1723
IMAGES_POOL = Manager().dict()

FEATURE_GATE = {
    'on_multiple_mode': True,
    'on_grpc': True,
    'on_restful': True,
    'on_sandbox': True,
    'on_authorized': False,
    'on_tensorflow_gpu_3splits': True,
    'on_statistic': False,
}

PLUGIN = {
    'statistic': lambda: print("plugin.statistic"),
}

BACKEND_FACTORY = {}
WORK_FACTORY = {}
OUTLET_FACTORY = {}

REQUESTS_COUNT = 0