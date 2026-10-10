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
        self.via_bloqueo.solicita_f5.connect(self._abrir_puente_f5)
        
        from .ruta2_limite_superado.puente_f5_cobranza import PuenteF5Cobranza
        self.via_f5 = PuenteF5Cobranza(self)
        self.via_f5.pago_completado.connect(self.pago_completado.emit)
        self.via_f5.cancelado.connect(self._volver_a_bloqueo)
        
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
        self.stack.addWidget(self.via_f5)       # 4

    def mostrar(self, monto, modo="Fiado"):
        self.show()
        self._monto_carrito = monto
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

    def _emitir_aprobado_normal(self, cliente_id, _abono):
        saldo_final = self._datos_cliente['deuda'] + self._monto_carrito
        dict_salida = {
            "estado": "APROBADO",
            "cliente_id": cliente_id,
            "monto_carrito": self._monto_carrito,
            "medio_pago": "CR\xc9DITO",
            "condiciones_ticket": {
                "es_cuenta_corriente": True,
                "cliente_nombre": self._datos_cliente["nombre"],
                "lineas_extra": [
                    "--------------------------------",
                    ">>> CUENTA CORRIENTE <<<",
                    f"CLIENTE: {self._datos_cliente['nombre']}",
                    f"SALDO PREVIO:   ${self._datos_cliente['deuda']:,.2f}",
                    f"ABONO F5:       $0.00",
                    f"SALDO RESTANTE: ${saldo_final:,.2f}",
                    "--------------------------------",
                    "FIRMA: _________________________"
                ]
            }
        }
        self.pago_completado.emit(dict_salida)

    def _abrir_puente_f5(self, datos):
        self.via_f5.poblar(datos)
        self.stack.setCurrentWidget(self.via_f5)

    def _volver_a_bloqueo(self):
        self.stack.setCurrentWidget(self.via_bloqueo)

    def _cliente_recien_creado(self, dict_datos):
        self._datos_cliente = dict_datos
        self._datos_cliente['compra'] = self._monto_carrito
        self._decidir_via_credito(self._datos_cliente)

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
            if self.stack.currentWidget() == self.via_f5:
                self._volver_a_bloqueo()
            elif self.stack.currentWidget() in (self.via_aprobado, self.via_bloqueo, self.via_nuevo):
                self.stack.setCurrentWidget(self.via_buscador)
                self.via_buscador.focus_caja()
                
            else:
                self.cancelado.emit()
        else:
            if self.stack.currentWidget():
                self.stack.currentWidget().keyPressEvent(event)

