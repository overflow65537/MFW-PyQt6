# -*- mode: python ; coding: utf-8 -*-

_base = 'base.spec'

exe = EXE(
    _base,
    name='MFW',
    console=False,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    argv_emulation=False,
    target_arch='x86_64',
    codesign_identity='Developer ID Application: Overflow (XXXXXXXXXX)',
    entitlements_file='entitlements.plist',
    icon='MFW_resource/icon/logo.icns',
    bundle_identifier="com.overflow65537.MFWPYQT6",
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '12.1'
    },
)