"""Tickets a crédito que todavía no están en la cuenta."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from src.utils.qt_compat import qt_exec
from src.admin.clientes.theme import _CLI
from src.clientes_fiado.cerebro.cerebro import cerebro


class DialogoCuadre(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cuadre de crédito")
        self.resize(860, 520)
        self.setStyleSheet(f"QDialog {{ background: {_CLI['bg']}; }}")
        self._filas = cerebro.ventas_sin_cargo()
        self._hubo_cambios = False
        self._armar()

    def _armar(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        titulo = QLabel("VENTAS SIN CARGO")
        titulo.setStyleSheet(
            f"color: {_CLI['text']}; font-size: 20px; font-weight: 900; background: transparent;"
        )
        lay.addWidget(titulo)

        nota = QLabel(
            "Estos tickets están cobrados como Fiado o Clientes y no tienen cargo en la cuenta. "
            "Cargar escribe el cargo en el cliente cuyo nombre coincide con el de la venta."
        )
        nota.setWordWrap(True)
        nota.setStyleSheet("color: #92400E; font-size: 13px; background: transparent;")
        lay.addWidget(nota)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["Ticket", "Fecha", "Medio", "Monto", "Cliente"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setStyleSheet(
            "QTableWidget { background: white; border: 1px solid #E2E8F0; border-radius: 8px; }"
        )
        lay.addWidget(self.tabla)

        self._pintar()

        barra = QHBoxLayout()
        volver = QPushButton("VOLVER")
        volver.setCursor(Qt.CursorShape.PointingHandCursor)
        volver.setStyleSheet(
            "background: white; color: #0F172A; font-weight: 800; border-radius: 8px; "
            "padding: 10px 16px; border: 1px solid #E2E8F0;"
        )
        volver.clicked.connect(self._cerrar)
        self.btn_cargar = QPushButton("CARGAR EN LA CUENTA")
        self.btn_cargar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cargar.setStyleSheet(
            "QPushButton { background: #059669; color: white; font-weight: 900; border-radius: 8px; "
            "padding: 10px 16px; border: none; }"
            "QPushButton:disabled { background: #CBD5E1; color: #475569; }"
        )
        self.btn_cargar.clicked.connect(self._cargar)
        barra.addWidget(volver)
        barra.addStretch()
        barra.addWidget(self.btn_cargar)
        lay.addLayout(barra)
        self._actualizar_boton()

    def _cerrar(self):
        if self._hubo_cambios:
            self.accept()
        else:
            self.reject()

    def _actualizar_boton(self):
        listos = [fila for fila in self._filas if fila.get("cliente_id")]
        self.btn_cargar.setEnabled(bool(listos))
        if listos:
            self.btn_cargar.setText(f"CARGAR EN LA CUENTA ({len(listos)})")
        else:
            self.btn_cargar.setText("CARGAR EN LA CUENTA")

    def _pintar(self):
        self.tabla.setRowCount(0)
        for fila in self._filas:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            fecha = str(fila.get("fecha") or "").split(".")[0]
            cliente = fila.get("nombre") or "Sin cliente con ese nombre"
            self.tabla.setItem(row, 0, QTableWidgetItem(str(fila.get("venta_id") or "")))
            self.tabla.setItem(row, 1, QTableWidgetItem(fecha))
            self.tabla.setItem(row, 2, QTableWidgetItem(str(fila.get("metodo") or "")))
            self.tabla.setItem(row, 3, QTableWidgetItem(f"${float(fila.get('total') or 0):,.2f}"))
            self.tabla.setItem(row, 4, QTableWidgetItem(cliente))
        self._actualizar_boton()

    def _cargar(self):
        listos = [fila for fila in self._filas if fila.get("cliente_id")]
        if not listos:
            return
        caja = QMessageBox(self)
        caja.setWindowTitle("Cuadre")
        caja.setText(
            f"Se cargan {len(listos)} tickets en la cuenta del cliente que figura en la venta."
        )
        caja.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        caja.button(QMessageBox.StandardButton.Yes).setText("Cargar")
        caja.button(QMessageBox.StandardButton.No).setText("Volver")
        if qt_exec(caja) != QMessageBox.StandardButton.Yes:
            return
        ids = [fila.get("venta_id") for fila in listos]
        hechos, pendientes = cerebro.anotar_faltantes(ids)
        self._filas = pendientes
        self._hubo_cambios = self._hubo_cambios or hechos > 0
        self._pintar()
        if not self._filas:
            QMessageBox.information(
                self, "Cuadre", f"Quedaron en la cuenta {hechos} ticket(s)."
            )
            self.accept()
            return
        QMessageBox.information(
            self,
            "Cuadre",
            f"Quedaron en la cuenta {hechos} de {len(ids)}.\n"
            f"Siguen sin cargo: {len(self._filas)} (nombre sin match único u otro motivo).",
        )
