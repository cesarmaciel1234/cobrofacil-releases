"""Planilla de los cargos (fiados / deuda). El ticket es el de la venta, no un COB."""
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QBrush, QFont
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from src.admin.clientes.theme import _CLI
from src.admin.clientes.componentes.filtro_periodo import (
    filtrar_por_rango,
    montar_chips,
    pintar_chips,
    resolver_ui,
)
from src.clientes_fiado.cerebro.cerebro import cerebro

_COLUMNAS = (
    "Fecha", "Ticket", "Cliente", "DNI", "Monto", "Origen", "Estado", "Saldo", "Descripción",
)
_ESTADOS = ("Todos", "Vivos", "Borrados", "Cancelados")
_ESTADO_CLAVE = {
    "Todos": None,
    "Vivos": "vivo",
    "Borrados": "borrado",
    "Cancelados": "cancelado",
}


class DialogoCargos(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cargos")
        self.setMinimumSize(1080, 680)
        self.resize(1220, 760)
        self.setStyleSheet(f"QDialog {{ background: {_CLI['bg']}; }}")
        self._filas = cerebro.listar_cargos()
        self._periodo = "Mes"
        self._rango = resolver_ui("Mes", self)
        self._timer_filtro = QTimer(self)
        self._timer_filtro.setSingleShot(True)
        self._timer_filtro.setInterval(220)
        self._timer_filtro.timeout.connect(self._pintar)
        self._armar()
        self._pintar()

    def _armar(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 32)
        lay.setSpacing(16)

        titulo = QLabel("CARGOS")
        titulo.setStyleSheet(
            f"color: {_CLI['text']}; font-size: 22px; font-weight: 900; background: transparent;"
            " padding: 4px 0 2px 0;"
        )
        lay.addWidget(titulo)
        sub = QLabel(
            "Ticket = #venta del cargo (o MANUAL si se cargó desde el panel). "
            "Un CARGO suma deuda. Borrado / Cancelado quedan tachados y no cuentan en el total vivo."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {_CLI['text_sec']}; font-size: 13px; background: transparent;")
        lay.addWidget(sub)

        chips, self._chips_periodo, _g = montar_chips(
            self, self._elegir, activo="Mes", color_activo="#DC2626"
        )
        lay.addLayout(chips)

        barra = QHBoxLayout()
        barra.setSpacing(14)
        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("Buscar cliente, DNI, ticket o descripción")
        self.buscar.setMinimumHeight(48)
        self.buscar.setStyleSheet(
            f"QLineEdit {{ padding: 12px 16px; border: 1px solid {_CLI['border']}; "
            f"border-radius: 12px; background: white; color: {_CLI['text']}; font-size: 15px; }}"
        )
        self.buscar.textChanged.connect(lambda _=None: self._timer_filtro.start())
        self.estado = QComboBox()
        self.estado.addItems(_ESTADOS)
        self.estado.setMinimumHeight(48)
        self.estado.setMinimumWidth(168)
        self.estado.setStyleSheet(
            f"QComboBox {{ padding: 10px 14px; border: 1px solid {_CLI['border']}; "
            f"border-radius: 12px; background: white; color: {_CLI['text']}; font-size: 15px; }}"
        )
        self.estado.currentTextChanged.connect(self._pintar)
        barra.addWidget(self.buscar, 1)
        barra.addWidget(self.estado)
        lay.addLayout(barra)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(_COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(list(_COLUMNAS))
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
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
            "color: #B91C1C; font-size: 16px; font-weight: 900; background: transparent;"
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
        if clave == self._periodo and clave != "Período":
            self._periodo = ""
            self._rango = None
            pintar_chips(self._chips_periodo, "", color_activo="#DC2626")
            self._pintar()
            return
        rango = resolver_ui(clave, self)
        if rango is None:
            pintar_chips(
                self._chips_periodo,
                self._periodo,
                (self._rango[2] if self._rango else ""),
                color_activo="#DC2626",
            )
            return
        self._periodo = clave
        self._rango = rango
        pintar_chips(
            self._chips_periodo, clave,
            rango[2] if clave == "Período" else "",
            color_activo="#DC2626",
        )
        self._pintar()

    def _visibles(self):
        texto = self.buscar.text().strip().lower()
        estado_clave = _ESTADO_CLAVE.get(self.estado.currentText())
        if self._rango:
            base = filtrar_por_rango(self._filas, self._rango[0], self._rango[1])
        else:
            base = list(self._filas)
        salida = []
        for fila in base:
            if estado_clave and fila.get("estado_clave") != estado_clave:
                continue
            blanco = (
                f"{fila.get('nombre', '')} {fila.get('dni', '')} "
                f"{fila.get('ticket', '')} {fila.get('descripcion', '')} {fila.get('venta_id', '')}"
            ).lower()
            if texto and texto not in blanco:
                continue
            salida.append(fila)
        return salida

    def _pintar(self):
        filas = self._visibles()
        self.tabla.setRowCount(len(filas))
        total_vivo = 0.0
        total_borrado = 0.0
        total_cancelado = 0.0
        for i, fila in enumerate(filas):
            monto = float(fila.get("monto") or 0)
            clave = fila.get("estado_clave")
            if clave == "vivo":
                total_vivo += monto
            elif clave == "borrado":
                total_borrado += monto
            elif clave == "cancelado":
                total_cancelado += monto
            valores = (
                fila.get("fecha") or "",
                fila.get("ticket") or "—",
                fila.get("nombre") or "—",
                fila.get("dni") or "—",
                f"${monto:,.2f}",
                fila.get("origen") or "—",
                fila.get("estado") or "—",
                f"${float(fila.get('saldo') or 0):,.2f}",
                fila.get("descripcion") or "—",
            )
            inactivo = clave in ("borrado", "cancelado")
            for col, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                if col == 1 and fila.get("venta_id"):
                    item.setForeground(QColor("#1D4ED8"))
                    item.setToolTip("Ticket de venta asociado al cargo")
                if col == 4:
                    item.setForeground(QColor("#DC2626" if clave == "vivo" else _CLI["muted_row"]))
                if col == 6:
                    if clave == "vivo":
                        item.setForeground(QColor("#B91C1C"))
                    elif clave == "borrado":
                        item.setForeground(QColor("#B45309"))
                    else:
                        item.setForeground(QColor("#475569"))
                if inactivo:
                    tachado = QFont()
                    tachado.setStrikeOut(True)
                    item.setFont(tachado)
                    item.setForeground(QColor(_CLI["muted_row"]))
                    item.setBackground(QBrush(QColor("#F8FAFC")))
                self.tabla.setItem(i, col, item)
        partes = [f"{len(filas)} cargos  ·  Vivos ${total_vivo:,.2f}"]
        if total_borrado:
            partes.append(f"Borrados ${total_borrado:,.2f}")
        if total_cancelado:
            partes.append(f"Cancelados ${total_cancelado:,.2f}")
        self.lbl_total.setText("    ".join(partes))
