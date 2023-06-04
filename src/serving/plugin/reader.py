import os

import cv2
import numpy as np

from serving.core import runtime
from serving.core import exception
from serving.core import regulator


@regulator.validate(regulator.reader_source_required)
def read_image(data):
    return cv2.imread(data['source'])

@regulator.validate(regulator.reader_source_required)
def read_buffer(data):
    bytes_as_np_array = np.frombuffer(data['source'], dtype=np.uint8)
    return cv2.imdecode(bytes_as_np_array, cv2.IMREAD_ANYCOLOR)

@regulator.validate(regulator.reader_source_required)
def read_image_sequence(data):
    if not os.path.exists(data['source']):
        raise exception.ParamValidationError(": invalid source")
    for f in os.listdir(data['source']):
        img = cv2.imread(f)

@regulator.validate(regulator.reader_source_required)
def read_stream(data):
    cap = cv2.VideoCapture(data['source'])
    if not cap.isOpened():
        raise exception.ParamValidationError(": failed to open")
    while True:
        ret, frame = cap.read()
        if not ret:
            raise exception.ParamValidationError(": failed to get frame")
