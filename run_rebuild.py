import sys

with open('original_panel.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add QLineEdit and redondear_dinero imports
text = text.replace(
    'from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QSizePolicy',
    'from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QSizePolicy, QLineEdit\nfrom PyQt6.QtGui import QDoubleValidator\nfrom src.utils.dinero import redondear_dinero'
)

# Add txt_monto_abono to _armar
armar_addition = """        self.txt_monto_abono = QLineEdit()
        self.txt_monto_abono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_monto_abono.setFixedHeight(64)
        self.txt_monto_abono.setValidator(QDoubleValidator(0.0, 9999999.0, 2))
        self.txt_monto_abono.setStyleSheet(
            "QLineEdit { background: #FFFFFF; color: #065F46; border: 2px solid #10B981; border-radius: 12px; font-size: 32px; font-weight: 900; }"
        )
        self.txt_monto_abono.hide()
        self.txt_monto_abono.installEventFilter(self)
        lay.addWidget(self.txt_monto_abono)

"""
text = text.replace(
    '        self.instruccion = QLabel("[ ENTER ] CONFIRMAR FIADO")',
    armar_addition + '        self.instruccion = QLabel("[ ENTER ] CONFIRMAR FIADO")'
)

# Update bloquea_enter and procesar_enter
text = text.replace(
    '        return self.isVisible() and self._modo == "confirmando"',
    '        return self.isVisible() and self._modo in ("confirmando", "cobranza")'
)

procesar_enter_new = """    def procesar_enter(self):
        if self._modo == "confirmando" and self._cliente_id:
            self._modo = "listo"
            self.pago_listo.emit(self._cliente_id, 0.0)
        elif self._modo == "cobranza" and self._cliente_id:
            self._procesar_cobranza()"""
text = text.replace(
    '    def procesar_enter(self):\n        if self._modo == "confirmando" and self._cliente_id:\n            self._modo = "listo"\n            self.pago_listo.emit(self._cliente_id, 0.0)',
    procesar_enter_new
)

# Add txt_monto_abono.hide() in mostrar
text = text.replace(
    '        self.instruccion.hide()\n        self.show()',
    '        self.instruccion.hide()\n        self.txt_monto_abono.hide()\n        self.show()'
)

# Add activar_cobranza and _procesar_cobranza before ocultar
cobranza_methods = """    def activar_cobranza(self, monto_sugerido, deuda_actual):
        self._modo = "cobranza"
        self.estado.setText("PAGO DE CUENTA CORRIENTE")
        self.detalle.setText(f"Deuda Previa: ${deuda_actual:,.2f}\\nVenta Actual: ${self._monto:,.2f}")
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

"""
text = text.replace('    def ocultar(self):', cobranza_methods + '    def ocultar(self):')

# In _al_cliente_encontrado: hide the icono and the detalle, as requested
al_cliente = """        self._modo = "confirmando"
        self.hoja_cuenta.ocultar()
        self.hoja_cuenta.caja.clearFocus()
        self.setStyleSheet("QFrame#PanelFiadoCobro { background: #ECFDF5; border: 2px solid #34D399; border-radius: 16px; }")
        
        # Ocultar icono (bien), limite y compra actual como pidio el usuario
        self.icono.hide()
        self.estado.setText(f"FIADO APROBADO\\n{nombre}")
        self.detalle.setText("")
        self.txt_monto_abono.hide()
        
        self.instruccion.setText("[ ENTER ] CONFIRMAR FIADO")
        self.instruccion.show()"""

old_al_cliente = """        self._modo = "confirmando"
        self.hoja_cuenta.ocultar()
        self.hoja_cuenta.caja.clearFocus()
        self.setStyleSheet("QFrame#PanelFiadoCobro { background: #ECFDF5; border: 2px solid #34D399; border-radius: 16px; }")
        self.icono.show()
        self.estado.setText(f"FIADO APROBADO\\n{nombre}")
        self.detalle.setText(
            f"Límite Disponible: ${disp:,.2f}\\nCompra Actual: ${self._monto:,.2f}"
        )
        self.instruccion.show()"""
text = text.replace(old_al_cliente, al_cliente)

# event filter
event_filter = """    def eventFilter(self, obj, event):
        if obj == self.txt_monto_abono and event.type() == event.Type.KeyPress:
            from PyQt6.QtCore import Qt
            if event.key() == Qt.Key.Key_Escape:
                self._al_cliente_encontrado(self._cliente_id)
                return True
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.procesar_enter()
                return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):"""
text = text.replace('    def resizeEvent(self, event):', event_filter)

with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'w', encoding='utf-8') as f:
    f.write(text)
