# tests/test_f6_enter_y_volver.py
import pytest
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent


from unittest.mock import patch

@pytest.fixture(scope="session")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_f6_primer_enter_se_frena_en_ficha_y_segundo_enter_pasa_a_pago(app):
    from src.cajero.f6_centro_cobranzas.dialogo import DialogoCentroCobranzas

    with patch.object(DialogoCentroCobranzas, "_f9"), \
         patch("src.cajero.f6_centro_cobranzas.panel.CentroCobranzasPanel._iniciar_hilo_interes"):

        dlg = DialogoCentroCobranzas()
        panel = dlg.panel

        # Estado inicial: buscando
        assert panel._modo == "buscando"
        assert panel.btn_volver_techo.text() == "✕ Salir"

        # Simular sugerencias con 1 cliente
        cliente_test = {"id": 101, "nombre": "RUBEN GOMEZ", "dni": "34123456", "deuda_actual": 5000.0}
        panel.panel_buscador.mostrar_sugerencias([cliente_test])

        # 1. Simular PRIMER ENTER en la caja de búsqueda
        ev_enter1 = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        dlg.keyPressEvent(ev_enter1)

        # El primer Enter debe seleccionar el cliente y FRENARSE en la Ficha del Cliente (Paso 2)
        assert panel._modo == "vista_cliente"
        assert panel._cliente_id == 101
        assert not panel.btn_iniciar_pago.isHidden()
        assert panel.btn_volver_techo.text() == "← Volver"
        assert panel.txt_monto_abono.isHidden()  # Aún NO pasó a medios de pago

        # 2. Simular SEGUNDO ENTER en la Ficha del Cliente
        ev_enter2 = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        dlg.keyPressEvent(ev_enter2)

        # El segundo Enter recién ahora pasa al Paso 3 (preparando pago / montos y medios)
        assert panel._modo == "preparando_pago"
        assert not panel.txt_monto_abono.isHidden()
        assert panel.btn_volver_techo.text() == "← Volver"


def test_f6_botones_volver_tactiles(app):
    from src.cajero.f6_centro_cobranzas.dialogo import DialogoCentroCobranzas

    with patch("src.cajero.f6_centro_cobranzas.panel.CentroCobranzasPanel._iniciar_hilo_interes"):
        dlg = DialogoCentroCobranzas()
        panel = dlg.panel

        # Seleccionar cliente directamente para ir a la Ficha
        cliente_test = {"id": 102, "nombre": "MARIA PEREZ", "dni": "28111222", "deuda_actual": 12000.0}
        panel.seleccionar_cliente_directo(cliente_test)

        # En la Ficha del Cliente (Paso 2):
        assert panel._modo == "vista_cliente"
        assert panel.btn_volver_techo.text() == "← Volver"

        # Clic táctil en el botón Volver del techo arriba a la derecha
        panel.btn_volver_techo.click()

        # Vuelve al buscador de clientes
        assert panel._modo == "buscando"
        assert panel._cliente_id is None
        assert panel.btn_volver_techo.text() == "✕ Salir"
        assert panel.panel_buscador.caja_busqueda.text() == ""

        # Nuevamente vamos a la Ficha y luego a Pago
        panel.seleccionar_cliente_directo(cliente_test)
        panel.btn_iniciar_pago.click()

        # En pantalla de pago (Paso 3):
        assert panel._modo == "preparando_pago"
        assert panel.btn_volver_techo.text() == "← Volver"

        # Clic táctil en el botón Volver del techo
        panel.btn_volver_techo.click()

        # Regresa limpiamente a la Ficha del Cliente
        assert panel._modo == "vista_cliente"
        assert panel._cliente_id == 102
        assert not panel.btn_iniciar_pago.isHidden()
        assert panel.txt_monto_abono.isHidden()
