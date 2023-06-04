#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import urllib

# relocate package, when trueno_sdk is not installed
sys.path.append(os.path.dirname(__file__)+os.sep+'../')
print(sys.path)
import trueno
from base_tests import run


def checker(result):
    return True

if __name__ == '__main__':
    print("Running Test:", __file__, "based on SDK:", trueno.__VERSION__)

    _u = "http://10.53.3.11:8080/file/"
    _m = "f1f696fed13ac9702c624860729e78d9-1"
    _code = None
    with urllib.request.urlopen(_u+_m+".code") as response:
        _code = str(response.read(), 'utf-8').strip()

    run(_u, _m, "generic", _code, "/tmp/private.pem", "/tmp/image", "/tmp/image", checker)
