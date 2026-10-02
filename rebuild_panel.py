from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QDoubleValidator
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QSizePolicy, QLineEdit
from src.clientes_fiado.cerebro.cerebro import cerebro
from src.clientes_fiado.interfaz.cobro.hoja import HojaCuentaCobro
from src.utils.dinero import redondear_dinero

class PanelFiadoCobro(QFrame):
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

        self.icono = QLabel('\u2713')
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
        
        self.txt_monto_abono = QLineEdit()
        self.txt_monto_abono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_monto_abono.setFixedHeight(64)
        self.txt_monto_abono.setValidator(QDoubleValidator(0.0, 9999999.0, 2))
        self.txt_monto_abono.setStyleSheet(
            "QLineEdit { background: #FFFFFF; color: #065F46; border: 2px solid #10B981; border-radius: 12px; font-size: 32px; font-weight: 900; }"
        )
        self.txt_monto_abono.hide()
        self.txt_monto_abono.installEventFilter(self)
        lay.addWidget(self.txt_monto_abono)
        
        self.instruccion = QLabel("[ ENTER ] CONFIRMAR FIADO")
        self.instruccion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruccion.setStyleSheet("color: #FFFFFF; background: #10B981; font-size: 24px; font-weight: 900; border-radius: 12px; padding: 14px;")
        lay.addWidget(self.instruccion)
        
        lay.addStretch(1)
        self.hide()

    def bloquea_enter(self):
        return self.isVisible() and self._modo in ("confirmando", "cobranza")
        
    def procesar_enter(self):
        if self._modo == "confirmando" and self._cliente_id:
            self._modo = "listo"
            self.pago_listo.emit(self._cliente_id, 0.0)
        elif self._modo == "cobranza" and self._cliente_id:
            self._procesar_cobranza()

    def mostrar(self, monto, modo="Fiado"):
        self._monto = float(monto or 0)
        self._modo = "buscando"
        self._cliente_id = None
        
        self.setStyleSheet("QFrame#PanelFiadoCobro { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; }")
        self.estado.setText("")
        self.detalle.setText("")
        self.icono.hide()
        self.instruccion.hide()
        self.txt_monto_abono.hide()
        self.show()
        
        self.cambio.emit("buscando")
        self.hoja_cuenta.abrir(modo, self._monto)

    def activar_cobranza(self, monto_sugerido, deuda_actual):
        self._modo = "cobranza"
        self.estado.setText("PAGO DE CUENTA CORRIENTE")
        self.detalle.setText(f"Deuda Previa: \nCompra Actual: ")
        self.icono.hide()
        
        self.txt_monto_abono.setText(f"{monto_sugerido:.2f}")
        self.txt_monto_abono.show()
        self.txt_monto_abono.setFocus()
        self.txt_monto_abono.selectAll()
        
        self.instruccion.setText("[ ENTER ] PROCESAR PAGO")
        
    def _procesar_cobranza(self):
        texto = self.txt_monto_abono.text().replace(',', '.')
        if not texto.strip(): return
        monto = redondear_dinero(float(texto))
        if monto <= 0: return
        
        from src.clientes_fiado.interfaz.cobro.medios.puerta import cobrar
        from src.clientes_fiado.interfaz.cobro.medios.cerrar import asentar
        from src.cajero.cajero_activo import CajeroActivo
        from src.config import config
        
        res = cobrar("Efectivo", monto)
        if not res or not getattr(res, 'ok', False):
            return
            
        cliente = cerebro.obtener(self._cliente_id)
        if not cliente: return
        try:
            cliente_dict = dict(cliente) if hasattr(cliente, 'keys') else cliente
            deuda_actual = float(cliente_dict.get('deuda_actual', 0) or 0)
        except:
            deuda_actual = 0.0
            
        hecho = asentar(
            self._cliente_id,
            monto,
            deuda_actual,
            "Cajero",
            CajeroActivo.nombre,
            res,
            imprimir_saldo=False,
        )
        if not hecho.get('ok'):
            return
            
        if hecho.get('entra_caja'):
            from src.cajero.paso5_terminal.logica.movimientos_caja_service import MovimientosCajaService
            MovimientosCajaService().registrar_ingreso_efectivo(
                hecho['monto_caja'],
                CajeroActivo.nombre,
                hecho['motivo'],
                config.get('caja_id', 1),
                abrir_cajon=False,
                imprimir=False,
            )
            
        from src.cajero.paso6_cobro.fiado_en_cobro.cobranza import ResultadoAbonoPrevio
        self.abono_registrado.emit(ResultadoAbonoPrevio(
            ok=True,
            cliente_id=self._cliente_id,
            monto=monto,
            nombre=str(hecho.get('nombre') or cliente.get('nombre') or 'Cliente'),
            saldo=float(hecho.get('saldo') or 0.0),
            deuda_anterior=deuda_actual
        ))
        
        self._modo = "listo"
        self.pago_listo.emit(self._cliente_id, 0.0)

    def ocultar(self):
        self._modo = "oculto"
        self.hoja_cuenta.ocultar()
        self.hide()

    def _al_cliente_encontrado(self, cliente_id, _abono=0.0):
        if self._modo == "confirmando" and int(self._cliente_id or 0) == int(cliente_id):
            self.procesar_enter()
            return
        self._cliente_id = cliente_id

        cliente = cerebro.obtener(cliente_id)
        if not cliente:
            self.cancelado.emit()
            return
            
        nombre = cliente.get("nombre") or cliente.get("nombre_completo") or "Cliente"
        disp = cerebro.credito_disponible(cliente)
        
        self._modo = "confirmando"
        self.hoja_cuenta.ocultar()
        self.hoja_cuenta.caja.clearFocus()
        self.setStyleSheet("QFrame#PanelFiadoCobro { background: #ECFDF5; border: 2px solid #34D399; border-radius: 16px; }")
        
        # Ocultar icono (bien), limite y compra actual como pidio el usuario
        self.icono.hide()
        self.estado.setText(f"FIADO APROBADO\n{nombre}")
        self.detalle.setText("")
        self.txt_monto_abono.hide()
        
        self.instruccion.setText("[ ENTER ] CONFIRMAR FIADO")
        self.instruccion.show()
        self.cambio.emit("confirmando")
        ventana = self.window()
        if ventana is not None:
            ventana.setFocus()
        
    def _al_cancelar_busqueda(self):
        self._modo = "oculto"
        self.hide()
        self.cancelado.emit()

    def eventFilter(self, obj, event):
        if obj == self.txt_monto_abono and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self._al_cliente_encontrado(self._cliente_id)
                return True
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.procesar_enter()
                return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.hoja_cuenta.isVisible():
            self.hoja_cuenta.ubicar()