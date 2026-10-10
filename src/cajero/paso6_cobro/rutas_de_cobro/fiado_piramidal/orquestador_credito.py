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
        evt = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier)
        self.parent.keyPressEvent(evt)
    def escribir(self, key):
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import Qt
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
        self.via_nuevo.creado.connect(self._cliente_recien_creado)

        from src.cajero.paso6_cobro.fiado_en_cobro.componentes_fiado.buscador import BuscadorFiado
        self.via_buscador = BuscadorFiado(self)
        self.via_buscador.cliente_seleccionado.connect(self._evaluar_cliente)

        self.stack.addWidget(self.via_buscador) # 0
        self.stack.addWidget(self.via_aprobado) # 1
        self.stack.addWidget(self.via_bloqueo)  # 2
        self.stack.addWidget(self.via_nuevo)    # 3
        self.stack.addWidget(self.via_f5)       # 4

    def mostrar_para(self, monto):
        self._monto_carrito = monto
        self.stack.setCurrentWidget(self.via_buscador)
        self.via_buscador.txt_busqueda.setFocus()
        self.via_buscador.txt_busqueda.selectAll()

    def ocultar(self):
        self.hide()

    def _evaluar_cliente(self, cliente_id):
        if cliente_id == 0:
            self.stack.setCurrentWidget(self.via_nuevo)
            self.via_nuevo.txt_input.setFocus()
            return
            
        from src.clientes_fiado.cerebro.cerebro import cerebro
        cli = cerebro.obtener(cliente_id)
        if not cli:
            return
            
        datos = {
            'id': cli.id,
            'nombre': cli.nombre,
            'deuda': cli.deuda_actual,
            'limite': cli.limite_credito,
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

    def _cliente_recien_creado(self, cliente_id):
        self._evaluar_cliente(cliente_id)

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
                self.via_buscador.txt_busqueda.setFocus()
                self.via_buscador.txt_busqueda.selectAll()
            else:
                self.cancelado.emit()
        else:
            if self.stack.currentWidget():
                self.stack.currentWidget().keyPressEvent(event)

