"""Libro de auditoría de clientes: qué pasó, a quién, en qué PC, quién y cuándo. Solo lee."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from src.admin.clientes.theme import _CLI
from src.clientes_fiado.oficina.huella.consulta import listar

_COLUMNAS = ("Fecha", "Acción", "Cliente", "PC", "Caja", "Usuario", "Llegó", "Detalle")
_TONO = {
    "Alta": "#047857",
    "Cargo": "#B91C1C",
    "Abono": "#1D4ED8",
    "Unido": "#B45309",
}


class DialogoAuditoriaClientes(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Auditoría de clientes")
        self.resize(1240, 700)
        self.setStyleSheet(f"QDialog {{ background: {_CLI['bg']}; }}")
        self._armar()
        self._pintar()

    def _armar(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 32)
        lay.setSpacing(18)

        titulo = QLabel("AUDITORÍA DE CLIENTES")
        titulo.setStyleSheet(
            f"color: {_CLI['text']}; font-size: 22px; font-weight: 900; background: transparent;"
            " padding: 4px 0 2px 0;"
        )
        lay.addWidget(titulo)
        sub = QLabel(
            "Cada alta, edición, límite, cargo y abono con su ID único, la PC, el usuario y la hora. "
            "Lo cargado sin red dice por dónde llegó."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #64748B; font-size: 13px; background: transparent;")
        lay.addWidget(sub)

        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("Buscar cliente, PC, usuario, acción o ID")
        self.buscar.setMinimumHeight(48)
        self.buscar.setStyleSheet(
            f"QLineEdit {{ padding: 12px 16px; border: 1px solid {_CLI['border']}; "
            f"border-radius: 12px; background: white; color: {_CLI['text']}; font-size: 15px; }}"
        )
        self.buscar.returnPressed.connect(self._pintar)
        self.buscar.textChanged.connect(lambda t: self._pintar() if not t else None)
        lay.addWidget(self.buscar)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(_COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(list(_COLUMNAS))
        cab = self.tabla.horizontalHeader()
        for col in range(len(_COLUMNAS)):
            cab.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(44)
        self.tabla.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {_CLI['border']}; border-radius: 14px;
                background: white; alternate-background-color: {_CLI['row_alt']};
                color: {_CLI['text']}; font-size: 14px; gridline-color: {_CLI['border']};
                padding: 6px;
            }}
            QHeaderView::section {{
                font-weight: 900; border: none; padding: 14px 12px;
                background: {_CLI['header_bg']}; color: #334155; font-size: 12px;
            }}
        """)
        lay.addWidget(self.tabla, 1)

        pie = QHBoxLayout()
        pie.setContentsMargins(0, 12, 0, 4)
        self.lbl_total = QLabel("")
        self.lbl_total.setStyleSheet(
            f"color: {_CLI['text']}; font-size: 16px; font-weight: 800; background: transparent;"
        )
        cerrar = QPushButton("Cerrar")
        cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        cerrar.setMinimumHeight(48)
        cerrar.setStyleSheet(
            f"QPushButton {{ background: white; color: {_CLI['text']}; border: 1px solid {_CLI['border']}; "
            "border-radius: 12px; padding: 12px 28px; font-weight: 800; font-size: 14px; }"
        )
        cerrar.clicked.connect(self.accept)
        pie.addWidget(self.lbl_total)
        pie.addStretch()
        pie.addWidget(cerrar)
        lay.addLayout(pie)

    def _pintar(self):
        filas = listar(self.buscar.text())
        self.tabla.setRowCount(len(filas))
        for i, f in enumerate(filas):
            valores = (
                f["fecha"], f["accion"], f["cliente"] or "—", f["pc"] or "—",
                f["caja"] or "—", f["usuario"] or "—", f["llegada"], f["detalle"],
            )
            for col, texto in enumerate(valores):
                item = QTableWidgetItem(str(texto))
                if col == 1 and texto in _TONO:
                    item.setForeground(QColor(_TONO[texto]))
                if col == 2 and f.get("uid"):
                    item.setToolTip(f"ID {f['uid']}")
                if col == 6 and "no aplicado" in str(texto):
                    item.setForeground(QColor("#B45309"))
                self.tabla.setItem(i, col, item)
        self.lbl_total.setText(f"{len(filas)} eventos" + (" (últimos 500)" if len(filas) >= 500 else ""))
