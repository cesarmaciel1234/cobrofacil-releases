"""Alta, stock y borrado del inventario, en una base aparte. No toca la tienda."""
import sqlite3

from src.base_de_datos.database import db_manager


def _base():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT, nombre TEXT, precio REAL, stock REAL, costo REAL,
            unidad TEXT, departamento TEXT, categoria TEXT, icono TEXT
        )
        """
    )
    conn.commit()
    return conn


def _enganchar(monkeypatch, conn):
    def execute_non_query(query, params=(), _reintento=False):
        conn.execute(query, params or ())
        conn.commit()
        return True

    def execute_query(query, params=(), _reintento=False):
        cur = conn.execute(query, params or ())
        return [dict(fila) for fila in cur.fetchall()]

    monkeypatch.setattr(db_manager, "execute_non_query", execute_non_query)
    monkeypatch.setattr(db_manager, "execute_query", execute_query)
    monkeypatch.setattr(db_manager, "last_error", None, raising=False)
    monkeypatch.setattr(db_manager, "_forced_local_offline", False, raising=False)
    monkeypatch.setattr(db_manager, "is_master", True, raising=False)
    monkeypatch.setattr(
        "src.proveedor_global.frontend.formula.motores.extension.seguir",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "src.motor_inventario.planilla.orquestador.MotorPlanilla.avisar",
        staticmethod(lambda: None),
    )
    monkeypatch.setattr(
        "src.cerebro_global.motor_global.invalidar_catalogo",
        lambda: None,
    )
    monkeypatch.setattr(
        "src.central_red_global.sync_tienda.empujar_producto_a_maestra",
        lambda *a, **k: False,
    )
    monkeypatch.setattr(
        "src.central_red_global.sync_tienda.enviar_png_a_maestra",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "src.central_red_global.sync_tienda.aviso_tv.avisar_datos_nuevos",
        lambda: None,
    )
    monkeypatch.setattr(
        "src.motor_inventario.base.productos_db.asociar_png_un_producto",
        lambda *a, **k: None,
    )
    from src.base_de_datos.offline_nutricion import offline_nutricion_manager

    monkeypatch.setattr(offline_nutricion_manager, "productos_pendientes", lambda: [])


def _stock(codigo):
    filas = db_manager.execute_query("SELECT stock FROM productos WHERE codigo = ?", (codigo,))
    return float(filas[0]["stock"])


def test_alta_stock_y_borrado(monkeypatch):
    from src.motor_inventario.procesos.editor_productos import (
        comprobar_si_codigo_existe,
        comprobar_si_nombre_existe,
        guardar_producto_en_db,
    )
    from src.motor_inventario.base.productos_db import eliminar_producto_de_db
    from src.proveedor_global.frontend.formula.motores.inventario import aceptar

    conn = _base()
    _enganchar(monkeypatch, conn)

    ok, _msg = guardar_producto_en_db({
        "codigo": "CRIT-ALI",
        "nombre": "Alitas",
        "precio": 100,
        "stock": 10,
        "costo": 50,
    })
    assert ok
    assert _stock("CRIT-ALI") == 10

    ok, _msg = guardar_producto_en_db({
        "codigo": "CRIT-ALI2",
        "nombre": "Alitas",
        "precio": 90,
        "stock": 4,
    })
    assert ok
    assert comprobar_si_nombre_existe("Alitas")
    assert comprobar_si_codigo_existe("CRIT-ALI")
    assert not comprobar_si_codigo_existe("LIBRE")

    cur = conn.cursor()
    escritos = aceptar(cur, [{"codigo": "CRIT-ALI", "nombre": "Alitas", "kilos": 5, "costo": 0}])
    conn.commit()
    assert escritos == 1
    assert _stock("CRIT-ALI") == 15
    assert _stock("CRIT-ALI2") == 4

    fila = db_manager.execute_query("SELECT id FROM productos WHERE codigo = ?", ("CRIT-ALI",))
    ident = fila[0]["id"]
    ok, _msg = guardar_producto_en_db({"id": ident, "codigo": "CRIT-ALI", "nombre": "Alitas", "stock": 3}, True, ident)
    assert ok
    assert _stock("CRIT-ALI") == 3

    bien, _msg = eliminar_producto_de_db(ident)
    assert bien
    assert db_manager.execute_query("SELECT id FROM productos WHERE codigo = ?", ("CRIT-ALI",)) == []
    assert _stock("CRIT-ALI2") == 4
