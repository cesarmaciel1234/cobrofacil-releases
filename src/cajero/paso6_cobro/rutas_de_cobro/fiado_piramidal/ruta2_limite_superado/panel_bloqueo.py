# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from src.clientes_fiado.interfaz.cobro.pin_admin import quien_autoriza

class PanelLimiteSuperado(QFrame):
    pin_validado = pyqtSignal(int, float)
    solicita_f5 = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelRojo")
        self.setStyleSheet("""
            QFrame#PanelRojo {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #EF4444, stop:1 #B91C1C);
                border-radius: 16px;
                border: 2px solid #7F1D1D;
            }
        """)
        
        self._admin_pin = ""
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(15)

        self.icono = QLabel("\u2718") # Heavy cross mark
        self.icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icono.setStyleSheet("color: #FFFFFF; font-size: 100px; font-weight: bold; margin-bottom: 10px;")
        lay.addWidget(self.icono)

        self.lbl_titulo = QLabel("RECHAZADO")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("color: #FFFFFF; font-size: 40px; font-weight: 900; letter-spacing: 4px;")
        lay.addWidget(self.lbl_titulo)

        self.lbl_nombre = QLabel("NOMBRE CLIENTE")
        self.lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_nombre.setStyleSheet("color: #FEE2E2; font-size: 24px; font-weight: 600; text-transform: uppercase;")
        lay.addWidget(self.lbl_nombre)

        lay.addStretch()

        self.lay_pin = QHBoxLayout()
        self.lay_pin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lay_pin.setSpacing(25)
        self.dots = []
        for _ in range(4):
            d = QLabel()
            d.setFixedSize(30, 30)
            d.setStyleSheet("border: 3px solid #FFFFFF; border-radius: 15px; background: transparent;")
            self.lay_pin.addWidget(d)
            self.dots.append(d)
        lay.addLayout(self.lay_pin)
        
        lay.addSpacing(15)

        self.btn_confirmar = QLabel("ESPERANDO PIN...")
        self.btn_confirmar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_confirmar.setStyleSheet(
            "QLabel { color: #FFFFFF; font-size: 18px; font-weight: 900; "
            "text-transform: uppercase; letter-spacing: 2px; }"
        )
        lay.addWidget(self.btn_confirmar)
        
        lay.addSpacing(15)
        
        self.lbl_f5 = QLabel("O presione [ F5 ] para PAGAR cuenta")
        self.lbl_f5.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_f5.setStyleSheet("color: #FEF2F2; background-color: #991B1B; padding: 12px; border-radius: 10px; font-size: 18px; font-weight: bold;")
        lay.addWidget(self.lbl_f5)

    def poblar(self, datos):
        self._datos = datos
        self.lbl_nombre.setText(f"{datos['nombre']}")
        self._admin_pin = ""
        self._estado_aprobado = False
        self.setStyleSheet("""
            QFrame#PanelRojo {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #EF4444, stop:1 #B91C1C);
                border-radius: 16px;
                border: 2px solid #7F1D1D;
            }
        """)
        self.icono.setText("✘")
        self.lbl_titulo.setText("RECHAZADO")
        self.btn_confirmar.setText("ESPERANDO PIN...")
        self.btn_confirmar.setStyleSheet("QLabel { color: #FFFFFF; font-size: 18px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px; }")
        self.actualizar_pin(0)

    def actualizar_pin(self, cantidad):
        for i, d in enumerate(self.dots):
            if i < cantidad:
                d.setStyleSheet("border: 3px solid #FFFFFF; border-radius: 15px; background: #FFFFFF;")
            else:
                d.setStyleSheet("border: 3px solid #FFFFFF; border-radius: 15px; background: transparent;")

    def _validar_pin(self):
        admin = quien_autoriza(self._admin_pin)
        if admin:
            from src.clientes_fiado.cerebro.cerebro import cerebro
            cerebro.conceder_excepcion(self._datos.get('id'), self._datos.get('compra', 0), admin)
            self._estado_aprobado = True
            self.setStyleSheet("""
                QFrame#PanelRojo {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10B981, stop:1 #047857);
                    border-radius: 16px;
                    border: 2px solid #064E3B;
                }
            """)
            self.icono.setText("✔")
            self.lbl_titulo.setText("EXCEPCIÓN APROBADA")
            self.btn_confirmar.setText("[ ENTER ] CONFIRMAR")
            self.btn_confirmar.setStyleSheet("QLabel { color: #047857; background-color: #FFFFFF; font-size: 24px; font-weight: 900; border-radius: 12px; padding: 20px; text-transform: uppercase; letter-spacing: 2px; }")
        else:
            self._admin_pin = ""
            self.actualizar_pin(0)
            # Give some visual feedback that it failed
            self.btn_confirmar.setText("PIN INCORRECTO")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self.btn_confirmar.setText("ESPERANDO PIN..."))

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
            if getattr(self, '_estado_aprobado', False):
                self.pin_validado.emit(int(self._datos['id']), 0.0)
            elif len(self._admin_pin) == 4:
                self._validar_pin()
            return
            
        if char.isdigit() and len(self._admin_pin) < 4:
            self._admin_pin += char
            self.actualizar_pin(len(self._admin_pin))
        else:
            event.ignore()
