import pytest
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent
from src.admin.auditoria_inventario.auditoria_main import DialogoConteo


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_dialogo_conteo_enter_guarda(qapp):
    """Verifica que presionar Enter (Key_Return o Key_Enter) guarde y aplique el conteo."""
    dlg = DialogoConteo(
        parent=None,
        nombre="Alitas",
        codigo="770",
        stock_sist="999877.930",
        conteo_actual="",
        departamento="GENERAL",
        unidad="kilos",
        pesable=True
    )

    # El usuario ingresa '1'
    dlg._tecla("1")
    assert dlg.valor() == 1.0
    assert dlg.btn_ok.isEnabled() is True

    # Simular tecla Enter
    key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
    dlg.keyPressEvent(key_event)

    # Debe haber aceptado el diálogo
    assert dlg.result() == QDialog.DialogCode.Accepted
    assert dlg.valor() == 1.0


def test_dialogo_conteo_enter_numpad(qapp):
    """Verifica que el Enter del teclado numérico (Key_Enter) también guarde."""
    dlg = DialogoConteo(
        parent=None,
        nombre="Asado",
        codigo="10",
        stock_sist="50.000",
        conteo_actual="",
        departamento="CARNES",
        unidad="kilos",
        pesable=True
    )

    dlg._tecla("2")
    dlg._tecla(",")
    dlg._tecla("5")
    assert dlg.valor() == 2.5

    # Simular Key_Enter (numpad)
    key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Enter, Qt.KeyboardModifier.NoModifier)
    dlg.keyPressEvent(key_event)

    assert dlg.result() == QDialog.DialogCode.Accepted
    assert dlg.valor() == 2.5


def test_dialogo_conteo_enter_vacio_toma_cero(qapp):
    """Si el usuario no escribe nada porque hay 0 stock, Enter guarda 0."""
    dlg = DialogoConteo(
        parent=None,
        nombre="Chorizo",
        codigo="1120",
        stock_sist="10.000",
        conteo_actual="",
        departamento="CARNES",
        unidad="kilos",
        pesable=True
    )

    # Buffer vacío -> al dar Enter se confirma 0
    key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
    dlg.keyPressEvent(key_event)

    assert dlg.result() == QDialog.DialogCode.Accepted
    assert dlg.valor() == 0.0
