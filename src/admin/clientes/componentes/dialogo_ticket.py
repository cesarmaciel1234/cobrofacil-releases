"""Ventana de lectura del desglose de una venta desde el historial del cliente."""

from __future__ import annotations

from src.utils.qt_compat import qt_exec
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class _CargarTicket(QThread):
    listo = pyqtSignal(object, str)

    def __init__(self, ticket: str, parent=None):
        super().__init__(parent)
        self.ticket = ticket

    def run(self):
        try:
            from src.clientes_fiado.oficina.ticket.motor import motor_ticket

            self.listo.emit(motor_ticket.detalle(self.ticket), "")
        except Exception as error:
            from src.logger import logger

            logger.warning(f"[Historial clientes] No se pudo leer el ticket {self.ticket}: {error}")
            self.listo.emit(None, str(error))


class DialogoDetalleTicket(QDialog):
    def __init__(self, ticket: str, parent=None):
        super().__init__(parent)
        self.ticket = ticket
        self.setWindowTitle(f"Detalle del ticket #{ticket}")
        self.setMinimumSize(650, 430)
        self.resize(760, 520)
        self.setStyleSheet("QDialog { background: #F1F5F9; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(12)

        self.titulo = QLabel(f"DETALLE DEL TICKET  #{ticket}")
        self.titulo.setStyleSheet("font-size: 18px; font-weight: 900; color: #1E293B;")
        layout.addWidget(self.titulo)

        self.resumen = QLabel("Buscando la venta y sus artículos…")
        self.resumen.setStyleSheet("font-size: 13px; color: #64748B;")
        layout.addWidget(self.resumen)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Cant.", "Descripción", "Precio", "Importe"])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setColumnWidth(0, 75)
        self.tabla.setColumnWidth(2, 120)
        self.tabla.setColumnWidth(3, 130)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet(
            "QTableWidget { background: white; alternate-background-color: #F8FAFC; "
            "border: 1px solid #CBD5E1; font-size: 13px; }"
            "QHeaderView::section { background: #E2E8F0; color: #334155; "
            "font-weight: 800; padding: 9px; border: none; }"
        )
        layout.addWidget(self.tabla, stretch=1)

        pie = QHBoxLayout()
        self.origen = QLabel("")
        self.origen.setStyleSheet("font-size: 11px; color: #64748B;")
        pie.addWidget(self.origen, stretch=1)
        self.total = QLabel("")
        self.total.setStyleSheet("font-size: 17px; font-weight: 900; color: #1E40AF;")
        pie.addWidget(self.total)
        layout.addLayout(pie)

        botones = QHBoxLayout()
        botones.addStretch()
        cerrar = QPushButton("CERRAR")
        cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        cerrar.setStyleSheet(
            "QPushButton { background: #3B82F6; color: white; font-weight: 900; "
            "padding: 10px 24px; border-radius: 8px; border: none; }"
            "QPushButton:hover { background: #2563EB; }"
        )
        cerrar.clicked.connect(self.accept)
        botones.addWidget(cerrar)
        layout.addLayout(botones)

        app = QApplication.instance()
        self._carga = _CargarTicket(ticket, app)
        self._carga.listo.connect(self._mostrar)
        self._carga.finished.connect(self._carga.deleteLater)
        self._carga.start()

    @staticmethod
    def _monto(valor) -> float:
        try:
            return float(valor or 0)
        except (TypeError, ValueError):
            return 0.0

    def _mostrar(self, detalle, error: str):
        if error:
            self.resumen.setText("No se pudo consultar el ticket. La cuenta del cliente no fue modificada.")
            self.resumen.setToolTip(error)
            return
        if not detalle:
            self.resumen.setText(
                "El ticket no está disponible en la maestra, la copia portable ni la base local."
            )
            return

        venta = detalle["venta"]
        fecha = str(venta.get("fecha") or "Fecha no disponible")
        metodo = str(venta.get("metodo_pago") or "Medio no disponible")
        estado = str(venta.get("estado") or "Estado no disponible")
        self.resumen.setText(f"{fecha}  ·  {metodo}  ·  {estado}")
        self.origen.setText(f"Datos: {detalle['origen']}")
        items = detalle["items"]
        self.tabla.setRowCount(len(items))
        for fila, item in enumerate(items):
            cantidad = self._monto(item.get("cantidad"))
            precio = self._monto(item.get("precio_unitario"))
            subtotal = self._monto(item.get("subtotal"))
            valores = (
                f"{cantidad:g}",
                str(item.get("nombre_producto") or "Artículo"),
                f"${precio:,.2f}",
                f"${subtotal:,.2f}",
            )
            for columna, texto in enumerate(valores):
                celda = QTableWidgetItem(texto)
                if columna in (0, 2, 3):
                    celda.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabla.setItem(fila, columna, celda)
        if not items:
            self.resumen.setText(self.resumen.text() + "  ·  El ticket no tiene renglones disponibles.")
        self.total.setText(f"Total: ${self._monto(venta.get('total')):,.2f}")


def abrir_detalle_ticket(ticket: str, parent=None):
    dialogo = DialogoDetalleTicket(ticket, parent)
    qt_exec(dialogo)
