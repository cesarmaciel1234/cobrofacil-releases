# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('src/ui_components', 'src/ui_components'), ('src/assets', 'src/assets'), ('src/carteleria/assets', 'src/carteleria/assets'), ('Catalogos', 'Catalogos')],
    hiddenimports=['pymysql', 'reportlab.graphics.barcode.code93', 'reportlab.graphics.barcode.code128', 'reportlab.graphics.barcode.code39', 'reportlab.graphics.barcode.eanbc', 'lxml', 'html5lib', 'openpyxl', 'reportlab.graphics.barcode.qr', 'reportlab.graphics.barcode.dmtx', 'reportlab.graphics.barcode.ecc200datamatrix', 'reportlab.graphics.barcode.fourstate', 'reportlab.graphics.barcode.lto', 'reportlab.graphics.barcode.qrencoder', 'reportlab.graphics.barcode.usps', 'reportlab.graphics.barcode.usps4s', 'reportlab.graphics.barcode.widgets', 'reportlab.graphics.barcode.common'],
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
