from src.proveedor_global.backend.recepcion_service import RecepcionService


def test_fechas_usa_el_dia_del_remito():
    corta, completa = RecepcionService._fechas("2026-10-12")
    assert corta == "2026-10-12"
    assert completa.startswith("2026-10-12 ")


def test_fechas_conserva_hora_si_viene():
    corta, completa = RecepcionService._fechas("2026-10-12 08:15:00")
    assert corta == "2026-10-12"
    assert completa == "2026-10-12 08:15:00"


def test_fechas_hoy_si_falta():
    corta, completa = RecepcionService._fechas(None)
    assert len(corta) == 10
    assert completa.startswith(corta)
