"""Pruebas unitarias para el Servicio Nativo Windows (Session 0) y compatibilidad con candados."""

import ctypes
import os
import sys
from unittest.mock import MagicMock

from src.central_red_global.servidor.servicio_windows import gestor
from src.utils import candados


def test_build_service_binpath_contiene_flags_y_service_root(tmp_path):
    cmd_str = gestor.build_service_binpath(str(tmp_path))
    assert "--server" in cmd_str
    assert "--winservice" in cmd_str
    assert "--service-root" in cmd_str
    assert str(tmp_path) in cmd_str


def test_candados_reconoce_pid_servicio_windows_session0(tmp_path, monkeypatch):
    if sys.platform != "win32":
        return

    monkeypatch.setattr(candados, "_LOCK_DIR", str(tmp_path))
    monkeypatch.setattr(candados, "STORE_SERVER_LOCK_PATH", str(tmp_path / "servidor_tienda.lock"))
    monkeypatch.setattr(
        gestor,
        "estado_servicio_windows",
        lambda: {
            "instalado": True,
            "en_ejecucion": True,
            "estado": 4,
            "pid": 99441,
            "auto_inicio": True,
        },
    )

    # Simular que OpenProcess falla por AccessDenied frente a LocalSystem
    monkeypatch.setattr(ctypes.windll.kernel32, "OpenProcess", lambda *_a: 0)
    monkeypatch.setattr(candados, "_pid_alive", lambda p: int(p) == 99441)

    assert candados.get_store_server_pid() == 99441
    assert candados.is_store_server_running() is True
    assert candados._is_our_process(99441) is True
    assert candados.acquire_store_server_lock() is False


def test_ensure_store_server_usa_servicio_windows_si_instalado(monkeypatch):
    if sys.platform != "win32":
        return

    from src.central_red_global.servidor.arranque import proceso

    monkeypatch.setattr("src.updater.silent_auto_updater.is_apply_guard_active", lambda: False)
    monkeypatch.setattr(proceso, "is_store_server_online", lambda: False)
    monkeypatch.setattr(proceso, "is_store_server_running", lambda: False)
    monkeypatch.setattr(proceso, "heal_store_server_lock_from_process", lambda: None)
    monkeypatch.setattr(proceso, "try_acquire_store_server_spawn_guard", lambda: True)
    monkeypatch.setattr(proceso, "release_store_server_spawn_guard", lambda: None)
    monkeypatch.setattr(proceso, "needs_mariadb", lambda: True)
    monkeypatch.setattr(proceso, "mariadb_port_open", lambda: True)
    monkeypatch.setattr(proceso, "lan_port_open", lambda: True)

    monkeypatch.setattr(
        gestor,
        "estado_servicio_windows",
        lambda: {"instalado": True, "en_ejecucion": False, "estado": 1, "pid": None, "auto_inicio": True},
    )
    start_mock = MagicMock(return_value=True)
    monkeypatch.setattr(gestor, "iniciar_servicio_windows", start_mock)
    popen_mock = MagicMock()
    monkeypatch.setattr(proceso.subprocess, "Popen", popen_mock)

    assert proceso.ensure_store_server_process(timeout_sec=5.0) is True
    assert start_mock.called
    assert not popen_mock.called


def test_autostart_admin_registra_servicio_y_conserva_lanzador(tmp_path, monkeypatch):
    if sys.platform != "win32":
        return

    from src.central_red_global.servidor.autostart import windows

    srv_lnk = str(tmp_path / "CobroFacil_ServidorTienda.lnk")
    hub_lnk = str(tmp_path / "CobroFacil_Lanzador.lnk")
    stamp = str(tmp_path / "startup_target.txt")

    with open(srv_lnk, "w", encoding="utf-8") as f:
        f.write("stale")

    monkeypatch.setattr(windows, "startup_shortcut_path", lambda: srv_lnk)
    monkeypatch.setattr(windows, "launcher_startup_shortcut_path", lambda: hub_lnk)
    monkeypatch.setattr(windows, "_startup_stamp_path", lambda: stamp)

    tasks = []
    monkeypatch.setattr(gestor, "es_administrador", lambda: True)
    inst_mock = MagicMock(return_value=(True, "ok"))
    monkeypatch.setattr(gestor, "instalar_servicio_windows", inst_mock)
    monkeypatch.setattr(gestor, "servicio_instalado", lambda: True)

    def fake_shortcut(path, target, args, workdir, desc):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{target} {args}")
        return True

    def fake_task(task_name, enabled, target="", args="", workdir="", description="", restart_count=999):
        tasks.append((task_name, enabled, args))

    monkeypatch.setattr(windows, "_create_shortcut_fast_or_ps", fake_shortcut)
    monkeypatch.setattr(windows, "_set_scheduled_task_item", fake_task)

    assert windows.set_windows_startup(True) is True
    assert inst_mock.called
    assert not os.path.exists(srv_lnk)  # reemplazado por Servicio Session 0
    assert os.path.isfile(hub_lnk)  # Lanzador en bandeja sigue registrado para sesión usuario
    assert ("CobroFacil_ServidorTienda", False, "") in tasks
    assert any(n == "CobroFacil_Lanzador" and en and "--background" in args for n, en, args in tasks)


def test_instalar_servicio_windows_requiere_admin(monkeypatch):
    monkeypatch.setattr(gestor, "es_administrador", lambda: False)
    sc_mock = MagicMock()
    monkeypatch.setattr(gestor, "_sc_run", sc_mock)

    ok, msg = gestor.instalar_servicio_windows("C:\\tmp")
    assert ok is False
    assert "Administrador" in msg or "Windows" in msg
    assert not sc_mock.called
