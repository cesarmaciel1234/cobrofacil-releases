# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from src.cajero.cajero_activo import CajeroActivo

class PanelLimiteSuperado(QWidget):
    pin_validado = pyqtSignal()
    solicita_f5 = pyqtSignal(dict) # Emits client data to open F5 bridge

    def __init__(self, parent=None):
        super().__init__(parent)
        self._datos = {}
        self._admin_pin = ""
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(5)

        self.icono = QLabel("\u274c")
        self.icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icono.setStyleSheet("color: #EF4444; font-size: 80px; font-weight: bold;")
        lay.addWidget(self.icono)

        self.lbl_titulo = QLabel("L\xcdMITE SUPERADO")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("color: #991B1B; font-size: 32px; font-weight: 900; letter-spacing: 2px;")
        lay.addWidget(self.lbl_titulo)

        self.lbl_nombre = QLabel("Nombre Cliente")
        self.lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_nombre.setStyleSheet("color: #B91C1C; font-size: 26px; font-weight: 800;")
        lay.addWidget(self.lbl_nombre)

        lay.addSpacing(2)

        # Desglose matemático
        self.lay_desglose = QVBoxLayout()
        self.lbl_deuda_anterior = QLabel("Deuda Anterior: $0.00")
        self.lbl_deuda_anterior.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_deuda_anterior.setStyleSheet("color: #991B1B; font-size: 18px; font-weight: bold;")
        self.lay_desglose.addWidget(self.lbl_deuda_anterior)
        
        self.lbl_compra = QLabel("+ Compra Actual: $0.00")
        self.lbl_compra.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_compra.setStyleSheet("color: #991B1B; font-size: 18px; font-weight: bold;")
        self.lay_desglose.addWidget(self.lbl_compra)
        
        self.linea = QFrame()
        self.linea.setFrameShape(QFrame.Shape.HLine)
        self.linea.setFixedHeight(2)
        self.linea.setStyleSheet("background-color: #FCA5A5;")
        self.lay_desglose.addWidget(self.linea)
        
        self.lbl_saldo_total = QLabel("SALDO TOTAL: $0.00")
        self.lbl_saldo_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_saldo_total.setStyleSheet("color: #DC2626; font-size: 26px; font-weight: 900;")
        self.lay_desglose.addWidget(self.lbl_saldo_total)
        
        self.lbl_limite = QLabel("(L\xedmite Asignado: $0.00)")
        self.lbl_limite.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_limite.setStyleSheet("color: #B91C1C; font-size: 16px; font-weight: bold;")
        self.lay_desglose.addWidget(self.lbl_limite)
        
        lay.addLayout(self.lay_desglose)
        lay.addSpacing(2)

        self.lbl_pin = QLabel("\u25cb \u25cb \u25cb \u25cb")
        self.lbl_pin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_pin.setStyleSheet("color: #991B1B; font-size: 40px; letter-spacing: 15px; font-weight: 900;")
        lay.addWidget(self.lbl_pin)

        self.btn_confirmar = QPushButton("[ ESPERANDO PIN ADMIN ]")
        self.btn_confirmar.setStyleSheet(
            "QPushButton { color: #FFFFFF; background-color: #EF4444; font-size: 22px; font-weight: 900; "
            "border-radius: 14px; padding: 18px; border-bottom: 6px solid #991B1B; text-transform: uppercase; letter-spacing: 1px; }"
        )
        lay.addWidget(self.btn_confirmar)
        
        # El Puente F5
        self.lbl_ayuda_f5 = QLabel("O presione [ F5 ] para COBRAR la deuda ahora mismo")
        self.lbl_ayuda_f5.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_ayuda_f5.setStyleSheet("color: #B91C1C; font-size: 16px; font-weight: bold; margin-top: 10px;")
        lay.addWidget(self.lbl_ayuda_f5)

    def poblar(self, datos):
        self._datos = datos
        self._admin_pin = ""
        self.actualizar_pin(0)
        
        self.lbl_nombre.setText(f"Hola {datos['nombre']}")
        
        d = float(datos.get('deuda', 0))
        c = float(datos.get('compra', 0))
        t = d + c
        
        self.lbl_deuda_anterior.setText(f"Deuda Anterior: ${d:,.2f}")
        self.lbl_compra.setText(f"+ Compra Actual: ${c:,.2f}")
        self.lbl_saldo_total.setText(f"SALDO TOTAL: ${t:,.2f}")
        self.lbl_limite.setText(f"(L\xedmite Asignado: ${float(datos.get('limite', 0)):,.2f})")

    def actualizar_pin(self, cantidad):
        llenos = "\u25cf " * cantidad
        vacios = "\u25cb " * (4 - cantidad)
        self.lbl_pin.setText((llenos + vacios).strip())

    def _validar_pin(self):
        admin = CajeroActivo.quien_autoriza(self._admin_pin)
        if admin:
            from src.clientes_fiado.cerebro.cerebro import conceder_excepcion
            conceder_excepcion(self._datos.get('id'), self._datos.get('compra', 0), admin)
            self.pin_validado.emit()
        else:
            # Error visual (se vacía)
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
        if char.isdigit() and len(self._admin_pin) < 4:
            self._admin_pin += char
            self.actualizar_pin(len(self._admin_pin))
            if len(self._admin_pin) == 4:
                self._validar_pin()
        else:
            event.ignore()
