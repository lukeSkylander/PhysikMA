# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pendulum', 'pendulum3d', 'rk4', 'energy_utils', 'save_projection_svg', 'ui_utils', 'rk4_test1', 'rk4_test2', 'rk4_test3'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
