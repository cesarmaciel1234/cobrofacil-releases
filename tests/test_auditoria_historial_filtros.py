"""Pruebas del Diálogo de Historial de Auditoría con Pantalla Completa y Filtros."""

import pytest
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.admin.auditoria_inventario.dialogo_historial import DialogoHistorialAuditoria


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_dialogo_historial_flags_y_fullscreen(qapp):
    """Verifica que el diálogo tenga el botón de maximizar al lado de la X y soporte pantalla completa."""
    mock_conector = MagicMock()
    mock_conector.obtener_historial_ajustes.return_value = [
        {"id": 1, "fecha": "2026-10-25 10:00:00", "producto_id": 770, "codigo": "77901", "nombre_producto": "Alitas", "stock_sistema": 100, "stock_fisico": 80, "diferencia": -20, "responsable": "admin", "motivo": "Conteo físico"},
        {"id": 2, "fecha": "2026-10-25 11:00:00", "producto_id": 400, "codigo": "77902", "nombre_producto": "Arrolldo", "stock_sistema": 10, "stock_fisico": 15, "diferencia": 5, "responsable": "supervisor", "motivo": "Ajuste manual"},
    ]

    dlg = DialogoHistorialAuditoria(conector=mock_conector)

    # 1. Verifica Window flags con botón de maximizar
    flags = dlg.windowFlags()
    assert bool(flags & Qt.WindowType.WindowMaximizeButtonHint) or bool(flags & Qt.WindowType.WindowMinMaxButtonsHint)

    # 2. Verifica existencia del botón de pantalla completa en la cabecera
    assert hasattr(dlg, "btn_fullscreen")
    assert "PANTALLA COMPLETA" in dlg.btn_fullscreen.text().upper()

    # 3. Toggle fullscreen
    dlg._toggle_fullscreen()
    assert dlg.isMaximized()
    assert "RESTAURAR" in dlg.btn_fullscreen.text().upper()

    dlg._toggle_fullscreen()
    assert not dlg.isMaximized()
    assert "PANTALLA COMPLETA" in dlg.btn_fullscreen.text().upper()


def test_dialogo_historial_filtros_multidimensionales(qapp):
    """Verifica el funcionamiento de los filtros por producto, usuario, diferencia y buscador de texto."""
    mock_conector = MagicMock()
    mock_conector.obtener_historial_ajustes.return_value = [
        {"id": 1, "fecha": "2026-10-25 10:00:00", "producto_id": 770, "codigo": "77901", "nombre_producto": "Alitas", "stock_sistema": 100, "stock_fisico": 80, "diferencia": -20.0, "responsable": "admin", "motivo": "Conteo físico"},
        {"id": 2, "fecha": "2026-10-25 11:00:00", "producto_id": 400, "codigo": "77902", "nombre_producto": "Arrolldo", "stock_sistema": 10, "stock_fisico": 15, "diferencia": 5.0, "responsable": "supervisor", "motivo": "Ajuste manual"},
        {"id": 3, "fecha": "2026-10-25 12:00:00", "producto_id": 100, "codigo": "77903", "nombre_producto": "Asado", "stock_sistema": 50, "stock_fisico": 50, "diferencia": 0.0, "responsable": "admin", "motivo": "Conteo físico"},
    ]

    dlg = DialogoHistorialAuditoria(conector=mock_conector)

    # Estado inicial: 3 registros cargados
    assert len(dlg.registros_filtrados) == 3
    assert dlg.tabla.rowCount() == 3
    assert dlg.val_total.text() == "3"
    assert dlg.val_prods.text() == "3"
    assert dlg.val_falt.text() == "-20.000"
    assert dlg.val_sobr.text() == "+5.000"

    # Filtro 1: Buscador de texto "alitas"
    dlg.txt_buscar.setText("alitas")
    assert len(dlg.registros_filtrados) == 1
    assert dlg.registros_filtrados[0]["nombre_producto"] == "Alitas"
    dlg.txt_buscar.clear()

    # Filtro 2: Selector de Producto por ID 400 (Arrolldo)
    idx_arrolldo = -1
    for i in range(dlg.cmb_producto.count()):
        if dlg.cmb_producto.itemData(i) == "400":
            idx_arrolldo = i
            break
    assert idx_arrolldo != -1
    dlg.cmb_producto.setCurrentIndex(idx_arrolldo)
    assert len(dlg.registros_filtrados) == 1
    assert dlg.registros_filtrados[0]["nombre_producto"] == "Arrolldo"
    dlg.cmb_producto.setCurrentIndex(0)  # Reset a todos

    # Filtro 3: Solo faltantes (diferencia negativa)
    idx_faltantes = -1
    for i in range(dlg.cmb_dif.count()):
        if dlg.cmb_dif.itemData(i) == "faltantes":
            idx_faltantes = i
            break
    assert idx_faltantes != -1
    dlg.cmb_dif.setCurrentIndex(idx_faltantes)
    assert len(dlg.registros_filtrados) == 1
    assert dlg.registros_filtrados[0]["nombre_producto"] == "Alitas"
    assert dlg.registros_filtrados[0]["diferencia"] == -20.0

    # Filtro 4: Solo sobrantes
    idx_sobrantes = -1
    for i in range(dlg.cmb_dif.count()):
        if dlg.cmb_dif.itemData(i) == "sobrantes":
            idx_sobrantes = i
            break
    dlg.cmb_dif.setCurrentIndex(idx_sobrantes)
    assert len(dlg.registros_filtrados) == 1
    assert dlg.registros_filtrados[0]["nombre_producto"] == "Arrolldo"

    # Limpiar filtros
    dlg._limpiar_filtros()
    assert len(dlg.registros_filtrados) == 3
