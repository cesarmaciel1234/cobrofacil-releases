import pytest
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent

from src.ui_global.inventario_ui.moleculas.dialogo_producto import DialogoProducto


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_dialogo_producto_enter_guarda_directo(qapp):
    """Verifica que presionar Enter (Key_Return) en cualquier campo guarde directamente."""
    dlg = DialogoProducto(datos={'id': 1, 'codigo': '7791234567890', 'nombre': 'Galletitas'})
    
    # Simular foco en precio
    dlg.txt_precio.setFocus()
    dlg.txt_precio.setText("1500.00")
    
    with patch("src.motor_inventario.motor_catalogo.MotorCatalogo.verificar_codigo_existe", return_value=False), \
         patch("src.motor_inventario.motor_catalogo.MotorCatalogo.verificar_nombre_existe", return_value=False):
        
        key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        dlg.keyPressEvent(key_event)
        
        assert dlg.result() == QDialog.DialogCode.Accepted


def test_dialogo_producto_enter_numpad_guarda(qapp):
    """Verifica que el Enter del teclado numérico (Key_Enter) también guarde directamente."""
    dlg = DialogoProducto(datos={'id': 2, 'codigo': '7799999999999', 'nombre': 'Leche Entera'})
    
    dlg.txt_stock.setFocus()
    dlg.txt_stock.setText("50")
    
    with patch("src.motor_inventario.motor_catalogo.MotorCatalogo.verificar_codigo_existe", return_value=False), \
         patch("src.motor_inventario.motor_catalogo.MotorCatalogo.verificar_nombre_existe", return_value=False):
        
        key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Enter, Qt.KeyboardModifier.NoModifier)
        dlg.keyPressEvent(key_event)
        
        assert dlg.result() == QDialog.DialogCode.Accepted


def test_dialogo_producto_enter_en_cancelar_rechaza(qapp):
    """Si el foco está en el botón Cancelar, Enter debe cancelar y no guardar."""
    dlg = DialogoProducto(datos={'id': 3, 'codigo': '123', 'nombre': 'Producto Prueba'})
    dlg.btn_cancel.setFocus()
    
    key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
    dlg.keyPressEvent(key_event)
    
    assert dlg.result() == QDialog.DialogCode.Rejected


def test_dialogo_producto_tab_order_secuencia(qapp):
    """Verifica que el orden de tabulación (Tab Order) navegue secuencialmente entre todos los controles."""
    dlg = DialogoProducto()
    dlg.show()
    
    # Secuencia exacta esperada de controles al presionar TAB
    orden_esperado = [
        dlg.txt_codigo,
        dlg.txt_nombre,
        dlg.cmb_cat,
        dlg.cmb_depto,
        dlg.cmb_uni,
        dlg.txt_costo,
        dlg.txt_precio,
        dlg.txt_mayoreo,
        dlg.txt_cant_mayoreo,
        dlg.txt_stock,
        dlg.txt_min,
        dlg.txt_max,
        dlg.btn_save,
        dlg.btn_cancel
    ]
    
    dlg.txt_codigo.setFocus()
    assert dlg.focusWidget() == orden_esperado[0]
    
    for widget_esperado in orden_esperado[1:]:
        dlg.focusNextChild()
        assert dlg.focusWidget() == widget_esperado, f"Se esperaba foco en {widget_esperado}, pero está en {dlg.focusWidget()}"
    
    # Probar que Shift+Tab navega hacia atrás
    dlg.focusPreviousChild()
    assert dlg.focusWidget() == dlg.btn_save
    
    dlg.close()
