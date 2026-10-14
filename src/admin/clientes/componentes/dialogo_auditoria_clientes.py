"""Libro de auditoría de clientes: qué pasó, a quién, en qué PC, quién y cuándo. Solo lee."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtWidgets import (
    QButtonGroup, QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from src.admin.clientes.theme import _CLI
from src.clientes_fiado.oficina.huella.consulta import listar

_COLUMNAS = (
    "Fecha", "Acción", "Cliente", "Referencia", "Medio", "Id de pago",
    "Usuario", "PC", "Caja", "Llegó", "Detalle",
)
_FILTROS = (
    ("Todas", None),
    ("Cargos", ("CARGO",)),
    ("Abonos", ("ABONO",)),
    ("Borrados", ("BORRADO", "ANULACION")),
    ("Ficha", ("ALTA", "EDICION", "LIMITE", "FUSION")),
)
_TONO = {
    "Alta": "#047857",
    "Cargo": "#B91C1C",
    "Abono": "#1D4ED8",
    "Borrado": "#64748B",
    "Anulación": "#475569",
    "Unido": "#B45309",
}
_CHIP = """
    QPushButton {{
        background: white; color: #334155; border: 1px solid #E2E8F0;
        border-radius: 16px; padding: 8px 14px; font-weight: 800; font-size: 12px;
    }}
    QPushButton:hover {{ border-color: #3B82F6; }}
    QPushButton:checked {{ background: #3B82F6; color: white; border-color: #3B82F6; }}
"""


class DialogoAuditoriaClientes(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Auditoría de clientes")
        self.setMinimumSize(1100, 680)
        self.resize(1280, 760)
        self.setStyleSheet(f"QDialog {{ background: {_CLI['bg']}; }}")
        self._filtro = None
        self._armar()
        self._pintar()

    def _armar(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 32)
        lay.setSpacing(16)

        titulo = QLabel("AUDITORÍA DE CLIENTES")
        titulo.setStyleSheet(
            f"color: {_CLI['text']}; font-size: 22px; font-weight: 900; background: transparent;"
            " padding: 4px 0 2px 0;"
        )
        lay.addWidget(titulo)
        sub = QLabel(
            "Misma referencia que la planilla: COB- del abono, ticket de venta del cargo, "
            "id de pago digital o F9 MANUAL. Borrado deja el cargo a la vista. "
            "Lo hecho sin red dice si ya llegó a la tienda."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #64748B; font-size: 13px; background: transparent;")
        lay.addWidget(sub)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        grupo = QButtonGroup(self)
        grupo.setExclusive(True)
        for texto, claves in _FILTROS:
            chip = QPushButton(texto)
            chip.setCheckable(True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.setStyleSheet(_CHIP)
            chip.clicked.connect(lambda _=False, c=claves: self._elegir(c))
            grupo.addButton(chip)
            chips.addWidget(chip)
            if texto == "Todas":
                chip.setChecked(True)
        chips.addStretch()
        lay.addLayout(chips)

        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("Buscar cliente, COB-, PC, usuario, acción o id de pago")
        self.buscar.setMinimumHeight(48)
        self.buscar.setStyleSheet(
            f"QLineEdit {{ padding: 12px 16px; border: 1px solid {_CLI['border']}; "
            f"border-radius: 12px; background: white; color: {_CLI['text']}; font-size: 15px; }}"
        )
        self.buscar.textChanged.connect(self._pintar)
        lay.addWidget(self.buscar)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(_COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(list(_COLUMNAS))
        cab = self.tabla.horizontalHeader()
        for col in range(len(_COLUMNAS)):
            cab.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(10, QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(44)
        self.tabla.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {_CLI['border']}; border-radius: 14px;
                background: white; alternate-background-color: {_CLI['row_alt']};
                color: {_CLI['text']}; font-size: 13px; gridline-color: {_CLI['border']};
                padding: 6px;
            }}
            QHeaderView::section {{
                font-weight: 900; border: none; padding: 14px 10px;
                background: {_CLI['header_bg']}; color: #334155; font-size: 12px;
            }}
        """)
        lay.addWidget(self.tabla, 1)

        pie = QHBoxLayout()
        pie.setContentsMargins(0, 8, 0, 4)
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

    def _elegir(self, claves):
        self._filtro = claves
        self._pintar()

    def _pintar(self):
        filas = listar(self.buscar.text())
        if self._filtro:
            filas = [f for f in filas if f.get("accion_raw") in self._filtro]
        self.tabla.setRowCount(len(filas))
        for i, f in enumerate(filas):
            valores = (
                f["fecha"], f["accion"], f["cliente"] or "—", f.get("referencia") or "—",
                f.get("medio") or "—", f.get("id_pago") or "—",
                f["usuario"] or "—", f["pc"] or "—", f["caja"] or "—",
                f["llegada"], f["detalle"],
            )
            borrado = f.get("accion_raw") in ("BORRADO", "ANULACION")
            for col, texto in enumerate(valores):
                item = QTableWidgetItem(str(texto))
                if col == 1 and texto in _TONO:
                    item.setForeground(QColor(_TONO[texto]))
                if col == 2 and f.get("uid"):
                    item.setToolTip(f"ID {f['uid']}")
                if col == 3 and texto not in ("—", ""):
                    item.setToolTip("Misma clave que historial o planilla de cobros.")
                if col == 5 and texto not in ("—", ""):
                    item.setForeground(QColor("#1D4ED8"))
                if col == 9 and "no aplicado" in str(texto):
                    item.setForeground(QColor("#B45309"))
                if col == 9 and str(texto).startswith("Pendiente"):
                    item.setForeground(QColor("#B45309"))
                if borrado:
                    item.setForeground(QColor("#64748B"))
                    item.setBackground(QBrush(QColor("#F8FAFC")))
                self.tabla.setItem(i, col, item)
        self.lbl_total.setText(f"{len(filas)} eventos" + (" (últimos 500)" if len(filas) >= 500 else ""))
