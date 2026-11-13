# tests/test_tabla_inventario_id.py
import sys
import pytest
from PyQt6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

def test_tabla_inventario_headers_e_id(qapp):
    from src.ui_global.inventario_ui.paneles.tabla_inventario import TablaInventario

    tabla = TablaInventario()
    headers = [tabla.horizontalHeaderItem(i).text() for i in range(tabla.columnCount())]
    assert headers[0] == ""
    assert headers[1] == "ID"
    assert headers[2] == "Código"
    assert headers[3] == "Producto"

    filas = [
        {
            "id": 78,
            "codigo": "7790158465332",
            "nombre": "Comino Alicante",
            "departamento": "ALMACEN",
            "costo": 1100,
            "precio": 1500,
            "stock": 7,
            "unidad": "UN",
        },
        {
            "id": 105,
            "codigo": "770",
            "nombre": "Alitas",
            "departamento": "CARNICERIA",
            "costo": 1740,
            "precio": 3500,
            "stock": -30.91,
            "unidad": "KG",
        },
    ]
    tabla.set_datos(filas)
    assert tabla.rowCount() == 2

    # Fila 0
    assert tabla.item(0, 1).text() == "#78"
    assert tabla.item(0, 2).text() == "7790158465332"
    assert tabla.item(0, 3).text() == "Comino Alicante"
    assert tabla.id_de_fila(0) == "78"
    assert tabla.nombre_de_fila(0) == "Comino Alicante"

    # Fila 1 (pesable / código corto)
    assert tabla.item(1, 1).text() == "#105"
    assert tabla.item(1, 2).text() == "770"
    assert tabla.item(1, 3).text() == "Alitas"
    assert tabla.id_de_fila(1) == "105"
    assert tabla.nombre_de_fila(1) == "Alitas"
