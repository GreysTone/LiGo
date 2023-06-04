#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import urllib

# relocate package, when ligo_sdk is not installed
sys.path.append(os.path.dirname(__file__)+os.sep+'../')
print(sys.path)
import ligo
from base_tests import run


def checker(result):
    return True

if __name__ == '__main__':
    print("Running Test:", __file__, "based on SDK:", ligo.__VERSION__)

    _u = "http://10.53.3.11:8080/file/"
    _m = "05149c36815172ff4577bf4307b4ce18-1"
    _code = None
    with urllib.request.urlopen(_u+_m+".code") as response:
        _code = str(response.read(), 'utf-8').strip()

    run(_u, _m, "atlas", _code, "/tmp/private.pem", "/tmp/image", "/tmp/image", checker)
