import sqlite3
import pytest

from src.cerebro_global.operacion.ejecucion import aprobar, crear_borrador, marcar_despachado, marcar_recibido, obtener
from src.cerebro_global.operacion.eventos import listar, registrar
from src.cerebro_global.operacion.eventos.archivo import guardar, _BASE
from src.cerebro_global.operacion.planificacion import construir
from src.cerebro_global.operacion.politicas import obtener as obtener_politica


@pytest.fixture(autouse=True)
def _limpiar_eventos():
    guardar(dict(_BASE))
    yield
    guardar(dict(_BASE))


class DbPrueba:
    db_engine_type = "sqlite"

    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row

    def execute_non_query(self, sql, params=()):
        try:
            self.conn.execute(sql, params)
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def execute_query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()


def test_evento_es_idempotente_y_conserva_un_solo_hecho():
    db = DbPrueba()

    assert registrar(db, "VENTA", "caja-1", {"total": 100}, "venta-1") == "venta-1"
    assert registrar(db, "VENTA", "caja-1", {"total": 100}, "venta-1") == "venta-1"

    eventos = listar(db)
    assert len(eventos) == 1
    assert eventos[0]["cuerpo"] == {"total": 100}


def test_plan_no_puede_saltar_las_etapas_de_aprobacion():
    db = DbPrueba()
    politica = obtener_politica(db)
    plan = construir(
        {"total": 1, "modo": "borrador", "acciones": [{"formula": "Pollo", "cantidad": 2}]},
        politica,
    )

    assert crear_borrador(db, plan)
    assert marcar_despachado(db, plan["plan_id"]) is False
    assert aprobar(db, plan["plan_id"])
    assert marcar_despachado(db, plan["plan_id"])
    assert marcar_recibido(db, plan["plan_id"])
    assert obtener(db, plan["plan_id"])["estado"] == "RECIBIDO"
    assert [evento["tipo"] for evento in listar(db, 10)] == [
        "PLAN_RECIBIDO", "PLAN_DESPACHADO", "PLAN_APROBADO", "PLAN_CREADO",
    ]
