from src.clientes_fiado.oficina.consulta_historial.motor import armar_fila, MotorConsultaHistorial


def test_abono_lleva_ticket_cobro():
    fila = armar_fila((98, "2026-10-14 03:29:25", "ABONO", 100, 0, "Cajero (QR: F9 MANUAL)", None))
    assert fila["referencia"] == "COB-98"
    assert fila["tipo"] == "ABONO"


def test_cargo_borrado_sigue_en_el_historial():
    fila = armar_fila({
        "id": 7,
        "fecha": "2026-10-14 03:29:27",
        "tipo": "CARGO",
        "monto": 100,
        "saldo_resultante": 100,
        "descripcion": "BORRADO · Venta a crédito ticket #1090093",
        "venta_id": 1090093,
    })
    assert fila["borrado"] is True
    assert fila["etiqueta"] == "CARGO · BORRADO"
    assert fila["referencia"] == "#1090093"
    assert "historial" in fila["linea"]


def test_ticket_cancelado_en_f3_queda_en_la_cuenta():
    fila = armar_fila({
        "id": 4,
        "fecha": "2026-10-14 00:40:00",
        "tipo": "CARGO",
        "monto": 100,
        "saldo_resultante": 0,
        "descripcion": "CANCELADO · Venta a crédito ticket #1090093",
        "venta_id": 1090093,
    })
    assert fila["cancelado"] is True
    assert fila["etiqueta"] == "CARGO · CANCELADO"
    assert fila["referencia"] == "#1090093"
    anul = armar_fila({
        "id": 5,
        "tipo": "ANULACION",
        "monto": 100,
        "descripcion": "Ticket cancelado #1090093 (F3)",
        "venta_id": 1090093,
    })
    assert anul["etiqueta"] == "TICKET CANCELADO"


def test_consulta_no_tira_si_el_libro_falla(monkeypatch):
    def rompe(_self, _cid):
        raise RuntimeError("base caída")

    monkeypatch.setattr(
        "src.clientes_fiado.oficina.cuenta.motor.MotorCuenta.movimientos",
        rompe,
    )
    assert MotorConsultaHistorial().movimientos(1) == []
