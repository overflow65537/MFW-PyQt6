# -*- mode: python ; coding: utf-8 -*-

_base = 'base.spec'

exe = EXE(
    _base,
    name='MFW',
    console=True,
    target_arch='arm64',
    upx=True,
    runtime_tmpdir=None,
    strip=True,
    bootloader_ignore_signals=False,
    binaries=[
        ('/usr/lib/aarch64-linux-gnu/libQt6Core.so.6', '.'),
        ('/usr/lib/aarch64-linux-gnu/libQt6Gui.so.6', '.')
    ]
)