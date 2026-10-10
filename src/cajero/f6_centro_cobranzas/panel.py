"""Fiado: busca al cliente y toma el abono (F6)."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

# Importar motores globales
from src.motores_empresariales.motor_busqueda_clientes.motor_busqueda import MotorBusquedaClientes
from src.motores_empresariales.motor_cobranzas_medios.motor_cobranza import MotorCobranzaMedios, ResultadoAbonoPrevio

# Componentes modulares copiados para F6
from src.cajero.f6_centro_cobranzas.componentes_f6.ui_buscador.panel_buscador import PanelBuscadorClientes
from src.cajero.f6_centro_cobranzas.componentes_f6.ui_estado.panel_estado import PanelEstadoCredito
from src.cajero.f6_centro_cobranzas.componentes_f6.ui_selector.panel_selector import PanelSelectorCobranza
from src.utils.dinero import redondear_dinero

class CentroCobranzasPanel(QWidget):
    """Panel F6 - FIADO modularizado."""
    pago_listo = pyqtSignal(int, float)
    abono_registrado = pyqtSignal(ResultadoAbonoPrevio)
    cambio = pyqtSignal(str)
    cancelado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cliente_id = None
        self._cliente_nombre = ""
        self._deuda_actual = 0.0
        self._monto = 0.0
        self._modo = "buscando"
        
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

        # Motores
        self.motor_busqueda = MotorBusquedaClientes(self)
        self.motor_cobranza = MotorCobranzaMedios(self)
        self.motor_cobranza.set_pedir_pin_callback(self._pin)
        self.motor_cobranza.abono_registrado.connect(self.abono_registrado.emit)
        self.motor_cobranza.pago_listo.connect(lambda cid, m: self._finalizado_ok(cid, m))
        self.motor_cobranza.error_cobranza.connect(lambda e: self._volver_de_lienzo())
        
        self.motor = self.motor_cobranza

        # 1. Buscador
        self.panel_buscador = PanelBuscadorClientes()
        self.panel_buscador.caja_busqueda.installEventFilter(self)
        self.panel_buscador.texto_cambiado.connect(self.motor_busqueda.buscar_texto)
        self.motor_busqueda.sugerencias_listas.connect(self.panel_buscador.mostrar_sugerencias)
        self.panel_buscador.cliente_elegido.connect(self._al_seleccionar_cliente)
        self.panel_buscador.creacion_solicitada.connect(self.motor_busqueda.buscar_estricto)
        self.motor_busqueda.limite_aprobado.connect(self._al_limite_aprobado)
        self.motor_busqueda.error_busqueda.connect(self._mostrar_error_busqueda)
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
        
        lay_cob.addWidget(self.panel_estado)
        lay_cob.addWidget(self.panel_selector)
        self.stack.addWidget(self.vista_cobranza)

        self.panel_selector.btn_efectivo.clicked.connect(lambda: self._iniciar_cobranza("Efectivo"))
        self.panel_selector.btn_qr.clicked.connect(lambda: self._iniciar_cobranza("QR"))
        self.panel_selector.btn_tarjeta.clicked.connect(lambda: self._iniciar_cobranza("Tarjeta"))
        self.panel_selector.btn_transferencia.clicked.connect(lambda: self._iniciar_cobranza("Transferencia"))
        
        self.btn_abono_libre.clicked.connect(lambda: self._iniciar_cobranza("Efectivo"))

        self.lienzo_efectivo.listo.connect(lambda monto: self._finalizar_cobranza_con_motor(monto, "Efectivo", None))
        self.lienzo_efectivo.volver.connect(self._volver_de_lienzo)
        
        self.lienzo_qr.listo.connect(lambda det: self._finalizar_cobranza_con_motor(self._monto_a_cobrar, "QR", det))
        self.lienzo_qr.volver.connect(self._volver_de_lienzo)
        
        self.lienzo_tarjeta.listo.connect(lambda det: self._finalizar_cobranza_con_motor(self._monto_a_cobrar, "Tarjeta", det))
        self.lienzo_tarjeta.fallo.connect(lambda text: self._volver_de_lienzo())
        self.lienzo_tarjeta.volver.connect(self._volver_de_lienzo)
        
        self.lienzo_transferencia.listo.connect(lambda det: self._finalizar_cobranza_con_motor(self._monto_a_cobrar, "Transferencia", det))
        self.lienzo_transferencia.volver.connect(self._volver_de_lienzo)

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

    def _mostrar_error_busqueda(self, msg):
        self.panel_buscador.lbl_error.setText(msg)
        self.panel_buscador.stack_busqueda.setCurrentIndex(1)
        self.panel_buscador.caja_busqueda.setText("")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2500, self._restaurar_buscador)

    def _restaurar_buscador(self):
        self.panel_buscador.stack_busqueda.setCurrentIndex(0)
        self.panel_buscador.caja_busqueda.setFocus()

    def seleccionar_cliente_directo(self, ficha, monto_sugerido=None):
        self._modo = "buscando"
        self._monto_sugerido_externo = monto_sugerido
        self.motor_busqueda.aprobar_credito(ficha)

    def mostrar(self, _=None):
        self._modo = "buscando"
        self._cliente_id = None
        self._cliente_nombre = ""
        
        self.card.setStyleSheet("QFrame#PanelFiadoCobro { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; }")
        self.panel_buscador.limpiar()
        self.stack.setCurrentWidget(self.panel_buscador)
        self.show()
        self.panel_buscador.focus_caja()
        self.cambio.emit("buscando")

    def _al_seleccionar_cliente(self, cliente):
        c = dict(cliente) if hasattr(cliente, "keys") else (cliente if isinstance(cliente, dict) else {})
        self.motor_busqueda.aprobar_credito(c)

    def _al_limite_aprobado(self, datos):
        self._cliente_id = datos['id']
        self._cliente_nombre = datos['nombre']
        self._modo = "cobranza"
        
        from src.clientes_fiado.cerebro.cerebro import cerebro
        cli = cerebro.obtener(self._cliente_id)
        cli_dict = dict(cli) if hasattr(cli, 'keys') else cli
        self._deuda_actual = float(cli_dict.get('deuda_actual', 0) or 0)
        
        # Consultar ultimo pago
        try:
            ultimo = cerebro.cuenta.ultimo_pago(self._cliente_id)
            if ultimo:
                # ultimo has fecha and monto
                fecha = ultimo[0]
                monto_ult = float(ultimo[1] or 0)
                self.ultimo_pago_lbl.setText(f"Ultimo pago: ${monto_ult:,.2f} el {fecha}")
                self.ultimo_pago_lbl.show()
            else:
                self.ultimo_pago_lbl.setText("No registra pagos anteriores.")
                self.ultimo_pago_lbl.show()
        except Exception:
            self.ultimo_pago_lbl.hide()
        
        self.card.setStyleSheet("QFrame#PanelFiadoCobro { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; }")
        self.estado.setText(f"Hola {self._cliente_nombre}")
        self.detalle.setText(f"Deuda actual: ${self._deuda_actual:,.2f}")
        self.icono.hide()
        
        # Ocultar botones de pago por defecto
        self.txt_monto_abono.hide()
        self.btn_abono_libre.hide()
        self.instruccion.hide()
        self.cont_botones.hide()
        self._cerrar_lienzos()
        
        # Mostrar botones de accion iniciales
        self.btn_imprimir_resumen.show()
        if self._deuda_actual > 0.01:
            self.btn_iniciar_pago.show()
        else:
            self.btn_iniciar_pago.hide()
        
        self.stack.setCurrentWidget(self.vista_cobranza)

    def _mostrar_controles_pago(self):
        self.btn_iniciar_pago.hide()
        self.btn_imprimir_resumen.hide()
        
        self.txt_monto_abono.setText(f"{self._deuda_actual:.2f}".replace('.', ','))
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
        self.btn_imprimir_resumen.show()
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

    def eventFilter(self, obj, event):
        txt_monto = getattr(self, 'txt_monto_abono', None)
        caja_busq = getattr(self.panel_buscador, 'caja_busqueda', None) if hasattr(self, 'panel_buscador') else None

        if txt_monto and obj == txt_monto and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.cancelado.emit()
                return True
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._iniciar_cobranza("Efectivo")
                return True
        elif caja_busq and obj == caja_busq and event.type() == event.Type.KeyPress:
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
        if self._modo == "cobrando_lienzo":
            actual = self.cont_lienzos.currentWidget()
            if hasattr(actual, "tecla"):
                actual.tecla(Qt.Key.Key_F9)
                return True
        return False
