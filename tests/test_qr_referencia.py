from datetime import datetime, timedelta, timezone

from src.cajero.paso6_cobro.qr_en_cobro.pedido import (
    en_ventana,
    pago_aprobado,
    pago_de_orden,
)


def test_orden_del_ticket_anterior_no_cierra():
    vieja = {
        "external_reference": "ref-vieja",
        "order_status": "paid",
        "total_amount": 1500,
        "payments": [{"id": 9, "status": "approved", "transaction_amount": 1500}],
    }
    assert pago_de_orden(vieja, "ref-nueva", 1500) is None


def test_orden_sin_referencia_no_cierra_por_importe():
    pos = {
        "order_status": "paid",
        "total_amount": 800,
        "payments": [{"id": 3, "status": "approved", "transaction_amount": 800}],
    }
    assert pago_de_orden(pos, "uuid-de-este-ticket", 800) is None


def test_esta_referencia_si_cierra():
    actual = {
        "external_reference": "uuid-de-este-ticket",
        "order_status": "paid",
        "payments": [{"id": 11, "status": "approved", "transaction_amount": 800}],
    }
    pago = pago_de_orden(actual, "uuid-de-este-ticket", 800)
    assert pago and str(pago["id"]) == "11"


def test_pago_aprobado_sin_token_no_busca_por_importe():
    assert pago_aprobado("", "ref", 100) is None


def test_transferencia_de_hace_una_hora_queda_fuera():
    ahora = datetime.now(timezone.utc)
    pago = {
        "id": 1,
        "transaction_amount": 1500,
        "date_created": (ahora - timedelta(hours=1)).isoformat(),
    }
    assert en_ventana(pago, desde=ahora) is False


def test_transferencia_dentro_de_la_escucha_entra():
    ahora = datetime.now(timezone.utc)
    pago = {
        "id": 2,
        "transaction_amount": 1500,
        "date_created": (ahora - timedelta(seconds=20)).isoformat(),
    }
    assert en_ventana(pago, desde=ahora - timedelta(seconds=30)) is True


def test_transferencia_anterior_a_abrir_el_medio_queda_fuera():
    ahora = datetime.now(timezone.utc)
    pago = {
        "id": 3,
        "transaction_amount": 1500,
        "date_created": (ahora - timedelta(seconds=40)).isoformat(),
    }
    assert en_ventana(pago, desde=ahora) is False
