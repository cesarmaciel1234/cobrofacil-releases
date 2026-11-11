"""Icono y ciclo de bandeja del Lanzador Maestro (vigila --server sin acoplar su vida)."""

from __future__ import annotations

import os
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon


def _icono_lanzador() -> QIcon:
    from src.utils.paths import get_resource_path

    for rel in (
        os.path.join("src", "icon.png"),
        os.path.join("src", "assets", "servidor.ico"),
    ):
        ruta = get_resource_path(rel)
        if os.path.isfile(ruta):
            return QIcon(ruta)
    return QIcon()


class ControladorBandejaLanzador:
    def __init__(self, win, on_quit_app):
        self._win = win
        self._on_quit_app = on_quit_app
        self._tray: QSystemTrayIcon | None = None
        self._timer_mostrar: QTimer | None = None
        self._salio = False
        self._aviso_mostrado = False

        if QSystemTrayIcon.isSystemTrayAvailable():
            icon = _icono_lanzador()
            if not icon.isNull():
                win.setWindowIcon(icon)
            tray = QSystemTrayIcon(icon, win)
            tray.setToolTip("Cobro Fácil PRO — Lanzador y Supervisor")

            menu = QMenu()
            menu.setStyleSheet(
                "QMenu { background: #FFFFFF; color: #1C1917; border: 1px solid #E7E0D8; "
                "border-radius: 8px; padding: 6px; font-family: 'Segoe UI'; font-size: 12px; } "
                "QMenu::item { padding: 8px 14px; border-radius: 6px; } "
                "QMenu::item:selected { background: #E0F2FE; color: #0369A1; }"
            )
            act_open = QAction("Abrir Lanzador", win)
            act_open.triggered.connect(self.mostrar)
            act_quit = QAction("Salir del Lanzador", win)
            act_quit.triggered.connect(self.salir)
            menu.addAction(act_open)
            menu.addSeparator()
            menu.addAction(act_quit)
            tray.setContextMenu(menu)
            tray.activated.connect(self._al_activar_tray)
            tray.show()
            self._tray = tray

            from src.utils.candados import registrar_lanzador_en_bandeja

            registrar_lanzador_en_bandeja(True)

            timer = QTimer(win)
            timer.setInterval(200)
            timer.timeout.connect(self._revisar_pedido_frente)
            timer.start()
            self._timer_mostrar = timer

    def disponible(self) -> bool:
        return self._tray is not None

    def saliendo(self) -> bool:
        return self._salio

    def _al_activar_tray(self, reason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ):
            self.mostrar()

    def _revisar_pedido_frente(self) -> None:
        from src.utils.candados import MASTER_SHOW_PATH

        if not os.path.isfile(MASTER_SHOW_PATH):
            return
        try:
            os.remove(MASTER_SHOW_PATH)
        except OSError:
            pass
        self.mostrar()

    def mostrar(self) -> None:
        if self._salio:
            return
        self._win.showNormal()
        self._win.raise_()
        self._win.activateWindow()

    def ocultar(self, silencioso: bool = False) -> None:
        if self._tray is None:
            self.salir()
            return
        self._win.hide()
        if not silencioso and not self._aviso_mostrado:
            self._aviso_mostrado = True
            self._tray.showMessage(
                "Cobro Fácil — Lanzador",
                "Queda vigilando en segundo plano. El Servidor sigue activo aparte.",
                QSystemTrayIcon.MessageIcon.Information,
                2500,
            )

    def salir(self) -> None:
        self._salio = True
        self.cerrar_limpio()
        if callable(self._on_quit_app):
            self._on_quit_app()

    def cerrar_limpio(self) -> None:
        if self._timer_mostrar is not None:
            try:
                self._timer_mostrar.stop()
            except Exception:
                pass
        try:
            from src.utils.candados import registrar_lanzador_en_bandeja

            registrar_lanzador_en_bandeja(False)
        except Exception:
            pass
        if self._tray is not None:
            try:
                self._tray.hide()
            except Exception:
                pass


def instalar_bandeja_lanzador(win, on_quit_app) -> ControladorBandejaLanzador:
    return ControladorBandejaLanzador(win, on_quit_app)
