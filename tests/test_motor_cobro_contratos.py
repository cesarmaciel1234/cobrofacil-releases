"""Contratos del motor de cobro (sin BD ni Qt)."""
from src.cajero.paso6_cobro.motor_pagos.comandos.armar_venta import armar_resultado_venta
from src.cajero.paso6_cobro.motor_pagos.motor_principal import MotorPrincipalCobros
from src.utils.dinero import redondear_dinero, redondear_items_carrito


def test_redondeo_dos_decimales():
    assert redondear_dinero(99.999) == 100.0
    assert redondear_dinero(10.555) == 10.56
    items = redondear_items_carrito(
        [{"id": "1", "precio": 10.555, "cant": 2, "subtotal": 21.1100001}]
    )
    assert items[0]["precio"] == 10.56
    assert items[0]["subtotal"] == 21.11


def test_armar_redondea_vuelto_mixto():
    r = armar_resultado_venta({
        "metodo": "Mixto",
        "total_final": 100.001,
        "p1": 60.004,
        "p2": 50.0,
    })
    assert r["total"] == 100.0
    assert r["cambio"] == 10.0
    assert r["pago_efectivo"] == 60.0


def test_armar_guarda_cajero_auxiliar():
    r = armar_resultado_venta({
        "metodo": "Efectivo",
        "total_final": 100,
        "p1": 100,
        "p2": 0,
        "cajero": "caja1",
        "cajero_sec": "auxiliar1",
    })
    assert r["usuario_secundario"] == "auxiliar1"


def test_metodo_desconocido_se_rechaza():
    ok, msg = MotorPrincipalCobros.iniciar_transaccion("ChequeMagico", {"items_carrito": [{"id": 1}]})
    assert ok is False
    assert "no registrado" in msg.lower()


def test_stock_sigue_la_opcion(monkeypatch):
    from src.base_de_datos.repos.stock_descuento import descontar_stock
    from src.config import config
    from src.motor_inventario.unidad_medida import alcanza_stock

    class Cur:
        def __init__(self):
            self.sql = ""
            self.args = ()

        def execute(self, sql, args):
            self.sql = sql
            self.args = args

    monkeypatch.setitem(config.data, "opt_stock_negativo", False)
    cur = Cur()
    cur.rowcount = 1
    descontar_stock(cur, "10", 2)
    assert "stock >=" in cur.sql

    cur.rowcount = 0
    try:
        descontar_stock(cur, "10", 2)
        raise AssertionError("debia rechazar el stock")
    except Exception as e:
        assert type(e).__name__ == "SinStock"

    monkeypatch.setitem(config.data, "opt_stock_negativo", True)
    descontar_stock(cur, "10", 2)
    assert "stock >=" not in cur.sql
    assert cur.sql.strip().startswith("UPDATE")

    assert alcanza_stock(1, 2, False) is False
    assert alcanza_stock(1, 2, True) is True
    assert alcanza_stock(None, 5, False) is True


def test_token_lan_es_fijo(monkeypatch):
    from src.config import CLAVE_RED, config

    monkeypatch.setitem(config.data, "lan_api_token", "secreto-compartido")
    monkeypatch.setitem(config.data, "local_pin", "a" * 64)
    assert config.token_api_lan() == CLAVE_RED
    assert config.token_api_lan() == "1234"


def test_animacion_finished_se_puede_conectar():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.utils.qt_compat import VariantFloatAnimation

    anim = VariantFloatAnimation()
    visto = []
    anim.finished.connect(lambda: visto.append(1))
    anim.setDuration(1)
    anim.start()
    app.processEvents()
    anim.finished.emit()
    assert visto
