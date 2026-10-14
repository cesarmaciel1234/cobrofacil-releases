"""Letras de góndola. Referencia visual: Admin → Etiquetas de góndola.

Tablas: QFont Bold en la celda (Consolas para id, Segoe UI para nombre y plata).
Títulos y KPIs: QSS weight 900 solo en QLabel.
Nunca QSS 900 y setBold en el mismo widget: en Windows se pintan letras dobles.
No usar en `src/cajero`.
"""

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QTableWidgetItem

QSS_TITULO = "font-size: 24px; font-weight: 900; letter-spacing: 1px;"
QSS_KPI = "font-size: 26px; font-weight: 900; letter-spacing: -0.5px;"
QSS_ROTULO = "font-size: 11px; font-weight: 900; letter-spacing: 1px;"


def fuente_id(px: int = 10) -> QFont:
    f = QFont("Consolas", px)
    f.setBold(True)
    return f


def fuente_nombre(px: int = 11) -> QFont:
    f = QFont("Segoe UI", px)
    f.setBold(True)
    return f


def fuente_numero(px: int = 11) -> QFont:
    return fuente_nombre(px)


def vestir_id(item: QTableWidgetItem) -> QTableWidgetItem:
    item.setFont(fuente_id())
    return item


def vestir_nombre(item: QTableWidgetItem) -> QTableWidgetItem:
    item.setFont(fuente_nombre())
    return item


def vestir_numero(item: QTableWidgetItem) -> QTableWidgetItem:
    item.setFont(fuente_numero())
    return item
