"""
  Router: gRPC Service Register

  Contact: arthur.r.song@gmail.com
"""

from serving.interface import backend_pb2_grpc as backend
from serving.interface import connectivity_pb2_grpc as connectivity
from serving.interface import exchange_pb2_grpc as exchange
from serving.interface import inference_pb2_grpc as inference
from serving.interface import model_pb2_grpc as model

from serving.handler import backend as hbe
from serving.handler import connectivity as hconn
from serving.handler import exchange as hexc
from serving.handler import inference as hinf
from serving.handler import model as hm


def grpc_response(server):
    backend.add_BackendServiceServicer_to_server(hbe.Backend(), server)
    connectivity.add_ConnectivityServicer_to_server(hconn.Connectivity(), server)
    exchange.add_ExchangeServicer_to_server(hexc.Exchange(), server)
    inference.add_InferenceServicer_to_server(hinf.Inference(), server)
    model.add_ModelServiceServicer_to_server(hm.Model(), server)
