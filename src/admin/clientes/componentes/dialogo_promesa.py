"""Diálogo mínimo: fecha de promesa de pago + nota (modo barrial)."""

from datetime import datetime

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QDateEdit,
)

from src.admin.clientes.theme import _CLI
from src.utils.qt_compat import qt_exec


class DialogoPromesa(QDialog):
    def __init__(self, cliente_id, nombre, fecha_actual=None, nota_actual="", parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.setWindowTitle("Promesa de pago")
        self.setModal(True)
        self.setFixedWidth(420)
        self.setStyleSheet(
            f"QDialog {{ background: white; }} "
            f"QLabel {{ color: {_CLI['text']}; border: none; }}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        tit = QLabel(f"Promesa — {nombre}")
        tit.setStyleSheet("font-size: 16px; font-weight: 900;")
        lay.addWidget(tit)
        sub = QLabel("Fecha en que el cliente dijo que paga. No escribe interés.")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {_CLI['text_sec']}; font-size: 12px;")
        lay.addWidget(sub)

        lay.addWidget(QLabel("Fecha"))
        self.fecha = QDateEdit()
        self.fecha.setCalendarPopup(True)
        self.fecha.setDisplayFormat("dd/MM/yyyy")
        self.fecha.setMinimumHeight(36)
        if fecha_actual:
            try:
                dt = datetime.strptime(str(fecha_actual)[:10], "%Y-%m-%d")
                self.fecha.setDate(QDate(dt.year, dt.month, dt.day))
            except ValueError:
                self.fecha.setDate(QDate.currentDate().addDays(7))
        else:
            self.fecha.setDate(QDate.currentDate().addDays(7))
        lay.addWidget(self.fecha)

        lay.addWidget(QLabel("Nota (opcional)"))
        self.nota = QLineEdit()
        self.nota.setPlaceholderText("Ej. paga el viernes con transferencia")
        self.nota.setText(str(nota_actual or ""))
        self.nota.setMinimumHeight(36)
        lay.addWidget(self.nota)

        botones = QHBoxLayout()
        btn_limpiar = QPushButton("Quitar promesa")
        btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_limpiar.clicked.connect(self._limpiar)
        botones.addWidget(btn_limpiar)
        botones.addStretch()
        btn_ok = QPushButton("Guardar")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet(
            "background: #1D4ED8; color: white; border: none; border-radius: 8px; "
            "padding: 10px 18px; font-weight: 800;"
        )
        btn_ok.clicked.connect(self._guardar)
        botones.addWidget(btn_ok)
        lay.addLayout(botones)

        self._resultado = None  # ("fijar", date_str, nota) | ("limpiar",) | None

    def _guardar(self):
        qd = self.fecha.date()
        self._resultado = (
            "fijar",
            qd.toString("yyyy-MM-dd"),
            self.nota.text().strip(),
        )
        self.accept()

    def _limpiar(self):
        self._resultado = ("limpiar",)
        self.accept()

    @staticmethod
    def pedir(cliente_id, nombre, fecha_actual=None, nota_actual="", parent=None):
        dlg = DialogoPromesa(cliente_id, nombre, fecha_actual, nota_actual, parent)
        if qt_exec(dlg) != QDialog.DialogCode.Accepted:
            return None
        return dlg._resultado
