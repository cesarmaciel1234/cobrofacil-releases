"""Mil productos bajan y suben de stock en memoria. No toca la tienda ni el cajero."""

import sqlite3
import time

from src.base_de_datos.repos.stock_descuento import SinStock, descontar_stock
from src.motor_abastecimiento.detector import calculador_quiebre
from src.motor_abastecimiento.enlace.puente_proveedor import resolver_proveedor

CANTIDAD = 1000
STOCK_INICIAL = 25.0
STOCK_MINIMO = 10.0
STOCK_MAXIMO = 40.0
VENTA_SANA = 5.0
VENTA_QUE_QUIEBRA = 12.0
DEPTOS = ("LACTEOS", "PANADERIA", "BEBIDAS", "LIMPIEZA")


def _config_sin_negativo(monkeypatch):
    from src.config import config

    original = config.get

    def get(key, default=None):
        if key == "opt_stock_negativo":
            return False
        return original(key, default)

    monkeypatch.setattr(config, "get", get)


def _base():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE productos (
            id INTEGER PRIMARY KEY,
            codigo TEXT,
            nombre TEXT,
            departamento TEXT,
            stock REAL,
            stock_minimo REAL,
            stock_maximo REAL,
            costo REAL,
            precio REAL
        )
        """
    )
    filas = []
    for i in range(1, CANTIDAD + 1):
        depto = "VARIOS" if i <= 200 else DEPTOS[(i - 201) % 4]
        filas.append(
            (i, f"C{i:04d}", f"Producto {i}", depto, STOCK_INICIAL, STOCK_MINIMO, STOCK_MAXIMO, 100.0, 150.0)
        )
    conn.executemany(
        "INSERT INTO productos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        filas,
    )
    conn.commit()
    return conn


def _usar_esta_base(monkeypatch, conn):
    from src.motor_inventario.alarma import consulta as consulta_alarma
    from src.motor_inventario.planilla import repo
    from src.motor_inventario.planilla.orquestador import MotorPlanilla

    def execute_query(sql, params=()):
        consulta_alarma.db_manager.last_error = ""
        cur = conn.execute(sql, params)
        return [dict(fila) for fila in cur.fetchall()]

    def execute_non_query(sql, params=()):
        conn.execute(sql, params)
        conn.commit()
        return True

    def execute_many(sql, params):
        conn.executemany(sql, params)
        conn.commit()
        return True

    monkeypatch.setattr(consulta_alarma.db_manager, "execute_query", execute_query)
    monkeypatch.setattr(repo.db_manager, "execute_query", execute_query)
    monkeypatch.setattr(repo.db_manager, "execute_non_query", execute_non_query)
    monkeypatch.setattr(repo.db_manager, "execute_many", execute_many)
    monkeypatch.setattr(repo, "_es_maria", lambda: False)
    return MotorPlanilla.actualizar


def _mapeos():
    mapas = [
        {
            "criterio_tipo": "departamento",
            "criterio_valor": depto,
            "proveedor_nombre": f"Proveedor {depto.title()}",
            "proveedor_codigo": f"P{n:05d}",
            "proveedor_id": n,
            "proveedor_telefono": "",
            "proveedor_email": "",
        }
        for n, depto in enumerate(DEPTOS, start=1)
    ]
    for i in range(801, 851):
        mapas.append(
            {
                "criterio_tipo": "producto_id",
                "criterio_valor": str(i),
                "proveedor_nombre": "Proveedor del producto",
                "proveedor_codigo": "P00050",
                "proveedor_id": 50,
                "proveedor_telefono": "",
                "proveedor_email": "",
            }
        )
    return mapas


def _catalogo(filas):
    return [r for r in filas or [] if not str(r.get("id") or "").startswith("formula:")]


def _stock(conn, producto_id):
    fila = conn.execute("SELECT stock FROM productos WHERE id = ?", (producto_id,)).fetchone()
    return float(fila["stock"])


def _bajar(conn, cantidad):
    cur = conn.cursor()
    rechazados = 0
    for i in range(1, CANTIDAD + 1):
        try:
            descontar_stock(cur, i, cantidad)
        except SinStock:
            rechazados += 1
    conn.commit()
    return rechazados


def _subir(conn, cantidad):
    cur = conn.cursor()
    for i in range(1, CANTIDAD + 1):
        cur.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (cantidad, i))
    conn.commit()


def test_mil_productos_bajan_y_suben(monkeypatch, capsys):
    _config_sin_negativo(monkeypatch)
    conn = _base()
    volcar = _usar_esta_base(monkeypatch, conn)
    mapas = _mapeos()

    inicio = time.perf_counter()
    rechazados_sanos = _bajar(conn, VENTA_SANA)
    ms_baja_sana = (time.perf_counter() - inicio) * 1000
    assert rechazados_sanos == 0
    assert _stock(conn, 1) == STOCK_INICIAL - VENTA_SANA
    volcar()
    assert _catalogo(calculador_quiebre.obtener_productos_bajo_minimo()) == []

    inicio = time.perf_counter()
    rechazados_quiebre = _bajar(conn, VENTA_QUE_QUIEBRA)
    ms_baja_quiebre = (time.perf_counter() - inicio) * 1000
    assert rechazados_quiebre == 0
    assert _stock(conn, 500) == 8.0
    assert conn.execute("SELECT COUNT(*) FROM productos WHERE stock < 0").fetchone()[0] == 0

    inicio = time.perf_counter()
    volcar()
    faltantes = _catalogo(calculador_quiebre.obtener_productos_bajo_minimo())
    ms_detector = (time.perf_counter() - inicio) * 1000
    assert len(faltantes) == CANTIDAD
    assert faltantes[0]["cantidad_a_pedir"] == 32.0
    assert faltantes[0]["costo_estimado_total"] == 3200.0

    grupos = {}
    for item in faltantes:
        elegido = resolver_proveedor(mapas, item)
        nombre = elegido["nombre"] if elegido and elegido.get("nombre") else "SIN PROVEEDOR ASIGNADO"
        grupo = grupos.setdefault(nombre, {"items": 0, "codigo": (elegido or {}).get("codigo") or ""})
        grupo["items"] += 1
    assert grupos["SIN PROVEEDOR ASIGNADO"]["items"] == 200
    assert grupos["Proveedor del producto"]["items"] == 50
    assert grupos["Proveedor del producto"]["codigo"] == "P00050"
    assert sum(g["items"] for g in grupos.values()) == CANTIDAD
    assert resolver_proveedor(mapas, {"id": 801, "departamento": "LACTEOS"})["nombre"] == "Proveedor del producto"

    antes = [_stock(conn, i) for i in range(1, CANTIDAD + 1)]
    inicio = time.perf_counter()
    rechazados_de_mas = _bajar(conn, 100)
    ms_rechazo = (time.perf_counter() - inicio) * 1000
    despues = [_stock(conn, i) for i in range(1, CANTIDAD + 1)]
    assert rechazados_de_mas == CANTIDAD
    assert antes == despues

    inicio = time.perf_counter()
    _subir(conn, 32)
    ms_suba = (time.perf_counter() - inicio) * 1000
    assert _stock(conn, 1) == STOCK_MAXIMO
    volcar()
    assert _catalogo(calculador_quiebre.obtener_productos_bajo_minimo()) == []

    _bajar(conn, 1)
    _subir(conn, 1)
    assert _stock(conn, 1000) == STOCK_MAXIMO

    with capsys.disabled():
        print(
            f"\n1000 productos | baja sana {ms_baja_sana:.0f} ms | "
            f"baja a quiebre {ms_baja_quiebre:.0f} ms | detector {ms_detector:.0f} ms | "
            f"1000 rechazos sin stock {ms_rechazo:.0f} ms | suba {ms_suba:.0f} ms | "
            f"grupos { {k: v['items'] for k, v in grupos.items()} }"
        )
