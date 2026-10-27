"""Ventana que el usuario ve. El oficio no se decide acá."""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.central_red_global.servidor.ventana.tablero import Tablero
from src.utils.candados import STORE_SERVER_WINDOW_TITLE
from src.utils.paths import get_resource_path

_HOJA = """
QWidget#ServidorMarco, QWidget#TableroNodo, QWidget#CajaNodo {
    background: #0B1220;
    color: #E2E8F0;
}
QLabel { background: transparent; border: none; color: #E2E8F0; }
QTextEdit#ConsolaServidor {
    background: #020617;
    color: #86EFAC;
    border: 1px solid #1E293B;
    border-radius: 10px;
    padding: 10px 12px;
    selection-background-color: #1E3A8A;
}
QPushButton#BtnOcultar {
    background: #1E293B; color: #E2E8F0; font-weight: 600;
    padding: 8px 14px; border-radius: 8px; border: 1px solid #334155;
}
QPushButton#BtnOcultar:hover { background: #334155; }
QPushButton#BtnApagar {
    background: #7F1D1D; color: #FEE2E2; font-weight: 700;
    padding: 8px 14px; border-radius: 8px; border: 1px solid #B91C1C;
}
QPushButton#BtnApagar:hover { background: #991B1B; }
"""

_TONO = {
    "ok": "#86EFAC",
    "aviso": "#FCD34D",
    "esclava": "#93C5FD",
    "malo": "#FCA5A5",
}


def hoja_menu() -> str:
    """El QSS global pinta todo QWidget de azul. El menú de la bandeja no."""
    return """
    QMenu {
        background: #0F172A;
        color: #E2E8F0;
        border: 1px solid #334155;
        padding: 4px;
    }
    QMenu::item {
        color: #E2E8F0;
        background: transparent;
        padding: 8px 16px;
        border-radius: 6px;
    }
    QMenu::item:selected {
        background: #1E293B;
        color: #F8FAFC;
    }
    QMenu::separator {
        height: 1px;
        background: #334155;
        margin: 4px 8px;
    }
    """


def icono_bandeja(esclava: bool) -> QIcon:
    icon_path = get_resource_path(os.path.join("src", "assets", "pos_icon.png"))
    if os.path.exists(icon_path):
        cargado = QIcon(icon_path)
        if not cargado.isNull():
            return cargado
    lienzo = QPixmap(32, 32)
    lienzo.fill(Qt.GlobalColor.transparent)
    pincel = QPainter(lienzo)
    pincel.setRenderHint(QPainter.RenderHint.Antialiasing)
    pincel.setBrush(QColor("#1D4ED8" if esclava else "#15803D"))
    pincel.setPen(Qt.PenStyle.NoPen)
    pincel.drawRoundedRect(1, 1, 30, 30, 8, 8)
    pincel.setPen(QColor("#FFFFFF"))
    letra = pincel.font()
    letra.setBold(True)
    letra.setPixelSize(16)
    pincel.setFont(letra)
    pincel.drawText(lienzo.rect(), int(Qt.AlignmentFlag.AlignCenter), "E" if esclava else "S")
    pincel.end()
    return QIcon(lienzo)


class ServidorMarco(QWidget):
    """El cierre lo atiende bandeja. Si no es subclase, Qt ignora el closeEvent."""

    def __init__(self):
        super().__init__()
        self._al_cerrar = None

    def closeEvent(self, event):
        event.ignore()
        if self._al_cerrar is not None:
            self._al_cerrar()


def armar_lienzo(esclava: bool) -> dict:
    """Arma la ventana. No la muestra: eso lo hace `bandeja.py`."""
    win = ServidorMarco()
    win.setObjectName("ServidorMarco")
    win.setWindowTitle(STORE_SERVER_WINDOW_TITLE)
    win.setMinimumSize(980, 700)
    win.resize(1120, 780)
    win.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
    win.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
    win.setAutoFillBackground(True)
    win.setStyleSheet(_HOJA)

    lay = QVBoxLayout(win)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(0)

    acento = QFrame()
    acento.setFixedHeight(4)
    acento.setStyleSheet(
        "background: #2563EB; border: none;" if esclava else "background: #16A34A; border: none;"
    )
    lay.addWidget(acento)

    cuerpo = QVBoxLayout()
    cuerpo.setContentsMargins(22, 16, 22, 16)
    cuerpo.setSpacing(10)

    fila = QHBoxLayout()
    title = QLabel("Servidor Cobro Fácil")
    title.setStyleSheet("font-size: 20px; font-weight: 700; color: #F8FAFC;")
    fila.addWidget(title)
    fila.addStretch()

    puesto = QLabel("ESCLAVA" if esclava else "MAESTRA")
    puesto.setStyleSheet(
        "font-size: 11px; font-weight: 700; color: #DBEAFE; background: #1E3A8A;"
        "border-radius: 8px; padding: 4px 10px;"
        if esclava
        else "font-size: 11px; font-weight: 700; color: #DCFCE7; background: #14532D;"
        "border-radius: 8px; padding: 4px 10px;"
    )
    fila.addWidget(puesto)
    cuerpo.addLayout(fila)

    status = QLabel("ESCLAVA — arrancando" if esclava else "Iniciando…")
    status.setWordWrap(True)
    status.setStyleSheet("font-size: 13px; font-weight: 600; color: #93C5FD;")
    cuerpo.addWidget(status)

    detail = QLabel(
        "Copia de backups y pulso de cartelería. Esta PC no abre MariaDB."
        if esclava
        else "MariaDB · API :8000 · Discovery UDP :37020"
    )
    detail.setWordWrap(True)
    detail.setStyleSheet("font-size: 12px; color: #94A3B8;")
    cuerpo.addWidget(detail)

    consola = Tablero()
    cuerpo.addWidget(consola, 1)

    row = QHBoxLayout()
    btn_hide = QPushButton("Ocultar en bandeja")
    btn_hide.setObjectName("BtnOcultar")
    btn_hide.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_stop = QPushButton("Apagar servidor")
    btn_stop.setObjectName("BtnApagar")
    btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
    row.addWidget(btn_hide)
    row.addStretch()
    row.addWidget(btn_stop)
    cuerpo.addLayout(row)

    lay.addLayout(cuerpo, 1)

    def poner_estado(texto: str, tono: str = "esclava") -> None:
        status.setText(texto)
        status.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {_TONO.get(tono, '#E2E8F0')};"
        )

    return {
        "win": win,
        "status": status,
        "detail": detail,
        "consola": consola,
        "poner_estado": poner_estado,
        "btn_hide": btn_hide,
        "btn_stop": btn_stop,
    }
