import os
import tempfile
from datetime import datetime
import pytest

from src.config import config
from src.admin.mercadopago.historial.cuentas import (
    registrar_token_activo,
    asegurar_inicializacion,
    rango_activo_token_actual,
    nombre_cuenta_para_pago,
    es_pago_valido_en_periodo,
)
from src.admin.mercadopago.historial import archivo
from src.motor_auditoria_digital.cruces import snapshot, totales


@pytest.fixture(autouse=True)
def _no_pisa_la_config_real(monkeypatch):
    from src.admin.mercadopago.historial import cuentas as cuentas_mod

    cuentas_mod._INICIALIZADO = False
    monkeypatch.setattr(cuentas_mod, "_consultar_me_mp", lambda token: {})
    monkeypatch.setattr(config, "_load_config", lambda: None)
    claves = ("mp_tokens_historial", "mp_token_alias", "mp_access_token", "mp_user_id")
    antes = {clave: config.data.get(clave) for clave in claves}
    guardar = config.save
    config.save = lambda: None
    try:
        yield
    finally:
        config.save = guardar
        cuentas_mod._INICIALIZADO = False
        for clave, valor in antes.items():
            config.data[clave] = valor
        guardar()


def test_el_token_toma_el_nombre_y_parte_el_mes(monkeypatch):
    from src.admin.mercadopago.historial import cuentas as cuentas_mod

    def me(token):
        if "otra" in token:
            return {"id": 999001, "first_name": "Ana", "last_name": "Lopez"}
        return {"id": 680256868, "first_name": "Cristina", "last_name": "Baez"}

    monkeypatch.setattr(cuentas_mod, "_consultar_me_mp", me)
    config.set("mp_tokens_historial", [])
    config.set("mp_token_alias", "")
    config.set("mp_access_token", "")
    nom = registrar_token_activo("APP_USR-cris-token-123456789", alias="Marcianito")
    assert nom == "Cristina Baez"
    h = config.get("mp_tokens_historial")
    assert h[0]["nombre_real"] == "Cristina Baez"
    assert "Marcianito" in h[0]["alias_viejos"]
    nom2 = registrar_token_activo("APP_USR-otra-token-987654321", alias="Juanito")
    assert nom2 == "Ana Lopez"
    h2 = config.get("mp_tokens_historial")
    assert len(h2) == 2
    assert h2[0]["activo_hasta"] is not None
    assert h2[1]["nombre"] == "Ana Lopez"
    assert h2[1]["collector_id"] == "999001"
    h2[0]["activo_desde"] = "2026-10-01 00:00:00"
    h2[0]["activo_hasta"] = "2026-10-10 23:59:59"
    h2[1]["activo_desde"] = "2026-10-11 00:00:00"
    h2[1]["activo_hasta"] = None
    config.set("mp_tokens_historial", h2)
    assert nombre_cuenta_para_pago("", "2026-10-05 12:00:00", "Marcianito") == "Cristina Baez"
    assert nombre_cuenta_para_pago("", "2026-10-15 12:00:00", "Juanito") == "Ana Lopez"
    assert nombre_cuenta_para_pago("", "") == ""
    sin_id = snapshot._fila(
        fecha="2026-10-27 10:00:00",
        nombre="Venta QR",
        monto=100.0,
        estado="SIN FIRMAR",
        ticket_venta="1092035",
    )
    assert sin_id["cuenta"] == "—"
    assert not sin_id["id"]


def test_rotacion_cuentas_y_periodos(monkeypatch):
    # Probar que al registrar Juanito y luego Marcianito, los periodos se cierran y abren
    config.set("mp_tokens_historial", [])
    config.set("mp_token_alias", "")
    config.set("mp_access_token", "APP_USR-juanito-token-123456789")

    # 1. Registrar Juanito
    nom1 = registrar_token_activo("APP_USR-juanito-token-123456789", alias="Juanito", collector_id="111111")
    assert nom1 == "Juanito"
    h1 = config.get("mp_tokens_historial")
    assert len(h1) == 1
    assert h1[0]["nombre"] == "Juanito"
    assert h1[0]["activo_hasta"] is None

    # Simular que Juanito estuvo activo del 2026-10-01 al 2026-10-10
    h1[0]["activo_desde"] = "2026-10-01 00:00:00"
    config.set("mp_tokens_historial", h1)

    # 2. Registrar Marcianito
    nom2 = registrar_token_activo("APP_USR-marcianito-token-987654321", alias="Marcianito", collector_id="222222")
    assert nom2 == "Marcianito"
    h2 = config.get("mp_tokens_historial")
    assert len(h2) == 2
    assert h2[0]["activo_hasta"] is not None  # Juanito cerrado
    assert h2[1]["nombre"] == "Marcianito"
    assert h2[1]["activo_hasta"] is None

    # Asignar fecha de inicio fija para Marcianito
    h2[0]["activo_hasta"] = "2026-10-10 23:59:59"
    h2[1]["activo_desde"] = "2026-10-11 00:00:00"
    config.set("mp_tokens_historial", h2)

    # Validar resolucion de nombres
    assert nombre_cuenta_para_pago("111111", "2026-10-05 14:00:00") == "Juanito"
    assert nombre_cuenta_para_pago("222222", "2026-10-15 11:00:00") == "Marcianito"
    assert nombre_cuenta_para_pago("", "2026-10-05 14:00:00") == "Juanito"
    assert nombre_cuenta_para_pago("", "2026-10-15 11:00:00") == "Marcianito"

    # Validar periodos validos vs invalidos (ej: pagos de septiembre o fuera de fecha)
    assert es_pago_valido_en_periodo("2026-10-05 12:00:00", "111111") is True
    assert es_pago_valido_en_periodo("2026-10-15 12:00:00", "111111") is False  # Juanito no cobra el 15
    assert es_pago_valido_en_periodo("2026-10-05 12:00:00", "222222") is False  # Marcianito no cobraba el 5
    assert es_pago_valido_en_periodo("2026-10-15 12:00:00", "222222") is True
    assert es_pago_valido_en_periodo("2026-09-20 12:00:00") is False  # Antes de que existiera el TPV


def test_archivo_csv_con_cuenta(monkeypatch, tmp_path):
    csv_temp = str(tmp_path / "mercado_pago_sync.csv")
    monkeypatch.setattr(archivo, "RUTA", csv_temp)

    # Configurar historial con Juanito y Marcianito
    config.set("mp_tokens_historial", [
        {
            "token_prefix": "APP_USR-juan…",
            "collector_id": "111111",
            "nombre": "Juanito",
            "activo_desde": "2026-10-01 00:00:00",
            "activo_hasta": "2026-10-10 23:59:59",
        },
        {
            "token_prefix": "APP_USR-marc…",
            "collector_id": "222222",
            "nombre": "Marcianito",
            "activo_desde": "2026-10-11 00:00:00",
            "activo_hasta": None,
        }
    ])

    pagos = [
        {
            "id": "1001",
            "transaction_amount": 5000.0,
            "date_approved": "2026-10-05T10:00:00.000-03:00",
            "status": "approved",
            "collector_id": "111111",
            "cuenta_nombre": "Juanito",
        },
        {
            "id": "1002",
            "transaction_amount": 8500.0,
            "date_approved": "2026-10-15T15:30:00.000-03:00",
            "status": "approved",
            "collector_id": "222222",
            "cuenta_nombre": "Marcianito",
        },
        # Pago viejo no correspondiente al periodo activo (ej: 2026-08)
        {
            "id": "999",
            "transaction_amount": 1000.0,
            "date_approved": "2026-08-01T12:00:00.000-03:00",
            "status": "approved",
            "collector_id": "111111",
        }
    ]

    guardados = archivo.guardar(pagos)
    assert guardados == 3

    datos = archivo.leer()
    # El pago 999 de agosto debe ser descartado porque está fuera del periodo activo del TPV
    ids = [p["id"] for p in datos["pagos"]]
    assert "1001" in ids
    assert "1002" in ids
    assert "999" not in ids

    p1 = next(p for p in datos["pagos"] if p["id"] == "1001")
    assert p1["cuenta"] == "Juanito"
    p2 = next(p for p in datos["pagos"] if p["id"] == "1002")
    assert p2["cuenta"] == "Marcianito"


def test_snapshot_cuenta_y_totales(monkeypatch):
    # Validar que _fila incluye cuenta y totales excluye cancelados
    fila_j = snapshot._fila(
        fecha="2026-10-05 10:00:00",
        pago_id="1001",
        cuenta="Juanito",
        nombre="Venta QR",
        monto=5000.0,
        monto_mp=5000.0,
        neto=4800.0,
        monto_ticket=5000.0,
        estado="FIRMADO",
        ticket_venta="501",
    )
    assert fila_j["cuenta"] == "Juanito"

    fila_m = snapshot._fila(
        fecha="2026-10-15 15:30:00",
        pago_id="1002",
        cuenta="Marcianito",
        nombre="Venta QR",
        monto=8500.0,
        monto_mp=8500.0,
        neto=8200.0,
        monto_ticket=8500.0,
        estado="FIRMADO",
        ticket_venta="502",
    )
    assert fila_m["cuenta"] == "Marcianito"

    tot = totales.de_filas([fila_j, fila_m])
    assert tot["bruto"] == 13500.0
    assert tot["neto"] == 13000.0
    assert tot["tickets"] == 13500.0

    # Si se filtra solo Juanito:
    tot_j = totales.de_filas([f for f in [fila_j, fila_m] if f["cuenta"] == "Juanito"])
    assert tot_j["bruto"] == 5000.0
    assert tot_j["neto"] == 4800.0
