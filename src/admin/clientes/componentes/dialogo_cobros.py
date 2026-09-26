"""Planilla de los abonos. El medio es el que se eligió al cobrar."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from src.admin.clientes.theme import _CLI
from src.clientes_fiado.cerebro.cerebro import cerebro

_COLUMNAS = ("Fecha", "Cliente", "DNI", "Monto", "Medio", "Id / detalle", "Perfil", "Registró", "Saldo")
_MEDIOS = ("Todos", "Efectivo", "Transferencia", "Tarjeta", "QR", "Mixto")


class DialogoCobros(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cobros")
        self.resize(1140, 680)
        self.setStyleSheet(f"QDialog {{ background: {_CLI['bg']}; }}")
        self._filas = cerebro.listar_cobros()
        self._armar()
        self._pintar()

    def _armar(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 32)
        lay.setSpacing(18)

        titulo = QLabel("COBROS")
        titulo.setStyleSheet(
            f"color: {_CLI['text']}; font-size: 22px; font-weight: 900; background: transparent;"
            " padding: 4px 0 8px 0;"
        )
        lay.addWidget(titulo)

        barra = QHBoxLayout()
        barra.setSpacing(14)
        barra.setContentsMargins(0, 4, 0, 4)
        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("Buscar cliente, DNI o id de pago")
        self.buscar.setMinimumHeight(48)
        self.buscar.setStyleSheet(
            f"QLineEdit {{ padding: 12px 16px; border: 1px solid {_CLI['border']}; "
            f"border-radius: 12px; background: white; color: {_CLI['text']}; font-size: 15px; }}"
        )
        self.buscar.textChanged.connect(self._pintar)
        self.medio = QComboBox()
        self.medio.addItems(_MEDIOS)
        self.medio.setMinimumHeight(48)
        self.medio.setMinimumWidth(168)
        self.medio.setStyleSheet(
            f"QComboBox {{ padding: 10px 14px; border: 1px solid {_CLI['border']}; "
            f"border-radius: 12px; background: white; color: {_CLI['text']}; font-size: 15px; }}"
        )
        self.medio.currentTextChanged.connect(self._pintar)
        barra.addWidget(self.buscar, 1)
        barra.addWidget(self.medio)
        lay.addLayout(barra)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(_COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(list(_COLUMNAS))
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(48)
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
        pie.setSpacing(16)
        self.lbl_total = QLabel("")
        self.lbl_total.setStyleSheet(
            "color: #047857; font-size: 18px; font-weight: 900; background: transparent;"
            " padding: 6px 0;"
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

    def _visibles(self):
        texto = self.buscar.text().strip().lower()
        medio = self.medio.currentText()
        salida = []
        for fila in self._filas:
            if medio != "Todos" and fila.get("medio") != medio:
                continue
            blanco = (
                f"{fila.get('nombre', '')} {fila.get('dni', '')} "
                f"{fila.get('detalle', '')} {fila.get('medio', '')}"
            ).lower()
            if texto and texto not in blanco:
                continue
            salida.append(fila)
        return salida

    def _pintar(self):
        filas = self._visibles()
        self.tabla.setRowCount(len(filas))
        total = 0.0
        for i, fila in enumerate(filas):
            total += float(fila.get("monto") or 0)
            valores = (
                fila.get("fecha") or "",
                fila.get("nombre") or "—",
                fila.get("dni") or "—",
                f"${float(fila.get('monto') or 0):,.2f}",
                fila.get("medio") or "—",
                fila.get("detalle") or "—",
                fila.get("perfil") or "—",
                fila.get("quien") or "—",
                f"${float(fila.get('saldo') or 0):,.2f}",
            )
            for col, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                if col == 4 and texto == "Efectivo":
                    item.setForeground(QColor("#047857"))
                if col == 5 and texto not in ("—", ""):
                    item.setForeground(QColor("#1D4ED8"))
                self.tabla.setItem(i, col, item)
        self.lbl_total.setText(f"{len(filas)} cobros    ${total:,.2f}")
