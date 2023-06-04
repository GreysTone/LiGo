import cv2
import base64
import logging
import threading
import numpy as np
from flask import Flask, jsonify, json, request

from serving.core import compute
from serving.core import exception
from serving.core.memory import BACKEND, REQUESTS_COUNT

sharelock = threading.Lock()
app = Flask(__name__)


@app.route('/api/detect', methods=['POST'])
def detect():
    try:
        data = json.loads(str(request.data, encoding="utf-8"))
        result = {}
        for b in BACKEND:
            bhash = BACKEND[b].hash()
            image = base64.b64decode(data['image'])
            # image check
            bytes_as_np_array = np.frombuffer(image, dtype=np.uint8)
            temp = cv2.imdecode(bytes_as_np_array, cv2.IMREAD_ANYCOLOR)
            if temp is None:
                return jsonify({"msg": "image is damaged!"})

            extra_info = data.get('extra', '')
            sharelock.acquire()
            logging.error("Lock!")
            compute.restful_sync({
                'bid': bhash,
                'uuid': 'simple',
                'data': image,
                'extra': extra_info,
            })
            result[bhash] = BACKEND[b].dequeue_result()['simple']
            sharelock.release()
            logging.error("Release!")
        if not result:
            return 501, jsonify({"msg": "not model detected"})
        return jsonify({"result": result})
    except KeyError as err:
        logging.exception(err)
        return 400, jsonify({"msg": "missing key: {}".format(err)})
    except exception.TruenoException as err:
        logging.exception(err)
        return 500, jsonify({"msg": "internal error: {}".format(err)})
    except UnboundLocalError:
        logging.info("UnboundLocalError: request too fast")

@app.route('/api/ping', methods=['GET'])
def ping():
    try:
        return jsonify({"msg":"healthy!"})
    except UnboundLocalError:
        logging.info("UnboundLocalError: request too fast")

@app.before_request
def before_request():
    path = request.path
    if path == '/api/ping':
        global REQUESTS_COUNT
        REQUESTS_COUNT += 1
        logging.info("count of /api/ping: {}".format(REQUESTS_COUNT))
