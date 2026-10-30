"""Cobertura de días y el pico viejo que no se compra."""

from datetime import date

from src.proveedor_global.frontend.predictiva.calendario.jornada import base, dias_cubiertos, preparar
from src.proveedor_global.frontend.predictiva.motor.calcular import definir, proyectar, ritmo_de
from src.proveedor_global.frontend.predictiva.motor.memoria import por_dia
from src.proveedor_global.frontend.predictiva.motor.feriados import es


def test_viernes_con_reparto_lunes_miercoles_viernes_cubre_dos_dias():
    proy = proyectar(date(2026, 10, 30), [0, 2, 4], 30 / 7, 0, "cajas", base())

    assert proy["entrega"] == date(2026, 11, 2)
    assert proy["prepara"] == date(2026, 11, 1)
    assert proy["dias"] == 2
    assert proy["pedir"] == 9


def test_el_lunes_a_la_tarde_cubre_media_jornada():
    datos = base()
    datos["turnos"] = {"0": "tarde"}

    assert dias_cubiertos(date(2026, 11, 2), date(2026, 11, 4), datos) == 1.5


def test_el_domingo_cerrado_no_se_vende_y_se_prepara_el_sabado():
    datos = base()
    datos["abiertos"] = [0, 1, 2, 3, 4, 5]
    datos["turnos"] = {"4": "tarde"}

    assert dias_cubiertos(date(2026, 10, 30), date(2026, 11, 2), datos) == 1.5
    assert preparar(date(2026, 11, 2), datos) == date(2026, 10, 31)


def test_un_sabado_corto_pesa_menos_que_la_jornada():
    datos = base()
    datos["horarios"] = {"5": {"modo": "corrido", "abre": "08:00", "cierra": "13:00"}}

    assert dias_cubiertos(date(2026, 10, 31), date(2026, 11, 1), datos) == 5 / 12


def test_el_doble_turno_de_la_tarde_solo_cuenta_el_segundo():
    datos = base()
    datos["modo"] = "doble"
    datos["abre"] = "08:00"
    datos["cierra"] = "13:00"
    datos["turno2_abre"] = "17:00"
    datos["turno2_cierra"] = "21:00"
    datos["turnos"] = {"0": "tarde"}

    assert dias_cubiertos(date(2026, 11, 2), date(2026, 11, 4), datos) == 1 + (4 / 9)


def test_en_cero_el_fin_de_semana_mas_el_lunes_a_la_manana_es_10_a_12():
    from src.proveedor_global.frontend.predictiva.calendario.jornada import hasta_el_camion
    from src.proveedor_global.frontend.predictiva.motor.calcular import rango

    datos = base()
    datos["modo"] = "doble"

    dias = hasta_el_camion(date(2026, 10, 31), date(2026, 11, 2), datos)

    assert dias == 2.5
    assert rango(dias, 0, 3, 5) == (10, 12)
    assert rango(dias, 5, 3, 5) == (5, 7)


def test_el_feriado_no_cuenta_como_dia_de_venta():
    assert dias_cubiertos(date(2026, 12, 7), date(2026, 12, 10), base()) == 2


def test_feriado_del_8_de_diciembre_no_reparte():
    assert es(date(2026, 12, 8))
    assert es(date(2026, 12, 25))


def test_el_sistema_separa_el_pico_del_maximo_historico():
    banda = definir([1, 1, 2, 10])

    assert banda["listo"]
    assert banda["pico"] == 10
    assert banda["minimo"] == 1
    assert banda["maximo"] == 2


def test_con_una_sola_venta_no_define_la_banda():
    assert definir([10])["listo"] is False


def test_una_carga_no_entra_en_el_pico():
    ventas = por_dia(
        [
            {"fecha": "2026-10-01", "pollo": 10},
            {"fecha": "2026-10-02", "pollo": 8},
            {"fecha": "2026-10-03", "pollo": 20},
            {"fecha": "2026-10-05", "pollo": 17},
        ],
        "pollo",
    )

    assert ventas == [2, 1.5]


def test_la_venta_reciente_baja_el_maximo_y_no_pasa_el_piso():
    ritmo, origen = ritmo_de(30 / 7, 20 / 7, [2, 2, 2])

    assert origen == "venta reciente"
    assert ritmo == 20 / 7
