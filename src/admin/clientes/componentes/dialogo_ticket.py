"""Panel de lectura del desglose de una venta, dentro del historial del cliente."""

from __future__ import annotations

from src.utils.qt_compat import qt_exec
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.utils.medio_pago import etiqueta_pago
from src.admin.clientes.consulta.hilo import iniciar_hilo_seguro
from src.clientes_fiado.oficina.cuenta.interes import MARCA_INTERES


def descripcion_cargo_visible(descripcion: str) -> str:
    texto = str(descripcion or "").strip()
    if texto.startswith(MARCA_INTERES):
        return MARCA_INTERES
    if not texto.upper().startswith("MANTENIMIENTO"):
        return texto
    indice_auditoria = texto.lower().find(" · cargado en ")
    if indice_auditoria > 0:
        return texto[:indice_auditoria]
    return texto


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


class PanelDetalleTicket(QFrame):
    """Desglose del ticket en la misma ventana del historial. No abre otro diálogo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._carga = None
        self.setStyleSheet(
            "QFrame#panelTicket { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; }"
        )
        self.setObjectName("panelTicket")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        self.titulo = QLabel("TICKET")
        self.titulo.setStyleSheet("font-size: 12px; font-weight: 900; color: #1E293B; border: none;")
        layout.addWidget(self.titulo)

        self.resumen = QLabel("Clic en una fila para ver ticket o cobro")
        self.resumen.setWordWrap(True)
        self.resumen.setStyleSheet("font-size: 11px; color: #1E293B; border: none;")
        layout.addWidget(self.resumen)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Cant.", "Descripción", "Precio", "Importe"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla.setColumnWidth(0, 70)
        self.tabla.setColumnWidth(2, 110)
        self.tabla.setColumnWidth(3, 120)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setMinimumHeight(100)
        self.tabla.setStyleSheet(
            "QTableWidget { background: white; alternate-background-color: #F8FAFC; "
            "border: 1px solid #CBD5E1; font-size: 12px; }"
            "QHeaderView::section { background: #E2E8F0; color: #334155; "
            "font-weight: 800; padding: 8px; border: none; }"
        )
        layout.addWidget(self.tabla, stretch=1)

        pie = QHBoxLayout()
        self.origen = QLabel("")
        self.origen.setStyleSheet("font-size: 11px; color: #1E293B; border: none;")
        pie.addWidget(self.origen, stretch=1)
        self.total = QLabel("")
        self.total.setStyleSheet("font-size: 15px; font-weight: 900; color: #1E40AF; border: none;")
        pie.addWidget(self.total)
        layout.addLayout(pie)

    def mensaje(self, texto: str):
        self._cancelar()
        self.titulo.setText("DETALLE")
        self.resumen.setText(texto)
        self.resumen.setToolTip("")
        self.origen.setText("")
        self.total.setText("")
        self.tabla.setRowCount(0)

    def mostrar_cobro(self, dato: dict):
        """Detalle de un ABONO (COB) en el panel inferior."""
        self._cancelar()
        ref = str((dato or {}).get("referencia") or "COB").strip() or "COB"
        fecha = str((dato or {}).get("fecha") or "").split(".")[0] or "—"
        monto = self._monto((dato or {}).get("monto"))
        saldo = self._monto((dato or {}).get("saldo_resultante"))
        desc = str((dato or {}).get("descripcion") or "Abono").strip()
        self.titulo.setText(f"COBRO  {ref}")
        self.resumen.setText(f"{fecha}  ·  {desc}")
        self.resumen.setToolTip("")
        self.origen.setText("Movimiento de cuenta corriente (abono)")
        self.total.setText(f"Abonado: ${monto:,.2f}")
        self.tabla.setRowCount(2)
        filas = (
            ("1", "Cobro recibido", f"${monto:,.2f}", f"${monto:,.2f}"),
            ("—", "Saldo resultante", "", f"${saldo:,.2f}"),
        )
        for i, valores in enumerate(filas):
            for col, texto in enumerate(valores):
                celda = QTableWidgetItem(texto)
                if col in (0, 2, 3):
                    celda.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                self.tabla.setItem(i, col, celda)

    def mostrar_cargo(self, dato: dict):
        """Cargo sin ticket de venta (manual / mantenimiento)."""
        self._cancelar()
        etiqueta = str((dato or {}).get("etiqueta") or (dato or {}).get("tipo") or "CARGO")
        fecha = str((dato or {}).get("fecha") or "").split(".")[0] or "—"
        monto = self._monto((dato or {}).get("monto"))
        saldo = self._monto((dato or {}).get("saldo_resultante"))
        desc = str((dato or {}).get("descripcion") or "Cargo").strip()
        desc_visible = descripcion_cargo_visible(desc)
        self.titulo.setText(etiqueta)
        self.resumen.setText(f"{fecha}  ·  {desc_visible}")
        self.resumen.setToolTip(desc if desc_visible != desc else "")
        self.origen.setText("Sin ticket de venta asociado")
        self.total.setText(f"Monto: ${monto:,.2f}")
        self.tabla.setRowCount(2)
        filas = (
            ("1", desc_visible[:80] or "Cargo", f"${monto:,.2f}", f"${monto:,.2f}"),
            ("—", "Saldo resultante", "", f"${saldo:,.2f}"),
        )
        for i, valores in enumerate(filas):
            for col, texto in enumerate(valores):
                celda = QTableWidgetItem(texto)
                if col == 1 and desc_visible != desc:
                    celda.setToolTip(desc)
                if col in (0, 2, 3):
                    celda.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                self.tabla.setItem(i, col, celda)

    def cargar(self, ticket: str):
        self._cancelar()
        self.titulo.setText(f"TICKET  #{ticket}")
        self.resumen.setText("Buscando la venta y sus artículos…")
        self.resumen.setToolTip("")
        self.origen.setText("")
        self.total.setText("")
        self.tabla.setRowCount(0)
        hilo = _CargarTicket(ticket)
        self._carga = hilo
        hilo.listo.connect(self._mostrar)
        hilo.finished.connect(self._al_terminar)
        iniciar_hilo_seguro(hilo)

    def _cancelar(self):
        hilo = self._carga
        self._carga = None
        if hilo is None:
            return
        try:
            hilo.listo.disconnect(self._mostrar)
        except (TypeError, RuntimeError):
            pass

    def _al_terminar(self):
        hilo = self.sender()
        if self._carga is hilo:
            self._carga = None

    @staticmethod
    def _monto(valor) -> float:
        try:
            return float(valor or 0)
        except (TypeError, ValueError):
            return 0.0

    def _mostrar(self, detalle, error: str):
        # Ignora resultados de un hilo que ya se canceló al abrir otro ticket.
        if self.sender() is not None and self.sender() is not self._carga:
            return
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
        metodo = etiqueta_pago(venta.get("metodo_pago")) or "Medio no disponible"
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
                celda.setToolTip(texto)
                if columna in (0, 2, 3):
                    celda.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabla.setItem(fila, columna, celda)
        if not items:
            self.resumen.setText(self.resumen.text() + "  ·  El ticket no tiene renglones disponibles.")
        self.total.setText(f"Total: ${self._monto(venta.get('total')):,.2f}")


class DialogoDetalleTicket(QDialog):
    """Ventana emergente limpia para visualizar el desglose del ticket, cobro o cargo."""

    def __init__(self, dato_o_ticket, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumSize(720, 480)
        self.resize(800, 520)
        self.setStyleSheet("""
            QDialog { background: #F8FAFC; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.panel = PanelDetalleTicket(self)
        layout.addWidget(self.panel, stretch=1)

        botones = QHBoxLayout()
        botones.setSpacing(8)

        self.ticket_id = ""
        self.btn_imprimir = QPushButton("🖨 IMPRIMIR COPIA TICKET")
        self.btn_imprimir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_imprimir.setStyleSheet(
            "QPushButton { background: white; color: #0F172A; font-weight: 800; "
            "padding: 10px 18px; border-radius: 8px; border: 1px solid #CBD5E1; font-size: 12px; }"
            "QPushButton:hover { background: #F1F5F9; border-color: #94A3B8; }"
        )
        self.btn_imprimir.clicked.connect(self._imprimir_copia)
        self.btn_imprimir.setVisible(False)
        botones.addWidget(self.btn_imprimir)

        botones.addStretch()

        cerrar = QPushButton("CERRAR")
        cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        cerrar.setDefault(True)
        cerrar.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: 900; "
            "padding: 10px 24px; border-radius: 8px; border: none; font-size: 13px; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        cerrar.clicked.connect(self.accept)
        botones.addWidget(cerrar)
        layout.addLayout(botones)

        self._cargar_contenido(dato_o_ticket)

    def _cargar_contenido(self, dato_o_ticket):
        if isinstance(dato_o_ticket, dict):
            dato = dato_o_ticket
            ticket = str(dato.get("venta_id") or "").strip()
            tipo = str(dato.get("tipo") or "").upper()
            if ticket and tipo in ("CARGO", "ANULACION"):
                self.ticket_id = ticket
                self.setWindowTitle(f"Detalle del ticket #{ticket}")
                self.btn_imprimir.setVisible(True)
                self.panel.cargar(ticket)
            elif tipo == "ABONO":
                cob = dato.get("referencia") or f"COB-{dato.get('id')}"
                self.setWindowTitle(f"Detalle del cobro {cob}")
                self.panel.mostrar_cobro(dato)
            elif dato.get("manual") or not ticket:
                self.setWindowTitle(f"Detalle del cargo #{dato.get('id') or ''}")
                self.panel.mostrar_cargo(dato)
            else:
                self.panel.mensaje(str(dato.get("descripcion") or "Movimiento"))
        else:
            ticket = str(dato_o_ticket or "").strip()
            if ticket:
                self.ticket_id = ticket
                self.setWindowTitle(f"Detalle del ticket #{ticket}")
                self.btn_imprimir.setVisible(True)
                self.panel.cargar(ticket)
            else:
                self.panel.mensaje("Sin datos para mostrar")

    def _imprimir_copia(self):
        if not self.ticket_id:
            return
        try:
            from src.hardware.printer import printer_manager
            from PyQt6.QtWidgets import QMessageBox
            ok = printer_manager.imprimir_ticket_venta(int(self.ticket_id))
            if ok:
                QMessageBox.information(self, "Imprimir", f"Ticket #{self.ticket_id} enviado a la tiketera.")
            else:
                QMessageBox.warning(self, "Imprimir", "No se pudo enviar el ticket a la tiketera.")
        except Exception as error:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Imprimir", f"No se pudo imprimir:\n{error}")


def abrir_detalle_ticket(dato_o_ticket, parent=None):
    dialogo = DialogoDetalleTicket(dato_o_ticket, parent)
    qt_exec(dialogo)
