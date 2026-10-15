# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

from src.motores_empresariales.motor_cobranzas_medios.motor_cobranza import MotorCobranzaMedios
from src.cajero.f6_centro_cobranzas.componentes_f6.ui_selector.panel_selector import PanelSelectorCobranza
from src.utils.dinero import redondear_dinero

class PanelCobranza(QFrame):
    """
    Módulo Independiente de Cobranza y Liquidación de Cuentas Corrientes.
    Permite liquidar deuda acumulada, cobrar el carrito actual o ambas cosas en simultáneo.
    """
    abono_exitoso = pyqtSignal()
    cancelado = pyqtSignal()
    submetodo_cambiado = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelCobranza")
        self.setStyleSheet(
            "QFrame#PanelCobranza { background-color: #FFFFFF; border-radius: 16px; border: 2px solid #E2E8F0; }"
        )
        
        self.motor = MotorCobranzaMedios(self)
        self.motor.abono_registrado.connect(lambda r: self.abono_exitoso.emit())
        self.motor.error_cobranza.connect(lambda e: self._volver_de_lienzo())

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 20, 28, 20)
        lay.setSpacing(10)

        # Encabezado corporativo
        h_top = QHBoxLayout()
        self.lbl_badge = QLabel("LIQUIDACION DE CUENTA CORRIENTE")
        self.lbl_badge.setStyleSheet(
            "color: #047857; background-color: #ECFDF5; border: 1px solid #A7F3D0; "
            "border-radius: 12px; font-size: 13px; font-weight: 800; padding: 4px 12px; letter-spacing: 1px;"
        )
        h_top.addWidget(self.lbl_badge, 0, Qt.AlignmentFlag.AlignCenter)
        lay.addLayout(h_top)

        self.lbl_nombre = QLabel("CLIENTE")
        self.lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_nombre.setStyleSheet("color: #0F172A; font-size: 26px; font-weight: 900; margin-top: 2px;")
        lay.addWidget(self.lbl_nombre)

        # Desglose Financiero Estilo Resumen
        self.frame_desglose = QFrame()
        self.frame_desglose.setStyleSheet(
            "background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px;"
        )
        lay_desglose = QVBoxLayout(self.frame_desglose)
        lay_desglose.setContentsMargins(24, 14, 24, 14)
        lay_desglose.setSpacing(6)
        
        def fila_resumen(texto_izq, texto_der, es_total=False):
            h = QHBoxLayout()
            lbl_i = QLabel(texto_izq)
            lbl_d = QLabel(texto_der)
            if es_total:
                lbl_i.setStyleSheet("color: #0F172A; font-size: 18px; font-weight: 900;")
                lbl_d.setStyleSheet("color: #059669; font-size: 24px; font-weight: 900;")
            else:
                lbl_i.setStyleSheet("color: #64748B; font-size: 16px; font-weight: 700;")
                lbl_d.setStyleSheet("color: #334155; font-size: 17px; font-weight: 800;")
            h.addWidget(lbl_i)
            h.addStretch()
            h.addWidget(lbl_d)
            return h, lbl_i, lbl_d
            
        h_ant, self.lbl_tag_ant, self.lbl_val_ant = fila_resumen("Saldo Pendiente Anterior:", "$0.00")
        h_act, self.lbl_tag_act, self.lbl_val_act = fila_resumen("Compra Actual en Carrito:", "$0.00")
        
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setStyleSheet("background-color: #CBD5E1; max-height: 1px;")
        
        h_tot, self.lbl_tag_tot, self.lbl_val_tot = fila_resumen("IMPORTE TOTAL SUGERIDO:", "$0.00", es_total=True)
        
        lay_desglose.addLayout(h_ant)
        lay_desglose.addLayout(h_act)
        lay_desglose.addWidget(linea)
        lay_desglose.addLayout(h_tot)
        
        lay.addWidget(self.frame_desglose)

        # Botones de Atajo Rapido de Monto
        self.frame_atajos = QFrame()
        lay_atajos = QHBoxLayout(self.frame_atajos)
        lay_atajos.setContentsMargins(0, 4, 0, 4)
        lay_atajos.setSpacing(8)
        
        def pill_btn(texto):
            btn = QPushButton(texto)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(34)
            btn.setStyleSheet(
                "QPushButton { background-color: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; "
                "border-radius: 8px; font-size: 13px; font-weight: 800; padding: 0 10px; } "
                "QPushButton:hover { background-color: #DBEAFE; border-color: #3B82F6; }"
            )
            return btn
            
        self.btn_pill_compra = pill_btn("Solo Carrito")
        self.btn_pill_deuda = pill_btn("Solo Deuda")
        self.btn_pill_todo = pill_btn("Liquidar Todo")
        
        self.btn_pill_compra.clicked.connect(self._fijar_solo_compra)
        self.btn_pill_deuda.clicked.connect(self._fijar_solo_deuda)
        self.btn_pill_todo.clicked.connect(self._fijar_todo)
        
        lay_atajos.addWidget(self.btn_pill_compra)
        lay_atajos.addWidget(self.btn_pill_deuda)
        lay_atajos.addWidget(self.btn_pill_todo)
        lay.addWidget(self.frame_atajos)

        # Caja de Edicion de Monto a Cobrar
        self.frame_monto = QFrame()
        self.frame_monto.setStyleSheet(
            "QFrame { background-color: #F8FAFC; border: 2px solid #059669; border-radius: 12px; }"
        )
        lay_monto = QHBoxLayout(self.frame_monto)
        lay_monto.setContentsMargins(16, 6, 16, 6)
        lay_monto.setSpacing(10)
        
        lbl_signo = QLabel("$")
        lbl_signo.setStyleSheet("color: #059669; font-size: 36px; font-weight: 900; background: transparent; border: none;")
        lay_monto.addWidget(lbl_signo)
        
        self.txt_monto_abono = QLineEdit()
        self.txt_monto_abono.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.txt_monto_abono.setStyleSheet(
            "QLineEdit { color: #0F172A; background-color: transparent; font-size: 38px; font-weight: 900; border: none; }"
        )
        self.txt_monto_abono.returnPressed.connect(lambda: self._iniciar_cobranza("Efectivo"))
        self.txt_monto_abono.installEventFilter(self)
        lay_monto.addWidget(self.txt_monto_abono, 1)
        
        self.btn_abono_libre = QPushButton("Editar")
        self.btn_abono_libre.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_abono_libre.setStyleSheet(
            "QPushButton { color: #475569; background-color: #E2E8F0; font-size: 14px; font-weight: 800; "
            "padding: 8px 14px; border-radius: 8px; border: none; } "
            "QPushButton:hover { background-color: #CBD5E1; color: #0F172A; }"
        )
        self.btn_abono_libre.clicked.connect(lambda: (self.txt_monto_abono.setFocus(), self.txt_monto_abono.selectAll()))
        lay_monto.addWidget(self.btn_abono_libre, 0)
        
        lay.addWidget(self.frame_monto)

        # Indicador de accion
        self.lbl_mid = QLabel("2. Tocá cómo paga")
        self.lbl_mid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_mid.setStyleSheet(
            "color: #1E3A8A; font-size: 16px; font-weight: 800; margin-top: 4px;"
        )
        lay.addWidget(self.lbl_mid)

        # Selector de Medios (ocupa el hueco: botones o lienzo de tarjeta/QR)
        self.panel_selector = PanelSelectorCobranza()
        self.cont_botones = self.panel_selector.cont_botones
        self.cont_lienzos = self.panel_selector.cont_lienzos
        
        self.lienzo_efectivo = self.panel_selector.lienzo_efectivo
        self.lienzo_qr = self.panel_selector.lienzo_qr
        self.lienzo_tarjeta = self.panel_selector.lienzo_tarjeta
        self.lienzo_transferencia = self.panel_selector.lienzo_transferencia
        self.lienzo_mixto = self.panel_selector.lienzo_mixto
        
        self.panel_selector.btn_efectivo.clicked.connect(lambda: self._iniciar_cobranza("Efectivo"))
        self.panel_selector.btn_qr.clicked.connect(lambda: self._iniciar_cobranza("QR"))
        self.panel_selector.btn_tarjeta.clicked.connect(lambda: self._iniciar_cobranza("Tarjeta"))
        self.panel_selector.btn_transferencia.clicked.connect(lambda: self._iniciar_cobranza("Transferencia"))
        self.panel_selector.btn_mixto.clicked.connect(lambda: self._iniciar_cobranza("Mixto"))
        
        self.lienzo_efectivo.listo.connect(lambda monto: self._finalizar_cobranza_con_motor(monto, "Efectivo", None))
        self.lienzo_efectivo.volver.connect(self._volver_de_lienzo)
        
        self.lienzo_qr.listo.connect(lambda det: self._on_lienzo_listo("QR", det))
        self.lienzo_qr.volver.connect(self._volver_de_lienzo)
        
        self.lienzo_tarjeta.listo.connect(lambda det: self._on_lienzo_listo("Tarjeta", det))
        self.lienzo_tarjeta.volver.connect(self._volver_de_lienzo)

        self.lienzo_transferencia.listo.connect(lambda det: self._on_lienzo_listo("Transferencia", det))
        self.lienzo_transferencia.volver.connect(self._volver_de_lienzo)

        self.lienzo_mixto.listo.connect(self._iniciar_cobro_mixto_secuencial)
        self.lienzo_mixto.volver.connect(self._volver_de_lienzo)

        lay.addWidget(self.panel_selector, 1)
        
        self._modo = "preparando_pago"

    def _ticket(self):
        return redondear_dinero(max(0.0, float(getattr(self, "compra", 0.0) or 0.0)))

    def _deuda_pendiente(self):
        d = float(getattr(self, "deuda", 0.0) or 0.0)
        return redondear_dinero(d) if d > 0.009 else 0.0

    def _saldo_a_favor(self):
        d = float(getattr(self, "deuda", 0.0) or 0.0)
        return redondear_dinero(-d) if d < -0.009 else 0.0

    def _escribir_monto(self, monto):
        valor = redondear_dinero(max(0.0, float(monto or 0.0)))
        self.txt_monto_abono.setText(f"{valor:.2f}".replace(".", ","))
        self.txt_monto_abono.setFocus()
        self.txt_monto_abono.selectAll()

    def poblar(self, datos):
        self._datos = datos
        d = datos.get('deuda')
        c = datos.get('compra')
        i = datos.get('id')
        self.deuda = float(d) if d is not None else 0.0
        self.compra = float(c) if c is not None else 0.0
        self.cliente_id = int(i) if i is not None else 0

        ticket = self._ticket()
        deuda_p = self._deuda_pendiente()
        favor = self._saldo_a_favor()

        nombre_raw = str(datos.get('nombre', '') or '').strip()
        nombre_amable = nombre_raw.title() if (nombre_raw.isupper() or nombre_raw.islower()) else nombre_raw
        if nombre_amable:
            self.lbl_nombre.setText(f"¡Hola, {nombre_amable}! 👋")
        else:
            self.lbl_nombre.setText("¡Bienvenido/a! 👋")

        if favor > 0.009:
            self.lbl_tag_ant.setText("Saldo a favor:")
            self.lbl_val_ant.setText(f"${favor:,.2f}")
        else:
            self.lbl_tag_ant.setText("Saldo Pendiente Anterior:")
            self.lbl_val_ant.setText(f"${deuda_p:,.2f}")

        self.lbl_val_act.setText(f"${ticket:,.2f}")
        self.lbl_tag_tot.setText("IMPORTE A COBRAR (TICKET):")
        self.lbl_val_tot.setText(f"${ticket:,.2f}")

        self.btn_pill_compra.setText(f"Solo Carrito (${ticket:,.0f})")
        self.btn_pill_deuda.setText(f"Solo Deuda (${deuda_p:,.0f})")
        self.btn_pill_todo.setText(f"Liquidar Todo (${deuda_p + ticket:,.0f})")
        self.btn_pill_deuda.setVisible(deuda_p > 0.009)
        self.btn_pill_todo.setVisible(deuda_p > 0.009)

        self.lbl_mid.setText("2. Tocá cómo paga")
        self._escribir_monto(ticket)
        self._volver_de_lienzo()

    def _fijar_solo_compra(self):
        self._escribir_monto(self._ticket())

    def _fijar_solo_deuda(self):
        deuda_p = self._deuda_pendiente()
        if deuda_p <= 0.009:
            self._escribir_monto(self._ticket())
            return
        self._escribir_monto(deuda_p)

    def _fijar_todo(self):
        deuda_p = self._deuda_pendiente()
        if deuda_p <= 0.009:
            self._escribir_monto(self._ticket())
            return
        self._escribir_monto(deuda_p + self._ticket())

    def _iniciar_cobranza(self, metodo="Efectivo"):
        from src.utils.parser import parse_float_regional
        texto = self.txt_monto_abono.text().strip()
        if not texto:
            return
        try:
            monto = redondear_dinero(parse_float_regional(texto))
        except Exception:
            return
        if monto <= 0:
            self.lbl_mid.setText("NO SE COBRA UN IMPORTE NEGATIVO. SE COBRA EL TICKET.")
            self._escribir_monto(self._ticket())
            return

        self._monto_a_cobrar = monto
        self._modo = "cobrando_lienzo"
        
        self.frame_desglose.hide()
        self.frame_atajos.hide()
        self.frame_monto.hide()
        self.lbl_mid.hide()
        self.cont_botones.hide()
        self.cont_lienzos.show()
        
        self.submetodo_cambiado.emit(metodo)
        
        if metodo == "Efectivo":
            self.cont_lienzos.setCurrentWidget(self.lienzo_efectivo)
            self.lienzo_efectivo.arrancar(monto)
        elif metodo == "Tarjeta":
            self.cont_lienzos.setCurrentWidget(self.lienzo_tarjeta)
            self.lienzo_tarjeta.arrancar(monto, descripcion="Abono de Cuenta")
        elif metodo == "QR":
            self.cont_lienzos.setCurrentWidget(self.lienzo_qr)
            self.lienzo_qr.arrancar(monto, title="Abono de Cuenta", description="Abono de Cuenta")
        elif metodo == "Transferencia":
            self.cont_lienzos.setCurrentWidget(self.lienzo_transferencia)
            self.lienzo_transferencia.arrancar(monto)
        elif metodo == "Mixto":
            self.cont_lienzos.setCurrentWidget(self.lienzo_mixto)
            self.lienzo_mixto.arrancar(monto)

    def soltar(self):
        self._detalles_mixto = None
        self._pasos_digitales_mixto = []
        self._modo = "preparando_pago"
        self.submetodo_cambiado.emit("")
        for lienzo in (
            getattr(self, "lienzo_efectivo", None),
            getattr(self, "lienzo_qr", None),
            getattr(self, "lienzo_tarjeta", None),
            getattr(self, "lienzo_transferencia", None),
            getattr(self, "lienzo_mixto", None),
        ):
            if lienzo is None:
                continue
            if hasattr(lienzo, "cerrar"):
                try:
                    lienzo.cerrar()
                except Exception:
                    pass
        self.cont_lienzos.hide()
        self.cont_botones.show()

    def _volver_de_lienzo(self):
        self._detalles_mixto = None
        self._pasos_digitales_mixto = []
        self._modo = "preparando_pago"
        self.submetodo_cambiado.emit("")
        self.cont_lienzos.hide()
        self.frame_desglose.show()
        self.frame_atajos.show()
        self.frame_monto.show()
        self.lbl_mid.show()
        self.cont_botones.show()
        self.txt_monto_abono.setFocus()
        self.txt_monto_abono.selectAll()

    def _iniciar_cobro_mixto_secuencial(self, det):
        self._detalles_mixto = det
        self._pasos_digitales_mixto = []
        
        # Primero cobramos los medios digitales que tengan monto > 0
        qr = float(det.get("QR", 0.0) or 0.0)
        tarjeta = float(det.get("Tarjeta", 0.0) or 0.0)
        transferencia = float(det.get("Transferencia", 0.0) or 0.0)
        
        if qr > 0.009:
            self._pasos_digitales_mixto.append(("QR", qr))
        if tarjeta > 0.009:
            self._pasos_digitales_mixto.append(("Tarjeta", tarjeta))
        if transferencia > 0.009:
            self._pasos_digitales_mixto.append(("Transferencia", transferencia))
            
        self._ejecutar_siguiente_paso_mixto()

    def _ejecutar_siguiente_paso_mixto(self):
        if not getattr(self, "_pasos_digitales_mixto", None):
            # Ya se cobraron todos los medios digitales (o solo era efectivo).
            # Ahora finalizamos la cobranza con el motor:
            # Esto asienta el pago total, y al tener efectivo, abre el cajón.
            self.submetodo_cambiado.emit("")
            det = getattr(self, "_detalles_mixto", None) or {}
            self._detalles_mixto = None
            self._finalizar_cobranza_con_motor(self._monto_a_cobrar, "Mixto", det)
            return

        medio, monto = self._pasos_digitales_mixto.pop(0)
        self._modo = "cobrando_lienzo"
        self.cont_lienzos.show()
        self.submetodo_cambiado.emit(medio)
        
        if medio == "QR":
            self.cont_lienzos.setCurrentWidget(self.lienzo_qr)
            self.lienzo_qr.arrancar(monto, title=f"Abono Mixto (QR: ${monto:,.2f})", description="Abono a cuenta corriente")
        elif medio == "Tarjeta":
            self.cont_lienzos.setCurrentWidget(self.lienzo_tarjeta)
            self.lienzo_tarjeta.arrancar(monto, descripcion=f"Abono Mixto (Tarjeta: ${monto:,.2f})")
        elif medio == "Transferencia":
            self.cont_lienzos.setCurrentWidget(self.lienzo_transferencia)
            self.lienzo_transferencia.arrancar(monto)

    def verificar_qr(self):
        if hasattr(self, "lienzo_qr") and self.cont_lienzos.currentWidget() == self.lienzo_qr:
            self.lienzo_qr._consultar_pago()
            return True
        return False

    def _on_lienzo_listo(self, medio, det):
        if getattr(self, "_detalles_mixto", None) is not None:
            if str(det or "").upper() == "F9 MANUAL":
                extra = dict(self._detalles_mixto)
                extra["pago_id"] = "F9 MANUAL"
                self._pasos_digitales_mixto = []
                self._detalles_mixto = None
                self.submetodo_cambiado.emit("")
                self._finalizar_cobranza_con_motor(self._monto_a_cobrar, "Mixto", extra)
                return
            self._ejecutar_siguiente_paso_mixto()
            return
        self._finalizar_cobranza_con_motor(self._monto_a_cobrar, medio, det)

    def _finalizar_cobranza_con_motor(self, monto_lienzo, medio, detalles):
        if not hasattr(self, '_monto_a_cobrar'):
            return
        self.motor.finalizar(self.cliente_id, self._monto_a_cobrar, medio, detalles)
        
    def procesar_f9(self):
        from PyQt6.QtCore import Qt
        actual = self.cont_lienzos.currentWidget() if hasattr(self, "cont_lienzos") else None
        if actual is not None and actual.isVisible() and hasattr(actual, "tecla"):
            return bool(actual.tecla(Qt.Key.Key_F9))
        return False

    def eventFilter(self, watched, event):
        from PyQt6.QtCore import QEvent, Qt
        if watched == self.txt_monto_abono and event.type() == QEvent.Type.KeyPress:
            k = event.key()
            if k == Qt.Key.Key_Escape:
                self.cancelado.emit()
                return True
            elif k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._iniciar_cobranza("Efectivo")
                return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event):
        k = event.key()
        from PyQt6.QtCore import Qt
        
        if self._modo == "cobrando_lienzo":
            actual = self.cont_lienzos.currentWidget()
            if hasattr(actual, "tecla"):
                actual.tecla(k)
            return

        if k == Qt.Key.Key_Escape:
            self.cancelado.emit()
        elif k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._iniciar_cobranza("Efectivo")
        else:
            super().keyPressEvent(event)
