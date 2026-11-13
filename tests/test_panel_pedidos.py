"""Pruebas de Realizar pedido: tipografía, KPIs, modos y tablas opcionales en lectura."""

import logging
import sqlite3

import pytest
from PyQt6.QtWidgets import QApplication, QLabel


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _panel_con_resumen(monkeypatch):
    from src.proveedor_global.frontend.pedido.pantalla.panel import PanelPedidosAutomaticos

    monkeypatch.setattr(PanelPedidosAutomaticos, "refrescar_datos", lambda self: None)
    monkeypatch.setattr("src.proveedor_global.frontend.pedido.sugerir.preparar", lambda _p: None)
    panel = PanelPedidosAutomaticos()
    resumen = {
        "total_articulos_faltantes": 3,
        "pedidos": {
            "Distribuidora Uno": {
                "proveedor": "Distribuidora Uno",
                "codigo": "P00001",
                "total_items": 2,
                "items": [
                    {
                        "id": 10,
                        "codigo": "7546975043572",
                        "nombre": "Sal carne",
                        "stock_actual": 0.0,
                        "stock_minimo": 5.0,
                        "stock_maximo": 10.0,
                        "cantidad_a_pedir": 10.0,
                        "costo_unitario": 100.0,
                        "precio_unitario": 150.0,
                        "valor_unitario": 100.0,
                        "presupuesto_linea": 1000.0,
                    },
                    {
                        "id": "formula:Pollo",
                        "codigo": "",
                        "nombre": "Caja de pollo (cajas)",
                        "es_formula": True,
                        "stock_actual": 2.0,
                        "stock_minimo": 0.0,
                        "stock_maximo": 0.0,
                        "cantidad_a_pedir": 4.0,
                        "costo_unitario": 5000.0,
                        "precio_unitario": 5000.0,
                        "valor_unitario": 5000.0,
                        "presupuesto_linea": 20000.0,
                    },
                ],
            },
            "Proveedor B": {
                "proveedor": "Proveedor B",
                "codigo": "P00002",
                "total_items": 1,
                "items": [
                    {
                        "id": 20,
                        "codigo": "7798088142615",
                        "nombre": "Aceite",
                        "stock_actual": 1.0,
                        "stock_minimo": 3.0,
                        "stock_maximo": 6.0,
                        "cantidad_a_pedir": 5.0,
                        "costo_unitario": 200.0,
                        "precio_unitario": 250.0,
                        "valor_unitario": 200.0,
                        "presupuesto_linea": 1000.0,
                    },
                ],
            },
        },
    }
    panel._pintar_resumen(resumen)
    return panel


def test_panel_pedidos_kpis_tipografia_y_anchos(qapp, monkeypatch):
    panel = _panel_con_resumen(monkeypatch)

    for card in (panel.kpi_faltantes, panel.kpi_proveedores, panel.kpi_inversion):
        assert card.minimumHeight() >= 98

    assert panel.tbl_items.columnWidth(0) >= 145
    assert panel.tbl_items.item(0, 0).font().family() == "Consolas"
    assert panel.tbl_items.item(0, 0).font().bold()
    assert panel.tbl_items.item(0, 1).font().family() == "Segoe UI"
    assert panel.tbl_items.item(0, 1).font().bold()
    assert panel.tbl_items.item(0, 2).text() == "0"
    assert panel.kpi_faltantes.findChild(QLabel, "Val").text() == "2"


def test_panel_pedidos_todos_y_whatsapp_respetan_modo(qapp, monkeypatch):
    panel = _panel_con_resumen(monkeypatch)

    assert panel.cb_proveedor.itemText(0) == "Todos (2)"
    assert panel.kpi_proveedores.findChild(QLabel, "Val").text() == "2"
    assert "Caja de pollo" not in panel.txt_whatsapp.toPlainText()

    panel.tbl_items.item(0, 5).setText("12")
    wa_auto = panel.txt_whatsapp.toPlainText()
    assert "*12x* Sal carne" in wa_auto
    assert "Caja de pollo" not in wa_auto

    panel._elegir_modo("bulto")
    assert panel.cb_proveedor.itemText(0) == "Todos (1)"
    assert panel.kpi_faltantes.findChild(QLabel, "Val").text() == "1"
    assert panel.kpi_proveedores.findChild(QLabel, "Val").text() == "1"
    assert "Caja de pollo" in panel.txt_whatsapp.toPlainText()
    assert "Sal carne" not in panel.txt_whatsapp.toPlainText()


def test_lector_copia_sin_ruido_en_tablas_opcionales(tmp_path, caplog, monkeypatch):
    from src.jefe.nodo_portable.espejo.lector import Lector
    from src.proveedor_global.backend.cuenta import _leer_pagos_lectura
    from src.proveedor_global.backend.motor_proveedor import MotorProveedor
    from src.proveedor_global.frontend.formula.motores import carne_stock, pregunta

    ruta_db = tmp_path / "copia_vacia.db"
    conn = sqlite3.connect(ruta_db)
    conn.execute("CREATE TABLE productos (id INTEGER PRIMARY KEY, codigo TEXT, nombre TEXT)")
    conn.commit()
    conn.close()

    pregunta._AUSENTES.clear()
    lector = Lector(str(ruta_db))
    monkeypatch.setattr(
        MotorProveedor,
        "_get_read_db",
        staticmethod(lambda *_a, **_k: (lector, "copia")),
    )

    with caplog.at_level(logging.WARNING):
        for _ in range(3):
            assert pregunta.vivos(lector, "Mocho") is None
            assert carne_stock._ultimo(lector, "Carne") is None
            assert _leer_pagos_lectura() == []

    errores_db = [r.message for r in caplog.records if r.name.startswith("PunPro") and "no such table" in r.message]
    avisos_formula = [r.message for r in caplog.records if r.name == "formula_pregunta"]
    assert errores_db == []
    assert len(avisos_formula) == 1
    pregunta._AUSENTES.clear()
