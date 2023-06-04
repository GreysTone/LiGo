"""
  Core.Compute: Compute Manager

  Contact: arthur.r.song@gmail.com
"""

import uuid
import logging

from serving.core import debug
from serving.core import scheduler
from serving.core import regulator
from serving.core.memory import FEATURE_GATE, BACKEND, IMAGES_POOL, PLUGIN
from serving.core.exception import InferenceDataError


@debug.flow("compute.local_async")
@regulator.validate(regulator.compute_required)
@regulator.validate(regulator.compute_local)
@regulator.if_feature_on_run(FEATURE_GATE['on_statistic'], PLUGIN['statistic'])
def local_async(data):
    backend_instance = BACKEND.get(data.get('bid'))
    if backend_instance is None:
        raise RuntimeError("failed to find backend")
    img_uuid = str(uuid.uuid4())
    IMAGES_POOL[img_uuid] = PLUGIN['reader'].read_image({'source': data['path']})
    backend_instance.enqueue_task(
        scheduler.Task(task_id=data['uuid'], image_id=img_uuid))

@debug.flow("compute.remote_async")
@regulator.validate(regulator.compute_required)
@regulator.validate(regulator.compute_remote)
@regulator.if_feature_on_run(FEATURE_GATE['on_statistic'], PLUGIN['statistic'])
def remote_async(data):
    backend_instance = BACKEND.get(data.get('bid'))
    if backend_instance is None:
        raise InferenceDataError(msg="failed to find backend")
    img_uuid = str(uuid.uuid4())
    #IMAGES_POOL[img_uuid] = PLUGIN['exbase64'].mem_b64_to_cvmat(
    #    bytes(data['base64'], encoding='utf8'),
    #    list(data['shape'])
    #)
    IMAGES_POOL[img_uuid] = PLUGIN['reader'].read_buffer({'source': data['data']})
    backend_instance.enqueue_task(
        scheduler.Task(task_id=data['uuid'], image_id=img_uuid))

@debug.flow("compute.restful_sync")
def restful_sync(data):
    backend_instance = BACKEND.get(data.get('bid'))
    extra_info = data.get('extra', '')
    if backend_instance is None:
        raise InferenceDataError(msg="failed to find backend")
    img_uuid = str(uuid.uuid4())
    IMAGES_POOL[img_uuid] = PLUGIN['reader'].read_buffer({'source': data['data']})
    backend_instance.enqueue_task(
        scheduler.Task(task_id=data['uuid'], image_id=img_uuid, extra=extra_info))
