"""Smoke del cierre piramidal (sin Qt / sin DB real)."""

from src.cerebro_global.cierre_caja_cerebro import (
    normalizar_modo,
    tipo_movimiento_cierre,
)
from src.cerebro_global.cierre_caja_cerebro.procesos.cierre import cerrar_caja
from src.cerebro_global.cierre_caja_cerebro.procesos.totales import obtener_datos_cierre


class FakeDB:
    def __init__(self):
        self.non_queries = []
        self.apertura = [{"fecha": "2026-08-04 08:00:00", "monto": 500}]
        self.ventas_abiertas = 2

    def execute_non_query(self, sql, params=()):
        self.non_queries.append((sql, params))
        if "UPDATE ventas" in sql:
            self.ventas_abiertas = 0

    def execute_query(self, sql, params=()):
        if "APERTURA" in sql:
            return list(self.apertura)
        return []

    def execute_scalar(self, sql, params=()):
        if "pago_efectivo" in sql:
            return 100
        if "Tarjeta" in sql:
            return 50
        if "Transferencia" in sql:
            return 20
        if "Fiado" in sql:
            return 10
        if "pago_otro" in sql:
            return 5
        if "SUM(total)" in sql and "metodo_pago" not in sql:
            return 185
        if "INGRESO" in sql:
            return 15
        if "RETIRO" in sql:
            return 5
        return 0

    def get_efectivo_en_caja(self, caja_id=1):
        return 750.0


def main():
    assert normalizar_modo("turno") == "cajero"
    assert normalizar_modo("dia") == "dia"
    assert tipo_movimiento_cierre("turno") == "CIERRE_TURNO"
    assert tipo_movimiento_cierre("dia") == "CIERRE_Z"
    print("modos OK")

    db = FakeDB()
    assert cerrar_caja("cajero1", 1, 750, 0, 750, 100, "turno", db=db)
    assert db.non_queries[0][1][1] == "CIERRE_TURNO"
    assert "UPDATE ventas" in db.non_queries[1][0]
    assert "usuario = ?" in db.non_queries[1][0]
    assert db.ventas_abiertas == 0
    print("cerrar turno OK")

    db2 = FakeDB()
    assert cerrar_caja("admin", 2, 1, 0, 1, 0, "dia", db=db2)
    assert db2.non_queries[0][1][1] == "CIERRE_Z"
    assert "usuario = ?" not in db2.non_queries[1][0]
    assert "caja_id = ?" in db2.non_queries[1][0]
    print("cerrar dia OK")

    d = obtener_datos_cierre(cajero="cajero1", caja_id=1, db=FakeDB())
    assert d["v_efectivo"] == 100
    assert d["v_credito"] == 10
    assert d["entradas_efectivo"] == 15
    assert d["v_caja_total"] == 750.0
    print("totales OK")

    import inspect
    from src.inicio_y_perfiles.logica.caja_controller import CajaController

    assert "CIERRE_TURNO" in inspect.getsource(CajaController.abrir_caja)
    print("CajaController OK")
    print("SMOKE PASS")


if __name__ == "__main__":
    main()
