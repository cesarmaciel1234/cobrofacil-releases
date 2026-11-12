import sys
from pathlib import Path
from unittest.mock import patch

import main
from src.services import github_error_reporter as ger


def test_chromium_only_loaded_for_web_terminal_roles():
    casos_sin_chromium = [
        ["main.py"],
        ["main.py", "--background"],
        ["main.py", "--server"],
        ["main.py", "--server", "--background"],
        ["main.py", "--updater"],
        ["main.py", "--role", "cajero"],
        ["main.py", "--role=jefe"],
        ["main.py", "--profile", "cajero"],
    ]
    for argv in casos_sin_chromium:
        with patch.object(sys, "argv", argv):
            assert main._rol_usa_chromium() is False, argv
            assert main._rol_sin_chromium() is True, argv

    casos_con_chromium = [
        ["main.py", "--role", "admin"],
        ["main.py", "--role=carteleria"],
        ["main.py", "--profile", "contabilidad"],
    ]
    for argv in casos_con_chromium:
        with patch.object(sys, "argv", argv):
            assert main._rol_usa_chromium() is True, argv
            assert main._rol_sin_chromium() is False, argv


def test_main_no_heavy_top_level_imports_or_duplicate_hardware_popup():
    src = Path(main.__file__).read_text(encoding="utf-8")
    assert "AutoBlindajeDB" not in src
    assert "motor_flash" not in src
    assert src.count("AVISO DE HARDWARE") == 0

    pos_early_lock = src.index("if not acquire_master_launcher_lock")
    pos_updater = src.index("apply_pending_update_on_startup(delegate)")
    pos_tema = src.index("aplicar_tema(app, qss_filename)")
    assert pos_early_lock > src.index("is_terminal_role = bool(target_role)")
    # La segunda ocurrencia de apply_pending_update_on_startup está en __main__ antes del loop UI
    pos_main_updater = src.index("apply_pending_update_on_startup(delegate)", pos_updater + 1)
    assert pos_early_lock < pos_main_updater < pos_tema


def test_github_reporter_auth_circuit_breaker_stops_http_spam(tmp_path, monkeypatch):
    ger.reset_auth_circuit_breaker()
    monkeypatch.setattr(ger, "_log_dir", lambda: str(tmp_path))
    monkeypatch.setattr(ger, "_report_settings", lambda: (True, "tok_bad_123", "owner/repo"))

    calls = []

    def fake_http(method, url, token, payload):
        calls.append((method, url, token))
        return 401, b"Bad credentials"

    monkeypatch.setattr(ger, "_http_json", fake_http)
    monkeypatch.setattr(ger, "_schedule_flush", lambda: calls.append(("schedule_flush", "", "")))

    ger.queue_error_report("error de prueba 1", source="unit", skip_heal=True)
    # _schedule_flush habría sido llamado en el primer encolado
    assert any(c[0] == "schedule_flush" for c in calls)
    calls.clear()

    sent_1 = ger.flush_pending_reports()
    assert sent_1 == 0
    # Solo 1 intento a /issues y 1 fallback a /dispatches antes de abrir el circuit breaker
    assert len(calls) == 2

    calls.clear()
    # Segundo flush con el mismo token inválido: 0 llamadas HTTP
    sent_2 = ger.flush_pending_reports()
    assert sent_2 == 0
    assert calls == []

    # Nuevo error con circuit-breaker abierto: se encola en JSON local pero NO agenda flush HTTP
    ger.queue_error_report("error de prueba 2", source="unit", skip_heal=True)
    assert calls == []

    q = ger._load_json(ger._queue_path(), [])
    assert len(q) >= 2
    ger.reset_auth_circuit_breaker()


def test_github_reporter_no_token_warns_only_once(tmp_path, monkeypatch, caplog):
    ger.reset_auth_circuit_breaker()
    monkeypatch.setattr(ger, "_log_dir", lambda: str(tmp_path))
    monkeypatch.setattr(ger, "_report_settings", lambda: (True, "", "owner/repo"))

    with caplog.at_level("INFO", logger="PunPro"):
        ger.queue_error_report("sin red 1", source="unit", skip_heal=True)
        ger.queue_error_report("sin red 2", source="unit", skip_heal=True)
        ger.flush_pending_reports()

    msgs = [r.message for r in caplog.records if "GitHub error report" in r.message]
    assert len(msgs) == 1
    ger.reset_auth_circuit_breaker()


def test_network_engine_reemplaza_fallback_cajero_por_rol_explicito(monkeypatch):
    from src.central_red_global import network_engine as ne

    creados = []

    class DummyEngine:
        def __init__(self, role):
            self.role = role
            self.stopped = False

        def start(self):
            creados.append(self.role)

        def stop(self):
            self.stopped = True

    monkeypatch.setattr(ne, "NetworkEngine", DummyEngine)
    monkeypatch.setattr(ne, "_cpp_alive", lambda obj: obj is not None)
    monkeypatch.setattr(ne, "_engine", None)

    e1 = ne.init_network_engine("cajero")
    assert e1.role == "cajero"
    e2 = ne.init_network_engine("admin")
    assert e1.stopped is True
    assert e2.role == "admin"
    # Un segundo llamado con 'cajero' ya no pisa al rol explícito 'admin'
    e3 = ne.init_network_engine("cajero")
    assert e3.role == "admin"
    assert creados == ["cajero", "admin"]
    ne._engine = None


def test_motor_proveedor_texto_compra_usa_flecha_ascii():
    from src.proveedor_global.backend.motor_proveedor import MotorProveedor

    desc, resumido = MotorProveedor._texto_compra(
        "Proveedor Demo",
        "123",
        {("Pollo", 1500.0): [("Pollo", 10.0, 2.0)]},
        "Contado (Pago Inmediato)",
    )
    assert "\u21b3" not in desc
    assert "  -> Total kg:" in desc
    assert len(resumido) == 1


def test_main_pre_mainwindow_role_y_una_sola_init_db():
    src = Path(main.__file__).read_text(encoding="utf-8")
    pos_init_net = src.index("init_network_engine(direct_role)")
    pos_main_win = src.index("main_window = MainWindow()")
    assert pos_init_net < pos_main_win
    assert 'if reload_config or not getattr(db_manager, "_init_completed", False):' in src
    assert "if is_terminal_role:\n        from src.hardware.cash_drawer import reset_drawer_manager" in src.replace("\r\n", "\n")


def test_dialogo_cargar_saldo_no_rompe_con_letra_tam(monkeypatch):
    from PyQt6.QtWidgets import QApplication, QDialog
    from src.admin.clientes.componentes import dialogo_historial_cliente as dhc

    app = QApplication.instance() or QApplication([])
    dummy = type("DummyDlg", (), {"cliente": {"nombre": "Cliente Test", "deuda_actual": 1250.5}})()
    # Inyectar QDialog.__init__ sin construir ventana padre real: usar QDialog parent=None
    real_parent = QDialog()
    real_parent.cliente = dummy.cliente
    real_parent.cliente_id = 1
    monkeypatch.setattr(QDialog, "exec", lambda self: 0)

    # Ejecutar método real _cargar_saldo (antes explotaba en vestir_nombre(lbl_head, tam=15))
    dhc.DialogoHistorialCliente._cargar_saldo(real_parent)
    real_parent.close()


def test_paso5_verificar_autocierre_sin_agregar_al_ticket_roto(monkeypatch):
    from datetime import datetime
    from src.cajero.paso5_terminal import paso5_terminal as p5
    from src.config import config
    from src.services import caja_service

    class FakeTerminal:
        flashed = []
        refreshed = 0

        def flash_feedback(self, success=True):
            self.flashed.append(success)

        def refresh_status_bar(self):
            self.refreshed += 1

    fake = FakeTerminal()
    ahora_str = datetime.now().strftime("%H:%M")
    orig_get = config.get
    monkeypatch.setattr(
        config,
        "get",
        lambda k, d=None: ahora_str if k == "cierre_auto_hora" else orig_get(k, d),
    )
    monkeypatch.setattr(caja_service, "verificar_y_realizar_autocierre", lambda: (True, 5000.0))

    p5.Paso5Terminal.verificar_autocierre(fake)
    assert fake.flashed == [True]
    assert fake.refreshed == 1
