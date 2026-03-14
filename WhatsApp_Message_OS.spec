# PyInstaller Spec File for WhatsApp Message OS
# This file configures the build process for creating a standalone .exe

import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
    ],
    hiddenimports=[
        'customtkinter',
        'tkinter',
        'pandas',
        'openpyxl',
        'selenium',
        'webdriver_manager',
    ] + collect_submodules('customtkinter'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=['matplotlib', 'PIL'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WhatsApp_Message_OS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Optional: Create a directory distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WhatsApp_Message_OS',
)
