import os
import re

file_path = 'src/cajero/paso6_cobro/fiado_en_cobro/panel.py'
with open(file_path, 'r', encoding='utf-8') as f:
    original = f.read()

new_code = """from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QLineEdit, QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QDoubleValidator
from src.clientes_fiado.interfaz.cobro.hoja import HojaCuenta
from src.clientes_fiado.oficina.cuenta.cerebro import cerebro
from src.utils.dinero import redondear_dinero

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
        
        # Botones de métodos de pago
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
        self.btn_efectivo.clicked.connect(lambda: self._procesar_cobranza("Efectivo"))
        
        self.btn_tarjeta = QPushButton("Tarjeta")
        self.btn_tarjeta.setStyleSheet(btn_style)
        self.btn_tarjeta.clicked.connect(lambda: self._procesar_cobranza("Tarjeta"))
        
        self.btn_qr = QPushButton("QR")
        self.btn_qr.setStyleSheet(btn_style)
        self.btn_qr.clicked.connect(lambda: self._procesar_cobranza("QR"))
        
        self.btn_transferencia = QPushButton("Transferencia")
        self.btn_transferencia.setStyleSheet(btn_style)
        self.btn_transferencia.clicked.connect(lambda: self._procesar_cobranza("Transferencia"))
        
        h_lay.addWidget(self.btn_efectivo)
        h_lay.addWidget(self.btn_tarjeta)
        h_lay.addWidget(self.btn_qr)
        h_lay.addWidget(self.btn_transferencia)
        
        lay.addWidget(self.cont_botones)
        self.cont_botones.hide()

        lay.addStretch(1)
        self.hide()

    def bloquea_enter(self):
        return self.isVisible() and self._modo in ("confirmando", "cobranza")
        
    def procesar_enter(self):
        if self._modo == "confirmando" and self._cliente_id:
            self._modo = "listo"
            self.pago_listo.emit(self._cliente_id, 0.0)
        elif self._modo == "cobranza" and self._cliente_id:
            self._procesar_cobranza("Efectivo")

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
        self.show()
        
        self.cambio.emit("buscando")
        self.hoja_cuenta.abrir(modo, self._monto)

    def activar_cobranza(self, monto_sugerido, deuda_actual):
        self._modo = "cobranza"
        nombre = getattr(self, "_cliente_nombre", "Cliente")
        self.estado.setText(f"Hola {nombre}")
        self.detalle.setText(f"Estás a punto de pagar toda la deuda, gracias.\\nSaldo anterior: ${deuda_actual:,.2f}\\nVenta actual: ${self._monto:,.2f}")
        self.icono.hide()
        
        self.txt_monto_abono.setText(f"{monto_sugerido:.2f}")
        self.txt_monto_abono.show()
        self.txt_monto_abono.setFocus()
        self.txt_monto_abono.selectAll()
        
        self.instruccion.setText("[ ENTER ] PARA FINALIZAR VENTA - ¿Con qué querés pagar?")
        self.cont_botones.show()
        
    def _procesar_cobranza(self, metodo="Efectivo"):
        texto = self.txt_monto_abono.text().replace(',', '.')
        if not texto.strip(): return
        monto = redondear_dinero(float(texto))
        if monto <= 0: return
        
        from src.clientes_fiado.interfaz.cobro.medios.puerta import cobrar
        from src.clientes_fiado.interfaz.cobro.medios.cerrar import asentar
        from src.cajero.cajero_activo import CajeroActivo
        from src.config import config
        
        res = cobrar(metodo, monto)
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
        self._cliente_nombre = nombre
        disp = cerebro.credito_disponible(cliente)
        
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
            from PyQt6.QtCore import Qt
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

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_code)
