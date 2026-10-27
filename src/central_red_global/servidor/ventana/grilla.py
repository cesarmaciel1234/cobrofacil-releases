"""Tabla de solo lectura. El tema global pinta el texto de azul; acá no."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

_HOJA = """
QTableWidget {
    background: #020617;
    color: #E2E8F0;
    gridline-color: #1E293B;
    border: 1px solid #1E293B;
    border-radius: 8px;
    selection-background-color: #1E3A8A;
    selection-color: #F8FAFC;
}
QHeaderView::section {
    background: #0F172A;
    color: #94A3B8;
    border: none;
    border-bottom: 1px solid #1E293B;
    padding: 6px 8px;
    font-weight: 700;
}
"""


class Grilla(QTableWidget):
    def __init__(self, columnas: list[str], parent=None):
        super().__init__(0, len(columnas), parent)
        self.setHorizontalHeaderLabels(columnas)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setStyleSheet(_HOJA + "QTableWidget { alternate-background-color: #0B1220; }")
        fuente = QFont("Consolas", 10)
        fuente.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(fuente)
        cabecera = self.horizontalHeader()
        cabecera.setStretchLastSection(True)
        cabecera.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cabecera.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.verticalHeader().setDefaultSectionSize(28)

    def poner(self, filas: list[tuple]) -> None:
        self.setRowCount(len(filas))
        for r, fila in enumerate(filas):
            for c, valor in enumerate(fila):
                pieza = QTableWidgetItem(str(valor))
                pieza.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                if str(valor) == "EN COLA":
                    pieza.setForeground(QColor("#FCD34D"))
                self.setItem(r, c, pieza)

    def agregar(self, fila: tuple, tope: int = 40) -> None:
        while self.rowCount() >= tope:
            self.removeRow(0)
        r = self.rowCount()
        self.insertRow(r)
        for c, valor in enumerate(fila):
            pieza = QTableWidgetItem(str(valor))
            pieza.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.setItem(r, c, pieza)
        self.scrollToBottom()
