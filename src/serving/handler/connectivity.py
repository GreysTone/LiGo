"""
  Handler.Connectivity: Connectivity module gRPC handler

  Contact: arthur.r.song@gmail.com
"""

import psutil
import logging

from google.protobuf.json_format import MessageToDict, ParseDict

from serving.core import work
from serving.core import config
from serving.core import exception
from serving.interface import common_pb2 as c_pb2
from serving.interface import connectivity_pb2 as conn_pb2
from serving.interface import connectivity_pb2_grpc as conn_pb2_grpc

class Connectivity(conn_pb2_grpc.ConnectivityServicer):

    def Ping(self, request, context):
        return conn_pb2.PingReply(version="Trueno: Not Available")

    def ListNodeResources(self, request, context):
        gpu_mem = ""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_mem = meminfo.used
        except Exception:
            gpu_mem = "N/A"

        return conn_pb2.ResourcesReply(
            cpu=str(psutil.cpu_percent(interval=1)),
            mem=str(psutil.virtual_memory().percent),
            gpu=str(gpu_mem),
            dsk=str(psutil.disk_usage('/')[3]),
        )

    def ListConfigs(self, request, context):
        try:
            ret = config.list_all_configs(MessageToDict(request))
            return conn_pb2.ConfigList(conf=ret)
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to list configs", err)

    def UpdateConfig(self, request, context):
        try:
            ret = config.update_config(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to update config", err)

    def CreateWork(self, request, context):
        try:
            ret = work.create_work(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to create work", err)

    def DeleteWork(self, request, context):
        try:
            ret = work.delete_work(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to delete work", err)

    def ListAllWorks(self, request, context):
        try:
            ret = work.list_all_works(MessageToDict(request))
            return ParseDict(ret, conn_pb2.WorkList())
        except exception.TruenoException as err:
            logging.error(err)
            return conn_pb2.WorkList(works=[])

    def InspectWork(self, request, context):
        try:
            ret = work.inspect_work(MessageToDict(request))
            return ParseDict(ret, conn_pb2.Work())
        except exception.TruenoException as err:
            logging.error(err)
            return conn_pb2.Work()

    def EnableWork(self, request, context):
        try:
            ret = work.enable_work(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to enable work", err)

    def DisableWork(self, request, context):
        try:
            ret = work.disable_work(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to disable work", err)

    def RunWork(self, request, context):
        try:
            ret = work.run_work(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to run work", err)

    def StopWork(self, request, context):
        try:
            ret = work.stop_work(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to stop work", err)
