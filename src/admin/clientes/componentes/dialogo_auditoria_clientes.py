"""Libro de auditoría de clientes: qué pasó, a quién, en qué PC, quién y cuándo. Solo lee."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QFont
from PyQt6.QtWidgets import (
    QButtonGroup, QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from src.admin.clientes.theme import _CLI
from src.clientes_fiado.oficina.huella.consulta import listar
from src.utils.letra import vestir_id, vestir_nombre, vestir_numero

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
    "Borrado": "#475569",
    "Anulación": "#475569",
    "Unido": "#B45309",
}
_CHIP = """
    QPushButton {
        background: white; color: #334155; border: 1px solid #E2E8F0;
        border-radius: 16px; padding: 8px 14px; font-weight: 800; font-size: 12px;
    }
    QPushButton:hover { border-color: #3B82F6; }
    QPushButton:checked { background: #3B82F6; color: white; border-color: #3B82F6; }
"""


class DialogoAuditoriaClientes(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Auditoría de clientes")
        self.setMinimumSize(1150, 700)
        self.resize(1320, 780)
        self.setStyleSheet(f"QDialog {{ background: {_CLI['bg']}; }}")
        self._filtro = None
        self._armar()
        self._pintar()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ajustar_columnas()

    def _ajustar_columnas(self):
        if not hasattr(self, "tabla") or self.tabla.columnCount() < len(_COLUMNAS):
            return
        vw = self.tabla.viewport().width()
        if vw <= 100:
            return
        # Anchos base proporcionales y estables (total base ~980px):
        # 0: Fecha (135), 1: Acción (80), 2: Cliente (140), 3: Referencia (100), 4: Medio (85),
        # 5: Id pago (120), 6: Usuario (80), 7: PC (150), 8: Caja (50), 9: Llegó (135)
        anchos_fijos = [135, 80, 140, 100, 85, 120, 80, 150, 50, 135]
        suma_fijos = sum(anchos_fijos)
        w_detalle = max(260, vw - suma_fijos)
        for c in range(10):
            self.tabla.setColumnWidth(c, anchos_fijos[c])
        self.tabla.setColumnWidth(10, w_detalle)

    def _armar(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 30, 36, 28)
        lay.setSpacing(14)

        titulo = QLabel("AUDITORÍA DE CLIENTES")
        titulo.setStyleSheet(
            f"color: {_CLI['text']}; font-size: 22px; font-weight: 900; background: transparent;"
            " padding: 2px 0;"
        )
        lay.addWidget(titulo)
        sub = QLabel(
            "Misma referencia que la planilla: COB- del abono, ticket de venta del cargo, "
            "id de pago digital o F9 MANUAL. Borrado deja el cargo a la vista. "
            "Lo hecho sin red dice si ya llegó a la tienda."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {_CLI['text_sec']}; font-size: 13px; background: transparent;")
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
        self.buscar.setPlaceholderText("Buscar cliente, COB-, PC, usuario, acción o id de pago…")
        self.buscar.setMinimumHeight(46)
        self.buscar.setStyleSheet(
            f"QLineEdit {{ padding: 10px 16px; border: 1px solid {_CLI['border']}; "
            f"border-radius: 12px; background: white; color: {_CLI['text']}; font-size: 14px; }}"
        )
        self.buscar.textChanged.connect(self._pintar)
        lay.addWidget(self.buscar)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(_COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(list(_COLUMNAS))
        cab = self.tabla.horizontalHeader()
        for col in range(len(_COLUMNAS)):
            cab.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        cab.setStretchLastSection(True)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(42)
        self.tabla.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {_CLI['border']}; border-radius: 14px;
                background: white; alternate-background-color: {_CLI['row_alt']};
                color: {_CLI['text']}; font-size: 13px; gridline-color: {_CLI['border']};
                padding: 4px;
            }}
            QHeaderView::section {{
                font-weight: 900; border: none; padding: 12px 8px;
                background: {_CLI['header_bg']}; color: #334155; font-size: 12px;
            }}
        """)
        lay.addWidget(self.tabla, 1)

        pie = QHBoxLayout()
        pie.setContentsMargins(0, 6, 0, 2)
        self.lbl_total = QLabel("")
        self.lbl_total.setStyleSheet(
            f"color: {_CLI['text']}; font-size: 15px; font-weight: 800; background: transparent;"
        )
        cerrar = QPushButton("Cerrar")
        cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        cerrar.setMinimumHeight(44)
        cerrar.setStyleSheet(
            f"QPushButton {{ background: white; color: {_CLI['text']}; border: 1px solid {_CLI['border']}; "
            "border-radius: 12px; padding: 10px 26px; font-weight: 800; font-size: 14px; }"
            f"QPushButton:hover {{ background: {_CLI['row_alt']}; border-color: #94A3B8; }}"
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
                item.setToolTip(str(texto))

                # Letras de góndola por columna:
                if col == 0:  # Fecha
                    vestir_numero(item)
                elif col == 1:  # Acción
                    f_bold = QFont("Segoe UI", 11)
                    f_bold.setBold(True)
                    item.setFont(f_bold)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if texto in _TONO:
                        item.setForeground(QColor(_TONO[texto]))
                elif col == 2:  # Cliente
                    vestir_nombre(item)
                    if f.get("uid"):
                        item.setToolTip(f"{texto}\nUID: {f['uid']}")
                elif col == 3:  # Referencia (COB-xxx, #xxx, Cargo #xxx)
                    vestir_id(item)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if texto not in ("—", ""):
                        item.setToolTip(f"Referencia: {texto} (misma clave en historial y planilla)")
                elif col == 4:  # Medio
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    f_medio = QFont("Segoe UI", 10)
                    f_medio.setBold(True)
                    item.setFont(f_medio)
                elif col == 5:  # Id de pago
                    vestir_id(item)
                    if texto not in ("—", ""):
                        item.setForeground(QColor("#1D4ED8"))
                elif col == 6:  # Usuario
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif col == 7:  # PC
                    vestir_id(item)
                elif col == 8:  # Caja
                    vestir_numero(item)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif col == 9:  # Llegó
                    if "no aplicado" in str(texto) or str(texto).startswith("Pendiente"):
                        item.setForeground(QColor("#B45309"))
                elif col == 10:  # Detalle
                    vestir_numero(item)

                if borrado:
                    item.setForeground(QColor("#475569"))
                    item.setBackground(QBrush(QColor("#F8FAFC")))
                self.tabla.setItem(i, col, item)
        self.lbl_total.setText(f"{len(filas)} eventos" + (" (últimos 500)" if len(filas) >= 500 else ""))
        self._ajustar_columnas()
