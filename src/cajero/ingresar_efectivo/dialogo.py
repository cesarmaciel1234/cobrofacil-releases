"""Junta Cambio, Fiado y Otros. No cobra la venta."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QFrame, QGridLayout, QLabel, QStackedWidget, QVBoxLayout

from src.cajero.ingresar_efectivo.cambio.panel import PanelIngresoEfectivo
from src.cajero.ingresar_efectivo.fiado.paleta import PALETA
from src.cajero.ingresar_efectivo.fiado.panel import CentroCobranzasPanel
from src.cajero.ingresar_efectivo.opciones.boton import boton_opcion
from src.cajero.ingresar_efectivo.otros.panel import PanelOtrosIngresos
from src.cajero.ingresar_efectivo.pie.botones import fila_pie


class DialogoIngresoEfectivo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monto_ingresado = 0.0
        self.motivo = ""
        self.tipo_ingreso = "FIADO"
        self.cliente_id = None
        self.cliente_nombre = ""
        self.en_venta = False
        self.deuda_actual = 0.0

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(560, 600)
        self._armar()

    def _armar(self):
        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(0, 0, 0, 0)

        hoja = QFrame()
        hoja.setStyleSheet(
            "QFrame { background: #FFFFFF; border: 2px solid #E2E8F0; border-radius: 18px; }"
        )
        exterior.addWidget(hoja)

        caja = QVBoxLayout(hoja)
        caja.setContentsMargins(20, 20, 20, 20)
        caja.setSpacing(10)

        grilla = QGridLayout()
        grilla.setSpacing(10)
        self.btn_cambio = boton_opcion("🪙", "CAMBIO", "#3B82F6")
        self.btn_fiado = boton_opcion("👥", "FIADO", PALETA["accent"])
        self.btn_otros = boton_opcion("📦", "OTROS", "#6366F1")
        self.btn_cambio.clicked.connect(lambda: self._set_modo("CAMBIO"))
        self.btn_fiado.clicked.connect(lambda: self._set_modo("FIADO"))
        self.btn_otros.clicked.connect(lambda: self._set_modo("OTROS"))
        grilla.addWidget(self.btn_cambio, 0, 0)
        grilla.addWidget(self.btn_fiado, 0, 1)
        grilla.addWidget(self.btn_otros, 0, 2)
        caja.addLayout(grilla)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: none;")
        self.panel_cambio = PanelIngresoEfectivo()
        self.panel_fiado = CentroCobranzasPanel()
        self.panel_otros = PanelOtrosIngresos()
        self.panel_cambio.txt_monto.returnPressed.connect(self._procesar)
        self.panel_fiado.txt_monto.returnPressed.connect(self._procesar)
        self.panel_otros.txt_monto.returnPressed.connect(self._procesar)
        self.stack.addWidget(self.panel_cambio)
        self.stack.addWidget(self.panel_fiado)
        self.stack.addWidget(self.panel_otros)
        caja.addWidget(self.stack)

        self.lbl_err = QLabel("")
        self.lbl_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_err.setStyleSheet("font-size: 12px; color: #DC2626; font-weight: bold; border: none;")
        caja.addWidget(self.lbl_err)
        caja.addLayout(fila_pie(self.reject, self._procesar))

        self._set_modo("FIADO")

    def _set_modo(self, modo):
        self.tipo_ingreso = modo
        self.btn_cambio.setChecked(modo == "CAMBIO")
        self.btn_fiado.setChecked(modo == "FIADO")
        self.btn_otros.setChecked(modo == "OTROS")
        self.lbl_err.setText("")

        if modo == "CAMBIO":
            self.stack.setCurrentIndex(0)
            self.panel_cambio.reset()
        elif modo == "FIADO":
            self.stack.setCurrentIndex(1)
            self.panel_fiado.cargar_clientes_abono()
        elif modo == "OTROS":
            self.stack.setCurrentIndex(2)
            self.panel_otros.reset()

    def _procesar(self):
        try:
            if self.tipo_ingreso == "CAMBIO":
                ok, err = self.panel_cambio.validar()
                if not ok:
                    self.lbl_err.setText(err)
                    return
                self.monto_ingresado = self.panel_cambio.monto()
                self.motivo = "Ingreso de Cambio / Fondo Fijo"
            elif self.tipo_ingreso == "FIADO":
                ok, err = self.panel_fiado.validar()
                if not ok:
                    self.lbl_err.setText(err)
                    return
                data = self.panel_fiado.cliente_actual()
                self.monto_ingresado = self.panel_fiado.monto()
                self.deuda_actual = self.panel_fiado.deuda_actual()
                self.cliente_id = data["id"]
                self.cliente_nombre = data["nombre"]
                self.motivo = f"Abono Fiado: {self.cliente_nombre}"
            elif self.tipo_ingreso == "OTROS":
                ok, err = self.panel_otros.validar()
                if not ok:
                    self.lbl_err.setText(err)
                    return
                self.monto_ingresado = self.panel_otros.monto()
                self.motivo = self.panel_otros.descripcion()
            self.accept()
        except Exception:
            self.lbl_err.setText("⚠️ Error interno al procesar el ingreso")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._procesar()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key.Key_Left:
            if self.tipo_ingreso == "FIADO":
                self._set_modo("CAMBIO")
            elif self.tipo_ingreso == "OTROS":
                self._set_modo("FIADO")
        elif event.key() == Qt.Key.Key_Right:
            if self.tipo_ingreso == "CAMBIO":
                self._set_modo("FIADO")
            elif self.tipo_ingreso == "FIADO":
                self._set_modo("OTROS")
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        parent = self.parent()
        if parent:
            geo = parent.window().geometry()
        else:
            geo = self.screen().geometry()
        self.move(
            geo.center().x() - self.width() // 2,
            geo.center().y() - self.height() // 2,
        )
