# Phase-0 configuration seed for pyside6-android-deploy.
#
# This file follows the current Qt for Python deploy spec section/key format.
# Run --init with the installed PySide6 release and review any generated changes,
# because tool defaults may evolve between releases.

[app]
# Android packaging requires an entry point named main.py.
title = MFW Android PoC
project_dir = .
input_file = main.py
exec_directory = .
project_file = android.pyproject
icon =

[python]
# pyside6-android-deploy itself is installed in the build virtual environment.
# Android PySide6/shiboken6 are supplied below as target-specific wheels.
python_path =
packages =
android_packages = buildozer==1.5.0,cython==0.29.33

[qt]
qml_files =
excluded_qml_plugins =
modules = Core,Widgets
plugins =

[android]
# REQUIRED before building: replace both placeholders with a matching pair of
# official Android aarch64 wheels. Do not commit developer-specific absolute
# paths and do not use desktop/manylinux wheels.
wheel_pyside = <PATH_TO_PYSIDE6_ANDROID_AARCH64_WHEEL>
wheel_shiboken = <PATH_TO_SHIBOKEN6_ANDROID_AARCH64_WHEEL>
plugins =

[buildozer]
# First PoC target: Android arm64-v8a (named aarch64 by this tool).
mode = debug
arch = aarch64

# MaaFramework is intentionally absent in Phase 0. A later phase can populate
# recipe_dir and/or local_libs after all arm64-v8a native dependencies exist.
recipe_dir =
jars_dir =
ndk_path =
sdk_path =
local_libs =
