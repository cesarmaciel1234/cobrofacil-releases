"""Interruptor Win/Auto: respaldo de boot."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QMessageBox, QPushButton


def crear_interruptor(on_toggle) -> QPushButton:
    from PyQt6.QtCore import Qt

    btn = QPushButton("Win: OFF")
    btn.setFixedHeight(26)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setToolTip(
        "Respaldo: arrancar --server al encender el PC (corte de luz / Linux sin pantalla). "
        "El lanzador ya despierta el servidor solo si esta PC es MAESTRA."
    )
    btn.clicked.connect(on_toggle)
    return btn


def pintar_interruptor(btn: QPushButton) -> None:
    from src.central_red_global.servidor import is_os_autostart_enabled

    on = is_os_autostart_enabled()
    pref = "Win" if sys.platform == "win32" else "Auto"
    btn.setText(f"{pref}: ON" if on else f"{pref}: OFF")
    btn.setStyleSheet(
        "QPushButton { font-size: 10px; font-weight: 800; border-radius: 8px; "
        "padding: 4px 10px; border: 1px solid %s; background: %s; color: %s; }"
        % (
            ("#86EFAC", "#DCFCE7", "#15803D") if on else ("#E2E8F0", "#F8FAFC", "#64748B")
        )
    )


def al_toggle_interruptor(parent, btn: QPushButton) -> None:
    from src.config import config
    from src.central_red_global.servidor import is_os_autostart_enabled, set_os_autostart

    new_state = not is_os_autostart_enabled()
    ok = set_os_autostart(new_state)
    config.set("auto_start_store_server", new_state)
    if not ok and new_state:
        QMessageBox.warning(
            parent,
            "Inicio automático",
            "No se pudo registrar el arranque del servidor.\n"
            "En Windows: ejecutar como Administrador.\n"
            "En Linux: systemd --user o ~/.config/autostart.",
        )
    pintar_interruptor(btn)
