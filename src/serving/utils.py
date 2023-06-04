"""
  Utils: All tools and utility functions

  Contact: arthur.r.song@gmail.com
"""

import os
import logging
from multiprocessing import Process
from enum import Enum, unique # auto is available after python 3.7

@unique
class Access(Enum):
    Essential = 'essential'
    Optional = 'optional'

def run_in_process(func):
    """Starts a function with a new process
    """
    def wrapper(*args, **kwargs):
        return Process(target=func, args=args, kwargs=kwargs).start()
    return wrapper

def get_value(key, dicts, env_key='', lvl=Access.Essential, validator=None):
    """Gets value from dictionary and environemnt

    Gets value from dictionary. If `env_key` is given and available, overwrite
    its value with environment variable.
    """
    value = dicts.get(key)
    if env_key in os.environ:
        value = os.environ[env_key]
        logging.debug("environment <%s> exists", env_key)
    if isinstance(value, str) and value == '':
        value = None
    # if this value is essential
    if lvl == Access.Essential and value is None:
        message = "failed to get essential <{}>".format(key)
        logging.fatal(message)
        raise RuntimeError(message)
    # validator
    if hasattr(validator, '__call__'):
        value, err = validator(value)
        if value is None:
            raise RuntimeError("validate <{}> failed: {}".format(key, err))
    else:
        if validator is not None and value != validator:
            raise RuntimeError("expected {}, but get {}".format(validator, value))
    # return
    logging.debug("get <%s>: %s", key, value)
    return value
