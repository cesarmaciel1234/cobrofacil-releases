import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent

from src.admin.etiquetas_panel_ui.etiquetas_panel_main import AdminEtiquetas


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_admin_etiquetas_carga_productos_sin_error(qapp):
    """Verifica que la tabla cargue los productos del catálogo SQLite sin el error AttributeError de sqlite3.Row."""
    w = AdminEtiquetas()
    assert w.tabla.rowCount() > 0, "La tabla debe cargar los productos disponibles"
    assert w.cmb_categoria.count() > 1, "El combo de categorías debe incluir 'Todas las Categorías' y las del catálogo"


def test_admin_etiquetas_filtro_categoria(qapp):
    """Verifica que seleccionar una categoría filtre las filas de la tabla."""
    w = AdminEtiquetas()
    total_inicial = w.tabla.rowCount()
    
    # Seleccionar la categoría 'CARNE' si existe
    idx_carne = w.cmb_categoria.findData("CARNE")
    if idx_carne > 0:
        w.cmb_categoria.setCurrentIndex(idx_carne)
        assert w.tabla.rowCount() > 0
        assert w.tabla.rowCount() <= total_inicial
        
        # Volver a todas
        w.cmb_categoria.setCurrentIndex(0)
        assert w.tabla.rowCount() == total_inicial


def test_admin_etiquetas_click_fila_alterna_checkbox(qapp):
    """Al hacer clic en cualquier celda de una fila (ej: nombre o precio), se debe marcar/desmarcar el checkbox."""
    w = AdminEtiquetas()
    if w.tabla.rowCount() == 0:
        return
    
    item_chk = w.tabla.item(0, 0)
    assert item_chk.checkState() == Qt.CheckState.Unchecked
    
    # Clic en la celda de descripción (columna 2)
    w._on_cell_clicked(0, 2)
    assert item_chk.checkState() == Qt.CheckState.Checked
    assert len(w.productos_seleccionados) == 1
    assert "1" in w.lbl_stat_lote.text()
    
    # Segundo clic desmarca
    w._on_cell_clicked(0, 2)
    assert item_chk.checkState() == Qt.CheckState.Unchecked
    assert len(w.productos_seleccionados) == 0


def test_admin_etiquetas_espacio_alterna_checkbox(qapp):
    """Presionar la barra espaciadora en la tabla debe marcar/desmarcar la fila seleccionada."""
    w = AdminEtiquetas()
    if w.tabla.rowCount() == 0:
        return
    
    w.tabla.setCurrentCell(0, 2)
    item_chk = w.tabla.item(0, 0)
    
    space_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier)
    w.tabla.keyPressEvent(space_event)
    
    assert item_chk.checkState() == Qt.CheckState.Checked
    assert len(w.productos_seleccionados) == 1
    
    # Desmarcar todo
    w.desmarcar_todo()
    assert item_chk.checkState() == Qt.CheckState.Unchecked
    assert len(w.productos_seleccionados) == 0
