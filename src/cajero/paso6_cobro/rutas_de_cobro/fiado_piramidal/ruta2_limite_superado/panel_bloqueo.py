# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from src.clientes_fiado.interfaz.cobro.pin_admin import quien_autoriza

class PanelLimiteSuperado(QWidget):
    pin_validado = pyqtSignal(int, float)
    solicita_f5 = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._admin_pin = ""
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(15)

        self.icono = QLabel("❌")
        self.icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icono.setStyleSheet("color: #EF4444; font-size: 80px; font-weight: bold;")
        lay.addWidget(self.icono)

        self.lbl_titulo = QLabel("LÍMITE SUPERADO")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("color: #991B1B; font-size: 32px; font-weight: 900; letter-spacing: 2px;")
        lay.addWidget(self.lbl_titulo)

        self.lbl_nombre = QLabel("Nombre Cliente")
        self.lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_nombre.setStyleSheet("color: #7F1D1D; font-size: 26px; font-weight: 800;")
        lay.addWidget(self.lbl_nombre)

        lay.addStretch()

        self.lay_pin = QHBoxLayout()
        self.lay_pin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lay_pin.setSpacing(20)
        self.dots = []
        for _ in range(4):
            d = QLabel()
            d.setFixedSize(24, 24)
            d.setStyleSheet("border: 2px solid #991B1B; border-radius: 12px; background: transparent;")
            self.lay_pin.addWidget(d)
            self.dots.append(d)
        lay.addLayout(self.lay_pin)
        
        lay.addSpacing(10)

        self.btn_confirmar = QLabel("[ ESPERANDO PIN ADMIN ]")
        self.btn_confirmar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_confirmar.setStyleSheet(
            "QLabel { color: #FFFFFF; background-color: #EF4444; font-size: 22px; font-weight: 900; "
            "border-radius: 14px; padding: 18px; border-bottom: 6px solid #991B1B; text-transform: uppercase; letter-spacing: 1px; }"
        )
        lay.addWidget(self.btn_confirmar)
        
        self.lbl_f5 = QLabel("O presione [ F5 ] para PAGAR cuenta")
        self.lbl_f5.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_f5.setStyleSheet("color: #991B1B; font-size: 16px; font-weight: bold;")
        lay.addWidget(self.lbl_f5)

    def poblar(self, datos):
        self._datos = datos
        self.lbl_nombre.setText(f"Hola {datos['nombre']}")
        self._admin_pin = ""
        self.actualizar_pin(0)

    def actualizar_pin(self, cantidad):
        for i, d in enumerate(self.dots):
            if i < cantidad:
                d.setStyleSheet("border: 2px solid #991B1B; border-radius: 12px; background: #EF4444;")
            else:
                d.setStyleSheet("border: 2px solid #991B1B; border-radius: 12px; background: transparent;")

    def _validar_pin(self):
        admin = quien_autoriza(self._admin_pin)
        if admin:
            from src.clientes_fiado.cerebro.cerebro import cerebro
            cerebro.conceder_excepcion(self._datos.get('id'), self._datos.get('compra', 0), admin)
            self.pin_validado.emit(int(self._datos['id']), 0.0)
        else:
            self._admin_pin = ""
            self.actualizar_pin(0)

    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key.Key_F5:
            self.solicita_f5.emit(self._datos)
            return
            
        if k == Qt.Key.Key_Backspace:
            if len(self._admin_pin) > 0:
                self._admin_pin = self._admin_pin[:-1]
                self.actualizar_pin(len(self._admin_pin))
            return
            
        char = event.text()
        if k == Qt.Key.Key_Return or k == Qt.Key.Key_Enter:
            if len(self._admin_pin) == 4:
                self._validar_pin()
            return
            
        if char.isdigit() and len(self._admin_pin) < 4:
            self._admin_pin += char
            self.actualizar_pin(len(self._admin_pin))
        else:
            event.ignore()
