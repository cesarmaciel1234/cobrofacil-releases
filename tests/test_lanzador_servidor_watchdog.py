"""Pruebas del watchdog del lanzador y autoarranque del servidor de tienda con Windows."""

from unittest.mock import MagicMock
from src.lanzador.servidor import pulso


def test_asegurar_servidor_activa_arranque_si_falta(monkeypatch):
    """Si auto_start_store_server está activo y el OS no tiene el acceso directo, debe registrarlo."""
    mock_autostart_enabled = MagicMock(return_value=False)
    mock_set_autostart = MagicMock()
    mock_online = MagicMock(return_value=True)

    monkeypatch.setattr("src.central_red_global.servidor.is_os_autostart_enabled", mock_autostart_enabled)
    monkeypatch.setattr("src.central_red_global.servidor.set_os_autostart", mock_set_autostart)
    monkeypatch.setattr("src.central_red_global.servidor.is_store_server_online", mock_online)

    pulso.asegurar_servidor()

    assert mock_autostart_enabled.called
    mock_set_autostart.assert_called_once_with(True)


def test_asegurar_servidor_revive_proceso_si_esta_caido(monkeypatch):
    """Si el servidor no responde o su proceso se cayó, asegurar_servidor() lo levanta con ensure_store_server_process."""
    mock_autostart_enabled = MagicMock(return_value=True)
    mock_set_autostart = MagicMock()
    mock_online = MagicMock(return_value=False)
    mock_ensure = MagicMock()
    mock_end_guard = MagicMock()

    monkeypatch.setattr("src.central_red_global.servidor.is_os_autostart_enabled", mock_autostart_enabled)
    monkeypatch.setattr("src.central_red_global.servidor.set_os_autostart", mock_set_autostart)
    monkeypatch.setattr("src.central_red_global.servidor.is_store_server_online", mock_online)
    monkeypatch.setattr("src.central_red_global.servidor.ensure_store_server_process", mock_ensure)
    monkeypatch.setattr("src.updater.silent_auto_updater.end_apply_guard", mock_end_guard)

    pulso.asegurar_servidor()

    assert not mock_set_autostart.called
    assert mock_end_guard.called
    mock_ensure.assert_called_once_with(timeout_sec=40.0)


def test_asegurar_servidor_no_relanza_si_esta_online(monkeypatch):
    """Si el servidor ya está online y el arranque con Windows registrado, no relanza proceso innecesariamente."""
    mock_autostart_enabled = MagicMock(return_value=True)
    mock_set_autostart = MagicMock()
    mock_online = MagicMock(return_value=True)
    mock_ensure = MagicMock()

    monkeypatch.setattr("src.central_red_global.servidor.is_os_autostart_enabled", mock_autostart_enabled)
    monkeypatch.setattr("src.central_red_global.servidor.set_os_autostart", mock_set_autostart)
    monkeypatch.setattr("src.central_red_global.servidor.is_store_server_online", mock_online)
    monkeypatch.setattr("src.central_red_global.servidor.ensure_store_server_process", mock_ensure)

    pulso.asegurar_servidor()

    assert not mock_ensure.called
