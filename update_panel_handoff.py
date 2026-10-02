import os

file_path = 'src/cajero/paso6_cobro/fiado_en_cobro/panel.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_func = """    def _procesar_cobranza(self, metodo="Efectivo"):
        texto = self.txt_monto_abono.text().replace(',', '.')
        if not texto.strip(): return
        monto = redondear_dinero(float(texto))
        if monto <= 0: return
        
        from src.clientes_fiado.interfaz.cobro.medios.puerta import cobrar
        from src.clientes_fiado.interfaz.cobro.medios.cerrar import asentar
        from src.cajero.cajero_activo import CajeroActivo
        from src.config import config
        
        res = cobrar(metodo, monto)"""

new_func = """    def _procesar_cobranza(self, metodo="Efectivo"):
        texto = self.txt_monto_abono.text().replace(',', '.')
        if not texto.strip(): return
        monto = redondear_dinero(float(texto))
        if monto <= 0: return

        # Si no es Efectivo, le pasamos el control al motor de Paso 6
        if metodo != "Efectivo":
            mw = self.window()
            mw._fiado_flujo_activo = True
            mw._fiado_abono_monto = monto
            mw._fiado_cliente_id = self._cliente_id
            self.ocultar()
            mw.stack.setCurrentIndex(0)
            mw.set_metodo(metodo)
            mw.total_final = monto
            mw.lbl_neto.setText(f"NETO A PAGAR: ${monto:,.2f}")
            if hasattr(mw, '_enter_cobro'):
                mw._enter_cobro()
            return
            
        from src.clientes_fiado.interfaz.cobro.medios.puerta import cobrar
        from src.clientes_fiado.interfaz.cobro.medios.cerrar import asentar
        from src.cajero.cajero_activo import CajeroActivo
        from src.config import config
        
        res = cobrar(metodo, monto)"""

if old_func in text:
    text = text.replace(old_func, new_func)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated panel.py QR handoff")
else:
    print("Could not find old_func")
