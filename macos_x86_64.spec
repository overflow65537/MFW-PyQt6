# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

_base = [
    ('MFW_resource/**', 'MFW_resource'),
    ('config/emulator.json', 'config'),
    ('dll/*', '.'),
    ('PyQt6/Qt/plugins', 'PyQt6/Qt/plugins'),
    ('PyQt6/Qt/translations', 'PyQt6/Qt/translations')
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[Tree('PyQt6/Qt/lib'), Tree('PyQt6/Qt/plugins')],
    datas=_base + [
        ('/path/to/maa/**', 'maa'),
        ('/path/to/MaaAgentBinary/**', 'MaaAgentBinary')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='MFW',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch='x86_64',
          codesign_identity='Developer ID Application: XXXXXXXX',
          entitlements_file='entitlements.plist',
          icon='MFW_resource/icon/logo.icns')