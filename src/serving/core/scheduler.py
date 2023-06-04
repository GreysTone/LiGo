"""
  Core.Scheduler: Task Scheduler

  Contact: arthur.r.song@gmail.com
"""

import abc
import logging

from serving.core import exception


class Task(metaclass=abc.ABCMeta):
    def __init__(self, task_id, image_id, extra=''):
        self.task_id = task_id
        self.image_id = image_id
        self.outlet_id = None
        self.extra = extra

    def __del__(self):
        #TODO: remove images from memory
        logging.debug("task(%s) release", self.task_id)

    def __str__(self):
        return '<Task: id: %s, img: %s, outlet: %s>' % (self.task_id, self.image_id, self.outlet_id)
    __repr__ = __str__

    def update_outlet(self, outlet_id):
        self.outlet_id = outlet_id
