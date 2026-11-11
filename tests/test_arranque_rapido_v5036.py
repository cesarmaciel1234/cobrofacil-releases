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
