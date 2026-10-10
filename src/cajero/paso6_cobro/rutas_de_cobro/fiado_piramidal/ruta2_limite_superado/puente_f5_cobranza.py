# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QLineEdit, QPushButton
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
        
        # Integrar motor global de cobranzas
        from src.motores_empresariales.motor_cobranzas_medios.motor_cobranza import MotorCobranzaMedios
        self.motor = MotorCobranzaMedios(self)
        self.motor.abono_registrado.connect(self._abono_completado)
        # Opcional: conectar error_cobranza si quieres mostrar un popup, o requerir autorizacion
        
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

        # La caja verde de monto, ahora editable!
        self.frame_monto = QFrame()
        self.frame_monto.setStyleSheet("background-color: #F8FAFC; border: 3px solid #10B981; border-radius: 12px;")
        lay_monto = QHBoxLayout(self.frame_monto)
        lay_monto.setContentsMargins(15, 10, 15, 10)
        
        self.txt_monto_abono = QLineEdit()
        self.txt_monto_abono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_monto_abono.setStyleSheet(
            "QLineEdit { color: #FFFFFF; background-color: #2563EB; font-size: 44px; font-weight: bold; padding: 5px 20px; border-radius: 6px; border: none; }"
            "QLineEdit:focus { background-color: #1D4ED8; border: 2px solid #93C5FD; }"
        )
        lay_monto.addWidget(self.txt_monto_abono, 1)
        
        self.btn_abono_libre = QPushButton("$ Personalizado")
        self.btn_abono_libre.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_abono_libre.setStyleSheet("QPushButton { color: #FFFFFF; background-color: #10B981; font-size: 18px; font-weight: bold; padding: 10px; border-radius: 6px; border: none; } QPushButton:hover { background-color: #059669; }")
        self.btn_abono_libre.clicked.connect(lambda: self.txt_monto_abono.setFocus())
        lay_monto.addWidget(self.btn_abono_libre, 0)
        
        lay.addWidget(self.frame_monto)

        self.lbl_mid = QLabel("?? ELIGE EL METODO DE PAGO O AJUSTA EL MONTO ??")
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
        
        btn_efectivo.clicked.connect(lambda: self._iniciar_pago("Efectivo"))
        btn_tarjeta.clicked.connect(lambda: self._iniciar_pago("Tarjeta"))
        btn_qr.clicked.connect(lambda: self._iniciar_pago("QR"))
        btn_transf.clicked.connect(lambda: self._iniciar_pago("Transferencia"))

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
        
        self.lbl_conf = QLabel("\u2714 CONFIRMAR")
        self.lbl_conf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_conf.setStyleSheet("color: #FFFFFF; background-color: #3B82F6; font-size: 14px; font-weight: bold; padding: 12px; border-radius: 8px;")
        
        self.lay_bottom.addWidget(self.lbl_esc, 1)
        self.lay_bottom.addWidget(self.lbl_conf, 2)
        lay.addLayout(self.lay_bottom)

    def _crear_boton(self, texto):
        btn = QPushButton(texto)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF; color: #1E3A8A; font-weight: bold; font-size: 18px; 
                border: 2px solid #94A3B8; border-radius: 8px; padding: 15px;
            }
            QPushButton:hover {
                background-color: #EFF6FF; border-color: #3B82F6;
            }
        """)
        return btn

    def poblar(self, datos):
        self._datos = datos
        d = datos.get('deuda')
        c = datos.get('compra')
        i = datos.get('id')
        self.deuda = float(d) if d is not None else 0.0
        self.compra = float(c) if c is not None else 0.0
        self.cliente_id = int(i) if i is not None else 0
        
        total = self.deuda + self.compra
        self._monto_sugerido = total
        
        self.lbl_nombre.setText(f"Hola {datos.get('nombre', '')}")
        self.lbl_deuda.setText(f"A cobrar: ${total:,.2f}")
        self.txt_monto_abono.setText(f"{total:.2f}".replace('.', ','))
        
        # Reset para evitar envios multiples
        self._procesando = False

    def _iniciar_pago(self, medio):
        if getattr(self, "_procesando", False):
            return
            
        texto_monto = self.txt_monto_abono.text().replace(',', '.')
        try:
            monto_abono = float(texto_monto)
        except ValueError:
            return
            
        if monto_abono <= 0:
            return
            
        self._procesando = True
        self._medio_elegido = medio
        self._monto_abono = monto_abono
        
        # Enviar al motor global
        self.motor.finalizar(self.cliente_id, monto_abono, medio, "Abono F5 Mixto")

    def _abono_completado(self, resultado):
        self._procesando = False
        if not resultado.ok:
            return
            
        saldo_final = self.deuda + self.compra - self._monto_abono
            
        # El carrito en s SIEMPRE debe quedar como Crdito para no duplicar el ingreso de dinero,
        # ya que el dinero fsico entr a travs del Abono en el Motor de Cobranzas.
        self.pago_completado.emit({
            "estado": "APROBADO",
            "cliente_id": self.cliente_id,
            "monto_carrito": self.compra,
            "medio_pago": "CR\xc9DITO",
            "condiciones_ticket": {
                "es_cuenta_corriente": True,
                "cliente_nombre": self._datos.get("nombre", ""),
                "lineas_extra": [
                    "--------------------------------",
                    ">>> PAGO TOTAL CUENTA <<<",
                    f"CLIENTE: {self._datos.get('nombre', '')}",
                    f"SALDO PREVIO:   ${self.deuda:,.2f}",
                    f"ABONO F5 ({self._medio_elegido}): ${self._monto_abono:,.2f}",
                    f"SALDO RESTANTE: ${saldo_final:,.2f}",
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
            self._iniciar_pago("Efectivo")
        elif k == Qt.Key.Key_2:
            self._iniciar_pago("Tarjeta")
        elif k == Qt.Key.Key_3:
            self._iniciar_pago("QR")
        elif k == Qt.Key.Key_4:
            self._iniciar_pago("Transferencia")
        else:
            super().keyPressEvent(event)
