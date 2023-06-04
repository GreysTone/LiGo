"""
  Trueno Stream Work

  Contact: arthur.r.song@gmail.com
"""

import time
import uuid
import logging

import cv2

from serving.core import debug
from serving.core.memory import PLUGIN, BACKEND, IMAGES_POOL
from serving.core import scheduler
from serving.work import abstract_work as aw
from serving.core import exception


def new_work(whash, wtype, configs, links):
    return StreamWork(whash, wtype, configs, links)

class StreamWork(aw.AbstractWork):
    def __init__(self, whash, wtype, configs, links):
        super().__init__(whash, wtype, configs, links)
        self.work_object = PLUGIN['soft-gst'].get_gst_pipeline(self.configs)
        self.fps_control = 0.4

    @debug.flow("StreamWork::_main_loop")
    def _main_loop(self, sync_status):
        try:
            backend_instance = BACKEND.get(self.backend_link)
            if backend_instance is None:
                return exception.ParamValidationError(": invalid backend link")
            self.work_object.run()
            idx = 1
            while True:
                if sync_status.value == aw.Status.Exiting.value:
                    break
                logging.debug("steamwork: %s", idx)
                if not self.work_object.available():
                    time.sleep(1)
                    continue
                frame = self.work_object.frame()
                img_uuid = str(uuid.uuid4())
                IMAGES_POOL[img_uuid] = frame

                backend_instance.enqueue_task(
                    scheduler.Task(task_id=self.work_hash, image_id=img_uuid),
                    self.outlet_link)
                #cv2.imwrite('./test-img'+str(idx)+'.jpg', frame)
                time.sleep(self.fps_control)
                idx = idx + 1
        except Exception as err:
            logging.exception(err)
