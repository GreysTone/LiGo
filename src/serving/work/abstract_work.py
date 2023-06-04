"""
  Abstract Work

  Contact: arthur.r.song@gmail.com
"""

import abc
import json
import time
import logging

from enum import Enum, unique
from multiprocessing import Process, Value

from serving.core import debug
from serving.core import config


class AbstractWork(metaclass=abc.ABCMeta):
    def __init__(self, whash, wtype, configs, links):
        self.work_hash = whash
        self.work_type = wtype
        self.configs = json.loads(configs)
        # self.backend_links = links
        print(links)
        self.backend_link = ""
        if links.get('bid') is not None:
            self.backend_link = links['bid']
        self.outlet_link = ""
        if links.get('outlet') is not None:
            self.outlet_link = links['outlet']

        self.persist = config.exist_persist_work(self.work_hash)
        self.executor = None
        self.executor_sync_state = Value('B', Status.Unknown.value)
        self.executor_sync_state.value = Status.Stop.value
        self.work_object = None

    def __str__(self):
        return {
            'whash': self.work_hash,
            'wtype': self.work_type,
            'status': self.executor_sync_state.value,
            'persist': config.exist_persist_work(self.work_hash),
            'configs': json.dumps(self.configs),
            'link': {
                'bid': self.backend_link,
                'outlet': self.outlet_link,
            }
        }
    __repr__ = __str__

    @debug.flow("aw.run")
    def run(self):
        self.executor_sync_state.value = Status.Running.value
        self.executor = Process(
            target=self._main_loop,
            args=(self.executor_sync_state,))
        self.executor.daemon = True
        self.executor.start()

    @debug.flow("aw.stop")
    def stop(self):
        self.executor_sync_state.value = Status.Exiting.value
        time.sleep(2) # wait for while-loop exit
        if self.executor is not None:
            logging.debug("main-loop proc status: %s, is_alive: %s",
                self.executor_sync_state.value,
                self.executor.is_alive())
            self.executor.terminate()
            logging.debug("main-loop proc is terminated(%s)", self.executor.is_alive())
            self.executor_sync_state.value = Status.Stop.value

    @debug.flow("aw.enable_persist")
    def enable_persist(self):
        return config.enable_persist_work({
            'whash': self.work_hash,
            'wtype': self.work_type,
            'configs': self.configs,
            'link': {
                'bid': self.backend_link,
                'outlet': self.outlet_link,
            }
        })

    @debug.flow("aw.disable_persist")
    def disable_persist(self):
        return config.disable_persist_work(self.work_hash)

    @abc.abstractmethod
    def _main_loop(self, sync_status):
        raise NotImplementedError()

@unique
class Status(Enum):
    """Work Status Class
    """
    Unknown = 0
    Stop = 1
    Running = 2
    Exiting = 3
