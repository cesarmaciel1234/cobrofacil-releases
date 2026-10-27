"""Pruebas del generador industrial de etiquetas de góndola térmicas con corte."""

import pytest
from src.hardware.printer import printer_manager, CUT_PAPER, GS, ESC, DOUBLE_HW_ON
from src.admin.etiquetas_panel_ui.generador_termica import (
    formatear_precio_argentino,
    normalizar_unidad,
    generar_codigo_barras_escpos,
    armar_etiqueta_termica,
    armar_preview_texto,
    armar_lote_etiquetas_termica,
)


def test_formatear_precio_argentino():
    assert formatear_precio_argentino(1500) == "$1.500"
    assert formatear_precio_argentino(1500.0) == "$1.500"
    assert formatear_precio_argentino(1500.50) == "$1.500,50"
    assert formatear_precio_argentino("23500") == "$23.500"
    assert formatear_precio_argentino("invalid") == "$0"


def test_normalizar_unidad():
    assert normalizar_unidad("kg") == "KILO"
    assert normalizar_unidad(None, es_pesable=True) == "KILO"
    assert normalizar_unidad("un") == "UNIDAD"
    assert normalizar_unidad("lt") == "LITRO"
    assert normalizar_unidad("gr") == "100 GR"


def test_generar_codigo_barras_escpos_ean13():
    ean = "7791234567890"
    raw = generar_codigo_barras_escpos(ean)
    assert raw.startswith(ESC + b"\x61\x01")  # Centrado
    assert GS + b"\x6b\x43" in raw  # EAN13 ESC/POS
    assert b"7791234567890" in raw


def test_generar_codigo_barras_escpos_code128():
    code = "ALFA-123"
    raw = generar_codigo_barras_escpos(code)
    assert GS + b"\x6b\x49" in raw or GS + b"\x6b\x45" in raw


def test_armar_etiqueta_termica_contiene_precio_gigante_y_corte():
    producto = {
        "id": "101",
        "codigo": "7791234567890",
        "nombre": "Asado Especial de Novillo",
        "precio": "8500",
        "unidad": "KG",
        "es_pesable": True,
        "is_oferta": False,
    }

    raw = armar_etiqueta_termica(
        producto=producto,
        rubro="CARNICERÍA",
        negocio="MACIEL",
        columnas=32,
        cortar=True,
        incluir_barcode=True,
        incluir_marca=True,
        incluir_fecha=True,
    )

    # Verifica reset y comandos ESC/POS
    assert raw.startswith(ESC + b"\x40")
    assert DOUBLE_HW_ON in raw  # Precio gigante (doble alto y ancho)
    assert b"$8.500" in raw
    assert b"MACIEL - CARNICERIA" in raw or b"MACIEL - CARNICER" in raw
    assert b"ASADO ESPECIAL DE NOVILLO" in raw
    assert b"x KILO" in raw
    assert b"PLU: 101" in raw
    # Verifica que termine con salto y corte de papel
    assert raw.endswith(CUT_PAPER)


def test_armar_etiqueta_termica_oferta():
    producto = {
        "id": "205",
        "codigo": "7798889990001",
        "nombre": "Pata Muslo x 3 Kilos",
        "precio": "6200",
        "precio_regular": "7500",
        "unidad": "KG",
        "is_oferta": True,
        "cant_oferta": 3,
        "tipo_unidad_oferta": "Kilos",
    }

    raw = armar_etiqueta_termica(
        producto=producto,
        rubro="GRANJA",
        negocio="MACIEL",
        columnas=32,
        cortar=True,
    )

    assert b"OFERTA" in raw
    assert b"$6.200" in raw
    assert b"Antes: $7.500" in raw
    assert raw.endswith(CUT_PAPER)


def test_armar_preview_texto():
    producto = {
        "id": "50",
        "codigo": "7790001112223",
        "nombre": "Milanesa de Nalga",
        "precio": "9200",
        "unidad": "KG",
        "is_oferta": False,
    }

    prev = armar_preview_texto(producto, rubro="CARNICERÍA", negocio="MACIEL", columnas=32)
    assert "MACIEL - CARNICERÍA" in prev
    assert "MILANESA DE NALGA" in prev
    assert "$9.200" in prev
    assert "x KILO" in prev
    assert "PLU: 50" in prev
    assert "✂️ [CORTE AUTOMÁTICO DE PAPEL]" in prev


def test_armar_lote_con_copias_y_corte_individual():
    productos = [
        {"id": "1", "nombre": "Prod A", "precio": "1000", "unidad": "UN"},
        {"id": "2", "nombre": "Prod B", "precio": "2000", "unidad": "UN"},
    ]

    lote_raw = armar_lote_etiquetas_termica(
        productos=productos,
        rubro="ALMACÉN",
        negocio="TIENDA",
        columnas=32,
        copias=2,  # 2 de cada uno = 4 etiquetas
        cortar_por_etiqueta=True,
    )

    # Cada etiqueta tiene un corte, total 4 cortes
    num_cortes = lote_raw.count(CUT_PAPER)
    assert num_cortes == 4
    # Comprobar que numera los productos del lote
    assert b"[1/2]" in lote_raw
    assert b"[2/2]" in lote_raw


def test_armar_lote_con_corte_al_final():
    productos = [
        {"id": "1", "nombre": "Prod A", "precio": "1000", "unidad": "UN"},
        {"id": "2", "nombre": "Prod B", "precio": "2000", "unidad": "UN"},
    ]

    lote_raw = armar_lote_etiquetas_termica(
        productos=productos,
        rubro="ALMACÉN",
        negocio="TIENDA",
        columnas=32,
        copias=1,
        cortar_por_etiqueta=False,  # Tira continua
    )

    # Solo 1 corte al final del lote
    num_cortes = lote_raw.count(CUT_PAPER)
    assert num_cortes == 1


def test_printer_manager_imprimir_etiquetas_gondola():
    # En modo test o simulación, debe enviar sin fallar
    test_bytes = b"\x1b\x40Test Etiqueta\n\n\n\n\x1d\x56\x41\x00"
    ok = printer_manager.imprimir_etiquetas_gondola(test_bytes)
    assert ok is True


def test_admin_etiquetas_ui_boton_termica():
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication.instance() or QApplication(sys.argv)
    from src.admin.etiquetas_panel_ui.etiquetas_panel_main import AdminEtiquetas
    from src.admin.etiquetas_panel_ui.dialogo_termica import ConfigurarTermicaDialog

    widget = AdminEtiquetas()
    assert hasattr(widget, "btn_print_thermal")
    assert widget.btn_print_thermal.objectName() == "btnPrintThermal"
    assert "TÉRMICA" in widget.btn_print_thermal.text().upper()

    # Prueba de instancia del diálogo de configuración
    sample_prods = [{"id": "1", "nombre": "Carne", "precio": "5000", "unidad": "KG"}]
    dlg = ConfigurarTermicaDialog(sample_prods, "CARNICERIA", "MACIEL")
    cfg = dlg.obtener_configuracion()
    assert cfg["columnas"] in (32, 48)
    assert cfg["copias"] >= 1
    assert cfg["cortar_por_etiqueta"] is True
    assert cfg["incluir_barcode"] is True
