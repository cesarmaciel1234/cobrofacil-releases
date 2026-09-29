from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QSizePolicy
from src.clientes_fiado.cerebro.cerebro import cerebro
from src.clientes_fiado.interfaz.cobro.hoja import HojaCuentaCobro

class PanelFiadoCobro(QFrame):
    """
    Validador enterprise de Cuenta Corriente (Fiado).
    Encapsula la búsqueda de cliente y muestra una pantalla verde de confirmación
    estilo POS antes de cerrar la venta.
    """
    pago_listo = pyqtSignal(int, float)
    cancelado = pyqtSignal()
    cambio = pyqtSignal(str)
    abono_registrado = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._modo = "oculto"
        self._monto = 0.0
        self._cliente_id = None
        self._armar()



    def _armar(self):
        self.setObjectName("PanelFiadoCobro")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            "QFrame#PanelFiadoCobro { background: #ECFDF5; border: 2px solid #34D399; border-radius: 16px; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 18, 24, 18)
        lay.setSpacing(12)
        
        self.hoja_cuenta = HojaCuentaCobro(self)
        self.hoja_cuenta.listo.connect(self._al_cliente_encontrado)
        self.hoja_cuenta.cancelado.connect(self._al_cancelar_busqueda)
        self.hoja_cuenta.abono_registrado.connect(self.abono_registrado.emit)
        lay.addWidget(self.hoja_cuenta)

        lay.addStretch(1)

        self.icono = QLabel("✓")
        self.icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icono.setStyleSheet("color: #10B981; font-size: 80px; font-weight: 900; background: transparent; border: none;")
        lay.addWidget(self.icono)

        self.estado = QLabel("")
        self.estado.setWordWrap(True)
        self.estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estado.setStyleSheet(
            "color: #065F46; font-size: 32px; font-weight: 900; background: transparent; border: none;"
        )
        lay.addWidget(self.estado)

        self.detalle = QLabel("")
        self.detalle.setWordWrap(True)
        self.detalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detalle.setStyleSheet(
            "color: #047857; font-size: 22px; font-weight: 700; background: transparent; border: none;"
        )
        lay.addWidget(self.detalle)
        
        self.instruccion = QLabel("[ ENTER ] CONFIRMAR FIADO")
        self.instruccion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruccion.setStyleSheet("color: #FFFFFF; background: #10B981; font-size: 24px; font-weight: 900; border-radius: 12px; padding: 14px;")
        lay.addWidget(self.instruccion)
        
        lay.addStretch(1)
        self.hide()

    def bloquea_enter(self):
        return self.isVisible() and self._modo == "confirmando"
        
    def procesar_enter(self):
        if self._modo == "confirmando" and self._cliente_id:
            self._modo = "listo"
            self.pago_listo.emit(self._cliente_id, 0.0)

    def mostrar(self, monto, modo="Fiado"):
        self._monto = float(monto or 0)
        self._modo = "buscando"
        self._cliente_id = None
        
        # Durante la búsqueda, ocultamos la interfaz de confirmación
        self.setStyleSheet("QFrame#PanelFiadoCobro { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; }")
        self.estado.setText("")
        self.detalle.setText("")
        self.icono.hide()
        self.instruccion.hide()
        self.show()
        
        self.cambio.emit("buscando")
        self.hoja_cuenta.abrir(modo, self._monto)

    def ocultar(self):
        self._modo = "oculto"
        self.hoja_cuenta.ocultar()
        self.hide()

    def _al_cliente_encontrado(self, cliente_id, _abono=0.0):
        self._cliente_id = cliente_id

        cliente = cerebro.cliente(cliente_id)
        if not cliente:
            self.cancelado.emit()
            return
            
        nombre = cliente.get("nombre") or cliente.get("nombre_completo") or "Cliente"
        disp = cerebro.credito_disponible(cliente)
        
        self._modo = "confirmando"
        # Cambiamos al estilo "Green Box" de confirmación
        self.setStyleSheet("QFrame#PanelFiadoCobro { background: #ECFDF5; border: 2px solid #34D399; border-radius: 16px; }")
        self.icono.show()
        self.estado.setText(f"FIADO APROBADO\n{nombre}")
        self.detalle.setText(f"Límite Disponible: \nCompra Actual: ")
        self.instruccion.show()
        self.cambio.emit("confirmando")
        
    def _al_cancelar_busqueda(self):
        self._modo = "oculto"
        self.hide()
        self.cancelado.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.hoja_cuenta.isVisible():
            self.hoja_cuenta.ubicar()
