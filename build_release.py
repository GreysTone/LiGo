#!/usr/bin/env python3

"""Build LiGo release pack"""

import os
import sys
import platform


MICRO_ARCH = platform.machine()
PY_MAJOR = str(sys.version_info[0])
PY_MINOR = str(sys.version_info[1])
SRC_INDEX = {
    'abstract_backend.py': ['serving/backend/', ''],
    'rknn_backend.py': ['serving/backend/', ''],
    'tensorflow_backend.py': ['serving/backend/', ''],
    'tensorflow_serving.py': ['serving/backend/', ''],
    'tensorflow_lite.py': ['serving/backend/', ''],
    'torch_python.py': ['serving/backend/', ''],
    'generic_backend.py': ['serving/backend/', ''],
    'atlas_backend.py': ['serving/backend/', ''],
    'atlas2_backend.py': ['serving/backend/', ''],
    'atlas2_acl.py': ['serving/backend/', ''],

    'backend.py': ['serving/core/', ''],
    'compute.py': ['serving/core/', ''],
    'config.py': ['serving/core/', ''],
    'debug.py': ['serving/core/', ''],
    'exception.py': ['serving/core/', ''],
    'memory.py': ['serving/core/', ''],
    'model.py': ['serving/core/', ''],
    'regulator.py': ['serving/core/', ''],
    'runtime.py': ['serving/core/', ''],
    'sandbox_helper.py': ['serving/core/', ''],
    'sandbox.py': ['serving/core/', ''],
    'scheduler.py': ['serving/core/', ''],
    'work.py': ['serving/core/', ''],
    'constants.py': ['serving/core/', ''],

    'restful.py': ['serving/handler/', ''],

    'backend_pb2_grpc.py': ['serving/interface/', ''],
    'backend_pb2.py': ['serving/interface/', ''],
    'common_pb2_grpc.py': ['serving/interface/', ''],
    'common_pb2.py': ['serving/interface/', ''],
    'connectivity_pb2_grpc.py': ['serving/interface/', ''],
    'connectivity_pb2.py': ['serving/interface/', ''],
    'exchange_pb2_grpc.py': ['serving/interface/', ''],
    'exchange_pb2.py': ['serving/interface/', ''],
    'inference_pb2_grpc.py': ['serving/interface/', ''],
    'inference_pb2.py': ['serving/interface/', ''],
    'model_pb2_grpc.py': ['serving/interface/', ''],
    'model_pb2.py': ['serving/interface/', ''],

    'abstract_outlet.py': ['serving/outlet/', ''],
    'mosquitto_outlet.py': ['serving/outlet/', ''],
    'redis_outlet.py': ['serving/outlet/', ''],
    'sync_outlet.py': ['serving/outlet/', ''],
    'syncexporter_outlet.py': ['serving/outlet/', ''],

    'exbase64.py': ['serving/plugin/', ''],
    'reader.py': ['serving/plugin/', ''],
    'soft_gst.py': ['serving/plugin/', ''],

    'abstract_work.py': ['serving/work/', ''],
    'stream_work.py': ['serving/work/', ''],

    'router_grpc.py': ['serving/', ''],
    'utils.py': ['serving/', ''],
}

def _clean_pycache(filepath):
    files = os.listdir(filepath)
    for fd in files:
        cur_path = os.path.join(filepath, fd)
        if os.path.isdir(cur_path):
            if fd == "__pycache__":
                print("rm %s -rf" % cur_path)
                os.system("rm %s -rf" % cur_path)
            else:
                _clean_pycache(cur_path)

def _build(DEV_SERIAL=""):
    try:
        # Cleaning
        print(">> Cleaning...")
        if os.path.exists(os.path.join(os.getcwd(), 'build')):
            if os.system("rm -r build") != 0:
                raise RuntimeError("[FAIL] Failed to remove previous internal builds")
        if os.path.exists(os.path.join(os.getcwd(), 'release-pack')):
            if os.system("rm -r release-pack") != 0:
                raise RuntimeError("[FAIL] Failed to remove previous builds")

        # Pre-process
        print(">> Pre processing...")
        # Overwrite DEV_SERIAL
        if DEV_SERIAL != "" or DEV_SERIAL is not None:
            if os.system("sed -i 's/SERIAL = None/SERIAL = \""+DEV_SERIAL+"\"/' src/serving/core/runtime.py") != 0:
                raise RuntimeError("[FAIL] Failed to overwrite DEV_SERIAL")
        # Overwrite _build_version
        _build_version = None
        with open("VERSION", 'r') as ver_file:
            _build_version = ver_file.read()
        _build_version = _build_version.strip()
        if _build_version is None:
            raise RuntimeError("[FAIL] BUILD_VERION is empty")
        if os.system("sed -i 's/Not Available/"+_build_version+"/' src/serving/handler/connectivity.py") != 0:
            raise RuntimeError("[FAIL] Failed to overwrite _build_version in Src")
        if os.system("sed -i 's/Not Available/"+_build_version+"/' ligo/__init__.py") != 0:
            raise RuntimeError("[FAIL] Failed to overwrite _build_version in SDK")
        if os.system("sed -i 's/Not Available/"+_build_version+"/' setup_sdk.py") != 0:
            raise RuntimeError("[FAIL] Failed to overwrite _build_version in SDK Builder")

        # Building
        print(">> Building", _build_version, "...")
        if os.system("make protoc") != 0:
            raise RuntimeError("[FAIL] Failed to install gRPC toolkit")
        if os.system("make message-linux-amd64") != 0:
            raise RuntimeError("[FAIL] Failed to compile .proto files")

        _scaned_src = []
        for index in SRC_INDEX:
            _decode_path = os.path.join("src/", SRC_INDEX[index][0], index)
            print("[INFO] Scaned:", _decode_path)
            _scaned_src.append(_decode_path)
        with open("srcs.txt", "w") as f:
            f.write(str(_scaned_src))
        if os.system("python3 setup.py build_ext") != 0:
            raise RuntimeError("[FAIL] Failed to generate compile files")

        # Constructing
        print(">> Constructing...")
        os.system("mkdir release-pack")
        os.system("cp src/run.py release-pack")
        _build_dir = "build/lib.linux-"+MICRO_ARCH+"-"+PY_MAJOR+"."+PY_MINOR+"/serving"
        os.system("cp -r "+_build_dir+" release-pack/")
        os.system("cp -r src/serving/handler release-pack/serving/")
        os.system("cp src/requirements.txt release-pack/")
        os.system("cp confs.example release-pack/confs.yaml")
        """
        for index in SRC_INDEX:
            _decode_path = os.path.join(SRC_INDEX[index][0], index)
            rm_cmd = "rm "+os.path.join("release-pack/", _decode_path.replace(".py", ".*"))
            os.system(rm_cmd)
            _built_path = os.path.join("build/lib.linux-"+MICRO_ARCH+"-"+PY_MAJOR+"."+PY_MINOR+"/", SRC_INDEX[index][1])
            _built_name = index.split('.')[0]+".cpython-"+PY_MAJOR+PY_MINOR+"m-"+MICRO_ARCH+"-linux-gnu.so"
            _target_path = os.path.join("release-pack/", SRC_INDEX[index][0])
            cp_cmd = "cp "+os.path.join(_built_path, _built_name)+" "+os.path.join(_target_path, _built_name)
            print(">", cp_cmd)
            if os.system(cp_cmd) != 0:
                raise RuntimeError("[FAIL] Failed to find generated file: {}".format(_built_name))
        _clean_pycache("release-pack")
        """

        if os.path.exists(os.path.join(os.getcwd(), 'build')):
            os.system("rm -r build")
        os.system("rm srcs.txt")

        # Build SDK whl package
        print(">> Constructing...")
        os.system("python3 setup_sdk.py bdist_wheel")

        # Change back DEV_SERIAL
        if os.system("sed -i 's/SERIAL = \""+DEV_SERIAL+"\"/SERIAL = None/' src/serving/core/runtime.py") != 0:
            raise RuntimeError("[FAIL] Failed to write back DEV_SERIAL")
        # Change back _build_version
        if os.system("sed -i 's/"+_build_version+"/Not Available/' src/serving/handler/connectivity.py") != 0:
            raise RuntimeError("[FAIL] Failed to write back _build_version in Src")
        if os.system("sed -i 's/"+_build_version+"/Not Available/' ligo/__init__.py") != 0:
            raise RuntimeError("[FAIL] Failed to write back _build_version in SDK")
        if os.system("sed -i 's/"+_build_version+"/Not Available/' setup_sdk.py") != 0:
            raise RuntimeError("[FAIL] Failed to write back _build_version in SDK Builder")

        print("Build release done.")
    except Exception as err:
        print(err)
        sys.exit(-1)

if __name__ == "__main__":
    _build()
