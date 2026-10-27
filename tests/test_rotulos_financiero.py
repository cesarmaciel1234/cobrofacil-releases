"""Los días del reporte no pueden volver a guardarse como MiÃ©."""

from datetime import date

from src.jefe.reportes.financiero.rotulos import ENCABEZADO_DIA, es_anio, nombre_dia, titulo_serie


def test_miercoles_y_sabado_se_leen():
    assert nombre_dia(date(2026, 10, 7)) == "Mi\u00e9"
    assert nombre_dia(date(2026, 10, 10)) == "S\u00e1b"
    assert "\u00c3" not in nombre_dia(date(2026, 10, 7))


def test_proyeccion_feriado_y_mismo_tramo():
    import datetime

    from src.jefe.reportes.financiero.feriados import es_feriado
    from src.jefe.reportes.financiero.periodo_previo import (
        mismo_tramo,
        proyectar,
        rango_anio_pasado,
    )

    assert es_feriado(datetime.date(2026, 5, 25))
    assert not es_feriado(datetime.date(2026, 10, 20))
    assert proyectar(100, [40, 0, 10]) == 150
    inicio, fin = mismo_tramo(
        "Semana Actual",
        "2026-10-19 00:00:00",
        "2026-10-25 23:59:59",
        datetime.datetime(2026, 10, 20, 15, 0, 0),
    )
    assert inicio == "2026-10-12 00:00:00"
    assert fin == "2026-10-13 15:00:00"
    anio = rango_anio_pasado("Semana Actual", "2026-10-19 00:00:00", "2026-10-20 23:59:59")
    assert anio[0][:10] == "2025-10-20"
    assert anio[1][:10] == "2025-10-26"


def test_la_semana_pasada_es_lunes_a_domingo():
    from src.jefe.reportes.financiero.periodo_previo import clave_anterior, rango_completo_anterior

    inicio, fin = rango_completo_anterior(
        "Semana Actual", "2026-10-19 00:00:00", "2026-10-20 23:59:59"
    )
    assert inicio == "2026-10-12 00:00:00"
    assert fin == "2026-10-18 23:59:59"
    assert clave_anterior("week", "2026-10-21") == "2026-10-14"


def test_semana_pasada_no_se_llama_en_curso():
    from src.jefe.reportes.financiero.rotulos import nombres_comparacion

    assert nombres_comparacion("Semana p.") == ("Semana pasada", "Semana previa")
    assert nombres_comparacion("Semana Actual") == ("Semana en curso", "Semana pasada")
    assert titulo_serie("Semana p.") == "Ventas por semana"


def test_el_anio_se_reconoce_y_el_mes_dice_dia():
    assert es_anio("A\u00f1o actual")
    assert not es_anio("Mes Actual")
    assert titulo_serie("Mes Actual") == "Ventas por d\u00eda"
    assert ENCABEZADO_DIA[0] == "D\u00eda"
