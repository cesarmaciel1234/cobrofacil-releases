import json
import os
import sqlite3
import pytest
from unittest.mock import MagicMock
from src.base_de_datos.offline_nutricion import OfflineNutricionManager
from src.base_de_datos.offline_sync import offline_sync_manager


@pytest.fixture
def temp_nutricion(tmp_path):
    mgr = OfflineNutricionManager()
    mgr.base_path = str(tmp_path)
    mgr.outbox_file = os.path.join(str(tmp_path), "offline_cambios.json")
    mgr._ensure_file()
    return mgr


def test_encolar_producto_offline(temp_nutricion):
    prod_data = {
        "codigo": "7791234567890",
        "nombre": "Yerba Mate 1kg",
        "precio": 2500.0,
        "costo": 1800.0,
        "stock": 45.0,
        "departamento": "ALMACEN"
    }
    assert temp_nutricion.encolar_producto(prod_data) is True

    resumen = temp_nutricion.obtener_resumen_pendientes()
    assert resumen["productos"] == 1
    assert resumen["total"] == 1

    # Actualizar producto existente en la cola (idéntico código)
    prod_data_edit = dict(prod_data, precio=2700.0)
    temp_nutricion.encolar_producto(prod_data_edit)

    resumen2 = temp_nutricion.obtener_resumen_pendientes()
    assert resumen2["productos"] == 1  # No se duplica, se actualiza el registro en cola

    cola = temp_nutricion._leer_cola()
    assert cola["productos"][0]["datos"]["precio"] == 2700.0


def test_encolar_recepcion_offline(temp_nutricion):
    items = [
        {"id": 1, "codigo": "779111", "nombre": "Fideos Tallarín", "cantidad": 10, "costo": 800.0},
        {"id": 2, "codigo": "779222", "nombre": "Salsa de Tomate", "cantidad": 20, "costo": 500.0}
    ]
    ok = temp_nutricion.encolar_recepcion(
        proveedor="Molinos Río de la Plata",
        items=items,
        total_bultos=30.0,
        total_monto=18000.0,
        condicion_pago="A Pagar",
        perfil="dueño"
    )
    assert ok is True

    resumen = temp_nutricion.obtener_resumen_pendientes()
    assert resumen["recepciones"] == 1
    assert resumen["total"] == 1

    cola = temp_nutricion._leer_cola()
    assert len(cola["recepciones"]) == 1
    rec = cola["recepciones"][0]
    assert rec["proveedor"] == "Molinos Río de la Plata"
    assert rec["total_monto"] == 18000.0
    assert len(rec["items"]) == 2


def test_encolar_cliente_offline(temp_nutricion):
    cli_data = {
        "nombre": "Juan Pérez",
        "dni": "35123456",
        "telefono": "1122334455",
        "limite_credito": 50000.0,
        "tipo_cliente": "regular"
    }
    assert temp_nutricion.encolar_cliente("ALTA", cli_data) is True

    resumen = temp_nutricion.obtener_resumen_pendientes()
    assert resumen["clientes"] == 1
    assert resumen["total"] == 1

    cola = temp_nutricion._leer_cola()
    assert cola["clientes"][0]["accion"] == "ALTA"
    assert cola["clientes"][0]["datos"]["nombre"] == "Juan Pérez"


def test_nutrir_maestra_ejecucion(temp_nutricion):
    # Encolar un producto, una recepción y un cliente
    temp_nutricion.encolar_producto({"codigo": "999", "nombre": "Galletitas", "precio": 1200, "stock": 10})
    temp_nutricion.encolar_recepcion("Arcor", [{"id": 10, "codigo": "999", "cantidad": 5, "costo": 700}], 5, 3500)
    temp_nutricion.encolar_cliente("ALTA", {"nombre": "Ana Gomez", "dni": "40111222"})

    assert temp_nutricion.obtener_resumen_pendientes()["total"] == 3

    # Simular db_manager conectado a MariaDB
    mock_db = MagicMock()
    mock_db.db_engine_type = "mariadb"
    mock_db.is_connected.return_value = True
    mock_db.execute_query.return_value = []
    mock_db.execute_non_query.return_value = True

    # Ejecutar nutrición
    ok, msg, stats = temp_nutricion.nutrir_maestra(mock_db)
    assert ok is True
    assert stats["productos"] == 1
    assert stats["recepciones"] == 1
    assert stats["clientes"] == 1

    # Verificar que el outbox quedó limpio tras el éxito
    assert temp_nutricion.obtener_resumen_pendientes()["total"] == 0
