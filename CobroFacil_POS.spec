# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('src/ui_components', 'src/ui_components'), ('src/assets', 'src/assets'), ('src/carteleria/assets', 'src/carteleria/assets'), ('src/carteleria/lanzador_tv/la_cara_web', 'src/carteleria/lanzador_tv/la_cara_web'), ('src/carteleria/creador_png/templates', 'src/carteleria/creador_png/templates'), ('src/carteleria/creador_png/static', 'src/carteleria/creador_png/static'), ('Catalogos', 'Catalogos')]
binaries = []
hiddenimports = ['reportlab.graphics.barcode.code93', 'reportlab.graphics.barcode.code128', 'reportlab.graphics.barcode.code39', 'reportlab.graphics.barcode.eanbc', 'src.cajero.paso5_terminal.componentes_paso5_terminal.componentes_barra_inferior.chatbot.chat_bot', 'lxml', 'html5lib', 'openpyxl', 'win32com', 'win32com.client', 'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore', 'src.carteleria.creador_png.app', 'src.carteleria.creador_png.servidor', 'flask', 'jinja2', 'werkzeug']
hiddenimports += collect_submodules('src.admin')
hiddenimports += collect_submodules('src.jefe')
hiddenimports += collect_submodules('src.cajero')
hiddenimports += collect_submodules('src.carteleria')
hiddenimports += collect_submodules('src.motor_descuentos')
hiddenimports += collect_submodules('src.services')
hiddenimports += collect_submodules('src.utils')
hiddenimports += collect_submodules('src.base_de_datos')
hiddenimports += collect_submodules('src.inicio_y_perfiles')
hiddenimports += collect_submodules('src.central_red_global')
hiddenimports += collect_submodules('src.ui_global')
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
    runtime_hooks=['01_Compiladores_y_Ejecutables/rthooks/pyi_rth_qt_dll_path.py'],
    excludes=['PyQt5', 'tkinter', 'tcl', '_tkinter', 'Tkinter', 'rembg', 'scipy', 'src.carteleria.creador_png.convertir_imagen'],
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
