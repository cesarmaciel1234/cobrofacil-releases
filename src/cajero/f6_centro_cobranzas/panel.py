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
from PyQt6.QtCore import QThread

class HiloInteresCajero(QThread):
    listo = pyqtSignal(int, float)

    def __init__(self, cliente_id, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id

    def run(self):
        try:
            from src.clientes_fiado.cerebro.cerebro import cerebro
            mapa = cerebro.intereses_acumulados([self.cliente_id])
            interes = float(mapa.get(self.cliente_id, 0.0) or 0.0)
            self.listo.emit(self.cliente_id, interes)
        except Exception:
            self.listo.emit(self.cliente_id, 0.0)


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
        self._interes_estimado = 0.0
        self._error_interes = False
        self._monto_sugerido_base = None
        
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
        self.motor_cobranza.abono_registrado.connect(self.abono_registrado.emit)
        self.motor_cobranza.pago_listo.connect(lambda cid, m: self._finalizado_ok(cid, m))
        self.motor_cobranza.error_cobranza.connect(self._al_fallar_cobranza)
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
        self.btn_imprimir_resumen.clicked.connect(self._abrir_historial_cliente)
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
        
        self.btn_abono_libre.clicked.connect(
            lambda: (self.txt_monto_abono.setFocus(), self.txt_monto_abono.selectAll())
        )

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

    def seleccionar_cliente_directo(self, ficha, monto_sugerido=None, ir_a_pago=False):
        f = dict(ficha) if hasattr(ficha, "keys") else {}
        cid = f.get("id")
        if cid and f.get("deuda_actual") is None and f.get("deuda") is None:
            try:
                from src.clientes_fiado.cerebro.cerebro import cerebro
                full = cerebro.obtener(cid)
                if full and hasattr(full, "keys"):
                    f = dict(full)
            except Exception:
                pass
        self._cliente_id = f.get("id")
        self._cliente_nombre = str(f.get("nombre") or f.get("nombre_completo") or "")
        self._interes_estimado = 0.0
        self._error_interes = False
        self._monto_sugerido_base = None

        try:
            capital_raw = float(f.get("deuda_actual") if f.get("deuda_actual") is not None else f.get("deuda") or 0)
        except (TypeError, ValueError):
            capital_raw = 0.0
        self._capital_base = capital_raw

        # Determinar de forma inmediata el total estimado y el interés acumulado
        if monto_sugerido is not None and float(monto_sugerido) > 0.009:
            self._deuda_actual = float(monto_sugerido)
            if self._capital_base > 0.009:
                self._interes_estimado = max(0.0, round(self._deuda_actual - self._capital_base, 2))
        else:
            self._deuda_actual = self._capital_base
            self._interes_estimado = 0.0
            if self._capital_base > 0.009 and self._cliente_id:
                self._iniciar_hilo_interes(self._cliente_id)

        self._monto_sugerido_externo = monto_sugerido
        self._ir_a_pago = bool(ir_a_pago)
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
            
        if self._deuda_actual > 0.009 and self._interes_estimado > 0.009:
            self.detalle.setToolTip(
                f"Capital: ${self._capital_base:,.2f}  +  Interés: ${self._interes_estimado:,.2f}"
            )
        else:
            self.detalle.setToolTip("")
        estimado = getattr(self.panel_estado, "lbl_total_estimado", None)
        if estimado:
            estimado.hide()

        lbl_hist = getattr(self.panel_estado, "lbl_historial", None)
        if lbl_hist:
            lbl_hist.hide()

        self.icono.hide()
        
        # Ocultar botones de pago por defecto
        self.txt_monto_abono.hide()
        self.btn_abono_libre.hide()
        self.instruccion.hide()
        self.cont_botones.hide()
        if getattr(self.panel_estado, "lbl_pregunta_monto", None):
            self.panel_estado.lbl_pregunta_monto.hide()
        self._cerrar_lienzos()
        
        # Mostrar botones de accion iniciales
        self.btn_imprimir_resumen.show()
        self.btn_iniciar_pago.show()
        
        self.stack.setCurrentWidget(self.vista_cobranza)
        if getattr(self, "_ir_a_pago", False):
            self._mostrar_controles_pago()
        else:
            self._modo = "vista_cliente"
            self.btn_iniciar_pago.setFocus()

    def _iniciar_hilo_interes(self, cliente_id):
        if getattr(self, "_hilo_int", None) is not None:
            try:
                self._hilo_int.listo.disconnect()
            except Exception:
                pass
        self._hilo_int = HiloInteresCajero(cliente_id, self)
        self._hilo_int.listo.connect(self._al_llegar_interes)
        self._hilo_int.finished.connect(self._hilo_int.deleteLater)
        self._hilo_int.start()

    def _al_llegar_interes(self, cliente_id, interes):
        if cliente_id != self._cliente_id or interes <= 0.009:
            return
        self._interes_estimado = interes
        self._deuda_actual = round(self._capital_base + interes, 2)
        if self._modo == "vista_cliente":
            self.detalle.setText(f"Deuda actual: ${self._deuda_actual:,.2f}")
            self.detalle.setToolTip(
                f"Capital: ${self._capital_base:,.2f}  +  Interés: ${self._interes_estimado:,.2f}"
            )
        elif self._modo == "preparando_pago":
            texto_base = f"{self._capital_base:.2f}".replace('.', ',')
            if self.txt_monto_abono.text() in (texto_base, ""):
                texto_nuevo = f"{self._deuda_actual:.2f}".replace('.', ',')
                self.txt_monto_abono.setText(texto_nuevo)
                self._monto_sugerido_base = texto_nuevo

    def _pedir_historial(self):
        # El historial se consulta a demanda mediante el botón [Ver / Imprimir]
        pass

    def _mostrar_historial(self, movs, error, gen):
        pass

    def _actualizar_monto_sugerido(self, total_estimado):
        pass

    def _mostrar_controles_pago(self):
        self._modo = "preparando_pago"
        self.btn_iniciar_pago.hide()
        self.btn_imprimir_resumen.hide()
        if getattr(self.panel_estado, "lbl_historial", None):
            self.panel_estado.lbl_historial.hide()
        
        monto_sugerido = (
            self._deuda_actual
            if self._deuda_actual > 0.009
            else 0.0
        )
        if monto_sugerido > 0:
            self.txt_monto_abono.setText(f"{monto_sugerido:.2f}".replace('.', ','))
            self._monto_sugerido_base = self.txt_monto_abono.text()
        else:
            self.txt_monto_abono.clear()
            self._monto_sugerido_base = None
            self.txt_monto_abono.setPlaceholderText("Ejemplo: 100 (queda a favor)")
        if getattr(self.panel_estado, "lbl_pregunta_monto", None):
            self.panel_estado.lbl_pregunta_monto.show()
        self.txt_monto_abono.show()
        self.btn_abono_libre.hide()
        self.instruccion.show()
        self.cont_botones.show()
        self.txt_monto_abono.setFocus()
        self.txt_monto_abono.selectAll()
        externo = getattr(self, "_monto_sugerido_externo", None)
        self._monto_sugerido_externo = None
        if externo:
            try:
                self.txt_monto_abono.setText(f"{float(externo):.2f}".replace(".", ","))
                self._monto_sugerido_base = self.txt_monto_abono.text()
            except (TypeError, ValueError):
                pass

    def _abrir_historial_cliente(self):
        """Abre el historial crudo: ver ticket/cobro e imprimir desde esa ventana."""
        if not self._cliente_id:
            return
        from src.utils.qt_compat import qt_exec
        from src.admin.clientes.componentes.dialogo_historial_cliente import DialogoHistorialCliente

        dlg = DialogoHistorialCliente(int(self._cliente_id), self)
        qt_exec(dlg)
        # Por si abonó / borró / editó desde el historial
        try:
            from src.clientes_fiado.cerebro.cerebro import cerebro
            ficha = cerebro.obtener(self._cliente_id) or {}
            if ficha:
                self.seleccionar_cliente_directo(ficha)
        except Exception:
            pass

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
        if getattr(self.panel_estado, "lbl_pregunta_monto", None):
            self.panel_estado.lbl_pregunta_monto.hide()
        self.detalle.hide()
        
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
            for clave in ("Tarjeta", "Transferencia", "QR")
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
        if getattr(self.panel_estado, "lbl_pregunta_monto", None):
            self.panel_estado.lbl_pregunta_monto.hide()
        self.detalle.show()
        self.btn_iniciar_pago.show()
        self.btn_imprimir_resumen.show()
        self.setFocus()

    def _al_fallar_cobranza(self, error):
        self._volver_de_lienzo()
        try:
            from src.notificaciones.motor.estado import publicar
            publicar("cobro_error", f"⚠️ Cobranza no completada: {error}", segundos=6)
        except Exception:
            pass

    def _volver_de_lienzo(self):
        self._cola_digital = None
        self._mixto_detalle = None
        self._modo = "preparando_pago"
        self._cerrar_lienzos()
        self.detalle.show()
        if getattr(self.panel_estado, "lbl_pregunta_monto", None):
            self.panel_estado.lbl_pregunta_monto.show()
        self.txt_monto_abono.show()
        self.btn_abono_libre.hide()
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
        if hasattr(self, "lienzo_mixto"):
            try:
                self.lienzo_mixto.vaciar()
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
        elif self._modo == "vista_cliente":
            focused = self.focusWidget()
            if focused == self.btn_imprimir_resumen:
                self._abrir_historial_cliente()
            else:
                self._mostrar_controles_pago()
        elif self._modo in ("preparando_pago", "cobranza") and getattr(self, "_cliente_id", None):
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
