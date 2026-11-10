from datetime import datetime
from decimal import Decimal

from src.clientes_fiado.oficina.cuenta.interes import (
    descripcion_interes,
    descripcion_reverso,
    proyectar_interes,
)


def _mov(mov_id, fecha, tipo, monto, venta_id=None, descripcion=""):
    return {
        "id": mov_id,
        "fecha": fecha,
        "tipo": tipo,
        "monto": monto,
        "venta_id": venta_id,
        "descripcion": descripcion,
    }


def test_tasa_mensual_se_prorratea_por_dia_y_no_es_retroactiva():
    activacion = datetime(2026, 1, 1)
    movimientos = [
        _mov(1, "2025-01-01 10:00:00", "CARGO", 1000, 7, "Ticket viejo"),
    ]

    resultado = proyectar_interes(
        movimientos,
        activacion,
        datetime(2026, 1, 16),
        tasa_base=Decimal('0.03'),
    )

    ticket = resultado["tickets"]["V:7"]
    assert ticket["dias"] == 15
    assert ticket["interes_acumulado"] == 15
    assert resultado["interes_acumulado"] == 15


def test_abono_cubre_interes_antes_del_capital_y_no_compone():
    activacion = datetime(2026, 1, 1)
    venta = _mov(1, "2026-01-01 00:00:00", "CARGO", 1000, 7)
    fecha_interes = datetime(2026, 1, 31)
    primer_calculo = proyectar_interes([venta], activacion, fecha_interes, tasa_base=Decimal('0.03'))
    detalle = {"V:7": Decimal("30")}
    cargo_interes = _mov(
        2,
        fecha_interes.strftime("%Y-%m-%d %H:%M:%S"),
        "CARGO",
        30,
        descripcion=descripcion_interes(detalle),
    )
    abono = _mov(3, fecha_interes, "ABONO", 10)
    resultado = proyectar_interes(
        [venta, cargo_interes, abono],
        activacion,
        datetime(2026, 3, 2),
        tasa_base=Decimal('0.03'),
        tasa_apal=0,
    )

    ticket = resultado["tickets"]["V:7"]
    assert primer_calculo["interes_acumulado"] == 30
    assert ticket["capital_pendiente"] == 1000
    assert ticket["interes_en_saldo"] == 20
    assert ticket["interes_pagado"] == 10
    assert ticket["interes_acumulado"] == 30


def test_fifo_de_tickets_reduce_primero_el_mas_antiguo():
    activacion = datetime(2026, 1, 20)
    movimientos = [
        _mov(1, "2026-01-01 00:00:00", "CARGO", 100, 7),
        _mov(2, "2026-01-11 00:00:00", "CARGO", 200, 8),
        _mov(3, "2026-01-20 00:00:00", "ABONO", 150),
    ]

    resultado = proyectar_interes(
        movimientos,
        activacion,
        datetime(2026, 1, 20),
    )

    assert resultado["tickets"]["V:7"]["capital_pendiente"] == 0
    assert resultado["tickets"]["V:8"]["capital_pendiente"] == 150
    assert resultado["tickets"]["V:8"]["dias"] == 0


def test_cancelar_ticket_reversa_interes_ya_cobrado():
    activacion = datetime(2026, 1, 1)
    ticket = _mov(1, "2026-01-01 00:00:00", "CARGO", 1000, 7)
    fecha_cargo = "2026-01-31 00:00:00"
    interes = _mov(
        2,
        fecha_cargo,
        "CARGO",
        30,
        descripcion=descripcion_interes({"V:7": Decimal("30")}),
    )
    abono = _mov(3, fecha_cargo, "ABONO", 30)
    reverso_desc = "Ticket cancelado #7" + descripcion_reverso("V:7", Decimal("30"))
    anulacion = _mov(4, "2026-02-01 00:00:00", "ANULACION", 1030, 7, reverso_desc)

    resultado = proyectar_interes(
        [ticket, interes, abono, anulacion],
        activacion,
        datetime(2026, 2, 1),
    )

    assert resultado["tickets"] == {}
    assert resultado["interes_acumulado"] == 0


def test_escalado_apalancamiento_aplica_despues_de_dias_plazo():
    activacion = datetime(2026, 1, 1)
    ticket = _mov(1, "2026-01-01 00:00:00", "CARGO", 1000, 7)

    # 15 días: tasa base 3% mensual -> $15.00
    res_15d = proyectar_interes(
        [ticket],
        activacion,
        datetime(2026, 1, 16),
        tasa_base=Decimal("0.03"),
        tasa_apal=Decimal("0.05"),
        dias_plazo=15,
    )
    assert res_15d["tickets"]["V:7"]["interes_acumulado"] == 15.0
    assert res_15d["tickets"]["V:7"]["en_apalancamiento"] is False

    # 25 días (15 base + 10 apalancados al 8%): 15 + 26.67 = 41.67
    res_25d = proyectar_interes(
        [ticket],
        activacion,
        datetime(2026, 1, 26),
        tasa_base=Decimal("0.03"),
        tasa_apal=Decimal("0.05"),
        dias_plazo=15,
    )
    assert res_25d["tickets"]["V:7"]["interes_acumulado"] == 41.67
    assert res_25d["tickets"]["V:7"]["en_apalancamiento"] is True


def test_cargo_manual_sin_ticket_genera_interes():
    activacion = datetime(2026, 1, 1)
    cargo_manual = _mov(50, "2026-01-01 10:00:00", "CARGO", 2000, venta_id=None, descripcion="Cargo manual desde panel Admin")
    resultado = proyectar_interes([cargo_manual], activacion, datetime(2026, 1, 16), tasa_base=Decimal('0.03'))
    assert "M:50" in resultado["tickets"]
    cargo_calc = resultado["tickets"]["M:50"]
    assert cargo_calc["dias"] == 15
    assert cargo_calc["interes_acumulado"] == 30.0
    assert resultado["interes_acumulado"] == 30.0


def test_abono_sin_cargo_interes_mensual_y_reinicio_conteo_diario():
    """Un abono reduce directo el capital y el saldo remanente arranca su conteo diario."""
    activacion = datetime(2026, 1, 1)
    venta = _mov(1, "2026-01-01 10:00:00", "CARGO", 1000, 7)
    abono = _mov(2, "2026-01-20 10:00:00", "ABONO", 400)

    # 1. Al día del abono (2026-01-20), el capital restante es 600 y los días e interés arrancan en 0
    res_abono = proyectar_interes(
        [venta, abono],
        activacion,
        datetime(2026, 1, 20, 10, 0, 0),
        tasa_base=Decimal("0.03"),
        tasa_apal=Decimal("0.05"),
        dias_plazo=30,
    )
    t_abono = res_abono["tickets"]["V:7"]
    assert t_abono["capital_pendiente"] == 600.0
    assert t_abono["dias"] == 0
    assert t_abono["interes_acumulado"] == 0.0

    # 2. 10 días después del abono (2026-01-30), corre el conteo diario sobre el saldo vivo ($600 * 0.1% * 10 = $6.00)
    res_10d = proyectar_interes(
        [venta, abono],
        activacion,
        datetime(2026, 1, 30, 10, 0, 0),
        tasa_base=Decimal("0.03"),
        tasa_apal=Decimal("0.05"),
        dias_plazo=30,
    )
    t_10d = res_10d["tickets"]["V:7"]
    assert t_10d["capital_pendiente"] == 600.0
    assert t_10d["dias"] == 10
    assert t_10d["interes_acumulado"] == 6.0
