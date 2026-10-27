"""El puente graba piso y techo. No toca el stock."""

from src.motor_inventario.piso.puente import guardar_piso_techo, validar_piso_techo


def test_un_techo_bajo_el_piso_no_escribe():
    limpios, error = validar_piso_techo([{"id": 1, "minimo": 10, "maximo": 4}])
    assert limpios == []
    assert error


def test_el_update_no_toca_la_columna_stock(monkeypatch):
    from src.base_de_datos.database import db_manager
    from src.motor_inventario.planilla.orquestador import MotorPlanilla

    vistos = []

    def execute_non_query(sql, params=()):
        vistos.append(sql)
        return True

    def _no_escribir():
        raise AssertionError("el puente no escribe la planilla")

    avisos = []
    monkeypatch.setattr(db_manager, "execute_non_query", execute_non_query)
    monkeypatch.setattr(MotorPlanilla, "actualizar", staticmethod(_no_escribir))
    monkeypatch.setattr(MotorPlanilla, "avisar", staticmethod(lambda: avisos.append(1)))
    ok, _msg = guardar_piso_techo([{"id": 7, "minimo": 2, "maximo": 9}])
    assert ok
    assert avisos == [1]
    assert len(vistos) == 1
    assert "stock_minimo" in vistos[0]
    assert "stock_maximo" in vistos[0]
    assert "SET stock " not in vistos[0]
