# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('src/styles.qss', 'src/'), ('src/ui_components/*.qss', 'src/ui_components/'), ('assets/*', 'assets/')]
binaries = []
hiddenimports = ['reportlab.graphics.barcode.code93', 'reportlab.graphics.barcode.code128', 'reportlab.graphics.barcode.code39', 'reportlab.graphics.barcode.eanbc', 'lxml', 'html5lib', 'openpyxl', 'win32com', 'win32com.client', 'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore']
hiddenimports += collect_submodules('src.admin')
hiddenimports += collect_submodules('src.jefe')
hiddenimports += collect_submodules('src.cajero')
hiddenimports += collect_submodules('src.carteleria')
hiddenimports += collect_submodules('src.services')
tmp_ret = collect_all('PyQt6.QtWebEngineCore')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('PyQt6.QtWebEngineWidgets')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='CobroFacil_POS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CobroFacil_POS',
)
