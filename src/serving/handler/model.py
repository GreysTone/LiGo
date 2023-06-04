from google.protobuf.json_format import MessageToDict, ParseDict

from serving.core import model
from serving.core import exception
from serving.interface import common_pb2 as c_pb2
from serving.interface import model_pb2 as m_pb2
from serving.interface import model_pb2_grpc as m_pb2_grpc


class Model(m_pb2_grpc.ModelServiceServicer):
    def CreateModel(self, request, context):
        try:
            return ParseDict(model.create_model(MessageToDict(request)), c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to create model", err)

    def DeleteModel(self, request, context):
        try:
            return ParseDict(model.delete_model(MessageToDict(request)), c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to delete model", err)

    def ListAllModels(self, request, context):
        try:
            return ParseDict(model.list_all_models(request), m_pb2.ModelList())
        except exception.TruenoException:
            return m_pb2.ModelList(models=[])

    def InspectModel(self, request, context):
        try:
            ret = model.inspect_model(MessageToDict(request))
            return ParseDict(ret, m_pb2.Model())
        except exception.TruenoException:
            return m_pb2.Model()

    def EnableModel(self, request, context):
        raise NotImplementedError

    def DisableModel(self, request, context):
        raise NotImplementedError

    def RunModel(self, request, context):
        raise NotImplementedError

    def StopModel(self, request, context):
        raise NotImplementedError


    def UpdateModelConfigs(self, request, context):
        try:
            model.update_model_configs(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to update model configs", err)

    def UpdateModelConfigsFromURI(self, request, context):
        try:
            model.update_uri_model_configs(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to update model configs", err)


    def ImportModelFromLocal(self, request, context):
        try:
            return ParseDict(model.import_model(MessageToDict(request)), c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to import model bundle", err)

    def ImportModelFromURI(self, request, context):
        try:
            return ParseDict(model.import_uri_model(MessageToDict(request)), c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to import model bundle", err)

    def ExportModelToLocal(self, request, context):
        try:
            return ParseDict(model.export_model(MessageToDict(request)), c_pb2.ResultReply())
        except exception.TruenoException as err:
            return exception.proto_response(c_pb2, "failed to export model bundle", err)


    def EncryptedModel(self, request, context):
        raise NotImplementedError

    def DecryptedModel(self, request, context):
        raise NotImplementedError
