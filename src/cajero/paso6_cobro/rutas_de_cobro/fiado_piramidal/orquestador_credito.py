# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import pyqtSignal

class HojaVirtual:
    def __init__(self, parent):
        self.parent = parent
    def _paso(self, *a, **k): pass
    def _cliente(self, *a, **k): pass
    def isVisible(self): return self.parent.isVisible()
    def isActiveWindow(self): return self.parent.isActiveWindow()
    def ubicar(self): pass
    def _cancelar(self): self.parent.cancelado.emit()
    def confirmar(self): self.parent.procesar_enter()
    def borrar(self): 
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import Qt
        if hasattr(self.parent.via_buscador, 'caja_busqueda') and self.parent.stack.currentWidget() == self.parent.via_buscador:
            txt = self.parent.via_buscador.caja_busqueda.text()
            self.parent.via_buscador.caja_busqueda.setText(txt[:-1])
        else:
            evt = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier)
            self.parent.keyPressEvent(evt)
    def escribir(self, key):
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import Qt
        if hasattr(self.parent.via_buscador, 'caja_busqueda') and self.parent.stack.currentWidget() == self.parent.via_buscador:
            txt = self.parent.via_buscador.caja_busqueda.text()
            self.parent.via_buscador.caja_busqueda.setText(txt + str(key))
        else:
            evt = QKeyEvent(QKeyEvent.Type.KeyPress, 0, Qt.KeyboardModifier.NoModifier, str(key))
            self.parent.keyPressEvent(evt)
    def fijar_monto(self, m): pass

class OrquestadorFiadoPiramidal(QFrame):
    pago_completado = pyqtSignal(dict)
    cancelado = pyqtSignal()
    abono_registrado = pyqtSignal(object)
    submetodo_cambiado = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hoja_cuenta = HojaVirtual(self)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack)

        # Rutas Piramidales
        from .ruta1_margen_aprobado.panel_aprobado import PanelMargenAprobado
        self.via_aprobado = PanelMargenAprobado(self)
        self.via_aprobado.confirmado.connect(self._emitir_aprobado_normal)
        
        from .ruta2_limite_superado.panel_bloqueo import PanelLimiteSuperado
        self.via_bloqueo = PanelLimiteSuperado(self)
        self.via_bloqueo.pin_validado.connect(self._emitir_aprobado_normal)
        self.via_bloqueo.solicita_cobranza.connect(self._abrir_cobranza)
        
        from .modulo_cobranza.panel_cobranza import PanelCobranza
        self.via_cobranza = PanelCobranza(self)
        self.via_cobranza.abono_exitoso.connect(self._finalizar_desde_cobranza)
        self.via_cobranza.cancelado.connect(self._volver_de_cobranza)
        self.via_cobranza.submetodo_cambiado.connect(self.submetodo_cambiado.emit)
        self.via_f5 = self.via_cobranza  # Alias retrocompatible
        
        from .ruta3_cliente_nuevo.panel_nuevo import PanelClienteNuevo
        self.via_nuevo = PanelClienteNuevo(self)
        self.via_nuevo.cliente_creado.connect(self._cliente_recien_creado)

        from src.cajero.paso6_cobro.fiado_en_cobro.ui.buscador_clientes.panel_buscador import PanelBuscadorClientes
        from src.motores_empresariales.motor_busqueda_clientes.motor_busqueda import MotorBusquedaClientes
        
        self.motor_busqueda = MotorBusquedaClientes(self)
        self.via_buscador = PanelBuscadorClientes(self)
        
        self.via_buscador.texto_cambiado.connect(self.motor_busqueda.buscar_texto)
        self.motor_busqueda.sugerencias_listas.connect(self.via_buscador.mostrar_sugerencias)
        self.via_buscador.cliente_elegido.connect(self._cliente_elegido)
        self.via_buscador.creacion_solicitada.connect(self._abrir_creacion)


        self.stack.addWidget(self.via_buscador) # 0
        self.stack.addWidget(self.via_aprobado) # 1
        self.stack.addWidget(self.via_bloqueo)  # 2
        self.stack.addWidget(self.via_nuevo)    # 3
        self.stack.addWidget(self.via_cobranza) # 4

    def mostrar(self, monto, modo="Fiado"):
        self.show()
        self._modo = modo
        self._monto_carrito = monto
        self.submetodo_cambiado.emit("")
        self.stack.setCurrentWidget(self.via_buscador)
        self.via_buscador.focus_caja()
        

    def ocultar(self):
        self.hide()

    def _cliente_elegido(self, dict_datos):
        self._evaluar_cliente(int(dict_datos['id']))

    def _abrir_creacion(self, nombre):
        self.stack.setCurrentWidget(self.via_nuevo)
        self.via_nuevo.poblar_inicial(nombre)

    def _evaluar_cliente(self, cliente_id):
        if cliente_id == 0:
            self.stack.setCurrentWidget(self.via_nuevo)
            self.via_nuevo.txt_input.setFocus()
            return
            
        from src.clientes_fiado.cerebro.cerebro import cerebro
        cli = cerebro.obtener(cliente_id)
        if not cli:
            return
            
        
        c_dict = dict(cli) if hasattr(cli, "keys") else (cli if isinstance(cli, dict) else {})
        
        datos = {
            'id': c_dict.get('id'),
            'nombre': c_dict.get('nombre'),
            'deuda': c_dict.get('deuda_actual', 0.0),
            'limite': c_dict.get('limite_credito', 0.0),
            'compra': self._monto_carrito
        }
        self._datos_cliente = datos
        if getattr(self, '_modo', '') == "MasCredito":
            self._abrir_cobranza(self._datos_cliente)
        else:
            self._decidir_via_credito(datos)

    def _decidir_via_credito(self, datos):
        limite = float(datos.get('limite', 0))
        deuda = float(datos.get('deuda', 0))
        compra = float(datos.get('compra', 0))
        
        disponible = limite - deuda
        
        if compra <= disponible:
            self.via_aprobado.poblar(datos)
            self.stack.setCurrentWidget(self.via_aprobado)
        else:
            self.via_bloqueo.poblar(datos)
            self.stack.setCurrentWidget(self.via_bloqueo)

    def _emitir_aprobado_normal(self, cliente_id, _abono=0.0):
        monto_abono = float(_abono or 0.0)
        saldo_previo = float(self._datos_cliente.get('deuda', 0.0) or 0.0)
        saldo_final = saldo_previo + self._monto_carrito
        dict_salida = {
            "estado": "APROBADO",
            "cliente_id": cliente_id,
            "monto_carrito": self._monto_carrito,
            "medio_pago": "CRÉDITO",
            "condiciones_ticket": {
                "es_cuenta_corriente": True,
                "cliente_nombre": self._datos_cliente["nombre"],
                "lineas_extra": [
                    "--------------------------------",
                    ">>> CUENTA CORRIENTE <<<",
                    f"CLIENTE: {self._datos_cliente['nombre']}",
                    f"SALDO PREVIO:   ${saldo_previo:,.2f}",
                    f"ABONO COBRANZA: ${monto_abono:,.2f}",
                    f"SALDO RESTANTE: ${saldo_final:,.2f}",
                    "--------------------------------",
                    "FIRMA: _________________________"
                ]
            }
        }
        self.pago_completado.emit(dict_salida)

    def _finalizar_desde_cobranza(self):
        # Al validar el PIN y asentarse el pago/abono en COBRANZA,
        # concedemos la excepcion activa para que el validador final de Paso 6 NO vuelva a pedir PIN,
        # y enviamos inmediatamente el OK al motor de cobro para finalizar la venta y emitir ticket.
        cliente_id = int(self._datos_cliente.get('id', 0))
        monto_abono = float(getattr(self.via_cobranza, '_monto_a_cobrar', 0.0) or 0.0)
        try:
            from src.clientes_fiado.cerebro.cerebro import cerebro
            from src.cajero.cajero_activo import CajeroActivo
            cerebro.conceder_excepcion(cliente_id, self._monto_carrito, CajeroActivo.nombre)
            cli = cerebro.obtener(cliente_id)
            if cli:
                c_dict = dict(cli) if hasattr(cli, "keys") else (cli if isinstance(cli, dict) else {})
                self._datos_cliente['deuda'] = float(c_dict.get('deuda_actual', 0.0) or 0.0)
        except Exception:
            pass
        self._emitir_aprobado_normal(cliente_id, monto_abono)

    _finalizar_desde_f5 = _finalizar_desde_cobranza  # Retrocompatibilidad

    def _recargar_cobranza(self):
        from src.clientes_fiado.cerebro.cerebro import cerebro
        cli = cerebro.obtener(self._datos_cliente['id'])
        if cli:
            c_dict = dict(cli) if hasattr(cli, "keys") else (cli if isinstance(cli, dict) else {})
            self._datos_cliente['deuda'] = float(c_dict.get('deuda_actual', 0.0))
        self.via_cobranza.poblar(self._datos_cliente)

    _recargar_f5 = _recargar_cobranza  # Retrocompatibilidad

    def _volver_de_cobranza(self):
        # El abono redujo la deuda, volvemos a la pantalla verde o bloqueo según corresponda.
        cw = self.via_aprobado if self._datos_cliente['compra'] <= self._datos_cliente['limite'] else self.via_bloqueo
        # Forzar estado aprobado si ya habian puesto el PIN (cw == via_bloqueo)
        if cw == self.via_bloqueo:
            self.via_bloqueo._estado_aprobado = True
        self.stack.setCurrentWidget(cw)

    _volver_de_f5 = _volver_de_cobranza  # Retrocompatibilidad
        
    def _abrir_cobranza(self, datos):
        self.via_cobranza.poblar(datos)
        self.stack.setCurrentWidget(self.via_cobranza)

    _abrir_puente_f5 = _abrir_cobranza  # Retrocompatibilidad

    def _volver_a_bloqueo(self):
        self.stack.setCurrentWidget(self.via_bloqueo)

    def _cliente_recien_creado(self, dict_datos):
        self._datos_cliente = dict_datos
        self._datos_cliente['compra'] = self._monto_carrito
        self._decidir_via_credito(self._datos_cliente)

    def procesar_cobranza(self):
        cw = self.stack.currentWidget()
        if cw in (self.via_aprobado, self.via_bloqueo):
            self._abrir_cobranza(self._datos_cliente)
            return True
        return False

    procesar_f5 = procesar_cobranza  # Retrocompatibilidad

    def procesar_f9(self):
        cw = self.stack.currentWidget()
        if cw == self.via_cobranza and hasattr(self.via_cobranza, "procesar_f9"):
            return self.via_cobranza.procesar_f9()
        return False

    def verificar_qr(self):
        cw = self.stack.currentWidget()
        if cw == self.via_cobranza and hasattr(self.via_cobranza, "verificar_qr"):
            return self.via_cobranza.verificar_qr()
        return False
        
    def bloquea_enter(self):
        return True

    def procesar_enter(self):
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import Qt
        
        if self.stack.currentWidget() == self.via_buscador:
            self.via_buscador.aceptar_actual()
            return
        if self.stack.currentWidget() == self.via_nuevo:
            self.via_nuevo._procesar()
            return
            
        evt = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        self.keyPressEvent(evt)

    def keyPressEvent(self, event):
        from PyQt6.QtCore import Qt
        if event.key() == Qt.Key.Key_Escape:
            if self.stack.currentWidget() == self.via_cobranza:
                self._volver_de_cobranza()
            elif self.stack.currentWidget() in (self.via_aprobado, self.via_bloqueo, self.via_nuevo):
                self.stack.setCurrentWidget(self.via_buscador)
                self.via_buscador.focus_caja()
                
            else:
                self.cancelado.emit()
        else:
            if self.stack.currentWidget():
                self.stack.currentWidget().keyPressEvent(event)

