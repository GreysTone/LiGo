"""
  Core.Debug: System debug and profile

  Contact: arthur.r.song@gmail.com
"""

import time
import logging
import signal,functools

from serving.core import config
from serving.core import exception

def profiler(prompt):
    """Profile function's running time
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if config.profile_option():
                ts = time.time()
                ret = func(*args, **kwargs)
                te = time.time()
                #logging.debug("{} elapse {} secs".format(prompt, te-ts))
                print("{} elapse {} secs".format(prompt, te-ts))
                return ret
            return func(*args, **kwargs)
        return wrapper
    return decorator

def timeout(seconds):
    """Restrict runtime for each function
    """
    def decorator(func):
        def signal_handler(signal_num, frame):
            raise exception.InferTimeOutError()

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, signal_handler)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
                return result
        return functools.wraps(func)(wrapper)
    return decorator


def flow(prompt):
    """Log function calling flow
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if config.debug_option():
                logging.debug(prompt)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def enable_debug():
    """Set debug level based on config
    """
    logging.getLogger('').setLevel(logging.DEBUG)
    logging.getLogger('').removeHandler(logging.getLogger('').handlers[0])
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(levelname)s: %(message)s [%(filename)s::%(lineno)d]"))
    if config.debug_vvv():
        _handler.setFormatter(logging.Formatter(
            "(%(asctime)s)<%(process)d>  %(levelname)s: %(message)s [%(filename)s:%(lineno)d]"))
    logging.getLogger('').addHandler(_handler)
    logging.debug(logging.getLogger('').handlers)
