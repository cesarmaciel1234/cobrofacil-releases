"""Pastilla ONLINE / ESCLAVA / OFFLINE."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QMessageBox


def crear_badge(parent, on_click):
    lbl = QLabel("Servidor: …")
    lbl.setStyleSheet(
        "font-size: 10px; font-weight: 800; color: #64748B; background: #F1F5F9; "
        "border: 1px solid #E2E8F0; border-radius: 8px; padding: 4px 10px;"
    )
    from PyQt6.QtCore import Qt

    lbl.setCursor(Qt.PointingHandCursor)
    lbl.setToolTip("Clic: mostrar / asegurar Servidor de Tienda")
    lbl.mousePressEvent = lambda e: on_click()
    return lbl


def pintar_badge(lbl: QLabel) -> None:
    from src.central_red_global.master_presence import es_pc_maestra_local
    from src.central_red_global.servidor import is_store_server_online
    from src.utils.candados import get_store_server_pid

    online = is_store_server_online()
    pid = get_store_server_pid()
    if not es_pc_maestra_local():
        lbl.setText("Rol: ESCLAVA")
        lbl.setStyleSheet(
            "font-size: 10px; font-weight: 800; color: #1E3A8A; background: #DBEAFE; "
            "border: 1px solid #93C5FD; border-radius: 8px; padding: 4px 10px;"
        )
        lbl.setToolTip("Esta PC ya sabe su puesto: se conecta a la maestra. No levanta MariaDB.")
        return
    if online:
        lbl.setText("Servidor: ONLINE" + (f" · {pid}" if pid else ""))
        lbl.setStyleSheet(
            "font-size: 10px; font-weight: 800; color: #15803D; background: #DCFCE7; "
            "border: 1px solid #86EFAC; border-radius: 8px; padding: 4px 10px;"
        )
    else:
        lbl.setText("Servidor: OFFLINE")
        lbl.setStyleSheet(
            "font-size: 10px; font-weight: 800; color: #B91C1C; background: #FEE2E2; "
            "border: 1px solid #FECACA; border-radius: 8px; padding: 4px 10px;"
        )


def al_clic_badge(parent, lbl: QLabel) -> None:
    from src.central_red_global.master_presence import es_pc_maestra_local
    from src.central_red_global.servidor import (
        ensure_store_server_process,
        is_store_server_online,
    )
    from src.updater.silent_auto_updater import end_apply_guard
    from src.utils.candados import focus_existing_store_server

    if not es_pc_maestra_local():
        QMessageBox.information(
            parent,
            "Esclava",
            "Esta PC ya tiene puesto de ESCLAVA.\n"
            "El servidor vive en la maestra. Acá no se levanta MariaDB.",
        )
        return
    if is_store_server_online():
        if not focus_existing_store_server():
            QMessageBox.information(
                parent,
                "Servidor",
                "El servidor ya está encendido (PID en la pastilla verde).\n\n"
                "No aparece junto a WhatsApp: está en una ventana propia "
                "o en la bandeja, abajo a la derecha junto al reloj.\n\n"
                "Doble clic en el icono de la bandeja para mostrarlo.",
            )
    else:
        end_apply_guard()
        lbl.setText("Servidor: arrancando…")
        ensure_store_server_process(timeout_sec=40.0)
    pintar_badge(lbl)
