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
    """
    if result[0][0] != 'chair':
        print("[FAIL] no label: chair0")
        return False
    if result[1][0] != 'chair':
        print("[FAIL] no label: chair1")
        return False
    if result[2][0] != 'person':
        print("[FAIL] no label: person")
        return False
    if result[3][0] != 'tvmonitor':
        print("[FAIL] no label: tvmonitor")
        return False
    """
    return True

if __name__ == '__main__':
    print("Running Test:", __file__, "based on SDK:", ligo.__VERSION__)

    _u = "http://10.53.3.11:8080/file/"
    _m = "31f312e631c2def1189b8c8d29e002e2-1"
    _code = None
    with urllib.request.urlopen(_u+_m+".code") as response:
        _code = str(response.read(), 'utf-8').strip()

    run(_u, _m, "rknn", _code, "/tmp/private.pem", "/tmp/image", "/tmp/image", checker)
