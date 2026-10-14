from src.cajero.paso6_cobro.qr_en_cobro.pedido import pago_de_orden
from src.cajero.paso6_cobro.transferencia_en_cobro.escucha import texto_enlazar


def test_orden_pos_cerrada_devuelve_pago():
    pago = pago_de_orden(
        {
            "external_reference": "ref-1",
            "order_status": "paid",
            "payments": [{"id": 99, "status": "approved", "transaction_amount": 1500}],
        },
        "ref-1",
    )
    assert pago["id"] == 99
    assert pago["transaction_amount"] == 1500


def test_orden_de_otro_ref_no_cierra():
    assert (
        pago_de_orden(
            {
                "external_reference": "otra",
                "order_status": "paid",
                "payments": [{"id": 1, "status": "approved"}],
            },
            "ref-1",
        )
        is None
    )


def test_orden_abierta_no_cierra():
    assert (
        pago_de_orden(
            {"external_reference": "ref-1", "status": "opened", "payments": []},
            "ref-1",
        )
        is None
    )


def test_orden_sin_ref_cierra_si_el_monto_es_el_mismo():
    pago = pago_de_orden(
        {
            "order_status": "paid",
            "total_amount": 1500,
            "payments": [{"id": 7, "status": "approved", "transaction_amount": 1500}],
        },
        "ref-1",
        1500,
    )
    assert pago["id"] == 7


def test_orden_cerrada_sin_lista_usa_id():
    pago = pago_de_orden(
        {"external_reference": "ref-1", "status": "closed", "id": 44, "total_amount": 200},
        "ref-1",
    )
    assert pago["id"] == 44
    assert pago["transaction_amount"] == 200


def test_texto_enlazar_pide_f9_o_esperar():
    texto = texto_enlazar(1500, destino="ticket")
    assert "1,500.00" in texto or "1.500,00" in texto or "1500" in texto
    assert "F9" in texto
    assert "monto exacto" in texto
