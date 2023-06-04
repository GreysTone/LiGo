"""
  Core.Runtime: Tracks all data structures shared by the whole system

  Contact: arthur.r.song@gmail.com
"""

import sys
import logging
import importlib

from serving.core import sandbox
from serving.core import regulator
from serving.core import exception
from serving.core.memory import FEATURE_GATE, PLUGIN, \
    BACKEND_FACTORY, WORK_FACTORY, OUTLET_FACTORY

DEV_SERIAL = None
MAIN_PROCESS_PID = None

def validate_device():
    """Validates current device by DEVICE_SERIAL
    """
    if DEV_SERIAL != sandbox.device_serial():
        logging.fatal("unauthorized devices")
        sys.exit(-1)

@regulator.if_feature_on_run(FEATURE_GATE['on_authorized'], validate_device)
def load_gates(customized=None):
    """Load features gates
    """
    # import or overwrite feature gates
    if customized is not None:
        for key in customized:
            FEATURE_GATE[key] = customized[key]
    logging.debug("loaded feature gates: %s", FEATURE_GATE.items())

@regulator.if_feature_on_run(FEATURE_GATE['on_authorized'], validate_device)
def load_plugins(customized=None):
    """Loads plugins
    """
    # default plugins
    _plugins = {
        'exbase64': 'serving.plugin.exbase64',
        'reader': 'serving.plugin.reader',
        'soft-gst': 'serving.plugin.soft_gst',
    }
    # customized plugins
    if customized is not None:
        for key in customized:
            if customized[key] == "macro.offload":
                logging.debug("offload plugin: %s", key)
                del _plugins[key]
            else:
                _plugins[key] = customized[key]
    # load plugins
    for key in _plugins:
        if importlib.util.find_spec(_plugins[key]) is not None:
            PLUGIN[key] = importlib.import_module(_plugins[key])
    logging.debug("loaded plugins: %s", PLUGIN.keys())

@regulator.if_feature_on_run(FEATURE_GATE['on_authorized'], validate_device)
def load_backend_factory(customized=None):
    # default backends
    _backends = {
        'tensorflow': 'serving.backend.tensorflow_backend',
        'rknn': 'serving.backend.rknn_backend',
        'generic': 'serving.backend.generic_backend',
        'atlas': 'serving.backend.atlas_backend',
        'atlas2': 'serving.backend.atlas2_backend',
    }
    # customized backends
    if customized is not None:
        for key in customized:
            if customized[key] == "macro.offload":
                logging.debug("offload backend factory: %s", key)
                del _backends[key]
            else:
                _backends[key] = customized[key]
    # load backends
    for key in _backends:
        if importlib.util.find_spec(_backends[key]) is not None:
            try:
                BACKEND_FACTORY[key] = importlib.import_module(_backends[key])
            except exception.TruenoException:
                logging.error("failed to load backend (%s): %s", key, _backends[key])
    logging.debug("loaded backend factories: %s", BACKEND_FACTORY.keys())

@regulator.if_feature_on_run(FEATURE_GATE['on_authorized'], validate_device)
def load_outlet_factory(customized=None):
    # default outlets
    _outlets = {
        'sync': 'serving.outlet.sync_outlet',
        'redis': 'serving.outlet.redis_outlet',
        'mosquitto': 'serving.outlet.mosquitto_outlet',
        'syncexporter': 'serving.outlet.syncexporter_outlet',
    }
    # customized outlets
    if customized is not None:
        for key in customized:
            if customized[key] == "macro.offload":
                logging.debug("offload outlet factory: %s", key)
                del _outlets[key]
            else:
                _outlets[key] = customized[key]
    # load outlets
    for key in _outlets:
        if importlib.util.find_spec(_outlets[key]) is not None:
            try:
                OUTLET_FACTORY[key] = importlib.import_module(_outlets[key])
            except exception.TruenoException:
                logging.error("failed to load outlet (%s): %s", key, _outlets[key])
    logging.debug("loaded outlet factories: %s", OUTLET_FACTORY.keys())

@regulator.if_feature_on_run(FEATURE_GATE['on_authorized'], validate_device)
def load_work_factory(customized=None):
    # default work
    _works = {
        'stream-work': 'serving.work.stream_work',
    }
    # customized work
    if customized is not None:
        for key in customized:
            if customized[key] == "macro.offload":
                logging.debug("offload work factory: %s", key)
                del _works[key]
            else:
                _works[key] = customized[key]
    # load work
    for key in _works:
        if importlib.util.find_spec(_works[key]) is not None:
            try:
                WORK_FACTORY[key] = importlib.import_module(_works[key])
            except exception.TruenoException:
                logging.error("failed to load work (%s): %s", key, _works[key])
    logging.debug("loaded work factories: %s", WORK_FACTORY.keys())
