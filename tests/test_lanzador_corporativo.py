"""Pruebas de arquitectura corporativa del Lanzador: bandeja, lock, autostart y watchdog."""

import os
from unittest.mock import MagicMock

from src.lanzador.cerebro.watchdog_perfiles import (
    build_launcher_command,
    decidir_accion_perfil_terminado,
)
from src.utils import candados


def test_decidir_accion_cierre_limpio_no_reabre_como_virus():
    for code in (0, 888, 889, None):
        accion, hist = decidir_accion_perfil_terminado(code, [100.0, 110.0], ahora=120.0)
        assert accion == "reposo"
        assert hist == []


def test_decidir_accion_circuit_breaker_60s():
    hist = []
    for t in (1000.0, 1010.0, 1020.0):
        accion, hist = decidir_accion_perfil_terminado(1, hist, ahora=t, max_reintentos=3, ventana_seg=60.0)
        assert accion == "relanzar"
    assert len(hist) == 3

    # 4ta caída dentro de 60s dispara circuit breaker
    accion4, hist4 = decidir_accion_perfil_terminado(
        -1073741819, hist, ahora=1030.0, max_reintentos=3, ventana_seg=60.0
    )
    assert accion4 == "pausado"
    assert len(hist4) == 4

    # Pasados > 60s, las caídas viejas caducan y permite volver a intentar
    accion_nueva, hist_nueva = decidir_accion_perfil_terminado(
        1, hist4, ahora=1120.0, max_reintentos=3, ventana_seg=60.0
    )
    assert accion_nueva == "relanzar"
    assert hist_nueva == [1120.0]


def test_decidir_accion_ignora_durante_actualizacion():
    accion, hist = decidir_accion_perfil_terminado(1, [50.0], ahora=60.0, apply_guard=True)
    assert accion == "ignorar"
    assert hist == [50.0]


def test_build_launcher_command_background_flag():
    cmd_bg = build_launcher_command(background=True)
    cmd_fg = build_launcher_command(background=False)
    assert "--background" in cmd_bg
    assert "--background" not in cmd_fg
    assert any(part.endswith("main.py") or part.endswith(".exe") for part in cmd_fg)


def test_lock_maestro_despierta_lanzador_en_bandeja_sin_matarlo(tmp_path, monkeypatch):
    lock_dir = str(tmp_path)
    lock_file = os.path.join(lock_dir, "lanzador_maestro.lock")
    show_file = os.path.join(lock_dir, "lanzador_maestro.mostrar")
    tray_file = os.path.join(lock_dir, "lanzador_maestro.tray")

    monkeypatch.setattr(candados, "_LOCK_DIR", lock_dir)
    monkeypatch.setattr(candados, "MASTER_LOCK_PATH", lock_file)
    monkeypatch.setattr(candados, "MASTER_SHOW_PATH", show_file)
    monkeypatch.setattr(candados, "MASTER_TRAY_STATE_PATH", tray_file)

    other_pid = os.getpid() + 55555
    with open(lock_file, "w", encoding="utf-8") as f:
        f.write(str(other_pid))
    with open(tray_file, "w", encoding="utf-8") as f:
        f.write(str(other_pid))

    monkeypatch.setattr(candados, "_pid_alive", lambda pid: pid == other_pid)
    monkeypatch.setattr(candados, "_is_our_process", lambda pid: pid == other_pid)
    kill_mock = MagicMock()
    monkeypatch.setattr(candados.subprocess, "run", kill_mock)

    # Arranque silencioso en background: respeta instancia en bandeja sin levantar ventana ni matar
    assert candados.acquire_master_launcher_lock(show_if_running=False) is False
    assert not os.path.exists(show_file)
    assert not kill_mock.called

    # Clic en acceso directo: pide mostrar la ventana en bandeja sin matar el proceso
    assert candados.acquire_master_launcher_lock(show_if_running=True) is False
    assert os.path.isfile(show_file)
    assert not kill_mock.called


def test_windows_startup_registra_servidor_y_lanzador_separados(tmp_path, monkeypatch):
    from src.central_red_global.servidor.autostart import windows

    srv_lnk = str(tmp_path / "CobroFacil_ServidorTienda.lnk")
    hub_lnk = str(tmp_path / "CobroFacil_Lanzador.lnk")
    stamp = str(tmp_path / "startup_target.txt")

    monkeypatch.setattr(windows, "startup_shortcut_path", lambda: srv_lnk)
    monkeypatch.setattr(windows, "launcher_startup_shortcut_path", lambda: hub_lnk)
    monkeypatch.setattr(windows, "_startup_stamp_path", lambda: stamp)

    created = []
    tasks = []

    def fake_shortcut(path, target, args, workdir, desc):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{target} {args}")
        created.append((path, args))
        return True

    def fake_task(task_name, enabled, target="", args="", workdir="", description="", restart_count=999):
        tasks.append((task_name, enabled, args, restart_count))

    monkeypatch.setattr(windows, "_create_shortcut_fast_or_ps", fake_shortcut)
    monkeypatch.setattr(windows, "_set_scheduled_task_item", fake_task)

    assert windows.set_windows_startup(True) is True
    assert os.path.isfile(srv_lnk)
    assert os.path.isfile(hub_lnk)
    assert any(name == "CobroFacil_ServidorTienda" and en and "--server" in args for name, en, args, _ in tasks)
    assert any(name == "CobroFacil_Lanzador" and en and "--background" in args and "--server" not in args for name, en, args, _ in tasks)

    tasks.clear()
    assert windows.set_windows_startup(False) is True
    assert not os.path.exists(srv_lnk)
    assert not os.path.exists(hub_lnk)
    assert ("CobroFacil_ServidorTienda", False, "", 999) in tasks
    assert ("CobroFacil_Lanzador", False, "", 999) in tasks


def test_lock_maestro_respeta_arranque_inicial_sin_matar(tmp_path, monkeypatch):
    lock_dir = str(tmp_path)
    lock_file = os.path.join(lock_dir, "lanzador_maestro.lock")
    show_file = os.path.join(lock_dir, "lanzador_maestro.mostrar")
    tray_file = os.path.join(lock_dir, "lanzador_maestro.tray")

    monkeypatch.setattr(candados, "_LOCK_DIR", lock_dir)
    monkeypatch.setattr(candados, "MASTER_LOCK_PATH", lock_file)
    monkeypatch.setattr(candados, "MASTER_SHOW_PATH", show_file)
    monkeypatch.setattr(candados, "MASTER_TRAY_STATE_PATH", tray_file)

    other_pid = os.getpid() + 44444
    with open(lock_file, "w", encoding="utf-8") as f:
        f.write(str(other_pid))

    monkeypatch.setattr(candados, "_pid_alive", lambda pid: pid == other_pid)
    monkeypatch.setattr(candados, "_is_our_process", lambda pid: pid == other_pid)
    monkeypatch.setattr(candados, "_master_window_exists", lambda: False)
    kill_mock = MagicMock()
    monkeypatch.setattr(candados.subprocess, "run", kill_mock)

    # Lock recién creado (<25s) mientras inicializa DB/Qt -> pide mostrar pero NO mata el PID
    assert candados.acquire_master_launcher_lock(show_if_running=True) is False
    assert os.path.isfile(show_file)
    assert not kill_mock.called
