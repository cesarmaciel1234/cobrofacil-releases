"""Planilla de los abonos. El medio es el que se eligió al cobrar."""
from collections import Counter
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtWidgets import (
    QButtonGroup, QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from src.admin.clientes.theme import _CLI
from src.clientes_fiado.cerebro.cerebro import cerebro

_COLUMNAS = (
    "Fecha", "Ticket cobro", "Cliente", "DNI", "Monto", "Medio",
    "Id de pago", "Perfil", "Registró", "Saldo",
)
_MEDIOS = ("Todos", "Efectivo", "Transferencia", "Tarjeta", "QR", "Mixto")
_PERIODOS = ("Hoy", "Semana", "Mes", "Año", "Todos")
_CHIP = """
    QPushButton {{
        background: white; color: #334155; border: 1px solid #E2E8F0;
        border-radius: 16px; padding: 8px 14px; font-weight: 800; font-size: 12px;
    }}
    QPushButton:hover {{ border-color: #3B82F6; }}
    QPushButton:checked {{ background: #3B82F6; color: white; border-color: #3B82F6; }}
"""


def _en_periodo(fecha_raw, clave):
    if clave == "Todos":
        return True
    bruto = str(fecha_raw or "")[:19]
    try:
        dt = datetime.strptime(bruto[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            dt = datetime.strptime(bruto[:10], "%Y-%m-%d")
        except ValueError:
            return True
    hoy = datetime.now().date()
    dia = dt.date()
    if clave == "Hoy":
        return dia == hoy
    if clave == "Semana":
        return (hoy - dia).days < 7 and dia <= hoy
    if clave == "Mes":
        return dia.year == hoy.year and dia.month == hoy.month
    if clave == "Año":
        return dia.year == hoy.year
    return True


class DialogoCobros(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cobros")
        self.setMinimumSize(1080, 680)
        self.resize(1220, 760)
        self.setStyleSheet(f"QDialog {{ background: {_CLI['bg']}; }}")
        self._filas = cerebro.listar_cobros()
        self._periodo = "Mes"
        self._armar()
        self._pintar()

    def _armar(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 32)
        lay.setSpacing(16)

        titulo = QLabel("COBROS")
        titulo.setStyleSheet(
            f"color: {_CLI['text']}; font-size: 22px; font-weight: 900; background: transparent;"
            " padding: 4px 0 2px 0;"
        )
        lay.addWidget(titulo)
        sub = QLabel(
            "Ticket cobro = COB-{id} del abono. Id de pago = Mercado Pago o F9 MANUAL. "
            "Efectivo queda como Caja. Un COB no es un ticket de venta."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #64748B; font-size: 13px; background: transparent;")
        lay.addWidget(sub)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)
        for clave in _PERIODOS:
            chip = QPushButton(clave)
            chip.setCheckable(True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.setStyleSheet(_CHIP)
            chip.clicked.connect(lambda _=False, c=clave: self._elegir(c))
            self._grupo.addButton(chip)
            chips.addWidget(chip)
            if clave == "Mes":
                chip.setChecked(True)
        chips.addStretch()
        lay.addLayout(chips)

        barra = QHBoxLayout()
        barra.setSpacing(14)
        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("Buscar cliente, DNI, COB- o id de pago")
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
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
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
        pie.setContentsMargins(0, 8, 0, 4)
        pie.setSpacing(16)
        self.lbl_total = QLabel("")
        self.lbl_total.setStyleSheet(
            "color: #047857; font-size: 16px; font-weight: 900; background: transparent;"
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

    def _elegir(self, clave):
        self._periodo = clave
        self._pintar()

    def _visibles(self):
        texto = self.buscar.text().strip().lower()
        medio = self.medio.currentText()
        salida = []
        for fila in self._filas:
            if not _en_periodo(fila.get("fecha_raw") or fila.get("fecha"), self._periodo):
                continue
            if medio != "Todos" and fila.get("medio") != medio:
                continue
            blanco = (
                f"{fila.get('nombre', '')} {fila.get('dni', '')} "
                f"{fila.get('ticket_cobro', '')} {fila.get('detalle', '')} {fila.get('medio', '')}"
            ).lower()
            if texto and texto not in blanco:
                continue
            salida.append(fila)
        return salida

    def _pintar(self):
        filas = self._visibles()
        claves = Counter(
            (
                str(f.get("nombre") or ""),
                round(float(f.get("monto") or 0), 2),
                str(f.get("medio") or ""),
                str(f.get("fecha_raw") or f.get("fecha") or "")[:16],
            )
            for f in filas
        )
        self.tabla.setRowCount(len(filas))
        total = 0.0
        efectivo = 0.0
        digital = 0.0
        avisos = 0
        for i, fila in enumerate(filas):
            monto = float(fila.get("monto") or 0)
            total += monto
            if fila.get("digital"):
                digital += monto
            elif str(fila.get("medio") or "").lower() == "efectivo":
                efectivo += monto
            clave = (
                str(fila.get("nombre") or ""),
                round(monto, 2),
                str(fila.get("medio") or ""),
                str(fila.get("fecha_raw") or fila.get("fecha") or "")[:16],
            )
            repetido = claves[clave] > 1
            if repetido:
                avisos += 1
            valores = (
                fila.get("fecha") or "",
                fila.get("ticket_cobro") or "—",
                fila.get("nombre") or "—",
                fila.get("dni") or "—",
                f"${monto:,.2f}",
                fila.get("medio") or "—",
                fila.get("detalle") or "—",
                fila.get("perfil") or "—",
                fila.get("quien") or "—",
                f"${float(fila.get('saldo') or 0):,.2f}",
            )
            for col, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                if col == 1 and texto not in ("—", ""):
                    item.setForeground(QColor("#0F172A"))
                    item.setToolTip("Ticket de cobro. No es el ticket de una venta.")
                if col == 5 and texto == "Efectivo":
                    item.setForeground(QColor("#047857"))
                if col == 6 and texto not in ("—", "", "Caja"):
                    item.setForeground(QColor("#1D4ED8"))
                if repetido:
                    item.setBackground(QBrush(QColor("#FEF3C7")))
                    item.setToolTip(
                        "Mismo cliente, monto, medio y minuto que otro cobro. "
                        "Cada fila tiene su COB. Revisar si se cobró más de una vez."
                    )
                self.tabla.setItem(i, col, item)
        extra = f"  ·  {avisos} coinciden en el mismo minuto" if avisos else ""
        self.lbl_total.setText(
            f"{len(filas)} cobros  ·  ${total:,.2f}    "
            f"Efectivo ${efectivo:,.2f}    Digital ${digital:,.2f}{extra}"
        )
