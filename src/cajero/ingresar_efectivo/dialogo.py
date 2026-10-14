"""F2 del paso 5: ingresar efectivo a la caja. No cobra fiado. No es F5 ni F6."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QFrame, QLabel, QVBoxLayout

from src.cajero.ingresar_efectivo.otros.panel import PanelOtrosIngresos
from src.cajero.ingresar_efectivo.pie.botones import fila_pie


class DialogoIngresoEfectivo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monto_ingresado = 0.0
        self.motivo = ""

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._armar()

    def showEvent(self, event):
        from src.utils.fondo_gris import cubrir
        cubrir(self)
        self._ajustar_pagina()
        self.panel.reset()
        super().showEvent(event)

    def paintEvent(self, event):
        from src.utils.fondo_gris import pintar
        pintar(self)

    def _armar(self):
        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(0, 0, 0, 0)
        exterior.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hoja = QFrame()
        hoja.setObjectName("IngresoCaja")
        hoja.setStyleSheet(
            "QFrame#IngresoCaja { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 24px; }"
            "QLabel { background: transparent; border: none; color: #0F172A; }"
        )
        caja = QVBoxLayout(hoja)
        caja.setContentsMargins(40, 36, 40, 28)
        caja.setSpacing(10)
        marca = QLabel("F2 · INGRESAR EFECTIVO")
        marca.setAlignment(Qt.AlignmentFlag.AlignCenter)
        marca.setStyleSheet(
            "color: #64748B; font-size: 12px; font-weight: 900; letter-spacing: 2px;"
        )
        caja.addWidget(marca)
        titulo = QLabel("Plata que entra a la caja")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("color: #0F172A; font-size: 22px; font-weight: 900;")
        caja.addWidget(titulo)
        self.panel = PanelOtrosIngresos()
        self.panel.txt_monto.returnPressed.connect(self._procesar)
        self.panel.txt_desc.returnPressed.connect(self._procesar)
        caja.addWidget(self.panel)
        self.lbl_err = QLabel("")
        self.lbl_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_err.setStyleSheet("font-size: 12px; color: #DC2626; font-weight: bold; border: none;")
        caja.addWidget(self.lbl_err)
        caja.addLayout(fila_pie(self.reject, self._procesar))
        exterior.addWidget(hoja)
        self.hoja = hoja

    def _ajustar_pagina(self):
        ancho = max(400, min(720, self.width() - 64))
        alto = max(360, min(560, self.height() - 40))
        self.hoja.setFixedSize(ancho, alto)

    def _procesar(self):
        ok, err = self.panel.validar()
        if not ok:
            self.lbl_err.setText(err)
            return
        self.monto_ingresado = self.panel.monto()
        self.motivo = self.panel.descripcion()
        self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._procesar()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
