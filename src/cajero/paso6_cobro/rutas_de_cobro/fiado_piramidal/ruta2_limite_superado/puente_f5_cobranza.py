# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, pyqtSignal

class PuenteF5Cobranza(QFrame):
    pago_completado = pyqtSignal(dict)
    cancelado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelF5")
        self.setStyleSheet("""
            QFrame#PanelF5 {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 3px solid #3B82F6;
            }
        """)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(15)

        self.lbl_sup = QLabel("PAGO TOTAL: VENTA + CUENTA")
        self.lbl_sup.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sup.setStyleSheet("color: #1E3A8A; font-size: 16px; font-weight: bold; letter-spacing: 2px;")
        lay.addWidget(self.lbl_sup)

        self.lbl_nombre = QLabel("Hola Cliente")
        self.lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_nombre.setStyleSheet("color: #047857; font-size: 30px; font-weight: 900;")
        lay.addWidget(self.lbl_nombre)

        self.lbl_deuda = QLabel("A cobrar: $0.00")
        self.lbl_deuda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_deuda.setStyleSheet("color: #B91C1C; font-size: 36px; font-weight: 900;")
        lay.addWidget(self.lbl_deuda)
        
        lay.addSpacing(10)

        # La caja verde de monto
        self.frame_monto = QFrame()
        self.frame_monto.setStyleSheet("background-color: #F8FAFC; border: 3px solid #10B981; border-radius: 12px;")
        lay_monto = QHBoxLayout(self.frame_monto)
        lay_monto.setContentsMargins(15, 10, 15, 10)
        
        self.lbl_monto_box = QLabel("111094.00")
        self.lbl_monto_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_monto_box.setStyleSheet("color: #FFFFFF; background-color: #2563EB; font-size: 44px; font-weight: bold; padding: 5px 20px; border-radius: 6px; border: none;")
        lay_monto.addWidget(self.lbl_monto_box, 1)
        
        self.lbl_pers = QLabel("$ Total Cerrado")
        self.lbl_pers.setStyleSheet("color: #FFFFFF; background-color: #10B981; font-size: 18px; font-weight: bold; padding: 10px; border-radius: 6px; border: none;")
        lay_monto.addWidget(self.lbl_pers, 0)
        
        lay.addWidget(self.frame_monto)

        self.lbl_mid = QLabel("?? ELIGE EL METODO DE PAGO ??")
        self.lbl_mid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_mid.setStyleSheet("color: #FFFFFF; background-color: #10B981; border-radius: 8px; font-size: 16px; font-weight: bold; padding: 12px;")
        lay.addWidget(self.lbl_mid)

        lay.addStretch()

        self.lay_botones = QHBoxLayout()
        self.lay_botones.setSpacing(10)

        btn_efectivo = self._crear_boton("Efectivo")
        btn_tarjeta = self._crear_boton("Tarjeta")
        btn_qr = self._crear_boton("QR")
        btn_transf = self._crear_boton("Transferencia")
        
        btn_efectivo.mousePressEvent = lambda e: self._procesar_pago("Efectivo")
        btn_tarjeta.mousePressEvent = lambda e: self._procesar_pago("Tarjeta")
        btn_qr.mousePressEvent = lambda e: self._procesar_pago("QR")
        btn_transf.mousePressEvent = lambda e: self._procesar_pago("Transferencia")

        self.lay_botones.addWidget(btn_efectivo)
        self.lay_botones.addWidget(btn_tarjeta)
        self.lay_botones.addWidget(btn_qr)
        self.lay_botones.addWidget(btn_transf)
        
        lay.addLayout(self.lay_botones)
        
        lay.addSpacing(10)
        
        self.lay_bottom = QHBoxLayout()
        self.lbl_esc = QLabel("ESC Cancelar")
        self.lbl_esc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_esc.setStyleSheet("color: #991B1B; background-color: #FEE2E2; font-size: 14px; font-weight: bold; padding: 12px; border-radius: 8px;")
        
        self.lbl_conf = QLabel("\u2714 SELECCIONE ARRIBA")
        self.lbl_conf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_conf.setStyleSheet("color: #FFFFFF; background-color: #3B82F6; font-size: 14px; font-weight: bold; padding: 12px; border-radius: 8px;")
        
        self.lay_bottom.addWidget(self.lbl_esc, 1)
        self.lay_bottom.addWidget(self.lbl_conf, 2)
        lay.addLayout(self.lay_bottom)

    def _crear_boton(self, texto):
        lbl = QLabel(texto)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("""
            QLabel {
                background-color: #FFFFFF; color: #1E3A8A; font-weight: bold; font-size: 18px; 
                border: 2px solid #94A3B8; border-radius: 8px; padding: 15px;
            }
            QLabel:hover {
                background-color: #EFF6FF; border-color: #3B82F6;
            }
        """)
        return lbl

    def poblar(self, datos):
        self._datos = datos
        self.deuda = float(datos.get('deuda', 0))
        self.compra = float(datos.get('compra', 0))
        self.cliente_id = int(datos.get('id', 0))
        
        total = self.deuda + self.compra
        
        self.lbl_nombre.setText(f"Hola {datos.get('nombre', '')}")
        self.lbl_deuda.setText(f"A cobrar: ${total:,.2f}")
        self.lbl_monto_box.setText(f"{total:.2f}")

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
        k = event.key()
        if k == Qt.Key.Key_Escape:
            self.cancelado.emit()
        elif k == Qt.Key.Key_1:
            self._procesar_pago("Efectivo")
        elif k == Qt.Key.Key_2:
            self._procesar_pago("Tarjeta")
        elif k == Qt.Key.Key_3:
            self._procesar_pago("QR")
        elif k == Qt.Key.Key_4:
            self._procesar_pago("Transferencia")
        else:
            event.ignore()
