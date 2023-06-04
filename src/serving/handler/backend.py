"""
  Handler.Backend: Backend module gRPC handler

  Contact: arthur.r.song@gmail.com
"""

import logging

from google.protobuf.json_format import MessageToDict, ParseDict

from serving.core import backend
from serving.core import exception
from serving.interface import backend_pb2 as be_pb2
from serving.interface import backend_pb2_grpc as be_pb2_grpc
from serving.interface import common_pb2 as c_pb2


class Backend(be_pb2_grpc.BackendServiceServicer):
    def ListSupportedType(self, request, context):
        return be_pb2.SupportedReply(support=backend.supported_backend())

    # Backend
    def CreateBackend(self, request, context):
        try:
            ret = backend.create_backend(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to create backend", err)

    def DeleteBackend(self, request, context):
        try:
            ret = backend.delete_backend(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to delete backend", err)

    def ListAllBackends(self, request, context):
        try:
            # add list_all_backend(signature)
            ret = backend.list_all_backends()
            return ParseDict(ret, be_pb2.BackendList())
        except exception.TruenoException as err:
            logging.error(err)
            return be_pb2.BackendList(backends=[])

    def InspectBackend(self, request, context):
        try:
            ret = backend.inspect_backend(MessageToDict(request))
            return ParseDict(ret, be_pb2.Backend())
        except exception.TruenoException as err:
            logging.error(err)
            return be_pb2.Backend()

    def EnableBackend(self, request, context):
        try:
            ret = backend.enable_backend(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to enable backend", err)

    def DisableBackend(self, request, context):
        try:
            ret = backend.disable_backend(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to disable backend", err)

    def RunModelOnBackend(self, request, context):
        try:
            ret = backend.run_backend(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to run backend", err)

    def StopModelOnBackend(self, request, context):
        try:
            ret = backend.stop_backend(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to stop backend", err)

    # Outlet
    def AppendOutlet(self, request, context):
        try:
            ret = backend.append_outlet(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to append outlet", err)

    def ListOutlets(self, request, context):
        try:
            ret = backend.list_all_outlets(MessageToDict(request))
            return ParseDict(ret, be_pb2.OutletList())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to list outlet", err)

    def RemoveOutlet(self, request, context):
        try:
            ret = backend.remove_outlet(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to append outlet", err)

    # Combine
    def CreateAndLoadModel(self, request, context):
        try:
            ret = backend.create_and_load_model(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to create and load", err)
