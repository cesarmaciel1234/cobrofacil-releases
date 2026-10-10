from PyQt6.QtWidgets import QFrame, QVBoxLayout, QWidget, QStackedWidget
from PyQt6.QtCore import pyqtSignal, Qt

from src.utils.dinero import redondear_dinero

# Nuevos componentes modulares del ecosistema local
from src.cajero.paso6_cobro.fiado_en_cobro.ui.buscador_clientes.panel_buscador import PanelBuscadorClientes
from src.cajero.paso6_cobro.fiado_en_cobro.ui.credito_aprobado.panel_aprobado import PanelCreditoAprobado
from src.motores_empresariales.motor_busqueda_clientes.motor_busqueda import MotorBusquedaClientes

# Componentes de cobranza existentes
from src.cajero.paso6_cobro.fiado_en_cobro.componentes_fiado.estado_credito.panel_estado import PanelEstadoCredito
from src.cajero.paso6_cobro.fiado_en_cobro.componentes_fiado.selector_cobranza.panel_selector import PanelSelectorCobranza
from src.motores_empresariales.motor_cobranzas_medios.motor_cobranza import MotorCobranzaMedios, ResultadoAbonoPrevio

class HojaCuentaProxy:
    """Proxi para engañar a paso6_cobro.py que espera el viejo componente hoja_cuenta."""
    def __init__(self, panel):
        self.panel = panel

    @property
    def _paso(self):
        # 1: Buscando, 2: Cliente aprobado (esperando enter/monto)
        return 1 if self.panel.stack.currentIndex() == 0 else 2

    @property
    def _cliente(self):
        # Si estamos en paso 2, hay cliente
        cliente_id = getattr(self.panel, '_cliente_id', None)
        return {"id": cliente_id} if cliente_id else None

    def isVisible(self):
        return self.panel.isVisible()
        
    def isActiveWindow(self):
        return self.panel.isActiveWindow()

    def ubicar(self):
        pass

    def _cancelar(self):
        if self.panel.stack.currentIndex() == 0:
            self.panel._al_cancelar_busqueda()
        elif getattr(self.panel, "_modo", "") == "cobrando_lienzo":
            self.panel._volver_de_lienzo()
        else:
            self.panel.cancelado.emit()

    def confirmar(self):
        self.panel.procesar_enter()

    def borrar(self):
        if self.panel.stack.currentIndex() == 0:
            txt = self.panel.panel_buscador.caja_busqueda.text()
            self.panel.panel_buscador.caja_busqueda.setText(txt[:-1])
        elif getattr(self.panel, 'txt_monto_abono', None) and self.panel.txt_monto_abono.hasFocus():
            txt = self.panel.txt_monto_abono.text()
            self.panel.txt_monto_abono.setText(txt[:-1])

    def escribir(self, key):
        if self.panel.stack.currentIndex() == 0:
            txt = self.panel.panel_buscador.caja_busqueda.text()
            self.panel.panel_buscador.caja_busqueda.setText(txt + key)
        elif getattr(self.panel, 'txt_monto_abono', None) and self.panel.txt_monto_abono.hasFocus():
            txt = self.panel.txt_monto_abono.text()
            self.panel.txt_monto_abono.setText(txt + key)

    def fijar_monto(self, monto):
        self.panel.actualizar_monto(monto)

class PanelFiadoCobro(QFrame):
    cambio = pyqtSignal(str)
    cancelado = pyqtSignal()
    pago_listo = pyqtSignal(int, float)
    abono_registrado = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hoja_cuenta = HojaCuentaProxy(self)
        self.setObjectName("PanelFiadoCobro")
        self.setStyleSheet("QFrame#PanelFiadoCobro { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; }")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Usaremos un StackedWidget para alternar limpiamente entre las vistas locales
        self.stack = QStackedWidget()
        lay.addWidget(self.stack)

        # --- Instanciar los motores globales ---
        self.motor_busqueda = MotorBusquedaClientes(self)
        self.motor_cobranza = MotorCobranzaMedios(self)
        self.motor_cobranza.set_pedir_pin_callback(self._pin)
        self.motor_cobranza.abono_registrado.connect(self.abono_registrado.emit)
        self.motor_cobranza.pago_listo.connect(lambda cid, m: self._finalizado_ok(cid, m))
        self.motor_cobranza.error_cobranza.connect(lambda e: self._volver_de_lienzo())
        self.motor = self.motor_cobranza  # Aliasing para no romper código externo

        # --- 1. Buscador (Paso 1) ---
        self.panel_buscador = PanelBuscadorClientes()
        self.panel_buscador.caja_busqueda.installEventFilter(self)
        self.panel_buscador.texto_cambiado.connect(self.motor_busqueda.buscar_texto)
        self.motor_busqueda.sugerencias_listas.connect(self.panel_buscador.mostrar_sugerencias)
        self.panel_buscador.cliente_elegido.connect(self._al_seleccionar_cliente)
        self.panel_buscador.creacion_solicitada.connect(self.motor_busqueda.identificar_o_crear)
        self.stack.addWidget(self.panel_buscador)

        # --- 2. Aprobado (Paso 2) ---
        self.panel_aprobado = PanelCreditoAprobado()
        self.panel_aprobado.confirmado.connect(self.procesar_enter)
        self.motor_busqueda.limite_aprobado.connect(self._al_limite_aprobado)
        self.stack.addWidget(self.panel_aprobado)

        # --- 3. Cobranza (Paso 3 y 4) ---
        self.vista_cobranza = QWidget()
        lay_cob = QVBoxLayout(self.vista_cobranza)
        lay_cob.setContentsMargins(16, 16, 16, 16)
        
        self.panel_estado = PanelEstadoCredito()
        self.panel_selector = PanelSelectorCobranza()
        
        # Mapeo de estado viejo
        self.icono = self.panel_estado.icono
        self.estado = self.panel_estado.estado
        self.detalle = self.panel_estado.detalle
        self.txt_monto_abono = self.panel_estado.txt_monto_abono
        self.btn_abono_libre = self.panel_estado.btn_abono_libre
        self.instruccion = self.panel_estado.instruccion
        self.cont_botones = self.panel_selector.cont_botones
        self.cont_lienzos = self.panel_selector.cont_lienzos
        
        self.txt_monto_abono.installEventFilter(self)
        
        self.lienzo_efectivo = self.panel_selector.lienzo_efectivo
        self.lienzo_qr = self.panel_selector.lienzo_qr
        self.lienzo_tarjeta = self.panel_selector.lienzo_tarjeta
        self.lienzo_transferencia = self.panel_selector.lienzo_transferencia
        
        botones_selector = [self.panel_selector.btn_efectivo, self.panel_selector.btn_tarjeta, self.panel_selector.btn_qr, self.panel_selector.btn_transferencia]
        for btn in botones_selector:
            btn.clicked.connect(lambda ch, m=btn.text(): self._iniciar_cobranza(m))

        lay_cob.addStretch(1)
        lay_cob.addWidget(self.panel_estado)
        lay_cob.addSpacing(40)
        lay_cob.addWidget(self.panel_selector)
        lay_cob.addStretch(2)
        self.stack.addWidget(self.vista_cobranza)

        # Conexiones de los lienzos
        self.lienzo_efectivo.listo.connect(lambda monto: self._finalizar_cobranza_con_motor(monto, "Efectivo", None))
        self.lienzo_efectivo.volver.connect(self._volver_de_lienzo)
        
        self.lienzo_qr.listo.connect(lambda det: self._finalizar_cobranza_con_motor(self._monto_a_cobrar, "QR", det))
        self.lienzo_qr.volver.connect(self._volver_de_lienzo)
        
        self.lienzo_tarjeta.listo.connect(lambda det: self._finalizar_cobranza_con_motor(self._monto_a_cobrar, "Tarjeta", det))
        self.lienzo_tarjeta.fallo.connect(lambda text: self._volver_de_lienzo())
        self.lienzo_tarjeta.volver.connect(self._volver_de_lienzo)
        
        self.lienzo_transferencia.listo.connect(lambda det: self._finalizar_cobranza_con_motor(self._monto_a_cobrar, "Transferencia", det))
        self.lienzo_transferencia.volver.connect(self._volver_de_lienzo)

        self.hide()

    def procesar_f9(self):
        if self._modo == "cobrando_lienzo":
            actual = self.cont_lienzos.currentWidget()
            if hasattr(actual, "tecla"):
                from PyQt6.QtCore import Qt
                actual.tecla(Qt.Key.Key_F9)
                return True
        return False

    def bloquea_enter(self):
        return self.isVisible() and self._modo in ("buscando", "confirmando", "cobranza", "cobrando_lienzo", "transicion", "excedido", "transicion_excedido")
        
    def keyPressEvent(self, event):
        if self._modo == "excedido":
            from PyQt6.QtCore import Qt
            k = event.key()
            if k == Qt.Key.Key_Escape:
                if hasattr(self.window(), "toast"):
                    self.window().toast.cerrar()
                self._admin_pin = ""
                self.panel_estado.actualizar_pin(0)
                self.mostrar(self._monto, "Fiado")
                return
            if Qt.Key.Key_0 <= k <= Qt.Key.Key_9:
                self._admin_pin += chr(k)
                self.panel_estado.actualizar_pin(len(self._admin_pin))
                
                if len(self._admin_pin) == 4:
                    from src.cajero.cajero_activo import CajeroActivo
                    if self._admin_pin == CajeroActivo.pin_admin:
                        if hasattr(self.window(), "toast"):
                            self.window().toast.cerrar()
                        self._modo = "listo"
                        self.pago_listo.emit(self._cliente_id, 0.0)
                    else:
                        self._admin_pin = ""
                        self.panel_estado.actualizar_pin(0)
                        if hasattr(self.window(), "toast"):
                            self.window().toast.alarma("PIN INCORRECTO")
            return
        super().keyPressEvent(event)

    def procesar_enter(self):
        if self._modo == "buscando":
            self.panel_buscador.aceptar_actual()
        elif self._modo == "confirmando" and getattr(self, "_cliente_id", None):
            self._modo = "listo"
            self.pago_listo.emit(self._cliente_id, 0.0)
        elif self._modo == "cobranza" and getattr(self, "_cliente_id", None):
            self._iniciar_cobranza("Efectivo")
        elif self._modo == "cobrando_lienzo":
            actual = self.cont_lienzos.currentWidget()
            if hasattr(actual, "tecla"):
                actual.tecla(Qt.Key.Key_Return)

    def mostrar(self, monto, modo="Fiado"):
        self._monto = float(monto or 0)
        self.motor_busqueda.set_monto_venta(self._monto)
        self._modo = "buscando"
        self._cliente_id = None
        self._cliente_nombre = ""
        
        self.setStyleSheet("QFrame#PanelFiadoCobro { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; }")
        self.panel_buscador.limpiar()
        self.stack.setCurrentWidget(self.panel_buscador)
        self.show()
        self.panel_buscador.focus_caja()
        self.cambio.emit("buscando")

    def _al_seleccionar_cliente(self, cliente):
        # Cuando se hace clic en la lista de sugerencias o se acepta con enter
        c = dict(cliente) if hasattr(cliente, "keys") else (cliente if isinstance(cliente, dict) else {})
        self.motor_busqueda.aprobar_credito(c)

    def _al_limite_aprobado(self, datos):
        self._cliente_id = datos['id']
        self._cliente_nombre = datos['nombre']
        
        excedido = float(datos.get('compra', 0)) > float(datos.get('limite', 0)) + 0.01
        
        if excedido:
            self._modo = "transicion_excedido"
            self.setStyleSheet("QFrame#PanelFiadoCobro { background: #FEF2F2; border: 2px solid #F87171; border-radius: 16px; }")
            self._admin_pin = ""
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(150, self._activar_modo_excedido)
        else:
            self._modo = "transicion"
            self.setStyleSheet("QFrame#PanelFiadoCobro { background: #ECFDF5; border: 2px solid #34D399; border-radius: 16px; }")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(150, self._activar_modo_confirmando)
            
        self.panel_aprobado.poblar(datos['nombre'], datos['limite'], datos['compra'])
        self.stack.setCurrentWidget(self.panel_aprobado)
        
    def _activar_modo_excedido(self):
        self._modo = "excedido"
        self.cambio.emit("confirmando")
        if hasattr(self.window(), "toast"):
            self.window().toast.pin("Autorización Admin", 0)
        self.panel_aprobado.btn_confirmar.setFocus()
        
    def _activar_modo_confirmando(self):
        self._modo = "confirmando"
        self.cambio.emit("confirmando")
        self.panel_aprobado.btn_confirmar.setFocus()

    def activar_cobranza(self, monto_sugerido, deuda_actual):
        self._modo = "cobranza"
        self._deuda_actual = deuda_actual
        nombre = getattr(self, "_cliente_nombre", "Cliente")
        
        self.setStyleSheet("QFrame#PanelFiadoCobro { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; }")
        self.estado.setText(f"Hola {nombre}")
        total_pagar = float(deuda_actual) + float(self._monto)
        self.detalle.setText(f"Total a pagar: ${total_pagar:,.2f}")
        self.icono.hide()
        
        self.txt_monto_abono.setText(f"{monto_sugerido:.2f}".replace('.', ','))
        self.txt_monto_abono.show()
        self.btn_abono_libre.show()
        
        self.instruccion.hide()
        self.cont_botones.show()
        self._cerrar_lienzos()
        
        self.stack.setCurrentWidget(self.vista_cobranza)
        self.txt_monto_abono.setFocus()
        self.txt_monto_abono.selectAll()

    def _pin(self):
        try:
            from src.cajero.paso5_terminal.dialogos.pin.dialogo_pin import DialogoPIN
            from src.utils.qt_compat import qt_exec
            dlg = DialogoPIN("Cajero", self.window())
            return bool(qt_exec(dlg) and dlg.ok)
        except Exception:
            return False

    def _iniciar_cobranza(self, metodo="Efectivo"):
        texto = self.txt_monto_abono.text().replace('.', '').replace(',', '.')
        if not texto.strip(): return
        monto = redondear_dinero(float(texto))
        if monto <= 0: return

        self._monto_a_cobrar = monto
        self._metodo_elegido = metodo
        
        self._modo = "cobrando_lienzo"
        self.txt_monto_abono.hide()
        self.btn_abono_libre.hide()
        self.cont_botones.hide()
        self.instruccion.hide()
        
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
            
    def _volver_de_lienzo(self):
        self._modo = "cobranza"
        self._cerrar_lienzos()
        self.txt_monto_abono.show()
        self.btn_abono_libre.show()
        self.cont_botones.show()
        self.txt_monto_abono.setFocus()
        
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

    def _al_cancelar_busqueda(self):
        self._modo = "oculto"
        self.hide()
        self.cancelado.emit()

    def eventFilter(self, obj, event):
        txt_monto = getattr(self, 'txt_monto_abono', None)
        caja_busq = getattr(self.panel_buscador, 'caja_busqueda', None) if hasattr(self, 'panel_buscador') else None

        if txt_monto and obj == txt_monto and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                # Volver a paso anterior, en este caso, se podria cancelar o volver a confirmando.
                # Para simplificar y mantener la logica vieja:
                self.cancelado.emit()
                return True
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.procesar_enter()
                return True
        elif caja_busq and obj == caja_busq and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self._al_cancelar_busqueda()
                return True
            elif event.key() == Qt.Key.Key_Up:
                self.panel_buscador.navegar("arriba")
                return True
            elif event.key() == Qt.Key.Key_Down:
                self.panel_buscador.navegar("abajo")
                return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def actualizar_monto(self, nuevo_monto_venta):
        self._monto = nuevo_monto_venta
        self.motor_busqueda.set_monto_venta(self._monto)
        if getattr(self, "_modo", "") in ("cobranza", "cobrando_lienzo"):
            if getattr(self, "_modo", "") == "cobrando_lienzo":
                self._volver_de_lienzo()
            deuda = getattr(self, "_deuda_actual", 0.0)
            monto_sugerido = nuevo_monto_venta + deuda
            self.detalle.setText(f"Total a pagar: ${monto_sugerido:,.2f}")
            self.txt_monto_abono.setText(f"{monto_sugerido:.2f}".replace('.', ','))
