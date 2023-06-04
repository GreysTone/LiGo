#!/usr/bin/env python3

"""
  Main entrance of LiGo

  Contact: arthur.r.song@gmail.com
"""

import os
import sys
import time
import signal
import logging
import argparse
from concurrent import futures


from serving.core import debug
from serving.core import config
from serving.core import backend
from serving.core import runtime
from serving.core.memory import FEATURE_GATE, BACKEND, PLUGIN

# force protobuf to use cpp-implementation
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'cpp'

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def load_multiple_model():
    model_list = []
    multiple_config = config.multiple_mode()
    for model, model_config in multiple_config.items():
        ret = backend.create_backend(model_config)
        b = BACKEND[ret['msg']]
        model_list.append(b)
        logging.debug("multiple_mode loading on: %s", ret['msg'])

    status_list = [-1] * len(model_list)
    for b in model_list:
        b.run()
    while min(status_list) < 4:
        status_list = []
        time.sleep(3)
        for b in model_list:
            r = b.report()
            status = r['cpstatus'][-1]
            status_list.append(status)
        logging.debug("cpstatus: {}".format(status_list))
    if max(status_list) > 4:
        logging.error("fail to load multiple model: {}".format(status_list))
        for b in model_list:
            b.stop()
        raise RuntimeError("fail to load multiple model")
    logging.debug("multiple_mode loaded!")

def boot_grpc():
    if FEATURE_GATE['on_grpc']:
        import grpc
        from serving import router_grpc
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        router_grpc.grpc_response(server)
        port = config.grpc_port()
        if server.add_insecure_port(port) == 0:
            logging.fatal("failed to bind on: %s", port)
            sys.exit(-1)
        server.start()
        logging.info("ligo listen gRPC at: %s", port)
        if not FEATURE_GATE['on_restful']:
            server.wait_for_termination()
    else:
        logging.info("ligo disabled gRPC server")

def boot_restful():
    if FEATURE_GATE['on_restful']:
        logging.info("ligo will accept RESTful by flask at: %s", config.restful_port())
        from serving.handler.restful import app
        app_jobs = []
        for key in PLUGIN:
            if "enable-" in key:
                app_jobs.append({"id": key, "func": PLUGIN[key].enable, "args": ""})
        if len(app_jobs) > 0:
            from flask_apscheduler import APScheduler
            scheduler = APScheduler()
            app.config["JOBS"] = app_jobs
            scheduler.init_app(app)
            scheduler.start()
        app.run(host="0.0.0.0", port=config.restful_port(), threaded=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LiGo')
    parser.add_argument('-c', '--conf', help='config file', type=str, default='confs.yaml')
    args = parser.parse_args()

    runtime.MAIN_PROCESS_PID = os.getpid()
    logging.getLogger('').setLevel(logging.INFO)
    config.load_configs_from_disk(config_path=args.conf)
    logging.debug(config.list_all_configs({'client': 'internal'}))

    # ignore child processes' signal
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    if config.debug_option():
        debug.enable_debug()
        from google.protobuf.internal import api_implementation
        logging.warning("using protobuf implementation: %s", api_implementation.Type())

    runtime.load_gates(customized=config.gates())
    runtime.load_plugins(customized=config.plugins())
    runtime.load_backend_factory(customized=config.backend_factory())
    runtime.load_work_factory(customized=config.work_factory())
    runtime.load_outlet_factory(customized=config.outlet_factory())

    if FEATURE_GATE['on_multiple_mode']:
        logging.debug("enter.multiple_mode")
        load_multiple_model()

    boot_grpc()
    boot_restful()
