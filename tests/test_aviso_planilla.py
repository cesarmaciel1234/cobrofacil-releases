"""Auditoría, recepción y piso avisan. El hilo de la planilla es el que escribe la hoja."""


def test_avisar_no_escribe_la_hoja(monkeypatch):
    from src.motor_inventario.planilla import hilo

    monkeypatch.setattr(hilo, "arrancar_hilo", lambda: None)
    hilo._despertar.clear()
    hilo.avisar_planilla()
    assert hilo._despertar.is_set()


def test_el_conteo_avisa_despues_del_set(monkeypatch):
    from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria
    from src.cerebro_global.auditoria.motor_conector_auditoria import MotorConectorAuditoria
    from src.motor_inventario.planilla.orquestador import MotorPlanilla

    con = MotorConectorAuditoria()
    escritos = []
    avisos = []
    monkeypatch.setattr(con, "_obtener_db_manager", lambda: object())
    monkeypatch.setattr(
        MotorAuditoria,
        "leer_producto",
        staticmethod(lambda db, pid: {"id": 3, "nombre": "Yerba", "stock": 1}),
    )
    monkeypatch.setattr(
        MotorAuditoria,
        "aplicar_ajuste_stock",
        staticmethod(lambda db, pid, stock: escritos.append(stock) or True),
    )
    monkeypatch.setattr(MotorAuditoria, "registrar_ajuste", staticmethod(lambda *a, **k: True))
    monkeypatch.setattr(MotorPlanilla, "avisar", staticmethod(lambda: avisos.append(1)))

    ok, _msg = con.solicitar_ajuste_stock(3, 5, "Cesar", "Conteo físico")
    assert ok
    assert escritos == [5.0]
    assert avisos == [1]


def test_sin_cambio_no_avisa(monkeypatch):
    from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria
    from src.cerebro_global.auditoria.motor_conector_auditoria import MotorConectorAuditoria
    from src.motor_inventario.planilla.orquestador import MotorPlanilla

    con = MotorConectorAuditoria()
    avisos = []
    monkeypatch.setattr(con, "_obtener_db_manager", lambda: object())
    monkeypatch.setattr(
        MotorAuditoria,
        "leer_producto",
        staticmethod(lambda db, pid: {"id": 3, "nombre": "Yerba", "stock": 5}),
    )
    def _no_escribir(*_a, **_k):
        raise AssertionError("no debía escribir")

    monkeypatch.setattr(MotorAuditoria, "aplicar_ajuste_stock", staticmethod(_no_escribir))
    monkeypatch.setattr(MotorPlanilla, "avisar", staticmethod(lambda: avisos.append(1)))

    ok, msg = con.solicitar_ajuste_stock(3, 5, "Cesar")
    assert ok
    assert msg == "Sin cambio"
    assert avisos == []


def test_si_el_set_falla_no_avisa(monkeypatch):
    from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria
    from src.cerebro_global.auditoria.motor_conector_auditoria import MotorConectorAuditoria
    from src.motor_inventario.planilla.orquestador import MotorPlanilla

    con = MotorConectorAuditoria()
    avisos = []
    monkeypatch.setattr(con, "_obtener_db_manager", lambda: object())
    monkeypatch.setattr(
        MotorAuditoria,
        "leer_producto",
        staticmethod(lambda db, pid: {"id": 3, "nombre": "Yerba", "stock": 1}),
    )
    monkeypatch.setattr(MotorAuditoria, "aplicar_ajuste_stock", staticmethod(lambda *a, **k: False))
    monkeypatch.setattr(MotorPlanilla, "avisar", staticmethod(lambda: avisos.append(1)))

    ok, _msg = con.solicitar_ajuste_stock(3, 5, "Cesar")
    assert not ok
    assert avisos == []


def test_el_lote_avisa_una_sola_vez(monkeypatch):
    from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria
    from src.cerebro_global.auditoria.motor_conector_auditoria import MotorConectorAuditoria
    from src.motor_inventario.planilla.orquestador import MotorPlanilla

    con = MotorConectorAuditoria()
    avisos = []
    monkeypatch.setattr(con, "_obtener_db_manager", lambda: object())
    monkeypatch.setattr(
        MotorAuditoria,
        "leer_producto",
        staticmethod(lambda db, pid: {"id": pid, "nombre": "Yerba", "stock": 0}),
    )
    monkeypatch.setattr(MotorAuditoria, "aplicar_ajuste_stock", staticmethod(lambda *a, **k: True))
    monkeypatch.setattr(MotorAuditoria, "registrar_ajuste", staticmethod(lambda *a, **k: True))
    monkeypatch.setattr(MotorPlanilla, "avisar", staticmethod(lambda: avisos.append(1)))

    ok, errores = con.aplicar_lote_ajustes(
        [{"id": 1, "stock_fisico": 4, "nombre": "A"}, {"id": 2, "stock_fisico": 6, "nombre": "B"}],
        "Cesar",
    )
    assert ok
    assert errores == []
    assert avisos == [1]


def test_si_la_planilla_no_contesta_el_conteo_queda(monkeypatch):
    from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria
    from src.cerebro_global.auditoria.motor_conector_auditoria import MotorConectorAuditoria
    from src.motor_inventario.planilla.orquestador import MotorPlanilla

    con = MotorConectorAuditoria()
    monkeypatch.setattr(con, "_obtener_db_manager", lambda: object())
    monkeypatch.setattr(
        MotorAuditoria,
        "leer_producto",
        staticmethod(lambda db, pid: {"id": 3, "nombre": "Yerba", "stock": 1}),
    )
    monkeypatch.setattr(MotorAuditoria, "aplicar_ajuste_stock", staticmethod(lambda *a, **k: True))
    monkeypatch.setattr(MotorAuditoria, "registrar_ajuste", staticmethod(lambda *a, **k: True))

    def _caer():
        raise RuntimeError("planilla caída")

    monkeypatch.setattr(MotorPlanilla, "avisar", staticmethod(_caer))
    ok, msg = con.solicitar_ajuste_stock(3, 8, "Cesar")
    assert ok
    assert msg == "Ajuste aplicado correctamente"


def test_el_ingreso_avisa_una_vez(monkeypatch):
    from src.base_de_datos.database import db_manager
    from src.motor_inventario.planilla.orquestador import MotorPlanilla
    from src.proveedor_global.backend.recepcion_service import RecepcionService

    def execute_non_query(sql, params=()):
        return True

    def execute_query(sql, params=()):
        if "romaneos" in sql:
            return [{"id": 9}]
        return []

    avisos = []
    monkeypatch.setattr(db_manager, "execute_non_query", execute_non_query)
    monkeypatch.setattr(db_manager, "execute_query", execute_query)
    monkeypatch.setattr(MotorPlanilla, "avisar", staticmethod(lambda: avisos.append(1)))

    ok, _msg, resumen = RecepcionService.procesar_ingreso_mercaderia(
        "Proveedor General",
        [{"id": 4, "cantidad": 2, "costo": 10, "nombre": "Yerba", "codigo": "1"}],
    )
    assert ok
    assert resumen["articulos_count"] == 1
    assert avisos == [1]
