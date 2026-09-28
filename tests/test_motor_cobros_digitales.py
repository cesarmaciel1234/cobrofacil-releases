"""Motor de cobros digitales (sin BD real ni red)."""
from datetime import datetime, timedelta
from urllib.parse import unquote

import pytest

from src.motor_cobros_digitales.bajada import mp as bajada
from src.motor_cobros_digitales.enlace import automatico
from src.motor_cobros_digitales.enlace.automatico import parejas
from src.motor_cobros_digitales.libro import tabla
from src.motor_cobros_digitales.veredicto.conciliar import _clase, _rango

T0 = datetime(2026, 9, 26, 12, 0, 0)


def m(minutos):
    return T0 + timedelta(minutes=minutos)


class _Marcas(dict):
    def leer(self, clave):
        return self.get(clave, "")

    def poner(self, clave, valor):
        self[clave] = valor
        return True


@pytest.fixture
def marcas(monkeypatch):
    libro = _Marcas()
    monkeypatch.setattr(tabla, "crear", lambda: True)
    monkeypatch.setattr(tabla, "leer_marca", libro.leer)
    monkeypatch.setattr(tabla, "poner_marca", libro.poner)
    return libro


# ---------- enlace automático ----------

def test_enlace_exacto():
    assert parejas([("101", m(0), 5000.0)], [("P1", m(1), 5000.0)]) == [("P1", "101")]


def test_enlace_tolera_un_centavo():
    assert parejas([("101", m(0), 5000.0)], [("P1", m(1), 5000.01)]) == [("P1", "101")]


def test_monto_distinto_no_enlaza():
    assert parejas([("101", m(0), 5000.0)], [("P1", m(1), 5001.0)]) == []


def test_mas_de_diez_minutos_no_enlaza():
    assert parejas([("101", m(0), 5000.0)], [("P1", m(11), 5000.0)]) == []


def test_empate_no_enlaza():
    assert parejas([("101", m(0), 5000.0)], [("P1", m(2), 5000.0), ("P2", m(-2), 5000.0)]) == []


def test_dos_ventas_mismo_monto_cada_una_su_pago():
    got = parejas(
        [("101", m(0), 800.0), ("102", m(6), 800.0)],
        [("P1", m(1), 800.0), ("P2", m(7), 800.0)],
    )
    assert sorted(got) == [("P1", "101"), ("P2", "102")]


def test_un_pago_para_dos_ventas_solo_la_mas_cercana():
    assert parejas([("101", m(0), 800.0), ("102", m(3), 800.0)], [("P1", m(1), 800.0)]) == [("P1", "101")]


def test_desde_marca(marcas):
    ahora = datetime(2026, 9, 26, 20, 0, 0)
    assert automatico.desde_marca(ahora) == ahora - timedelta(days=3)
    marcas["mp_historial_desde"] = "2026-09-01 00:00:00"
    assert automatico.desde_marca(ahora) == datetime(2026, 9, 1)
    marcas["mp_enlace_hasta"] = "2026-09-20 10:00:00"
    assert automatico.desde_marca(ahora) == datetime(2026, 9, 19, 10, 0, 0)


def _enlace_falso(monkeypatch, ventas, pagos, firmar_ok=True):
    pedidos = {}
    monkeypatch.setattr(automatico, "_ventas_sin_firma", lambda d: pedidos.setdefault("ventas", d) and ventas)
    monkeypatch.setattr(automatico, "_pagos_sueltos", lambda d: pedidos.setdefault("pagos", d) and pagos)
    firmados = []
    monkeypatch.setattr(tabla, "firmar_motor", lambda p: firmados.extend(p) or firmar_ok)
    return pedidos, firmados


def test_enlazar_retoma_desde_la_marca_y_la_corre(monkeypatch, marcas):
    marcas["mp_enlace_hasta"] = "2026-09-10 08:00:00"
    marcas["mp_historial_hasta"] = "2026-09-26 19:00:00"
    pedidos, firmados = _enlace_falso(monkeypatch, [("101", m(0), 100.0)], [("P1", m(1), 100.0)])
    assert automatico.enlazar() == 1
    assert pedidos["ventas"] == "2026-09-09"
    assert firmados == [("P1", "101")]
    assert marcas["mp_enlace_hasta"] == "2026-09-26 19:00:00"


def test_enlazar_si_falla_no_corre_la_marca(monkeypatch, marcas):
    marcas["mp_enlace_hasta"] = "2026-09-10 08:00:00"
    marcas["mp_historial_hasta"] = "2026-09-26 19:00:00"
    _enlace_falso(monkeypatch, [("101", m(0), 100.0)], [("P1", m(1), 100.0)], firmar_ok=False)
    assert automatico.enlazar() == -1
    assert marcas["mp_enlace_hasta"] == "2026-09-10 08:00:00"


def test_enlazar_sin_bajada_no_corre_la_marca(monkeypatch, marcas):
    _enlace_falso(monkeypatch, [], [])
    assert automatico.enlazar() == 0
    assert "mp_enlace_hasta" not in marcas


def test_marca_de_enlace_nunca_va_para_atras(marcas):
    marcas["mp_enlace_hasta"] = "2026-09-26 19:00:00"
    marcas["mp_historial_hasta"] = "2026-09-20 10:00:00"
    automatico._correr_marca()
    assert marcas["mp_enlace_hasta"] == "2026-09-26 19:00:00"


# ---------- libro ----------

def test_fila_guarda_el_pago_completo():
    pago = {
        "id": 123, "collector_id": 77, "transaction_amount": 1500, "status": "approved",
        "date_approved": "2026-09-26T10:00:00.000-04:00", "date_created": "2026-09-26T09:59:00.000-04:00",
        "payment_type_id": "credit_card", "installments": 3,
        "card": {"last_four_digits": "4321"}, "payer": {"first_name": "José 😀", "identification": {"number": "20111222"}},
    }
    fila = dict(zip(tabla.COLUMNAS, tabla._fila(pago)))
    assert fila["payment_id"] == "123"
    assert fila["fecha"] == "2026-09-26 11:00:00"
    assert fila["crudo"].isascii()
    assert fila["cliente"] == "José"
    import json
    assert json.loads(fila["crudo"]) == pago


def test_venta_id():
    assert tabla.venta_id("1089793") == 1089793
    assert tabla.venta_id(" 42 ") == 42
    assert tabla.venta_id("") is None
    assert tabla.venta_id("T-12") is None


@pytest.mark.parametrize("pago, op, canal", [
    ({"payment_type_id": "bank_transfer"}, "transferencia", "Transferencia"),
    ({"point_of_interaction": {"type": "INSTORE"}, "payment_type_id": "credit_card"}, "regular_payment", "QR"),
    ({"point_of_interaction": {"type": "POINT"}}, "pos_payment", "Tarjeta"),
    ({"payment_type_id": "debit_card"}, "regular_payment", "Tarjeta"),
    ({"payment_type_id": "account_money"}, "regular_payment", "QR"),
    ({"payment_type_id": "ticket"}, "regular_payment", "Otro"),
])
def test_canal(pago, op, canal):
    assert tabla._canal(pago, op) == canal


# ---------- veredicto ----------

@pytest.mark.parametrize("fila, clase", [
    ({"payment_id": None, "estado": None, "metodo_pago": "QR", "canal": None}, "sin_cobro"),
    ({"payment_id": "P", "estado": "", "metodo_pago": "QR", "canal": None}, "pendiente"),
    ({"payment_id": "P", "estado": "refunded", "metodo_pago": "QR", "canal": "QR"}, "devuelto"),
    ({"payment_id": "P", "estado": "approved", "metodo_pago": "Tarjeta", "canal": "Transferencia"}, "otro_medio"),
    ({"payment_id": "P", "estado": "approved", "metodo_pago": "Mixto", "canal": "Transferencia"}, "verdadero"),
    ({"payment_id": "P", "estado": "approved", "metodo_pago": "QR", "canal": "QR"}, "verdadero"),
    ({"payment_id": "P", "estado": "approved", "metodo_pago": "QR", "canal": "QR", "venta_estado": "CANCELADA"}, "cancelada"),
    ({"payment_id": None, "estado": None, "metodo_pago": "QR", "canal": None, "venta_estado": "CANCELADA"}, "cancelada"),
])
def test_clase(fila, clase):
    assert _clase(fila) == clase


def test_rango_incluye_el_ultimo_dia():
    assert _rango("2026-09-01", "2026-09-30") == ("2026-09-01", "2026-10-01")
    assert _rango("2026-12-31", "2026-12-31") == ("2026-12-31", "2027-01-01")


# ---------- bajada ----------

class _Resp:
    def __init__(self, code, data):
        self.status_code = code
        self._data = data

    def json(self):
        return self._data


@pytest.fixture
def mp_falso(monkeypatch, marcas):
    guardados, ventanas = [], []
    monkeypatch.setattr(tabla, "guardar", lambda p: guardados.extend(p) or len(p))
    monkeypatch.setattr(bajada, "_al_monitor", lambda p, mes: None)
    monkeypatch.setattr(bajada.time, "sleep", lambda s: None)
    bajada._cuentas.clear()

    def get(url, headers=None, timeout=0, verify=True):
        if "users/me" in url:
            return _Resp(200, {"id": 77})
        ventanas.append(unquote(url))
        n = len(ventanas)
        return _Resp(200, {"results": [
            {"id": f"A{n}", "collector_id": 77, "transaction_amount": 100, "status": "approved"},
            {"id": f"B{n}", "collector_id": 12, "transaction_amount": 100, "status": "approved"},
            {"id": f"C{n}", "collector_id": 77, "transaction_amount": 0, "status": "approved"},
        ]})

    monkeypatch.setattr(bajada.requests, "get", get)
    return guardados, ventanas


def test_bajada_recorre_dias_y_filtra(mp_falso, marcas):
    guardados, ventanas = mp_falso
    marcas["mp_historial_hasta"] = (datetime.now() - timedelta(days=2, hours=3)).strftime("%Y-%m-%d %H:%M:%S")
    total = bajada.ponerse_al_dia("TOKEN")
    assert total == len(ventanas) == 3
    assert all(p["collector_id"] == 77 and p["transaction_amount"] > 0 for p in guardados)
    assert all("range=date_last_updated" in u and "end_date=" in u for u in ventanas)
    assert marcas["mp_historial_hasta"][:13] == datetime.now().strftime("%Y-%m-%d %H")


def test_bajada_primera_vez_arranca_el_dia_uno(mp_falso, marcas):
    bajada.ponerse_al_dia("TOKEN")
    assert marcas["mp_historial_desde"] == datetime.now().strftime("%Y-%m-01 00:00:00")


def test_bajada_mp_caido_no_mueve_la_marca(monkeypatch, mp_falso, marcas):
    marcas["mp_historial_hasta"] = "2026-09-26 10:00:00"
    monkeypatch.setattr(
        bajada.requests, "get",
        lambda url, **k: _Resp(200, {"id": 77}) if "users/me" in url else _Resp(500, {}),
    )
    assert bajada.ponerse_al_dia("TOKEN") == -1
    assert marcas["mp_historial_hasta"] == "2026-09-26 10:00:00"


def test_bajada_forzada_no_mueve_la_marca_para_atras(mp_falso, marcas):
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    marcas["mp_historial_hasta"] = ahora
    bajada.ponerse_al_dia("TOKEN", desde=datetime.now() - timedelta(days=2))
    assert marcas["mp_historial_hasta"] >= ahora


def test_bajada_sin_token():
    assert bajada.ponerse_al_dia("") == 0
