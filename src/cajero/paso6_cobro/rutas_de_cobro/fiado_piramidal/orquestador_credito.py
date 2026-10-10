# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSignal

# Import global search engine
from src.motores_empresariales.motor_busqueda_clientes.motor_busqueda import MotorBusquedaClientes
from src.cajero.paso6_cobro.fiado_en_cobro.ui.buscador_clientes.panel_buscador import PanelBuscadorClientes

# Import the routes
from .ruta1_margen_aprobado.panel_aprobado import PanelMargenAprobado
from .ruta2_limite_superado.panel_bloqueo import PanelLimiteSuperado
from .ruta3_cliente_nuevo.panel_nuevo import PanelClienteNuevo


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
    def borrar(self): pass
    def escribir(self, key): pass
    def fijar_monto(self, m): pass

class OrquestadorFiadoPiramidal(QFrame):
    # Signals emitted to Paso 6 Checkout
    pago_listo = pyqtSignal()
    cancelado = pyqtSignal()
    abono_registrado = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OrquestadorFiadoPiramidal")
        self.setStyleSheet("QFrame#OrquestadorFiadoPiramidal { background: transparent; }")
        
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        self.lay.addWidget(self.stack)

        # Motores
        self.motor_busqueda = MotorBusquedaClientes()
        
        # Vías
        self.via_buscador = PanelBuscadorClientes()
        self.via_aprobado = PanelMargenAprobado()
        self.via_bloqueo = PanelLimiteSuperado()
        self.via_nuevo = PanelClienteNuevo()
        
        self.stack.addWidget(self.via_buscador)
        self.stack.addWidget(self.via_aprobado)
        self.stack.addWidget(self.via_bloqueo)
        self.stack.addWidget(self.via_nuevo)
        
        # Conexiones Buscador
        self.via_buscador.texto_cambiado.connect(self.motor_busqueda.buscar_texto)
        self.motor_busqueda.sugerencias_listas.connect(self.via_buscador.mostrar_sugerencias)
        self.via_buscador.cliente_elegido.connect(self._ruta_analisis)
        self.via_buscador.creacion_solicitada.connect(self._ruta_cliente_nuevo)
        
        # Respuestas del Orquestador
        self.motor_busqueda.limite_aprobado.connect(self._decidir_via_credito)

        # Conexiones Finales
        self.via_aprobado.confirmado.connect(self.pago_listo.emit)
        self.via_bloqueo.pin_validado.connect(self.pago_listo.emit)
        self.via_bloqueo.solicita_f5.connect(self._abrir_puente_f5)
        self.via_nuevo.cliente_creado.connect(self._ruta_analisis_desde_nuevo)

        self._monto_venta = 0.0
        self.hoja_cuenta = HojaVirtual(self)
        

    def iniciar(self, monto):
        self._monto_venta = float(monto or 0)
        self.motor_busqueda.set_monto_venta(self._monto_venta)
        self.via_buscador.limpiar()
        self.stack.setCurrentWidget(self.via_buscador)
        self.via_buscador.focus_caja()

    def _ruta_analisis(self, datos_cliente):
        # We pass it to the engine, which will calculate and emit 'limite_aprobado'
        self.motor_busqueda.aprobar_credito(datos_cliente)
        
    def _ruta_analisis_desde_nuevo(self, datos_cliente):
        # Once created, we analyze it just like a selected client
        self.motor_busqueda.aprobar_credito(datos_cliente)

    def _decidir_via_credito(self, datos):
        compra = float(datos.get('compra', 0))
        limite = float(datos.get('limite', 0))
        
        excedido = compra > (limite + 0.01)
        
        if excedido:
            self.via_bloqueo.poblar(datos)
            self.stack.setCurrentWidget(self.via_bloqueo)
        else:
            self.via_aprobado.poblar(datos)
            self.stack.setCurrentWidget(self.via_aprobado)

    def _ruta_cliente_nuevo(self, texto):
        self.via_nuevo.poblar_inicial(texto)
        self.stack.setCurrentWidget(self.via_nuevo)

    def _abrir_puente_f5(self, datos_cliente):
        # Here we will open the F5 modal. 
        pass

    def keyPressEvent(self, event):
        # Orquestador handles global escape
        if event.key() == Qt.Key.Key_Escape:
            if self.stack.currentWidget() == self.via_buscador:
                self.cancelado.emit()
            else:
                # Go back to search
                self.iniciar(self._monto_venta)
        else:
            # Let the current widget handle it
            if self.stack.currentWidget():
                self.stack.currentWidget().keyPressEvent(event)

    def mostrar(self, monto, modo="Fiado"):
        self.iniciar(monto)
        self.show()

    def ocultar(self):
        self.hide()

    def actualizar_monto(self, monto):
        self._monto_venta = float(monto or 0)
        self.motor_busqueda.set_monto_venta(self._monto_venta)

    def activar_cobranza(self, monto):
        pass

    def bloquea_enter(self):
        return True

    def procesar_enter(self):
        from PyQt6.QtGui import QKeyEvent
        evt = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        self.keyPressEvent(evt)

    def procesar_f9(self):
        return False
