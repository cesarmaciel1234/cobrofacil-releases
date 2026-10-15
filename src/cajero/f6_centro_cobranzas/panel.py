"""Paso 5 F6: cobranza de cuentas. No crea clientes (eso es paso 6 crédito)."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from src.motores_empresariales.motor_cobranzas_medios.motor_cobranza import MotorCobranzaMedios, ResultadoAbonoPrevio
from src.cajero.f6_centro_cobranzas.consulta import buscar_cuentas

# Componentes modulares copiados para F6
from src.cajero.f6_centro_cobranzas.componentes_f6.ui_buscador.panel_buscador import PanelBuscadorClientes
from src.cajero.f6_centro_cobranzas.componentes_f6.ui_estado.panel_estado import PanelEstadoCredito
from src.cajero.f6_centro_cobranzas.componentes_f6.ui_selector.panel_selector import PanelSelectorCobranza
from src.utils.dinero import redondear_dinero

class CentroCobranzasPanel(QWidget):
    """Panel F6 del paso 5: solo cobranza con medios de pago."""
    pago_listo = pyqtSignal(int, float)
    abono_registrado = pyqtSignal(ResultadoAbonoPrevio)
    cambio = pyqtSignal(str)
    cancelado = pyqtSignal()

    def __init__(self, parent=None, perfil="Cajero"):
        super().__init__(parent)
        self._perfil = (perfil or "Cajero").strip() or "Cajero"
        self._cliente_id = None
        self._cliente_nombre = ""
        self._deuda_actual = 0.0
        self._monto = 0.0
        self._modo = "buscando"
        self._cola_digital = None
        self._mixto_detalle = None
        self._hilo_hist = None
        self._hist_gen = 0
        
        self.setStyleSheet("background: transparent; border: none;")
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        row_center = QHBoxLayout()
        row_center.addStretch(1)
        self.card = QFrame()
        self.card.setMinimumWidth(850)
        self.card.setMaximumWidth(950)
        self.card.setObjectName("PanelFiadoCobro")
        self.card.setStyleSheet(
            "QFrame#PanelFiadoCobro { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; }"
        )

        lay = QVBoxLayout(self.card)
        lay.setContentsMargins(36, 28, 36, 24)
        lay.setSpacing(10)

        tit = QLabel("CENTRO DE COBRANZAS")
        tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tit.setStyleSheet(
            "color: #1E3A8A; font-size: 14px; font-weight: 900; "
            "letter-spacing: 2px; border: none; background: transparent;"
        )
        lay.addWidget(tit)

        self.stack = QStackedWidget()
        lay.addWidget(self.stack)

        self.motor_cobranza = MotorCobranzaMedios(self, perfil=self._perfil)
        self.motor_cobranza.set_pedir_pin_callback(self._pin)
        self.motor_cobranza.abono_registrado.connect(self.abono_registrado.emit)
        self.motor_cobranza.pago_listo.connect(lambda cid, m: self._finalizado_ok(cid, m))
        self.motor_cobranza.error_cobranza.connect(lambda e: self._volver_de_lienzo())
        self.motor = self.motor_cobranza

        self._q = ""
        self._timer_busca = QTimer(self)
        self._timer_busca.setSingleShot(True)
        self._timer_busca.timeout.connect(self._consultar_cuentas)

        self.panel_buscador = PanelBuscadorClientes()
        self.panel_buscador.caja_busqueda.installEventFilter(self)
        self.panel_buscador.texto_cambiado.connect(self._on_texto_busqueda)
        self.panel_buscador.cliente_elegido.connect(self.seleccionar_cliente_directo)
        self.stack.addWidget(self.panel_buscador)

        # 2. Cobranza
        self.vista_cobranza = QWidget()
        lay_cob = QVBoxLayout(self.vista_cobranza)
        lay_cob.setContentsMargins(16, 16, 16, 16)
        
        self.panel_estado = PanelEstadoCredito()
        self.panel_selector = PanelSelectorCobranza()
        
        self.icono = self.panel_estado.icono
        self.estado = self.panel_estado.estado
        self.detalle = self.panel_estado.detalle
        self.ultimo_pago_lbl = self.panel_estado.ultimo_pago_lbl
        self.txt_monto_abono = self.panel_estado.txt_monto_abono
        self.btn_abono_libre = self.panel_estado.btn_abono_libre
        self.btn_imprimir_resumen = self.panel_estado.btn_imprimir_resumen
        self.btn_iniciar_pago = self.panel_estado.btn_iniciar_pago
        self.btn_iniciar_pago.clicked.connect(self._mostrar_controles_pago)
        self.btn_imprimir_resumen.clicked.connect(self._imprimir_estado_cuenta)
        self.instruccion = self.panel_estado.instruccion
        self.cont_botones = self.panel_selector.cont_botones
        self.cont_lienzos = self.panel_selector.cont_lienzos
        
        self.txt_monto_abono.installEventFilter(self)
        
        self.lienzo_efectivo = self.panel_selector.lienzo_efectivo
        self.lienzo_qr = self.panel_selector.lienzo_qr
        self.lienzo_tarjeta = self.panel_selector.lienzo_tarjeta
        self.lienzo_transferencia = self.panel_selector.lienzo_transferencia
        self.lienzo_mixto = self.panel_selector.lienzo_mixto
        
        lay_cob.addWidget(self.panel_estado)
        lay_cob.addWidget(self.panel_selector)
        self.stack.addWidget(self.vista_cobranza)

        self.panel_selector.btn_efectivo.clicked.connect(lambda: self._iniciar_cobranza("Efectivo"))
        self.panel_selector.btn_qr.clicked.connect(lambda: self._iniciar_cobranza("QR"))
        self.panel_selector.btn_tarjeta.clicked.connect(lambda: self._iniciar_cobranza("Tarjeta"))
        self.panel_selector.btn_transferencia.clicked.connect(lambda: self._iniciar_cobranza("Transferencia"))
        self.panel_selector.btn_mixto.clicked.connect(lambda: self._iniciar_cobranza("Mixto"))
        
        self.btn_abono_libre.clicked.connect(lambda: self._iniciar_cobranza("Efectivo"))

        self.lienzo_efectivo.listo.connect(lambda monto: self._finalizar_cobranza_con_motor(monto, "Efectivo", None))
        self.lienzo_efectivo.volver.connect(self._volver_de_lienzo)
        
        self.lienzo_qr.listo.connect(lambda det: self._digital_listo("QR", det))
        self.lienzo_qr.volver.connect(self._volver_de_lienzo)
        
        self.lienzo_tarjeta.listo.connect(lambda det: self._digital_listo("Tarjeta", det))
        self.lienzo_tarjeta.volver.connect(self._volver_de_lienzo)
        
        self.lienzo_transferencia.listo.connect(lambda det: self._digital_listo("Transferencia", det))
        self.lienzo_transferencia.volver.connect(self._volver_de_lienzo)
        self.lienzo_mixto.listo.connect(self._armar_cola_mixto)
        self.lienzo_mixto.volver.connect(self._volver_de_lienzo)

        row_center.addWidget(self.card)
        row_center.addStretch(1)
        outer.addLayout(row_center)

    def _pin(self):
        from src.cajero.paso5_terminal.dialogos.pin.dialogo_pin import DialogoPIN
        from src.utils.qt_compat import qt_exec
        from src.cajero.cajero_activo import CajeroActivo
        dlg = DialogoPIN(CajeroActivo.nombre, self)
        if qt_exec(dlg) and dlg.ok:
            return True
        return False

    def _on_texto_busqueda(self, texto):
        self._q = (texto or "").strip()
        if len(self._q) < 3:
            self.panel_buscador.mostrar_sugerencias([])
            return
        self._timer_busca.start(160)

    def _consultar_cuentas(self):
        try:
            filas = buscar_cuentas(self._q)
        except Exception:
            filas = []
        self.panel_buscador.mostrar_sugerencias(filas)

    def seleccionar_cliente_directo(self, ficha, monto_sugerido=None):
        f = dict(ficha) if hasattr(ficha, "keys") else {}
        if f.get("id") and f.get("deuda_actual") is None and f.get("deuda") is None:
            try:
                from src.clientes_fiado.cerebro.cerebro import cerebro
                full = cerebro.obtener(f.get("id"))
                if full and hasattr(full, "keys"):
                    f = dict(full)
            except Exception:
                pass
        self._monto_sugerido_externo = monto_sugerido
        self._cliente_id = f.get("id")
        self._cliente_nombre = str(f.get("nombre") or f.get("nombre_completo") or "")
        try:
            self._deuda_actual = float(f.get("deuda_actual") if f.get("deuda_actual") is not None else f.get("deuda") or 0)
        except (TypeError, ValueError):
            self._deuda_actual = 0.0
        self._mostrar_ficha()

    def _mostrar_ficha(self):
        self.card.setStyleSheet("QFrame#PanelFiadoCobro { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; }")
        self.estado.setText(f"Hola {self._cliente_nombre}")
        
        if self._deuda_actual < -0.009:
            self.detalle.setText(f"Saldo a favor: ${abs(self._deuda_actual):,.2f}")
            self.detalle.setStyleSheet("color: #10B981; font-size: 36px; font-weight: 900; background: transparent; border: none;")
        elif self._deuda_actual > 0.009:
            self.detalle.setText(f"Deuda actual: ${self._deuda_actual:,.2f}")
            self.detalle.setStyleSheet("color: #B91C1C; font-size: 36px; font-weight: 900; background: transparent; border: none;")
        else:
            self.detalle.setText("Al día · se puede cobrar y deja saldo a favor")
            self.detalle.setStyleSheet("color: #047857; font-size: 22px; font-weight: 900; background: transparent; border: none;")
            
        self.icono.hide()
        
        # Ocultar botones de pago por defecto
        self.txt_monto_abono.hide()
        self.btn_abono_libre.hide()
        self.instruccion.hide()
        self.cont_botones.hide()
        self._cerrar_lienzos()
        
        # Mostrar botones de accion iniciales
        self.btn_imprimir_resumen.show()
        self.btn_iniciar_pago.show()
        
        if self._monto_sugerido_externo:
            # Si entramos a F6 y ya nos habian pasado un monto para cobrar/pagar, vamos directo
            self._mostrar_controles_pago()
        
        self._modo = "vista_cliente"
        self.stack.setCurrentWidget(self.vista_cobranza)
        self.setFocus()
        self._pedir_historial()

    def _pedir_historial(self):
        lbl = getattr(self.panel_estado, "lbl_historial", None)
        if lbl is None:
            return
        lbl.setText("Historial…")
        lbl.show()
        self._hist_gen += 1
        gen = self._hist_gen
        if self._hilo_hist is not None:
            try:
                self._hilo_hist.listo.disconnect()
            except TypeError:
                pass
        try:
            from src.cajero.f6_centro_cobranzas.consulta_historial.hilo import HiloMovimientosCajero
        except Exception:
            lbl.hide()
            return
        self._hilo_hist = HiloMovimientosCajero(self._cliente_id, self)
        self._hilo_hist.listo.connect(lambda movs, err, g=gen: self._mostrar_historial(movs, err, g))
        self._hilo_hist.finished.connect(self._hilo_hist.deleteLater)
        self._hilo_hist.start()

    def _mostrar_historial(self, movs, error, gen):
        if gen != self._hist_gen:
            return
        lbl = getattr(self.panel_estado, "lbl_historial", None)
        if lbl is None:
            return
        if error:
            lbl.hide()
            return
        lineas = []
        for dato in list(movs or [])[:4]:
            lineas.append(str(dato.get("linea") or ""))
        if not lineas:
            lbl.setText("Sin movimientos previos.")
            lbl.show()
            return
        lbl.setText("\n".join(lineas))
        lbl.show()


    def _mostrar_controles_pago(self):
        self._modo = "preparando_pago"
        self.btn_iniciar_pago.hide()
        self.btn_imprimir_resumen.hide()
        if getattr(self.panel_estado, "lbl_historial", None):
            self.panel_estado.lbl_historial.hide()
        
        monto_sugerido = self._deuda_actual if self._deuda_actual > 0.009 else 0.0
        if monto_sugerido > 0:
            self.txt_monto_abono.setText(f"{monto_sugerido:.2f}".replace('.', ','))
        else:
            self.txt_monto_abono.clear()
            self.txt_monto_abono.setPlaceholderText("Monto a cobrar (queda a favor)")
        self.txt_monto_abono.show()
        self.btn_abono_libre.show()
        self.instruccion.show()
        self.cont_botones.show()
        self.txt_monto_abono.setFocus()
        self.txt_monto_abono.selectAll()
        if getattr(self, '_monto_sugerido_externo', None):
            self.txt_monto_abono.setText(str(float(self._monto_sugerido_externo)))
            self._monto_sugerido_externo = None
        if getattr(self, '_monto_sugerido_externo', None):
            self.txt_monto_abono.setText(str(float(self._monto_sugerido_externo)))
            self._monto_sugerido_externo = None

    def _imprimir_estado_cuenta(self):
        try:
            from src.hardware.printer import printer_manager
            printer_manager.imprimir_saldo_fiado(self._cliente_nombre, self._deuda_actual, 0.0, self._deuda_actual)
            
            from src.notificaciones.motor.estado import publicar
            publicar("cobro_ok", f"??? Estado de cuenta impreso: {self._cliente_nombre}", segundos=5)
        except Exception as e:
            import logging
            logging.getLogger("PunPro").error(f"Error imprimiendo resumen: {e}")
            from src.notificaciones.motor.estado import publicar
            publicar("error", f"Error imprimiendo resumen: {e}", segundos=5)

    def _iniciar_cobranza(self, metodo="Efectivo"):
        texto = self.txt_monto_abono.text().replace('.', '').replace(',', '.')
        if not texto.strip(): return
        monto = redondear_dinero(float(texto))
        if monto <= 0: return

        self._monto_a_cobrar = monto
        
        self._modo = "cobrando_lienzo"
        self.txt_monto_abono.hide()
        self.btn_abono_libre.hide()
        self.cont_botones.hide()
        self.instruccion.hide()
        
        self._abrir_lienzo(metodo, monto)

    def _abrir_lienzo(self, metodo, monto):
        self.cont_lienzos.show()
        if metodo == "Efectivo":
            self.cont_lienzos.setCurrentWidget(self.lienzo_efectivo)
            self.lienzo_efectivo.arrancar(monto)
        elif metodo == "QR":
            self.cont_lienzos.setCurrentWidget(self.lienzo_qr)
            self.lienzo_qr.arrancar(monto, title="Abono a Cuenta", description="Abono a cuenta corriente")
        elif metodo == "Tarjeta":
            self.cont_lienzos.setCurrentWidget(self.lienzo_tarjeta)
            self.lienzo_tarjeta.arrancar(monto, descripcion="Abono a Cuenta Corriente")
        elif metodo == "Transferencia":
            self.cont_lienzos.setCurrentWidget(self.lienzo_transferencia)
            self.lienzo_transferencia.arrancar(monto)
        elif metodo == "Mixto":
            self.cont_lienzos.setCurrentWidget(self.lienzo_mixto)
            self.lienzo_mixto.arrancar(monto)

    def _digital_listo(self, nombre, detalle):
        if getattr(self, "_cola_digital", None) is not None:
            if str(detalle or "").upper() == "F9 MANUAL":
                extra = dict(getattr(self, "_mixto_detalle", {}) or {})
                extra["pago_id"] = "F9 MANUAL"
                self._cola_digital = None
                self._mixto_detalle = None
                self._finalizar_cobranza_con_motor(self._monto_a_cobrar, "Mixto", extra)
                return
            self._seguir_cola_digital()
            return
        self._finalizar_cobranza_con_motor(self._monto_a_cobrar, nombre, detalle)

    def _armar_cola_mixto(self, partes):
        partes = partes or {}
        self._mixto_detalle = partes
        self._cola_digital = [
            (clave, float(partes.get(clave) or 0))
            for clave in ("Transferencia", "Tarjeta", "QR")
            if float(partes.get(clave) or 0) > 0.009
        ]
        self._seguir_cola_digital()

    def _seguir_cola_digital(self):
        cola = getattr(self, "_cola_digital", None)
        if not cola:
            detalle = getattr(self, "_mixto_detalle", {}) or {}
            self._cola_digital = None
            self._mixto_detalle = None
            self._finalizar_cobranza_con_motor(self._monto_a_cobrar, "Mixto", detalle)
            return
        clave, valor = cola.pop(0)
        self._abrir_lienzo(clave, valor)
            
    def tecla(self, k):
        """Flechas de esta hoja. No abre F2 ni F5."""
        if k in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
            if self._modo == "vista_cliente":
                if k in (Qt.Key.Key_Right, Qt.Key.Key_Down):
                    self.btn_iniciar_pago.setFocus()
                else:
                    self.btn_imprimir_resumen.setFocus()
            return True
        return False

    def keyPressEvent(self, event):
        from PyQt6.QtCore import Qt
        if event.key() == Qt.Key.Key_Escape:
            if self._modo == "buscando":
                self.ocultar()
                self.cancelado.emit()
                return
            elif self._modo == "vista_cliente":
                self._volver_al_buscador()
                return
            elif self._modo == "preparando_pago":
                self._cancelar_preparacion_pago()
                return
            elif self._modo == "cobrando_lienzo":
                self._volver_de_lienzo()
                return
        if self.tecla(event.key()):
            event.accept()
            return
        super().keyPressEvent(event)
        
    def _volver_al_buscador(self):
        self._modo = "buscando"
        self._cliente_id = None
        self.stack.setCurrentWidget(self.panel_buscador)
        self.panel_buscador.caja_busqueda.setText("")
        self.panel_buscador.caja_busqueda.setFocus()
        
    def _cancelar_preparacion_pago(self):
        self._modo = "vista_cliente"
        self.txt_monto_abono.hide()
        self.btn_abono_libre.hide()
        self.instruccion.hide()
        self.cont_botones.hide()
        self.btn_iniciar_pago.show()
        self.btn_imprimir_resumen.show()
        self.setFocus()

    def _volver_de_lienzo(self):
        self._cola_digital = None
        self._mixto_detalle = None
        self._modo = "preparando_pago"
        self._cerrar_lienzos()
        self.txt_monto_abono.show()
        self.btn_abono_libre.show()
        self.instruccion.show()
        self.cont_botones.show()
        self.txt_monto_abono.setFocus()
        self.txt_monto_abono.selectAll()
        
    def _cerrar_lienzos(self):
        for lienzo in (self.lienzo_efectivo, self.lienzo_qr, self.lienzo_tarjeta, self.lienzo_transferencia):
            try:
                lienzo.cerrar()
            except Exception:
                pass
        self.cont_lienzos.hide()

    def _finalizado_ok(self, cid, m):
        self._cerrar_lienzos()
        self._modo = "listo"
        self.pago_listo.emit(cid, m)

    def _finalizar_cobranza_con_motor(self, monto, metodo, detalle):
        self.motor.finalizar(self._cliente_id, monto, metodo, detalle)

    def ocultar(self):
        self._modo = "oculto"
        self._cerrar_lienzos()
        self.hide()

    def eventFilter(self, obj, event):
        txt_monto = getattr(self, 'txt_monto_abono', None)
        caja_busq = getattr(self.panel_buscador, 'caja_busqueda', None) if hasattr(self, 'panel_buscador') else None

        if txt_monto and obj == txt_monto and event.type() == event.Type.KeyPress:
            from PyQt6.QtCore import Qt
            if event.key() == Qt.Key.Key_Escape:
                self._cancelar_preparacion_pago()
                return True
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._iniciar_cobranza("Efectivo")
                return True
        elif caja_busq and obj == caja_busq and event.type() == event.Type.KeyPress:
            from PyQt6.QtCore import Qt
            if event.key() == Qt.Key.Key_Escape:
                self.ocultar()
                self.cancelado.emit()
                return True
            elif event.key() == Qt.Key.Key_Up:
                self.panel_buscador.navegar("arriba")
                return True
            elif event.key() == Qt.Key.Key_Down:
                self.panel_buscador.navegar("abajo")
                return True
        return super().eventFilter(obj, event)

    def procesar_enter(self):
        if self._modo == "buscando":
            self.panel_buscador.aceptar_actual()
        elif self._modo == "cobranza" and getattr(self, "_cliente_id", None):
            self._iniciar_cobranza("Efectivo")
        elif self._modo == "cobrando_lienzo":
            actual = self.cont_lienzos.currentWidget()
            if hasattr(actual, "tecla"):
                actual.tecla(Qt.Key.Key_Return)

    def procesar_f9(self):
        actual = self.cont_lienzos.currentWidget() if hasattr(self, "cont_lienzos") else None
        if actual is not None and actual.isVisible() and hasattr(actual, "tecla"):
            return bool(actual.tecla(Qt.Key.Key_F9))
        return False

    def mostrar(self, _=None):
        self._volver_al_buscador()
