# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [('assets', 'assets')]
binaries = []
hiddenimports = []

# Collect all ruamel.yaml dependencies
tmp_ret = collect_all('ruamel.yaml')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Explicitly collect utils submodules as they are imported dynamically/conditionally
hiddenimports += collect_submodules('utils')
hiddenimports += ['core', 'ui']

block_cipher = None

a = Analysis(
    ['main_gui_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='RecyclarrConfigurator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False, # Disable UPX for GitHub Actions reliability
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/screenshot.png'
)
