#!/usr/bin/env python3

"""Build Trueno DEB package"""

import os
import sys
import platform


MICRO_ARCH = platform.machine()
PY_MAJOR = str(sys.version_info[0])
PY_MINOR = str(sys.version_info[1])

# Cleaning
print(">> Cleaning...")
if os.path.exists(os.path.join(os.getcwd(), 'deb')):
    os.system("rm -r deb")

# Insert Device Info
# TODO(): overwrite device serial number

# Building
VERSION = None
with open("VERSION", 'r') as ver_file:
    VERSION = ver_file.read()
if VERSION is None:
    raise RuntimeError("failed to read version")
VERSION = VERSION.strip()

arch = None
print("Detected build env:", MICRO_ARCH)
if MICRO_ARCH == "x86_64":
    arch = "amd64"
if MICRO_ARCH == "aarch64":
    arch = "arm64"
if arch is None:
    raise RuntimeError("failed to determine architecture")
print(">> Building", VERSION, "in:", arch, "...")

# Constructing
print(">> Constructing...")
os.system("mkdir deb")
os.system("cp -r DEBIAN deb/")
os.system("cp -r release-pack deb/ligo")
os.system("cp VERSION deb/ligo/")
os.system("cp CHANGELOG deb/ligo/")
ctrl_content = None
with open("deb/DEBIAN/control", 'r') as ctrl_file:
    ctrl_content = ctrl_file.read()
ctrl_content = ctrl_content.replace("REPLACE_VERSION", VERSION.strip())
ctrl_content = ctrl_content.replace("REPLACE_ARCH", arch)
with open("deb/DEBIAN/control", 'w') as ctrl_file:
    ctrl_file.write(ctrl_content)
    ctrl_file.flush()
print(ctrl_content)
print("Done")
os.system("dpkg-deb -b deb ligo-linux-"+arch+"-"+VERSION+".deb")
