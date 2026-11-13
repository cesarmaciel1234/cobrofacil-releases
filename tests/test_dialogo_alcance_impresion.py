# tests/test_dialogo_alcance_impresion.py
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
import sys

@pytest.fixture(scope="session")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_dialogo_alcance_impresion_instanciacion_y_seleccion(app):
    from src.clientes_fiado.interfaz.historial.dialogo import (
        DialogoAlcanceImpresionCuenta,
        imprimir_historial_dialogo,
    )

    info = {
        "tiene_corte": True,
        "cant_actual": 5,
        "cant_total": 20,
    }

    dlg = DialogoAlcanceImpresionCuenta(None, info, nombre_cliente="RUBEN")

    # Verificar ancho amplio para evitar recorte
    assert dlg.width() >= 500

    # Verificar estado inicial
    assert dlg.resultado is None

    # Probar selección de deuda actual
    dlg._elegir_actual()
    assert dlg.resultado is True

    # Probar selección de historial completo
    dlg._elegir_completo()
    assert dlg.resultado is False


def test_imprimir_historial_dialogo_corte_usa_nuevo_dialogo(app):
    from src.clientes_fiado.interfaz.historial.dialogo import imprimir_historial_dialogo

    cliente = {"id": 1, "nombre": "RUBEN", "deuda_actual": 290235.0}
    movimientos = [{"tipo": "VENTA", "monto": 100}] * 20
    totales = {}

    with patch("src.hardware.printer.resumen_corte_cuenta") as mock_corte, \
         patch("src.hardware.printer.printer_manager.imprimir_historial_cuenta") as mock_print, \
         patch("src.clientes_fiado.interfaz.historial.dialogo.qt_exec") as mock_exec, \
         patch("PyQt6.QtWidgets.QMessageBox.information") as mock_info:

        mock_corte.return_value = {
            "tiene_corte": True,
            "cant_actual": 5,
            "cant_total": 20,
        }
        mock_print.return_value = True

        # Simulamos que el usuario eligió "Solo deuda actual" (resultado = True)
        def fake_exec(dlg):
            dlg.resultado = True
            return 1  # Accepted

        mock_exec.side_effect = fake_exec

        imprimir_historial_dialogo(None, cliente, movimientos, totales)

        # Debe llamar al printer con solo_deuda_actual=True
        mock_print.assert_called_once_with(
            cliente,
            movimientos,
            totales,
            solo_deuda_actual=True,
        )
