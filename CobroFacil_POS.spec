# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/assets', 'src/assets'),
        ('src/ui_components/*.qss', 'src/ui_components'),
        ('src/cajero/paso5_terminal/componentes_paso5_terminal/apariencia/aviso/*.qss', 'src/cajero/paso5_terminal/componentes_paso5_terminal/apariencia/aviso'),
        ('src/cajero/paso5_terminal/componentes_paso5_terminal/apariencia/perfil/*.qss', 'src/cajero/paso5_terminal/componentes_paso5_terminal/apariencia/perfil')
    ],
    hiddenimports=[
        'src.cajero.paso5_terminal.componentes_paso5_terminal.apariencia.hoja',
        'src.cajero.paso6_cobro.mercadopago_core',
        'src.reportes_core',
        'src.services.db_network_service',
        'src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.atajos',
        'src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.bloquear',
        'src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.chatbot',
        'src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.espera',
        'src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.teclado',
        'src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.tema',
        'src.cajero.paso5_terminal.componentes_paso5_terminal.barra_de_herramientas_inferior.version',
        'qrcode'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5'],
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
