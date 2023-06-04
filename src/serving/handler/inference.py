import logging

from google.protobuf.json_format import MessageToDict

from serving.core import compute
from serving.core import exception
from serving.interface import common_pb2 as c_pb2
from serving.interface import inference_pb2_grpc as inf_pb2_grpc

class Inference(inf_pb2_grpc.InferenceServicer):
    def InferenceLocal(self, request, context):
        try:
            compute.local_async(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to inference locally", err)

    def InferenceRemote(self, request, context):
        try:
            pass_in = {
                'bid': request.bid,
                'uuid': request.uuid,
                'outlet': request.outlet,
                'path': request.path,
                'data': request.data,
                'extra': request.extra,
                'dtype': request.dtype,
            }
            compute.remote_async(pass_in)
            return c_pb2.ResultReply(code=0, msg="")
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to inference remotely", err)
