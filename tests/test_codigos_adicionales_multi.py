# tests/test_codigos_adicionales_multi.py
import pytest
from unittest.mock import patch
from src.repositories.producto_repository import ProductoRepository
from src.cajero.paso5_terminal.logica.carrito_service import CarritoService


def test_codigos_adicionales_crud_y_cajero():
    from src.base_de_datos.database import db_manager

    # Asegurar tabla
    ProductoRepository.asegurar_tabla_codigos_adicionales()

    # Insertar producto de prueba
    db_manager.execute_non_query(
        "INSERT INTO productos (id, nombre, precio, stock, codigo) VALUES (99991, 'Alfajor Triple', 1000.0, 100, '7791234999911')"
    )

    try:
        # 1. Agregar código adicional de bulto x12 (DUN-14)
        ok, msg = ProductoRepository.agregar_codigo_adicional(
            producto_id=99991,
            codigo="17791234999918",
            tipo="DUN",
            factor_unidades=12.0,
            descripcion="Caja cerrada x12"
        )
        assert ok is True

        # 2. Obtener códigos del producto
        lista = ProductoRepository.obtener_codigos_adicionales(99991)
        assert len(lista) >= 1
        item = [x for x in lista if x["codigo"] == "17791234999918"][0]
        assert float(item["factor_unidades"]) == 12.0
        assert item["tipo"] == "DUN"

        # 3. Intentar agregar duplicado debe fallar
        ok_dup, msg_dup = ProductoRepository.agregar_codigo_adicional(
            producto_id=99991,
            codigo="17791234999918",
            tipo="DUN"
        )
        assert ok_dup is False
        assert "ya está asignado" in msg_dup

        # 4. Probar búsqueda en CarritoService (Cajero)
        svc = CarritoService()

        # Escanear código principal (unidad)
        ok_scan, prod_unit, cant_unit, _ = svc.procesar_codigo_escaneado("7791234999911")
        assert ok_scan is True
        assert prod_unit["id"] == 99991
        assert cant_unit == 1.0

        # Escanear código de bulto (Caja x12)
        ok_scan_bulto, prod_bulto, cant_bulto, _ = svc.procesar_codigo_escaneado("17791234999918")
        assert ok_scan_bulto is True
        assert prod_bulto["id"] == 99991
        assert cant_bulto == 12.0  # Multiplicó por el factor del bulto!

        # Escanear 2 cajas de bulto (2*17791234999918)
        ok_scan_doble, prod_doble, cant_doble, _ = svc.procesar_codigo_escaneado("2*17791234999918")
        assert ok_scan_doble is True
        assert cant_doble == 24.0  # 2 * 12 = 24 unidades!

        # 5. Eliminar código adicional
        reg_id = item["id"]
        del_ok = ProductoRepository.eliminar_codigo_adicional(reg_id)
        assert del_ok is True
        lista_post = ProductoRepository.obtener_codigos_adicionales(99991)
        assert not any(x["codigo"] == "17791234999918" for x in lista_post)

    finally:
        # Limpieza
        db_manager.execute_non_query("DELETE FROM productos WHERE id = 99991")
        db_manager.execute_non_query("DELETE FROM productos_codigos_adicionales WHERE producto_id = 99991")
