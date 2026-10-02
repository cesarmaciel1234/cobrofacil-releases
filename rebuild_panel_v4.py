import os

new_code = """from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QLineEdit, QWidget, QHBoxLayout, QPushButton, QStackedWidget
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QDoubleValidator
from src.clientes_fiado.interfaz.cobro.hoja import HojaCuentaCobro as HojaCuenta
from src.clientes_fiado.cerebro.cerebro import cerebro
from src.utils.dinero import redondear_dinero

from src.cajero.ingresar_efectivo.medios.efectivo.lienzo import LienzoEfectivo
from src.cajero.ingresar_efectivo.medios.qr.lienzo import LienzoQr
from src.cajero.ingresar_efectivo.medios.tarjeta.lienzo import LienzoTarjeta
from src.cajero.ingresar_efectivo.medios.transferencia.lienzo import LienzoTransferencia

class PanelFiadoCobro(QFrame):
    cambio = pyqtSignal(str)
    cancelado = pyqtSignal()
    pago_listo = pyqtSignal(int, float)
    abono_registrado = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelFiadoCobro")
        self.setStyleSheet("QFrame#PanelFiadoCobro { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; }")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        self.hoja_cuenta = HojaCuenta(self)
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
        
        self.cont_botones = QWidget()
        h_lay = QHBoxLayout(self.cont_botones)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(8)
        
        btn_style = \"\"\"
            QPushButton {
                background-color: #E2E8F0;
                color: #0F172A;
                border-radius: 8px;
                padding: 12px;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid #CBD5E1;
            }
            QPushButton:hover {
                background-color: #CBD5E1;
            }
        \"\"\"
        
        self.btn_efectivo = QPushButton("Efectivo")
        self.btn_efectivo.setStyleSheet(btn_style)
        self.btn_efectivo.clicked.connect(lambda: self._iniciar_cobranza("Efectivo"))
        
        self.btn_tarjeta = QPushButton("Tarjeta")
        self.btn_tarjeta.setStyleSheet(btn_style)
        self.btn_tarjeta.clicked.connect(lambda: self._iniciar_cobranza("Tarjeta"))
        
        self.btn_qr = QPushButton("QR")
        self.btn_qr.setStyleSheet(btn_style)
        self.btn_qr.clicked.connect(lambda: self._iniciar_cobranza("QR"))
        
        self.btn_transferencia = QPushButton("Transferencia")
        self.btn_transferencia.setStyleSheet(btn_style)
        self.btn_transferencia.clicked.connect(lambda: self._iniciar_cobranza("Transferencia"))
        
        h_lay.addWidget(self.btn_efectivo)
        h_lay.addWidget(self.btn_tarjeta)
        h_lay.addWidget(self.btn_qr)
        h_lay.addWidget(self.btn_transferencia)
        
        lay.addWidget(self.cont_botones)
        self.cont_botones.hide()

        # LIENZOS PARA COBRO
        self.cont_lienzos = QStackedWidget()
        self.lienzo_efectivo = LienzoEfectivo()
        self.lienzo_qr = LienzoQr()
        self.lienzo_tarjeta = LienzoTarjeta()
        self.lienzo_transferencia = LienzoTransferencia()
        self.cont_lienzos.addWidget(self.lienzo_efectivo)
        self.cont_lienzos.addWidget(self.lienzo_qr)
        self.cont_lienzos.addWidget(self.lienzo_tarjeta)
        self.cont_lienzos.addWidget(self.lienzo_transferencia)
        
        # Conexiones
        self.lienzo_efectivo.listo.connect(lambda monto: self._finalizar_cobranza_con_motor(monto, "Efectivo", None))
        self.lienzo_efectivo.volver.connect(self._volver_de_lienzo)
        
        self.lienzo_qr.listo.connect(lambda det: self._finalizar_cobranza_con_motor(self._monto_a_cobrar, "QR", det))
        self.lienzo_qr.volver.connect(self._volver_de_lienzo)
        
        self.lienzo_tarjeta.listo.connect(lambda det: self._finalizar_cobranza_con_motor(self._monto_a_cobrar, "Tarjeta", det))
        self.lienzo_tarjeta.fallo.connect(lambda text: self._volver_de_lienzo())
        self.lienzo_tarjeta.volver.connect(self._volver_de_lienzo)
        
        self.lienzo_transferencia.listo.connect(lambda det: self._finalizar_cobranza_con_motor(self._monto_a_cobrar, "Transferencia", det))
        self.lienzo_transferencia.volver.connect(self._volver_de_lienzo)
        
        self.cont_lienzos.hide()
        lay.addWidget(self.cont_lienzos)

        lay.addStretch(1)
        self.hide()

    def bloquea_enter(self):
        return self.isVisible() and self._modo in ("confirmando", "cobranza", "cobrando_lienzo")
        
    def procesar_enter(self):
        if self._modo == "confirmando" and self._cliente_id:
            self._modo = "listo"
            self.pago_listo.emit(self._cliente_id, 0.0)
        elif self._modo == "cobranza" and self._cliente_id:
            self._iniciar_cobranza("Efectivo")
        elif self._modo == "cobrando_lienzo":
            # Pasar enter al lienzo activo
            actual = self.cont_lienzos.currentWidget()
            if hasattr(actual, "tecla"):
                actual.tecla(Qt.Key.Key_Return)

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
        self.cont_botones.hide()
        self._cerrar_lienzos()
        self.show()
        
        self.cambio.emit("buscando")
        self.hoja_cuenta.abrir(modo, self._monto)

    def activar_cobranza(self, monto_sugerido, deuda_actual):
        self._modo = "cobranza"
        nombre = getattr(self, "_cliente_nombre", "Cliente")
        self.estado.setText(f"Hola {nombre}")
        self.detalle.setText(f"Saldo anterior: ${deuda_actual:,.2f}\\nVenta actual: ${self._monto:,.2f}")
        self.icono.hide()
        
        self.txt_monto_abono.setText(f"{monto_sugerido:.2f}")
        self.txt_monto_abono.show()
        self.txt_monto_abono.setFocus()
        self.txt_monto_abono.selectAll()
        
        self.instruccion.hide()
        self.cont_botones.show()
        self._cerrar_lienzos()
        
    def _pin(self):
        try:
            from src.cajero.paso5_terminal.dialogos.pin.dialogo_pin import DialogoPIN
            from src.utils.qt_compat import qt_exec
            dlg = DialogoPIN("Cajero", self.window())
            return bool(qt_exec(dlg) and dlg.ok)
        except Exception:
            return False
            
    def _iniciar_cobranza(self, metodo="Efectivo"):
        texto = self.txt_monto_abono.text().replace(',', '.')
        if not texto.strip(): return
        monto = redondear_dinero(float(texto))
        if monto <= 0: return

        self._monto_a_cobrar = monto
        self._metodo_elegido = metodo
        
        if metodo == "Efectivo":
            if not self._pin():
                return
            self._finalizar_cobranza_con_motor(monto, metodo, None)
            return

        self._modo = "cobrando_lienzo"
        self.estado.hide()
        self.detalle.hide()
        self.txt_monto_abono.hide()
        self.cont_botones.hide()
        self.instruccion.hide()
        
        self.cont_lienzos.show()
        if metodo == "QR":
            self.cont_lienzos.setCurrentWidget(self.lienzo_qr)
            self.lienzo_qr.arrancar(monto)
        elif metodo == "Tarjeta":
            self.cont_lienzos.setCurrentWidget(self.lienzo_tarjeta)
            self.lienzo_tarjeta.arrancar(monto)
        elif metodo == "Transferencia":
            self.cont_lienzos.setCurrentWidget(self.lienzo_transferencia)
            self.lienzo_transferencia.arrancar(monto)
            
    def _volver_de_lienzo(self):
        self._modo = "cobranza"
        self._cerrar_lienzos()
        self.estado.show()
        self.detalle.show()
        self.txt_monto_abono.show()
        self.cont_botones.show()
        self.txt_monto_abono.setFocus()
        
    def _cerrar_lienzos(self):
        for lienzo in (self.lienzo_efectivo, self.lienzo_qr, self.lienzo_tarjeta, self.lienzo_transferencia):
            try:
                lienzo.cerrar()
            except Exception:
                pass
        self.cont_lienzos.hide()

    def _finalizar_cobranza_con_motor(self, monto, metodo, detalle):
        from src.clientes_fiado.interfaz.cobro.medios.resultado import ResultadoMedio
        from src.clientes_fiado.interfaz.cobro.medios.cerrar import asentar
        from src.cajero.cajero_activo import CajeroActivo
        from src.config import config
        
        res = ResultadoMedio(True, metodo, (metodo == "Efectivo"), detalle)
        
        cliente = cerebro.obtener(self._cliente_id)
        if not cliente: 
            self._volver_de_lienzo()
            return
            
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
            self._volver_de_lienzo()
            return
            
        if hecho.get('entra_caja'):
            from src.cajero.paso5_terminal.logica.movimientos_caja_service import MovimientosCajaService
            MovimientosCajaService().registrar_ingreso_efectivo(
                hecho['monto_caja'],
                CajeroActivo.nombre,
                hecho['motivo'],
                config.get('caja_id', 1),
                abrir_cajon=True,
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
        
        self._cerrar_lienzos()
        self._modo = "listo"
        self.pago_listo.emit(self._cliente_id, 0.0)

    def ocultar(self):
        self._modo = "oculto"
        self._cerrar_lienzos()
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
        self._cliente_nombre = nombre
        
        self._modo = "confirmando"
        self.hoja_cuenta.ocultar()
        self.hoja_cuenta.caja.clearFocus()
        self.setStyleSheet("QFrame#PanelFiadoCobro { background: #ECFDF5; border: 2px solid #34D399; border-radius: 16px; }")
        
        self.icono.hide()
        self.estado.setText(f"Hola {nombre}")
        self.detalle.setText("Crédito Aprobado")
        if hasattr(self, 'txt_monto_abono'):
            self.txt_monto_abono.hide()
        self.cont_botones.hide()
        self._cerrar_lienzos()
        self.instruccion.setText("[ ENTER ] PARA FINALIZAR VENTA")
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
"""

with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'w', encoding='utf-8') as f:
    f.write(new_code)
