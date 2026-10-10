# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal

class PuenteF5Cobranza(QWidget):
    pago_completado = pyqtSignal(dict)
    cancelado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(15)

        self.lbl_titulo = QLabel("PAGO TOTAL F5")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("color: #1E3A8A; font-size: 32px; font-weight: 900; letter-spacing: 2px;")
        lay.addWidget(self.lbl_titulo)

        self.lbl_deuda = QLabel("Deuda Hist\xf3rica: $0.00")
        self.lbl_deuda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_deuda.setStyleSheet("color: #475569; font-size: 24px; font-weight: bold;")
        lay.addWidget(self.lbl_deuda)
        
        self.lbl_carrito = QLabel("Venta Actual: $0.00")
        self.lbl_carrito.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_carrito.setStyleSheet("color: #475569; font-size: 24px; font-weight: bold;")
        lay.addWidget(self.lbl_carrito)
        
        self.lbl_total = QLabel("A COBRAR: $0.00")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_total.setStyleSheet("color: #0F172A; font-size: 40px; font-weight: 900;")
        lay.addWidget(self.lbl_total)

        lay.addStretch()

        self.lay_botones = QHBoxLayout()
        self.lay_botones.setSpacing(10)

        # Botones rpidos
        btn_efectivo = self._crear_boton("EFECTIVO", "#10B981")
        btn_tarjeta = self._crear_boton("TARJETA", "#3B82F6")
        btn_qr = self._crear_boton("QR", "#8B5CF6")
        
        btn_efectivo.mousePressEvent = lambda e: self._procesar_pago("Efectivo")
        btn_tarjeta.mousePressEvent = lambda e: self._procesar_pago("Tarjeta")
        btn_qr.mousePressEvent = lambda e: self._procesar_pago("QR")

        self.lay_botones.addWidget(btn_efectivo)
        self.lay_botones.addWidget(btn_tarjeta)
        self.lay_botones.addWidget(btn_qr)
        
        lay.addLayout(self.lay_botones)
        
        self.lbl_cancelar = QLabel("Presione [ ESC ] para volver")
        self.lbl_cancelar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cancelar.setStyleSheet("color: #64748B; font-size: 16px;")
        lay.addWidget(self.lbl_cancelar)

    def _crear_boton(self, texto, color):
        lbl = QLabel(texto)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"background-color: {color}; color: white; font-weight: bold; font-size: 20px; border-radius: 10px; padding: 15px;")
        return lbl

    def poblar(self, datos):
        self._datos = datos
        self.deuda = float(datos.get('deuda', 0))
        self.compra = float(datos.get('compra', 0))
        self.cliente_id = int(datos.get('id', 0))
        
        self.lbl_deuda.setText(f"Deuda Hist\xf3rica: ${self.deuda:,.2f}")
        self.lbl_carrito.setText(f"Venta Actual: ${self.compra:,.2f}")
        self.lbl_total.setText(f"A COBRAR: ${(self.deuda + self.compra):,.2f}")

    def _procesar_pago(self, medio):
        from src.clientes_fiado.cerebro.cerebro import cerebro
        if self.deuda > 0:
            cerebro.abonar_caja(self.cliente_id, self.deuda, self.deuda, medio=medio)
            
        self.pago_completado.emit({
            "estado": "APROBADO",
            "cliente_id": self.cliente_id,
            "monto_carrito": self.compra,
            "medio_pago": medio,
            "condiciones_ticket": {
                "es_cuenta_corriente": True,
                "cliente_nombre": self._datos.get("nombre", ""),
                "lineas_extra": [
                    "--------------------------------",
                    ">>> PAGO TOTAL CUENTA <<<",
                    f"CLIENTE: {self._datos.get('nombre', '')}",
                    f"SALDO PREVIO:   ${self.deuda:,.2f}",
                    f"ABONO F5:       ${self.deuda:,.2f}",
                    f"SALDO RESTANTE: $0.00",
                    "--------------------------------",
                    "FIRMA: _________________________"
                ]
            }
        })

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancelado.emit()
        else:
            event.ignore()
