PROTOC_VER=3.10.0
PROTOC_LINK=https://github.com/protocolbuffers/protobuf/releases/download/v$(PROTOC_VER)
PROTOC_SRC=protoc-$(PROTOC_VER)-linux-x86_64.zip

GRPCIO_VER=1.24.3
GRPCIO_TOOLS_VER=1.24.3

SRC_DIR=src/serving/interface
SDK_DIR=ligo/interface

.PHONY: protoc message-linux-amd64

protoc:
	# https://grpc.io/docs/quickstart/python/
	python3 -m pip install grpcio
	python3 -m pip install grpcio-tools

message-linux-amd64:
	echo ">>> coping: $(SRC_DIR)"; \
	rm -r $(SRC_DIR); \
	cp -r interface $(SRC_DIR); \
	srcs="backend connectivity inference model exchange"; \
	for proto_file in common $$srcs; do \
		echo "building:" $(SRC_DIR)/$$proto_file.proto; \
		python3 -m grpc_tools.protoc -I$(SRC_DIR) --python_out=$(SRC_DIR) --grpc_python_out=$(SRC_DIR) $(SRC_DIR)/$$proto_file.proto; \
		cmd="sed -i 's/$${proto_file}_pb2/serving.interface.&/' $(SRC_DIR)/$${proto_file}_pb2_grpc.py"; \
		eval $$cmd; \
	done; \
	for proto_file in $$srcs; do \
		echo "updating:" $(SRC_DIR)/$$proto_file.proto; \
		cmd="sed -i 's/common_pb2/serving.interface.&/' $(SRC_DIR)/$${proto_file}_pb2.py"; \
		eval $$cmd; \
		cmd="sed -i 's/common_pb2/serving.interface.&/' $(SRC_DIR)/$${proto_file}_pb2_grpc.py"; \
		eval $$cmd; \
	done; \
	echo "updating:" $(SRC_DIR)/backend.proto; \
	cmd="sed -i 's/model_pb2/serving.interface.&/' $(SRC_DIR)/backend_pb2.py"; \
	eval $$cmd; \
	cmd="sed -i 's/model_pb2/serving.interface.&/' $(SRC_DIR)/backend_pb2_grpc.py"; \
	eval $$cmd; \
	echo ">>> coping: $(SDK_DIR)"; \
	rm -r $(SDK_DIR); \
	cp -r interface $(SDK_DIR); \
	srcs="backend connectivity inference model exchange"; \
	for proto_file in common $$srcs; do \
		echo "building:" $(SDK_DIR)/$$proto_file.proto; \
		python3 -m grpc_tools.protoc -I$(SDK_DIR) --python_out=$(SDK_DIR) --grpc_python_out=$(SDK_DIR) $(SDK_DIR)/$$proto_file.proto; \
		cmd="sed -i 's/$${proto_file}_pb2/ligo.interface.&/' $(SDK_DIR)/$${proto_file}_pb2_grpc.py"; \
		eval $$cmd; \
	done; \
	for proto_file in $$srcs; do \
		echo "updating:" $(SDK_DIR)/$$proto_file.proto; \
		cmd="sed -i 's/common_pb2/ligo.interface.&/' $(SDK_DIR)/$${proto_file}_pb2.py"; \
		eval $$cmd; \
		cmd="sed -i 's/common_pb2/ligo.interface.&/' $(SDK_DIR)/$${proto_file}_pb2_grpc.py"; \
		eval $$cmd; \
	done; \
	echo "updating:" $(SRC_DIR)/backend.proto; \
	cmd="sed -i 's/model_pb2/ligo.interface.&/' $(SDK_DIR)/backend_pb2.py"; \
	eval $$cmd; \
	cmd="sed -i 's/model_pb2/ligo.interface.&/' $(SDK_DIR)/backend_pb2_grpc.py"; \
	eval $$cmd; \
	echo "done!"
