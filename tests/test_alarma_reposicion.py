"""La alarma sale del inventario. No toca la tienda."""

import sqlite3

from src.motor_abastecimiento.detector.calculador_quiebre import obtener_productos_bajo_minimo
from src.motor_inventario.alarma.consulta import productos_con_alarma_reposicion


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
    conn.executemany(
        "INSERT INTO productos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (1, "A", "Vacio", "ALMACEN", 0, 0, 0, 10, 20),
            (2, "B", "Bajo piso", "ALMACEN", 3, 10, 20, 10, 20),
            (3, "C", "Sano", "ALMACEN", 20, 10, 40, 10, 20),
            (4, "D", "Poco sin piso", "ALMACEN", 4, 0, 0, 10, 20),
            (5, "E", "Articulo comun", "ALMACEN", 0, 0, 0, 10, 20),
            (6, "F", "Solo piso", "ALMACEN", 2, 8, 0, 10, 20),
        ],
    )
    conn.commit()
    return conn


def _memoria(monkeypatch, conn):
    from src.motor_inventario.alarma import consulta as consulta_alarma
    from src.motor_inventario.planilla import repo

    def execute_query(sql, params=()):
        consulta_alarma.db_manager.last_error = ""
        cur = conn.execute(sql, params)
        return [dict(fila) for fila in cur.fetchall()]

    def execute_non_query(sql, params=()):
        conn.execute(sql, params)
        conn.commit()
        return True

    monkeypatch.setattr(consulta_alarma.db_manager, "execute_query", execute_query)
    monkeypatch.setattr(repo.db_manager, "execute_non_query", execute_non_query)
    monkeypatch.setattr(repo.db_manager, "execute_query", execute_query)
    monkeypatch.setattr(repo, "_es_maria", lambda: False)


def test_si_la_planilla_no_contesta_el_pedido_sigue(monkeypatch):
    from src.motor_abastecimiento.hilo.pregunta import preguntar_alarma
    from src.motor_inventario.planilla.orquestador import MotorPlanilla

    def caida():
        raise RuntimeError("planilla caida")

    monkeypatch.setattr(MotorPlanilla, "leer", staticmethod(caida))
    assert preguntar_alarma() == []
    assert obtener_productos_bajo_minimo() == []


def test_la_alarma_es_critico_o_piso(monkeypatch):
    from src.motor_inventario.planilla.orquestador import MotorPlanilla

    conn = _base()
    _memoria(monkeypatch, conn)
    MotorPlanilla.actualizar()

    alarma = {p["nombre"]: p["motivo"] for p in productos_con_alarma_reposicion()}
    assert alarma["Vacio"] == "critico"
    assert alarma["Bajo piso"] == "reposicion"
    assert alarma["Solo piso"] == "reposicion"
    assert "Sano" not in alarma

    pedidos = {p["nombre"]: p for p in obtener_productos_bajo_minimo()}
    assert pedidos["Vacio"]["cantidad_a_pedir"] == 0
    assert pedidos["Vacio"]["motivo"] == "sin_piso"
    assert pedidos["Bajo piso"]["cantidad_a_pedir"] == 17
    assert pedidos["Solo piso"]["cantidad_a_pedir"] == 6
    assert "Sano" not in pedidos
    assert "Poco sin piso" not in pedidos


def test_si_la_lectura_falla_queda_la_hoja_anterior(monkeypatch):
    from src.motor_inventario.alarma import consulta as consulta_alarma
    from src.motor_inventario.planilla.orquestador import MotorPlanilla

    conn = _base()
    _memoria(monkeypatch, conn)
    MotorPlanilla.actualizar()
    assert any(p["nombre"] == "Vacio" for p in MotorPlanilla.leer())

    def lectura_rota():
        raise RuntimeError("stock no leido")

    monkeypatch.setattr(consulta_alarma, "productos_con_alarma_reposicion", lectura_rota)
    assert MotorPlanilla.actualizar() == 0
    assert any(p["nombre"] == "Vacio" for p in MotorPlanilla.leer())
