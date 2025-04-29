# -*- mode: python ; coding: utf-8 -*-

_base = 'base.spec'

exe = EXE(
    _base,
    name='MFW',
    console=False,
    icon='MFW_resource/icon/logo.ico',
    bootloader_ignore_signals=True,
    upx=True,
    runtime_tmpdir=None,
    target_arch='x64',
    uac_admin=True
)