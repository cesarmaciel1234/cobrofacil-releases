"""Pruebas del watchdog del lanzador, autoarranque Windows, backoff y healthchecks del servidor."""

from unittest.mock import MagicMock
from src.lanzador.servidor import pulso


def test_asegurar_servidor_activa_arranque_si_falta(monkeypatch):
    """Si auto_start_store_server está activo y el OS no tiene el acceso directo, debe registrarlo."""
    pulso.reset_watchdog_backoff()
    from src.config import config
    monkeypatch.setitem(config.data, "auto_start_store_server", True)
    mock_autostart_enabled = MagicMock(return_value=False)
    mock_set_autostart = MagicMock()
    mock_online = MagicMock(return_value=True)

    monkeypatch.setattr("src.central_red_global.servidor.is_os_autostart_enabled", mock_autostart_enabled)
    monkeypatch.setattr("src.central_red_global.servidor.set_os_autostart", mock_set_autostart)
    monkeypatch.setattr("src.central_red_global.servidor.is_store_server_online", mock_online)

    assert pulso.asegurar_servidor() is True
    assert mock_autostart_enabled.called
    mock_set_autostart.assert_called_once_with(True)


def test_asegurar_servidor_revive_proceso_si_esta_caido(monkeypatch):
    """Si el servidor no responde o su proceso se cayó, asegurar_servidor() lo levanta con ensure_store_server_process."""
    pulso.reset_watchdog_backoff()
    mock_autostart_enabled = MagicMock(return_value=True)
    mock_set_autostart = MagicMock()
    mock_online = MagicMock(return_value=False)
    mock_ensure = MagicMock(return_value=True)
    mock_end_guard = MagicMock()

    monkeypatch.setattr("src.central_red_global.servidor.is_os_autostart_enabled", mock_autostart_enabled)
    monkeypatch.setattr("src.central_red_global.servidor.set_os_autostart", mock_set_autostart)
    monkeypatch.setattr("src.central_red_global.servidor.is_store_server_online", mock_online)
    monkeypatch.setattr("src.central_red_global.servidor.ensure_store_server_process", mock_ensure)
    monkeypatch.setattr("src.updater.silent_auto_updater.end_apply_guard", mock_end_guard)

    assert pulso.asegurar_servidor() is True
    assert not mock_set_autostart.called
    assert mock_end_guard.called
    mock_ensure.assert_called_once_with(timeout_sec=40.0)


def test_asegurar_servidor_no_relanza_si_esta_online(monkeypatch):
    """Si el servidor ya está online y el arranque con Windows registrado, no relanza proceso innecesariamente."""
    pulso.reset_watchdog_backoff()
    mock_autostart_enabled = MagicMock(return_value=True)
    mock_set_autostart = MagicMock()
    mock_online = MagicMock(return_value=True)
    mock_ensure = MagicMock()

    monkeypatch.setattr("src.central_red_global.servidor.is_os_autostart_enabled", mock_autostart_enabled)
    monkeypatch.setattr("src.central_red_global.servidor.set_os_autostart", mock_set_autostart)
    monkeypatch.setattr("src.central_red_global.servidor.is_store_server_online", mock_online)
    monkeypatch.setattr("src.central_red_global.servidor.ensure_store_server_process", mock_ensure)

    assert pulso.asegurar_servidor() is True
    assert not mock_ensure.called


def test_asegurar_servidor_aplica_backoff_en_fallos(monkeypatch):
    """Si ensure_store_server_process falla, el segundo intento inmediato es omitido por backoff salvo force=True."""
    pulso.reset_watchdog_backoff()
    monkeypatch.setattr("src.central_red_global.servidor.is_os_autostart_enabled", lambda: True)
    monkeypatch.setattr("src.central_red_global.servidor.is_store_server_online", lambda: False)
    monkeypatch.setattr("src.updater.silent_auto_updater.end_apply_guard", lambda: None)

    mock_ensure = MagicMock(return_value=False)
    monkeypatch.setattr("src.central_red_global.servidor.ensure_store_server_process", mock_ensure)

    # Primer intento falla -> programa backoff
    assert pulso.asegurar_servidor() is False
    assert mock_ensure.call_count == 1

    # Segundo intento inmediato -> bloqueado por backoff
    assert pulso.asegurar_servidor() is False
    assert mock_ensure.call_count == 1

    # Con force=True -> vuelve a intentar
    assert pulso.asegurar_servidor(force=True) is False
    assert mock_ensure.call_count == 2
    pulso.reset_watchdog_backoff()


def test_build_server_command_background():
    from src.central_red_global.servidor.comando import build_server_command

    cmd_bg = build_server_command(background=True)
    assert "--server" in cmd_bg
    assert "--background" in cmd_bg

    cmd_fg = build_server_command(background=False)
    assert "--server" in cmd_fg
    assert "--background" not in cmd_fg


def test_is_store_server_online_valida_maestra_y_esclava(monkeypatch):
    from src.central_red_global.servidor.arranque import proceso

    monkeypatch.setattr(proceso, "is_store_server_running", lambda: True)
    monkeypatch.setattr(proceso, "needs_mariadb", lambda: True)
    monkeypatch.setattr(proceso, "mariadb_port_open", lambda: True)
    monkeypatch.setattr(proceso, "http_health_ok", lambda: False)
    monkeypatch.setattr(proceso, "lan_port_open", lambda: False)
    # Si tanto HTTP health como puerto LAN están caídos, Maestra NO está online
    assert proceso.is_store_server_online() is False

    monkeypatch.setattr(proceso, "http_health_ok", lambda: True)
    assert proceso.is_store_server_online() is True

    # En Esclava valida el heartbeat fresco
    monkeypatch.setattr(proceso, "needs_mariadb", lambda: False)
    monkeypatch.setattr("src.central_red_global.servidor.oficio.agente.esclava_heartbeat_fresco", lambda: False)
    assert proceso.is_store_server_online() is False

    monkeypatch.setattr("src.central_red_global.servidor.oficio.agente.esclava_heartbeat_fresco", lambda: True)
    assert proceso.is_store_server_online() is True


def test_mariadb_controller_cuarentena_no_borra_datos(tmp_path):
    """La recuperación InnoDB resguarda archivos en corrupt_backup_* sin destruir punpro_db."""
    from src.services.mariadb_controller import MariaDBController

    server_dir = tmp_path / "mariadb_server"
    data_dir = server_dir / "data"
    punpro_dir = data_dir / "punpro_db"
    punpro_dir.mkdir(parents=True)
    (data_dir / "ibdata1").write_bytes(b"ibdata")
    (punpro_dir / "ventas.ibd").write_bytes(b"ventas_reales")

    ctrl = MariaDBController()
    backup_dir = ctrl._quarantine_corrupt_files(str(server_dir), str(data_dir))

    import pathlib
    b = pathlib.Path(backup_dir)
    assert b.is_dir()
    assert (b / "ibdata1").read_bytes() == b"ibdata"
    assert (b / "punpro_db" / "ventas.ibd").read_bytes() == b"ventas_reales"
    assert not (data_dir / "ibdata1").exists()


def test_lan_server_health_endpoint(monkeypatch):
    """El endpoint /health responde 200 ok o 503 degraded según disponibilidad real de BD."""
    import json
    import threading
    import urllib.error
    import urllib.request
    from http.server import ThreadingHTTPServer

    from src.central_red_global import lan_server
    from src.central_red_global.servidor import puerto

    monkeypatch.setattr(lan_server.db_manager, "is_master", True, raising=False)
    monkeypatch.setattr(puerto, "needs_mariadb", lambda: False)
    monkeypatch.setattr(puerto, "mariadb_port_open", lambda timeout=0.4: False)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), lan_server.LANRequestHandler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2.0) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "ok"
        assert data["http_ok"] is True
        assert data["db_ok"] is True
        assert "uptime_sec" in data

        monkeypatch.setattr(puerto, "needs_mariadb", lambda: True)
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2.0)
            assert False, "Debió responder 503 en estado degraded"
        except urllib.error.HTTPError as err:
            assert err.code == 503
            degraded = json.loads(err.read().decode("utf-8"))
            assert degraded["status"] == "degraded"
            assert degraded["db_ok"] is False
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_autostart_windows_com_in_worker_thread():
    """is_windows_startup_enabled funciona en hilos secundarios sin error CoInitialize y usa caché."""
    import threading

    from src.central_red_global.servidor.autostart import windows as autostart_win

    resultados = []
    errores = []

    def _run():
        try:
            resultados.append(autostart_win.is_windows_startup_enabled())
            resultados.append(autostart_win.is_windows_startup_enabled())
        except Exception as exc:
            errores.append(exc)

    hilo = threading.Thread(target=_run)
    hilo.start()
    hilo.join(timeout=5.0)
    assert not errores
    assert len(resultados) == 2
    assert isinstance(resultados[0], bool)
    assert resultados[0] == resultados[1]

