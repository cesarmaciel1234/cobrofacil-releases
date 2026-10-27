"""El Point solo cuenta como enviado cuando ya muestra el monto."""

from src.cajero.paso6_cobro.tarjeta_en_cobro.envio import clasificar_estado, enviar_monto


class _Resp:
    def __init__(self, code, data):
        self.status_code = code
        self._data = data

    def json(self):
        return self._data


def test_clasificar_estado_del_point():
    assert clasificar_estado("processed") == "FINISHED"
    assert clasificar_estado("at_terminal") == "AT_TERMINAL"
    assert clasificar_estado("created") == "CREATED"
    assert clasificar_estado("canceled") == "CANCELED"
    assert clasificar_estado("") == ""


def test_enviar_cuando_el_point_ya_muestra(monkeypatch):
    llamadas = []

    def post(url, payload, token, timeout=10, extra_headers=None):
        llamadas.append(url)
        return _Resp(201, {"id": "ORD1", "status": "at_terminal"})

    monkeypatch.setattr(
        "src.cajero.paso6_cobro.tarjeta_en_cobro.envio.mandar.MPApiClient.post",
        post,
    )
    pedido = enviar_monto("token", "NEWLAND_N950__X", 20)
    assert pedido["ok"] is True
    assert pedido["intent"] == "ORD1"
    assert llamadas == ["https://api.mercadopago.com/v1/orders"]


def test_espera_y_sigue_cuando_pasa_a_la_terminal(monkeypatch):
    monkeypatch.setattr(
        "src.cajero.paso6_cobro.tarjeta_en_cobro.envio.mandar.time.sleep",
        lambda _s: None,
    )
    monkeypatch.setattr(
        "src.cajero.paso6_cobro.tarjeta_en_cobro.envio.mandar.MPApiClient.post",
        lambda *a, **k: _Resp(201, {"id": "ORD2", "status": "created"}),
    )
    lecturas = {"n": 0}

    def get(url, token, timeout=10):
        lecturas["n"] += 1
        estado = "created" if lecturas["n"] == 1 else "at_terminal"
        return _Resp(200, {"status": estado, "transactions": {"payments": [{"amount": "20.00"}]}})

    monkeypatch.setattr(
        "src.cajero.paso6_cobro.tarjeta_en_cobro.envio.estado.MPApiClient.get",
        get,
    )
    pedido = enviar_monto("token", "NEWLAND_N950__X", 20)
    assert pedido["ok"] is True
    assert lecturas["n"] == 2


def test_cancela_si_la_cuenta_no_es_la_del_point(monkeypatch):
    monkeypatch.setattr(
        "src.cajero.paso6_cobro.tarjeta_en_cobro.envio.mandar.time.sleep",
        lambda _s: None,
    )
    posts = []

    def post(url, payload, token, timeout=10, extra_headers=None):
        posts.append(url)
        return _Resp(201, {"id": "ORD3", "status": "created"})

    monkeypatch.setattr(
        "src.cajero.paso6_cobro.tarjeta_en_cobro.envio.mandar.MPApiClient.post",
        post,
    )
    monkeypatch.setattr(
        "src.cajero.paso6_cobro.tarjeta_en_cobro.envio.soltar.MPApiClient.post",
        post,
    )
    monkeypatch.setattr(
        "src.cajero.paso6_cobro.tarjeta_en_cobro.envio.estado.MPApiClient.get",
        lambda *a, **k: _Resp(200, {"status": "created", "transactions": {"payments": []}}),
    )
    pedido = enviar_monto("token", "NEWLAND_N950__X", 20)
    assert pedido == {"ok": False, "motivo": "otra_cuenta"}
    assert posts[-1].endswith("/ORD3/cancel")
