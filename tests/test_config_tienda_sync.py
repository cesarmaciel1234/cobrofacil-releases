"""Pruebas de única fuente de verdad (Maestra -> Esclavas), nota de cargo manual y heartbeat PID."""

from __future__ import annotations

import json
import os
import threading
import time
from http.server import ThreadingHTTPServer

from src.central_red_global import lan_server
from src.central_red_global.sync_tienda.config_tienda import tienda as cfg_tienda
from src.config import config


def _aislar_config(monkeypatch, tmp_path, filename="config.json", inicial=None):
    ruta = tmp_path / filename
    data = {
        **config.DEFAULT_CONFIG,
        "business_name": "Carnicería Original",
        "fiado_mantenimiento_pct": 3.0,
        "fiado_apalancamiento_pct": 5.0,
        "fiado_plazo_dias": 30,
        "tienda_config_version": 1,
        **(inicial or {}),
    }
    ruta.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(config, "config_path", str(ruta))
    monkeypatch.setattr(config, "data", dict(data))
    monkeypatch.setattr(config, "_last_mtime", os.path.getmtime(ruta))
    monkeypatch.setattr(config, "_no_guardar", False, raising=False)
    return ruta


def test_esclava_envia_a_maestra_y_todas_sincronizan(tmp_path, monkeypatch):
    # Estado de la Maestra (persistido por separado para simular 3 PCs en el test)
    maestra_state = {
        "version": 1,
        "updated_at": time.time(),
        "updated_by": "PC-MAESTRA",
        "values": {
            "business_name": "Carnicería Original",
            "fiado_mantenimiento_pct": 3.0,
            "fiado_apalancamiento_pct": 5.0,
            "fiado_plazo_dias": 30,
        },
    }

    def fake_leer_maestra():
        return dict(maestra_state)

    def fake_aplicar_maestra(cambios, origen=""):
        limpios = cfg_tienda.sanitizar_cambios(cambios)
        if not limpios:
            return False, {}, "Sin cambios válidos"
        maestra_state["version"] += 1
        maestra_state["updated_at"] = time.time()
        maestra_state["updated_by"] = origen or "MAESTRA"
        maestra_state["values"] = {**maestra_state["values"], **limpios}
        return True, dict(maestra_state), ""

    monkeypatch.setattr(cfg_tienda, "leer_estado_maestra", fake_leer_maestra)
    monkeypatch.setattr(cfg_tienda, "aplicar_en_maestra", fake_aplicar_maestra)
    monkeypatch.setattr(cfg_tienda, "leer_version_local", lambda: maestra_state["version"])

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), lan_server.LANRequestHandler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    try:
        from src.central_red_global.sync_tienda import rol

        monkeypatch.setattr(rol, "url_maestra", lambda path, host=None: f"http://127.0.0.1:{port}{path}")
        monkeypatch.setattr(rol, "es_esta_pc", lambda host: False)
        monkeypatch.setattr(cfg_tienda, "_es_rol_maestra_real", lambda: False)
        monkeypatch.setattr(cfg_tienda, "_host_maestra_activo", lambda: "192.168.0.8")

        # 1) Esclava 1 modifica interés + nombre -> envía a Maestra -> Maestra acepta (v2)
        ruta_esclava1 = _aislar_config(monkeypatch, tmp_path, "esclava1.json")
        ok, err = cfg_tienda.guardar_y_sincronizar({
            "fiado_mantenimiento_pct": 4.5,
            "fiado_plazo_dias": 45,
            "business_name": "Carnicería Nueva",
        })
        assert ok is True, err
        assert err == ""
        assert maestra_state["version"] == 2
        saved1 = json.loads(ruta_esclava1.read_text(encoding="utf-8"))
        assert saved1["fiado_mantenimiento_pct"] == 4.5
        assert saved1["fiado_plazo_dias"] == 45
        assert saved1["business_name"] == "Carnicería Nueva"
        assert saved1["tienda_config_version"] == 2

        # 2) Esclava 2 arranca desactualizada (v1) -> sincroniza desde Maestra -> queda en v2
        ruta_esclava2 = _aislar_config(monkeypatch, tmp_path, "esclava2.json")
        changed = cfg_tienda.sincronizar_desde_maestra()
        assert changed is True
        saved2 = json.loads(ruta_esclava2.read_text(encoding="utf-8"))
        assert saved2["fiado_mantenimiento_pct"] == 4.5
        assert saved2["fiado_plazo_dias"] == 45
        assert saved2["business_name"] == "Carnicería Nueva"
        assert saved2["tienda_config_version"] == 2
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_esclava_offline_no_diverge_local(tmp_path, monkeypatch):
    ruta = _aislar_config(monkeypatch, tmp_path, "esclava_offline.json")
    monkeypatch.setattr(cfg_tienda, "_es_rol_maestra_real", lambda: False)
    monkeypatch.setattr(cfg_tienda, "_host_maestra_activo", lambda: "")

    ok, msg = cfg_tienda.guardar_y_sincronizar({"fiado_mantenimiento_pct": 9.0, "business_name": "Otro"})
    assert ok is False
    assert "Maestra" in msg
    # El config.json local queda intacto
    saved = json.loads(ruta.read_text(encoding="utf-8"))
    assert saved["fiado_mantenimiento_pct"] == 3.0
    assert saved["business_name"] == "Carnicería Original"


def test_guardar_politicas_credito_detalle_con_reload(tmp_path, monkeypatch):
    from src.clientes_fiado.cerebro.cerebro import cerebro

    _aislar_config(monkeypatch, tmp_path, "maestra_politicas.json")
    monkeypatch.setattr(cfg_tienda, "_es_rol_maestra_real", lambda: True)
    monkeypatch.setattr(cfg_tienda, "_persistir_en_mariadb", lambda _estado: True)
    monkeypatch.setattr(cfg_tienda, "_leer_de_mariadb", lambda: None)
    monkeypatch.setattr(cfg_tienda, "_notificar_cambio_a_esclavas", lambda _v: None)

    ok, err = cerebro.guardar_politicas_credito_detalle(6.5, 2.0, 20)
    assert ok is True
    assert err == ""
    assert cerebro.mantenimiento_pct() == 6.5
    assert cerebro.apalancamiento_pct() == 2.0
    assert cerebro.plazo_dias_politica() == 20


def test_cargar_manual_pasa_nota_editable(monkeypatch):
    from src.clientes_fiado.cerebro.cerebro import cerebro

    llamados = []

    def fake_cargar_manual(cid, monto, desc):
        llamados.append((cid, monto, desc))
        return True, 15000.0, "Antonio Pan"

    monkeypatch.setattr(cerebro.cuenta, "cargar_manual", fake_cargar_manual)
    ok, saldo, nombre = cerebro.cargar_manual(10, 5000.0, "Ajuste por cobro duplicado COB-123")
    assert ok is True
    assert saldo == 15000.0
    assert nombre == "Antonio Pan"
    assert llamados == [(10, 5000.0, "Ajuste por cobro duplicado COB-123")]


def test_esclava_heartbeat_ignora_pid_ajeno_o_previo(tmp_path, monkeypatch):
    from src.central_red_global.servidor.oficio import agente

    hb = tmp_path / "esclava_heartbeat.txt"
    monkeypatch.setattr(agente, "_esclava_heartbeat_path", lambda: str(hb))

    # Archivo viejo de otro PID (999999) mientras corre PID 4242 -> NO debe marcar espejo apagado
    hb.write_text("1000.0|999999", encoding="utf-8")
    viejo = time.time() - 600
    os.utime(hb, (viejo, viejo))
    monkeypatch.setattr("src.utils.candados.get_store_server_pid", lambda: 4242)
    assert agente.esclava_heartbeat_fresco(max_age_sec=180.0) is True

    # Archivo vencido del MISMO PID vivo 4242 -> SÍ detecta bloqueo/estancamiento
    hb.write_text("1000.0|4242", encoding="utf-8")
    os.utime(hb, (viejo, viejo))
    assert agente.esclava_heartbeat_fresco(max_age_sec=180.0) is False

    # Archivo fresco del mismo PID -> True
    os.utime(hb, (time.time(), time.time()))
    assert agente.esclava_heartbeat_fresco(max_age_sec=180.0) is True
