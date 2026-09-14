"""Inicio automático en Linux (desktop + systemd user)."""

from __future__ import annotations

import os
import subprocess

from src.logger import logger
from src.central_red_global.servidor.comando import build_server_command


def linux_desktop_autostart_path() -> str:
    return os.path.join(
        os.path.expanduser("~"), ".config", "autostart", "cobrofacil-servidor.desktop"
    )


def linux_systemd_unit_path() -> str:
    return os.path.join(
        os.path.expanduser("~"),
        ".config",
        "systemd",
        "user",
        "cobrofacil-servidor.service",
    )


def set_linux_autostart(enabled: bool) -> bool:
    desktop = linux_desktop_autostart_path()
    unit = linux_systemd_unit_path()
    try:
        if not enabled:
            for p in (desktop, unit):
                if os.path.exists(p):
                    os.remove(p)
            subprocess.run(
                ["systemctl", "--user", "disable", "--now", "cobrofacil-servidor.service"],
                capture_output=True,
                timeout=10,
            )
            return True

        from src.utils.paths import get_base_path

        cmd = build_server_command()
        exec_line = " ".join(f'"{c}"' if " " in c else c for c in cmd)
        workdir = get_base_path()
        os.makedirs(os.path.dirname(desktop), exist_ok=True)
        with open(desktop, "w", encoding="utf-8") as f:
            f.write(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=CobroFacil Servidor de Tienda\n"
                "Exec=" + exec_line + "\n"
                f"Path={workdir}\n"
                "X-GNOME-Autostart-enabled=true\n"
                "Hidden=false\n"
            )
        os.makedirs(os.path.dirname(unit), exist_ok=True)
        with open(unit, "w", encoding="utf-8") as f:
            f.write(
                "[Unit]\n"
                "Description=CobroFacil Servidor de Tienda\n"
                "After=network-online.target\n"
                "Wants=network-online.target\n"
                "\n"
                "[Service]\n"
                "Type=simple\n"
                f"WorkingDirectory={workdir}\n"
                f"ExecStart={exec_line}\n"
                "Restart=on-failure\n"
                "RestartSec=5\n"
                "Environment=QT_QPA_PLATFORM=offscreen\n"
                "\n"
                "[Install]\n"
                "WantedBy=default.target\n"
            )
        subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            capture_output=True,
            timeout=10,
        )
        subprocess.run(
            ["systemctl", "--user", "enable", "--now", "cobrofacil-servidor.service"],
            capture_output=True,
            timeout=15,
        )
        return os.path.exists(desktop) or os.path.exists(unit)
    except Exception as e:
        logger.error(f"Autostart Linux: {e}")
        return os.path.exists(desktop)


def is_linux_autostart_enabled() -> bool:
    return os.path.exists(linux_desktop_autostart_path()) or os.path.exists(
        linux_systemd_unit_path()
    )
